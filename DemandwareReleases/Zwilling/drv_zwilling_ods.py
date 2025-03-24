# "Size matters not. Look at me. Judge me by my size, do you? Hmm? Hmm. And well you should not.
# For my ally is the Force, and a powerful ally it is. Life creates it, makes it grow.
# Its energy surrounds us and binds us. Luminous beings are we, not this crude matter.
# You must feel The Force around you; here, between you, me, the tree, the rock, everywhere, yes.
# Even between the land and the ship."


# This is used to verify Demandware Releases before replication from Staging to Production
# Login to Salesforce Business Manager(SFCC) - Staging Instance and make exports.
# Login to Salesforce Business Manager(SFCC) - Development Instance and make export.
# Create new On Demand Sandbox and wait for it to be in state "started"
# Change On Demand Sandbox Compatibility mode by transferring a ".apiversion" file with "api.version=18.10" content to active code version in Cartridges
# Login ot newly created ODS and make imports.
# Rebuild Indexes
# Clear Cache
# Exports and imports algorithms can be found at https://wiki.isobarsystems.com/pages/viewpage.action?spaceKey=SUPTEAM&title=How+to+prepare+sandbox+for+Demandware+release+since+13.4


import pyotp
import time
import logging
import shutil
import os
import requests
from pathlib import Path
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from urllib.parse import urlparse
import urllib3
from webdav3.client import Client as webdavClient
import constants as const
from set_email import send_email
import url_links
from client_creds_token import get_access_token
from browser_setup_chrome import my_browser
from ods_parameters import ods_config
from slack_messaging import slack_post

script_start_time = time.perf_counter()

SCRIPT_NAME = 'drv-zwilling-ods'
PROJECT_NAME = 'ZWG'
PROJECT_INSTANCE = 'Stag'
PROJECT_NAME_DEV = 'ZWG'
PROJECT_INSTANCE_DEV = 'Dev'
ZWILLING_DEV = url_links.zwilling_dev
DEV_HOST_NAME = urlparse(ZWILLING_DEV).hostname
ZWILLING_STAGING = url_links.zwilling_staging
STAGING_HOST_NAME = urlparse(ZWILLING_STAGING).hostname

# Create and configure logger
log_format = '%(levelname)s %(asctime)s - %(message)s'
SCRIPT_LOG_FILE = f'{SCRIPT_NAME}-{const.today_is}.log'
logging.basicConfig(filename=SCRIPT_LOG_FILE,
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


def close_popup_and_reload_cookies():
    cookies_before = driver.get_cookies()

    try:
        popup_element = driver.find_element_by_class_name("bb-button _pendo-button-custom _pendo-button")
        popup_element.find_element_by_xpath(".//button[contains(text(), 'Skip for now')]").click()
    except NoSuchElementException:
        pass

    for cookie in cookies_before:
        driver.add_cookie(cookie)

    driver.refresh()


def login_bm(bm_instance):
    # noinspection PyBroadException
    try:
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'loginSSO'))))
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
        slack_post(f'Failed to login to {bm_instance}')
        driver.save_screenshot('FailedBMLogin.png')
        raise


def goto_site_import_export():
    log_and_print('Click Administration')
    try:
        # Click "Administration"
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/div[4]/div[1]/ccbm/div[2]/header/div[2]/nav/ul/li[2]/div/a'))))
    except Exception as exc:
        slack_post('Failed to click Administration')
        log_and_print(exc)
        driver.save_screenshot('FailedAdministration.png')
        raise

    log_and_print('Click Site Development')
    try:
        # Click "Site Development"
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="menuoverview"]/div/div[1]/div[4]/a/article/div/header/div[2]/h2/span'))))
    except Exception as exc:
        slack_post('Failed to click Site Development')
        log_and_print(exc)
        driver.save_screenshot('FailedSiteDevelopment.png')
        raise

    log_and_print('Click Site Import Export')
    try:
        # Click "Site Import Export"
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="menuoverview"]/div/div[1]/div[9]/a/article/div/header/div[2]/h2/span'))))
    except Exception as exc:
        slack_post('Failed to click Site Import Export')
        log_and_print(exc)
        driver.save_screenshot('FailedSiteImportExport.png')
        raise


def goto_code_deploy():
    log_and_print('Click Administration')
    try:
        # Click "Administration"
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/div[4]/div[1]/ccbm/div[2]/header/div[2]/nav/ul/li[2]/div/a'))))
    except Exception as exc:
        slack_post('Failed to click Administration')
        log_and_print(exc)
        driver.save_screenshot('FailedAdministration.png')
        raise

    log_and_print('Click Site Development')
    try:
        # Click "Site Development"
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="menuoverview"]/div/div[1]/div[4]/a/article/div/header/div[2]/h2/span'))))
    except Exception as exc:
        slack_post('Failed to click Site Development')
        log_and_print(exc)
        driver.save_screenshot('FailedSiteDevelopment.png')
        raise

    log_and_print('Click Code Deployment')
    try:
        # Click "Code Deployment"
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="menuoverview"]/div/div[1]/div[2]/a/article/div/header/div[2]/h2/span'))))
    except Exception as exc:
        slack_post('Failed to click Code Deployment')
        log_and_print(exc)
        driver.save_screenshot('FailedCodeDeployment.png')
        raise


def press_export():
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="export"]'))))
    log_and_print('Press "Export button"')
    time.sleep(5)


def check_export_import_status(logger_text, sleep_time):
    time.sleep(10)
    span_element = driver.find_element(By.CSS_SELECTOR, '.table_detail.s.top.center')
    status_top_cell = span_element.text
    log_and_print(f'Get Status column top cell value = {status_top_cell}')

    while 'Running' in status_top_cell:
        log_and_print(logger_text)
        time.sleep(sleep_time)
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.NAME, 'refresh'))))
        log_and_print('Press refresh button to check status')
        span_element = driver.find_element(By.CSS_SELECTOR, '.table_detail.s.top.center')
        status_top_cell = span_element.text
        log_and_print(f'Job is in status {status_top_cell}')


def logout_bm():
    # Find "Logout" and click it
    log_and_print('Click "Logout"')
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="ext-gen9"]/div[4]/div[1]/ccbm/div[2]/header/div[1]/div[2]/ul/li[6]/div/button/span'))))
    log_and_print('Logout success')
    slack_post('Logout success')


def logout_ods():
    # Find "Logout" and click it
    log_and_print('Click "Logout"')
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[4]/div[1]/ccbm/div[2]/header/div[1]/div[2]/ul/li[6]/div/button'))))
    log_and_print('Logout success')
    slack_post('Logout success')


def connect_to_remote(remote_instance):
    try:
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                          '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table[5]/tbody/tr/td/table/tbody/tr[2]/td/input[2]'))))
        log_and_print('Click Remote')
        # remove_banner()
        driver.find_element(By.XPATH,
                            '//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[1]/td[2]/input').send_keys(
            STAGING_HOST_NAME)
        driver.find_element(By.XPATH,
                            '//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[2]/td[2]/input').send_keys(
            const.my_ods_email)
        driver.find_element(By.XPATH,
                            '//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[3]/td[2]/input').send_keys(
            const.my_ods_pass)
        driver.execute_script("arguments[0].click();",
                              WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                          '//*[@id="fetchremotedir"]'))))
        log_and_print('Find Hostname staging, Login and Password')
    except Exception as exc:
        log_and_print(exc)
        log_and_print(f'Failed to connect to {remote_instance}')
        driver.save_screenshot('FailedRemoteConnect.png')
        raise


def confirm_import():
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, 'confirmremoteimport'))))
    log_and_print('Click Import button')
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table[5]/tbody/tr/td[3]/table/tbody/tr/td[1]/button'))))
    log_and_print('Click OK button')
    log_and_print('Wait 5 seconds')
    time.sleep(5)


def select_site():
    # Click Sandbox - bcgv dropdown
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="SelectedSiteID-wrap"]/span/span[1]'))))
    log_and_print('Click Sandbox - bcgv dropdown')

    # Click Select a Site
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="SelectedSiteID-wrap"]/span/span[2]/span/span[1]'))))
    log_and_print('Click Select a Site')


# noinspection PyBroadException
def rebuild_index(website):
    try:
        # Click Search
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="menuoverview"]/div/div[1]/div[3]/article/div/header/div[2]/a'))))
        log_and_print('Click Search')

        # Click Search Indexes
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="menuoverview"]/div/div[1]/div[1]/article/div/header/div[2]/a'))))
        log_and_print('Click Search Indexes')

        # Check Index Type
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr[1]/td[1]/input'))))
        log_and_print('Check Index Type')

        # Check Shared Index Type
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr[8]/td[1]/input'))))
        log_and_print('Check Shared Index Type')

        # Press Rebuild
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr[10]/td[1]/button/span'))))
        log_and_print('Press Rebuild')
        time.sleep(60)
    except:
        log_and_print(f'Rebuild Index Failed for {website}')
        slack_post(f'Rebuild Index Failed for {website}')
        driver.save_screenshot('FailedRebuildIndex.png')


def clear_cache():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table[1]/tbody/tr/td[3]/a'))))
    log_and_print('Click Cache TAB')

    driver.find_element(By.XPATH,
                        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[2]/table[1]/tbody/tr[4]/td/table/tbody/tr/td[2]/input').clear()
    driver.find_element(By.XPATH,
                        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[2]/table[1]/tbody/tr[4]/td/table/tbody/tr/td[2]/input').send_keys(
        '0')
    config_clear_cache(
        '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[2]/table[2]/tbody/tr[5]/td/button[1]',
        'Set TTL Cache to 0',
    )

    config_clear_cache(
        '//*[@id="staticCacheRoot"]', 'Invalidate Static'
    )

    config_clear_cache(
        '//*[@id="pageCacheRoot"]', 'Invalidate Entire Page Cache'
    )


def config_clear_cache(arg0, arg1):
    driver.execute_script(
        "arguments[0].click();",
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, arg0))
        ),
    )

    log_and_print(arg1)
    log_and_print('Wait 2 seconds')
    time.sleep(2)


def manage_sites():
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="bm-breadcrumb"]/a[3]'))))
    log_and_print('Click Manage Sites')


slack_post(
    'Sandbox preparation process for Demandware Release validation on Zwilling has been started, so grab a coffee')

# Create folder "DataFolder"
os.mkdir('DataFolder')
log_and_print('Create folder "DataFolder"')

# Get Current working directory
current_directory = os.getcwd()
log_and_print(f'Current Working Directory is {current_directory}')

# _______________________________________________________________ BROWSER SETUP __________________________________________________________________________________________________________________________________________________________________________________

slack_post('Setting up browser')
driver = my_browser(download_directory=current_directory)
driver.implicitly_wait(30)
slack_post('Browser setup completed')

# ______________________________________________________________ BROWSER SETUP END _________________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ EXPORT PHASE START ________________________________________________________________________________________________________________________________________________________________________________

slack_post('Export phase Start')

# Set timing for Export phase
log_and_print('Export phase start')
export_phase_start = time.perf_counter()

# Load Zwilling Staging
driver.get(ZWILLING_STAGING)
log_and_print('Zwilling staging is loaded')

login_bm(ZWILLING_STAGING)

# Find and extract Staging version
time.sleep(5)
stag_version = driver.find_element(By.CLASS_NAME, 'footer__version').get_attribute('title')
stag_version = stag_version[:4]
log_and_print(f'Staging version is {stag_version}')
staging_version = stag_version.replace('.', '')

slack_post('Log on Staging')

goto_site_import_export()

check_export_import_status('Wait 5 minutes', 300)

slack_post('Staging exports preparation start')

# Configure sites archive name
export_date_staging = datetime.now().strftime('%Y%m%d')
staging_sites_archive = f'{staging_version}_SitesOps_{PROJECT_NAME}_{PROJECT_INSTANCE}_{export_date_staging}'
staging_sites_zip = f'{staging_sites_archive}.zip'
log_and_print(f'Sites archive name is {staging_sites_archive}')

# Find Archive name textbox and send value to it
driver.find_element(By.NAME, 'exportFile').send_keys(staging_sites_archive)
log_and_print('Archive name textbox found and value sent')

# Click "Sites" checkbox
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//span[text() = "Sites"]/preceding-sibling::input'))))
log_and_print('Click "Sites" checkbox')

# Click "Sites" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "Sites" plus')

# Click "zwilling-us" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-us" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-ca" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-ca" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-global" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-global" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-tr" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-tr" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-de" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-de" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-fr" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-fr" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-it" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-it" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Uncheck zwilling-br"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[8]/div/div[1]/input'))))
log_and_print('Uncheck zwilling-br')

# Click "zwilling-be" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-be" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-dk" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-dk" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-uk" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[11]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-uk" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[11]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[11]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-es" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[12]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-es" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[12]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[12]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

# Click "zwilling-jp" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[13]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-jp" plus')

# Uncheck "Custom objects"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[13]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck "Custom objects"')

# Uncheck "Site Preferences"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[13]/ul/li[19]/div/div[1]/input'))))
log_and_print('Uncheck "Site Preferences"')

press_export()

slack_post('Sites export initiated. Check export status on every 200 seconds')

check_export_import_status('Wait 200 seconds', 200)

log_and_print('Sites export is ready')

slack_post(f'Sites export is ready. Export name is {staging_sites_archive}')

# Configure Catalog archive name
export_date_staging = datetime.now().strftime('%Y%m%d')
staging_catalog_archive = f'{staging_version}_CatalogOps_{PROJECT_NAME}_{PROJECT_INSTANCE}_{export_date_staging}'
staging_catalog_zip = f'{staging_catalog_archive}.zip'
log_and_print(f'Catalogs archive name is {staging_catalog_archive}')

# Find Archive name textbox and send value to it
driver.find_element(By.NAME, 'exportFile').send_keys(staging_catalog_archive)
log_and_print('Archive name textbox found and value sent')

# Check Catalogs
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//span[text() = "Catalogs"]/preceding-sibling::input'))))
log_and_print('Check Catalogs')

# Click Catalogs plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[4]/div/div[1]/img[1]'))))
log_and_print('Click Catalogs plus')

# Uncheck zwilling-storefront-catalog-br
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[4]/ul/li[5]/div/div[1]/input'))))
log_and_print('Uncheck zwilling-storefront-catalog-br')

press_export()

slack_post('Catalogs export initiated. Check export status on every 4 minutes')

check_export_import_status('Wait 4 minutes', 240)

log_and_print('Catalogs export is ready')

slack_post(f'Catalogs export is ready. Export name is {staging_catalog_archive}')

# Configure Price Books archive name
export_date_staging = datetime.now().strftime('%Y%m%d')
staging_pb_archive = f'{staging_version}_PriceBooksOps_{PROJECT_NAME}_{PROJECT_INSTANCE}_{export_date_staging}'
staging_pb_zip = f'{staging_pb_archive}.zip'
log_and_print(f'Price Books archive name is {staging_pb_archive}')

# Find Archive name textbox and send value to it
driver.find_element(By.NAME, 'exportFile').send_keys(staging_pb_archive)
log_and_print('Archive name textbox found and value sent')

# Check Price Books
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[6]/div/div[1]/input'))))
log_and_print('Check Price Books')

# Click Price Books plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[6]/div/div[1]/img[1]'))))
log_and_print('Click Price Books plus')

# Uncheck br-brl-msrp-bundletest
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[6]/ul/li[8]/div/div[1]/input'))))
log_and_print('Uncheck br-brl-msrp-bundletest')

# Uncheck br-brl-msrp-prices
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[6]/ul/li[9]/div/div[1]/input'))))
log_and_print('Uncheck br-brl-msrp-prices')

# Uncheck br-brl-promotion-prices
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[6]/ul/li[10]/div/div[1]/input'))))
log_and_print('Uncheck br-brl-promotion-prices')

press_export()

slack_post('Price Books export initiated. Check export status on every 30 seconds')

check_export_import_status('Wait 30 seconds', 30)

log_and_print('Price Books Export is ready')

slack_post(f'Price Books export is ready. Export name is {staging_pb_archive}')

# Configure Inventory Lists archive name
export_date_staging = datetime.now().strftime('%Y%m%d')
staging_il_archive = f'{staging_version}_InventoryListsOps_{PROJECT_NAME}_{PROJECT_INSTANCE}_{export_date_staging}'
staging_il_zip = f'{staging_il_archive}.zip'
log_and_print(f'Inventory Lists archive name is {staging_il_archive}')

# Find Archive name textbox and send value to it
driver.find_element(By.NAME, 'exportFile').send_keys(staging_il_archive)
log_and_print('Archive name textbox found and value sent')

# Check Inventory Lists
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[7]/div/div[1]/input'))))
log_and_print('Check Inventory Lists')

# Click Inventory Lists plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[7]/div/div[1]/img[1]'))))
log_and_print('Click Inventory Lists plus')

# Uncheck inventory-br
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[7]/ul/li[3]/div/div[1]/input'))))
log_and_print('Uncheck inventory-br')

press_export()

slack_post('Inventory Lists export initiated. Check export status on every 30 seconds')

check_export_import_status('Wait 30 seconds', 30)

log_and_print('Inventory Lists export is ready')

slack_post(f'Inventory Lists export is ready. Export name is {staging_il_archive}')

# Configure Global Data archive name
export_date_staging = datetime.now().strftime('%Y%m%d')
staging_gd_archive = f'{staging_version}_GlobalDataOps_{PROJECT_NAME}_{PROJECT_INSTANCE}_{export_date_staging}'
staging_gd_zip = f'{staging_gd_archive}.zip'
log_and_print(f'Global Data archive name is {staging_gd_archive}')

# Find Archive name textbox and send value to it
driver.find_element(By.NAME, 'exportFile').send_keys(staging_gd_archive)
log_and_print('Archive name textbox found and value sent')

# Click "Global Data" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/div/div[1]/img[1]'))))
log_and_print('Find "Global Data plus and click it')

# Check Locales
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[1]/div/div[1]/input'))))
log_and_print('Check Locales')

# Check Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[2]/div/div[1]/input'))))
log_and_print('Check Preferences')

# Check Global Custom Objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[3]/div/div[1]/input'))))
log_and_print('Check Global Custom Objects')

# Check Meta Data
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[6]/div/div[1]/input'))))
log_and_print('Check Meta Data')

# Check Geolocations
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[10]/div/div[1]/input'))))
log_and_print('Check Geolocations')

# Check OAuth Providers
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[12]/div/div[1]/input'))))
log_and_print('Check OAuth Providers')

# Check OCAPI Settings
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[13]/div/div[1]/input'))))
log_and_print('Check OCAPI Settings')

# Check WebDAV Client Permissions
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[14]/div/div[1]/input'))))
log_and_print('Check WebDAV Client Permissions')

# Check Services
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[15]/div/div[1]/input'))))
log_and_print('Check Services')

# Check CSC Settings
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[16]/div/div[1]/input'))))
log_and_print('Check CSC Settings')

# Check Page Meta Tags
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[17]/div/div[1]/input'))))
log_and_print('Check Page Meta Tags')

# Check Price Adjustment Limits
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[18]/div/div[1]/input'))))
log_and_print('Check Price Adjustment Limits')

# Check CSRF Allowlists
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check CSRF Allowlists')

# Check Sorting Rules
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[9]/ul/li[20]/div/div[1]/input'))))
log_and_print('Check Sorting Rules')

press_export()

slack_post('Global Data export initiated. Check export status on every 7 minutes')

check_export_import_status('Wait 7 minutes', 420)

log_and_print('Global Data export is ready')

slack_post(f'Global Data export is ready. Export name is {staging_gd_archive}')

goto_code_deploy()

# Find, extract and click Active version
codeVersion = driver.find_element(By.XPATH,
                                  '//img[@title="Active version."]/following::*/a').get_attribute(
    'innerText')
log_and_print(f'Code version is {codeVersion}')
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//img[@title="Active version."]/following::*/a'))))
log_and_print('Find and click active version')

# Click Download
log_and_print('Wait 5 seconds')
time.sleep(5)
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="downloadButton"]'))))
log_and_print('Click Download')

slack_post(f'Code Version {codeVersion} download initiated. It will take up to 1 minute')

log_and_print('Wait 60 seconds')
time.sleep(60)

# Unzip downloaded zip and delete it
try:
    unpack_zip = f'{codeVersion}.zip'
    shutil.unpack_archive(str(unpack_zip), current_directory)
    os.remove(unpack_zip)
    log_and_print('Unzip downloaded zip with Code version and delete zip')
    log_and_print('Wait 15 seconds')
    time.sleep(15)
except Exception as e:
    print(e)
    log_and_print(f'Code version download in {SCRIPT_NAME} failed')
    slack_post(
        f'Code version download in {SCRIPT_NAME} failed. Check in Salesforce Business Manager if Download button is responsive')
    raise

slack_post('Code version has been downloaded and unzipped')

logout_bm()

time.sleep(3)
slack_post('Log off from Staging')

# ______________________________________________________________ Staging End ________________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ Dev start __________________________________________________________________________________________________________________________________________________________________________________

# Get Zwilling Dev Site
driver.get(ZWILLING_DEV)
time.sleep(2)
log_and_print('Get Zwilling Dev Site')

login_bm(ZWILLING_DEV)

# Find and extract Staging version
development_version = driver.find_element(By.CLASS_NAME, 'footer__version').get_attribute('title')
development_version = development_version[:4]
log_and_print(f'SFCC version on Dev is {development_version}')
dev_version = development_version.replace('.', '')

slack_post('Log on Development')

goto_site_import_export()

# Configure archive name
export_date_dev = datetime.now().strftime('%Y%m%d')
dev_archive = f'{dev_version}_SitesOPS_{PROJECT_NAME_DEV}_{PROJECT_INSTANCE_DEV}_{export_date_dev}'
dev_zip = f'{dev_archive}.zip'
log_and_print(f'Dev archive name is {dev_archive}')

# Find Archive name textbox and send value to it
driver.find_element(By.NAME, 'exportFile').send_keys(dev_archive)
log_and_print('Archive name textbox found and value sent')

# Click "Sites" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "Sites" plus')

# Click "zwilling-us" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-us" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[1]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-ca" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-ca" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[2]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-global" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-global" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[3]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-tr" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-tr" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[4]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-de" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-de" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[5]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-fr" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-fr" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[6]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-it" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-it" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[7]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-be" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-be" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[9]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-dk" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-dk" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[10]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-uk" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[11]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-uk" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[11]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[11]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-es" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[12]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-es" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[12]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[12]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

# Click "zwilling-jp" plus
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[13]/div/div[1]/img[1]'))))
log_and_print('Click "zwilling-jp" plus')

# Check Custom objects
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[13]/ul/li[9]/div/div[1]/input'))))
log_and_print('Check Custom objects')

# Check Site Preferences
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="ext-gen21"]/div/li[1]/ul/li[13]/ul/li[19]/div/div[1]/input'))))
log_and_print('Check Site Preferences')

press_export()

slack_post(f'Sites export from Development initiated. Export name is {dev_archive}')

logout_bm()

time.sleep(3)
log_and_print('Click "Logoff" button')

log_and_print('Export phase end')
export_phase_end = time.perf_counter()
log_and_print(f'Export phase was performed in {round(export_phase_end - export_phase_start, 2)} seconds.')
slack_post(
    f'Export phase has been completed. It was performed in {round(export_phase_end - export_phase_start, 2)} seconds.')

# ______________________________________________________________ EXPORT PHASE END ____________________________________________________________________________________________________________________________________________________________________________

# ______________________________________________________________ SANDBOX PREPARATION _________________________________________________________________________________________________________________________________________________________________________


slack_post('Attempt to create ODS')

# Set timing for Sandbox preparation
log_and_print('Sandbox preparation start')
sandbox_preparation_start = time.perf_counter()

try:
    access_token = get_access_token()
except ValueError as value_error:
    log_and_print(value_error)
    log_and_print(
        'Failed to get authorization for access token.')
    slack_post(f'Failed to get authorization for access token in {SCRIPT_NAME} job')
    raise

try:
    headers = {'Authorization': f'Bearer {access_token}'}
except KeyError as key_error:
    log_and_print(key_error)
    log_and_print('Some of the credentials are invalid. Check them carefully')
    slack_post(
        'Failed to get access token in {SCRIPT_NAME} job. Some of the credentials are invalid. Check them carefully.')
    raise
log_and_print('We got the access token')

create_json = ods_config

# Make request to url for creating new sandbox
log_and_print('First request endpoint - create new sandbox')

create_new_sandbox = requests.post('https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes',
                                   headers=headers, verify=False, json=create_json).json()

log_and_print(f'First request endpoint answer is {create_new_sandbox}')

new_sandbox = []

# Extract all data from returned dictionary
log_and_print('Extract all data from returned dictionary')
sandbox_id = create_new_sandbox['data']['id']
log_and_print(f'Sandbox ID is - {sandbox_id}')
new_sandbox.append(sandbox_id)
realm = create_new_sandbox['data']['realm']
log_and_print(f'Realm is - {realm}')
new_sandbox.append(realm)
instance = create_new_sandbox['data']['instance']
log_and_print(f'Instance is - {instance}')
new_sandbox.append(instance)
versions = create_new_sandbox['data']['versions']
log_and_print(f'Version is - {versions}')
new_sandbox.append(versions)
state = create_new_sandbox['data']['state']
log_and_print(f'State is - {state}')
new_sandbox.append(state)
created_at = create_new_sandbox['data']['createdAt']
log_and_print(f'Created at - {created_at}')
new_sandbox.append(created_at)
created_by = create_new_sandbox['data']['createdBy']
log_and_print(f'Created by - {created_by}')
new_sandbox.append(created_by)
bm = create_new_sandbox['data']['links']['bm']
log_and_print(f'Business Manager link is - {bm}')
new_sandbox.append(bm)
ocapi = create_new_sandbox['data']['links']['ocapi']
log_and_print(f'OCAPI link is - {ocapi}')
new_sandbox.append(ocapi)
impex = create_new_sandbox['data']['links']['impex']
log_and_print(f'Impex link is - {impex}')
new_sandbox.append(impex)
code = create_new_sandbox['data']['links']['code']
log_and_print(f'Code Link is - {code}')
new_sandbox.append(code)
logs = create_new_sandbox['data']['links']['logs']
log_and_print(f'Logs are at - {logs}')
new_sandbox.append(logs)
log_and_print('Data extracted from response')

# Switch variable for state
state_of_new_sandbox = state
log_and_print(f'Sandbox state is {state_of_new_sandbox}')

# Request to get sandbox state in every 3 minutes. After creation each sandbox change it`s state several times. We need the state to be "started"
while 'started' not in state_of_new_sandbox:
    log_and_print('Wait another 3 minutes before checking the state of the new sandbox')
    time.sleep(180)

    check_state = requests.get(f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}",
                               headers=headers).json()

    state_of_new_sandbox = check_state['data']['state']
    log_and_print(f'Sandbox state is {state_of_new_sandbox}')

log_and_print('Sandbox preparation end')
sandbox_preparation_end = time.perf_counter()
log_and_print(
    f'Sandbox preparation was performed in {round(sandbox_preparation_end - sandbox_preparation_start, 2)} seconds.')
slack_post(f'Sandbox {sandbox_id} in realm {realm} was created, started and available at {bm}.')

# ______________________________________________________________ SANDBOX PREPARATION END _________________________________________________________________________________________________________________________________________________________________________

# ______________________________________________________________ IMPORT PHASE START _____________________________________________________________________________________________________________________________________________________________________________

slack_post('Import phase has been started')
log_and_print('Import phase start')
import_phase_start = time.perf_counter()

slack_post('Wait 2 minutes, before login to ODS')
time.sleep(120)

# Goto Sandbox
driver.get(bm)
slack_post('Sandbox is loaded')
log_and_print('Sandbox is loaded')

login_bm(bm)

goto_code_deploy()

# Press Refresh
driver.execute_script("arguments[0].click();",
                      WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,
                                                                                  '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[3]/td[1]/table/tbody/tr/td/span/button'))))
slack_post('Sandbox is refreshed')
log_and_print('Press Refresh')

logout_ods()

time.sleep(7)
log_and_print('Click Logout')

slack_post('Starting to change Compatibility mode')

# Set Compatibility mode Url and variable
log_and_print('Set Compatibility mode Url and variable')
compatibility_mode_url = f'{code}/version1/'
compatibility_mode_file = '.apiversion'

# WebDav upload of Compatibility mode file
log_and_print('Set webdav options')
options = {
    'webdav_hostname': compatibility_mode_url,
    'webdav_login': const.my_ods_email,
    'webdav_password': const.my_ods_pass,
    'webdav_timeout': 300
}
webdav = webdavClient(options)
webdav.verify = False
log_and_print('Start uploading Compatibility mode file to WebDav')
comp_mode_file_upload_start = time.perf_counter()

try:
    webdav.upload(compatibility_mode_file, compatibility_mode_file)
except Exception as e:
    print(e)
    log_and_print(f'Compatibility mode file transfer in {SCRIPT_NAME} failed')
    slack_post(f'Compatibility mode file transfer in {SCRIPT_NAME} failed')
    raise

comp_mode_file_upload_end = time.perf_counter()
log_and_print('Finished uploading Compatibility mode file to WebDav')
slack_post('Compatibility mode has been changed')
log_and_print(
    f'Compatibility mode file was uploaded for {round(comp_mode_file_upload_end - comp_mode_file_upload_start, 2)} seconds.')
log_and_print('Wait 5 seconds')
time.sleep(5)

slack_post('Restarting sandbox')

# Stop sandbox
log_and_print('Stop sandbox')

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json',
}

data = '{"operation": "stop"}'

try:
    stop_sandbox = requests.post(
        f'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/operations',
        headers=headers, data=data).json()

except Exception as e:
    print(e)
    log_and_print(f'Sandbox stop operation in {SCRIPT_NAME} failed')
    slack_post(f'Sandbox stop operation in {SCRIPT_NAME} failed')
    raise
log_and_print(f'Stop sandbox api endpoint answer is {stop_sandbox}')
log_and_print('Wait 5 seconds')
time.sleep(5)

# Start sandbox
log_and_print('Start sandbox')

data = '{"operation": "start"}'

try:
    start_sandbox = requests.post(
        f'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/operations',
        headers=headers, data=data).json()

except Exception as e:
    print(e)
    log_and_print(f'Sandbox start operation in {SCRIPT_NAME} failed')
    slack_post(f'Sandbox start operation in {SCRIPT_NAME} failed')
    raise

log_and_print(f'Start sandbox api endpoint answer is {start_sandbox}')
log_and_print('Wait 5 seconds')
time.sleep(5)

while 'started' not in start_sandbox:
    log_and_print('Wait another 4 minutes before checking the state of the new sandbox')
    time.sleep(240)

    check_state = requests.get(f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}",
                               headers=headers).json()

    start_sandbox = check_state['data']['state']
    log_and_print(f'Sandbox state is {start_sandbox}')

slack_post('Sandbox has been restarted')

driver.get(bm)
log_and_print('Sandbox is loaded')

login_bm(bm)

time.sleep(2)

goto_site_import_export()

time.sleep(2)

connect_to_remote('Staging')

time.sleep(2)

# Click Global Data archive from staging
driver.execute_script("arguments[0].click();",
                      WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                  "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(
                                                                                      staging_gd_zip)))))
log_and_print('Click Global Data archive from staging Import Radio Button')

confirm_import()

slack_post('Global data import from Staging has been initiated.')

check_export_import_status('Wait 3 minutes', 180)

log_and_print('Global Data Import is completed')
slack_post('Global Data import from Staging has been completed')

sites_import_start = time.perf_counter()

# Click Sites archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(staging_sites_zip)))))
log_and_print('Click Sites archive from staging Import Radio Button')

confirm_import()

slack_post('Sites import from Staging has been initiated.')

check_export_import_status('Wait 7 minutes', 420)

sites_import_end = time.perf_counter()
log_and_print(f'Sites import was performed in {round(sites_import_end - sites_import_start, 2)} seconds.')
slack_post(f'Sites import was performed in {round(sites_import_end - sites_import_start, 2)} seconds.')

logout_ods()

time.sleep(3)
log_and_print('Click Logout')

slack_post(
    'Starting to upload Code version via Webdav from local host to sandbox.')

# WebDav upload of Code Version
options = {
    'webdav_hostname': code,
    'webdav_login': const.my_ods_email,
    'webdav_password': const.my_ods_pass,
    'webdav_timeout': 300
}
webdav = webdavClient(options)
webdav.verify = False
log_and_print('Start uploading code Version to WebDav')
webdav_upload_start = time.perf_counter()

try:
    webdav.upload_directory(codeVersion, codeVersion)
except Exception as e:
    print(e)
    slack_post(f'Webdav transfer in {SCRIPT_NAME} failed')
    log_and_print(f'Webdav transfer in {SCRIPT_NAME} failed')
    raise

webdav_upload_end = time.perf_counter()
log_and_print(f'Code version was uploaded for {round(webdav_upload_end - webdav_upload_start, 2)} seconds.')
slack_post(f'Code version was uploaded for {round(webdav_upload_end - webdav_upload_start, 2)} seconds.')
shutil.rmtree(f'./{codeVersion}')
log_and_print('Remove folder with code version')

# Goto Sandbox
driver.get(bm)
log_and_print('Sandbox is loaded')

login_bm(bm)

time.sleep(2)

goto_code_deploy()

# Press Activate
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                           '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form[1]/table/tbody/tr[2]/td[7]/a[2]/span'))))
log_and_print('Press Activate')

# Accept Activation
# noinspection PyDeprecation
driver.switch_to_alert().accept()
log_and_print('Switch to Alert')
log_and_print('Wait s seconds')
time.sleep(3)

log_and_print('Press Enter')
slack_post('Code version was activated')

goto_site_import_export()

time.sleep(2)

connect_to_remote('Staging')

time.sleep(2)

# Click Catalog archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(staging_catalog_zip)))))
log_and_print('Click Catalog archive from staging Import Radio Button')

confirm_import()

import_catalog_start = time.perf_counter()

slack_post('Catalog archive import from staging has been initiated')

check_export_import_status('Wait 10 minutes', 600)

import_catalog_end = time.perf_counter()
log_and_print(f'Catalogs Import has been completed in {round(import_catalog_end - import_catalog_start, 2)} seconds.')
slack_post(f'Catalogs Import has been completed in {round(import_catalog_end - import_catalog_start, 2)} seconds.')

# Click Price Books archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(staging_pb_zip)))))
log_and_print('Click Price Books archive from staging Import Radio Button')

confirm_import()

slack_post('Price books import from Staging has been initiated.')

check_export_import_status('Wait 3 minutes', 180)

log_and_print('Price Books Import is completed.')
slack_post('Price books import is completed.')

# Click Inventory lists archive from staging
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(staging_il_zip)))))
log_and_print('Click Inventory lists archive from staging Import Radio Button')

confirm_import()

slack_post('Inventory lists import from Staging has been initiated.')

check_export_import_status('Wait 1 minute', 60)

log_and_print('Inventory lists Import is completed')
slack_post('Inventory lists Import is completed')

# remove_banner()

# Find Hostname, clear field and insert Dev Hostname
driver.find_element(By.XPATH, '//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[1]/td[2]/input').clear()
driver.find_element(By.XPATH,
                    '//*[@id="remoteSiteImpex"]/table[1]/tbody/tr/td/table/tbody/tr[1]/td[2]/input').send_keys(
    DEV_HOST_NAME)
driver.find_element(By.XPATH, '//*[@id="fetchremotedir"]').click()

# Find archive from Development
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, "//*[@id='remoteSiteImpex']/table[2]/tbody/tr/td[1]/input[@value='{}']".format(dev_zip)))))
log_and_print('Find and click Development Import Radio Button')

confirm_import()

slack_post('Sites import from Development has been initiated.')

check_export_import_status('Wait 3 minutes', 180)

log_and_print('Dev archive Import is completed')
slack_post('Dev archive Import is completed')

log_and_print('Import phase end')
import_phase_end = time.perf_counter()
log_and_print(f'Import phase was performed in {round(import_phase_end - import_phase_start, 2)} seconds.')
slack_post(f'Import phase was performed in {round(import_phase_end - import_phase_start, 2)} seconds.')

# ______________________________________________________________ IMPORT PHASE END _____________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ REBUILD INDEXES START ________________________________________________________________________________________________________________________________________________________________________

slack_post('Rebuild indexes start')

log_and_print('Rebuild Indexes start')
rebuild_index_start = time.perf_counter()

# remove_banner()

select_site()

# Click Site 1
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[3]/td/a'))))
time.sleep(2)
log_and_print('Click Site 1')

rebuild_index('Site 1')

select_site()

# Click Site 2
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/a'))))
time.sleep(2)
log_and_print('Click Site 2')

rebuild_index('Site 2')

select_site()

# Click Site 3
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[5]/td/a'))))
time.sleep(2)
log_and_print('Click Site 3')

rebuild_index('Site 3')

select_site()

# Click Site 4
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[6]/td/a'))))
time.sleep(2)
log_and_print('Click Site 4')

rebuild_index('Site 4')

select_site()

# Click Site 5
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[7]/td/a'))))
time.sleep(2)
log_and_print('Click Site 5')

rebuild_index('Site 5')

select_site()

# Click Site 6
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[8]/td/a'))))
time.sleep(2)
log_and_print('Click Site 6')

rebuild_index('Site 6')

select_site()

# Click Site 7
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[9]/td/a'))))
time.sleep(2)
log_and_print('Click Site 7')

rebuild_index('Site 7')

select_site()

# Click Site 8
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[10]/td/a'))))
time.sleep(2)
log_and_print('Click Site 8')

rebuild_index('Site 8')

select_site()

# Click Site 9
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[11]/td/a'))))
time.sleep(2)
log_and_print('Click Site 9')

rebuild_index('Site 9')

select_site()

# Click Site 10
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[12]/td/a'))))
time.sleep(2)
log_and_print('Click Site 10')

rebuild_index('Site 10')

select_site()

# Click Site 11
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[13]/td/a'))))
time.sleep(2)
log_and_print('Click Site 11')

rebuild_index('Site 11')

# Click Site 12
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[14]/td/a'))))
time.sleep(2)
log_and_print('Click Site 12')

rebuild_index('Site 12')

log_and_print('Rebuild Index end')
rebuild_index_end = time.perf_counter()
log_and_print(f'Rebuild Index phase was performed in {round(rebuild_index_end - rebuild_index_start, 2)} seconds.')
slack_post(f'Rebuild Index phase was performed in {round(rebuild_index_end - rebuild_index_start, 2)} seconds.')

# ______________________________________________________________ REBUILD INDEXES END __________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ CLEAR CACHE START ____________________________________________________________________________________________________________________________________________________________________________

slack_post('Clear cache start')

log_and_print('Clear Cache start')
clear_cache_start = time.perf_counter()

# Click "Administration"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div[1]/ccbm/div[2]/header/div[2]/nav/ul/li[2]/div/a'))))
log_and_print('Click Administration')

# Click "Sites"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="menuoverview"]/div/div[1]/div[3]/article/div/header/div[2]/a'))))
log_and_print('Click Sites')

# Click "Manage Sites"
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="menuoverview"]/div/div[1]/div[1]/article/div/header/div[2]/a'))))
time.sleep(2)
log_and_print('Click Manage Sites')

# Click Site 1
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[2]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 1')

clear_cache()

manage_sites()

# Click Site 2
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[3]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 2')

clear_cache()

manage_sites()

# Click Site 3
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[4]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 3')

clear_cache()

manage_sites()

# Click Site 4
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[5]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 4')

clear_cache()

manage_sites()

# Click Site 5
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[6]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 5')

clear_cache()

manage_sites()

# Click Site 6
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[7]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 6')

clear_cache()

manage_sites()

# Click Site 7
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[8]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 7')

clear_cache()

manage_sites()

# Click Site 8
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[9]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 8')

clear_cache()

manage_sites()

# Click Site 9
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[10]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 9')

clear_cache()

manage_sites()

# Click Site 10
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[11]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 10')

clear_cache()

manage_sites()

# Click Site 11
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[12]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 11')

clear_cache()

# Click Site 12
driver.execute_script("arguments[0].click();", WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH,
                                '//*[@id="bm_content_column"]/table/tbody/tr/td/table/tbody/tr/td[2]/form/table/tbody/tr/td/table[2]/tbody/tr[13]/td[2]/a'))))
time.sleep(2)
log_and_print('Click Site 12')

clear_cache()

log_and_print('Clear Cache end')
clear_cache_end = time.perf_counter()
log_and_print(f'Clear cache phase was performed in {round(clear_cache_end - clear_cache_start, 2)} seconds.')
slack_post(f'Clear cache phase was performed in {round(clear_cache_end - clear_cache_start, 2)} seconds.')

# ______________________________________________________________ CLEAR CACHE END ______________________________________________________________________________________________________________________________________________________________________________


# ______________________________________________________________ CLOSE BROWSER AND SEND EMAIL ______________________________________________________________________________________________________________________________________________________________________________

driver.close()
driver.quit()
slack_post('Browser closed and driver quit')
log_and_print('Browser closed and driver quit')

# Ending point of the time counter
script_finish_time = time.perf_counter()
log_and_print(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')
slack_post(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')

# Copy logfile to folder with script data
shutil.copy(SCRIPT_LOG_FILE, 'DataFolder')

# Create zip file of the directory with all script data and delete directory
log_and_print('Create zip file of the directory with all screenshots and delete directory')
shutil.make_archive('ZwillingDemandwareReleaseVerify', 'zip', 'DataFolder')
shutil.rmtree('./DataFolder')

# Send email with attached zip containing screenshots
log_and_print('Send email with attached zip containing screenshots')
email_recipient = const.my_business_email
email_subject = 'Demandware Release verification on Zwilling'
email_text = f'Hi Team, this is to inform you that on demand sandbox preparation for Demandware Release verification on Zwilling has been completed. You can performed validation on site following the standard procedure at {bm}.'
email_attachment = str(Path.cwd() / 'ZwillingDemandwareReleaseVerify.zip')
send_email(email_recipient, email_subject, email_text, email_attachment)

# Delete archive with screenshots
os.remove('ZwillingDemandwareReleaseVerify.zip')
slack_post(f'Email has been sent to {email_recipient}')
slack_post('THE END')
