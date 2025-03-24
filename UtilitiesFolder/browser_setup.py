from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager


def setup_chrome_browser() -> WebDriver:
    """
    Set up a Chrome browser instance.

    :return: A `WebDriver` instance for controlling the Chrome browser.
    """
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/83.0.4103.61 Safari/537.36"
    )

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_experimental_option("prefs", {
        "dom.webnotifications.serviceworker.enabled": False,
        "dom.webnotifications.enabled": False,
    })
    options.add_argument("--headless")

    return webdriver.Chrome(
        executable_path=ChromeDriverManager().install(), options=options
    )
