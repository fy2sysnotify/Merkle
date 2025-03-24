import os
import datetime
import logging
from pathlib import Path
import dateutil.relativedelta
import pandas as pd
import requests
import urllib3
import xlsxwriter
import constants as const
from client_creds_token import get_access_token
from set_email import send_email
from my_logger import configure_logger


class SandboxUsage:
    def __init__(self, sandbox_id: str, access_token: str, logger: logging.Logger):
        self.sandbox_id = sandbox_id
        self.access_token = access_token
        self.logger = logger

    def get_last_month_usage(self):
        last_month = datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)
        usage_start_date = last_month.strftime('%Y-%m-%d')

        headers = {'Authorization': 'Bearer ' + self.access_token}

        try:
            with requests.Session() as session:
                last_month_usage = session.get(
                    f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{self.sandbox_id}/usage?from={usage_start_date}",
                    headers=headers).json()
        except Exception as conn_error:
            self.logger.error(f'Failed to get Sandbox usage for the last month from api\n{conn_error}')
            raise

        return {
            'minutes_up': last_month_usage['data']['minutesUp'],
            'minutes_down': last_month_usage['data']['minutesDown'],
            'credits_spent': last_month_usage['data']['minutesUp'] + (last_month_usage['data']['minutesDown'] * 0.3),
        }

    def write_to_excel(self, data: list, filename: str):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet('Sandbox usage report')

        bold_format = workbook.add_format({'bold': True})

        worksheet_header = ['SandboxID', 'Minutes up for previous month', 'Minutes down for previous month',
                            'Credits for previous month']
        worksheet.write_row(0, 0, worksheet_header, bold_format)
        self.logger.debug('Workbook and worksheet created. Headers and bold format to headers added')

        worksheet.write_row(1, 0, data)

        workbook.close()
        self.logger.debug('Data has been written into the excel file')

    def read_excel(self, filename: str):
        df = pd.read_excel(filename)
        return pd.DataFrame(df)


def main():
    script_name = Path(__file__).stem
    script_log_file = f'{script_name}-{const.today_is}.log'
    logger = configure_logger(Path(__file__).stem)

    urllib3.disable_warnings()

    try:
        access_token = get_access_token(os.getenv('CLIENT_ID_ODS'), os.getenv('CLIENT_SECRET_ODS'))
    except ValueError as value_error:
        logger.error(f'Failed to get authorization for access token.\n{value_error}')
        raise

    sandbox_id = '82a4552f-7e6a-4241-8c4a-275d148e0141'
    usage = SandboxUsage(sandbox_id, access_token, logger)
    last_month_usage = usage.get_last_month_usage()

    data = [sandbox_id, last_month_usage['minutes_up'], last_month_usage['minutes_down'],
            last_month_usage['credits_spent']]
    excel_file = f'{script_name}_{const.today_is}.xlsx'
    usage.write_to_excel(data, excel_file)

    data_frame = usage.read_excel(excel_file)
    send_email(data_frame, email_subject='Sandbox usage report',
               email_message='Attached is the report for the previous month Sandbox usage',
               email_to=os.getenv('EMAIL_TO_ODS'), email_from=os.getenv('EMAIL_FROM_ODS'),
               access_token=access_token, logger=logger)


