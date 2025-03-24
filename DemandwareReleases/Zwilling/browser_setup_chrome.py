from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def my_browser(download_directory=None):
    options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': download_directory}
    options.add_experimental_option('prefs', prefs)
    options.add_argument('--no-sandbox')
    options.add_argument('----disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.headless = True
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                            options=options)
