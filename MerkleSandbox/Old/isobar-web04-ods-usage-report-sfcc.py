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
import time
import logging
import requests
import urllib3
import xlsxwriter
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Set script name
scriptName = 'isobar-web04-ods-usage-report'

# Starting point of the time counter
scriptStartTime = time.perf_counter()

# Print current time
print(time.asctime(time.localtime(time.time())))

# Get date for yesterday and set it in format ISO 8601
yesterdayIs = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

# # Get date for today and set it in format ISO 8601
todayIs = datetime.today().strftime('%Y-%m-%d')

# Create and configure logger
print('Set logger')
logFormat = '%(levelname)s %(asctime)s - %(message)s'
scriptLogFile = f'{scriptName}-{todayIs}.log'
logging.basicConfig(filename=scriptLogFile,
                    level=logging.DEBUG,
                    format=logFormat)
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
        server.sendmail(email_sender, email_recipient, text)
        print('email sent')
        server.quit()
    except:
        print("SMPT server connection error")
        logger.debug("SMPT server connection error. Failed to send email")
    return True


# Create excel workbook and worksheet in workbook for today's report
workbook = xlsxwriter.Workbook(f'{scriptName}_{todayIs}.xlsx')
excel_file = f'{scriptName}_{todayIs}.xlsx'
worksheet = workbook.add_worksheet('Sandbox usage report')

# Add bold formatting
boldFormat = workbook.add_format({'bold': True})

# Add headers to excel worksheet with bold format
worksheetHeader = ['SandboxID', 'Realm', 'Instance', 'State', 'Created at', 'Created by', 'Minutes up since created',
                   'Minutes down since created', 'Total credits', 'Minutes up in last 24 hours',
                   'Minutes down in last 24 hours', 'Credits since 01.03.2021']
worksheet.write_row(0, 0, worksheetHeader, boldFormat)
logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

# Requesting access token with password credentials
logger.debug('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

accessTokenResponse = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                    verify=False,
                                    allow_redirects=False, auth=(client_id, client_secret))

try:
    accessToken = json.loads(accessTokenResponse.text)
except ValueError as value_error:
    logger.error(value_error)
    logger.debug('Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get authorization for access token in {scriptName}'
    email_text = f'Failed to get authorization for access token in {scriptName}. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

try:
    headers = {'Authorization': 'Bearer ' + accessToken['access_token']}
except KeyError as key_error:
    logger.error(key_error)
    logger.debug('Some of the credentials are invalid. Check them carefully')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Some of the credentials in cron job - {scriptName} are invalid'
    email_text = f'Failed to get access token in cron job - {scriptName}. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise
logger.debug('We got the access token')

# Make request to url for listing all ODS - Sandbox On Demand
log_and_print('First request endpoint - get list of all sandboxes')

try:
    sandboxList = requests.get(
        "https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes?include_deleted=false",
        headers=headers, verify=False).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox list')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get Sandbox lists in cron job - {scriptName}'
    email_text = f'Failed to get Sandbox lists in cron job - {scriptName}.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug(f'First request endpoint answer is {sandboxList}')

rowNumber = 1
columnNumber = 0
list2fill = []
for i in sandboxList['data']:
    realm = i['realm']
    realmName = ''
    if realm == 'aakr':  # Smenyash ID-to mezhdu kavichkite s tova na klienta, koito iskash da reportvash. ID-to se vzima ot https://wiki.isobarsystems.com/display/SUPTEAM/Local+POD+time+-+Notifications
        realmName = 'web04'  # Smenyash imeto mezhdu kavichkite s tova na klienta, koito iskash da reportvash.
        sandboxId = i['id']
        list2fill.append(sandboxId)
        list2fill.append(realmName)
        instance = i['instance']
        realmUrl = f'{realm}-{instance}.sandbox.us01.dx.commercecloud.salesforce.com'
        list2fill.append(realmUrl)
        state = i['state']
        list2fill.append(state)
        createdAt = i['createdAt']
        list2fill.append(createdAt)
        createdBy = i['createdBy']
        list2fill.append(createdBy)
        logger.debug(f'List to fill with parsed values from first request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since inception
        log_and_print('Second request endpoint - get Sandbox usage since inception')

        createDate = createdAt[:10]

        try:
            sandboxUsageSinceInception = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from={createDate}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from second request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = f'Failed to get Sandbox usage since inception in cron job - {scriptName}'
            email_text = f'Failed to get Sandbox usage since inception in cron job - {scriptName}. Check the attached logs'
            email_attachment = str(Path.cwd() / scriptLogFile)
            send_email(email_recipient, email_subject, email_text, email_attachment)

        logger.debug(f'Second request endpoint answer is {sandboxUsageSinceInception}')

        minutesUp = sandboxUsageSinceInception['data']['minutesUp']
        list2fill.append(minutesUp)
        minutesDown = sandboxUsageSinceInception['data']['minutesDown']
        list2fill.append(minutesDown)
        creditsSpentOnRealmAakr = minutesUp + (minutesDown * 0.3)
        list2fill.append(creditsSpentOnRealmAakr)
        logger.debug(f'List to fill with parsed values from second request endpoint is {list2fill}')

        # Make request with sandboxIDs to get each Sandbox usage since yesterday
        log_and_print('Third request endpoint - Sandbox usage since yesterday')

        try:
            sandboxUsageLast24 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from={yesterdayIs}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from third request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = f'Failed to get Sandbox usage for the last 24 hours in cron job - {scriptName}'
            email_text = f'Failed to get Sandbox usage for the last 24 hours in cron job - {scriptName}. Check the attached logs'
            email_attachment = str(Path.cwd() / scriptLogFile)
            send_email(email_recipient, email_subject, email_text, email_attachment)

        logger.debug(f'Third request endpoint answer is {sandboxUsageLast24}')

        minutesUpLast24 = sandboxUsageLast24['data']['minutesUp']
        list2fill.append(minutesUpLast24)
        minutesDownLast24 = sandboxUsageLast24['data']['minutesDown']
        list2fill.append(minutesDownLast24)
        logger.debug(f'List to fill with parsed values from third request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since 2021-03-01
        log_and_print('Fourth request endpoint - Sandbox usage since 2021-03-01')

        try:
            sandboxUsageOnRealmAakrSince2021_03_01 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from=2021-03-01",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from fourth request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = f'Failed to get Sandbox usage since 21.03.01. in cron job - {scriptName}'
            email_text = f'Failed to get Sandbox usage since 21.01.03. in cron job - {scriptName}. Check the attached logs'
            email_attachment = str(Path.cwd() / scriptLogFile)
            send_email(email_recipient, email_subject, email_text, email_attachment)

        logger.debug(f'Fourth request endpoint answer is {sandboxUsageOnRealmAakrSince2021_03_01}')

        realmAakrMinutesUp210301 = sandboxUsageOnRealmAakrSince2021_03_01['data']['minutesUp']
        realmAakrMinutesDown210301 = sandboxUsageOnRealmAakrSince2021_03_01['data']['minutesDown']
        creditsSpentOnRealmAakr = realmAakrMinutesUp210301 + (realmAakrMinutesDown210301 * 0.3)
        list2fill.append(creditsSpentOnRealmAakr)
        logger.debug(f'List to fill with parsed values from fourth request endpoint is {list2fill}')

        # Write the list with data to excel worksheet
        worksheet.write_row(rowNumber, columnNumber, list2fill)
        rowNumber += 1

        list2fill.clear()
        logger.debug(f'List to fill has been cleared - {list2fill}')
    else:
        list2fill.clear()

# Write data to Excel table, save and close
workbook.close()
logger.debug('Data has been written into the excel file')

# Get usage for realm aakr since 01.03.2021
log_and_print('Fifth request endpoint - get Sandbox usage on realm aakr since 2021-03-01')

try:
    sandboxUsageOnRealmAakrSince2021_03_01 = requests.get(
        f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/realms/aakr/usage?from=2021-03-01",
        headers=headers).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox usage on realm aakr from fifth request endpoint')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get Sandbox usage on realm aakr since 21.03.01 in cron job - {scriptName}'
    email_text = f'Failed to get Sandbox usage on realm aakr since 21.03.01 in cron job - {scriptName}. Check the attached logs'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)

logger.debug(f'Fifth request endpoint answer is {sandboxUsageOnRealmAakrSince2021_03_01}')

realmAakrMinutesUp210301 = sandboxUsageOnRealmAakrSince2021_03_01['data']['minutesUp']
realmAakrMinutesDown210301 = sandboxUsageOnRealmAakrSince2021_03_01['data']['minutesDown']
creditsSpentOnRealmAakr = realmAakrMinutesUp210301 + (realmAakrMinutesDown210301 * 0.3)
log_and_print(creditsSpentOnRealmAakr)

# Convert Excel to pandas dataframe
df = pd.read_excel(excel_file)
dataFrame = pd.DataFrame(df)
logger.debug('Data has been transformed from excel to pandas dataframe')

# Sort Pandas dataframe by column 'CreatedAt'
dataFrame.sort_values(by=['Created at'], inplace=True, ascending=False)

# Add row with total credits spend on realm
lastDataframeRow = {'SandboxID': '', 'Realm': '', 'Instance': '', 'State': '', 'Created at': '', 'Created by': '', 'Minutes up since created': '', 'Minutes down since created': '', 'Total credits': '', 'Minutes up in last 24 hours': '', 'Minutes down in last 24 hours': '', 'Credits since 01.03.2021': creditsSpentOnRealmAakr}
dataFrame = dataFrame.append(lastDataframeRow, ignore_index=True)

# Convert pandas to html, remove index column and allign to center
html = dataFrame.to_html(index=False)
html2Attach = html.replace('<tr>', '<tr align="center">')
logger.debug('Data has been transformed from pandas dataframe to html with index column removed')

# Ending point of the time counter
scriptFinishTime = time.perf_counter()
log_and_print(f'Script execution time is {round(scriptFinishTime - scriptStartTime, 2)} seconds. Keep in mind there will be around 0,5 seconds difference between this time and what will be received in email as execution time')

# Add text to the email
emailText = f'Hi Team. My name is {scriptName}. Please check the overview for today. Keep in mind that living sandboxes on demand are spending credits. Each minute uptime = 1 credit. And each minute down time = 0.3 credit. If you have any questions, please do not hesitate to contact Merkle Operations Support.'

email_recipient = 'konstantin.yanev@isobar.com'
email_subject = 'Merkle Web04 ODS update for today'
email_text = emailText + html2Attach
email_attachment = str(Path.cwd() / excel_file)
send_email(email_recipient, email_subject, email_text, email_attachment)

# Print current time
print(time.asctime(time.localtime(time.time())))