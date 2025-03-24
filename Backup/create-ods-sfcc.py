# "The Dark Side of the Force is a pathway to many abilities some consider to be unnatural."

# This will create new sandbox on demand (ODS) and wait for it to be in status "started"
# and the login to Salesforce Business Manager(SFCC) to check if it is working.

import json
import smtplib
import time
import logging
import shutil
import os.path
import os
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import urllib3
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set script name
scriptName = 'create-ods'

# Starting point of the time counter
scriptStartTime = time.perf_counter()

# Get date for today and set it in format ISO 8601
todayIs = datetime.today().strftime('%Y-%m-%d')

# Create and configure logger
print('Set logger')
logFormat = '%(levelname)s %(asctime)s - %(message)s'
scriptLogFile = f'create-ods.log'
logging.basicConfig(filename=scriptLogFile,
                    level=logging.DEBUG,
                    format=logFormat)
logger = logging.getLogger()

# Disable warnings
urllib3.disable_warnings()


# Set function for sending emails with attachment, text and html
def send_email(email_recipient,
               email_subject,
               email_message,
               attachment_location=''):
    email_sender = ods_email

    email = MIMEMultipart()
    email['From'] = ods_email
    email['To'] = email_recipient
    email_cc = 'kosyoyanev@gmail.com'
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


# Get credentials from global variables. Keep in mind that getting them on Linux has slightly different syntax
print('Request credentials from globvars')
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

# Create folder "DataFolder"
os.mkdir('DataFolder')
logger.debug('Create folder "DataFolder"')
print('Create folder "DataFolder"')

# Get Current working directory
currentDirectory = os.getcwd()
logger.debug(f'Current Working Directory is {currentDirectory}')
print(f'Current Working Directory is {currentDirectory}')

# Set browser preferences for headless browsing
prefs = {'download.default_directory': currentDirectory,
         'directory_upgrade': True}
options = webdriver.ChromeOptions()
options.add_argument('--disable-popup-blocking')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')
options.add_argument('--start-maximized')
options.headless = True
options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome('chromedriver', service_args=["--verbose", "--log-path=chromedriver.log"], options=options)
driver.implicitly_wait(30)

# Requesting access token with password credentials
print('Requesting access token with password credentials')
logger.debug('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

accessTokenResponse = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                    verify=False,
                                    allow_redirects=False, auth=(client_id, client_secret))

try:
    accessToken = json.loads(accessTokenResponse.text)
except ValueError as value_error:
    print(value_error)
    logger.error(value_error)
    logger.debug(
        'Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Failed to get authorization for access token in {scriptName} job'
    email_text = f'Failed to get authorization for access token in {scriptName} job. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    print('email with error sent')
    raise

try:
    headers = {'Authorization': 'Bearer ' + accessToken['access_token']}
except KeyError as key_error:
    print(key_error)
    logger.error(key_error)
    logger.debug('Some of the credentials are invalid. Check them carefully')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Some of the credentials in {scriptName} job are invalid'
    email_text = f'Failed to get access token in {scriptName} job. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    print('email with error sent')
    raise
print('We got the access token')
logger.debug('We got the access token')

# Make request to create new ODS
logger.debug('Create dictionary for new ODS')
print('Create dictionary for new ODS')

create_json = {
    "realm": "bcgv",
    "ttl": 1,
    "settings": {
        "ocapi": [
            {
                "client_id": "b4836c9b-d346-43b8-8800-edbf811035c2",
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
                "client_id": "b4836c9b-d346-43b8-8800-edbf811035c2",
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

# Make request to url for creating new sandbox
print('First request endpoint - create new sandbox')
logger.debug('First request endpoint - create new sandbox')
createNewSandbox = requests.post('https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes',
                                 headers=headers, verify=False, json=create_json).json()

print(f'First request endpoint answer is {createNewSandbox}')
logger.debug(f'First request endpoint answer is {createNewSandbox}')

newSandbox = []

# Extract all data from returned dictionary
print('Extract all data from returned dictionary')
sandboxId = createNewSandbox['data']['id']
print(f'Sandbox ID is - {sandboxId}')
logger.debug(f'Sandbox ID is - {sandboxId}')
newSandbox.append(sandboxId)
realm = createNewSandbox['data']['realm']
print(f'Realm is - {realm}')
logger.debug(f'Realm is - {realm}')
newSandbox.append(realm)
instance = createNewSandbox['data']['instance']
print(f'Instance is - {instance}')
logger.debug(f'Instance is - {instance}')
newSandbox.append(instance)
versions = createNewSandbox['data']['versions']
print(f'Version is - {versions}')
logger.debug(f'Version is - {versions}')
newSandbox.append(versions)
state = createNewSandbox['data']['state']
print(f'State is - {state}')
logger.debug(f'State is - {state}')
newSandbox.append(state)
createdAt = createNewSandbox['data']['createdAt']
print(f'Created at - {createdAt}')
logger.debug(f'Created at - {createdAt}')
newSandbox.append(createdAt)
createdBy = createNewSandbox['data']['createdBy']
print(f'Created by - {createdBy}')
logger.debug(f'Created by - {createdBy}')
newSandbox.append(createdBy)
# eol = createNewSandbox['data']['eol']
# print(f'End Of Life is - {eol} GMT')
# logger.debug(f'End Of Life is - {eol} GMT')
# newSandbox.append(eol)
bm = createNewSandbox['data']['links']['bm']
print(f'Business Manager link is - {bm}')
logger.debug(f'Business Manager link is - {bm}')
newSandbox.append(bm)
ocapi = createNewSandbox['data']['links']['ocapi']
print(f'OCAPI link is - {ocapi}')
logger.debug(f'OCAPI link is - {ocapi}')
newSandbox.append(ocapi)
impex = createNewSandbox['data']['links']['impex']
print(f'Impex link is - {impex}')
logger.debug(f'Impex link is - {impex}')
newSandbox.append(impex)
code = createNewSandbox['data']['links']['code']
print(f'Code Link is - {code}')
logger.debug(f'Code Link is - {code}')
newSandbox.append(code)
logs = createNewSandbox['data']['links']['logs']
print(f'Logs are at - {logs}')
logger.debug(f'Logs are at - {logs}')
newSandbox.append(logs)
print('Data extracted from response')

# Put to sleep for 10 minutes before checking for the state of the new sandbox
print('Wait 10 minutes before checking the state of the new sandbox')
logger.debug('Wait 10 minutes before checking the state of the new sandbox')
time.sleep(600)
stateOfNewSandbox = state
logger.debug(f'Sandbox state is {stateOfNewSandbox}')
print(f'Sandbox state is {stateOfNewSandbox}')

# Request to get sandbox state. After creation each sandbox change it`s state several times. We need the state to be "started"
while 'started' not in stateOfNewSandbox:
    time.sleep(180)
    checkState = requests.get(f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}",
                              headers=headers).json()

    stateOfNewSandbox = checkState['data']['state']
    print(f'Sandbox state is {stateOfNewSandbox}')
    logger.debug(f'Sandbox state is {stateOfNewSandbox}')
    print('Wait another 3 minutes before checking the state of the new sandbox')
    logger.debug('Wait another 3 minutes before checking the state of the new sandbox')

# Go to Sandbox
print('Go to sandbox')
logger.debug('Go to sandbox')
driver.get(bm)
logger.debug('Sandbox is loaded')
print('Sandbox is loaded')

# At the authentication URL we are searching for the id value of 'username' textbox and we are passing username value extracted from global variable
enterUsername = driver.find_element_by_id('idToken1')
driver.save_screenshot('./DataFolder/1_UsernameScreen.png')
enterUsername.send_keys(username)
logger.debug('Username textbox found and User Name value sent')
print('Username textbox found and User Name value sent')

# At the authentication URL we are searching for the id value of 'login' button and we are clicking it
driver.find_element_by_id('loginButton_0').click()
logger.debug('Login button after username clicked')
print('Login button after username clicked')

# At the authentication URL we are searching for the id value of 'password' textbox and we are passing password value extracted from global variable
enterPassword = driver.find_element_by_id('idToken2')
driver.save_screenshot('./DataFolder/2_PasswordScreen.png')
enterPassword.send_keys(password)
logger.debug('Password textbox found and password value sent')
print('Password textbox found and password value sent')

# At the authentication URL we are searching for the id value of 'login' button and we are clicking it
driver.find_element_by_id('loginButton_0').click()
logger.debug('Login button after password clicked')
print('Login button after password clicked')

# Find and extract Sandbox version
sfccSandboxVersion = driver.find_element_by_class_name('footer__version').get_attribute('title')
sfccSandboxVersion = sfccSandboxVersion[:4]
driver.save_screenshot('./DataFolder/3_WelcomeToBusinessManager.png')
logger.debug(f'Find and extract Sandbox version =  {sfccSandboxVersion}')
print(f'Find and extract Sandbox version = {sfccSandboxVersion}')

# Skip the Annoying banner
try:
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'pendo-button-f490c282'))))
except:
    pass

try:
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pendo-close-guide-699765a8"]'))))
except:
    pass

try:
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_header_row"]/td/header/div/div[2]/ul/li[7]/a'))))
    logger.debug('Logout Sandbox')
    print('Logout Sandbox')
except:
    pass

driver.close()
driver.quit()
print('Browser closed and driver quit')
logger.debug('Browser closed and driver quit')

# Create zip file of the directory with all script data and delete directory
print('Create zip file of the directory with all screenshots and delete directory')
logger.debug('Create zip file of the directory with all screenshots and delete directory')
archiveFolder = 'LoginScreenshots'
shutil.make_archive(archiveFolder, 'zip', 'DataFolder')
shutil.rmtree('./DataFolder')

# Send email with attached zip containing screenshots
print('Send email with attached zip containing screenshots')
logger.debug('Send email with attached zip containing screenshots')
email_recipient = 'konstantin.yanev@isobar.com'
email_subject = f'Sandbox {sandboxId} in realm {realm} is ready'
email_text = f'Hi Team, this is to inform you that Sandbox {sandboxId} in realm {realm} is ready. Software version is {sfccSandboxVersion}. You can login to Business Manager at {bm}'
email_attachment = str(Path.cwd() / f'{archiveFolder}.zip')
send_email(email_recipient, email_subject, email_text, email_attachment)

# Delete archive with screenshots
os.remove(f'{archiveFolder}.zip')
print('Delete archive with screenshots')

# Ending point of the time counter
scriptFinishTime = time.perf_counter()
print(f'Script execution time is {round(scriptFinishTime - scriptStartTime, 2)} seconds.')

# Print current time
print(time.asctime(time.localtime(time.time())))
