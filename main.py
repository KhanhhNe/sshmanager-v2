import logging
import os
import warnings
import webbrowser
from multiprocessing import freeze_support

import cryptography
import hypercorn
import hypercorn.trio
import trio
import trio_asyncio

with warnings.catch_warnings():
    # Ignore the warnings of using deprecated cryptography libraries in asyncssh
    warnings.filterwarnings('ignore', category=cryptography.CryptographyDeprecationWarning)
    import asyncssh
    from app import app

import config
import utils
from controllers import tasks, actions
from models.database import init_db


async def run_app(conf):
    asyncssh.set_log_level(logging.CRITICAL)

    # Run the web app
    async with trio.open_nursery() as nursery:
        actions.reset_old_status()
        nursery.start_soon(tasks.run_all_tasks)
        # noinspection PyTypeChecker
        await hypercorn.trio.serve(app, conf)
        nursery.cancel_scope.cancel()


if __name__ == '__main__':
    freeze_support()
    port = config.get('web_port')
    os.makedirs('data', exist_ok=True)

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
    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{port}']
    config.graceful_timeout = 0
    config.accesslog = '-'
    config.errorlog = '-'

    # Run the app
    try:
        trio_asyncio.run(run_app, config)
    except KeyboardInterrupt:
        pass
    finally:
        print("Exited")
