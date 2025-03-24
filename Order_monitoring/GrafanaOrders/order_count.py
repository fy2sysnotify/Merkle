import os
import logging
import datetime
import requests
from slack_messaging import slack_post
from client_creds_token import get_access_token

SCRIPT_NAME = 'order_count'
sites = ['ASDA', 'ASDA-INT']
DT = (datetime.datetime.now() - datetime.timedelta(minutes=125)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

log_format = '%(levelname)s %(asctime)s - %(message)s'
SCRIPT_LOG_FILE = f'{SCRIPT_NAME}_{datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename=SCRIPT_LOG_FILE,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {get_access_token(os.getenv("ASDA_CLIENT_ID"), os.getenv("ASDA_CLIENT_PASS"))}',
}

json_data = {
    'query': {
        'filtered_query': {
            'filter': {
                'range_filter': {
                    'field': 'creation_date',
                    'from': DT,
                },
            },
            'query': {
                'match_all_query': {},
            },
        },
    },
    'select': '(total)',
}


def log_and_print(text):
    print(text)
    logger.info(text)


def get_order_count():
    response = requests.post(
        f'https://george.com/s/{site_id}/dw/shop/v19_5/order_search',
        headers=headers, json=json_data)

    order_count = response.json()
    print(order_count)

    return order_count['total']


for site_id in sites:
    try:
        log_and_print(f'{site_id} = {get_order_count()}')
    except Exception as e:
        log_and_print(e)
