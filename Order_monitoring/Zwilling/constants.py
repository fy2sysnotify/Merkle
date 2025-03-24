import os

ods_email = os.getenv('ODS_MONITORING_EMAIL')
ods_pass = os.getenv('ODS_MONITORING_PASS')
smtp_server = os.getenv('ISOBARSMTP')
smtp_port = os.getenv('ISOBARSMTPPORT')
slack_token = os.getenv('SLACK_BOT_GRAFANA')
my_ods_email = os.getenv('BUSINESS_EMAIL')
my_ods_pass = os.getenv('CREATE_ODS_PASSWORD')
zwilling_prod = 'https://production-eu01-zwilling.demandware.net'
orders_url = '/on/demandware.servlet/webdav/Sites/Impex/src/order/'
order_archive = '/outgoing/archive'
