import os
import time
from datetime import datetime
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.common.by import By

url = 'https://www.atlassian.com/trust/security/advisories'

options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome('c:/Selenium/chromedriver', options=options)
driver.maximize_window()
driver.implicitly_wait(10)

driver.get(url)

try:
    driver.find_element(By.XPATH, '//*[@id="onetrust-close-btn-container"]/button').click()
except Exception as exc:
    print(exc)

time.sleep(5)

S = lambda X: driver.execute_script(f'return document.body.parentNode.scroll{X}')
driver.set_window_size(S('Width'), S('Height'))
driver.find_element(By.TAG_NAME, 'body').screenshot('new.png')

driver.quit()

original_screenshot = Image.open('original.png')
new_screenshot = Image.open('new.png')

screenshots_difference = ImageChops.difference(original_screenshot, new_screenshot).convert('RGB')

if screenshots_difference.getbbox():
    print('there is difference')
    screenshots_difference.show()
    screenshots_difference.save(f'difference_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png')
else:
    print('same pictures')

os.remove('original.png')
os.rename('new.png', 'original.png')
