import json
import urllib3
import url_links
import requests
import constants as const


def access_token():
    urllib3.disable_warnings()

    data = {
        'grant_type': 'password',
        'username': const.my_business_email,
        'password': const.password
    }

    sfcc_response = requests.post(url_links.ACCESS_TOKEN_AUTH_URL, data=data,
                                  verify=False,
                                  allow_redirects=False, auth=(const.client_id, const.client_secret))

    response_dictionary = json.loads(sfcc_response.text)

    return response_dictionary['access_token']


print(access_token())
