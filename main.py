import os
import webbrowser
from multiprocessing import freeze_support

import uvicorn

import config
import utils

if __name__ == '__main__':
    freeze_support()
    os.makedirs('data', exist_ok=True)

    # noinspection HttpUrlsUsage
    if os.environ.get("DEBUG"):
        if os.path.exists('data/config.ini'):
            os.remove('data/config.ini')

    port = config.get('web_port')
    if not os.environ.get("DEBUG"):
        webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")

    if os.path.exists('data/current_thread.txt'):
        os.remove('data/current_thread.txt')
    # loop='none' to 'make' it use asyncio.ProactorEventLoop
    # so we can use asyncio.create_subprocess_exec()
    uvicorn.run('app:app',
                host='0.0.0.0', port=port,
                workers=config.get('web_workers_count'), loop='none',
                log_config='logging_config.json')
