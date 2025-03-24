import os
import time
import json
import requests
import pandas as pd


script_start_time = time.perf_counter()

df = pd.read_excel('empty_email_users_la_jira.xlsx')

jira_user = os.getenv('j_prd_us_la')
jira_pass = os.getenv('j_prd_ps_la')
jira_server = os.getenv('j_prd_url_la')

with requests.Session() as session:
    session.auth = (jira_user, jira_pass)

    headers = {
        "Content-Type": "application/json"
    }

    for index, row in df.iterrows():
        user = row['name']
        user_new_email = row['emailAddress']

        url = f'{jira_server}/rest/api/2/user?username={user}'

        data = {
            "name": user, "emailAddress": user_new_email
        }

        response = session.put(url, headers=headers, data=json.dumps(data))

        print(response.status_code)

        if response.status_code == 200:
            data = response.json()
            email = data["emailAddress"]
            print(f"Successfully updated email for {user}: {email}")
        else:
            print(f"Failed to update email for {user}. Status code: {response.status_code}")

    script_finish_time = time.perf_counter()

    print(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')
