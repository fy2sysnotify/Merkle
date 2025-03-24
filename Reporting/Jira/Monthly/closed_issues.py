from typing import Dict, Tuple, Optional
from decouple import config  # To manage environment variables
from datetime import datetime  # To handle date and time
from dateutil.relativedelta import relativedelta  # To manage date manipulations
import pandas as pd  # For data manipulation and analysis
from jira import JIRA, JIRAError  # For interacting with JIRA API
from projects_config import PROJECT_KEYS  # List of project keys for querying JIRA


class JiraConnection:
    """
    A class to manage the connection to a JIRA server.

    :param server: The base URL of the JIRA server.
    :type server: str
    :param token: The API token for authentication.
    :type token: str
    """

    def __init__(self, server: str, token: str):
        self.server = server  # Store the JIRA server URL
        self.token = token  # Store the API token
        self.jira: Optional[JIRA] = None  # Initialize the JIRA instance as None

    def __enter__(self) -> 'JiraConnection':
        """
        Enter the runtime context related to this object.

        :return: The JiraConnection instance with an active connection.
        :rtype: JiraConnection
        """
        self.jira = self._connect()  # Establish the connection to JIRA
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the runtime context related to this object, closing the JIRA connection if it exists.

        :param exc_type: Exception type if an exception was raised.
        :type exc_type: type
        :param exc_val: Exception value if an exception was raised.
        :type exc_val: BaseException
        :param exc_tb: Traceback object if an exception was raised.
        :type exc_tb: traceback
        """
        if self.jira:  # If there is an active JIRA connection
            self.jira.close()  # Close the JIRA connection

    def _connect(self) -> JIRA:
        """
        Establish a connection to the JIRA server.

        :return: A JIRA instance connected to the server.
        :rtype: JIRA
        :raises JIRAError: If the connection to JIRA fails.
        """
        try:
            # Attempt to create a JIRA instance with the provided server and token
            return JIRA(server=self.server, token_auth=self.token)
        except JIRAError as e:
            # Log an error message if connection fails
            print(f"Failed to connect to JIRA: {e}")
            raise  # Rethrow the exception

    def search_issues(self, jql_query: str, start_at: int, max_results: int) -> list:
        """
        Search for issues in JIRA using a JQL query.

        :param jql_query: The JQL query string.
        :type jql_query: str
        :param start_at: The index of the first issue to return (0-based).
        :type start_at: int
        :param max_results: The maximum number of issues to return.
        :type max_results: int
        :return: A list of JIRA issues that match the query.
        :rtype: list
        :raises JIRAError: If the search query fails.
        """
        try:
            # Perform the search query on JIRA and return the results
            return self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
        except JIRAError as e:
            # Log an error message if the search fails
            print(f"Failed to search issues: {e}")
            raise  # Rethrow the exception


class IssueFetcher:
    """
    A class to fetch issues from JIRA.

    :param jira_connection: An active JiraConnection instance.
    :type jira_connection: JiraConnection
    """

    def __init__(self, jira_connection: JiraConnection):
        self.jira_connection = jira_connection  # Store the JIRA connection instance

    def fetch_issues_for_month(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """
        Fetch issues that were closed within a specified date range.

        :param start_date: The start date of the range.
        :type start_date: datetime
        :param end_date: The end date of the range.
        :type end_date: datetime
        :return: A dictionary with project keys as keys and the count of closed issues as values.
        :rtype: Dict[str, int]
        :raises Exception: If an error occurs while fetching the issues.
        """
        # Format start and end dates to strings
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        project_keys_str = ', '.join(PROJECT_KEYS)  # Join project keys with commas

        # Construct JQL query for fetching issues
        jql_query = (
            f'project in ({project_keys_str}) '
            f'AND issuetype = "Support Request" '
            f'AND status changed to Closed during ("{start_date_str}", "{end_date_str}")'
        )

        print(jql_query)

        start_at = 0  # Initialize the start index for paginated results
        max_results = 1000  # Set the maximum number of results per query
        all_issues = []  # List to store all fetched issues

        try:
            while True:
                # Fetch issues from JIRA using the constructed JQL query
                jira_issues = self.jira_connection.search_issues(jql_query, start_at, max_results)

                # Extend the all_issues list with the fetched issues
                all_issues.extend(jira_issues)

                if len(jira_issues) < max_results:
                    # If the number of issues fetched is less than the maximum, break the loop
                    break

                start_at += max_results  # Increment the start index for the next batch
        except Exception as e:
            # Log an error message if fetching issues fails
            print(f"Error fetching issues: {e}")
            raise  # Rethrow the exception

        # Initialize a dictionary to count issues per project
        issues_count_per_project = {key: 0 for key in PROJECT_KEYS}

        # Count the number of issues for each project
        for issue in all_issues:
            project_key = issue.fields.project.key
            if project_key in issues_count_per_project:
                issues_count_per_project[project_key] += 1

        return issues_count_per_project


class IssueReporter:
    """
    A class to generate and print reports based on JIRA issues.

    :param issue_fetcher: An IssueFetcher instance.
    :type issue_fetcher: IssueFetcher
    """

    def __init__(self, issue_fetcher: IssueFetcher):
        self.issue_fetcher = issue_fetcher  # Store the issue fetcher instance
        self.issues_count_per_month: Dict[str, Dict[str, int]] = {}  # Dictionary to store issue counts per month
        self.monthly_totals: Dict[str, int] = {}  # Dictionary to store total issue counts per month

    def generate_report(self) -> None:
        """
        Generate a report of issues closed each month for the past year.

        :raises Exception: If an error occurs while generating the report.
        """
        # Get the current date and time, and reset to the start of the current month
        today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        try:
            for i in range(12):
                # Calculate the start and end dates for each month in the past year
                start_date = (today - relativedelta(months=i + 1)).replace(day=1)
                end_date = (today - relativedelta(months=i)).replace(day=1) - relativedelta(days=1)

                # Fetch issues for the calculated month
                monthly_issues = self.issue_fetcher.fetch_issues_for_month(start_date, end_date)
                self.issues_count_per_month[start_date.strftime('%Y-%m')] = monthly_issues

                # Calculate the total number of issues for the month
                monthly_total = sum(monthly_issues.values())
                self.monthly_totals[start_date.strftime('%Y-%m')] = monthly_total
        except Exception as e:
            # Log an error message if generating the report fails
            print(f"Error generating report: {e}")
            raise  # Rethrow the exception

    def get_project_issues_df(self) -> Dict[str, pd.DataFrame]:
        """
        Get a dictionary of dataframes, each containing monthly issue counts for a specific project.

        :return: A dictionary with project keys as keys and corresponding dataframes as values.
        :rtype: Dict[str, pd.DataFrame]
        """
        project_dfs = {}
        for project_key in PROJECT_KEYS:
            # Create a dictionary with months as keys and issue counts as values for the project
            data = {month: projects.get(project_key, 0) for month, projects in self.issues_count_per_month.items()}
            # Convert the dictionary to a dataframe
            data_frame = pd.DataFrame.from_dict(data, orient='index', columns=[project_key]).reset_index().rename(
                columns={'index': 'Month'})
            # Store the dataframe in the project_dfs dictionary
            project_dfs[project_key] = data_frame
        return project_dfs

    def get_total_issues_df(self) -> pd.DataFrame:
        """
        Get a dataframe containing the total number of issues closed each month.

        :return: A dataframe with months as rows and total issue counts as values.
        :rtype: pd.DataFrame
        """
        # Convert the monthly_totals dictionary to a dataframe
        return pd.DataFrame.from_dict(self.monthly_totals, orient='index', columns=['Total']).reset_index().rename(
            columns={'index': 'Month'})


def generate_jira_reports() -> Tuple[Optional[Dict[str, pd.DataFrame]], Optional[pd.DataFrame]]:
    """
    Generate JIRA reports for the past year.

    :return: A tuple containing two elements:
        - A dictionary of dataframes for project issues.
        - A dataframe for total issues.
    :rtype: Tuple[Optional[Dict[str, pd.DataFrame]], Optional[pd.DataFrame]]
    """
    jira_server = config('JIRA_BASE_URL')  # Get the JIRA server URL from environment variables
    jira_api_token = config('JIRA_TOKEN')  # Get the JIRA API token from environment variables

    try:
        with JiraConnection(jira_server, jira_api_token) as jira_connection:
            # Create an IssueFetcher instance with the JIRA connection
            issue_fetcher: IssueFetcher = IssueFetcher(jira_connection)
            # Create an IssueReporter instance with the IssueFetcher
            issue_reporter: IssueReporter = IssueReporter(issue_fetcher)

            # Generate the report
            issue_reporter.generate_report()

            # Get dataframes for project issues and total issues
            project_issues_dataframes = issue_reporter.get_project_issues_df()
            total_issues_dataframes = issue_reporter.get_total_issues_df()

            return project_issues_dataframes, total_issues_dataframes
    except Exception as e:
        # Log an error message if generating the reports fails
        print(f"An error occurred while generating JIRA reports: {e}")
        return None, None  # Return None if there is an error
