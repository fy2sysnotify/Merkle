import time
import requests
import url_links
from get_totp_headless_browsing import get_access_token
from excel_to_list import convert_excel_to_list

script_start_time = time.perf_counter()

# This is used if users are in Excel file. Please use Excel with single sheet and single column
users_to_disable = convert_excel_to_list(file_name='users_to_disable.xlsx', column_name='users')

access_token = get_access_token()

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

try:
    am_response = requests.get('https://account.demandware.com/dw/rest/v1/users?page=0&size=5000', headers=headers).json()
except Exception as conn_error:
    print(conn_error)
    raise

counter = 0
for item in am_response['content']:
    for email in users_to_disable:
        if item['mail'] == email:
            counter += 1
            user_id = (item['id'])
            data = {'userState': 'DELETED'}

            try:
                am_response = requests.put(f'{url_links.users_endpoint}/{user_id}', headers=headers, json=data).json()
            except Exception as conn_error:
                print(conn_error)
                raise

            print(am_response)

print(f'{counter} users were disabled')

script_finish_time = time.perf_counter()
print(f'Script execution time was {round(script_finish_time - script_start_time, 2)} seconds.')
