import webbrowser
from multiprocessing import freeze_support

import uvicorn

import utils

if __name__ == '__main__':
    freeze_support()
    port = 6080
    # noinspection HttpUrlsUsage
    webbrowser.open_new_tab(f"http://{utils.get_ipv4_address()}:{port}")
    # workers=5 to increase performance and loop='none' to 'make' it use
    # asyncio.ProactorEventLoop so we can use asyncio.create_subprocess_exec()
    uvicorn.run('app:app', host='0.0.0.0', port=port, workers=5, loop='none')
