import json
import os.path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from views import ports_api, settings_api, ssh_api

os.environ['PATH'] += ';executables'


package_data = json.load(open('package.json', encoding='utf-8'))
app = FastAPI(title="SSHManager by KhanhhNe",
              description=package_data['description'],
              version=package_data['version'])


# Routers
app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')
app.mount('/', StaticFiles(directory='dist', html=True, check_dir=False))
