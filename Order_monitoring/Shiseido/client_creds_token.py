import requests
import json
import urllib3


def get_access_token(client_id: str = None, client_secret: str = None, access_token_endpoint: str = None) -> str:
    """
    Get the access token for the given client ID and client secret.

    :param: client_id (str): The client ID to use when getting the access token.
    :param: client_secret (str): The client secret to use when getting the access token.
    :param: access_token_endpoint (str): The endpoint URL used to obtain the access token.
    :return (str): The access token.
    """
    data = {
        'grant_type': 'client_credentials'
    }

    urllib3.disable_warnings()

    access_token_response = requests.post(
        access_token_endpoint,
        data=data,
        verify=False,
        allow_redirects=False,
        auth=(client_id, client_secret))

    access_token = json.loads(access_token_response.text)

    return access_token['access_token']
