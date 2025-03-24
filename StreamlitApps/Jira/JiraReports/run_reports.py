import os
import streamlit as st
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from typing import Callable

from decouple import config

# Importing local modules
from aged_jira import (
    JQLQueryBuilder,
    JiraConnector,
    IssueFetcher,
    IssueCounter,
    ExcelSaver,
)
from available_priorities import issue_priorities
from projects_config import PROJECT_KEYS

# Imports for the second functionality
from retailer_perf import (
    JiraClient,
    IssueCounter as ApiIssueCounter,
    DataFrameTransformer,
    ExcelExporter
)

# Imports for the third functionality
from monthly_rating import (
    JiraConnection,
    IssueFetcher as RatingIssueFetcher,
    IssueAggregator,
    IssueReporter,
    DataFrameGenerator,
    save_to_excel
)

# Imports for the fourth functionality
from monthly import (
    IssueDataFetcher,
    DataFrameMerger,
    ExcelReportGenerator,
    ReportGenerator
)

# Set Streamlit page configuration
st.set_page_config(page_title="JIRA Monthly Reporter", layout="wide")

# Set Streamlit page title
st.title("JIRA Monthly Reporter")

# Fetching JIRA credentials from .env file
jira_base_url = config('JIRA_BASE_URL')
jira_api_token = config('JIRA_TOKEN')

# Set the environment variables for JIRA
os.environ['JIRA_BASE_URL'] = jira_base_url
os.environ['JIRA_TOKEN'] = jira_api_token


def run_aged_jira() -> str:
    """
    Generates the Aged JIRA report and saves it as an Excel file.

    Returns:
        str: The filename of the generated Excel report.
    """
    project_keys = PROJECT_KEYS
    jql_query_builder = JQLQueryBuilder(project_keys)
    jql_queries_dict = jql_query_builder.construct_jql_queries()

    # Initialize results dictionary to store issue counts
    results = {
        "case_type_issue": defaultdict(lambda: defaultdict(dict)),
        "case_type_not_issue": defaultdict(lambda: defaultdict(dict)),
        "support_request": defaultdict(lambda: defaultdict(dict))
    }

    with JiraConnector() as jira_connection:
        issue_fetcher = IssueFetcher(jira_connection)
        for query_type, queries in jql_queries_dict.items():
            for current_query_name, query_string in queries.items():
                # Fetch issues using JQL query
                fetched_issues = issue_fetcher.fetch_issues_with_jql(query_string)
                # Count issues by project and priority
                issue_counts = IssueCounter.count_issues_by_project_and_priority(
                    fetched_issues, PROJECT_KEYS, issue_priorities)
                results[query_type][current_query_name] = issue_counts

    # Generate filename for the Excel report
    filename = f'AgedJira_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    # Save issue counts to Excel
    ExcelSaver.save_counts_to_excel(
        filename,
        results,
        PROJECT_KEYS,
        issue_priorities
    )
    return filename


def run_retailer_perf() -> str:
    """
    Generates the Retailer Performance report and saves it as an Excel file.

    Returns:
        str: The filename of the generated Excel report.
    """
    jira_api_url = jira_base_url  # Use the base URL directly as API URL

    try:
        with JiraClient(jira_api_url, jira_api_token) as client:
            # Initialize issue counter
            issue_counter = ApiIssueCounter(client, PROJECT_KEYS)
            # Get issue counts
            issue_counts = issue_counter.get_issue_counts()
            # Fetch detailed issues
            issues = issue_counter.fetch_issues()

        transformer = DataFrameTransformer()
        # Transform issue counts to dataframes
        dataframes = transformer.transform_to_dataframes(issue_counts)
        # Create a specific dataframe for issues
        specific_dataframe = transformer.create_issue_specific_dataframe(issues)

        # Generate filename for the Excel report
        filename = f'RetailerPerf_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        # Export dataframes to Excel
        with ExcelExporter(filename, column_width=20) as exporter:
            exporter.export(dataframes, specific_dataframe)

        return filename
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e


def run_monthly_rating() -> str:
    """
    Generates the Monthly Rating report and saves it as an Excel file.

    Returns:
        str: The filename of the generated Excel report.
    """
    jira_server_url = jira_base_url
    jira_token = jira_api_token

    try:
        with JiraConnection(jira_server_url, jira_token) as jira_conn:
            issue_fetcher = RatingIssueFetcher(jira_conn)
            issue_aggregator = IssueAggregator()
            issue_reporter = IssueReporter(issue_fetcher, issue_aggregator)

            # Generate and print the report
            issue_reporter.generate_report()

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

            # Generate filename for the Excel report
            filename = f'MonthlyRating_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            # Save dataframes to Excel
            save_to_excel(combined_dataframes, total_issues_dataframe, low_rated_issues_dataframe, filename)

            return filename
    except Exception as e:
        print(f"An error occurred while generating JIRA reports: {e}")
        raise e


def run_monthly() -> str:
    """
    Generates the Monthly report and saves it as an Excel file.

    Returns:
        str: The filename of the generated Excel report.
    """
    try:
        data_fetcher = IssueDataFetcher()
        merger = DataFrameMerger()
        # Generate filename for the Excel report
        excel_filename = f'Monthly_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        excel_generator = ExcelReportGenerator(excel_filename)
        report_generator = ReportGenerator(data_fetcher, merger, excel_generator)

        # Generate the report
        report_generator.generate_report()
        return excel_filename
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e


def generate_report_button(report_name: str, generate_report_function: Callable[[], str]) -> None:
    """
    Creates a button to generate a report and display a download link for the report.

    Args:
        report_name (str): The name of the report to generate.
        generate_report_function (Callable[[], str]): The function to call to generate the report.
    """
    col1, col2 = st.columns([1, 3])  # Create two columns with different widths
    with col1:
        if st.button(report_name):  # Display button in the first column
            with st.spinner(f"Generating {report_name}..."):  # Display spinner while generating the report
                try:
                    output_file = generate_report_function()  # Generate the report
                    st.success(f"Report generated: {output_file}")  # Display success message
                    with col2:
                        with open(output_file, "rb") as file:  # Open the generated report file
                            st.download_button(
                                label="Download Excel Report",  # Display download button
                                data=file,
                                file_name=output_file,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                except Exception as ex:
                    st.error(f"An error occurred: {ex}")  # Display error message if report generation fails


# Create buttons for each report type
generate_report_button("Aged Jira Report", run_aged_jira)
generate_report_button("Retailer Performance Report", run_retailer_perf)
generate_report_button("Monthly Rating Report", run_monthly_rating)
generate_report_button("Monthly Report", run_monthly)
