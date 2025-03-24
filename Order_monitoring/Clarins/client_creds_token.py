import requests
import json
import urllib3


def get_access_token(client_id: str, client_secret: str) -> str:
    """
    Get the access token for the given client ID and client secret.

    :param client_id: The client ID to use when getting the access token.
    :param client_secret: The client secret to use when getting the access token.
    :return: The access token.
    """
    data = {
        'grant_type': 'client_credentials'
    }

    urllib3.disable_warnings()

    access_token_response = requests.post(
        'https://account.demandware.com:443/dwsso/oauth2/access_token',
        data=data,
        verify=False,
        allow_redirects=False,
        auth=(client_id, client_secret))

    access_token = json.loads(access_token_response.text)

    return access_token['access_token']
