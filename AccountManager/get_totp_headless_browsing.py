import time
import pyotp
import constants as const
from selenium.webdriver.common.by import By
from browser_setup import setup_chrome_browser


def get_otp_code() -> str:
    """
    Returns the One Time Password (OTP) code.

    :return: The OTP code as a string
    """
    get_otp = pyotp.TOTP(const.sfcc_am_qr)

    return get_otp.now()


def get_token_url() -> str:
    """
    With headless browsing returns the URL for the access token.

    :return: The URL for the access token.
    """
    driver = setup_chrome_browser()
    driver.implicitly_wait(30)
    driver.get(const.totp_auth_url)

    driver.find_element(
        By.ID, "idToken2").send_keys(const.sfcc_am_user)
    time.sleep(1)
    driver.find_element(
        By.ID, "loginButton_0").click()
    time.sleep(1)
    driver.find_element(
        By.ID, "idToken2").send_keys(const.sfcc_am_pass)
    time.sleep(1)
    driver.find_element(
        By.ID, "loginButton_0").click()
    time.sleep(1)

    driver.find_element(
        By.XPATH, '//*[@id="input-9"]').send_keys(get_otp_code())
    time.sleep(3)
    driver.find_element(
        By.XPATH, '//button[@type="submit"]').click()

    time.sleep(5)

    access_token_url = driver.current_url
    driver.quit()

    return access_token_url


def get_access_token(input_string: str = get_token_url()) -> str:
    """
    Returns the access token extracted from the input URL.

    :param: input_string (str): The URL from which to extract the access token.
    :return: The access token.
    """
    string_start = input_string.find("access_token=")
    string_end = input_string.find("&scope")
    string_to_cut = input_string[string_start:string_end]

    return string_to_cut[13:string_end]


def main() -> None:
    """
    This is the main function of the script.It retrieves
    the access token and prints it to the console.

    :return: None
    """
    access_token = get_access_token()
    print(access_token)


if __name__ == '__main__':
    main()
