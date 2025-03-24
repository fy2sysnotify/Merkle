import time
import pyotp
import constants as const
from selenium.webdriver.common.by import By
from browser_setup_chrome import my_browser


def get_otp_code() -> str:
    """
    Returns the One Time Password (OTP) code.

    :return: The OTP code as a string
    """
    get_otp = pyotp.TOTP(const.otp_qr)

    return get_otp.now()


def get_token_url() -> str:
    """
    Facilitating Selenium library headless returns the URL for the access token.

    :return: The URL for the access token.
    """
    driver = my_browser()
    driver.implicitly_wait(30)
    driver.get(const.totp_auth_url)

    driver.find_element(
        By.ID, "idToken1").send_keys(const.my_ods_email)
    driver.find_element(
        By.ID, "loginButton_0").click()
    driver.find_element(
        By.ID, "idToken2").send_keys(const.my_ods_pass)
    driver.find_element(
        By.ID, "loginButton_0").click()

    driver.find_element(
        By.XPATH, '//*[@id="input-9"]').send_keys(get_otp_code())
    driver.find_element(
        By.XPATH, '//button[@type="submit"]').click()

    time.sleep(5)

    access_token_url = driver.current_url
    driver.quit()

    return access_token_url


def get_access_token(input_string: str = get_token_url()) -> str:
    """
    Returns the access token extracted from the input URL.

    :param: input_string: The URL from which to extract the access token.
    :return: The access token.
    """
    string_start = input_string.find("access_token=")
    string_end = input_string.find("&scope")
    string_to_cut = input_string[string_start:string_end]

    return string_to_cut[13:string_end]
