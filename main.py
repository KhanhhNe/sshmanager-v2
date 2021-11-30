import os
from multiprocessing import freeze_support

import uvicorn

import config

if __name__ == '__main__':
    freeze_support()
    conf = config.get_config()
    port = conf.getint('WEB', 'port')
    workers = conf.getint('WEB', 'workers')

    if os.path.exists('current_thread.txt'):
        os.remove('current_thread.txt')

    # noinspection HttpUrlsUsage
    # webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")
    # loop='none' to 'make' it use asyncio.ProactorEventLoop
    # so we can use asyncio.create_subprocess_exec()
    uvicorn.run('app:app',
                host='0.0.0.0', port=port,
                workers=workers, loop='none')
