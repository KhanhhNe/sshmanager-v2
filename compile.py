import os
import zipfile

import PyInstaller.__main__

app_name = os.path.basename(os.getcwd())
dist_path = 'app_dist'

##if os.path.exists(dist_path):
##    shutil.rmtree(dist_path)


PyInstaller.__main__.run([
    'main.py', f'--name={app_name}', '--icon=public/favicon.ico',
    f'--distpath={dist_path}', '--onedir', '--noconfirm', '--clean',
    '--add-binary=dist/*;dist',
    '--add-binary=executables/*;executables',
    '--hidden-import=app',
    '--hidden-import=pony.orm.dbproviders',
    '--hidden-import=pony.orm.dbproviders.sqlite',
    '--hidden-import=websockets.legacy',
    '--hidden-import=websockets.legacy.server',
])

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
