from pathlib import Path
from datetime import datetime  # To handle date and time
from dateutil.relativedelta import relativedelta  # To manage date manipulations
from collections import defaultdict
from typing import Generator, List, Dict, Optional, Any
from decouple import config  # To manage environment variables
from contextlib import contextmanager
import pandas as pd  # For data manipulation and analysis
from jira import JIRA, JIRAError  # For interacting with JIRA API
from StreamlitApps.Jira.JiraReports.ConfigModules.projects_config import PROJECT_KEYS  # List of project keys for querying JIRA
from StreamlitApps.Jira.JiraReports.ConfigModules.my_logger import configure_logger  # For logging

# Configure the logger using the script name as the logger name
logger = configure_logger(script_name=Path(__file__).stem)


@contextmanager
def jira_connection(server_url: str, api_token: str) -> Generator[Optional[JIRA], None, None]:
    """
    Context manager for establishing a connection to JIRA.

    :param server_url: The URL of the JIRA server.
    :type server_url: str
    :param api_token: The API token for authentication.
    :type api_token: str
    :yield: An instance of the JIRA client or None if connection fails.
    :rtype: Generator[Optional[JIRA], None, None]

    :raises JIRAError: If the connection to JIRA fails.
    """
    jira = None
    try:
        # Attempt to connect to JIRA with the provided server URL and API token
        jira = JIRA(server=server_url, token_auth=api_token)
        yield jira
    except JIRAError as ex:
        # Log an error message if the connection fails
        logger.error(f"Failed to connect to JIRA: {ex}")
        yield None
    finally:
        # Ensure the JIRA connection is properly closed
        if jira:
            jira.close()


class JiraClient:
    """
    A client for fetching issues from JIRA.

    :param jira: An instance of the JIRA client.
    :type jira: JIRA
    """

    def __init__(self, jira: JIRA):
        self.jira = jira

    def fetch_issues_for_year(self, start_date: str, end_date: str, project_keys: List[str]) -> List[Any]:
        """
        Fetches issues from JIRA for a given year and list of project keys.

        :param start_date: The start date for fetching issues (format: 'YYYY-MM-DD').
        :type start_date: str
        :param end_date: The end date for fetching issues (format: 'YYYY-MM-DD').
        :type end_date: str
        :param project_keys: A list of project keys to filter the issues.
        :type project_keys: List[str]
        :return: A list of JIRA issues.
        :rtype: List[Any]

        :raises JIRAError: If fetching issues from JIRA fails.
        """
        # Join the project keys into a single string for the JQL query
        project_keys_query = ','.join(f'{key}' for key in project_keys)
        # Define the JQL query to fetch issues resolved within the specified date range
        jql_query = (
            f'project IN ({project_keys_query}) '
            f'AND issuetype = "Support Request" '
            f'AND resolved >= "{start_date}" '
            f'AND resolved < "{end_date}"'
        )

        print(jql_query)

        # Log the JQL query for debugging purposes
        logger.debug(f"JQL Query: {jql_query}")

        start_at = 0  # Start at the first result
        max_results = 1000  # Maximum number of results to fetch per batch
        all_issues = []  # Initialize a list to hold all fetched issues

        while True:
            try:
                # Fetch a batch of issues using the JQL query
                jira_issues = self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
                all_issues.extend(jira_issues)  # Add the fetched issues to the list

                # Break the loop if fewer issues than the maximum batch size were fetched
                if len(jira_issues) < max_results:
                    break

                # Update the start index for the next batch
                start_at += max_results
            except JIRAError as ex:
                # Log an error message if fetching issues fails
                logger.error(f"Error fetching issues from JIRA: {ex}")
                break

        return all_issues


class IssueReporter:
    """
    A class for processing and reporting JIRA issues.

    :param project_keys: A list of project keys to process.
    :type project_keys: List[str]
    """

    def __init__(self, project_keys: List[str]):
        self.project_keys = project_keys
        # Initialize dictionaries to count issues per project per month
        self.issues_count_per_project_per_month: Dict[str, Dict[str, int]] = {
            project: defaultdict(int) for project in project_keys
        }
        self.total_count_per_month: Dict[str, int] = defaultdict(int)  # Initialize dictionary to count issues per month
        self.total_count_per_project: Dict[str, int] = {project: 0 for project in
                                                        project_keys}  # Count issues per project
        self.overall_total_count: int = 0  # Overall total count of issues

    @staticmethod
    def populate_months() -> List[str]:
        """
        Populates a list of the last 12 months in 'YYYY-MM' format.

        :return: A list of the last 12 months.
        :rtype: List[str]
        """
        today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return [(today - relativedelta(months=i)).strftime('%Y-%m') for i in range(1, 13)]

    def process_issues(self, issues: List[Any]) -> None:
        """
        Processes a list of JIRA issues to count them per project per month.

        :param issues: A list of JIRA issues.
        :type issues: List[Any]
        """
        all_months = self.populate_months()  # Get the last 12 months

        for issue in issues:
            try:
                project_key = issue.fields.project.key  # Get the project key from the issue
                resolution_month = issue.fields.resolutiondate[:7]  # Get the resolution month (YYYY-MM)
                if project_key in self.project_keys:
                    # Update issue counts in the respective dictionaries
                    self.issues_count_per_project_per_month[project_key][resolution_month] += 1
                    self.total_count_per_month[resolution_month] += 1
                    self.total_count_per_project[project_key] += 1
                    self.overall_total_count += 1
            except AttributeError as ex:
                # Log a warning if there is an issue processing an individual JIRA issue
                logger.warning(f"Error processing issue: {ex}")

        # Ensure every month is present in the counts dictionaries
        for project in self.project_keys:
            for month in all_months:
                if month not in self.issues_count_per_project_per_month[project]:
                    self.issues_count_per_project_per_month[project][month] = 0

        for month in all_months:
            if month not in self.total_count_per_month:
                self.total_count_per_month[month] = 0

    def get_issues_count_dfs_per_project(self) -> Dict[str, pd.DataFrame]:
        """
        Returns dataframes of issue counts per project per month.

        :return: A dictionary where keys are project keys and values are dataframes.
        :rtype: Dict[str, pd.DataFrame]
        """
        project_dfs = {}
        for project, monthly_counts in self.issues_count_per_project_per_month.items():
            # Prepare data for each project
            data = [{'Month': month, 'Count': count} for month, count in sorted(monthly_counts.items())]
            # Create a dataframe from the data
            project_dfs[project] = pd.DataFrame(data)
        return project_dfs

    def get_total_count_per_month_df(self) -> pd.DataFrame:
        """
        Returns a dataframe of total issue counts per month.

        :return: A dataframe of total issue counts per month.
        :rtype: pd.DataFrame
        """
        data = [{'Month': month, 'Total Count': count} for month, count in sorted(self.total_count_per_month.items())]
        # Create a dataframe from the data
        return pd.DataFrame(data)

    def get_total_count_per_project_df(self) -> pd.DataFrame:
        """
        Returns a dataframe of total issue counts per project.

        :return: A dataframe of total issue counts per project.
        :rtype: pd.DataFrame
        """
        data = [{'Project': project, 'Total Count': count} for project, count in self.total_count_per_project.items()]
        # Create a dataframe from the data
        return pd.DataFrame(data)

    def get_overall_total_count(self) -> int:
        """
        Returns the overall total issue count.

        :return: The overall total issue count.
        :rtype: int
        """
        return self.overall_total_count


class JiraIssueFetcher:
    """
    A class for fetching and reporting JIRA issues.

    This class manages the connection to JIRA, fetches issues, and reports them
    using an instance of the IssueReporter class.
    """

    def __init__(self):
        self.jira_server: str = config('JIRA_BASE_URL')  # JIRA server URL from environment variables
        self.jira_api_token: str = config('JIRA_TOKEN')  # JIRA API token from environment variables
        self.issue_reporter: IssueReporter = IssueReporter(PROJECT_KEYS)  # Initialize the IssueReporter

    def fetch_and_report_issues(self) -> Dict[str, Any]:
        """
        Fetches issues from JIRA and generates reports.

        :return: A dictionary containing dataframes of issue counts per project,
                 total counts per month, total counts per project, and overall total count.
        :rtype: Dict[str, Any]
        """
        with jira_connection(self.jira_server, self.jira_api_token) as jira:
            if jira is None:
                # Log an error message if the JIRA connection fails
                logger.error("Skipping issue fetching due to JIRA connection failure.")
                return {}

            jira_client: JiraClient = JiraClient(jira)  # Initialize the JiraClient

            today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_date = (today - relativedelta(months=12)).strftime(
                '%Y-%m-%d')  # Calculate the start date (12 months ago)
            end_date = (today - relativedelta(months=0)).strftime('%Y-%m-%d')  # Calculate the end date (today)

            try:
                # Fetch issues from JIRA within the specified date range
                issues = jira_client.fetch_issues_for_year(start_date, end_date, PROJECT_KEYS)
                # Process the fetched issues
                self.issue_reporter.process_issues(issues)

                # Generate dataframes for the report
                resolved_issues_count_dfs_per_project = self.issue_reporter.get_issues_count_dfs_per_project()
                resolved_total_count_per_month_df = self.issue_reporter.get_total_count_per_month_df()
                resolved_total_count_per_project_df = self.issue_reporter.get_total_count_per_project_df()
                resolved_overall_total_count = self.issue_reporter.get_overall_total_count()

                # Compile the results into a dictionary
                result = {
                    "projects": resolved_issues_count_dfs_per_project,
                    "total_count_per_month": resolved_total_count_per_month_df,
                    "total_count_per_project": resolved_total_count_per_project_df,
                    "overall_total_count": resolved_overall_total_count
                }

                # Log an info message indicating successful completion
                logger.info("Issue fetching and reporting completed successfully.")
                return result

            except Exception as ex:
                # Log an error message if an exception occurs
                logger.error(f"An error occurred while fetching and reporting issues: {ex}")
                return {}
