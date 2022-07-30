import functools
import logging
import multiprocessing
import os
import warnings
import webbrowser
from traceback import format_exc

import cryptography
import hypercorn.trio
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


async def run_tasks():
    asyncssh.set_log_level(logging.CRITICAL)
    async with trio.open_nursery() as nursery:
        await run_sync(init_db)
        await run_sync(actions.reset_entities_data)
        nursery.start_soon(tasks.run_all_tasks)


def run_hypercorn_server(conf: hypercorn.Config):
    utils.configure_logging()
    run(conf)


if __name__ == '__main__':
    # freeze_support()
    os.makedirs('data', exist_ok=True)
    port = config.get('web_port')

    if os.environ.get("DEBUG"):
        # Remove config.ini file by default when debugging
        if os.path.exists('data/config.ini'):
            os.remove('data/config.ini')
    else:
        # Open the web browser pointing to app's URL
        webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")

    # Logging related config
    utils.configure_logging()

    # Hypercorn config
    conf = hypercorn.config.Config()
    conf.bind = [f'0.0.0.0:{port}']
    conf.graceful_timeout = 0
    conf.accesslog = '-'
    conf.errorlog = '-'
    conf.worker_class = 'trio'
    conf.workers = 5
    conf.application_path = 'app:app'

    run_server = functools.partial(run_hypercorn_server, conf)
    process = multiprocessing.Process(target=run_server)
    process.start()

    # Run the app
    try:
        trio_asyncio.run(run_tasks)
    except Exception:
        logger.exception(format_exc())
        raise
    finally:
        process.terminate()
        process.join()
        logger.info("Exited")
