import os
import webbrowser
from multiprocessing import freeze_support

import uvicorn

import config
import utils

if __name__ == '__main__':
    freeze_support()

    # noinspection HttpUrlsUsage
    if os.environ.get("DEBUG"):
        if os.path.exists('config.ini'):
            os.remove('config.ini')

    conf = config.get_config()
    port = conf.getint('WEB', 'port')
    workers = conf.getint('WEB', 'workers')

    if not os.environ.get("DEBUG"):
        webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")

    if os.path.exists('current_thread.txt'):
        os.remove('current_thread.txt')
    # loop='none' to 'make' it use asyncio.ProactorEventLoop
    # so we can use asyncio.create_subprocess_exec()
    uvicorn.run('app:app',
                host='0.0.0.0', port=port,
                workers=workers, loop='none')
