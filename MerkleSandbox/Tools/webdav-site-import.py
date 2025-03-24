from urllib.parse import urlparse
from webdav3.client import Client as webdavClient
import constants as const

file_to_import = '223_InventoryListsOps_ZWG_Stag_20220317.zip'
sfcc_instance = 'https://aaay-008.sandbox.us01.dx.commercecloud.salesforce.com'
import_location = '/on/demandware.servlet/webdav/Sites/impex'

print(sfcc_instance)

# WebDav upload of Code Version
options = {
    'webdav_hostname': sfcc_instance,
    'webdav_login': const.my_ods_email,
    'webdav_password': const.my_ods_pass,
    'webdav_timeout': 300
}
webdav = webdavClient(options)
webdav.verify = False

try:
    webdav.upload_file(import_location, file_to_import)
except Exception as e:
    print(e)
    raise
