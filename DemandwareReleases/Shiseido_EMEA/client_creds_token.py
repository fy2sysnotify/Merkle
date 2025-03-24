import requests
import json
import urllib3
import constants as const


def get_access_token():
    data = {
        'grant_type': 'client_credentials'
    }

    urllib3.disable_warnings()

    access_token_response = requests.post(
        const.access_token_auth_url,
        data=data, verify=False, allow_redirects=False,
        auth=(const.client_id_ods, const.client_secret_ods)
    )

    access_token = json.loads(access_token_response.text)

    return access_token['access_token']
