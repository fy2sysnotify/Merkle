# "A long time ago in a galaxy far, far away"

import os
import glob
import shutil
from datetime import datetime

# Setting value for current date
todayIs = datetime.today().strftime('%Y-%m-%d')

# Making archive of all files in base directory - destination directory+filename, archive type, base directory
shutil.make_archive(f'OdsUsageReports_{todayIs}', 'zip', 'C://Backups//ODS_DB_DUMP')
shutil.move(f'OdsUsageReports_{todayIs}.zip', 'C://Backups//ODS_DB_DUMP')

# Deleting all sql files in base directory
filesToRemove = glob.glob('C://Backups//ODS_DB_DUMP//*.sql')
for file in filesToRemove:
    os.remove(file)
