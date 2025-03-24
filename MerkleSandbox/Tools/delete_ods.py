# Remember... The Force will be with you. Always.

import json
import requests
import urllib3
import logging
import url_links
import constants as const

script_name = 'delete-ods'

log_format = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{const.today_is}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

urllib3.disable_warnings()


def log_and_print(text):
    print(text)
    logger.info(text)


sandbox_list = ['Your sandbox list here']

data = {
    'grant_type': 'password',
    'username': const.username,
    'password': const.password
}

access_token_response = requests.post(url_links.ACCESS_TOKEN_AUTH_URL, data=data,
                                      verify=False,
                                      allow_redirects=False, auth=(const.client_id, const.client_secret))

try:
    access_token = json.loads(access_token_response.text)
except ValueError as value_error:
    log_and_print(value_error)
    raise

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ' + access_token['access_token']
}

for sandbox in sandbox_list:
    try:
        delete_sandbox = requests.delete(f'{url_links.SANDBOX_URL}/{sandbox}',
                                         headers=headers, verify=False).json()
        log_and_print(delete_sandbox)

    except Exception as exc:
        log_and_print(f'Failed to delete {sandbox}')
        log_and_print(exc)
        raise
