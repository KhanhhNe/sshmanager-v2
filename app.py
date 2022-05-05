import json
import logging
import os.path
import time

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from views import ports_api, settings_api, ssh_api

os.environ['PATH'] += ';executables'


package_data = json.load(open('package.json', encoding='utf-8'))
app = FastAPI(title="SSHManager by KhanhhNe",
              description=package_data['description'],
              version=package_data['version'])


# Middlewares
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger('Request')
    start_time = time.perf_counter()

    response: Response = await call_next(request)

    process_time = "{:5.2f}".format((time.perf_counter() - start_time) * 1000)
    query = request.url.query
    if query:
        query = '?' + query
    logger.info(f"{request.method} {response.status_code} ({process_time}ms) - "
                f"{request.url.path}{query}")

    return response


# Routers
app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')
app.mount('/', StaticFiles(directory='dist', html=True, check_dir=False))
