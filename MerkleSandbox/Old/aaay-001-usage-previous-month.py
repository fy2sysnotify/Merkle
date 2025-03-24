# "Size matters not. Look at me. Judge me by my size, do you? Hmm? Hmm. And well you should not. For my ally is the Force
# and a powerful ally it is. Life creates it, makes it grow. Its energy surrounds us and binds us. Luminous beings are we,
# not this crude matter. You must feel the Force around you; here, between you, me, the tree, the rock, everywhere, yes.
# Even between the land and the ship."

import os.path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import logging
import requests
import urllib3
import xlsxwriter
import pandas as pd
from pathlib import Path
import dateutil.relativedelta
import datetime

# Set script name
script_name = 'aaay-001-usage-previous-month'

# sandbox Id to be used for reporting
sandbox_id = '82a4552f-7e6a-4241-8c4a-275d148e0141'

row_number = 1
column_number = 0
list2fill = []

# Get date for today, but last month and set it in format ISO 8601
last_month = datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)
usage_start_date = last_month.strftime('%Y-%m-%d')

# # Get date for today and set it in format ISO 8601
today_is = datetime.datetime.now().strftime('%Y-%m-%d')

# Create and configure logger
log_format = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{today_is}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

# Disable warnings
urllib3.disable_warnings()

# Get credentials from env variables and store in local vars
logger.debug('Request credentials from globvars')
client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
logger.debug('We got the credentials')


def log_and_print(text):
    print(text)
    logger.debug(text)


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
    except Exception as e:
        log_and_print(f'SMPT server connection error. Failed to send email. {e}')
    return True


# Create excel workbook and worksheet in workbook for today's report
workbook = xlsxwriter.Workbook(f'{script_name}_{today_is}.xlsx')
excel_file = f'{script_name}_{today_is}.xlsx'
worksheet = workbook.add_worksheet('Sandbox usage report')

# Add bold formatting
bold_format = workbook.add_format({'bold': True})

# Add headers to excel worksheet with bold format
worksheetHeader = ['SandboxID', 'Minutes up for previous month', 'Minutes down for previous month', 'Credits for previous month']
worksheet.write_row(0, 0, worksheetHeader, bold_format)
logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

# Requesting access token with password credentials
logger.debug('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

access_token_response = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                      verify=False,
                                      allow_redirects=False, auth=(client_id, client_secret))

try:
    access_token = json.loads(access_token_response.text)
except ValueError as value_error:
    logger.error(value_error)
    logger.debug('Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get authorization for access token in {script_name}'
    email_text = f'Failed to get authorization for access token in {script_name}. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

try:
    headers = {'Authorization': 'Bearer ' + access_token['access_token']}
except KeyError as key_error:
    logger.error(key_error)
    logger.debug('Some of the credentials are invalid. Check them carefully')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Some of the credentials in cron job - {script_name} are invalid'
    email_text = f'Failed to get access token in cron job - {script_name}. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug('We got the access token')

# Make request to url for previous month usage with sandbox Id and start date = today - 1 month
log_and_print('Make request to url for previous month usage with sandbox Id and start date = today - 1 month')

try:
    last_month_usage = requests.get(
        f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={usage_start_date}",
        headers=headers).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox usage for the last month from api')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get Sandbox usage in cron job - {script_name}'
    email_text = f'Failed to get Sandbox usage in cron job - {script_name}. Check the attached logs'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug(f'Fourth request endpoint answer is {last_month_usage}')

minutes_up_last_month = last_month_usage['data']['minutesUp']
minutes_down_last_month = last_month_usage['data']['minutesDown']
credits_spent_last_month = minutes_up_last_month + (minutes_down_last_month * 0.3)

list2fill.append(sandbox_id)
list2fill.append(minutes_up_last_month)
list2fill.append(minutes_down_last_month)
list2fill.append(credits_spent_last_month)

# Write the list with data to excel worksheet
worksheet.write_row(row_number, column_number, list2fill)
row_number += 1

list2fill.clear()
logger.debug(f'List to fill has been cleared - {list2fill}')

# Write data to Excel table, save and close
workbook.close()
logger.debug('Data has been written into the excel file')

# Convert Excel to pandas dataframe
df = pd.read_excel(excel_file)
data_frame = pd.DataFrame(df)
logger.debug('Data has been transformed from excel to pandas dataframe')

# Add row with total credits spend on realm
last_dataframe_row = {'SandboxID': '', 'Minutes up for previous month': '', 'Minutes down for previous month': '', 'Credits for previous month': ''}

# Convert pandas to html, remove index column and allign to center
html = data_frame.to_html(index=False)
html2_attach = html.replace('<tr>', '<tr align="center">')
logger.debug('Data has been transformed from pandas dataframe to html with index column removed')

# Add text to the email
emailText = f'Hi Team. My name is {script_name}. Please check Sandbox ID {sandbox_id} usage for the previous month. Keep in mind that living sandboxes on demand are spending credits. Each minute uptime = 1 credit. And each minute down time = 0.3 credit. If you have any questions, please do not hesitate to contact Isobar Operations Support.'

email_recipient = 'kosyoyanev@gmail.com'
email_subject = f'SandboxId {sandbox_id} usage for previous month'
email_text = emailText + html2_attach
email_attachment = str(Path.cwd() / excel_file)
send_email(email_recipient, email_subject, email_text, email_attachment)
