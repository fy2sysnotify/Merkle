from pathlib import Path
from typing import Dict, Tuple, Optional
from decouple import config  # To handle environment variables securely
from datetime import datetime
from dateutil.relativedelta import relativedelta  # To handle date manipulations easily
import pandas as pd
from jira import JIRA, JIRAError  # JIRA library to interact with JIRA API
from StreamlitApps.Jira.JiraReports.ConfigModules.projects_config import PROJECT_KEYS, \
    PROJECT_NAMES  # Project configurations
from StreamlitApps.Jira.JiraReports.ConfigModules.my_logger import configure_logger  # Custom logger configuration

# Initialize the logger
logger = configure_logger(script_name=Path(__file__).stem)


class JiraConnection:
    """
    Manages a connection to a JIRA server.

    :param server: URL of the JIRA server.
    :type server: str
    :param token: Authentication token for the JIRA server.
    :type token: str
    """

    def __init__(self, server: str, token: str):
        self.server = server
        self.token = token
        self.jira: Optional[JIRA] = None

    def __enter__(self) -> 'JiraConnection':
        """
        Establishes a JIRA connection when entering the context.

        :return: JiraConnection instance.
        :rtype: JiraConnection
        """
        self.jira = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Closes the JIRA connection when exiting the context.
        """
        if self.jira:
            self.jira.close()

    def _connect(self) -> JIRA:
        """
        Connects to the JIRA server using the provided server URL and token.

        :return: JIRA connection object.
        :rtype: JIRA
        :raises JIRAError: If connection to JIRA fails.
        """
        try:
            return JIRA(server=self.server, token_auth=self.token)
        except JIRAError as e:
            # Log the error and raise an exception if connection fails
            logger.error(f"Failed to connect to JIRA: {e}")
            raise

    def search_issues(self, jql_query: str, start_at: int, max_results: int) -> list:
        """
        Searches for JIRA issues using JQL query.

        :param jql_query: JQL query string.
        :type jql_query: str
        :param start_at: The index of the first issue to return.
        :type start_at: int
        :param max_results: Maximum number of issues to return.
        :type max_results: int
        :return: List of JIRA issues.
        :rtype: list
        :raises JIRAError: If the search fails.
        """
        try:
            return self.jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
        except JIRAError as e:
            # Log the error and raise an exception if the search fails
            logger.error(f"Failed to search issues: {e}")
            raise


class IssueFetcher:
    """
    Fetches issues from a JIRA server.

    :param jira_connection: An instance of JiraConnection.
    :type jira_connection: JiraConnection
    """

    def __init__(self, jira_connection: JiraConnection):
        self.jira_connection = jira_connection

    def fetch_issues_for_month(self, start_date: datetime, end_date: datetime) -> (
            Tuple)[Dict[str, Dict[str, Dict[int, int]]], pd.DataFrame]:
        """
        Fetches JIRA issues closed within a specified date range and organizes them by project and rating.

        :param start_date: The start date for fetching issues.
        :type start_date: datetime
        :param end_date: The end date for fetching issues.
        :type end_date: datetime
        :return: A tuple containing the issues data and a DataFrame of low-rated issues.
        :rtype: Tuple[Dict[str, Dict[str, Dict[int, int]]], pd.DataFrame]
        :raises Exception: If an error occurs while fetching issues.
        """
        # Convert dates to strings for the JQL query
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        project_keys_str = ', '.join(PROJECT_KEYS)

        # Formulate the JQL query to fetch issues
        jql_query = (
            f'project in ({project_keys_str}) '
            f'AND issuetype = "Support Request" '
            f'AND status changed to Closed during ("{start_date_str}", "{end_date_str}")'
        )

        print(jql_query)

        logger.info(f"JQL Query: {jql_query}")

        start_at = 0  # Start at the beginning
        max_results = 1000  # Fetch up to 1000 results at a time
        all_issues = []

        try:
            while True:
                # Fetch issues in batches
                jira_issues = self.jira_connection.search_issues(jql_query, start_at, max_results)
                all_issues.extend(jira_issues)

                # Break if there are no more issues to fetch
                if len(jira_issues) < max_results:
                    break

                start_at += max_results  # Move to the next batch
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            raise

        # Initialize a dictionary to store issues data
        issues_data = {key: {'count': 0, 'ratings': {i: 0 for i in range(1, 6)}, 'unrated': 0} for key in PROJECT_KEYS}
        low_rated_issues_data = []  # List to store low-rated issues

        for issue in all_issues:
            project_key = issue.fields.project.key
            if project_key in issues_data:
                issues_data[project_key]['count'] += 1  # Increment the issue count for the project
                customfield_10700_value = getattr(issue.fields, 'customfield_10700', None)
                if customfield_10700_value:
                    # If the custom field has a value, handle it based on its type
                    if isinstance(customfield_10700_value, list):
                        for option in customfield_10700_value:
                            value = option.value if hasattr(option, 'value') else option
                            issues_data[project_key]['ratings'][int(value)] += 1
                    else:
                        value = customfield_10700_value.value if hasattr(customfield_10700_value,
                                                                         'value') else customfield_10700_value
                        issues_data[project_key]['ratings'][int(value)] += 1

                        if int(value) < 4:
                            # Collect low-rated issues
                            low_rated_issues_data.append({
                                'key': issue.key,
                                'summary': issue.fields.summary,
                                'rating': value
                            })
                else:
                    issues_data[project_key]['unrated'] += 1  # Increment the unrated issues count

        low_rated_issues_dataframe = pd.DataFrame(low_rated_issues_data)  # Convert low-rated issues to a DataFrame
        return issues_data, low_rated_issues_dataframe


class IssueAggregator:
    """
    Aggregates issue data across multiple months.
    """

    def __init__(self):
        self.issues_data_per_month: Dict[str, Dict[str, Dict[str, Dict[int, int]]]] = {}  # Data per month
        self.monthly_totals: Dict[str, int] = {}  # Total issues per month
        self.total_ratings_per_month: Dict[str, Dict[int, int]] = {}  # Total ratings per month
        self.total_unrated_per_month: Dict[str, int] = {}  # Total unrated issues per month

    def aggregate_monthly_data(self, month: str, monthly_issues_data: Dict[str, Dict[str, Dict[int, int]]]) -> None:
        """
        Aggregates issues data for a given month.

        :param month: The month for which data is aggregated.
        :type month: str
        :param monthly_issues_data: The issues data for the month.
        :type monthly_issues_data: Dict[str, Dict[str, Dict[int, int]]]
        """
        self.issues_data_per_month[month] = monthly_issues_data

        # Calculate the total number of issues for the month
        monthly_total = sum(project_data['count'] for project_data in monthly_issues_data.values())
        self.monthly_totals[month] = monthly_total

        # Initialize dictionaries to store total ratings and unrated issues
        total_ratings = {i: 0 for i in range(1, 6)}
        total_unrated = 0

        for project_data in monthly_issues_data.values():
            for rating, count in project_data['ratings'].items():
                total_ratings[rating] += count  # Sum up the ratings
            total_unrated += project_data['unrated']  # Sum up the unrated issues

        self.total_ratings_per_month[month] = total_ratings
        self.total_unrated_per_month[month] = total_unrated


class IssueReporter:
    """
    Generates and prints a report of aggregated issues data.

    :param issue_fetcher: An instance of IssueFetcher.
    :type issue_fetcher: IssueFetcher
    :param issue_aggregator: An instance of IssueAggregator.
    :type issue_aggregator: IssueAggregator
    """

    def __init__(self, issue_fetcher: IssueFetcher, issue_aggregator: IssueAggregator):
        self.issue_fetcher = issue_fetcher
        self.issue_aggregator = issue_aggregator

    def generate_report(self) -> None:
        """
        Generates a report for the last 12 months.
        """
        today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        try:
            for i in range(12):
                start_date = (today - relativedelta(months=i + 1)).replace(day=1)
                end_date = (today - relativedelta(months=i)).replace(day=1) - relativedelta(days=1)

                # Fetch issues for each month and aggregate the data
                monthly_issues_data, _ = self.issue_fetcher.fetch_issues_for_month(start_date, end_date)
                self.issue_aggregator.aggregate_monthly_data(start_date.strftime('%Y-%m'), monthly_issues_data)
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def print_report(self) -> None:
        """
        Prints the aggregated report to the logger.
        """
        try:
            for month, projects in self.issue_aggregator.issues_data_per_month.items():
                logger.info(f'{month}:')
                for project_key, data in projects.items():
                    logger.info(f'  {project_key}: {data["count"]}')
                    for rating, count in data['ratings'].items():
                        logger.info(f'    Rating {rating}: {count}')
                    logger.info(f'    Unrated: {data["unrated"]}')
                logger.info(f'Total: {self.issue_aggregator.monthly_totals[month]}')
        except Exception as e:
            logger.error(f"Error printing report: {e}")
            raise


class DataFrameGenerator:
    """
    Generates DataFrames from aggregated issues data.
    """

    @staticmethod
    def get_project_issues_df(issues_data_per_month: Dict[str, Dict[str, Dict[str, Dict[int, int]]]]) -> (
            Dict[str, pd.DataFrame]):
        """
        Generates DataFrames for each project's monthly issues count.

        :param issues_data_per_month: Aggregated issues data per month.
        :type issues_data_per_month: Dict[str, Dict[str, Dict[str, Dict[int, int]]]]
        :return: A dictionary of DataFrames for each project.
        :rtype: Dict[str, pd.DataFrame]
        """
        project_dataframes = {}
        for project_key in PROJECT_KEYS:
            data = {
                month: projects.get(project_key, {}).get('count', 0) for month, projects in
                issues_data_per_month.items()
            }
            data_frame = pd.DataFrame.from_dict(data, orient='index', columns=['Closed']).reset_index().rename(
                columns={'index': 'Month'})
            project_dataframes[project_key] = data_frame
        return project_dataframes

    @staticmethod
    def get_customfield_10700_df(issues_data_per_month: Dict[str, Dict[str, Dict[str, Dict[int, int]]]]) -> (
            Dict[str, pd.DataFrame]):
        """
        Generates DataFrames for each project's custom field ratings.

        :param issues_data_per_month: Aggregated issues data per month.
        :type issues_data_per_month: Dict[str, Dict[str, Dict[str, Dict[int, int]]]]
        :return: A dictionary of DataFrames for each project's custom field ratings.
        :rtype: Dict[str, pd.DataFrame]
        """
        customfield_dataframes = {}
        for project_key in PROJECT_KEYS:
            ratings_data = {month: projects.get(project_key, {}).get('ratings', {}) for month, projects in
                            issues_data_per_month.items()}
            unrated_data = {month: projects.get(project_key, {}).get('unrated', 0) for month, projects in
                            issues_data_per_month.items()}
            formatted_data = {'Month': []}
            for rating in range(1, 6):
                formatted_data[f'Rating {rating}'] = []
            formatted_data['Unrated'] = []
            formatted_data['Average Rating'] = []
            for month, ratings in ratings_data.items():
                formatted_data['Month'].append(month)
                total_ratings = 0
                total_count = 0
                for rating in range(1, 6):
                    count = ratings.get(rating, 0)
                    formatted_data[f'Rating {rating}'].append(count)
                    total_ratings += rating * count
                    total_count += count
                formatted_data['Unrated'].append(unrated_data.get(month, 0))
                average_rating = round(total_ratings / total_count, 2) if total_count > 0 else 0
                formatted_data['Average Rating'].append(average_rating)
            data_frame = pd.DataFrame(formatted_data)
            customfield_dataframes[project_key] = data_frame
        return customfield_dataframes

    @staticmethod
    def get_combined_df(project_dataframes: Dict[str, pd.DataFrame], customfield_dataframes: Dict[str, pd.DataFrame]) -> \
            Dict[str, pd.DataFrame]:
        """
        Combines project issues DataFrames and custom field ratings DataFrames.

        :param project_dataframes: DataFrames for each project's monthly issues count.
        :type project_dataframes: Dict[str, pd.DataFrame]
        :param customfield_dataframes: DataFrames for each project's custom field ratings.
        :type customfield_dataframes: Dict[str, pd.DataFrame]
        :return: A dictionary of combined DataFrames for each project.
        :rtype: Dict[str, pd.DataFrame]
        """
        combined_dataframes = {}
        for project_key in PROJECT_KEYS:
            project_df = project_dataframes.get(project_key)
            customfield_df = customfield_dataframes.get(project_key)
            # Merge the two DataFrames on the 'Month' column
            combined_df = pd.merge(project_df, customfield_df, on='Month', how='left')
            combined_dataframes[project_key] = combined_df
        return combined_dataframes

    @staticmethod
    def get_total_issues_df(monthly_totals: Dict[str, int], total_ratings_per_month: Dict[str, Dict[int, int]],
                            total_unrated_per_month: Dict[str, int]) -> pd.DataFrame:
        """
        Generates a DataFrame for total issues and ratings per month.

        :param monthly_totals: Total issues per month.
        :type monthly_totals: Dict[str, int]
        :param total_ratings_per_month: Total ratings per month.
        :type total_ratings_per_month: Dict[str, Dict[int, int]]
        :param total_unrated_per_month: Total unrated issues per month.
        :type total_unrated_per_month: Dict[str, int]
        :return: DataFrame of total issues and ratings per month.
        :rtype: pd.DataFrame
        """
        total_issues_data = []
        for month, total_count in monthly_totals.items():
            row = {'Month': month, 'Closed': total_count}
            for rating in range(1, 6):
                row[f'Rating {rating}'] = total_ratings_per_month[month].get(rating, 0)
            row['Unrated'] = total_unrated_per_month[month]
            total_ratings_sum = sum(rating * count for rating, count in total_ratings_per_month[month].items())
            total_count_ratings = sum(total_ratings_per_month[month].values())
            row['Average Rating'] = round(total_ratings_sum / total_count_ratings, 2) if total_count_ratings > 0 else 0
            total_issues_data.append(row)
        return pd.DataFrame(total_issues_data)


def generate_jira_reports() -> Tuple[
    Optional[Dict[str, pd.DataFrame]], Optional[pd.DataFrame], Optional[Dict[str, pd.DataFrame]], Optional[
        Dict[str, pd.DataFrame]], Optional[pd.DataFrame]]:
    """
    Generates JIRA reports including project issues, total issues, custom field ratings, and combined DataFrames.

    :return: A tuple containing DataFrames for project issues, total issues, custom field ratings, combined DataFrames, and low-rated issues.
    :rtype: Tuple[Optional[Dict[str, pd.DataFrame]], Optional[pd.DataFrame], Optional[Dict[str, pd.DataFrame]], Optional[Dict[str, pd.DataFrame]], Optional[pd.DataFrame]]
    """
    jira_server_url = config('JIRA_BASE_URL')
    jira_token = config('JIRA_TOKEN')

    try:
        with JiraConnection(jira_server_url, jira_token) as jira_conn:
            # Instantiate issue fetcher and aggregator
            issue_fetcher = IssueFetcher(jira_conn)
            issue_aggregator = IssueAggregator()
            issue_reporter = IssueReporter(issue_fetcher, issue_aggregator)

            # Generate and print the report
            issue_reporter.generate_report()
            issue_reporter.print_report()

            # Generate DataFrames for project issues, total issues, custom field ratings, and combined data
            project_issues_dataframes = DataFrameGenerator.get_project_issues_df(issue_aggregator.issues_data_per_month)
            total_issues_dataframe = DataFrameGenerator.get_total_issues_df(
                issue_aggregator.monthly_totals, issue_aggregator.total_ratings_per_month,
                issue_aggregator.total_unrated_per_month)
            customfield_dataframes = DataFrameGenerator.get_customfield_10700_df(issue_aggregator.issues_data_per_month)
            combined_dataframes = DataFrameGenerator.get_combined_df(project_issues_dataframes, customfield_dataframes)

            # Fetch issues for the previous month to generate a DataFrame of low-rated issues
            _, low_rated_issues_dataframe = issue_fetcher.fetch_issues_for_month(
                (datetime.now() - relativedelta(months=1)).replace(day=1),
                datetime.now().replace(day=1) - relativedelta(days=1)
            )

            return project_issues_dataframes, total_issues_dataframe, customfield_dataframes, combined_dataframes, low_rated_issues_dataframe
    except Exception as e:
        logger.error(f"An error occurred while generating JIRA reports: {e}")
        return None, None, None, None, None


def save_to_excel(combined_dataframes: Dict[str, pd.DataFrame], total_issues_dataframe: pd.DataFrame,
                  low_rated_issues_dataframe: pd.DataFrame, output_file_path: str) -> None:
    """
    Saves generated DataFrames to an Excel file.

    :param combined_dataframes: Combined DataFrames for each project.
    :type combined_dataframes: Dict[str, pd.DataFrame]
    :param total_issues_dataframe: DataFrame of total issues and ratings per month.
    :type total_issues_dataframe: pd.DataFrame
    :param low_rated_issues_dataframe: Pandas DataFrame of low-rated issues.
    :type low_rated_issues_dataframe: pd.DataFrame
    :param output_file_path: The path to save the Excel file.
    :type output_file_path: str
    """
    execution_date = datetime.now().strftime("%Y-%m-%d")

    with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        header_format = workbook.add_format({'bold': True, 'align': 'center'})

        for project_key, df in combined_dataframes.items():
            # Reverse the order of the DataFrame rows. It is done to present months from oldest to newest.
            df = df.iloc[::-1].reset_index(drop=True)
            project_name = PROJECT_NAMES.get(project_key, project_key)
            sheet_name = f'{project_key}_Rating'
            df.to_excel(writer, sheet_name=sheet_name, startrow=2, index=False)

            worksheet = writer.sheets[sheet_name]
            header = f"Jira Monthly Issues Rating ({project_name.upper()}) - Execution Date: {execution_date}"
            worksheet.merge_range('A1:I1', header, header_format)

            # Set column width to 15 for each column in the worksheet
            for col_num, col in enumerate(df.columns):
                worksheet.set_column(col_num, col_num, 15)

        # Reverse the order of the total issues DataFrame rows. It is done to present months from oldest to newest.
        total_issues_dataframe = total_issues_dataframe.iloc[::-1].reset_index(drop=True)

        # Add the header for the total issues dataframe
        total_issues_dataframe.to_excel(writer, sheet_name='Total_Rating', startrow=2, index=False)
        worksheet = writer.sheets['Total_Rating']
        header = f"Jira Monthly Issues Rating (Total) - Execution Date: {execution_date}"
        worksheet.merge_range('A1:I1', header, header_format)

        # Set column width to 15 for each column in the total issues worksheet
        for col_num, col in enumerate(total_issues_dataframe.columns):
            worksheet.set_column(col_num, col_num, 15)

        # Reverse the order of the low rated issues DataFrame rows
        low_rated_issues_dataframe = low_rated_issues_dataframe.iloc[::-1].reset_index(drop=True)

        # Add the header for the low rated issues dataframe
        low_rated_issues_dataframe.to_excel(writer, sheet_name='Low_Rated_Issues', startrow=2, index=False)
        worksheet = writer.sheets['Low_Rated_Issues']
        header = f"Low Rated Issues (Previous Month) - Execution Date: {execution_date}"
        worksheet.merge_range('A1:C1', header, header_format)

        # Set column width to 15 for each column in the low rated issues worksheet
        for col_num, col in enumerate(low_rated_issues_dataframe.columns):
            worksheet.set_column(col_num, col_num, 15)

    logger.info(f"Reports have been saved to {output_file_path}")


def main():
    # Generate JIRA reports
    project_issues_dfs, total_issues_df, customfield_dfs, combined_dfs, low_rated_issues_df = generate_jira_reports()
    if (project_issues_dfs is not None and total_issues_df is not None and customfield_dfs is not None and combined_dfs
            is not None and low_rated_issues_df is not None):
        # Specify the path to save the Excel file
        excel_output_path = f'MonthlyRating_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        save_to_excel(combined_dfs, total_issues_df, low_rated_issues_df, excel_output_path)
        logger.info(f"Reports have been saved to {excel_output_path}")


if __name__ == "__main__":
    main()
