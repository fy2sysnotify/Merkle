# The Dark side of the Force is a pathway to many abilities some consider to be unnatural."

import requests
import json
import logging
import time
from pathlib import Path
import os.path
import smtplib
import urllib3
import xlsxwriter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Set script name
script_name = 'upskill-sfcc-ods-list'

greeting = 'Hi Team'

# Starting point of the time counter
script_start_time = time.perf_counter()

# # Get date for today and set it in format ISO 8601
today_is = datetime.today().strftime('%Y-%m-%d')

# Create and configure logger
logFormat = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{today_is}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=logFormat)
logger = logging.getLogger()

# Disable warnings
urllib3.disable_warnings()


def log_and_print(text):
    print(text)
    logger.debug(text)


# Get credentials from env variables and store in local vars
log_and_print('Request credentials from globvars')
client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
slack_token = os.getenv('SLACK_BOT')
log_and_print('We got the credentials')


# Set function for sending emails with attachment, text and html
def send_email(email_recipient,
               email_subject,
               email_message,
               attachment_location=''):
    email_sender = ods_email

    email = MIMEMultipart()
    email_cc = 'konstantin.yanev@isobar.com'
    email['From'] = ods_email
    email['To'] = email_recipient
    email['Subject'] = email_subject

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
        server.sendmail(email_sender, [email_recipient, email_cc], text)
        print('email sent')
        server.quit()
    except:
        print("SMPT server connection error")
        logger.debug("SMPT server connection error. Failed to send email")
    return True


# Create excel workbook and worksheet in workbook for today's report
workbook = xlsxwriter.Workbook(f'{script_name}_{today_is}.xlsx')
excel_file = f'{script_name}_{today_is}.xlsx'
worksheet = workbook.add_worksheet('Academy ODS List')

# Add bold formatting
boldFormat = workbook.add_format({'bold': True})

# Add headers to excel worksheet with bold format
worksheetHeader = ['SandboxID', 'Realm', 'Instance', 'Resource profile', 'State', 'Created at', 'Created by', 'Host name', 'Business Manager']
worksheet.write_row(0, 0, worksheetHeader, boldFormat)
logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

# Requesting access token with password credentials
log_and_print('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

access_token_response = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                      verify=False,
                                      allow_redirects=False, auth=(client_id, client_secret))

try:
    access_token = json.loads(access_token_response.text)
except ValueError as value_error:
    log_and_print(value_error)
    log_and_print(
        'Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get authorization for access token in {script_name} job'
    email_text = f'Failed to get authorization for access token in {script_name} job. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    log_and_print('email with error sent')
    raise

try:
    headers = {'Authorization': 'Bearer ' + access_token['access_token']}
except KeyError as key_error:
    log_and_print(key_error)
    log_and_print('Some of the credentials are invalid. Check them carefully')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Some of the credentials in {script_name} job are invalid'
    email_text = f'Failed to get access token in {script_name} job. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    log_and_print('email with error sent')
    raise
log_and_print('We got the access token')


realm_id = 'aaay'
ttl = 0

create_json = {
    "realm": realm_id,
    "ttl": ttl,
    "settings": {
        "ocapi": [
            {
                "client_id": client_id,
                "resources": [
                    {
                        "resource_id": "/**",
                        "methods": [
                            "get",
                            "post",
                            "put",
                            "patch",
                            "delete"
                        ],
                        "read_attributes": "(**)",
                        "write_attributes": ""
                    }
                ]
            }
        ],
        "webdav": [
            {
                "client_id": client_id,
                "permissions": [
                    {
                        "path": "/cartridges",
                        "operations": [
                            "read_write"
                        ]
                    },
                    {
                        "path": "/impex",
                        "operations": [
                            "read_write"
                        ]
                    }
                ]
            }
        ]
    }
}

row_number = 1
column_number = 0
new_sandbox = []

for _ in range(21):

    # Make request to url for creating new sandbox
    log_and_print('Request endpoint - create new sandbox')
    create_new_sandbox = requests.post('https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes',
                                       headers=headers, verify=False, json=create_json).json()
    log_and_print(f'First request endpoint answer is {create_new_sandbox}')

    # Extract all data from returned dictionary
    sandbox_id = create_new_sandbox['data']['id']
    new_sandbox.append(sandbox_id)
    realm = create_new_sandbox['data']['realm']
    new_sandbox.append(realm)
    instance = create_new_sandbox['data']['instance']
    new_sandbox.append(instance)
    resource_profile = create_new_sandbox['data']['resourceProfile']
    new_sandbox.append(resource_profile)
    state = create_new_sandbox['data']['state']
    new_sandbox.append(state)
    created_at = create_new_sandbox['data']['createdAt']
    new_sandbox.append(created_at)
    created_by = create_new_sandbox['data']['createdBy']
    new_sandbox.append(created_by)
    ods_hostname = create_new_sandbox['data']['hostName']
    new_sandbox.append(ods_hostname)
    bm = create_new_sandbox['data']['links']['bm']
    new_sandbox.append(bm)
    ocapi = create_new_sandbox['data']['links']['ocapi']
    impex = create_new_sandbox['data']['links']['impex']
    code = create_new_sandbox['data']['links']['code']
    logs = create_new_sandbox['data']['links']['logs']

    # Write the list with data to excel worksheet
    worksheet.write_row(row_number, column_number, new_sandbox)
    row_number += 1

    # Clear list in order to be filled on the next round
    new_sandbox.clear()
    logger.debug(f'List to fill has been cleared - {new_sandbox}')

    time.sleep(10)

# Write data to Excel table, save and close
workbook.close()
log_and_print('Data has been written into the excel file')

script_finish_time = time.perf_counter()
log_and_print(
    f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds. Keep in mind there will be around 0,5 seconds difference between this time and what will be received in email as execution time')

email_recipient = 'oggie.astardzhiev@isobar.com'
email_subject = script_name
email_text = f'Hi Team. My name is {script_name}. I am sending you Excel file with ods info.'
email_attachment = str(Path.cwd() / excel_file)
send_email(email_recipient, email_subject, email_text, email_attachment)

# Print current time
print(time.asctime(time.localtime(time.time())))
