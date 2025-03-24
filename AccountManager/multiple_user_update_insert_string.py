import requests
import url_links
from get_totp_headless_browsing import get_access_token


access_token = get_access_token()

try:
    headers = {'Authorization': f'Bearer {access_token}'}
except KeyError as key_error:
    print(key_error)
    raise

try:
    am_response = requests.get('https://account.demandware.com/dw/rest/v1/users?page=0&size=5000', headers=headers).json()
except Exception as conn_error:
    print(conn_error)
    raise

counter = 0
for item in am_response['content']:
    if item['userState'] == 'ENABLED' and '@merklecxm.com' in item['mail'] and 'CCDX_SBX_USER:aaay_sbx' in item['roleTenantFilter']:
        counter += 1
        user_id = item['id']
        mail = item['mail']
        roleTenantFilter = item['roleTenantFilter']
        print(mail, roleTenantFilter)
        # roleTenantFilter = roleTenantFilter.replace('CCDX_SBX_USER:aaay_sbx,', 'CCDX_SBX_USER:')
        # roleTenantFilter = roleTenantFilter.replace('ECOM_ADMIN:', 'ECOM_ADMIN:bjxb_sbx,')
        # data = {'roleTenantFilter': roleTenantFilter}
        #
        # try:
        #     am_response = requests.put(f'{url_links.users_endpoint}/{user_id}', headers=headers, json=data).json()
        # except Exception as conn_error:
        #     print(conn_error)
        #     raise
        #
        # print(am_response)


print(counter)
