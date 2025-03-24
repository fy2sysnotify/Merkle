import os
import pandas as pd
from jira import JIRA

# Connect to Jira
jira = JIRA(basic_auth=(os.getenv('j_prd_us_la'), os.getenv('j_prd_ps_la')),
            options={'server': os.getenv('j_prd_url_la')})

# Specify the project key
project_key = 'JTIP'

# Create an empty dataframe to store the data
df = pd.DataFrame(columns=['Issue Number', 'Issue Type', 'Status'])

start_at = 0
while True:
    # Get all issues for the project
    issues = jira.search_issues('project = {} and status != Done and status != Cancelled'.format(project_key), startAt=start_at, maxResults=50)
    # Break the loop if there are no more issues
    if len(issues) == 0:
        break
    # Iterate through the issues and add the data to the dataframe
    for issue in issues:
        df = df.append({
            'Issue Number': issue.key,
            'Issue Type': issue.fields.issuetype.name,
            'Status': issue.fields.status.name
        }, ignore_index=True)
    start_at += 50

# Write the dataframe to an Excel file
df.to_excel('issues.xlsx', index=False)
