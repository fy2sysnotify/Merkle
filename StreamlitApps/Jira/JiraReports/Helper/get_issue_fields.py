import requests
from decouple import config

# Replace with your API token and Jira domain
api_token = config('JIRA_TOKEN', default='')
url = 'https://jira-emea.merkle.com/rest/api/2/field'

# Make the API request with the token in the Authorization header
response = requests.get(
    url,
    headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
)

# Check for HTTP errors
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print(f"HTTP error occurred: {err}")
    print(f"Response content: {response.text}")
else:
    try:
        fields = response.json()
        for field in fields:
            print(f"Field ID: {field['id']}, Field Name: {field['name']}")
    except requests.exceptions.JSONDecodeError as json_err:
        print(f"JSON decode error: {json_err}")
        print(f"Response content: {response.text}")
