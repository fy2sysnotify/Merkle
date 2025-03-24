from jira import JIRA, Issue
from decouple import config
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Tuple, DefaultDict
import collections
from StreamlitApps.Jira.JiraReports.Helper.projects_config import PROJECT_KEYS


class JiraConnector:
    """
    A class to manage the connection to a JIRA server.

    Attributes
    ----------
    jira_server : str
        The JIRA server URL.
    jira_api_token : str
        The JIRA API token for authentication.
    jira : JIRA
        The JIRA instance used to interact with the JIRA server.
    """

    def __init__(self):
        """
        Initializes the JiraConnector with server URL and API token.
        """
        self.jira_server: str = config('JIRA_BASE_URL')  # Fetch JIRA server URL from environment variables
        self.jira_api_token: str = config('JIRA_TOKEN')  # Fetch JIRA API token from environment variables
        self.jira: JIRA = None

    def __enter__(self):
        self.jira = self.connect()  # Establish connection to JIRA server
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.jira:
            self.jira.close()  # Close the JIRA connection

    def connect(self) -> JIRA:
        """
        Establishes a connection to the JIRA server.

        :return: An authenticated JIRA instance.
        :rtype: JIRA
        """
        try:
            return JIRA(server=self.jira_server, token_auth=self.jira_api_token)  # Create and return JIRA instance
        except Exception as exc:
            print(f"Failed to connect to JIRA: {exc}")
            raise


class IssueFetcher:
    """
    A class to fetch issues from a JIRA server.

    Attributes
    ----------
    jira : JIRA
        The JIRA instance used to fetch issues.
    project_keys : Tuple[str, ...]
        A tuple containing project keys for which to fetch issues.
    """

    def __init__(self, jira: JIRA, project_keys: Tuple[str, ...]):
        """
        Initializes the IssueFetcher with a JIRA instance and project keys.

        :param jira: An authenticated JIRA instance.
        :type jira: JIRA
        :param project_keys: A tuple of project keys.
        :type project_keys: Tuple[str, ...]
        """
        self.jira: JIRA = jira  # Assign JIRA instance to self.jira
        self.project_keys: Tuple[str, ...] = project_keys  # Assign project keys to self.project_keys

    def fetch_all_issues(self, start_date: datetime, end_date: datetime) -> List[Issue]:
        """
        Fetches all issues from the JIRA server within a specified date range.

        :param start_date: The start date for fetching issues.
        :type start_date: datetime
        :param end_date: The end date for fetching issues.
        :type end_date: datetime
        :return: A list of issues fetched from the JIRA server.
        :rtype: List[Issue]
        """
        projects_query: str = ','.join(self.project_keys)  # Join project keys into a single string for JQL query
        jql_query: str = (f'project IN ({projects_query}) AND created >= "{start_date.strftime("%Y-%m-%d")}" '
                          f'AND created < "{end_date.strftime("%Y-%m-%d")}" AND issuetype = "Support Request"')

        # Print the JQL query to be executed
        print(jql_query)

        start_at: int = 0  # Start index for pagination
        max_results: int = 1000  # Maximum number of results to fetch per request
        all_issues: List[Issue] = []  # List to store all fetched issues

        while True:
            try:
                # Fetch issues from JIRA server
                jira_issues: List[Issue] = self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
                all_issues.extend(jira_issues)  # Append fetched issues to the list

                # Break the loop if fewer issues than max_results were fetched, indicating no more issues to fetch
                if len(jira_issues) < max_results:
                    break

                # Update start_at for the next batch of issues
                start_at += max_results
            except Exception as ex:
                print(f"Failed to fetch issues: {ex}")
                break

        return all_issues  # Return the list of all fetched issues


class IssueProcessor:
    """
    A class to process fetched JIRA issues.

    Attributes
    ----------
    project_keys : Tuple[str, ...]
        A tuple containing project keys for which to process issues.
    """

    def __init__(self, project_keys: Tuple[str, ...]):
        """
        Initializes the IssueProcessor with project keys.

        :param project_keys: A tuple of project keys.
        :type project_keys: Tuple[str, ...]
        """
        self.project_keys: Tuple[str, ...] = project_keys  # Assign project keys to self.project_keys

    def process_issues(self, all_issues: List[Issue], today: datetime) -> Tuple[Dict[str, DefaultDict[str, int]],
    DefaultDict[str, int]]:
        """
        Processes the fetched issues to count them per project per month.

        :param all_issues: A list of issues to be processed.
        :type all_issues: List[Issue]
        :param today: The current date.
        :type today: datetime
        :return: A tuple containing:
                 - A dictionary with counts of issues per project per month.
                 - A dictionary with total counts of issues per month.
        :rtype: Tuple[Dict[str, DefaultDict[str, int]], DefaultDict[str, int]]
        """
        # Initialize dictionaries to store issue counts
        issues_count_per_project_per_month: Dict[str, DefaultDict[str, int]] = {project: collections.defaultdict(int)
                                                                                for project in self.project_keys}
        total_issues_per_month: DefaultDict[str, int] = collections.defaultdict(int)

        for issue in all_issues:
            try:
                project_key: str = issue.fields.project.key  # Get project key from issue
                created_date: datetime = datetime.strptime(issue.fields.created,
                                                           '%Y-%m-%dT%H:%M:%S.%f%z')  # Parse issue creation date
                month_str: str = created_date.strftime('%Y-%m')  # Format date as year-month

                if project_key in self.project_keys:
                    issues_count_per_project_per_month[project_key][
                        month_str] += 1  # Increment project-specific issue count
                    total_issues_per_month[month_str] += 1  # Increment total issue count
            except Exception as exc:
                print(f"Failed to process issue {issue.key}: {exc}")

        # Ensure all months in the last year are present in the result
        for project in self.project_keys:
            for i in range(12):
                month_str: str = (today - relativedelta(months=i + 1)).strftime('%Y-%m')
                if month_str not in issues_count_per_project_per_month[project]:
                    issues_count_per_project_per_month[project][
                        month_str] = 0  # Set count to 0 if no issues found for that month

        return issues_count_per_project_per_month, total_issues_per_month  # Return issue counts

    @staticmethod
    def display_issues_count(issues_count_per_project_per_month: Dict[str, DefaultDict[str, int]],
                             total_issues_per_month: DefaultDict[str, int]) -> None:
        """
        Displays the count of issues per project per month and total issues per month.

        :param issues_count_per_project_per_month: A dictionary with counts of issues per project per month.
        :type issues_count_per_project_per_month: Dict[str, DefaultDict[str, int]]
        :param total_issues_per_month: A dictionary with total counts of issues per month.
        :type total_issues_per_month: DefaultDict[str, int]
        """
        # Print issue counts per project per month
        for project, month_counts in issues_count_per_project_per_month.items():
            print(f'Project: {project}')
            for month, count in sorted(month_counts.items()):
                print(f'  {month}: {count}')

        # Print total issue counts per month
        print('Total issues per month:')
        for month, total_count in sorted(total_issues_per_month.items()):
            print(f'  {month}: {total_count}')


class IssueReport:
    """
    A class to generate a report of JIRA issues.

    Attributes
    ----------
    project_keys : Tuple[str, ...]
        A tuple containing project keys for which to generate the report.
    """

    def __init__(self):
        """
        Initializes the IssueReport with project keys.
        """
        self.project_keys: Tuple[str, ...] = PROJECT_KEYS  # Assign project keys to self.project_keys

    def generate_report(self) -> Tuple[Dict[str, DefaultDict[str, int]], DefaultDict[str, int]]:
        """
        Generates a report of JIRA issues, displaying the count per project per month and total issues per month.

        :return: A tuple containing:
                 - A dictionary with counts of issues per project per month.
                 - A dictionary with total counts of issues per month.
        :rtype: Tuple[Dict[str, DefaultDict[str, int]], DefaultDict[str, int]]
        """
        with JiraConnector() as jira_connector:  # Create JiraConnector instance
            try:
                issue_fetcher: IssueFetcher = IssueFetcher(jira_connector.jira,
                                                           self.project_keys)  # Create IssueFetcher instance

                today: datetime = datetime.now().replace(day=1, hour=0, minute=0, second=0,
                                                         microsecond=0)  # Get current date set to the start of the month
                start_date: datetime = today - relativedelta(months=12)  # Calculate start date (12 months ago)
                end_date: datetime = today  # End date is the current date

                all_issues: List[Issue] = issue_fetcher.fetch_all_issues(start_date,
                                                                         end_date)  # Fetch all issues within the date range

                issue_processor: IssueProcessor = IssueProcessor(self.project_keys)  # Create IssueProcessor instance
                issues_count_per_project_per_month, total_issues_per_month = issue_processor.process_issues(all_issues,
                                                                                                            today)  # Process fetched issues

                IssueProcessor.display_issues_count(issues_count_per_project_per_month,
                                                    total_issues_per_month)  # Display issue counts

                return issues_count_per_project_per_month, total_issues_per_month  # Return issue counts
            except Exception as exc:
                print(f"Failed to generate report: {exc}")
                return {}, collections.defaultdict(int)


if __name__ == "__main__":
    try:
        created_issue_report: IssueReport = IssueReport()  # Create IssueReport instance
        created_issues_count_per_project, created_total_issues_per_month_overall = created_issue_report.generate_report()  # Generate and display issue report
    except Exception as e:
        print(f"Failed to execute main program: {e}")
