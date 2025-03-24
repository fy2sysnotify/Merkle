# "I've been waiting for you, Obi-Wan. We meet again, at last.
# The circle is now complete. When I left you, I was but the learner.
# Now I am the master."

import os
import logging
import urllib3
import requests
import mysql.connector
from pathlib import Path
from datetime import datetime
import constants as const
from set_email import send_email
from client_creds_token import get_access_token

# Set script name
script_name = 'zwilling-ods-usage-2db'

# Set credits start date - must be in ISO 8601 format
credits_start_date = '2021-01-01'

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


try:
    access_token = get_access_token()
except ValueError as value_error:
    logger.error(value_error)
    log_and_print('Failed to get authorization for access token.')
    email_recipient = const.my_business_email
    email_subject = f'Failed to get authorization for access token in {script_name}'
    email_text = f'Failed to get authorization for access token in {script_name}.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

try:
    headers = {'Authorization': f'Bearer {access_token}'}
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
    log_and_print('Failed to get Sandbox list')
    email_recipient = const.my_business_email
    email_subject = f'Failed to get Sandbox lists in cron job - {script_name}'
    email_text = f'Failed to get Sandbox lists in cron job - {script_name}.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

log_and_print(f'First request endpoint answer is {sandbox_list}')

data_for_db = []
for i in sandbox_list['data']:
    realm = i['realm']
    realm_name = ''
    if realm == 'bcgv':  # Smenyash ID-to mezhdu kavichkite s tova na klienta, koito iskash da reportvash. ID-to se vzima ot https://wiki.isobarsystems.com/display/SUPTEAM/Local+POD+time+-+Notifications
        realm_name = 'Zwilling'  # Smenyash imeto mezhdu kavichkite s tova na klienta, koito iskash da reportvash.
        sandbox_id = i['id']
        time_stamp = datetime.now()
        time_stamp = time_stamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        list2fill = [time_stamp, sandbox_id, realm_name]
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
        log_and_print('Second request endpoint - get Sandbox usage since inception')

        create_date = created_at[:10]

        sandbox_usage_since_created = None

        try:
            sandbox_usage_since_created = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from={create_date}",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            log_and_print('Failed to get Sandbox usage from second request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage since inception in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage since inception in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        log_and_print(f'Second request endpoint answer is {sandbox_usage_since_created}')

        minutes_up_since_created = sandbox_usage_since_created['data']['minutesUp']
        list2fill.append(minutes_up_since_created)
        minutes_down_since_created = sandbox_usage_since_created['data']['minutesDown']
        list2fill.append(minutes_down_since_created)
        total_credits = minutes_up_since_created + (minutes_down_since_created * 0.3)
        list2fill.append(total_credits)
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
            log_and_print('Failed to get Sandbox usage from third request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage for the last 24 hours in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage for the last 24 hours in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        log_and_print(f'Third request endpoint answer is {sandbox_usage_last24}')

        minutes_up_last24 = sandbox_usage_last24['data']['minutesUp']
        list2fill.append(minutes_up_last24)
        minutes_down_last24 = sandbox_usage_last24['data']['minutesDown']
        list2fill.append(minutes_down_last24)
        logger.debug(f'List to fill with parsed values from third request endpoint is {list2fill}')

        # Make request with sandboxIDs to get Sandbox usage since 2021-01-01
        log_and_print('Fourth request endpoint - get Sandbox usage since 2021-01-01')

        this_sandbox_usage_since2021_01_01 = None

        try:
            this_sandbox_usage_since2021_01_01 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes/{sandbox_id}/usage?from=2021-01-01",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            logger.debug('Failed to get Sandbox usage from fourth request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage since 21.01.01. in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage since 21.01.01. in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        log_and_print(f'Fourth request endpoint answer is {this_sandbox_usage_since2021_01_01}')

        this_sandbox_minutes_up210101 = this_sandbox_usage_since2021_01_01['data']['minutesUp']
        this_sandbox_minutes_down210101 = this_sandbox_usage_since2021_01_01['data']['minutesDown']
        credits_spent_on_this_sandbox210101 = this_sandbox_minutes_up210101 + (this_sandbox_minutes_down210101 * 0.3)
        list2fill.append(credits_spent_on_this_sandbox210101)
        logger.debug(f'List to fill with parsed values from fourth request endpoint is {list2fill}')

        # Get usage for realm bcgv since 01.01.2021
        log_and_print('Fifth request endpoint - get Sandbox usage on realm bcgv since 2021-01-01')

        sandbox_usage_on_realm_bcgv_since2021_01_01 = None

        try:
            sandbox_usage_on_realm_bcgv_since2021_01_01 = requests.get(
                f"https://admin.us01.dx.commercecloud.salesforce.com/api/v1/realms/bcgv/usage?from=2021-01-01",
                headers=headers).json()
        except Exception as conn_error:
            logger.error(conn_error)
            log_and_print('Failed to get Sandbox usage on realm bcgv from fifth request endpoint')
            email_recipient = const.my_business_email
            email_subject = f'Failed to get Sandbox usage on realm bcgv since 21.01.01 in cron job - {script_name}'
            email_text = f'Failed to get Sandbox usage on realm bcgv since 21.01.01 in cron job - {script_name}. Check the attached logs'
            email_attachment = str(Path.cwd() / script_log_file)
            send_email(email_recipient, email_subject, email_text, email_attachment)
            raise

        log_and_print(f'Fifth request endpoint answer is {sandbox_usage_on_realm_bcgv_since2021_01_01}')

        realm_bcgv_minutes_up210101 = sandbox_usage_on_realm_bcgv_since2021_01_01['data']['minutesUp']
        realm_bcgv_minutes_down210101 = sandbox_usage_on_realm_bcgv_since2021_01_01['data']['minutesDown']
        credits_spent_on_realm_bcgv = realm_bcgv_minutes_up210101 + (realm_bcgv_minutes_down210101 * 0.3)
        list2fill.append(credits_spent_on_realm_bcgv)
        tuple2fill = tuple(list2fill)
        data_for_db.append(tuple2fill)

log_and_print('Open DB connection and insert data')

db = None

try:
    db = mysql.connector.connect(
        host="localhost",
        user=os.getenv('MySQLUser'),
        passwd=os.getenv('MySQLPassword'),
        database='odsreports'
    )

    cursor = db.cursor()

    sql = 'INSERT INTO ZwillingODSUsage(TimeStamp, SandboxID, Realm, Instance, State, CreatedAt, CreatedBy, MinutesUpSinceCreated, MinutesDownSinceCreated, TotalCredits, MinutesUpInLast24Hours, MinutesDownInLast24Hours, ThisODSCreditsSince01012021, TotalCreditsInRealmSince01012021) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

    cursor.executemany(sql, data_for_db)
    db.commit()

except mysql.connector.Error as dbError:
    db.rollback()
    logger.error(dbError)
    logger.debug(f'Failed to connect or insert to database in {script_name}')
    email_recipient = const.my_business_email
    email_subject = f'Failed to connect or insert to database in {script_name}'
    email_text = f'Failed to connect or insert to database in {script_name}.'
    email_attachment = str(Path.cwd() / script_log_file)
    send_email(email_recipient, email_subject, email_text, email_attachment)
    raise

db.close()

log_and_print('Data inserted and DB connection closed')
