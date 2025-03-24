import os
from jira import JIRA

jira_user = os.getenv('j_prd_us')
jira_pass = os.getenv('j_prd_ps')
jira_server = os.getenv('j_prd_url')
jira_groups = ['jira-ecommera', 'bitbucket-users', 'confluence-users']

jira = JIRA(basic_auth=(jira_user, jira_pass), options={'server': jira_server})

jira.add_user(username='Pesho.Programista', email='trenirovka@abv.bg', password='P@r0l@t@m1', fullname=' Pesho Programista', notify=True, active=True)

for group in jira_groups:
    jira.add_user_to_group(username='Pesho.Programista', group=group)
