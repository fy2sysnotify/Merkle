import requests
import json
import urllib3


def get_access_token(client_id: str, client_secret: str) -> str:
    """
    Retrieves an access token using the specified client ID and client secret.

    Args:
        client_id (str): The client ID to use when getting the access token.
        client_secret (str): The client secret to use when getting the access token.

    Returns:
        The access token as a string.

    Raises:
        JSONDecodeError: If the access token response from the server cannot be decoded as JSON.
        requests.exceptions.RequestException: If an error occurs while sending the request.
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
