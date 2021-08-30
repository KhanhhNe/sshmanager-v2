from multiprocessing import freeze_support

import uvicorn

if __name__ == '__main__':
    freeze_support()
    uvicorn.run('app:app', reload=True)
