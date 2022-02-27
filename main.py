import os
import subprocess
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

    process = None
    if os.environ.get("DEVMODE"):
        process = subprocess.Popen(["npm", "run", "build-watch"],
                                   stderr=subprocess.DEVNULL,
                                   shell=True)

    port = config.get('web_port')
    workers = config.get('web_workers_count')

    if not os.environ.get("DEBUG"):
        webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")

    if os.path.exists('data/current_thread.txt'):
        os.remove('data/current_thread.txt')
    # loop='none' to 'make' it use asyncio.ProactorEventLoop
    # so we can use asyncio.create_subprocess_exec()
    uvicorn.run('app:app',
                host='0.0.0.0', port=port,
                workers=workers, loop='none',
                log_level='warning')
    if process is not None:
        process.kill()
