import os

client_id = os.getenv('ODS_REPORT_CLIENT_ID')
client_secret = os.getenv('ODS_REPORT_CLIENT_SECRET')
username = os.getenv('ODS_REPORT_USERNAME')
password = os.getenv('ODS_REPORT_PASSWORD')
ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
db_host = 'localhost',
db_user = os.getenv('MySQLUser'),
db_password = os.getenv('MySQLPassword'),
db_database = 'odsreports'
slack_token = os.getenv('SLACK_BOT')
access_token_auth_url = 'https://account.demandware.com:443/dwsso/oauth2/access_token'
sandbox_list_url = 'https://admin.us01.dx.commercecloud.salesforce.com/api/v1/sandboxes?include_deleted=false'
my_business_email = 'konstantin.yanev@isobar.com'
my_personal_email = 'kosyoyanev@gmail.com'
