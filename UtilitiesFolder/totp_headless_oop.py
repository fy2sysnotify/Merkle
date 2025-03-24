import os
import time
import pyotp
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import constants as const


class ChromeBrowser:
    def __init__(self) -> None:
        """
        Initializes the Chrome browser and sets necessary options.
        """
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/83.0.4103.61 Safari/537.36"
        )
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(f"user-agent={self.user_agent}")
        self.options.add_experimental_option("prefs", {
            "dom.webnotifications.serviceworker.enabled": False,
            "dom.webnotifications.enabled": False,
        })
        self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), options=self.options
        )
        self.driver.implicitly_wait(30)

    def __del__(self) -> None:
        """
        Closes the browser.

        :return: None
        """
        self.driver.quit()


class OTP:
    def __init__(self, secret) -> None:
        """
        Initializes the OTP class with the given secret.

        :param: secret(str): OTP secret.
        """
        self.secret = secret
        self.get_otp = pyotp.TOTP(secret)

    def get_otp_code(self) -> str:
        """
        Generates the OTP code for the current time.

        :return (str): OTP code
        """

        return self.get_otp.now()


class Login:
    def __init__(self, browser: ChromeBrowser, sfcc_email: str, sfcc_password: str, totp_auth_url: str) -> None:
        """
        Initializes the Login class with the given browser, email, password, and totp auth url.

        :param: browser(Chrome browser): Chrome browser.
        :param: sfcc_email (str): Email to log in with.
        :param: sfcc_password (str): Password to log in with.
        :param: totp_auth_url (str): TOTP auth url.
        """
        self.browser = browser
        self.totp_auth_url = totp_auth_url
        self.browser.driver.get(self.totp_auth_url)
        self.email = sfcc_email
        self.password = sfcc_password

    def login(self, otp: OTP) -> None:
        """
        Logs in using the given OTP, email and password.

        :param: otp(OTP): OTP instance
        :return: None
        """
        self.browser.driver.find_element(By.ID, "idToken1").send_keys(self.email)
        self.browser.driver.find_element(By.ID, "loginButton_0").click()
        self.browser.driver.find_element(By.ID, "idToken2").send_keys(self.password)
        self.browser.driver.find_element(By.ID, "loginButton_0").click()
        self.browser.driver.find_element(By.XPATH, '//*[@id="input-9"]').send_keys(otp.get_otp_code())
        self.browser.driver.find_element(By.XPATH, '//button[@type="submit"]').click()

    def get_access_token_url(self) -> str:
        """
        Get current url after login and waiting for 5 seconds. Waiting time is mandatory.

        :return (str): The current url
        """
        time.sleep(5)
        return self.browser.driver.current_url


class AccessToken:
    def __init__(self, input_string: str) -> None:
        """
        Initializes the AccessToken class with the given input string.

        :param: input_string (str): URL containing access token.
        :return: None
        """
        self.input_string = input_string

    def get_access_token(self) -> str:
        """
        Extracts the access token from the input string.

        :return (str): Access token.
        """
        string_start = self.input_string.find("access_token=")
        string_end = self.input_string.find("&scope")
        string_to_cut = self.input_string[string_start:string_end]
        return string_to_cut[13:string_end]


def main() -> None:
    """
    Main function that performs the following steps:
    1. Initializes a Chrome browser.
    2. Initializes an OTP instance with the given secret.
    3. Initializes a Login instance with the given browser, email, password, and totp auth url.
    4. Logs in using the given OTP, email and password.
    5. Extracts the access token from the access token URL.
    6. Prints the access token.

    :return: None
    """
    browser = ChromeBrowser()
    otp = OTP(os.getenv('ODS_REPORT_TOTP'))
    login = Login(
        browser, os.getenv('BUSINESS_EMAIL'),
        os.getenv('CREATE_ODS_PASSWORD'),
        const.totp_auth_url
    )
    login.login(otp)
    access_token_url = login.get_access_token_url()
    access_token = AccessToken(access_token_url).get_access_token()
    print(access_token)


if __name__ == "__main__":
    main()
