import os
from jira import JIRA


jira_user = os.getenv('j_prd_us')
jira_pass = os.getenv('j_prd_ps')

jira = JIRA(basic_auth=(jira_user, jira_pass), options={'server': 'https://jira.isobarsystems.com/'})

for issue in jira.search_issues(
        'participants = currentUser() AND status != resolved AND status != closed order by created DESC'):
    print(
        f'You are participant in:\nIssue: {issue.key}\nSummary: {issue.fields.summary}\nAssignee: '
        f'{issue.fields.assignee}\nReporter: {issue.fields.reporter}\nCreate Date: {issue.fields.created}')
for issue in jira.search_issues(
        'assignee = currentUser() AND status != resolved AND status != closed order by created DESC'):
    print(
        f'You are assignee in:\nIssue: {issue.key}\nSummary: {issue.fields.summary}\nAssignee: '
        f'{issue.fields.assignee}\nReporter: {issue.fields.reporter}\nCreate Date: {issue.fields.created}')
for issue in jira.search_issues(
        'reporter = currentUser() AND status != resolved AND status != closed order by created DESC'):
    print(
        f'You are reporter in:\nIssue: {issue.key}\nSummary: {issue.fields.summary}\nAssignee: '
        f'{issue.fields.assignee}\nReporter: {issue.fields.reporter}\nCreate Date: {issue.fields.created}')
