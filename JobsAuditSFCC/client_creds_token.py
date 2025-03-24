import requests
import json
import urllib3
from decouple import config


def get_access_token() -> str:
    """
    Retrieve an access token using the client credentials grant type.

    This function sends a POST request to an OAuth2 authorization server to obtain
    an access token using the client credentials grant type.

    :return: The access token obtained from the authorization server.
    :rtype: str

    :raises requests.exceptions.RequestException: An error occurred during the HTTP request.
    :raises ValueError: The response from the authorization server does not contain an access token.

    This function retrieves an access token by sending a POST request to the authorization server
    using client credentials (client ID and client secret). The retrieved access token is returned.
    """

    client_id = config('CLIENT_ID', default='')
    client_secret = config('CLIENT_SECRET', default='')
    access_token_url = config('ACCESS_TOKEN_URL', default='')

    data = {
        'grant_type': 'client_credentials'
    }

    urllib3.disable_warnings()

    access_token_response = requests.post(
        access_token_url,
        data=data,
        verify=False,
        allow_redirects=False,
        auth=(client_id, client_secret)
    )

    access_token_data = json.loads(access_token_response.text)

    if 'access_token' in access_token_data:
        return access_token_data['access_token']
    else:
        raise ValueError("Access token not found in the response.")
