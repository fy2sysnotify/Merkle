from jira import JIRA, JIRAError
from decouple import config  # For configuration management
from datetime import datetime
from dateutil.relativedelta import relativedelta  # For date manipulation
from collections import defaultdict  # For creating dictionaries with default values
from typing import Generator, List, Dict, Optional, Any
from StreamlitApps.Jira.JiraReports.Helper.projects_config import PROJECT_KEYS  # Importing project keys from a config file
from contextlib import contextmanager  # For creating context managers


@contextmanager
def jira_connection(server_url: str, api_token: str) -> Generator[Optional[JIRA], None, None]:
    """
    Context manager for establishing a JIRA connection.

    :param server_url: URL of the JIRA server.
    :type server_url: str
    :param api_token: API token for authenticating with JIRA.
    :type api_token: str
    :yield: A JIRA instance or None if connection fails.
    :rtype: Generator[Optional[JIRA], None, None]
    """
    jira = None
    try:
        jira = JIRA(server=server_url, token_auth=api_token)  # Establish JIRA connection
        yield jira  # Provide the JIRA connection to the caller
    except JIRAError as ex:
        print(f"Failed to connect to JIRA: {ex}")  # Log connection error
        yield None  # Yield None in case of failure
    finally:
        if jira:
            jira.close()  # Ensure the JIRA connection is closed


class JiraClient:
    """
    A client for interacting with the JIRA API.
    """

    def __init__(self, jira: JIRA):
        """
        Initialize the JiraClient.

        :param jira: An authenticated JIRA instance.
        :type jira: JIRA
        """
        self.jira = jira  # Store the JIRA instance

    def fetch_issues_for_year(self, start_date: str, end_date: str, project_keys: List[str]) -> List[Any]:
        """
        Fetch issues from JIRA for a given date range and project keys.

        :param start_date: The start date for fetching issues (inclusive).
        :type start_date: str
        :param end_date: The end date for fetching issues (exclusive).
        :type end_date: str
        :param project_keys: List of project keys to fetch issues for.
        :type project_keys: List[str]
        :return: A list of issues fetched from JIRA.
        :rtype: List[Any]
        """
        # Create JQL query string
        project_keys_query = ','.join(f'"{key}"' for key in project_keys)
        jql_query = f'project IN ({project_keys_query}) AND resolved >= "{start_date}" AND resolved < "{end_date}" AND issuetype = "Support Request"'
        print(jql_query)

        start_at = 0
        max_results = 1000
        all_issues = []

        # Fetch issues in batches (pagination)
        while True:
            try:
                # Fetch a batch of issues
                jira_issues = self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
                all_issues.extend(jira_issues)

                # Break loop if no more issues are found
                if len(jira_issues) < max_results:
                    break

                start_at += max_results  # Move to the next batch
            except JIRAError as ex:
                print(f"Error fetching issues from JIRA: {ex}")  # Log fetching error
                break

        return all_issues


class IssueReporter:
    """
    A reporter for processing and displaying issues.
    """

    def __init__(self, project_keys: List[str]):
        """
        Initialize the IssueReporter.

        :param project_keys: List of project keys to report issues for.
        :type project_keys: List[str]
        """
        self.project_keys = project_keys
        # Dictionaries to hold issue counts
        self.issues_count_per_project_per_month: Dict[str, Dict[str, int]] = {project: defaultdict(int) for project in
                                                                              project_keys}
        self.total_count_per_month: Dict[str, int] = defaultdict(int)
        self.total_count_per_project: Dict[str, int] = {project: 0 for project in project_keys}
        self.overall_total_count: int = 0

    @staticmethod
    def populate_months() -> List[str]:
        """
        Populate the list of months for the past year, excluding the current month.

        :return: A list of month strings in 'YYYY-MM' format for the past year.
        :rtype: List[str]
        """
        today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Generate list of past 12 months excluding the current month
        return [(today - relativedelta(months=i)).strftime('%Y-%m') for i in range(1, 13)]

    def process_issues(self, issues: List[Any]) -> None:
        """
        Process issues and calculate counts per project and month.

        :param issues: A list of issues to process.
        :type issues: List[Any]
        """
        all_months = self.populate_months()  # Get all months in the past year

        for issue in issues:
            try:
                # Extract project key and resolution month
                project_key = issue.fields.project.key
                resolution_month = issue.fields.resolutiondate[:7]
                if project_key in self.project_keys:
                    # Increment counters
                    self.issues_count_per_project_per_month[project_key][resolution_month] += 1
                    self.total_count_per_month[resolution_month] += 1
                    self.total_count_per_project[project_key] += 1
                    self.overall_total_count += 1
            except AttributeError as ex:
                print(f"Error processing issue: {ex}")

        # Ensure all months have entries, set to 0 if no issues
        for project in self.project_keys:
            for month in all_months:
                if month not in self.issues_count_per_project_per_month[project]:
                    self.issues_count_per_project_per_month[project][month] = 0

        # Ensure total counts for each month, set to 0 if no issues
        for month in all_months:
            if month not in self.total_count_per_month:
                self.total_count_per_month[month] = 0

    def display_report(self) -> None:
        """
        Display the report of issues per project and month.
        """
        for project, monthly_counts in self.issues_count_per_project_per_month.items():
            print(f'Project: {project}')
            for month, count in sorted(monthly_counts.items()):
                print(f'  {month}: {count}')
            print(f'  Total for project {project}: {self.total_count_per_project[project]}')

        print("\nTotal issues per month:")
        for month, count in sorted(self.total_count_per_month.items()):
            print(f'{month}: {count}')

        print(f'\nOverall total issues count: {self.overall_total_count}')


class JiraIssueFetcher:
    """
    A class to fetch and report JIRA issues.
    """

    def __init__(self):
        """
        Initialize the JiraIssueFetcher.
        """
        self.jira_server: str = config('JIRA_BASE_URL')  # Get JIRA server URL from config
        self.jira_api_token: str = config('JIRA_TOKEN')  # Get JIRA API token from config
        self.issue_reporter: IssueReporter = IssueReporter(PROJECT_KEYS)  # Initialize IssueReporter

    def fetch_and_report_issues(self) -> None:
        """
        Fetch and report JIRA issues for the past year, excluding the current month.
        """
        with jira_connection(self.jira_server, self.jira_api_token) as jira:
            if jira is None:
                print("Skipping issue fetching due to JIRA connection failure.")
                return

            jira_client = JiraClient(jira)

            today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_date = (today - relativedelta(months=12)).strftime('%Y-%m-%d')
            end_date = (today - relativedelta(months=0)).strftime(
                '%Y-%m-%d')  # Adjusted end_date to the start of the current month

            try:
                # Fetch and process issues
                issues = jira_client.fetch_issues_for_year(start_date, end_date, PROJECT_KEYS)
                self.issue_reporter.process_issues(issues)
                self.issue_reporter.display_report()
            except Exception as ex:
                print(f"An error occurred while fetching and reporting issues: {ex}")


if __name__ == "__main__":
    try:
        issue_fetcher = JiraIssueFetcher()
        issue_fetcher.fetch_and_report_issues()
    except Exception as e:
        print(f"An error occurred in the main execution: {e}")
