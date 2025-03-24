import os
from datetime import datetime, timedelta

client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
client_id_ods = os.getenv('CLIENT_ID_ODS')
client_secret_ods = os.getenv('CLIENT_SECRET_ODS')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
slack_token = os.getenv('SLACK_BOT')
access_token_auth_url = 'https://account.demandware.com:443/dwsso/oauth2/access_token'
sandbox_list_url = 'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes?include_deleted=false'
totp_auth_url = 'https://account.demandware.com/dwsso/XUI/?realm=%2F&goto=https%3A%2F%2Faccount.demandware.com%3A443%2Fdwsso%2Foauth2%2Fauthorize%3Fresponse_type%3Dtoken%26state%3D%26client_id%3Db4836c9b-d346-43b8-8800-edbf811035c2%26scope%3D%26redirect_uri%3Dhttps%253A%252F%252Fadmin.us01.dx.commercecloud.salesforce.com%252Foauth2-redirect.html#login/'
my_business_email = os.getenv('BUSINESS_EMAIL')
my_personal_email = 'kosyoyanev@gmail.com'
support_email = 'support@merklecxm.com'
my_ods_email = os.getenv('BUSINESS_EMAIL')
my_ods_pass = os.getenv('CREATE_ODS_PASSWORD')
otp_qr = os.getenv('ODS_REPORT_TOTP')
otp_qr_ods = os.getenv('ODS_MONITOR_TOTP')
yesterday_is = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
today_is = datetime.now().strftime('%Y-%m-%d')
