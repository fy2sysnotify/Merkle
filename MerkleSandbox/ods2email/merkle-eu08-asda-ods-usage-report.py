import os
import requests
import urllib3
import xlsxwriter
import pandas as pd
from pathlib import Path
import constants as const
from my_logger import configure_logger
from set_email import send_email
from client_creds_token import get_access_token

script_name = Path(__file__).stem
credits_start_date = '2022-07-14'
logger = configure_logger(script_name)

urllib3.disable_warnings()

workbook = xlsxwriter.Workbook(f'{script_name}_{const.today_is}.xlsx')
excel_file = f'{script_name}_{const.today_is}.xlsx'
worksheet = workbook.add_worksheet('Sandbox usage report')
bold_format = workbook.add_format({'bold': True})
worksheet_header = ['SandboxID', 'Realm', 'Instance', 'State', 'Created at', 'Created by', 'Minutes up since created',
                    'Minutes down since created', 'Total credits', 'Minutes up in last 24 hours',
                    'Minutes down in last 24 hours', 'Credits since 14.07.2022']
worksheet.write_row(0, 0, worksheet_header, bold_format)
logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

access_token = get_access_token(
    os.getenv('CLIENT_ID_ODS'),
    os.getenv('CLIENT_SECRET_ODS')
)

headers = {
    'Authorization': 'Bearer ' + access_token
}


def get_sandbox_list():
    with requests.get(
            const.sandbox_list_url,
            headers=headers,
            verify=False
    ) as response:
        ods_list_response = response.json()

        return ods_list_response


sandbox_list = get_sandbox_list()

logger.debug(f'First request endpoint answer is {sandbox_list}')

row_number = 1
column_number = 0
list2fill = []
for i in sandbox_list['data']:
    realm = i['realm']
    realm_name = ''
    if realm == 'bjxb':  # Smenyash ID-to mezhdu kavichkite s tova na klienta, koito iskash da reportvash. ID-to se vzima ot https://wiki.isobarsystems.com/display/SUPTEAM/Local+POD+time+-+Notifications
        realm_name = 'asda.eu08'  # Smenyash imeto mezhdu kavichkite s tova na klienta, koito iskash da reportvash.
        sandbox_id = i['id']
        list2fill.extend((sandbox_id, realm_name))
        instance = i['instance']
        realm_url = i['hostName']
        list2fill.append(realm_url)
        state = i['state']
        list2fill.append(state)
        created_at = i['createdAt']
        list2fill.append(created_at)
        created_by = i['createdBy']
        list2fill.append(created_by)
        logger.debug(f'List to fill with parsed values from first request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since inception
        logger.info('Second request endpoint - get Sandbox usage since inception')

        create_date = created_at[:10]

        sandbox_usage_since_inception = None

        try:
            sandbox_usage_since_inception = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={create_date}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            raise

        logger.debug(f'Second request endpoint answer is {sandbox_usage_since_inception}')

        minutes_up = sandbox_usage_since_inception['data']['minutesUp']
        list2fill.append(minutes_up)
        minutes_down = sandbox_usage_since_inception['data']['minutesDown']
        list2fill.append(minutes_down)
        credits_spent_on_realm_bjxb = minutes_up + (minutes_down * 0.3)
        list2fill.append(credits_spent_on_realm_bjxb)
        logger.debug(f'List to fill with parsed values from second request endpoint is {list2fill}')

        # Make request with sandboxIDs to get each Sandbox usage since yesterday
        logger.info('Third request endpoint - Sandbox usage since yesterday')

        sandbox_usage_last24 = None

        try:
            sandbox_usage_last24 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={const.yesterday_is}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            raise

        logger.debug(f'Third request endpoint answer is {sandbox_usage_last24}')

        minutes_up_last24 = sandbox_usage_last24['data']['minutesUp']
        list2fill.append(minutes_up_last24)
        minutes_down_last24 = sandbox_usage_last24['data']['minutesDown']
        list2fill.append(minutes_down_last24)
        logger.debug(f'List to fill with parsed values from third request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since 2022-07-14
        logger.info(f'Fourth request endpoint - Sandbox usage since {credits_start_date}')

        sandbox_usage_on_realm_bjxb_since2022_07_14 = None

        try:
            sandbox_usage_on_realm_bjxb_since2022_07_14 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={credits_start_date}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            raise

        logger.debug(f'Fourth request endpoint answer is {sandbox_usage_on_realm_bjxb_since2022_07_14}')

        realm_bjxb_minutes_up220714 = sandbox_usage_on_realm_bjxb_since2022_07_14['data']['minutesUp']
        realm_bjxb_minutes_down220714 = sandbox_usage_on_realm_bjxb_since2022_07_14['data']['minutesDown']
        credits_spent_on_realm_bjxb = realm_bjxb_minutes_up220714 + (realm_bjxb_minutes_down220714 * 0.3)
        list2fill.append(credits_spent_on_realm_bjxb)
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

# Get usage for realm bjxb since 14.07.2022
logger.info(f'Fifth request endpoint - get Sandbox usage on realm bjxb since {credits_start_date}')

sandbox_usage_on_realm_bjxb_since2022_07_14 = None

try:
    sandbox_usage_on_realm_bjxb_since2022_07_14 = requests.get(
        f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/realms/bjxb/usage?from={credits_start_date}",
        headers=headers).json()
except Exception as conn_error:
    logger.error(conn_error)
    raise

logger.debug(f'Fifth request endpoint answer is {sandbox_usage_on_realm_bjxb_since2022_07_14}')

realm_bjxb_minutes_up220714 = sandbox_usage_on_realm_bjxb_since2022_07_14['data']['minutesUp']
realm_bjxb_minutes_down220714 = sandbox_usage_on_realm_bjxb_since2022_07_14['data']['minutesDown']
credits_spent_on_realm_bjxb = realm_bjxb_minutes_up220714 + (realm_bjxb_minutes_down220714 * 0.3)
logger.info(credits_spent_on_realm_bjxb)

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
                      'Credits since 14.07.2022': credits_spent_on_realm_bjxb}
data_frame = data_frame.append(last_dataframe_row, ignore_index=True)

# Convert pandas to html, remove index column and align to center
html = data_frame.to_html(index=False)
html2_attach = html.replace('<tr>', '<tr align="center">')
logger.debug('Data has been transformed from pandas dataframe to html with index column removed')

# Add text to the email
emailText = f'Hi Team. My name is "{script_name}". Please check the overview for today. Keep in mind that living sandboxes on demand are spending credits. You can check more on the topic here - https://documentation.b2c.commercecloud.salesforce.com/DOC1/topic/com.demandware.dochelp/content/b2c_commerce/topics/sandboxes/b2c_sandbox_resource_profiles.html. If you have any questions, please do not hesitate to contact Merkle Operations Support.'

email_recipient = 'kosyoyanev@gmail.com'
email_subject = 'Merkle ASDA.EU08 ODS update for today'
email_text = emailText + html2_attach
email_attachment = str(Path.cwd() / excel_file)
send_email(email_recipient, email_subject, email_text, email_attachment)
