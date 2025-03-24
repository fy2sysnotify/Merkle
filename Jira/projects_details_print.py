from decouple import config
from jira import JIRA

# Jira server options
jira_options = {'server': config('JIRA_BASE_URL')}
jira = JIRA(options=jira_options, token_auth=config('JIRA_TOKEN'))

# Fetch all projects
projects = jira.projects()

# Iterate through projects and print all attributes
for project in projects:
    print(f"Project: {project.name} ({project.key})")
    for attr in dir(project):
        if not attr.startswith("_") and not callable(getattr(project, attr)):
            print(f"  {attr}: {getattr(project, attr)}")
    print("-" * 40)
