# 'The Dark side of the Force is a pathway to many abilities some consider to be unnatural.'

import requests
import json
import time
import logging
import urllib3
import url_links
import xlsxwriter
import new_ods_json
from pathlib import Path
import constants as const
from datetime import datetime
from set_email import send_email

SCRIPT_NAME = 'upskill-sfcc-ods-list'
GREETING = 'Hi Team'
SCRIPT_START_TIME = time.perf_counter()
TODAY_IS = datetime.today().strftime('%Y-%m-%d')

logFormat = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{SCRIPT_NAME}-{TODAY_IS}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=logFormat)
logger = logging.getLogger()

urllib3.disable_warnings()


def log_and_print(text):
    print(text)
    logger.debug(text)


workbook = xlsxwriter.Workbook(f'{SCRIPT_NAME}_{TODAY_IS}.xlsx')
excel_file = f'{SCRIPT_NAME}_{TODAY_IS}.xlsx'
worksheet = workbook.add_worksheet('Academy ODS List')
boldFormat = workbook.add_format({'bold': True})
worksheetHeader = ['SandboxID', 'Realm', 'Instance', 'Resource profile', 'State', 'Created at', 'Created by', 'Host name', 'Business Manager']
worksheet.write_row(0, 0, worksheetHeader, boldFormat)

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
    'Authorization': 'Bearer ' + access_token['access_token']
}

row_number = 1
column_number = 0
new_sandbox = []

for _ in range(2):

    log_and_print('Create new sandbox')
    create_new_sandbox = requests.post(url_links.SANDBOX_URL,
                                       headers=headers, verify=False, json=new_ods_json.create_json).json()
    log_and_print(create_new_sandbox)

    sandbox_id = create_new_sandbox['data']['id']
    new_sandbox.append(sandbox_id)
    realm = create_new_sandbox['data']['realm']
    new_sandbox.append(realm)
    instance = create_new_sandbox['data']['instance']
    new_sandbox.append(instance)
    resource_profile = create_new_sandbox['data']['resourceProfile']
    new_sandbox.append(resource_profile)
    state = create_new_sandbox['data']['state']
    new_sandbox.append(state)
    created_at = create_new_sandbox['data']['createdAt']
    new_sandbox.append(created_at)
    created_by = create_new_sandbox['data']['createdBy']
    new_sandbox.append(created_by)
    ods_hostname = create_new_sandbox['data']['hostName']
    new_sandbox.append(ods_hostname)
    bm = create_new_sandbox['data']['links']['bm']
    new_sandbox.append(bm)
    ocapi = create_new_sandbox['data']['links']['ocapi']
    impex = create_new_sandbox['data']['links']['impex']
    code = create_new_sandbox['data']['links']['code']
    logs = create_new_sandbox['data']['links']['logs']

    worksheet.write_row(row_number, column_number, new_sandbox)
    row_number += 1

    new_sandbox.clear()
    logger.debug(f'List to fill has been cleared - {new_sandbox}')

    time.sleep(10)

workbook.close()
log_and_print('Data has been written into the excel file')

script_finish_time = time.perf_counter()
log_and_print(
    f'Script execution time is {round(script_finish_time - SCRIPT_START_TIME, 2)} seconds. Keep in mind there will be around 0,5 seconds difference between this time and what will be received in email as execution time')

email_recipient = f'kosyoyanev2@gmail.com,{const.my_personal_email}'
email_subject = SCRIPT_NAME
email_text = f'{GREETING}. My name is {SCRIPT_NAME}. I am sending you Excel file with ods info.'
email_attachment = str(Path.cwd() / excel_file)
send_email(email_recipient, email_subject, email_text, email_attachment)
