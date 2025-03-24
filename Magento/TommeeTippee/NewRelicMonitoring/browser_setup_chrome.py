from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional


def my_browser(download_directory: Optional[str] = None) -> webdriver.Chrome:
    """
    Create a customized headless Chrome webdriver.

    :param download_directory: Optional. The directory where downloads should be saved.
    :type download_directory: str or None
    :return: Configured Chrome webdriver instance.
    :rtype: selenium.webdriver.Chrome
    """
    # Define a custom user agent
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/83.0.4103.61 Safari/537.36"
    )

    # Configure Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    prefs = {'download.default_directory': download_directory}
    options.add_experimental_option('prefs', prefs)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')

    # Create and return the Chrome webdriver
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
