import requests
import json
import urllib3
import pyotp
import os
from typing import Optional

SFCC_OAUTH_URL = 'https://account.demandware.com/dwsso/oauth2/access_token?grant_type=client_credentials'


def generate_totp_code() -> str:
    """
    Generate a Time-based One-Time Password (TOTP).

    Returns:
        str: The TOTP code as a string.
    """
    totp = pyotp.TOTP(os.getenv('sfcc_am_totp'))
    return totp.now()


def get_access_token() -> Optional[str]:
    """
    Get an access token using the provided username, password, and OAuth 2.0 client credentials.

    Returns:
        Optional[str]: The access token as a string, or None if an error occurs.
    """
    try:
        # Get configuration variables
        username: str = os.getenv('sfcc_am_user')
        password: str = f'{os.getenv("sfcc_am_pass")}{generate_totp_code()}'

        data = {
            'grant_type': 'password',
            'username': username,
            'password': password,
        }

        # Disable SSL/TLS warnings
        urllib3.disable_warnings()

        client_id: str = os.getenv('SFCC_OAUTH_CLIENT_ID')
        client_secret: str = os.getenv('SFCC_OAUTH_CLIENT_SECRET')

        response = requests.post(
            SFCC_OAUTH_URL,
            data=data,
            verify=False,
            allow_redirects=False,
            auth=(client_id, client_secret)
        )

        # Raise an exception for bad status codes
        response.raise_for_status()

        access_token_response: dict = json.loads(response.text)
        access_token: str = access_token_response.get('access_token')
        return access_token

    except Exception as e:
        # Handle exceptions or log errors as needed
        print(f"An error occurred: {str(e)}")
        return None


def main() -> None:
    new_access_token = get_access_token()
    if new_access_token:
        print(f"Access Token: {new_access_token}")


if __name__ == "__main__":
    main()
