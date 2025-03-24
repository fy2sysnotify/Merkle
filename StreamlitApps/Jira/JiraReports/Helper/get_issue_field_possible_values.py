import requests
import json

api_token = 'NTIyODY0MzQ1NzMwOlOswsq1hyDeevfgpvqwEb4H/NrK'
domain = 'jira-emea.merkle.com'

# API endpoint for all fields
url = f'https://{domain}/rest/api/2/field'

# Headers
headers = {
    'Authorization': f'Bearer {api_token}',
    'Accept': 'application/json'
}

# Make the request to get all fields
response = requests.get(url, headers=headers)

# Check the response
if response.status_code == 200:
    fields = response.json()
    # Find the custom field
    custom_field = next((field for field in fields if field['id'] == 'customfield_10200'), None)
    if custom_field:
        print(json.dumps(custom_field, indent=4))
    else:
        print("Custom field not found")
else:
    print(f"Failed to retrieve fields: {response.status_code}")
    print(response.text)
