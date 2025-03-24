from typing import Dict, Tuple, Optional
from jira import JIRA, JIRAError
from decouple import config
from datetime import datetime
from dateutil.relativedelta import relativedelta
from StreamlitApps.Jira.JiraReports.Helper.projects_config import PROJECT_KEYS


class JiraConnection:
    """
    Manages the connection to the JIRA server.

    :param server: The URL of the JIRA server.
    :param token: The API token for authenticating with the JIRA server.
    """

    def __init__(self, server: str, token: str):
        self.server = server
        self.token = token
        self.jira: Optional[JIRA] = None

    def __enter__(self) -> 'JiraConnection':
        """
        Establishes the connection to the JIRA server when entering the context.

        :return: The JiraConnection instance with an active connection.
        """
        self.jira = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Closes the connection to the JIRA server when exiting the context.

        :param exc_type: The exception type, if an exception occurred.
        :param exc_val: The exception value, if an exception occurred.
        :param exc_tb: The traceback, if an exception occurred.
        """
        if self.jira:
            self.jira.close()

    def _connect(self) -> JIRA:
        """
        Establishes a connection to the JIRA server.

        :return: An authenticated JIRA client instance.
        :raises JIRAError: If there is an issue connecting to the JIRA server.
        """
        try:
            return JIRA(server=self.server, token_auth=self.token)
        except JIRAError as e:
            print(f"Failed to connect to JIRA: {e}")
            raise

    def search_issues(self, jql_query: str, start_at: int, max_results: int) -> list:
        """
        Searches for issues in JIRA using the provided JQL query.

        :param jql_query: The JQL query string.
        :param start_at: The index of the first issue to return (for pagination).
        :param max_results: The maximum number of issues to return.
        :return: A list of JIRA issues matching the query.
        :raises JIRAError: If there is an issue executing the search query.
        """
        try:
            return self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
        except JIRAError as e:
            print(f"Failed to search issues: {e}")
            raise


class IssueFetcher:
    """
    Fetches issues from JIRA.

    :param jira_connection: An active JIRA connection.
    """

    def __init__(self, jira_connection: JiraConnection):
        self.jira_connection = jira_connection

    def fetch_issues_for_month(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """
        Fetches issues for a specific month.

        :param start_date: The start date of the month.
        :param end_date: The end date of the month.
        :return: A dictionary with project keys as keys and issue counts as values.
        """
        # Format dates to the format required by JQL (YYYY-MM-DD)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Define JQL query for the specific month and all projects
        project_keys_str = ', '.join(PROJECT_KEYS)
        jql_query = f'project in ({project_keys_str}) AND status changed to Closed during ("{start_date_str}", "{end_date_str}") AND issuetype = "Support Request"'
        print(jql_query)

        # Initialize variables for pagination
        start_at = 0
        max_results = 1000  # Adjust as needed
        all_issues = []

        try:
            while True:
                # Execute the JQL query with pagination
                jira_issues = self.jira_connection.search_issues(jql_query, start_at, max_results)

                # Append fetched issues to the list
                all_issues.extend(jira_issues)

                # Check if we have fetched all issues
                if len(jira_issues) < max_results:
                    break

                # Update the start_at for the next batch
                start_at += max_results
        except Exception as e:
            print(f"Error fetching issues: {e}")
            raise

        # Initialize the count dictionary
        issues_count_per_project = {key: 0 for key in PROJECT_KEYS}

        # Count issues per project
        for issue in all_issues:
            project_key = issue.fields.project.key
            if project_key in issues_count_per_project:
                issues_count_per_project[project_key] += 1

        return issues_count_per_project


class IssueReporter:
    """
    Generates and prints a report of issues fetched from JIRA.

    :param issue_fetcher: An IssueFetcher instance for fetching issues.
    """

    def __init__(self, issue_fetcher: IssueFetcher):
        self.issue_fetcher = issue_fetcher
        self.issues_count_per_month: Dict[str, Dict[str, int]] = {}
        self.monthly_totals: Dict[str, int] = {}

    def generate_report(self) -> None:
        """
        Generates a report of issues for the past 12 months.

        :raises Exception: If there is an error during report generation.
        """
        # Calculate the current date and initialize a nested dictionary to store issues count
        today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        try:
            # Loop through the previous 12 months
            for i in range(12):
                # Define the start and end dates for the current month
                start_date = (today - relativedelta(months=i + 1)).replace(day=1)
                end_date = (today - relativedelta(months=i)).replace(day=1) - relativedelta(days=1)

                # Fetch issues for the current month
                monthly_issues = self.issue_fetcher.fetch_issues_for_month(start_date, end_date)
                self.issues_count_per_month[start_date.strftime('%Y-%m')] = monthly_issues

                # Calculate the total issues for the current month by summing all projects
                monthly_total = sum(monthly_issues.values())
                self.monthly_totals[start_date.strftime('%Y-%m')] = monthly_total
        except Exception as e:
            print(f"Error generating report: {e}")
            raise

    def print_report(self) -> None:
        """
        Prints the generated report.

        :raises Exception: If there is an error during report printing.
        """
        try:
            # Print the issues count per month per project
            for month, projects in self.issues_count_per_month.items():
                print(f'{month}:')
                for project, count in projects.items():
                    print(f'  {project}: {count}')
                # Print the total issues for the current month
                print(f'Total: {self.monthly_totals[month]}')

        except Exception as e:
            print(f"Error printing report: {e}")
            raise


def main() -> Tuple[Optional[Dict[str, Dict[str, int]]], Optional[Dict[str, int]]]:
    """
    Main function to fetch and report JIRA issues.

    :return: A tuple containing the issues count per month and monthly totals, or None in case of an error.
    """
    # Get JIRA instance URL and API token from environment variables
    jira_server = config('JIRA_BASE_URL')
    jira_api_token = config('JIRA_TOKEN')

    try:
        # Use the context manager to manage the JIRA connection
        with JiraConnection(jira_server, jira_api_token) as jira_connection:
            issue_fetcher = IssueFetcher(jira_connection)
            issue_reporter = IssueReporter(issue_fetcher)

            # Generate and print the report
            issue_reporter.generate_report()
            issue_reporter.print_report()

            return issue_reporter.issues_count_per_month, issue_reporter.monthly_totals
    except Exception as e:
        print(f"An error occurred in main: {e}")
        return None, None


if __name__ == "__main__":
    # Run the main function
    issues_count, monthly_totals_result = main()
