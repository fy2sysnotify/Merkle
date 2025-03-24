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
import time
import logging
import pyotp
import requests
import xlsxwriter
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from selenium import webdriver
import pyautogui

# Starting point of the time counter
scriptStartTime = time.perf_counter()

# Print current time
print(time.asctime(time.localtime(time.time())))

# Get date for yesterday and set it in format ISO 8601
yesterdayIs = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

# # Get date for today and set it in format ISO 8601
todayIs = datetime.today().strftime('%Y-%m-%d')

# Create and configure logger
logFormat = '%(levelname)s %(asctime)s - %(message)s'
logging.basicConfig(filename=f'ods-usage-report_{todayIs}.log',
                    level=logging.DEBUG,
                    format=logFormat)
logger = logging.getLogger()

# Get credentials from env variables and store in local vars
logger.debug('Request credentials from globvars')
client_id = os.getenv('ODS_REPORT_CLIENT_ID')
otpQR = os.getenv('ODS_REPORT_TOTP')
username = os.getenv('CREATE_ODS_USERNAME')
password = os.getenv('CREATE_ODS_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
logger.debug('We got the credentials')


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
    except:
        print("SMPT server connection error")
        logger.debug("SMPT server connection error. Failed to send email")
    return True


# Create excel workbook and worksheet in workbook for today's report
workbook = xlsxwriter.Workbook(f'ods-usage-report_{todayIs}.xlsx')
worksheet = workbook.add_worksheet('Sandbox usage report')

# Add bold formatting
boldFormat = workbook.add_format({'bold': True})

# Add headers to excel worksheet with bold format
worksheetHeader = ['SandboxID', 'Realm', 'Instance', 'State', 'Created at', 'Created by', 'Minutes up since created', 'Minutes down since created', 'Total credits', 'Minutes up in last 24 hours', 'Minutes down in last 24 hours', 'Credits since 2021.03.01']
worksheet.write_row(0, 0, worksheetHeader, boldFormat)
logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

requestCounter = 3

# Set authentication URL to hit, set browser and get the URL opened in browser
auth_url = 'https://account.demandware.com/dwsso/XUI/?realm=%2F&goto=https%3A%2F%2Faccount.demandware.com%3A443%2Fdwsso%2Foauth2%2Fauthorize%3Fresponse_type%3Dtoken%26state%3D%26client_id%3Db4836c9b-d346-43b8-8800-edbf811035c2%26scope%3D%26redirect_uri%3Dhttps%253A%252F%252Fadmin.us01.dx.commercecloud.salesforce.com%252Foauth2-redirect.html#login/'
driver = webdriver.Chrome('chromedriver')
driver.get(auth_url)
time.sleep(5)

# At the authentication URL we are searching for the id value of 'username' textbox and we are passing username value extracted from global variable
driver.find_element_by_id('idToken1').send_keys(username)
time.sleep(1)
# At the authentication URL we are searching for the id value of 'login' button and we are clicking it
driver.find_element_by_id('loginButton_0').click()
time.sleep(5)

# At the authentication URL we are searching for the id value of 'password' textbox and we are passing password value extracted from global variable
driver.find_element_by_id('idToken2').send_keys(password)
time.sleep(1)
# At the authentication URL we are searching for the id value of 'login' button and we are clicking it
driver.find_element_by_id('loginButton_0').click()
time.sleep(5)

# This will return the OTP Code
otpQR = os.getenv('ODS_REPORT_TOTP')
getOtp = pyotp.TOTP(otpQR)
otp = getOtp.now()
print(otp)

# I cannot retrieve the value of the element by id on the redirected page. This is why we are just entering OTP code and pressing enter
pyautogui.typewrite(otp)
pyautogui.press('enter')
time.sleep(15)

# After waiting time of 15 seconds we have landed on the final url and we are extracting the whole of it as a string
accessTokenUrl = driver.current_url
print(accessTokenUrl)
driver.quit()

# We are manipulating url string to extract access token by getting the indexes of start and end point
# we are interested in. Then we are removing first 13 symbols and we have the access token.
stringStart = accessTokenUrl.find('access_token=')
stringEnd = accessTokenUrl.find('&scope')
print(stringStart)
print(stringEnd)
stringToCut = accessTokenUrl[stringStart:stringEnd]
finalString = stringToCut[13:stringEnd]
print(finalString)

try:
    accessToken = finalString
except ValueError as value_error:
    logger.error(value_error)
    logger.debug('Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = 'Failed to get authorization for access token in ods-usage-report'
    email_text = 'Failed to get authorization for access token in ods-usage-report. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.'
    email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.log')
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

try:
    headers = {'Authorization': 'Bearer ' + accessToken}
except KeyError as key_error:
    logger.error(key_error)
    logger.debug('Some of the credentials are invalid. Check them carefully')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = 'Some of the credentials in cron job - ods-usage-report are invalid'
    email_text = 'Failed to get access token in cron job - ods-usage-report. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.log')
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise
logger.debug('We got the access token')

print('First request endpoint - get list of all sandboxes')
# Make request to url for listing all ODS - Sandbox On Demand
logger.debug('First request endpoint - get list of all sandboxes')

try:
    sandboxList = requests.get(
        "https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes?include_deleted=false",
        headers=headers, verify=False).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox list')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = 'Failed to get Sandbox lists in cron job - ods-usage-report'
    email_text = 'Failed to get Sandbox lists in cron job - ods-usage-report.'
    email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.log')
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug(f'First request endpoint answer is {sandboxList}')
print(sandboxList)

rowNumber = 1
columnNumber = 0
list2fill = []
for i in sandboxList['data']:
    sandboxId = i['id']
    list2fill.append(sandboxId)
    realm = i['realm']
    realmName = ''
    if realm == 'aaay':
        realmName = 'web'
    elif realm == 'aakr':
        realmName = 'web04'
    elif realm == 'bfmt':
        realmName = 'Mester Gronn'
    else:
        realmName = 'No Name'
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

    requestCounter += 1

    print('Second request endpoint')
    # Make request with sandboxIDs to get Sandbox usage since inception
    logger.debug('Second request endpoint')

    createDate = createdAt[:10]

    try:
        sandboxUsageSinceInception = requests.get(
            f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from={createDate}",
            headers=headers).json()
    except Exception as conn_error:
        logger.error(conn_error)
        logger.debug('Failed to get Sandbox usage from second request endpoint')
        email_recipient = 'konstantin.yanev@isobar.com'
        email_subject = 'Failed to get Sandbox usage since inception in cron job - ods-usage-report'
        email_text = 'Failed to get Sandbox usage since inception in cron job - ods-usage-report. Check the attached logs'
        email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.log')
        send_email(email_recipient, email_subject, email_text, email_attachment)

    logger.debug(f'Second request endpoint answer is {sandboxUsageSinceInception}')
    print(sandboxUsageSinceInception)

    minutesUp = sandboxUsageSinceInception['data']['minutesUp']
    list2fill.append(minutesUp)
    minutesDown = sandboxUsageSinceInception['data']['minutesDown']
    list2fill.append(minutesDown)
    creditsSpent = minutesUp + (minutesDown * 0.3)
    list2fill.append(creditsSpent)
    logger.debug(f'List to fill with parsed values from second request endpoint is {list2fill}')

    requestCounter += 1

    print('Third request endpoint - Sandbox usage since yesterday')
    # Make request with sandboxIDs to get each Sandbox usage since yesterday
    logger.debug('Third request endpoint - Sandbox usage since yesterday')

    try:
        sandboxUsageLast24 = requests.get(
            f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from={yesterdayIs}",
            headers=headers).json()
    except Exception as conn_error:
        logger.error(conn_error)
        logger.debug('Failed to get Sandbox usage from third request endpoint')
        email_recipient = 'konstantin.yanev@isobar.com'
        email_subject = 'Failed to get Sandbox usage for the last 24 hours in cron job - ods-usage-report'
        email_text = 'Failed to get Sandbox usage for the last 24 hours in cron job - ods-usage-report. Check the attached logs'
        email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.log')
        send_email(email_recipient, email_subject, email_text, email_attachment)

    logger.debug(f'Third request endpoint answer is {sandboxUsageLast24}')
    print(sandboxUsageLast24)

    minutesUpLast24 = sandboxUsageLast24['data']['minutesUp']
    list2fill.append(minutesUpLast24)
    minutesDownLast24 = sandboxUsageLast24['data']['minutesDown']
    list2fill.append(minutesDownLast24)
    logger.debug(f'List to fill with parsed values from third request endpoint is {list2fill}')

    requestCounter += 1

    print('Fourth request endpoint - get Sandbox usage since 2021-03-01')
    # Make request with sandboxIDs to get Sandbox usage since 2021-03-01
    logger.debug('Fourth request endpoint - Sandbox usage since 2021-03-01')

    try:
        sandboxUsageSince2021_03_01 = requests.get(
            f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/usage?from=2021-03-01",
            headers=headers).json()
    except Exception as conn_error:
        logger.error(conn_error)
        logger.debug('Failed to get Sandbox usage from fourth request endpoint')
        email_recipient = 'konstantin.yanev@isobar.com'
        email_subject = 'Failed to get Sandbox usage since 21.03.01. in cron job - ods-usage-report'
        email_text = 'Failed to get Sandbox usage since 21.03.01. in cron job - ods-usage-report. Check the attached logs'
        email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.log')
        send_email(email_recipient, email_subject, email_text, email_attachment)

    logger.debug(f'Fourth request endpoint answer is {sandboxUsageSince2021_03_01}')

    print(sandboxUsageSince2021_03_01)

    minutesUp210301 = sandboxUsageSince2021_03_01['data']['minutesUp']
    minutesDown210301 = sandboxUsageSince2021_03_01['data']['minutesDown']
    creditsSpent = minutesUp210301 + (minutesDown210301 * 0.3)
    list2fill.append(creditsSpent)
    logger.debug(f'List to fill with parsed values from fourth request endpoint is {list2fill}')

    # Write the list with data to excel worksheet
    worksheet.write_row(rowNumber, columnNumber, list2fill)
    rowNumber += 1

    print(f'list2fill, {list2fill}')

    list2fill.clear()
    logger.debug(f'List to fill has been cleared - {list2fill}')

# Write data to Excel table, save and close
workbook.close()
logger.debug('Data has been written into the excel file')

# Convert Excel to pandas dataframe
df = pd.read_excel(f'ods-usage-report_{todayIs}.xlsx')
dataFrame = pd.DataFrame(df)
logger.debug('Data has been transformed from excel to pandas dataframe')

# Sort Pandas dataframe by column 'CreatedAt'
dataFrame.sort_values(by=['Created at'], inplace=True, ascending=False)

# Convert pandas to html, remove index column and allign to center
html = dataFrame.to_html(index=False)
html2Attach = html.replace('<tr>', '<tr align="center">')
logger.debug('Data has been transformed from pandas dataframe to html with index column removed')

# Ending point of the time counter
scriptFinishTime = time.perf_counter()
logger.debug(f'Script execution time is {scriptFinishTime}. Keep in mind there will be around 0,5 seconds difference between this time and what will be received in email as execution time')

# Ending point of the time counter
scriptFinishTime = time.perf_counter()
logger.debug(f'Script execution time is {round(scriptFinishTime - scriptStartTime, 2)} seconds. Keep in mind there will be around 0,5 seconds difference between this time and what will be received in email as execution time')

# Add text to the email
emailText = f'Hi Team. My name is "ods-usage-report". Please check the overview for today. Keep in mind that living sandboxes on demand are spending credits. Each minute uptime = 1 credit. And each minute down time = 0.3 credit. If you have any questions, please do not hesitate to contact Isobar Operations Support.'

email_recipient = 'konstantin.yanev@isobar.com'
email_subject = 'Sandbox on demand update for today'
email_text = emailText + html2Attach
email_attachment = str(Path.cwd() / f'ods-usage-report_{todayIs}.xlsx')
send_email(email_recipient, email_subject, email_text, email_attachment)
logger.debug('Email is sent and job is success')

# Print current time
print(time.asctime(time.localtime(time.time())))
