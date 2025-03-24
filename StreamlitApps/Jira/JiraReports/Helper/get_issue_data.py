import requests
import json
from decouple import config

# Replace with your API token and Jira domain
api_token = config('JIRA_TOKEN', default='')
issue_key = 'CLRG-65764'
url = f'https://jira-emea.merkle.com/rest/api/2/issue/{issue_key}'

response = requests.get(
    url,
    headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
)

if response.status_code == 200:
    issue_data = response.json()
    print(json.dumps(issue_data, indent=4))
    print(issue_data['fields']['priority']['name'])
else:
    print(f"Failed to retrieve issue: {response.status_code}, {response.text}")
