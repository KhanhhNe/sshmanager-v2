import asyncio
import json
import logging
import os
import warnings
import webbrowser
from multiprocessing import freeze_support

import cryptography
import hypercorn
from hypercorn.asyncio import serve

with warnings.catch_warnings():
    # Ignore the warnings of using deprecated cryptography libraries in asyncssh
    warnings.filterwarnings('ignore', category=cryptography.CryptographyDeprecationWarning)
    import asyncssh
    from app import app

import config
import utils
from controllers import tasks
from models.database import init_db


async def run_app(conf):
    asyncssh.set_log_level(logging.CRITICAL)

    # Run background tasks
    runner = tasks.AllTasksRunner()
    asyncio.create_task(runner.run())

    # Run the web app
    # noinspection PyTypeChecker
    await hypercorn.asyncio.worker_serve(app, conf)

    # Stop background tasks
    await runner.stop()


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
    config.logconfig_dict = json.load(open('logging_config.json'))

    # Run the app
    asyncio.get_event_loop().run_until_complete(run_app(config))
