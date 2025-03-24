import os
import logging
import datetime
import requests
from slack_messaging import slack_post
from client_creds_token import get_access_token

SCRIPT_NAME = 'failed_order_count_zwilling'
sites = ['zwilling-us', 'zwilling-ca', 'zwilling-global', 'zwilling-tr', 'zwilling-de', 'zwilling-fr', 'zwilling-it', 'zwilling-br', 'zwilling-be', 'zwilling-dk', 'zwilling-uk', 'zwilling-es', 'zwilling-jp']
DT = (datetime.datetime.now() - datetime.timedelta(minutes=195)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

log_format = '%(levelname)s %(asctime)s - %(message)s'
SCRIPT_LOG_FILE = f'{SCRIPT_NAME}_{datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename=SCRIPT_LOG_FILE,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {get_access_token(os.getenv("ZWILLING_CLIENT_ID"), os.getenv("ZWILLING_CLIENT_PASS"))}',
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
                'term_query': {
                    'fields': ['status'],
                    'operator': 'is',
                    'values': ['failed'],
                },
            },
        },
    },
    'select': '(hits.(data.(creation_date, status, total)))',
}


def log_and_print(text):
    print(text)
    logger.info(text)


def get_order_count():

    response = requests.post(
        f'https://www.zwilling.com/s/{site_id}/dw/shop/v22_10/order_search',
        headers=headers, json=json_data)

    order_count = response.json()

    return order_count


for site_id in sites:
    try:
        log_and_print(f'{site_id} = {get_order_count()}\nNumber of failed orders in {site_id} = {str(get_order_count()).count("failed")}')
    except Exception as e:
        log_and_print(e)
        slack_post(f'Failed to get order count for *{site_id}* in script "*{SCRIPT_NAME}*"')

