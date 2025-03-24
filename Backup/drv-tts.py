# "Size matters not. Look at me. Judge me by my size, do you? Hmm? Hmm. And well you should not. For my ally is the Force, and a powerful ally it is.
# Life creates it, makes it grow. Its energy surrounds us and binds us. Luminous beings are we, not this crude matter.
# You must feel the Force around you; here, between you, me, the tree, the rock, everywhere, yes. Even between the land and the ship."


# This is used to verify Demandware Releases before replication from Staging to Production
# Login to Salesforce Business Manager(SFCC) - Staging Instance and make exports.
# Login to Salesforce Business Manager(SFCC) - Development Instance and make export.
# Create new On Demand Sandbox and wait for it to be in state "started"
# Change On Demand Sandbox Compatibility mode by transferring a ".apiversion" file with "api.version=18.10" content to active code version in Cartridges
# Login ot newly created ODS and make imports.
# Exports and imports algorithms can be found at https://wiki.isobarsystems.com/pages/viewpage.action?spaceKey=SUPTEAM&title=How+to+prepare+sandbox+for+Demandware+release+since+13.4


import requests
import json
import smtplib
import time
import logging
import shutil
import os.path
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from urllib.parse import urlparse
from jira import JIRA
import urllib3
from webdav3.client import Client as webdavClient
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pyttsx3

# Set script name
scriptName = 'drv-tts'

# Starting point of the time counter
scriptStartTime = time.perf_counter()

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
        print('email sent')
        server.quit()
    except:
        log_and_print('SMPT server connection error. Failed to send email')
    return True


def raise_jira(summary, description):
    jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_url})

    newIssue = {
        'project': 'ZWG',
        'issuetype': 'Support Request',
        'summary': summary,
        'description': description
    }

    jira.create_issue(fields=newIssue)


engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

try:
    engine.say('Request credentials from global variables')
    engine.runAndWait()
except:
    pass

# Get credentials from global variables. Keep in mind that getting them on Linux has slightly different syntax
log_and_print('Request credentials from global variables')
client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
jira_username = os.getenv('jiraUser')
jira_password = os.getenv('jiraPass')
jira_url = os.getenv('jiraURL')
log_and_print('We got the credentials')

try:
    engine.say('We got the credentials')
    engine.runAndWait()
except:
    pass

try:
    # Create folder "DataFolder"
    pof = 'Create Data Folder'
    os.mkdir('DataFolder')
    log_and_print('Create folder "DataFolder"')
except FileExistsError as fee:
    raise_jira('Demandware Release validation of Zwilling failed', f'Demandware Release validation of Zwilling failed at pof {pof}. Restart the process or continue from point of failure')
    print(fee)
    raise

# Get Current working directory
currentDirectory = os.getcwd()
log_and_print(f'Current Working Directory is {currentDirectory}')

# _______________________________________________________________ BROWSER SETUP __________________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('I will setup the browser for you')
    engine.runAndWait()
except:
    pass

# Get Staging URL to hit, set browser options and get the URL opened in browser
zwillingDev = 'https://development-eu01-zwilling.demandware.net/on/demandware.store/Sites-Site/default/ViewLogin-StartAM'
devHostName = urlparse(zwillingDev).hostname
log_and_print(f'Dev hostname is {devHostName}')
zwillingStaging = 'https://staging-eu01-zwilling.demandware.net/on/demandware.store/Sites-Site/default/ViewLogin-StartAM'
stagingHostName = urlparse(zwillingStaging).hostname
log_and_print(f'Staging hostname is {stagingHostName}')

prefs = {'download.default_directory': currentDirectory,
         'directory_upgrade': True}
options = webdriver.ChromeOptions()
# options.add_argument('--disable-popup-blocking')
# options.add_argument('--disable-infobars')
# options.add_argument('--disable-notifications')
# options.add_argument('--incognito')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--start-maximized')
# options.headless = True
options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome('chromedriver', service_args=["--verbose", "--log-path=chromedriver.log"], options=options)
driver.implicitly_wait(30)

try:
    engine.say('Browser options are set')
    engine.runAndWait()
except:
    pass

# ______________________________________________________________ BROWSER SETUP END _________________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ EXPORT PHASE START ________________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('I will start export phase now')
    engine.runAndWait()
except:
    pass

# Set timing for Export phase
log_and_print('Export phase start')
log_and_print(time.asctime(time.localtime(time.time())))
exportPhaseStart = time.perf_counter()

# Load Zwilling Staging
driver.get(zwillingStaging)
time.sleep(3)
driver.save_screenshot('./DataFolder/1_ZwillingStageLwamPage.png')
log_and_print('Zwilling staging is loaded')


def login_bm():
    time.sleep(5)
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, 'loginSSO'))))
    log_and_print('Login with Account Manager')
    driver.find_element_by_id('idToken1').send_keys(username)
    log_and_print('Username textbox found and User Name value sent')
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'loginButton_0'))))
    log_and_print('Login button after username clicked')
    driver.find_element_by_id('idToken2').send_keys(password)
    log_and_print('Password textbox found and password value sent')
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'loginButton_0'))))
    log_and_print('Login button after password clicked')


login_bm()

# Find and extract Staging version
stagVersion = driver.find_element_by_class_name('footer__version').get_attribute('title')
stagVersion = stagVersion[:4]
log_and_print(f'Staging version is {stagVersion}')
stagingVersion = stagVersion.replace('.', '')

try:
    engine.say('I am logged on Staging now')
    engine.runAndWait()
except:
    pass

try:
    engine.say(f'Staging version is {stagVersion}')
    engine.runAndWait()
except:
    pass

# Click "Administration"
adminLink = driver.find_element_by_class_name('admin-link').click()
time.sleep(3)
driver.save_screenshot('./DataFolder/2_Administration.png')
log_and_print('Click Administration')

# Click "Site development"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[5]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/3_SiteDevelopment.png')
log_and_print('Click Site development')

# Click "Site Import & Export"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[11]/td[1]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/4_Site_Import_Export.png')
log_and_print('Click Site Import & Export')

try:
    engine.say('I am checking for a job in status running')
    engine.runAndWait()
except:
    pass


def check_export_status(logger_text, sleep_time):
    span_element = driver.find_element_by_css_selector('.table_detail.s.top.center')
    status_top_cell = span_element.text
    log_and_print(f'Get Status column top cell value = {status_top_cell}')

    while 'Running' in status_top_cell:
        log_and_print(logger_text)
        time.sleep(sleep_time)
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="siteImpexBottom"]/table[5]/tbody/tr[12]/td[1]/button'))))
        log_and_print('Press refresh button to check status')
        span_element = driver.find_element_by_css_selector('.table_detail.s.top.center')
        status_top_cell = span_element.text
        log_and_print(f'Job is in status {status_top_cell}')


check_export_status('Wait 5 minutes', 300)

try:
    engine.say('There is no job in status running')
    engine.runAndWait()
except:
    pass

# Configure sites.json archive name
projectName = 'ZWG'
projectInstance = 'Stag'
exportDateStaging = datetime.today().strftime('%Y%m%d')
stagingSitesArchive = f'{stagingVersion}_SitesOps_{projectName}_{projectInstance}_{exportDateStaging}'
stagingSitesZip = f'{stagingSitesArchive}.zip'
log_and_print(f'Sites archive name is {stagingSitesArchive}')

# Find Archive name textbox and send value to it
driver.find_element_by_name('exportFile').send_keys(stagingSitesArchive)
log_and_print('Archive name textbox found and value sent')

# Click "Sites" checkbox
driver.find_element_by_class_name('x-tree-node-cb').click()
log_and_print('Click "Sites" checkbox')

# Click "Sites" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "Sites" plus')

# Click "Zwilling-US" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-US" plus')

# Uncheck "Zwilling-US Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-US Site Preferences"')

# Uncheck "Zwilling-US Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-US Site Custom objects"')

# Click "Zwilling-CA plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-CA plus')

# Uncheck "Zwilling-CA Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-CA Site Preferences"')

# Uncheck "Zwilling-CA Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-CA Site Custom objects"')

# Click "Zwilling-Global plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-Global plus')

# Uncheck "Zwilling-Global Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-Global Site Preferences"')

# Uncheck "Zwilling-Global Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-Global Site Custom objects"')

# Uncheck "Zwilling-Global Site Content" - !!! REMOVE THIS UNCHECK WHEN DATA IS CLEAR!!!
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[5]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-Global Site Content"')

# Click "Zwilling-TR plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-TR plus')

# Uncheck "Zwilling-TR Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-TR Site Preferences"')

# Uncheck "Zwilling-TR Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-TR Site Custom objects"')

# Click "Zwilling-DE plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-DE plus')

# Uncheck "Zwilling-DE Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-DE Site Preferences"')

# Uncheck "Zwilling-DE Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-DE Site Custom objects"')

# Click "Zwilling-FR plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-FR plus')

# Uncheck "Zwilling-FR Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-FR Site Preferences"')

# Uncheck "Zwilling-FR Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-FR Site Custom objects"')

# Click "Zwilling-IT plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-IT plus')

# Uncheck "Zwilling-IT Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-IT Site Preferences"')

# Uncheck "Zwilling-IT Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-IT Site Custom objects"')

# Click"Zwilling-BR plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/div/div[1]/img[1]'))))
log_and_print('Click"Zwilling-BR plus')

# Uncheck "Zwilling-BR Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-BR Site Preferences"')

# Uncheck "Zwilling-BR Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-BR Site Custom objects"')

# Click "Zwilling-BE plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-BE plus')

# Uncheck "Zwilling-BE Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-BE Site Preferences"')

# Uncheck "Zwilling-BE Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-BE Site Custom objects"')

# Click "Zwilling-DK plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-DK plus')

# Uncheck "Zwilling-DK Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-DK Site Preferences"')

# Uncheck "Zwilling-DK Site Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Zwilling-DK Site Custom objects"')
driver.save_screenshot('./DataFolder/5_SitesExportName.png')

try:
    engine.say('Initiating export of Sites elements from staging')
    engine.runAndWait()
except:
    pass


def press_export():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="export"]'))))
    log_and_print('Press "Export button"')
    time.sleep(2)


press_export()

try:
    engine.say('I will check Sites export status on every 3 minutes')
    engine.runAndWait()
except:
    pass

check_export_status('Wait 3 minutes', 180)

log_and_print('Sites Export is ready')

try:
    engine.say('Export of Sites elements from staging has been completed')
    engine.runAndWait()
except:
    pass

# # Configure Library Static Resources archive name
# projectName = 'ZWG'
# projectInstance = 'Stag'
# exportDateStaging = datetime.today().strftime('%Y%m%d')
# stagingLSRArchive = f'{stagingVersion}_LSROps_{projectName}_{projectInstance}_{exportDateStaging}'
# stagingLSRZip = f'{stagingLSRArchive}.zip'
# log_and_print(f'LSR archive name is {stagingLSRArchive}')
#
# # Find Archive name textbox and send value to it
# driver.find_element_by_name('exportFile').send_keys(stagingLSRArchive)
# log_and_print('Archive name textbox found and value sent')
#
# # Check Library Static Resources
# driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
#     EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[3]/div/div[1]/input'))))
# log_and_print('Check Library Static Resources')
#
# press_export()
#
# check_export_status('Wait 7 minutes', 420)
#
# log_and_print('LSR Export is ready')

# Configure Catalog archive name
projectName = 'ZWG'
projectInstance = 'Stag'
exportDateStaging = datetime.today().strftime('%Y%m%d')
stagingCatalogArchive = f'{stagingVersion}_CatalogOps_{projectName}_{projectInstance}_{exportDateStaging}'
stagingCatalogZip = f'{stagingCatalogArchive}.zip'
log_and_print(f'Catalogs archive name is {stagingCatalogArchive}')

# Find Archive name textbox and send value to it
driver.find_element_by_name('exportFile').send_keys(stagingCatalogArchive)
log_and_print('Archive name textbox found and value sent')

# Check Catalogs
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[4]/div/div[1]/input'))))
log_and_print('Check Catalogs')
driver.save_screenshot('./DataFolder/6_CatalogExportName.png')

try:
    engine.say('Initiating Catalogs export from staging')
    engine.runAndWait()
except:
    pass

press_export()

try:
    engine.say('I will check Catalogs export status on every 6 minutes')
    engine.runAndWait()
except:
    pass

check_export_status('Wait 6 minutes', 360)

try:
    engine.say('Catalogs Export from staging has been completed')
    engine.runAndWait()
except:
    pass

log_and_print('Catalogs Export is ready')

# # Configure Catalog Static Resources archive name
# projectName = 'ZWG'
# projectInstance = 'Stag'
# exportDateStaging = datetime.today().strftime('%Y%m%d')
# stagingCSRArchive = f'{stagingVersion}_CSROps_{projectName}_{projectInstance}_{exportDateStaging}'
# stagingCSRZip = f'{stagingCSRArchive}.zip'
# log_and_print(f'CSR archive name is {stagingCSRArchive}')
#
# # Find Archive name textbox and send value to it
# driver.find_element_by_name('exportFile').send_keys(stagingCSRArchive)
# log_and_print('Archive name textbox found and value sent')
#
# # Check Catalog Static Resources
# driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
#     EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[5]/div/div[1]/input'))))
# log_and_print('Check Catalog Static Resources')
#
# press_export()
#
# check_export_status('Wait 7 minutes', 420)
#
# log_and_print('CSR Export is ready')

# Configure Price Books archive name
projectName = 'ZWG'
projectInstance = 'Stag'
exportDateStaging = datetime.today().strftime('%Y%m%d')
stagingPBArchive = f'{stagingVersion}_PriceBooksOps_{projectName}_{projectInstance}_{exportDateStaging}'
stagingPBZip = f'{stagingPBArchive}.zip'
log_and_print(f'Price Books archive name is {stagingPBArchive}')

# Find Archive name textbox and send value to it
driver.find_element_by_name('exportFile').send_keys(stagingPBArchive)
log_and_print('Archive name textbox found and value sent')

# Check Price Books
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[6]/div/div[1]/input'))))
log_and_print('Check Price Books')
driver.save_screenshot('./DataFolder/7_PriceBooksExportName.png')

try:
    engine.say('Initiating export of Price books from staging')
    engine.runAndWait()
except:
    pass

press_export()

try:
    engine.say('I will check Price books export status on every 30 seconds')
    engine.runAndWait()
except:
    pass

check_export_status('Wait 30 seconds', 30)

try:
    engine.say('Export of Price books from staging has been completed')
    engine.runAndWait()
except:
    pass

log_and_print('Price Books Export is ready')

# Configure Inventory Lists archive name
projectName = 'ZWG'
projectInstance = 'Stag'
exportDateStaging = datetime.today().strftime('%Y%m%d')
stagingILArchive = f'{stagingVersion}_InventoryListsOps_{projectName}_{projectInstance}_{exportDateStaging}'
stagingILZip = f'{stagingILArchive}.zip'
log_and_print(f'Inventory Lists archive name is {stagingILArchive}')

# Find Archive name textbox and send value to it
driver.find_element_by_name('exportFile').send_keys(stagingILArchive)
log_and_print('Archive name textbox found and value sent')

# Check Inventory Lists
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[7]/div/div[1]/input'))))
log_and_print('Check Inventory Lists')
driver.save_screenshot('./DataFolder/8_InventoryListsName.png')

try:
    engine.say('Initiating export of Inventory lists from staging')
    engine.runAndWait()
except:
    pass

press_export()

try:
    engine.say('I will check Inventory lists export status on every 30 seconds')
    engine.runAndWait()
except:
    pass

check_export_status('Wait 30 seconds', 30)

try:
    engine.say('Export of Inventory lists from staging has been completed')
    engine.runAndWait()
except:
    pass

log_and_print('Inventory Lists Export is ready')

# Configure Global Data archive name
projectName = 'ZWG'
projectInstance = 'Stag'
exportDateStaging = datetime.today().strftime('%Y%m%d')
stagingGDArchive = f'{stagingVersion}_GlobalDataOps_{projectName}_{projectInstance}_{exportDateStaging}'
stagingGDZip = f'{stagingGDArchive}.zip'
log_and_print(f'Global Data archive name is {stagingGDArchive}')

# Find Archive name textbox and send value to it
driver.find_element_by_name('exportFile').send_keys(stagingGDArchive)
log_and_print('Archive name textbox found and value sent')

# Check "Global Data"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/div/div[1]/input'))))
log_and_print('Check Global Data')

# Find "Global Data plus and click it
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/div/div[1]/img[1]'))))
log_and_print('Find "Global Data plus and click it')

# Uncheck Global Data Jobs
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[4]/div/div[1]/input'))))
log_and_print('Uncheck Global Data Jobs')

# Uncheck Global Data Jobs Deprecated
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[5]/div/div[1]/input'))))
log_and_print('Uncheck Global Data Jobs Deprecated')

# Uncheck Global Data Static Resources
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[7]/div/div[1]/input'))))
log_and_print('Uncheck Global Data Static Resources')

# Uncheck Global Data Users
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[8]/div/div[1]/input'))))
log_and_print('Uncheck Global Data Users')

# Uncheck Global Data Access Roles
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck Global Data Access Roles')

# Uncheck "Custom Quota Settings"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[11]/div/div[1]/input'))))
log_and_print('Uncheck Custom Quota Settings')
driver.save_screenshot('./DataFolder/9_GlobalDataName.png')

try:
    engine.say('Initiating export of Global data elements from staging')
    engine.runAndWait()
except:
    pass

press_export()

try:
    engine.say('I will check Global data export status on every 7 minutes')
    engine.runAndWait()
except:
    pass

check_export_status('Wait 7 minutes', 420)

try:
    engine.say('Export of Global data elements from staging has been completed')
    engine.runAndWait()
except:
    pass

log_and_print('Global Data Export is ready')

# Click "Administration"
driver.find_element_by_class_name('admin-link').click()
driver.save_screenshot('./DataFolder/10_Administration.png')
log_and_print('Click Administration')

# Find and click "Site development"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[5]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/11_SiteDevelopment.png')
log_and_print('Find and click Site development')

# Click "Code deployment"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td[5]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/12_CodeDeployment.png')
log_and_print('Click Code Deployment')

# Find, extract and click Active version
codeVersion = driver.find_element_by_xpath(
    '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[11]/td[3]/a').get_attribute(
    'innerText')
log_and_print(f'Code version is {codeVersion}')
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[11]/td[3]/a'))))
driver.save_screenshot('./DataFolder/13_ActiveVersion.png')
log_and_print('Find and click active version')

try:
    engine.say(f'Now I will export Code version {codeVersion} from staging')
    engine.runAndWait()
except:
    pass

# Click Download
log_and_print('Wait 5 seconds')
time.sleep(5)
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="downloadButton"]'))))
log_and_print('Click Download')
log_and_print('Wait 45 seconds')
time.sleep(45)

# Unzip downloaded zip and delete it
unpackZip = f'{codeVersion}.zip'
shutil.unpack_archive(str(unpackZip), currentDirectory)
os.remove(unpackZip)
log_and_print('Unzip downloaded zip with Code version and delete zip')
log_and_print('Wait 15 seconds')
time.sleep(15)

try:
    engine.say('Code version export from staging has been completed')
    engine.runAndWait()
except:
    pass

try:
    time.sleep(2)
    engine.say('I will log out from staging now')
    engine.runAndWait()
except:
    pass

# Find "Logout" and click it
log_and_print('Click "Logout"')
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_header_row"]/td/header/div/div[2]/ul/li[7]/a/span'))))
log_and_print('Logout success')
time.sleep(3)
driver.save_screenshot('./DataFolder/14_LogOutStaging.png')

# ______________________________________________________________ Staging End ________________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ Dev start __________________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('I will log on development now')
    engine.runAndWait()
except:
    pass

# Get Zwilling Dev Site
driver.get(zwillingDev)
time.sleep(2)
driver.save_screenshot('./DataFolder/14_ZDevBM.png')
log_and_print('Get Zwilling Dev Site')

login_bm()

# Find and extract Staging version
developmentVersion = driver.find_element_by_class_name('footer__version').get_attribute('title')
developmentVersion = developmentVersion[:4]
log_and_print(f'SFCC version on Dev is {developmentVersion}')
devVersion = developmentVersion.replace('.', '')

try:
    engine.say(f'Development version is {developmentVersion}')
    engine.runAndWait()
except:
    pass

# Click "Administration"
driver.save_screenshot('./DataFolder/15_AdministrationDev.png')
driver.find_element_by_class_name('admin-link').click()
log_and_print('Click Administration')

# Click "Site development"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[5]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/16_SiteDevelopmentDev.png')
log_and_print('Click Site development')

# Click "Site Import & Export"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[11]/td[1]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/17_SiteImportExportDev.png')
log_and_print('Click Site Import & Export')

# Configure archive name
projectNameDev = 'ZWG'
projectInstanceDev = 'Dev'
exportDateDev = datetime.today().strftime('%Y%m%d')
devArchive = f'{devVersion}_SitesOPS_{projectNameDev}_{projectInstanceDev}_{exportDateDev}'
devZip = f'{devArchive}.zip'
log_and_print(f'Dev archive name is {devArchive}')

# Find Archive name textbox and send value to it
driver.find_element_by_name('exportFile').send_keys(devArchive)
log_and_print('Archive name textbox found and value sent')

# Click "Sites" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "Sites" plus')

# Click "Zwilling-us" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-us" plus')

# Check Zwilling-us Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-us Site Preferences')

# Check Zwilling-us Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-us Custom objects')

# Click "Zwilling-ca" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-ca" plus')

# Check Zwilling-ca Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-ca Site Preferences')

# Check Zwilling-ca Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-ca Custom objects')

# Click "Zwilling-global" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-global" plus')

# Check Zwilling-global Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-global Site Preferences')

# Check Zwilling-global Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-global Custom objects')

# Click "Zwilling-tr" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-tr" plus')

# Check Zwilling-tr Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-tr Site Preferences')

# Check Zwilling-tr Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-tr Custom objects')

# Click "Zwilling-de" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-de" plus')

# Check Zwilling-de Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-de Site Preferences')

# Check Zwilling-de Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-de Custom objects')

# Click "Zwilling-fr" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-fr" plus')

# Check Zwilling-fr Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-fr Site Preferences')

# Check Zwilling-fr Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-fr Custom objects')

# Click "Zwilling-it" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-it" plus')

# Check Zwilling-it Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-it Site Preferences')

# Check Zwilling-it Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-it Custom objects')

# Click "Zwilling-br" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-br" plus')

# Check Zwilling-br Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-br Site Preferences')

# Check Zwilling-br Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-br Custom objects')

# Click "Zwilling-be" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-be" plus')

# Check Zwilling-be Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-be Site Preferences')

# Check Zwilling-be Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-be Custom objects')

# Click "Zwilling-dk" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/div/div[1]/img[1]'))))
log_and_print('Click "Zwilling-dk" plus')

# Check Zwilling-dk Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Zwilling-dk Site Preferences')

# Check Zwilling-dk Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Zwilling-dk Custom objects')
driver.save_screenshot('./DataFolder/18_DevSitesArchiveName.png')

try:
    engine.say('Initiating export of Sites elements from development')
    engine.runAndWait()
except:
    pass

press_export()

try:
    engine.say('I will log off from development now')
    engine.runAndWait()
except:
    pass

# Click "Logoff" button
driver.execute_script("arguments[0].click();",
                      WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_header_row"]/td/header/div/div[2]/ul/li[7]/a'))))
time.sleep(3)
driver.save_screenshot('./DataFolder/19_DevLogOff.png')
log_and_print('Click "Logoff" button')

log_and_print('Export phase end')
print(time.asctime(time.localtime(time.time())))
exportPhaseEnd = time.perf_counter()
exportPhaseTime = round(exportPhaseEnd - exportPhaseStart, 2)
log_and_print(f'Export phase was performed in {exportPhaseTime} seconds.')

try:
    engine.say(f'Export phase has been completed. It was performed in {exportPhaseTime} seconds.')
    engine.runAndWait()
except:
    pass

# ______________________________________________________________ EXPORT PHASE END ____________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ SANDBOX PREPARATION _________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('I am starting sandbox preparation phase now')
    engine.runAndWait()
except:
    pass

# Set timing for Sandbox preparation
log_and_print('Sandbox preparation start')
print(time.asctime(time.localtime(time.time())))
sandboxPreparationStart = time.perf_counter()

# Requesting access token with password credentials
log_and_print('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

try:
    engine.say('I am requesting access token with password credentials')
    engine.runAndWait()
except:
    pass

accessTokenResponse = requests.post('https://account.demandware.com:443/dwsso/oauth2/access_token', data=data,
                                    verify=False,
                                    allow_redirects=False, auth=(client_id, client_secret))

try:
    accessToken = json.loads(accessTokenResponse.text)
except ValueError as value_error:
    log_and_print(value_error)
    log_and_print('Failed to get authorization for access token. Check if virtual machine is up and running. Check if SFCC Authenticator is active. Check if fake GPS is up and running.')
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
    log_and_print(key_error)
    log_and_print('Some of the credentials are invalid. Check them carefully')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Some of the credentials in {scriptName} job are invalid'
    email_text = f'Failed to get access token in {scriptName} job. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    print('email with error sent')
    raise
log_and_print('We got the access token')

try:
    engine.say('I have the access token and I will create the on demand sandbox for you')
    engine.runAndWait()
except:
    pass

create_json = {
    "realm": "aaay",
    "ttl": 96,
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
log_and_print('First request endpoint - create new sandbox')

createNewSandbox = requests.post('https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes',
                                 headers=headers, verify=False, json=create_json).json()

log_and_print(f'First request endpoint answer is {createNewSandbox}')

newSandbox = []

# Extract all data from returned dictionary
print('Extract all data from returned dictionary')
sandboxId = createNewSandbox['data']['id']
log_and_print(f'Sandbox ID is - {sandboxId}')
newSandbox.append(sandboxId)
realm = createNewSandbox['data']['realm']
log_and_print(f'Realm is - {realm}')
newSandbox.append(realm)
instance = createNewSandbox['data']['instance']
log_and_print(f'Instance is - {instance}')
newSandbox.append(instance)
versions = createNewSandbox['data']['versions']
log_and_print(f'Version is - {versions}')
newSandbox.append(versions)
state = createNewSandbox['data']['state']
log_and_print(f'State is - {state}')
newSandbox.append(state)
createdAt = createNewSandbox['data']['createdAt']
log_and_print(f'Created at - {createdAt}')
newSandbox.append(createdAt)
createdBy = createNewSandbox['data']['createdBy']
log_and_print(f'Created by - {createdBy}')
newSandbox.append(createdBy)
bm = createNewSandbox['data']['links']['bm']
log_and_print(f'Business Manager link is - {bm}')
newSandbox.append(bm)
ocapi = createNewSandbox['data']['links']['ocapi']
log_and_print(f'OCAPI link is - {ocapi}')
newSandbox.append(ocapi)
impex = createNewSandbox['data']['links']['impex']
log_and_print(f'Impex link is - {impex}')
newSandbox.append(impex)
code = createNewSandbox['data']['links']['code']
log_and_print(f'Code Link is - {code}')
newSandbox.append(code)
logs = createNewSandbox['data']['links']['logs']
log_and_print(f'Logs are at - {logs}')
newSandbox.append(logs)
print('Data extracted from response')

# Switch variable for state
stateOfNewSandbox = state
log_and_print(f'Sandbox state is {stateOfNewSandbox}')

try:
    engine.say('Sandbox was created and I will check its status on every 4 minutes')
    engine.runAndWait()
except:
    pass

# Request to get sandbox state in every 4 minutes. After creation each sandbox change it`s state several times. We need the state to be "started"
while 'started' not in stateOfNewSandbox:
    log_and_print('Wait another 4 minutes before checking the state of the new sandbox')
    time.sleep(240)

    checkState = requests.get(f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}",
                              headers=headers).json()

    stateOfNewSandbox = checkState['data']['state']
    log_and_print(f'Sandbox state is {stateOfNewSandbox}')

log_and_print('Sandbox preparation end')
print(time.asctime(time.localtime(time.time())))
sandboxPreparationEnd = time.perf_counter()
log_and_print(f'Sandbox preparation was performed in {round(sandboxPreparationEnd - sandboxPreparationStart, 2)} seconds.')

try:
    engine.say('Sandbox is in status started and I will use it through the rest of the process')
    engine.runAndWait()
except:
    pass

# ______________________________________________________________ SANDBOX PREPARATION END _________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ IMPORT PHASE START _____________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('I am starting the import phase')
    engine.runAndWait()
except:
    pass

log_and_print('Import phase start')
print(time.asctime(time.localtime(time.time())))
importPhaseStart = time.perf_counter()

# Goto Sandbox
driver.get(bm)
log_and_print('Sandbox is loaded')


def login_sb():
    try:
        time.sleep(5)
        enterUsername = driver.find_element_by_id('idToken1')
        enterUsername.send_keys(username)
        log_and_print('Username textbox found and User Name value sent')
        driver.find_element_by_id('loginButton_0').click()
        log_and_print('Login button after username clicked')
        enterPassword = driver.find_element_by_id('idToken2')
        enterPassword.send_keys(password)
        log_and_print('Password textbox found and password value sent')
        driver.find_element_by_id('loginButton_0').click()
        log_and_print('Login button after password clicked')
    except:
        log_and_print(f'Failed to login to Sandbox {sandboxId} in {scriptName}')
        email_recipient = 'konstantin.yanev@isobar.com'
        email_subject = f'Failed to login to Sandbox {sandboxId} in {scriptName}'
        email_text = f'Failed to login to Sandbox {sandboxId} in {scriptName}'
        email_attachment = str(Path.cwd() / scriptLogFile)
        send_email(email_recipient, email_subject, email_text, email_attachment)
        print('email with error sent')
        raise


login_sb()

time.sleep(2)
driver.save_screenshot('./DataFolder/20_SBWelcome.png')


def remove_banner():
    try:
        driver.find_element_by_xpath('//*[@id="pendo-button-f490c282"]').click()
    except:
        pass
    try:
        driver.find_element_by_xpath('//*[@id="pendo-button-79283998"]').click()
    except:
        pass
    try:
        driver.find_element_by_xpath('//*[@id="pendo-button-167df6d2"]').click()
    except:
        pass
    try:
        driver.find_element_by_xpath('//*[@id="pendo-button-2c1837e0"]').click()
    except:
        pass
    try:
        driver.find_element_by_xpath('//*[@id="pendo-button-07b6bf7a"]').click()
    except:
        pass


remove_banner()

try:
    engine.say('I have just logged on sandbox')
    engine.runAndWait()
except:
    pass


def goto_code_deploy():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="site_navigation_column "]/div[3]/span/a/span[1]'))))
    log_and_print('Click Administration')

    remove_banner()

    # Click "Site Development"
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[5]/table/tbody/tr[1]/td[2]/a'))))
    log_and_print('Click Site Development')

    remove_banner()

    # Click "Code Deployment"
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td[5]/table/tbody/tr[1]/td[2]/a'))))
    log_and_print('Click Code Deployment')


goto_code_deploy()
driver.save_screenshot('./DataFolder/21_SBCodeDeploy.png')

# Press Refresh
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[3]/td[1]/table/tbody/tr/td/span/button'))))
log_and_print('Press Refresh')

try:
    engine.say('I have refreshed code version, so webdav link can be responsive')
    engine.runAndWait()
except:
    pass

# Click "Logout"
driver.find_element_by_xpath('//*[@id="bm_header_row"]/td/header/div/div[2]/ul/li[7]/a').click()
time.sleep(7)
log_and_print('Click Logout')
driver.save_screenshot('./DataFolder/22_LoOutSB.png')

try:
    engine.say('I am logged off the sandbox and will transfer compatibility mode file to webdav')
    engine.runAndWait()
except:
    pass

# Set Compatibility mode Url and variable
log_and_print('Set Compatibility mode Url and variable')
compatibilityModeUrl = f'{code}/version1/'
compatibilityModeFile = '.apiversion'

# WebDav upload of Compatibility mode file
log_and_print('Set webdav options')
options = {
    'webdav_hostname': compatibilityModeUrl,
    'webdav_login': username,
    'webdav_password': password,
    'webdav_timeout': 300
}
webdav = webdavClient(options)
webdav.verify = False
log_and_print('Start uploading Compatibility mode file to WebDav')
print(time.asctime(time.localtime(time.time())))
compModeFileUploadStart = time.perf_counter()

try:
    webdav.upload(compatibilityModeFile, compatibilityModeFile)
except Exception as e:
    print(e)
    log_and_print(f'Compatibility mode file transfer in {scriptName} failed')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Compatibility mode file transfer in {scriptName} failed'
    email_text = f'Compatibility mode file transfer in {scriptName} failed'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

compModeFileUploadEnd = time.perf_counter()
log_and_print('Finished uploading Compatibility mode file to WebDav')
print(time.asctime(time.localtime(time.time())))
log_and_print(f'Compatibility mode file was uploaded for {round(compModeFileUploadEnd - compModeFileUploadStart, 2)} seconds.')
log_and_print('Wait 5 seconds')
time.sleep(5)

try:
    engine.say('Compatibility mode file was transferred and sandbox restart process was initiated')
    engine.runAndWait()
except:
    pass

# Stop sandbox
log_and_print('Stop sandbox')

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ' + accessToken['access_token'],
    'Content-Type': 'application/json',
}

data = '{"operation": "stop"}'

try:
    stopSandbox = requests.post(
        f'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/operations',
        headers=headers, data=data).json()

except Exception as e:
    print(e)
    log_and_print(f'Sandbox stop operation in {scriptName} failed')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Sandbox stop operation in {scriptName} failed'
    email_text = f'Sandbox stop operation in {scriptName} failed'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise
log_and_print(f'Stop sandbox api endpoint answer is {stopSandbox}')
log_and_print('Wait 5 seconds')
time.sleep(5)

# Start sandbox
log_and_print('Start sandbox')

data = '{"operation": "start"}'

try:
    startSandbox = requests.post(
        f'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}/operations',
        headers=headers, data=data).json()

except Exception as e:
    print(e)
    log_and_print(f'Sandbox start operation in {scriptName} failed')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Sandbox start operation in {scriptName} failed'
    email_text = f'Sandbox start operation in {scriptName} failed'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

log_and_print(f'Start sandbox api endpoint answer is {startSandbox}')
log_and_print('Wait 5 seconds')
time.sleep(5)

# Request to get sandbox state in every 4 minutes.
while 'started' not in startSandbox:
    log_and_print('Wait another 4 minutes before checking the state of the new sandbox')
    time.sleep(240)

    checkState = requests.get(f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandboxId}",
                              headers=headers).json()

    startSandbox = checkState['data']['state']
    log_and_print(f'Sandbox state is {startSandbox}')

try:
    engine.say('Sandbox was restarted and set in status started')
    engine.runAndWait()
except:
    pass

# Goto Sandbox
driver.get(bm)
log_and_print('Sandbox is loaded')

login_sb()

time.sleep(3)
driver.save_screenshot('./DataFolder/23_SBLogin.png')

try:
    engine.say('I am logged on sandbox')
    engine.runAndWait()
except:
    pass


def site_import_export():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="site_navigation_column "]/div[3]/span/a/span[1]'))))
    log_and_print('Click Administration')

    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[5]/table/tbody/tr[1]/td[2]/a'))))
    log_and_print('Click Site Development')

    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                      '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[11]/td[1]/table/tbody/tr[1]/td[2]/a'))))
    log_and_print('Find and click Site Import Export')


site_import_export()

time.sleep(2)
driver.save_screenshot('./DataFolder/24_SBSiteImpExp.png')


def connect_to_remote():
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                      '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table[5]/tbody/tr/td/table/tbody/tr[2]/td/input[2]'))))
    log_and_print('Click Remote')
    remove_banner()
    driver.find_element_by_xpath('//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[1]/td[2]/input').send_keys(
        stagingHostName)
    driver.find_element_by_xpath('//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[2]/td[2]/input').send_keys(
        username)
    driver.find_element_by_xpath('//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[3]/td[2]/input').send_keys(
        password)
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                      '//*[@id="fetchremotedir"]'))))
    log_and_print('Find Hostname staging, Login and Password')


connect_to_remote()

time.sleep(2)
driver.save_screenshot('./DataFolder/25_SBRemoteToStaging.png')

try:
    engine.say('I am connected remotely to staging.')
    engine.runAndWait()
except:
    pass

# Click Global Data archive from staging
driver.execute_script("arguments[0].click();",
                      WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                  "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(
                                                                                      stagingGDZip)))))
log_and_print('Click Global Data archive from staging Import Radio Button')


def confirm_import():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, 'confirmremoteimport'))))
    log_and_print('Click Import button')
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table[5]/tbody/tr/td[3]/table/tbody/tr/td[1]/button'))))
    log_and_print('Click OK button')
    log_and_print('Wait 5 seconds')
    time.sleep(5)


confirm_import()

try:
    engine.say('Global data import was initiated')
    engine.runAndWait()
except:
    pass


def check_import_status(logger_text, sleep_time):
    span_status = driver.find_element_by_xpath('//*[@id="siteImpexBottom"]/table[5]/tbody/tr[2]/td[5]')
    status_top_cell = span_status.text
    log_and_print(f'Job is in status {status_top_cell}')

    while 'Running' in status_top_cell:
        log_and_print(logger_text)
        time.sleep(sleep_time)
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.NAME, 'refresh'))))
        log_and_print('Press refresh button to check status')
        span_status = driver.find_element_by_xpath('//*[@id="siteImpexBottom"]/table[5]/tbody/tr[2]/td[5]')
        status_top_cell = span_status.text
        log_and_print(f'Job is in status {status_top_cell}')


try:
    engine.say('I will check Global data export status on every 3 minutes')
    engine.runAndWait()
except:
    pass

check_import_status('Wait 3 minutes', 180)

log_and_print('Global Data Import is completed')

try:
    engine.say('Global data import has been completed')
    engine.runAndWait()
except:
    pass

# Click Sites archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(stagingSitesZip)))))
log_and_print('Click Sites archive from staging Import Radio Button')

try:
    engine.say('Sites elements import from staging was initiated. This will take more than 2 hours.')
    engine.runAndWait()
except:
    pass

confirm_import()

remove_banner()

try:
    engine.say('I will check Sites import status on every 7 minutes')
    engine.runAndWait()
except:
    pass

check_import_status('Wait 7 minutes', 420)

log_and_print('Sites import has been completed')

try:
    engine.say('Sites import has been completed')
    engine.runAndWait()
except:
    pass

# Click "Logout"
driver.find_element_by_xpath('//*[@id="bm_header_row"]/td/header/div/div[2]/ul/li[7]/a').click()
time.sleep(3)
log_and_print('Click Logout')
driver.save_screenshot('./DataFolder/26_LogoutSB.png')

try:
    engine.say('We have logged off sandbox and initiated code version upload through webdav. This will take more than hour and a half.')
    engine.runAndWait()
except:
    pass

# WebDav upload of Code Version
options = {
    'webdav_hostname': code,
    'webdav_login': username,
    'webdav_password': password,
    'webdav_timeout': 300
}
webdav = webdavClient(options)
webdav.verify = False
log_and_print('Start uploading code Version to WebDav')
print(time.asctime(time.localtime(time.time())))
webdavUploadStart = time.perf_counter()

try:
    webdav.upload_directory(codeVersion, codeVersion)
except Exception as e:
    print(e)
    log_and_print(f'Webdav transfer in {scriptName} failed')
    email_recipient = 'konstantin.yanev@isobar.com'
    email_subject = f'Webdav transfer in {scriptName} failed'
    email_text = f'Webdav transfer in {scriptName} failed'
    email_attachment = str(Path.cwd() / scriptLogFile)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

webdavUploadEnd = time.perf_counter()
log_and_print('Finished uploading code Version to WebDav')
print(time.asctime(time.localtime(time.time())))
log_and_print(f'Code version was uploaded for {round(webdavUploadEnd - webdavUploadStart, 2)} seconds.')
shutil.rmtree(f'./{codeVersion}')
log_and_print('Remove folder with code version')

try:
    engine.say('Code version upload has been completed')
    engine.runAndWait()
except:
    pass

# Goto Sandbox
driver.get(bm)
log_and_print('Sandbox is loaded')

login_sb()

time.sleep(2)
driver.save_screenshot('./DataFolder/27_SBLogin.png')

try:
    engine.say('I am logged on sandbox again and will try to activate new code version')
    engine.runAndWait()
except:
    pass

goto_code_deploy()

remove_banner()

# Press Activate
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[2]/td[7]/a[2]/span'))))
log_and_print('Press Activate')

# Accept Activation
driver.switch_to_alert().accept()
log_and_print('Switch to Alert')
log_and_print('Wait s seconds')
time.sleep(3)
driver.save_screenshot('./DataFolder/28_SBCodeDeploy.png')
log_and_print('Press Enter')

try:
    engine.say('Code version was activated')
    engine.runAndWait()
except:
    pass

site_import_export()

time.sleep(2)
driver.save_screenshot('./DataFolder/29_SBSiteImpExp.png')

connect_to_remote()

time.sleep(2)
driver.save_screenshot('./DataFolder/30_ConnectToStaging.png')

try:
    engine.say('I am remotely connected to staging again')
    engine.runAndWait()
except:
    pass

# # Click LSR archive from staging
# driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(stagingLSRZip)))))
# logger.debug('Click LSR archive from staging Import Radio Button')
# print('Click LSR archive from staging Import Radio Button')
#
# confirm_import()
#
# check_export_status('Wait 10 minutes', 600)
#
# log_and_print('LSR Import is completed')

# Click Catalog archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(stagingCatalogZip)))))
log_and_print('Click Catalog archive from staging Import Radio Button')

confirm_import()

try:
    engine.say('Catalogs import has been initiated. I will check its status on every 10 minutes')
    engine.runAndWait()
except:
    pass

check_import_status('Wait 10 minutes', 600)

log_and_print('Catalog Import is completed')

try:
    engine.say('Catalogs import has been completed.')
    engine.runAndWait()
except:
    pass

# # Click CSR archive from staging
# driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(stagingCSRZip)))))
# logger.debug('Click CSR archive from staging Import Radio Button')
# print('Click CSR archive from staging Import Radio Button')
#
# confirm_import()
#
# check_export_status('Wait 10 minutes', 600)
#
# log_and_print('CSR Import is completed')

# Click Price Books archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(stagingPBZip)))))
logger.debug('Click Price Books archive from staging Import Radio Button')
print('Click Price Books archive from staging Import Radio Button')

confirm_import()

try:
    engine.say('Price Books import has been initiated. I will check its status on every 3 minutes')
    engine.runAndWait()
except:
    pass

check_import_status('Wait 3 minutes', 180)

log_and_print('Price Books Import is completed')

try:
    engine.say('Price Books import has been completed.')
    engine.runAndWait()
except:
    pass

# Click Inventory lists archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(stagingILZip)))))
log_and_print('Click Inventory lists archive from staging Import Radio Button')

confirm_import()

try:
    engine.say('Inventory lists import has been initiated. I will check its status every minute')
    engine.runAndWait()
except:
    pass

check_import_status('Wait 1 minute', 60)

log_and_print('Inventory lists Import is completed')

try:
    engine.say('Inventory lists import has been completed.')
    engine.runAndWait()
except:
    pass

try:
    engine.say('Connecting to development.')
    engine.runAndWait()
except:
    pass

# Find Hostname, clear field and insert Dev Hostname
driver.find_element_by_xpath('//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[1]/td[2]/input').clear()
driver.find_element_by_xpath('//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[1]/td[2]/input').send_keys(devHostName)
driver.find_element_by_xpath('//*[@id="fetchremotedir"]').click()
driver.save_screenshot('./DataFolder/31_SBREmote2Dev.png')

# Find archive from Development
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(devZip)))))
log_and_print('Find and click Development Import Radio Button')

confirm_import()

try:
    engine.say('Sites elements import from development has been initiated. I will check its status on every 3 minutes')
    engine.runAndWait()
except:
    pass

check_import_status('Wait 3 minutes', 180)

log_and_print('Dev archive Import is completed')

try:
    engine.say('Dev import has been completed')
    engine.runAndWait()
except:
    pass

log_and_print('Import phase end')
print(time.asctime(time.localtime(time.time())))
importPhaseEnd = time.perf_counter()
log_and_print(f'Import phase was performed in {round(importPhaseEnd - importPhaseStart, 2)} seconds.')

try:
    engine.say('Import phase has been completed')
    engine.runAndWait()
except:
    pass

# ______________________________________________________________ IMPORT PHASE END _____________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ REBUILD INDEXES START ________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('Rebuild index phase was initiated')
    engine.runAndWait()
except:
    pass

log_and_print('Rebuild Index start')
print(time.asctime(time.localtime(time.time())))
rebuildIndexStart = time.perf_counter()


def select_site():
    # Click Sandbox - bcgv dropdown
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="SelectedSiteID-wrap"]/span'))))
    log_and_print('Click Sandbox - bcgv dropdown')

    # Click Select a Site
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="SelectedSiteID-wrap"]/span/span[2]/span/span[1]'))))
    log_and_print('Click Select a Site')


def rebuild_index():
    # Click Search
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                               '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[1]/table/tbody/tr[1]/td[2]/a'))))
    log_and_print('Click Search')

    # Click Search Indexes
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                               '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td[1]/table/tbody/tr[1]/td[2]/a'))))
    log_and_print('Click Search Indexes')

    # Check Index Type
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                               '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr[1]/td[1]/input'))))
    log_and_print('Check Index Type')

    # Check Shared Index Type
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                               '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr[8]/td[1]/input'))))
    log_and_print('Check Shared Index Type')

    # Press Rebuild
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                               '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr[10]/td[1]/button/span'))))
    log_and_print('Press Rebuild')


select_site()

# Click Zwilling-BE
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/32_ZwillingBE.png')
log_and_print('Click Zwilling-BE')

rebuild_index()
driver.save_screenshot('./DataFolder/33_RebuildBE.png')

remove_banner()

select_site()

# Click Zwilling-BR
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/34_ZwillingBR.png')
log_and_print('Click Zwilling-BR')

rebuild_index()
driver.save_screenshot('./DataFolder/35_RebuildBR.png')

remove_banner()

select_site()

# Click Zwilling-CA
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/36_ZwillingCA.png')
log_and_print('Click Zwilling-CA')

rebuild_index()
driver.save_screenshot('./DataFolder/37_RebuildCA.png')

remove_banner()

select_site()

# Click Zwilling-DE
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[6]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/38_ZwillingDE.png')
log_and_print('Click Zwilling-DE')

rebuild_index()
driver.save_screenshot('./DataFolder/39_RebuildDE.png')

remove_banner()

select_site()

# Click Zwilling-DK
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[7]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/40_ZwillingDK.png')
log_and_print('Click Zwilling-DK')

rebuild_index()
driver.save_screenshot('./DataFolder/41_RebuildDK.png')

remove_banner()

select_site()

# Click Zwilling-FR
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[8]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/42_ZwillingFR.png')
log_and_print('Click Zwilling-FR')

rebuild_index()
driver.save_screenshot('./DataFolder/43_RebuildFR.png')

remove_banner()

select_site()

# Click Zwilling-GLOBAL
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[9]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/44_ZwillingGlobal.png')
log_and_print('Click Zwilling-GLOBAL')

rebuild_index()
driver.save_screenshot('./DataFolder/45_RebuildGlobal.png')

remove_banner()

select_site()

# Click Zwilling-IT
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[10]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/46_ZwillingIT.png')
log_and_print('Click Zwilling-IT')

rebuild_index()
driver.save_screenshot('./DataFolder/47_RebuildIT.png')

remove_banner()

select_site()

# Click Zwilling-TR
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[11]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/48_ZwillingTR.png')
log_and_print('Click Zwilling-TR')

rebuild_index()
driver.save_screenshot('./DataFolder/49_RebuildTR.png')

remove_banner()

select_site()

# Click Zwilling-USA
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[12]/td/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/50_ZwillingUSA.png')
log_and_print('Click Zwilling-USA')

rebuild_index()
driver.save_screenshot('./DataFolder/51_RebuildUSA.png')

remove_banner()

log_and_print('Rebuild Index end')
print(time.asctime(time.localtime(time.time())))
rebuildIndexEnd = time.perf_counter()
log_and_print(f'Rebuild Index phase was performed in {round(rebuildIndexEnd - rebuildIndexStart, 2)} seconds.')

try:
    engine.say('Rebuild index phase has been completed')
    engine.runAndWait()
except:
    pass

# ______________________________________________________________ REBUILD INDEXES END __________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ CLEAR CACHE START ____________________________________________________________________________________________________________________________________________________________________________

try:
    engine.say('Starting to invalidate cache and set ttl to 0 for every site.')
    engine.runAndWait()
except:
    pass

log_and_print('Clear Cache start')
print(time.asctime(time.localtime(time.time())))
clearCacheStart = time.perf_counter()

# Click "Administration"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="site_navigation_column "]/div[3]/span/a/span[1]'))))
driver.save_screenshot('./DataFolder/52_SBAdministration.png')
log_and_print('Click Administration')

# Click "Sites"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td[1]/table/tbody/tr[1]/td[2]/a'))))
driver.save_screenshot('./DataFolder/53_SBSites.png')
log_and_print('Click Sites')

# Click "Manage Sites"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td[1]/table/tbody/tr[1]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/54_SBManageSites.png')
log_and_print('Click Manage Sites')

# Click "ZWILLING BE"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[2]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/55_ZwillingBE.png')
log_and_print('Click ZWILLING BE')


def clear_cache():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table[1]/tbody/tr/td[3]/a'))))
    log_and_print('Click Cache TAB')

    driver.find_element_by_xpath(
        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[2]/table[1]/tbody/tr[4]/td/table/tbody/tr/td[2]/input').clear()
    driver.find_element_by_xpath(
        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[2]/table[1]/tbody/tr[4]/td/table/tbody/tr/td[2]/input').send_keys(
        '0')
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[2]/table[2]/tbody/tr[5]/td/button[1]'))))
    log_and_print('Set TTL Cache to 0')
    log_and_print('Wait 2 seconds')
    time.sleep(2)
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="staticCacheRoot"]'))))
    log_and_print('Invalidate Static')
    log_and_print('Wait 2 seconds')
    time.sleep(2)
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="pageCacheRoot"]'))))
    log_and_print('Invalidate Entire Page Cache')
    log_and_print('Wait 2 seconds')
    time.sleep(2)


def manage_sites():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="bm-breadcrumb"]/a[3]'))))
    log_and_print('Click Manage Sites')


clear_cache()

driver.save_screenshot('./DataFolder/56_ClearBE.png')

manage_sites()

# Click "ZWILLING BR"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[3]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/57_ZwillingBR.png')
log_and_print('Click ZWILLING BR')

clear_cache()

driver.save_screenshot('./DataFolder/58_ClearBR.png')

manage_sites()

# Click "ZWILLING CA"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[4]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/59_ZwillingCA.png')
log_and_print('Click ZWILLING CA')

clear_cache()

driver.save_screenshot('./DataFolder/60_ClearCA.png')

manage_sites()

# Click "ZWILLING DE"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[5]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/61_ZwillingDE.png')
log_and_print('Click ZWILLING DE')

clear_cache()

driver.save_screenshot('./DataFolder/62_ClearDE.png')

manage_sites()

# Click "ZWILLING DK"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[6]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/63_ZwillingDK.png')
log_and_print('Click ZWILLING DK')

clear_cache()

driver.save_screenshot('./DataFolder/64_ClearDK.png')

manage_sites()

# Click "ZWILLING FR"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[7]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/65_ZwillingFR.png')
log_and_print('Click ZWILLING FR')

clear_cache()

driver.save_screenshot('./DataFolder/66_ClearFR.png')

manage_sites()

# Click "ZWILLING Global"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[8]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/67_ZwillingGlobal.png')
log_and_print('Click ZWILLING Global')

clear_cache()

driver.save_screenshot('./DataFolder/68_ClearGlobal.png')

manage_sites()

# Click "ZWILLING IT"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[9]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/69_ZwillingIT.png')
log_and_print('Click ZWILLING IT')

clear_cache()

driver.save_screenshot('./DataFolder/70_ClearIT.png')

manage_sites()

# Click "ZWILLING TR"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[10]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/71_ZwillingTR.png')
log_and_print('Click ZWILLING TR')

clear_cache()

driver.save_screenshot('./DataFolder/72_ClearTR.png')

manage_sites()

# Click "ZWILLING USA"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[11]/td[2]/a'))))
time.sleep(2)
driver.save_screenshot('./DataFolder/73_ZwillingUSA.png')
log_and_print('Click ZWILLING USA')

clear_cache()

driver.save_screenshot('./DataFolder/74_ClearUSA.png')

log_and_print('Clear Cache end')
print(time.asctime(time.localtime(time.time())))
clearCacheEnd = time.perf_counter()
log_and_print(f'Clear cache phase was performed in {round(clearCacheEnd - clearCacheStart, 2)} seconds.')

try:
    engine.say('Clear cache has been completed.')
    engine.runAndWait()
except:
    pass

# ______________________________________________________________ CLEAR CACHE END ______________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ LOGOUT CLOSE BROWSER AND SEND EMAIL ______________________________________________________________________________________________________________________________________________________________________________

remove_banner()

# Click "Logout"
try:
    driver.find_element_by_xpath('//*[@id="bm_header_row"]/td/header/div/div[2]/ul/li[7]/a/span').click()
    log_and_print('Click Logout')
    time.sleep(3)
    driver.save_screenshot('./DataFolder/75_LogoutSB.png')
except:
    pass

driver.close()
driver.quit()
log_and_print('Browser closed and driver quit')

# Ending point of the time counter
scriptFinishTime = time.perf_counter()
log_and_print(f'Script execution time is {round(scriptFinishTime - scriptStartTime, 2)} seconds.')

# Copy logfile to folder with script data
shutil.copy(scriptLogFile, 'DataFolder')

# Create zip file of the directory with all script data and delete directory
log_and_print('Create zip file of the directory with all screenshots and delete directory')
shutil.make_archive('ZwillingDemandwareReleaseVerify', 'zip', 'DataFolder')
shutil.rmtree('./DataFolder')

# Send email with attached zip containing screenshots
log_and_print('Send email with attached zip containing screenshots')
email_recipient = 'konstantin.yanev@isobar.com'
email_subject = 'Demandware Release verification on Zwilling'
email_text = f'Hi Team, this is to inform you that on demand sandbox preparation for Demandware Release verification on Zwilling has been completed. Sandbox ID is {sandboxId}. You can performed validation on site following the standard procedure at {bm}.'
email_attachment = str(Path.cwd() / 'ZwillingDemandwareReleaseVerify.zip')
send_email(email_recipient, email_subject, email_text, email_attachment)

# Delete archive with screenshots
print('Delete archive with screenshots')
os.remove('ZwillingDemandwareReleaseVerify.zip')