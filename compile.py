import json
import os
import shutil
import subprocess
import zipfile

import PyInstaller.__main__

app_name = os.path.basename(os.getcwd()).replace('-v2', '')
version = json.load(open('package.json', encoding='utf-8'))['version']
web_dist = 'build/web_dist'
work_path = 'build/pyinstaller'
dist_path = 'build/dist'

shutil.rmtree(dist_path, ignore_errors=True)
shutil.rmtree(work_path, ignore_errors=True)
completed = subprocess.run('npm run build', shell=True)
if completed.returncode:
    print("NPM build failed!")
    exit()

PyInstaller.__main__.run([
    'main.py', f'--name={app_name}', '--icon=public/favicon.ico',
    f'--distpath={dist_path}/{app_name}', f'--workpath={work_path}', '--onefile', '--noconfirm',

    '--hidden-import=app',

    # PonyORM and SQLite
    '--hidden-import=pony.orm.dbproviders',
    '--hidden-import=pony.orm.dbproviders.sqlite',

    # Websockets
    '--hidden-import=websockets.legacy',
    '--hidden-import=websockets.legacy.server',
])

shutil.copy('package.json', f"{dist_path}/{app_name}")
shutil.copy('logging_config.json', f"{dist_path}/{app_name}")
shutil.copytree('executables', f"{dist_path}/{app_name}/executables", dirs_exist_ok=True)
shutil.copytree(web_dist, f"{dist_path}/{app_name}/web", dirs_exist_ok=True)

print("Zipping files...")

current_dir = os.getcwd()
os.chdir(dist_path)
dist_file = zipfile.ZipFile(f'{app_name}-v{version}.zip', 'w')

for folder, _, filenames in os.walk(app_name):
    for filename in filenames:
        filepath = os.path.join(folder, filename)
        print(f"Zipping {filepath}")
        dist_file.write(filepath)

os.chdir(current_dir)

if os.path.exists(f"{app_name}.spec"):
    os.remove(f"{app_name}.spec")

print("Done!")
