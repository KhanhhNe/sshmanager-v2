import logging
import os
import warnings
import webbrowser

import cryptography
import hypercorn.trio
import trio
import trio_asyncio
from hypercorn.run import run

with warnings.catch_warnings():
    # Ignore the warnings of using deprecated cryptography libraries in asyncssh
    warnings.filterwarnings('ignore', category=cryptography.CryptographyDeprecationWarning)
    import asyncssh

import config
import utils
from controllers import tasks, actions
from models import init_db


async def run_app(hypercorn_config):
    asyncssh.set_log_level(logging.CRITICAL)

    async with trio.open_nursery() as nursery:
        actions.reset_old_status()
        nursery.start_soon(tasks.run_all_tasks)
        nursery.start_soon(trio.to_thread.run_sync, run, hypercorn_config)


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
    init_db()

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
    except KeyboardInterrupt:
        pass
    finally:
        print("Exited")
        exit()
