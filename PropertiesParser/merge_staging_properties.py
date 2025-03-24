# “The Force is not a power you have. It’s not about lifting rocks.
# It’s the energy between all things, a tension, a balance, that binds the Universe together.”

import os
import smtplib
import time
from datetime import datetime
import urllib3
from webdav3.client import Client as webdavClient
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
import shutil
import glob

# Set script name
script_name = 'merge-staging-properties'

# Starting point of the time counter
script_start_time = time.perf_counter()
#
# Get date for today and set it in format ISO 8601
today_is = datetime.today().strftime('%Y-%m-%d')

# Create and configure logger
print('Set logger')
log_format = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{today_is}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

# Disable warnings
urllib3.disable_warnings()


def log_and_print(text):
    print(text)
    logger.debug(text)


# Set function for sending emails with attachment, text and html
def send_email(recipient,
               subject,
               email_message,
               attachment_location=''):
    email_sender = ods_email

    email = MIMEMultipart()
    email['From'] = ods_email
    email['To'] = recipient
    email['Subject'] = subject

    email.attach(MIMEText(email_message, 'html'))

    if attachment_location != '':
        filename = os.path.basename(attachment_location)
        attachment = open(attachment_location, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        "attachment; filename= %s" % filename)
        email.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(ods_email, ods_pass)
        text = email.as_string()
        server.sendmail(email_sender, recipient, text)
        print('email sent')
        server.quit()
    except Exception as exc:
        log_and_print(f'SMPT server connection error. Failed to send email{exc}')


# Get credentials from global variables. Keep in mind that getting them on Linux has slightly different syntax
log_and_print('Request credentials from globvars')
client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
log_and_print('We got the credentials')

# Set dev_folder URL, local and remote folder name and create local folder and backup folder
log_and_print('Set dev_folder URL, local and remote folder name and create local folder and backup folder')
source_url = 'https://aaay-003.sandbox.us01.dx.commercecloud.salesforce.com/on/demandware.servlet/webdav/Sites/Dynamic/zwilling-ca'
folder_name = 'resource'
os.mkdir(folder_name)
current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

# WebDav setup
log_and_print('Setup WebDav Options')
options = {
    'webdav_hostname': source_url,
    'webdav_login': username,
    'webdav_password': password,
    'webdav_timeout': 300
}
webdav = webdavClient(options)
webdav.verify = False
log_and_print('Start downloading dev_folder folder from WebDav')
print(time.asctime(time.localtime(time.time())))
webdav_download_start = time.perf_counter()

try:
    webdav.download_directory(folder_name, folder_name)
except:
    log_and_print(f'PropertiesParser download in {script_name} failed')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'PropertiesParser download in {script_name} failed'
    email_text = f'PropertiesParser download in {script_name} failed'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

webdav_download_end = time.perf_counter()
log_and_print(f'Finished downloading dev_folder folder from WebDav in {source_url}')
print(time.asctime(time.localtime(time.time())))
log_and_print(f'Resource folder downloaded for {round(webdav_download_end - webdav_download_start, 2)} seconds.')

output_folder = 'OutputFolder'
os.mkdir(output_folder)
backup_folder = f'BackupFolder_{current_time}'
os.mkdir(backup_folder)
subfolder2_remove = '.history'
dev_folder = 'Release'

# Remove .history subfolder if it exists
log_and_print('Remove subfolder .history if exists')
dir_path = Path(folder_name, subfolder2_remove)
if dir_path.exists() and dir_path.is_dir():
    shutil.rmtree(dir_path)

# Copy content of downloaded folder to back up folder
log_and_print('Copy content of downloaded folder to backup folder')
shutil.copytree(folder_name, backup_folder, dirs_exist_ok=True)
log_and_print('Zip backup folder and delete it')
zip_archive = f'backupFolder_{current_time}'
shutil.make_archive(backup_folder, 'zip', zip_archive)
shutil.rmtree(f'./{zip_archive}')

# log_and_print('Create a dictionary with file names as keys and for each file name their paths')
file_paths = {}
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.properties'):
            if f not in file_paths:
                file_paths[f] = []
            file_paths[f].append(root)

log_and_print(
    'Concatenate the content of the files in each directory and write the merged content into a file with the same name at the current working directory')
for file, paths in file_paths.items():
    properties = []
    for path in paths:
        with open(os.path.join(path, file)) as file_object:
            properties.append(file_object.read())
    with open(file, 'a') as file3:
        file3.write('\n'.join(properties))

# Move all appended files to Output folder
log_and_print('Move all appended files to Output folder')
for property_file in glob.iglob('*.properties'):
    shutil.move(property_file, output_folder)

# Remove 'dev_folder' local folder
log_and_print(f'Remove {folder_name} local folder')
shutil.rmtree(folder_name)

# Send email for job success with log attached
email_recipient = 'konstantin.yanev@isobar.com'
email_subject = f'{script_name} job has been completed successfully'
email_text = f'{script_name} job has been completed successfully'
email_attachment = str(Path.cwd() / script_log_file)
send_email(email_recipient, email_subject, email_text, email_attachment)
