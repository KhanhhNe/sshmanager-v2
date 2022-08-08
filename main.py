import atexit
import functools
import logging
import multiprocessing
import os
import warnings
import webbrowser
from traceback import format_exc

import cryptography
import hypercorn.trio
import psutil
import trio
import trio_asyncio
from hypercorn.run import run
from trio.to_thread import run_sync

with warnings.catch_warnings():
    # Ignore the warnings of using deprecated cryptography libraries in asyncssh
    warnings.filterwarnings('ignore', category=cryptography.CryptographyDeprecationWarning)
    import asyncssh

import config
import utils
from controllers import tasks, actions
from models import init_db

logger = logging.getLogger('Main')
exited = multiprocessing.Event()


async def run_tasks():
    asyncssh.set_log_level(logging.CRITICAL)
    async with trio.open_nursery() as nursery:
        await run_sync(init_db)
        await run_sync(actions.reset_entities_data)
        nursery.start_soon(tasks.run_all_tasks)


def run_hypercorn_server(hypercorn_conf: hypercorn.Config):
    utils.configure_logging()
    run(hypercorn_conf)


def kill_all_processes(parent_pid: int):
    try:
        exited.wait()
    except KeyboardInterrupt:
        pass

    children = psutil.Process(pid=parent_pid).children(recursive=True)
    children = [p for p in children if p.pid != os.getpid()]

    for child in children:
        child.terminate()
    gone, alive = psutil.wait_procs(children, timeout=1)
    for child in alive:
        child.kill()


if __name__ == '__main__':
    # freeze_support()
    os.makedirs('data', exist_ok=True)
    port = config.get('web_port')

    # Logging related config
    utils.configure_logging()

    # Hypercorn config
    conf = hypercorn.config.Config()
    conf.bind = [f'0.0.0.0:{port}']
    conf.graceful_timeout = 0
    conf.accesslog = '-'
    conf.errorlog = '-'
    conf.worker_class = 'trio'
    conf.application_path = 'app:app'

    if os.environ.get("DEBUG"):
        # Reset config.ini to default values
        if os.path.exists('data/config.ini'):
            os.remove('data/config.ini')

        # Use reloader for convenient development
        conf.use_reloader = True
    else:
        # Open the web browser pointing to app's URL
        webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")

        # Use multiple worker to speed up the server
        conf.workers = multiprocessing.cpu_count()

    # Make sure to set the exit event after this process exits
    atexit.register(exited.set)

    run_server = functools.partial(run_hypercorn_server, conf)
    multiprocessing.Process(target=run_server).start()
    multiprocessing.Process(target=kill_all_processes, args=(os.getpid(),)).start()

    # Run the app
    try:
        trio_asyncio.run(run_tasks)
    except Exception:
        logger.exception(format_exc())
        raise
    finally:
        logger.info("Exited")
