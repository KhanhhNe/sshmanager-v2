import os
import shutil
import zipfile

import PyInstaller.__main__

app_name = os.path.basename(os.getcwd())
dist_path = 'app_dist'

PyInstaller.__main__.run([
    'main.py', f'--name={app_name}', '--icon=public/favicon.ico',
    f'--distpath={dist_path}', '--onedir', '--noconfirm',
    '--add-binary=executables/*;executables',
    '--add-binary=api-ms-win-core-path-l1-1-0.dll;.', # Win 7 compatibility
    '--hidden-import=app',
    '--hidden-import=pony.orm.dbproviders',
    '--hidden-import=pony.orm.dbproviders.sqlite',
    '--hidden-import=websockets.legacy',
    '--hidden-import=websockets.legacy.server',
])

shutil.copytree('dist', f"{dist_path}/{app_name}/dist", dirs_exist_ok=True)

print("Zipping files...")
built_file = zipfile.ZipFile(f'{app_name}.zip', 'w')

os.chdir('app_dist')
for folder, _, filenames in os.walk(app_name):
    for filename in filenames:
        filepath = os.path.join(folder, filename)
        print(f"Zipping {filepath}")
        built_file.write(filepath)
os.chdir('..')

print("Done!")
