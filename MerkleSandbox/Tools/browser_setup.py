from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def my_browser(default_download_folder=None):
    prefs = {'download.default_directory': default_download_folder,
             'directory_upgrade': True}
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.headless = True
    options.add_experimental_option('prefs', prefs)
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                            options=options)
