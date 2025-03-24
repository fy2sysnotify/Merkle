# "I've been waiting for you, Obi-Wan. We meet again, at last.
# The circle is now complete. When I left you, I was but the learner.
# Now I am the master."

import json
import time
import os.path
import smtplib
import logging
import urllib3
import requests
import mysql.connector
from pathlib import Path
from email import encoders
from datetime import datetime, timedelta
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set script name
scriptName = 'isobar-web-ods-usage-2db'

# Starting point of the time counter
scriptStartTime = time.perf_counter()

# Print current time
print(time.asctime(time.localtime(time.time())))

# Get date for yesterday and set it in format ISO 8601
yesterdayIs = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

# Get date for today and set it in format ISO 8601
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
        log_and_print('email sent')
        server.quit()
    except:
        log_and_print("SMPT server connection error. Failed to send email")
    return True


# Requesting access token with password credentials
log_and_print('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

accessTokenResponse = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                    verify=False,
                                    allow_redirects=False, auth=(client_id, client_secret))

try:
    accessToken = json.loads(accessTokenResponse.text)
except ValueError as value_error:
    logger.error(value_error)
    log_and_print('Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get authorization for access token in {scriptName}'
    email_text = f'Failed to get authorization for access token in {scriptName}. Check with VPN if virtual machine (https://asofivcenter01.srv.ecm/ui/) is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.'
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
    log_and_print('Failed to get Sandbox list')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get Sandbox lists in cron job - {scriptName}'
    email_text = f'Failed to get Sandbox lists in cron job - {scriptName}.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

log_and_print(f'First request endpoint answer is {sandboxList}')

dataForDB = []
for i in sandboxList['data']:
    realm = i['realm']
    realmName = ''
    if realm == 'aaay':  # Smenyash ID-to mezhdu kavichkite s tova na klienta, koito iskash da reportvash. ID-to se vzima ot https://wiki.isobarsystems.com/display/SUPTEAM/Local+POD+time+-+Notifications
        realmName = 'web'  # Smenyash imeto mezhdu kavichkite s tova na klienta, koito iskash da reportvash.
        sandboxId = i['id']
        timeStamp = datetime.now()
        timeStamp = timeStamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        list2fill = []
        list2fill.append(timeStamp)
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
            sandboxUsageSinceCreated = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from={createDate}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            log_and_print('Failed to get Sandbox usage from second request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = f'Failed to get Sandbox usage since inception in cron job - {scriptName}'
            email_text = f'Failed to get Sandbox usage since inception in cron job - {scriptName}. Check the attached logs'
            email_attachment = str(Path.cwd() / scriptLogFile)
            send_email(email_recipient, email_subject, email_text, email_attachment)

        log_and_print(f'Second request endpoint answer is {sandboxUsageSinceCreated}')

        minutesUpSinceCreated = sandboxUsageSinceCreated['data']['minutesUp']
        list2fill.append(minutesUpSinceCreated)
        minutesDownSinceCreated = sandboxUsageSinceCreated['data']['minutesDown']
        list2fill.append(minutesDownSinceCreated)
        totalCredits = minutesUpSinceCreated + (minutesDownSinceCreated * 0.3)
        list2fill.append(totalCredits)
        logger.debug(f'List to fill with parsed values from second request endpoint is {list2fill}')

        # Make request with sandboxIDs to get each Sandbox usage since yesterday
        log_and_print('Third request endpoint - Sandbox usage since yesterday')

        try:
            sandboxUsageLast24 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from={yesterdayIs}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            log_and_print('Failed to get Sandbox usage from third request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = f'Failed to get Sandbox usage for the last 24 hours in cron job - {scriptName}'
            email_text = f'Failed to get Sandbox usage for the last 24 hours in cron job - {scriptName}. Check the attached logs'
            email_attachment = str(Path.cwd() / scriptLogFile)
            send_email(email_recipient, email_subject, email_text, email_attachment)

        log_and_print(f'Third request endpoint answer is {sandboxUsageLast24}')

        minutesUpLast24 = sandboxUsageLast24['data']['minutesUp']
        list2fill.append(minutesUpLast24)
        minutesDownLast24 = sandboxUsageLast24['data']['minutesDown']
        list2fill.append(minutesDownLast24)
        logger.debug(f'List to fill with parsed values from third request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since 2021-03-01
        log_and_print('Fourth request endpoint - get Sandbox usage since 2021-03-01')

        try:
            thisSandboxUsageSince2021_03_01 = requests.get(
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

        log_and_print(f'Fourth request endpoint answer is {thisSandboxUsageSince2021_03_01}')

        thisSandboxMinutesUp210301 = thisSandboxUsageSince2021_03_01['data']['minutesUp']
        thisSandboxMinutesDown210301 = thisSandboxUsageSince2021_03_01['data']['minutesDown']
        creditsSpentOnThisSandbox210301 = thisSandboxMinutesUp210301 + (thisSandboxMinutesDown210301 * 0.3)
        list2fill.append(creditsSpentOnThisSandbox210301)
        logger.debug(f'List to fill with parsed values from fourth request endpoint is {list2fill}')

        # Get usage for realm aaay since 01.03.2021
        log_and_print('Fifth request endpoint - get Sandbox usage on realm aaay since 2021-03-01')

        try:
            sandboxUsageOnRealmAaaySince2021_03_01 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/realms/aaay/usage?from=2021-03-01",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            log_and_print('Failed to get Sandbox usage on realm aaay from fifth request endpoint')
            email_recipient = 'konstantin.yanev@isobar.com'
            email_subject = f'Failed to get Sandbox usage on realm aaay since 21.03.01 in cron job - {scriptName}'
            email_text = f'Failed to get Sandbox usage on realm aaay since 21.03.01 in cron job - {scriptName}. Check the attached logs'
            email_attachment = str(Path.cwd() / scriptLogFile)
            send_email(email_recipient, email_subject, email_text, email_attachment)

        log_and_print(f'Fifth request endpoint answer is {sandboxUsageOnRealmAaaySince2021_03_01}')

        realmAaayMinutesUp210301 = sandboxUsageOnRealmAaaySince2021_03_01['data']['minutesUp']
        realmAaayMinutesDown210301 = sandboxUsageOnRealmAaaySince2021_03_01['data']['minutesDown']
        creditsSpentOnRealmAaay = realmAaayMinutesUp210301 + (realmAaayMinutesDown210301 * 0.3)
        list2fill.append(creditsSpentOnRealmAaay)
        tuple2fill = tuple(list2fill)
        dataForDB.append(tuple2fill)

log_and_print('Open DB connection and insert data')

try:
    db = mysql.connector.connect(
        host="localhost",
        user=os.getenv('MySQLUser'),
        passwd=os.getenv('MySQLPassword'),
        database='odsreports'
    )

    cursor = db.cursor()

    sql = ('INSERT INTO IsobarWebODSUsage(TimeStamp, SandboxID, Realm, Instance, State, CreatedAt, CreatedBy, MinutesUpSinceCreated, MinutesDownSinceCreated, TotalCredits, MinutesUpInLast24Hours, MinutesDownInLast24Hours, ThisODSCreditsSince01032021, TotalCreditsInRealmSince01032021) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)')

    cursor.executemany(sql, dataForDB)
    db.commit()

except mysql.connector.Error as dbError:
    db.rollback()
    logger.error(dbError)
    logger.debug(f'Failed to connect or insert to database in {scriptName}')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to connect or insert to database in {scriptName}'
    email_text = f'Failed to connect or insert to database in {scriptName}.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

db.close()

log_and_print('Data inserted and DB connection closed')

# Ending point of the time counter
scriptFinishTime = time.perf_counter()
logger.debug(f'Script execution time is {round(scriptFinishTime - scriptStartTime, 2)} seconds. Keep in mind there will be around 0,5 seconds difference between this time and what will be received in email as execution time')

# Print current time
print(time.asctime(time.localtime(time.time())))