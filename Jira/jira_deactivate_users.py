import os
from jira import JIRA

jira_user = os.getenv('j_prd_us')
jira_pass = os.getenv('j_prd_ps')
jira_server = 'https://jira.isobarsystems.com'
jira_groups = ['jira-ecommera', 'bitbucket-users', 'confluence-users']


jira = JIRA(basic_auth=(jira_user, jira_pass), options={'server': jira_server})

jira.deactivate_user('Pesho.Programista')
