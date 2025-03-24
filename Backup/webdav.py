from webdav3.client import Client as webdavClient

options = {
 'webdav_hostname': 'put here url',
 'webdav_login':    'put username',
 'webdav_password': 'put password'
}
webdav = webdavClient(options)
webdav.verify = False
webdav.upload_directory('put name of destination folder', 'put name of resources folder')

