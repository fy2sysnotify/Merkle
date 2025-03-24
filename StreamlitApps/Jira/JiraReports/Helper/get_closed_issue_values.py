import requests
import json

# Jira instance URL
jira_url = 'https://jira-emea.merkle.com'

# Your JQL query
jql = 'project in (ASD,DNY,CLRG,CCHV,MAYB) AND status changed to Closed during ("2024-05-01", "2024-05-01") AND issuetype = "Support Request"'

# API endpoint for JQL search
search_url = f'{jira_url}/rest/api/2/search'

# Your Jira API token
api_token = 'NTIyODY0MzQ1NzMwOlOswsq1hyDeevfgpvqwEb4H/NrK'

# Set up headers with token-based authentication
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_token}'
}

# Set up the request payload
payload = {
    'jql': jql,
    'startAt': 0,
    'maxResults': 1000  # Adjust the number of results as needed
}

# Make the request to the Jira API
response = requests.post(search_url, data=json.dumps(payload), headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Print the entire JSON response
    print(json.dumps(response.json(), indent=4))
else:
    print(f"Failed to fetch issues: {response.status_code}, {response.text}")
