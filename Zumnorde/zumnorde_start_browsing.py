import time
import logging
import requests
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from slack_messaging import slack_post
from browser_setup import my_browser

script_name = 'zumnorde_start_browsing'
url_to_test = 'https://www.zumnorde.de'
script_start_time = time.perf_counter()

log_format = '%(levelname)s %(asctime)s - %(message)s'
SCRIPT_LOG_FILE = f'{script_name}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
logging.basicConfig(filename=SCRIPT_LOG_FILE,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()


def log_and_print(text):
    print(text)
    logger.debug(text)


log_and_print('Set browser')
driver = my_browser()
driver.implicitly_wait(30)

log_and_print(f'Goto {url_to_test}')
try:
    driver.get(url_to_test)
except Exception as exc:
    print(exc)
    zumnorde_response = requests.get(url_to_test)
    status_code = zumnorde_response.status_code
    if status_code != 200:
        slack_post(f'Test bot in {script_name} was unable to load {url_to_test}.'
                   f'\nAnother test was made and status code was {status_code}')
    else:
        log_and_print(f'Test bot in {script_name} was unable to load {url_to_test}.'
                   f'\nAnother test was made and status code was {status_code}')
    raise

log_and_print(f'{url_to_test} is loaded')

try:
    driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver,
                                        30).until(EC.element_to_be_clickable((By.XPATH,
                                                                              '//button[@aria-label="Alle akzeptieren"]'))))
except Exception as exc:
    print(exc)
    slack_post(f'{script_name} was unable to find and press "Alle akzeptieren" at https://www.zumnorde.de/')
    raise

log_and_print(f'Goto {url_to_test} success')

driver.quit()
log_and_print('Tear down browser')

script_finish_time = time.perf_counter()
log_and_print(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')
