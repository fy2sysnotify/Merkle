from pathlib import Path
from decouple import config  # To manage environment variables
from datetime import datetime  # To handle date and time
from dateutil.relativedelta import relativedelta  # To manage date manipulations
from typing import List, Dict, Tuple, DefaultDict
import collections
import pandas as pd  # For data manipulation and analysis
from jira import JIRA, Issue  # For interacting with JIRA API
from StreamlitApps.Jira.JiraReports.ConfigModules.projects_config import PROJECT_KEYS  # List of project keys for querying JIRA
from StreamlitApps.Jira.JiraReports.ConfigModules.my_logger import configure_logger  # For logging

# Configure the logger using the script name as the logger name
logger = configure_logger(script_name=Path(__file__).stem)


class JiraConnector:
    """
    A context manager for connecting to JIRA.

    Attributes
    ----------
    jira_server : str
        URL of the JIRA server.
    jira_api_token : str
        API token for authentication.
    jira : JIRA
        JIRA connection object.

    Methods
    -------
    connect() -> JIRA
        Connects to the JIRA server.
    """

    def __init__(self):
        """Initialize the JiraConnector with server URL and API token."""
        self.jira_server: str = config('JIRA_BASE_URL')  # Load JIRA server URL from environment variables
        self.jira_api_token: str = config('JIRA_TOKEN')  # Load JIRA API token from environment variables
        self.jira: JIRA = None  # Initialize JIRA connection object as None

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns
        -------
        JiraConnector
            The connected JiraConnector instance.
        """
        self.jira = self.connect()  # Connect to JIRA when entering context
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and close the JIRA connection if it exists."""
        if self.jira:
            self.jira.close()  # Close JIRA connection when exiting context

    def connect(self) -> JIRA:
        """
        Connect to the JIRA server.

        Returns
        -------
        JIRA
            The JIRA connection object.

        Raises
        ------
        Exception
            If the connection to JIRA fails.
        """
        try:
            logger.info("Connecting to JIRA...")  # Log info about connecting to JIRA
            return JIRA(server=self.jira_server, token_auth=self.jira_api_token)  # Return JIRA connection object
        except Exception as exc:
            logger.error(f"Failed to connect to JIRA: {exc}")  # Log error if connection fails
            raise  # Raise exception to be handled by caller


class IssueFetcher:
    """
    A class to fetch issues from JIRA.

    Attributes
    ----------
    jira : JIRA
        JIRA connection object.
    project_keys : Tuple[str, ...]
        Tuple of project keys.

    Methods
    -------
    fetch_all_issues(start_date: datetime, end_date: datetime) -> List[Issue]
        Fetches all issues created within the specified date range.
    """

    def __init__(self, jira: JIRA, project_keys: Tuple[str, ...]):
        """
        Initialize the IssueFetcher with JIRA connection and project keys.

        Parameters
        ----------
        jira : JIRA
            JIRA connection object.
        project_keys : Tuple[str, ...]
            Tuple of project keys.
        """
        self.jira: JIRA = jira  # JIRA connection object
        self.project_keys: Tuple[str, ...] = project_keys  # Tuple of project keys to fetch issues for

    def fetch_all_issues(self, start_date: datetime, end_date: datetime) -> List[Issue]:
        """
        Fetch all issues created within the specified date range.

        Parameters
        ----------
        start_date : datetime
            The start date for fetching issues.
        end_date : datetime
            The end date for fetching issues.

        Returns
        -------
        List[Issue]
            A list of fetched JIRA issues.

        Raises
        ------
        Exception
            If fetching issues from JIRA fails.
        """
        # Create a JQL query to fetch issues from the specified projects and date range
        projects_query: str = ','.join(self.project_keys)
        jql_query: str = (
            f'project IN ({projects_query}) '
            f'AND issuetype = "Support Request" '
            f'AND created >= "{start_date.strftime("%Y-%m-%d")}" '
            f'AND created < "{end_date.strftime("%Y-%m-%d")}"'
        )

        print(jql_query)

        logger.debug(f"JQL Query: {jql_query}")  # Log the JQL query

        start_at: int = 0  # Start fetching from the first issue
        max_results: int = 1000  # Maximum number of results to fetch in one batch
        all_issues: List[Issue] = []  # List to store all fetched issues

        while True:
            try:
                logger.info(f"Fetching issues starting from {start_at}")  # Log info about fetching issues
                jira_issues: List[Issue] = self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
                all_issues.extend(jira_issues)  # Add fetched issues to the list

                if len(jira_issues) < max_results:
                    break  # Exit loop if the number of fetched issues is less than the max_results

                start_at += max_results  # Increment start_at to fetch the next batch of issues
            except Exception as ex:
                logger.exception(f"Failed to fetch issues: {ex}")  # Log exception if fetching fails
                break  # Exit loop if an exception occurs

        logger.info(f"Total issues fetched: {len(all_issues)}")  # Log the total number of fetched issues
        return all_issues  # Return the list of all fetched issues


class IssueProcessor:
    """
    A class to process JIRA issues.

    Attributes
    ----------
    project_keys : Tuple[str, ...]
        Tuple of project keys.

    Methods
    -------
    process_issues(all_issues: List[Issue], today: datetime) -> Tuple[Dict[str, DefaultDict[str, int]], DefaultDict[str, int]]
        Processes issues and aggregates counts per project per month.
    issues_count_to_dataframes(issues_count_per_project_per_month: Dict[str, DefaultDict[str, int]], total_issues_per_month: DefaultDict[str, int]) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]
        Converts issues count to pandas DataFrames.
    """

    def __init__(self, project_keys: Tuple[str, ...]):
        """
        Initialize the IssueProcessor with project keys.

        Parameters
        ----------
        project_keys : Tuple[str, ...]
            Tuple of project keys.
        """
        self.project_keys: Tuple[str, ...] = project_keys  # Tuple of project keys to process issues for

    def process_issues(self, all_issues: List[Issue], today: datetime) -> Tuple[Dict[str,
    DefaultDict[str, int]], DefaultDict[str, int]]:
        """
        Process issues and aggregate counts per project per month.

        Parameters
        ----------
        all_issues : List[Issue]
            List of all JIRA issues.
        today : datetime
            Current date used to calculate monthly statistics.

        Returns
        -------
        Tuple[Dict[str, DefaultDict[str, int]], DefaultDict[str, int]]
            Dictionary of issues count per project per month and total issues per month.

        Raises
        ------
        Exception
            If processing of any issue fails.
        """
        # Initialize dictionaries to store issue counts per project per month and total issue counts per month
        issues_count_per_project_per_month: Dict[str, DefaultDict[str, int]] = {
            project_key: collections.defaultdict(int)
            for project_key in self.project_keys}
        total_issues_per_month: DefaultDict[str, int] = collections.defaultdict(int)

        for issue in all_issues:
            try:
                # Extract project key and created date from the issue
                project_key: str = issue.fields.project.key
                created_date: datetime = datetime.strptime(issue.fields.created, '%Y-%m-%dT%H:%M:%S.%f%z')
                month_str: str = created_date.strftime('%Y-%m')  # Convert created date to 'YYYY-MM' format

                # Increment issue count for the project and month
                if project_key in self.project_keys:
                    issues_count_per_project_per_month[project_key][month_str] += 1
                    total_issues_per_month[month_str] += 1
            except Exception as exc:
                logger.exception(f"Failed to process issue {issue.key}: {exc}")  # Log exception if processing fails

        # Ensure all months within the last 12 months are present in the dictionary
        for project_key in self.project_keys:
            for i in range(12):
                month_str: str = (today - relativedelta(months=i + 1)).strftime('%Y-%m')
                if month_str not in issues_count_per_project_per_month[project_key]:
                    issues_count_per_project_per_month[project_key][month_str] = 0

        logger.info("Issues processed successfully.")  # Log info about successful processing
        return issues_count_per_project_per_month, total_issues_per_month  # Return processed issue counts

    @staticmethod
    def issues_count_to_dataframes(issues_count_per_project_per_month: Dict[str, DefaultDict[str, int]],
                                   total_issues_per_month: DefaultDict[str, int]) -> Tuple[Dict[str, pd.DataFrame],
    pd.DataFrame]:
        """
        Convert issues count to pandas DataFrames.

        Parameters
        ----------
        issues_count_per_project_per_month : Dict[str, DefaultDict[str, int]]
            Dictionary of issues count per project per month.
        total_issues_per_month : DefaultDict[str, int]
            Dictionary of total issues count per month.

        Returns
        -------
        Tuple[Dict[str, pd.DataFrame], pd.DataFrame]
            Tuple containing dictionaries of DataFrames for each project and a DataFrame for total issues.
        """
        dataframes = {}
        # Convert issue counts per project per month to DataFrames
        for project_key, month_counts in issues_count_per_project_per_month.items():
            project_data = [[month, count] for month, count in month_counts.items()]
            project_df = pd.DataFrame(project_data, columns=['Month', 'Count'])
            dataframes[project_key] = project_df

        # Convert total issue counts per month to a DataFrame
        total_data = [[month, count] for month, count in total_issues_per_month.items()]
        total_dataframe = pd.DataFrame(total_data, columns=['Month', 'Total Count'])

        logger.info("Converted issues count to DataFrames.")  # Log info about successful conversion
        return dataframes, total_dataframe  # Return DataFrames


class IssueReport:
    """
    A class to generate issue reports from JIRA data.

    Attributes
    ----------
    project_keys : Tuple[str, ...]
        Tuple of project keys.

    Methods
    -------
    generate_report() -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]
        Generates a report containing issues count DataFrames.
    """

    def __init__(self):
        """Initialize the IssueReport with project keys."""
        self.project_keys: Tuple[str, ...] = PROJECT_KEYS  # Load project keys from configuration

    def generate_report(self) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
        """
        Generate a report containing issues count DataFrames.

        Returns
        -------
        Tuple[Dict[str, pd.DataFrame], pd.DataFrame]
            Tuple containing dictionaries of DataFrames for each project and a DataFrame for total issues.

        Raises
        ------
        Exception
            If report generation fails.
        """
        # Use JiraConnector context manager to manage JIRA connection
        with JiraConnector() as jira_connector:
            try:
                issue_fetcher: IssueFetcher = IssueFetcher(jira_connector.jira,
                                                           self.project_keys)  # Initialize IssueFetcher

                # Define the date range for fetching issues (last 12 months)
                today: datetime = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_date: datetime = today - relativedelta(months=12)
                end_date: datetime = today

                # Fetch all issues within the specified date range
                all_issues: List[Issue] = issue_fetcher.fetch_all_issues(start_date, end_date)

                issue_processor: IssueProcessor = IssueProcessor(self.project_keys)  # Initialize IssueProcessor
                # Process the fetched issues to get counts per project per month and total counts per month
                issues_count_per_project_per_month, total_issues_per_month = issue_processor.process_issues(all_issues,
                                                                                                            today)

                # Convert the processed issue counts to DataFrames
                projects_dataframes, total_dataframe = IssueProcessor.issues_count_to_dataframes(
                    issues_count_per_project_per_month, total_issues_per_month)

                logger.info("Report generated successfully.")  # Log info about successful report generation
                return projects_dataframes, total_dataframe  # Return the generated report DataFrames
            except Exception as exc:
                logger.exception(f"Failed to generate report: {exc}")  # Log exception if report generation fails
                return {}, pd.DataFrame()  # Return empty report on failure
