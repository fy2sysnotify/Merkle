import logging
import pandas as pd
from pandas import *
from datetime import datetime
from jira import JIRA
import os

# Get credentials from env/user variables
username = os.environ.get('jiraUser')
password = os.environ.get('jiraPass')
url = os.environ.get('jiraURL')
ods_email = os.environ.get('ODS_MONITORING_EMAIL')
ods_pass = os.environ.get('ODS_MONITORING_PASS')
smtp_server = os.environ.get('ISOBARSMTP')
smtp_port = os.environ.get('ISOBARSMTPPORT')

# Ask for full file name
excel_file = 'JiraFeed.xlsx'
# csv_file = 'Demandware Upgrade 2021.csv'

# Convert Excel or CSV to pandas dataframe
df = pd.read_excel(excel_file)
# df = pd.read_csv(csv_file)
dataframe = pd.DataFrame(df)

# dataframe.to_excel(r'Demandware Upgrade 2021.xlsx', index=False)

for index, row in dataframe.iterrows():
    project_key = row['ProjectKey']
    issue_type = row['Type']
    summary = row['Summary']
    description = row['Description']
    assignee = row['Assignee']
    environment = row['Environment']
    label = row['Label']
    chargeable = row['Chargable']
    epic = row['Epic']
    due_date = row['DueDate']
    jira_note = row['Note']

    jira = JIRA(basic_auth=(username, password), options={'server': url})

    newIssue = {
        'project': project_key,
        'issuetype': issue_type,
        'summary': summary,
        'description': description
        # 'environment': environment
    }

    jira.create_issue(fields=newIssue)
