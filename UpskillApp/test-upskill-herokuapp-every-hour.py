import os
import logging
import requests
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from slack_messaging import slack_post
from browser_setup import my_browser


# Set script name
script_name = 'test-upskill-herokuapp-every-hour'

# Set url to test
url_to_test = 'https://upskill-ods.herokuapp.com/'

# Starting point of the time counter
script_start_time = time.perf_counter()

# # Get date for today and set it in format ISO 8601
today_is = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

# Create and configure logger
log_format = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{today_is}.log'
logging.basicConfig(filename=f'{script_name}_{today_is}.log',
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()


def log_and_print(text):
    print(text)
    logger.debug(text)


log_and_print('Set credentials')
slack_token = os.getenv('SLACK_BOT')
herokuapp_username = os.getenv('UPSKILL_BOT_USERNAME')
herokuapp_password = os.getenv('UPSKILL_BOT_PASSWORD')

log_and_print('Set browser')
driver = my_browser()
driver.implicitly_wait(30)

log_and_print(f'Goto {url_to_test}')
try:
    driver.get(url_to_test)
except Exception as e:
    log_and_print(e)
    heroku_response = requests.get(url_to_test)
    status_code = heroku_response.status_code
    if status_code != 200:
        slack_post(f'Test bot in {script_name} was unable to load {url_to_test}.'
                   f'\nAnother test was made and status code was {status_code}')
    else:
        log_and_print(f'Test bot in {script_name} was unable to load {url_to_test}.'
                      f'\nAnother test was made and status code was {status_code}')
    raise

log_and_print(f'{url_to_test} is loaded')

try:
    driver.find_element(By.ID, 'username_login').send_keys(herokuapp_username)
    driver.find_element(By.ID, 'pwd_login').send_keys(herokuapp_password)
    driver.find_element(By.NAME, 'login').click()
except Exception as exc:
    log_and_print(exc)
    slack_post(
        f'Test bot could not Log IN {url_to_test} while running {script_name}')

try:
    driver.find_element(By.XPATH, '//*[contains(text(),"Log out")]/parent::a').click()
    driver.find_element(By.XPATH, '//a[contains(text(),"Log out")]').click()
except Exception as e:
    log_and_print(e)
    slack_post(
        f'Test bot could not Log OUT {url_to_test} while running {script_name}')

log_and_print(f'Login and log out {url_to_test} success')

driver.quit()
log_and_print('Tear down browser')

# Ending point of the time counter
script_finish_time = time.perf_counter()
log_and_print(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')
