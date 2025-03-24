# Remember... The Force will be with you. Always.

# This will do the following
# 1 - Create new on demand sandbox
# 2 - Wait until is in status "started"
# 3 - Login to ODS BM
# 4 - Goto code deploy section
# 5 - Press refresh button in order to make WebDav for this sandbox to be available immediately
# 6 - Log out
# 7 - Establish connection to WebDav and upload .apiversion file with desired compatibility mode
# 8 - Stop ODS
# 9 - Start ODS

import os
import pyotp
import time
import json
import requests
import slack_sdk
import urllib3
import logging
import url_links
import constants as const
from selenium import webdriver
from new_ods_json import create_json
from webdav3.client import Client as webdavClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

script_name = 'create-ods-and-change-compatibility-mode'

log_format = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{const.today_is}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

urllib3.disable_warnings()


def log_and_print(text):
    print(text)
    logger.info(text)


def get_otp_code():
    get_otp = pyotp.TOTP(const.otp_qr)
    return get_otp.now()


# noinspection PyBroadException
def slack_post(slack_message):
    try:
        slack_channel = '#ods-operations'
        slack_client = slack_sdk.WebClient(token=const.slack_token)
        slack_client.chat_postMessage(channel=slack_channel, text=slack_message)
    except:
        pass


def login_bm():
    # noinspection PyBroadException
    try:
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, 'loginSSO'))))
    except:
        pass
    try:
        log_and_print('Login with Account Manager')
        driver.find_element(By.ID, 'idToken1').send_keys(const.my_ods_email)
        log_and_print('Username textbox found and User Name value sent')
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'loginButton_0'))))
        log_and_print('Login button after username clicked')
        driver.find_element(By.ID, 'idToken2').send_keys(const.my_ods_pass)
        log_and_print('Password textbox found and password value sent')
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'loginButton_0'))))
        log_and_print('Login button after password clicked')
        driver.find_element(By.XPATH, '//*[@id="input-9"]').send_keys(get_otp_code())
        log_and_print('OTP sent')
        driver.find_element(By.XPATH,
                            '//*[@id="root"]/vaasdist-verify/div/vaas-verify/div/vaas-verify-totp/vaas-container/div/div/slot/div/form/div/vaas-button-brand/button').click()
        log_and_print('Verify after OTP clicked')
        slack_post('Logged in BM')
    except Exception as exc:
        log_and_print(exc)
        slack_post(f'{exc}\nFailed to login to ods')
        raise


def logout_ods():
    # Find "Logout" and click it
    log_and_print('Click "Logout"')
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div[1]/ccbm/div[2]/header/div[1]/div[2]/ul/li[6]/div/button'))))
    log_and_print('Logout success')
    slack_post('Logout success')


def goto_code_deploy():
    # Click "Administration"
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '/html/body/div[4]/div[1]/ccbm/div[2]/header/div[2]/nav/ul/li[2]/div/a'))))
    log_and_print('Click Administration')

    # Click "Site Development"
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="menuoverview"]/div/div[1]/div[4]/article/div/header/div[2]/a'))))
    log_and_print('Click Site Development')

    # Click "Code Deployment"
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="menuoverview"]/div/div[1]/div[2]/article/div/header/div[2]/a'))))
    log_and_print('Click Code Deployment')


def check_ods_status(var_input=None):
    while 'started' not in var_input:
        time.sleep(180)

        check_state = requests.get(f"{url_links.SANDBOX_URL}/{sandbox_id}",
                                   headers=headers).json()

        var_input = check_state['data']['state']


prefs = {
    'download.default_directory': os.getcwd(),
    'directory_upgrade': True
}
options = webdriver.ChromeOptions()
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--start-maximized')
options.headless = True
options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome('chromedriver', service_args=["--verbose", "--log-path=chromedriver.log"], options=options)
driver.implicitly_wait(30)

slack_post('Attempt to create ODS')

data = {
    'grant_type': 'password',
    'username': const.username,
    'password': const.password
}

access_token_response = requests.post(const.access_token_auth_url, data=data,
                                      verify=False,
                                      allow_redirects=False, auth=(const.client_id, const.client_secret))

try:
    access_token = json.loads(access_token_response.text)
except ValueError as value_error:
    log_and_print(value_error)
    slack_post(f'Failed to get authorization for access token in {script_name} job.')
    raise

try:
    headers = {
        'Authorization': 'Bearer ' + access_token['access_token']
    }
except KeyError as key_error:
    log_and_print(key_error)
    slack_post(
        f'Failed to get access token in {script_name} job. Some of the credentials are invalid. Check them carefully.')
    raise

slack_post('Attempt to create ODS')

create_new_sandbox = requests.post(url_links.SANDBOX_URL,
                                   headers=headers, verify=False, json=create_json).json()

sandbox_id = create_new_sandbox['data']['id']
log_and_print(sandbox_id)
realm = create_new_sandbox['data']['realm']
log_and_print(realm)
state = create_new_sandbox['data']['state']
log_and_print(state)
bm = create_new_sandbox['data']['links']['bm']
log_and_print(bm)
code = create_new_sandbox['data']['links']['code']
log_and_print(code)

check_ods_status(state)

slack_post(f'Sandbox {sandbox_id} in realm {realm} was created, started and available at {bm}.')

driver.get(bm)

login_bm()

goto_code_deploy()

# Press Refresh
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[3]/td[1]/table/tbody/tr/td/span/button'))))
slack_post('Sandbox is refreshed')
log_and_print('Press Refresh')

logout_ods()

slack_post('Starting to change Compatibility mode')

compatibility_mode_url = f'{code}/version1/'
compatibility_mode_file = '.apiversion'

options = {
    'webdav_hostname': compatibility_mode_url,
    'webdav_login': const.my_ods_email,
    'webdav_password': const.my_ods_pass,
    'webdav_timeout': 300
}

webdav = webdavClient(options)
webdav.verify = False

try:
    webdav.upload(compatibility_mode_file, compatibility_mode_file)
except Exception as e:
    log_and_print(e)
    slack_post(f'Compatibility mode file transfer in {script_name} failed')
    raise

slack_post('Compatibility mode has been changed')
time.sleep(5)

slack_post('Restarting sandbox')

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ' + access_token['access_token'],
    'Content-Type': 'application/json',
}

data = '{"operation": "stop"}'

try:
    stop_sandbox = requests.post(
        f'{url_links.SANDBOX_URL}/{sandbox_id}/operations',
        headers=headers, data=data).json()

except Exception as e:
    log_and_print(e)
    slack_post(f'Sandbox stop operation in {script_name} failed')
    raise

time.sleep(5)

data = '{"operation": "start"}'

try:
    start_sandbox = requests.post(
        f'{url_links.SANDBOX_URL}/{sandbox_id}/operations',
        headers=headers, data=data).json()

except Exception as e:
    log_and_print(e)
    slack_post(f'Sandbox start operation in {script_name} failed')
    raise

time.sleep(5)

check_ods_status(start_sandbox)

slack_post('Sandbox has been restarted')
