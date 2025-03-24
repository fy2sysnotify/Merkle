# "Size matters not. Look at me. Judge me by my size, do you? Hmm? Hmm. And well you should not. For my ally is the Force
# and a powerful ally it is. Life creates it, makes it grow. Its energy surrounds us and binds us. Luminous beings are we,
# not this crude matter. You must feel the Force around you; here, between you, me, the tree, the rock, everywhere, yes.
# Even between the land and the ship."

import logging
import requests
import urllib3
import xlsxwriter
import pandas as pd
from pathlib import Path
import constants as const
from set_email import send_email
from client_creds_token import get_access_token

# Set script name
script_name = 'shiseido-emea-ods-usage-report'

# Set credits start date - must be in ISO 8601 format
credits_start_date = '2022-03-18'

# Create and configure logger
log_format = '%(levelname)s %(asctime)s - %(message)s'
script_log_file = f'{script_name}-{const.today_is}.log'
logging.basicConfig(filename=script_log_file,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

# Disable warnings
urllib3.disable_warnings()


def log_and_print(text):
    print(text)
    logger.debug(text)


# Create excel workbook and worksheet in workbook for today's report
workbook = xlsxwriter.Workbook(f'{script_name}_{const.today_is}.xlsx')
excel_file = f'{script_name}_{const.today_is}.xlsx'
worksheet = workbook.add_worksheet('Sandbox usage report')

# Add bold formatting
bold_format = workbook.add_format({'bold': True})

# Add headers to excel worksheet with bold format
worksheet_header = ['SandboxID', 'Realm', 'Instance', 'State', 'Created at', 'Created by', 'Minutes up since created',
                    'Minutes down since created', 'Total credits', 'Minutes up in last 24 hours',
                    'Minutes down in last 24 hours', 'Credits since 18.03.2022']
worksheet.write_row(0, 0, worksheet_header, bold_format)
logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

try:
    access_token = get_access_token()
except ValueError as value_error:
    logger.error(value_error)
    logger.debug('Failed to get authorization for access token.')
    email_recipient = const.my_business_email
    email_subject = f'Failed to get authorization for access token in {script_name}'
    email_text = f'Failed to get authorization for access token in {script_name}.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

try:
    headers = {'Authorization': 'Bearer ' + access_token}
except KeyError as key_error:
    logger.error(key_error)
    logger.debug('Some of the credentials are invalid. Check them carefully')
    email_recipient = const.my_business_email
    email_subject = f'Some of the credentials in cron job - {script_name} are invalid'
    email_text = f'Failed to get access token in cron job - {script_name}. Some of the credentials are invalid. Check them carefully.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug('We got the access token')

# Make request to url for listing all ODS - Sandbox On Demand
log_and_print('First request endpoint - get list of all sandboxes')

try:
    sandbox_list = requests.get(const.sandbox_list_url,
                                headers=headers, verify=False).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox list')
    email_recipient = const.my_business_email
    email_subject = f'Failed to get Sandbox lists in cron job - {script_name}'
    email_text = f'Failed to get Sandbox lists in cron job - {script_name}.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug(f'First request endpoint answer is {sandbox_list}')

row_number = 1
column_number = 0
list2fill = []
for i in sandbox_list['data']:
    realm = i['realm']
    realm_name = ''
    if realm == 'bcmq':  # Smenyash ID-to mezhdu kavichkite s tova na klienta, koito iskash da reportvash. ID-to se vzima ot https://wiki.isobarsystems.com/display/SUPTEAM/Local+POD+time+-+Notifications
        realm_name = 'Shiseido-EMEA'  # Smenyash imeto mezhdu kavichkite s tova na klienta, koito iskash da reportvash.
        sandbox_id = i['id']
        instance = i['instance']
        realm_url = i['hostName']
        state = i['state']
        created_at = i['createdAt']
        created_by = i['createdBy']
        list2fill.extend(
            (sandbox_id, realm_name, realm_url, state, created_at, created_by)
        )

        logger.debug(f'List to fill with parsed values from first request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since inception
        log_and_print('Second request endpoint - get Sandbox usage since inception')

        create_date = created_at[:10]

        sandbox_usage_since_inception = None

        try:
            sandbox_usage_since_inception = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={create_date}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from second request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage since inception in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage since inception in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        logger.debug(f'Second request endpoint answer is {sandbox_usage_since_inception}')

        minutes_up = sandbox_usage_since_inception['data']['minutesUp']
        list2fill.append(minutes_up)
        minutes_down = sandbox_usage_since_inception['data']['minutesDown']
        list2fill.append(minutes_down)
        credits_spent_on_realm_bcmq = minutes_up + (minutes_down * 0.3)
        list2fill.append(credits_spent_on_realm_bcmq)
        logger.debug(f'List to fill with parsed values from second request endpoint is {list2fill}')

        # Make request with sandboxIDs to get each Sandbox usage since yesterday
        log_and_print('Third request endpoint - Sandbox usage since yesterday')

        sandbox_usage_last24 = None

        try:
            sandbox_usage_last24 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={const.yesterday_is}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from third request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage for the last 24 hours in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage for the last 24 hours in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        logger.debug(f'Third request endpoint answer is {sandbox_usage_last24}')

        minutes_up_last24 = sandbox_usage_last24['data']['minutesUp']
        list2fill.append(minutes_up_last24)
        minutes_down_last24 = sandbox_usage_last24['data']['minutesDown']
        list2fill.append(minutes_down_last24)
        logger.debug(f'List to fill with parsed values from third request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since 2022-03-01
        log_and_print(f'Fourth request endpoint - Sandbox usage since {credits_start_date}')

        sandbox_usage_on_realm_bcmq_since2022_03_18 = None

        try:
            sandbox_usage_on_realm_bcmq_since2022_03_18 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={credits_start_date}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from fourth request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage since {credits_start_date}. in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage since {credits_start_date}. in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        logger.debug(f'Fourth request endpoint answer is {sandbox_usage_on_realm_bcmq_since2022_03_18}')

        realm_bcmq_minutes_up220318 = sandbox_usage_on_realm_bcmq_since2022_03_18['data']['minutesUp']
        realm_bcmq_minutes_down220318 = sandbox_usage_on_realm_bcmq_since2022_03_18['data']['minutesDown']
        credits_spent_on_realm_bcmq = realm_bcmq_minutes_up220318 + (realm_bcmq_minutes_down220318 * 0.3)
        list2fill.append(credits_spent_on_realm_bcmq)
        logger.debug(f'List to fill with parsed values from fourth request endpoint is {list2fill}')

        # Write the list with data to excel worksheet
        worksheet.write_row(row_number, column_number, list2fill)
        row_number += 1

        list2fill.clear()
        logger.debug(f'List to fill has been cleared - {list2fill}')
    else:
        list2fill.clear()

# Write data to Excel table, save and close
workbook.close()
logger.debug('Data has been written into the excel file')

# Get usage for realm bcmq since18.03.2022
log_and_print(f'Fifth request endpoint - get Sandbox usage on realm bcmq since {credits_start_date}')

sandbox_usage_on_realm_bcmq_since2022_03_18 = None

try:
    sandbox_usage_on_realm_bcmq_since2022_03_18 = requests.get(
        f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/realms/bcmq/usage?from={credits_start_date}",
        headers=headers).json()
except Exception as conn_error:
    logger.error(conn_error)
    logger.debug('Failed to get Sandbox usage on realm aaay from fifth request endpoint')
    email_recipient = const.my_business_email
    email_subject = f'Failed to get Sandbox usage on realm bcmq since {credits_start_date} in cron job - {script_name}'
    email_text = f'Failed to get Sandbox usage on realm bcmq since {credits_start_date} in cron job - {script_name}. Check the attached logs'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

logger.debug(f'Fifth request endpoint answer is {sandbox_usage_on_realm_bcmq_since2022_03_18}')

realm_bcmq_minutes_up220318 = sandbox_usage_on_realm_bcmq_since2022_03_18['data']['minutesUp']
realm_bcmq_minutes_down220318 = sandbox_usage_on_realm_bcmq_since2022_03_18['data']['minutesDown']
credits_spent_on_realm_bcmq = realm_bcmq_minutes_up220318 + (realm_bcmq_minutes_down220318 * 0.3)
log_and_print(credits_spent_on_realm_bcmq)

# Convert Excel to pandas dataframe
df = pd.read_excel(excel_file)
data_frame = pd.DataFrame(df)
logger.debug('Data has been transformed from excel to pandas dataframe')

# Sort Pandas dataframe by column 'CreatedAt'
data_frame.sort_values(by=['Created at'], inplace=True, ascending=False)

# Add row with total credits spend on realm
last_dataframe_row = {'SandboxID': '', 'Realm': '', 'Instance': '', 'State': '', 'Created at': '', 'Created by': '',
                      'Minutes up since created': '', 'Minutes down since created': '', 'Total credits': '',
                      'Minutes up in last 24 hours': '', 'Minutes down in last 24 hours': '',
                      'Credits since 18.03.2022': credits_spent_on_realm_bcmq}
data_frame = data_frame.append(last_dataframe_row, ignore_index=True)

# Convert pandas to html, remove index column and align to center
html = data_frame.to_html(index=False)
html2_attach = html.replace('<tr>', '<tr align="center">')
logger.debug('Data has been transformed from pandas dataframe to html with index column removed')

# Add text to the email
emailText = f'Hi Team. My name is {script_name}. Please check the overview for today. Keep in mind that living sandboxes on demand are spending credits. Each minute uptime for Medium ODS = 1 credit. And each minute down time = 0.3 credit. If you have any questions, please do not hesitate to contact Merkle Operations Support.'


email_recipient = f'{const.my_business_email},kosyoyanev@gmail.com'
email_subject = 'Shiseido EMEA ODS update for today'
email_text = emailText + html2_attach
email_attachment = str(Path.cwd() / excel_file)
send_email(email_recipient, email_subject, email_text, email_attachment)
