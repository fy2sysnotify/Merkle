# When gone am I, the last of the Jedi will you be. The Force runs strong in your family. Pass on what you have learned

import pyotp
import os.path
from selenium import webdriver
import time
import logging
from datetime import datetime
from datetime import timedelta
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Set script name
scriptName = 'get-totp-headless-browsing'

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


def log_and_print(text):
    print(text)
    logger.debug(text)


# Get credentials from global variables. Keep in mind that getting them on Linux has slightly different syntax
client_id = os.getenv('CREATE_ODS_CLIENT_ID')
username = os.getenv('CREATE_ODS_USERNAME')
password = os.getenv('CREATE_ODS_PASSWORD')
log_and_print('We got credentials')


# Requesting access token with password credentials
log_and_print('Requesting access token with password credentials')
data = {'grant_type': 'password', 'username': username, 'password': password}

# Set authentication URL to hit, set browser and get the URL opened in browser
log_and_print('Set authentication URL to hit, set browser and get the URL opened in browser')
auth_url = 'https://account.demandware.com/dwsso/XUI/?realm=%2F&goto=https%3A%2F%2Faccount.demandware.com%3A443%2Fdwsso%2Foauth2%2Fauthorize%3Fresponse_type%3Dtoken%26state%3D%26client_id%3Db4836c9b-d346-43b8-8800-edbf811035c2%26scope%3D%26redirect_uri%3Dhttps%253A%252F%252Fadmin.us01.dx.commercecloud.salesforce.com%252Foauth2-redirect.html#login/'
options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome('chromedriver', service_args=["--verbose", "--log-path=chromedriver.log"], options=options)
driver.implicitly_wait(30)
driver.get(auth_url)

# At the authentication URL we are searching for the id value of 'username' textbox and we are passing username value extracted from global variable
log_and_print('At the authentication URL we are searching for the id value of username textbox and we are passing username value extracted from global variable')
driver.find_element_by_id('idToken1').send_keys(username)

# At the authentication URL we are searching for the id value of 'login' button and we are clicking it
log_and_print('At the authentication URL we are searching for the id value of login button and we are clicking it')
driver.execute_script("arguments[0].click();",
                          WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'loginButton_0'))))

# At the authentication URL we are searching for the id value of 'password' textbox and we are passing password value extracted from global variable
log_and_print('At the authentication URL we are searching for the id value of password textbox and we are passing password value extracted from global variable')
driver.find_element_by_id('idToken2').send_keys(password)

# At the authentication URL we are searching for the id value of 'login' button and we are clicking it
log_and_print('At the authentication URL we are searching for the id value of login button and we are clicking it')
driver.execute_script("arguments[0].click();",
                      WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'loginButton_0'))))

# This will return the OTP Code
log_and_print('Getting OTP')
otpQR = os.getenv('ODS_REPORT_TOTP')
getOtp = pyotp.TOTP(otpQR)
otp = getOtp.now()
log_and_print(otp)

# Add OTP code and press enter
driver.find_element_by_xpath('//*[@id="input-9"]').send_keys(otp)
driver.execute_script("arguments[0].click();",
                      WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/vaasdist-verify/div/vaas-verify/div/vaas-verify-totp/vaas-container/div/div/slot/div/form/div/vaas-button-brand/button'))))
log_and_print('Type otp code and press enter')
time.sleep(15)

# After waiting time of 15 seconds we have landed on the final url and we are extracting the whole of it as a string
log_and_print('Get access token url as string')
accessTokenUrl = driver.current_url
log_and_print(accessTokenUrl)
driver.quit()

# We are manipulating url string to extract access token by getting the indexes of start and end point
# we are interested in. Then we are removing first 13 symbols and we have the access token.
stringStart = accessTokenUrl.find('access_token=')
stringEnd = accessTokenUrl.find('&scope')
log_and_print(stringStart)
log_and_print(stringEnd)
stringToCut = accessTokenUrl[stringStart:stringEnd]
finalString = stringToCut[13:stringEnd]
log_and_print(finalString)