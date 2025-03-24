import os
import logging
import requests
import typing


class JiraClient:
    def __init__(self, url: str, username: str, password: str):
        """
        Initialize a JiraClient instance.

        :param: url (str): URL of the Jira instance
        :param: username (str): username for authenticating with the Jira instance
        :param: password (str): password for authenticating with the Jira instance
        """
        self.url = url
        self.auth = (username, password)

    def __enter__(self) -> 'JiraClient':
        """
        Enter a context for the JiraClient instance.
        This will create a new session and authenticate it with the Jira instance.

        :return: "JiraClient"
        """
        self.session = requests.Session()
        self.session.auth = self.auth
        return self

    def __exit__(self, *args):
        """
        Exit a context for the JiraClient instance. This will close the session.

        :param: args: exception information if an exception occurred in the context,
                    or None if no exception occurred
        :return: None
        """
        self.session.close()

    def get_issues(self, project_key: str) -> typing.List[dict]:
        """
        Get a list of issues for the specified project.

        :param: project_key (str): key of the project to get the issues for
        :return: (List[dict]): list of issues for the project
        """
        response = self.session.get(f"{self.url}/rest/api/2/search?jql=project={project_key}")
        response.raise_for_status()
        return response.json()["issues"]

    def create_issue(self, data: dict) -> dict:
        """
        Create a new issue in the Jira instance.

        :param: data(dict): Data for the issue to be created
        :return (dict): created issue
        """
        response = self.session.post(f"{self.url}/rest/api/2/issue", json=data)
        response.raise_for_status()
        return response.json()


def transfer_issues(
        source_url: str,
        source_username: str,
        source_password: str,
        target_url: str,
        target_username: str,
        target_password: str,
        project_key: str,
) -> None:
    """
    Transfer all issues from one Jira instance to another.

    :param: source_url (str): URL of the source Jira instance
    :param: source_username (str): username for authenticating with the source Jira instance
    :param: source_password (str): password for authenticating with the source Jira instance
    :param: target_url (str): URL of the target Jira instance
    :param: target_username (str): username for authenticating with the target Jira instance
    :param: target_password (str): password for authenticating with the target Jira instance
    :param: project_key (str): key of the project to transfer the issues for
    :return: None
    """
    source_client = JiraClient(source_url, source_username, source_password)
    target_client = JiraClient(target_url, target_username, target_password)

    issues = source_client.get_issues(project_key)

    for issue in issues:
        data = {
            "fields": {
                "project": {"key": project_key},
                "issuetype": {"name": issue["fields"]["issuetype"]["name"]},
                "summary": issue["fields"]["summary"],
                "description": issue["fields"]["description"],
                "reporter": {"name": issue["fields"]["reporter"]["name"]},
                "assignee": {"name": issue["fields"]["assignee"]["name"]},
                "priority": {"name": issue["fields"]["priority"]["name"]},
            }
        }

        try:
            target_client.create_issue(data)
            print(f"Created issue {issue['key']}")
            logging.info(f"Created issue {issue['key']}")
        except Exception as e:
            print(f"Error creating issue {issue['key']}: {e}")
            logging.error(f"Error creating issue {issue['key']}: {e}")


def main() -> None:
    """
    Transfer all issues from the source Jira instance to the target Jira instance.

    :return: None
    """
    transfer_issues(
        os.getenv("source_jira_url"),
        os.getenv("source_jira_user"),
        os.getenv("source_jira_pass"),
        os.getenv("target_jira_url"),
        os.getenv("target_jira_user"),
        os.getenv("target_jira_pass"),
        "PRETM",
    )


if __name__ == "__main__":
    main()
