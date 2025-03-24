# "I find your lack of faith disturbing"

import json
import time
import logging
import requests
import urllib3
import os.path
import smtplib
import slack_sdk
from email import encoders
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

# Set script name
scriptName = 'stop-multiple-ods-daily'

# Get date for today and set it in format ISO 8601
todayIs = datetime.today().strftime('%Y-%m-%d')

# Create and configure logger
logFormat = '%(levelname)s %(asctime)s - %(message)s'
scriptLogFile = f'{scriptName}-{todayIs}.log'
logging.basicConfig(filename=scriptLogFile,
                    level=logging.DEBUG,
                    format=logFormat)
logger = logging.getLogger()


def log_and_print(text):
    print(text)
    logger.debug(text)


# Disable warnings
urllib3.disable_warnings()

# Get credentials from env variables and store in local vars
log_and_print('Request credentials from globvars')
slack_token = os.getenv('SLACK_BOT')
client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
log_and_print('We got the credentials')


# Set function to push slack messages
def slack_post(slack_message):
    try:
        slack_channel = '#stop-multiple-ods-daily'
        slack_client = slack_sdk.WebClient(token=slack_token)
        slack_client.chat_postMessage(channel=slack_channel, text=slack_message)
    except BaseException as e:
        log_and_print(e)
        raise


# Set function for sending emails with attachment, text and html
def send_email(email_recipient,
               email_subject,
               email_message,
               attachment_location=''):
    email_sender = ods_email

    email = MIMEMultipart()
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
        server.sendmail(email_sender, email_recipient, text)
        print('email sent')
        server.quit()
    except BaseException as exc:
        log_and_print(f' {exc} SMPT server connection error. Failed to send email')
        slack_post(f'SMPT server connection error. Failed to send email in {scriptName}')
        raise


# Requesting access token with password credentials
log_and_print('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

accessTokenResponse = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                    verify=False,
                                    allow_redirects=False, auth=(client_id, client_secret))

try:
    accessToken = json.loads(accessTokenResponse.text)
except ValueError as value_error:
    logger.debug('Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    slack_post(f'Failed to get authorization for access token in {scriptName}. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    raise

try:
    headers = {'Authorization': 'Bearer ' + accessToken['access_token']}
except KeyError as key_error:
    logger.debug('Some of the credentials are invalid. Check them carefully')
    slack_post(f'Failed to get access token in cron job - {scriptName}. Some of the credentials are invalid. Check them carefully.')
    raise
log_and_print('We got the access token')

log_and_print('Stop sandboxes begin')

sandboxes_list = (
    '1f170acc-4230-4284-b761-1f4359653c21', '1f096dc6-28de-4c40-a40f-e6121f7dca0d', '0fd31572-27a6-43bf-9367-78abdb37145e',
    'f92a72ee-698a-4838-a166-436ec598e34f', 'fb6c93f7-48af-4ed7-857d-fee8dee130a7', '4d49f2c1-3dd1-4209-bc9c-3566b46ffac7',
    '72e4088e-e349-4004-a98d-8d217cbe27a0', '27f3029c-2dc7-42a1-85f8-4fe708cd3deb', '6ebea269-6f57-48fb-8ec0-bc5286ebe9f1',
    '0a919829-c5cf-4ec4-9517-d5b995721bbc', '2b3a4b58-33c0-4d57-a75a-8b7de30402ab', '45dea6d9-7cec-46e3-a78c-05b5e9619513',
    '180407d7-0f52-4f48-b003-75ae6eb6fc42', '62d1f71f-2f73-4053-a647-d94e1fd1b54b', 'efabe172-b138-4274-b4b7-fa27996b4ef1',
    '064156e6-93cc-4647-a0ac-00c697009985', 'e1784001-f091-4f67-ab08-5ce2891c5326', '7a6b4339-1101-4c61-a733-10e78696b976',
    'ce378498-8c3d-437a-b973-fd9420d420f5', '53cdf077-a461-4371-8281-48f8ea9a04bf', 'f7edb621-aae1-426e-aa82-28b98e81f04b'
)

for sandbox_id in sandboxes_list:

    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + accessToken['access_token'],
        'Content-Type': 'application/json',
    }

    data = '{"operation": "stop"}'

    try:
        stopSandbox = requests.post(
            f'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/operations',
            headers=headers, data=data).json()

    except Exception as e:
        print(e)
        log_and_print(f'Sandbox stop operation  for {sandbox_id} in {scriptName} failed')
        slack_post(f'Sandbox stop operation  for {sandbox_id} in {scriptName} failed')
        raise
    log_and_print(f'Stop sandbox api endpoint answer is {stopSandbox}')
    log_and_print('Wait 10 seconds')
    time.sleep(10)

email_recipient = 'konstantin.yanev@isobar.com'
email_subject = scriptName
email_text = f'Hi Team. My name is {scriptName}. All ods are stopped. Please double check.'
send_email(email_recipient, email_subject, email_text)
