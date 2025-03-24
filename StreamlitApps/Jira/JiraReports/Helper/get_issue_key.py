import requests

# Jira API endpoint
url = "https://jira-emea.merkle.com/rest/api/2/search"

# JQL query
jql_query = """
project = CLRG
AND issuetype = "Support Request" 
AND created >= startOfMonth(-2) 
AND created <= endOfMonth(-2) 
AND cf[10200] = "PSR01"
"""

# Parameters
params = {
    "jql": jql_query,
    "fields": "key",  # Only fetch issue keys
    "maxResults": 1000  # Adjust this as needed, Jira default is 50
}

# Authentication details (token only)
api_token = "NTIyODY0MzQ1NzMwOlOswsq1hyDeevfgpvqwEb4H/NrK"

# Headers
headers = {
    "Authorization": f"Bearer {api_token}",
    "Accept": "application/json"
}

# Make the request
response = requests.get(url, headers=headers, params=params)

# Check for successful response
if response.status_code == 200:
    issues = response.json()["issues"]
    issue_keys = [issue["key"] for issue in issues]
    for key in issue_keys:
        print(key)
else:
    print(f"Failed to fetch issues: {response.status_code} - {response.text}")
