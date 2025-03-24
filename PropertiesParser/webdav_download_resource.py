import os
import time
import shutil
import urllib3
from pathlib import Path
from datetime import datetime
from webdav3.client import Client as webdavClient


source_url = 'https://development-eu01-biocodex.demandware.net/on/demandware.servlet/webdav/Sites/Dynamic/SymbiosysFR'
username = 'konstantin.yanev@isobar.com'
password = 'D4t1g0n4p1n46'

folder_name = 'resources'
os.mkdir(folder_name)

urllib3.disable_warnings()

options = {
    'webdav_hostname': source_url,
    'webdav_login': username,
    'webdav_password': password,
    'webdav_timeout': 300
}

webdav = webdavClient(options)
webdav.verify = False

print('Start downloading dev_folder folder from WebDav')
webdav_download_start = time.perf_counter()

try:
    webdav.download_directory(folder_name, folder_name)
except:
    raise

webdav_download_end = time.perf_counter()
print(f'Finished downloading dev_folder folder from WebDav in {source_url}')
print(f'Resource folder downloaded for {round(webdav_download_end - webdav_download_start, 2)} seconds.')

current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
backup_folder = f'BackupFolder_{current_time}'
os.mkdir(backup_folder)
subfolder2_remove = '.history'
dev_folder = 'dev_folder'

# Remove .history subfolder if it exists
print('Remove subfolder .history if exists')
dir_path = Path(folder_name, subfolder2_remove)
if dir_path.exists() and dir_path.is_dir():
    shutil.rmtree(dir_path)

shutil.copytree(folder_name, backup_folder, dirs_exist_ok=True)
zip_archive = f'backupFolder_{current_time}'
shutil.make_archive(backup_folder, 'zip', zip_archive)
shutil.rmtree(f'./{zip_archive}')
