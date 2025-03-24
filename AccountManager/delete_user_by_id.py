import requests
import time
import pandas as pd  # ✅ Import pandas to read Excel files
import url_links
from get_totp_headless_browsing import get_access_token

# 🔥 Be careful, this is irreversible!
headers = {
    'Authorization': f'Bearer {get_access_token()}',
    'Content-Type': 'application/json'
}

# ✅ Read the Excel file properly
df = pd.read_excel('users.xlsx')

for index, row in df.iterrows():
    user_id = row['id']  # ✅ Make sure 'id' is a valid column in your Excel file
    print(f'user_id to delete = {user_id}')

    am_response = requests.delete(f'{url_links.users_endpoint}/{user_id}', headers=headers)

    print(f'Response status code = {am_response.status_code}')

    time.sleep(2)
