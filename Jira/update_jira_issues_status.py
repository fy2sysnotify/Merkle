import os
import pandas as pd
from jira import JIRA

# Connect to Jira
jira = JIRA(basic_auth=(os.getenv('j_prd_us'), os.getenv('j_prd_ps')),
            options={'server': os.getenv('j_prd_url')})

# Read the Excel file
df = pd.read_excel('transition_issues.xlsx')

# Iterate through the rows of the dataframe
for index, row in df.iterrows():
    # Get the issue number and status
    issue_number = row['Issue Number']
    status = row['Status']
    # Get the issue from Jira
    issue = jira.issue(issue_number)
    # Get the available transitions for the issue
    transitions = jira.transitions(issue)
    # Find the transition that matches the desired status
    transition = next((t for t in transitions if t['to']['name'] == status), None)
    if transition:
        # Perform the transition
        jira.transition_issue(issue, transition['id'])
        print(f"Issue {issue_number} transitioned to {status}")
    else:
        print(f"Transition to {status} not available for issue {issue_number}")

