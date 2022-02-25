import json
import os
import shutil
import subprocess
import zipfile

import PyInstaller.__main__

app_name = os.path.basename(os.getcwd()).replace('-v2', '')
version = json.load(open('package.json', encoding='utf-8'))['version']
dist_path = 'app_dist'

shutil.rmtree('dist', ignore_errors=True)
shutil.rmtree('app_dist', ignore_errors=True)
completed = subprocess.run('npm run build', shell=True)
if completed.returncode:
    print("NPM build failed!")
    exit()

PyInstaller.__main__.run([
    'main.py', f'--name={app_name}', '--icon=public/favicon.ico',
    f'--distpath={dist_path}', '--onedir', '--noconfirm',
    '--add-data=package.json;.',
    '--add-binary=executables/*;executables',
    '--hidden-import=app',
    '--hidden-import=pony.orm.dbproviders',
    '--hidden-import=pony.orm.dbproviders.sqlite',
    '--hidden-import=websockets.legacy',
    '--hidden-import=websockets.legacy.server',
])

shutil.copytree('dist', f"{dist_path}/{app_name}/dist", dirs_exist_ok=True)

print("Zipping files...")
built_file = zipfile.ZipFile(f'{app_name}-v{version}.zip', 'w')

os.chdir(dist_path)
for folder, _, filenames in os.walk(app_name):
    for filename in filenames:
        filepath = os.path.join(folder, filename)
        print(f"Zipping {filepath}")
        built_file.write(filepath)
os.chdir('..')

print("Done!")
