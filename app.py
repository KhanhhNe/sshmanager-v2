import json
import os.path
import zipfile
from io import BytesIO

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from models import init_db
from views import ports_api, settings_api, ssh_api

os.environ['PATH'] += ';executables'

package_data = json.load(open('package.json', encoding='utf-8'))
app = FastAPI(title="SSHManager by KhanhhNe",
              description=package_data['description'],
              version=package_data['version'])


@app.on_event("startup")
def app_init():
    init_db()


@app.get('/api/debug-zip')
def get_debug_file():
    bytes_io = BytesIO()
    zip_file = zipfile.ZipFile(bytes_io, 'w')
    for filename in os.listdir('data'):
        zip_file.write(f'data/{filename}', filename)
    zip_file.close()
    return Response(content=bytes_io.getvalue(), media_type='application/zip')


# Routers
app.include_router(ssh_api.router, prefix='/api/ssh')
app.include_router(ports_api.router, prefix='/api/ports')
app.include_router(settings_api.router, prefix='/api/settings')

static_dir = next(filter(os.path.exists, ['web', 'build/web_dist']))
app.mount('/', StaticFiles(directory=static_dir, html=True, check_dir=False))
