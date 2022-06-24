import functools
import logging
import os
import warnings
import webbrowser
from multiprocessing import Event
from typing import Optional

import cryptography
import hypercorn.trio
import trio
import trio_asyncio
from hypercorn.trio import worker_serve
from hypercorn.utils import check_multiprocess_shutdown_event
from trio.to_thread import run_sync

with warnings.catch_warnings():
    # Ignore the warnings of using deprecated cryptography libraries in asyncssh
    warnings.filterwarnings('ignore', category=cryptography.CryptographyDeprecationWarning)
    import asyncssh
    from app import app

import config
import utils
from controllers import tasks, actions
from models import init_db

logger = logging.getLogger('Main')


def run_web(hypercorn_config: hypercorn.Config,
            sockets: Optional[hypercorn.config.Sockets] = None,
            shutdown_event: Optional[Event] = None):
    if sockets is not None:
        for sock in sockets.secure_sockets:
            sock.listen(hypercorn_config.backlog)
        for sock in sockets.insecure_sockets:
            sock.listen(hypercorn_config.backlog)

    shutdown_trigger = None
    if shutdown_event is not None:
        shutdown_trigger = functools.partial(check_multiprocess_shutdown_event, shutdown_event, trio.sleep)

    logger.debug("Initialized web server")
    return functools.partial(worker_serve, app, hypercorn_config, sockets=sockets, shutdown_trigger=shutdown_trigger)


async def run_app(hypercorn_config: hypercorn.Config):
    asyncssh.set_log_level(logging.CRITICAL)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(run_web(hypercorn_config))
        nursery.start_soon(run_sync, actions.reset_old_status)
        nursery.start_soon(tasks.run_all_tasks)


if __name__ == '__main__':
    # freeze_support()
    os.makedirs('data', exist_ok=True)
    port = config.get('web_port')

    # Remove config.ini file by default when debugging
    if os.environ.get("DEBUG"):
        if os.path.exists('data/config.ini'):
            os.remove('data/config.ini')

    # Open the webbrowser pointing to app's URL
    if not os.environ.get("DEBUG"):
        webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")

    # Logging related config
    utils.configure_logging()

    # Initialize database
    logger.debug("Database initializing...")
    init_db()
    logger.debug("Database initialized")

    # Hypercorn config
    conf = hypercorn.config.Config()
    conf.bind = [f'0.0.0.0:{port}']
    conf.graceful_timeout = 0
    conf.accesslog = '-'
    conf.errorlog = '-'
    conf.worker_class = 'trio'
    conf.workers = 1
    conf.application_path = 'app:app'

    # Run the app
    try:
        trio_asyncio.run(run_app, conf)
    finally:
        print("Exited")

    exit()
