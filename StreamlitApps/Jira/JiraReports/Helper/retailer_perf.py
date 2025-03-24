from pathlib import Path
import requests
from decouple import config
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from projects_config import PROJECT_KEYS, PROJECT_NAMES
from available_priorities import issue_priorities
from fields_mapping import customfield_10200
from my_logger import configure_logger

# Configure the logger
logger = configure_logger(script_name=Path(__file__).stem)


class ApiClient:
    """
    API Client for handling HTTP requests.

    :param base_url: The base URL for the API.
    :type base_url: str
    :param api_token: The API token for authentication.
    :type api_token: str
    """

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url
        self.api_token = api_token
        self.session = None  # Session will be initialized in the context manager
        logger.info(f"ApiClient initialized with base_url: {base_url}")

    def __enter__(self) -> 'ApiClient':
        """
        Enter the runtime context related to this object.

        :return: The API client instance with an open session.
        :rtype: ApiClient
        """
        self.session = requests.Session()
        # Set headers for the session
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        })
        logger.info("Session started for ApiClient")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the runtime context related to this object.

        Closes the session when exiting the context.

        :param exc_type: The exception type.
        :type exc_type: type
        :param exc_val: The exception value.
        :type exc_val: Exception
        :param exc_tb: The traceback object.
        :type exc_tb: TracebackType
        """
        if self.session:
            self.session.close()  # Ensure the session is closed to free up resources
            logger.info("Session closed for ApiClient")

    def perform_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform an HTTP GET request.

        :param endpoint: The API endpoint to call.
        :type endpoint: str
        :param params: The query parameters for the request.
        :type params: Dict[str, Any]
        :return: The JSON response from the API.
        :rtype: Dict[str, Any]
        :raises Exception: If the request fails.
        """
        try:
            # Make the GET request to the API endpoint
            response = self.session.get(self.base_url + endpoint, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.info(f"Request to {endpoint} successful with params: {params}")
            return response.json()  # Return the response JSON
        except requests.RequestException as e:
            # Handle any request exceptions
            logger.error(f"Failed to fetch data from JIRA: {e}")
            raise Exception(f"Failed to fetch data from JIRA: {e}")


class JiraClient(ApiClient):
    """
    JIRA Client for fetching issues from a JIRA instance.

    Inherits from ApiClient.
    """

    def fetch_issues(self, jql_query: str, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch issues from JIRA using a JQL query.

        :param jql_query: The JQL query string.
        :type jql_query: str
        :param max_results: The maximum number of results to return, defaults to 1000.
        :type max_results: int, optional
        :return: A list of issues from JIRA.
        :rtype: List[Dict[str, Any]]
        """
        params = {
            "jql": jql_query,  # Set the JQL query parameter
            "maxResults": max_results  # Limit the number of results
        }
        logger.debug(f"Fetching issues with JQL: {jql_query}")
        return self.perform_request("/rest/api/2/search", params).get('issues', [])


class IssueCounter:
    """
    Class for counting issues in JIRA per project.

    :param jira_client: An instance of JiraClient to fetch issues.
    :type jira_client: JiraClient
    :param project_keys: A list of project keys to count issues for.
    :type project_keys: List[str]
    """

    def __init__(self, jira_client: JiraClient, project_keys: List[str]) -> None:
        self.jira_client = jira_client
        self.project_keys = project_keys
        logger.info(f"IssueCounter initialized with projects: {project_keys}")

    def get_jql_query(self) -> str:
        """
        Generate the JQL query string for fetching issues.

        :return: The JQL query string.
        :rtype: str
        """
        projects_query = ','.join(self.project_keys)  # Join project keys into a comma-separated string
        jql_query = (
            f'project IN ({projects_query}) '
            f'AND issuetype = "Support Request" '
            f'AND created >= startOfMonth(-1) '
            f'AND created <= endOfMonth(-1)'
        )
        logger.debug(f"Generated JQL query: {jql_query}")
        print(f"Generated JQL query: {jql_query}")
        return jql_query

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch issues from JIRA based on the JQL query.

        :return: A list of issues from JIRA.
        :rtype: List[Dict[str, Any]]
        """
        jql_query = self.get_jql_query()  # Generate the JQL query
        logger.debug(f"Fetching issues with query: {jql_query}")
        return self.jira_client.fetch_issues(jql_query)

    def count_issues_per_project(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Count issues per project, categorized by priority and custom fields.

        :param issues: A list of issues fetched from JIRA.
        :type issues: List[Dict[str, Any]]
        :return: A dictionary with issue counts per project.
        :rtype: Dict[str, Any]
        """
        logger.info("Counting issues per project")
        # Initialize the issue count structure
        issue_count = {
            project: {
                "total": 0,
                "priority": {priority: 0 for priority in issue_priorities},
                "customfield": {value: {"total": 0, "priority": {priority: 0 for priority in issue_priorities}} for
                                value in customfield_10200.values()}
            }
            for project in self.project_keys
        }

        # Iterate through each issue and update the counts
        for issue in issues:
            project_key = issue['fields']['project']['key']  # Get the project key
            priority = issue['fields']['priority']['name']  # Get the issue priority
            custom_field_values = issue['fields'].get('customfield_10200', [])  # Get custom field values

            if not isinstance(custom_field_values, list):
                custom_field_values = [custom_field_values]  # Ensure custom field values are in a list

            if project_key in issue_count:
                issue_count[project_key]["total"] += 1  # Increment total issue count
                if priority in issue_count[project_key]["priority"]:
                    issue_count[project_key]["priority"][priority] += 1  # Increment priority-specific count

                for custom_field in custom_field_values:
                    if isinstance(custom_field, dict):
                        custom_field_value = custom_field.get('value')
                        custom_field_label = customfield_10200.get(custom_field_value, "Unknown")

                        if custom_field_label not in issue_count[project_key]["customfield"]:
                            issue_count[project_key]["customfield"][custom_field_label] = {
                                "total": 0, "priority": {priority: 0 for priority in issue_priorities}}

                        issue_count[project_key]["customfield"][custom_field_label]["total"] += 1
                        if priority in issue_count[project_key]["customfield"][custom_field_label]["priority"]:
                            issue_count[project_key]["customfield"][custom_field_label]["priority"][priority] += 1

        logger.debug(f"Issue count per project: {issue_count}")
        return issue_count

    def get_issue_counts(self) -> Dict[str, Any]:
        """
        Get the counts of issues per project and cumulative counts.

        :return: A dictionary with issue counts per project and cumulative counts.
        :rtype: Dict[str, Any]
        :raises Exception: If there is an error fetching or counting issues.
        """
        try:
            logger.info("Getting issue counts")
            issues = self.fetch_issues()  # Fetch the issues from JIRA
            issue_count_per_project = self.count_issues_per_project(issues)  # Count issues per project
            cumulative_count = {
                "total": 0,
                "priority": {priority: 0 for priority in issue_priorities},
                "customfield": {value: {"total": 0, "priority": {priority: 0 for priority in issue_priorities}} for
                                value in customfield_10200.values()}
            }

            # Aggregate cumulative counts across all projects
            for counts in issue_count_per_project.values():
                cumulative_count["total"] += counts["total"]
                for priority, count in counts["priority"].items():
                    cumulative_count["priority"][priority] += count
                for custom_field, custom_counts in counts["customfield"].items():
                    cumulative_count["customfield"][custom_field]["total"] += custom_counts["total"]
                    for priority, count in custom_counts["priority"].items():
                        cumulative_count["customfield"][custom_field]["priority"][priority] += count

            logger.debug(f"Cumulative issue count: {cumulative_count}")
            return {
                "per_project": issue_count_per_project,
                "cumulative": cumulative_count
            }
        except Exception as e:
            logger.error(f"Error in getting issue counts: {e}")
            raise Exception(f"Error in getting issue counts: {e}")


class DataFrameTransformer:
    """
    Transformer class to convert issue counts to pandas DataFrames.
    """

    @staticmethod
    def transform_to_dataframes(issue_counts: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        Transform issue counts into pandas DataFrames.

        :param issue_counts: A dictionary with issue counts per project and cumulative counts.
        :type issue_counts: Dict[str, Any]
        :return: A dictionary of pandas DataFrames for each project and cumulative data.
        :rtype: Dict[str, pd.DataFrame]
        :raises Exception: If there is an error transforming data to DataFrames.
        """
        try:
            logger.info("Transforming issue counts to dataframes")
            dataframes: Dict[str, pd.DataFrame] = {}
            # Transform counts for each project into a DataFrame
            for project_key, counts in issue_counts["per_project"].items():
                data: Dict[str, List[Any]] = {
                    "Priority": list(issue_priorities),
                    "Total": [counts["priority"][priority] for priority in issue_priorities]
                }
                for custom_field in customfield_10200.values():
                    data[custom_field] = [counts["customfield"][custom_field]["priority"].get(priority, 0) for priority
                                          in issue_priorities]
                df = pd.DataFrame(data)
                df.loc["Total"] = df.sum(numeric_only=True)
                df.loc["Total", "Priority"] = "Total"

                df.columns = ["" if col in ["Total", "Priority"] else col for col in df.columns]

                dataframes[PROJECT_NAMES[project_key]] = df

            # Transform cumulative counts into a DataFrame
            cumulative_data: Dict[str, List[Any]] = {
                "Priority": list(issue_priorities),
                "Total": [issue_counts["cumulative"]["priority"][priority] for priority in issue_priorities]
            }
            for custom_field in customfield_10200.values():
                cumulative_data[custom_field] = [
                    issue_counts["cumulative"]["customfield"][custom_field]["priority"].get(priority, 0) for priority in
                    issue_priorities]
            cumulative_df = pd.DataFrame(cumulative_data)
            cumulative_df.loc["Total"] = cumulative_df.sum(numeric_only=True)
            cumulative_df.loc["Total", "Priority"] = "Total"

            cumulative_df.columns = ["" if col in ["Total", "Priority"] else col for col in cumulative_df.columns]

            dataframes["All Projects"] = cumulative_df

            logger.debug("Dataframes created successfully")
            return dataframes
        except Exception as e:
            logger.error(f"Error in transforming data to dataframes: {e}")
            raise Exception(f"Error in transforming data to dataframes: {e}")


class ExcelExporter:
    """
    Class for exporting data to an Excel file.

    :param file_name: The name of the Excel file to export.
    :type file_name: str
    :param column_width: The width of the columns in the Excel file, defaults to 15.
    :type column_width: int, optional
    """

    def __init__(self, file_name: str, column_width: int = 15) -> None:
        self.file_name = file_name
        self.column_width = column_width
        self.writer = None
        self.workbook = None
        logger.info(f"ExcelExporter initialized with file_name: {file_name}")

    def __enter__(self) -> 'ExcelExporter':
        """
        Enter the runtime context related to this object.

        :return: The ExcelExporter instance with an initialized Excel writer.
        :rtype: ExcelExporter
        :raises Exception: If there is an error initializing the Excel writer.
        """
        try:
            self.writer = pd.ExcelWriter(self.file_name, engine='xlsxwriter')
            self.workbook = self.writer.book
            logger.info("Excel writer initialized")
            return self
        except Exception as e:
            logger.error(f"Error initializing Excel writer: {e}")
            raise Exception(f"Error initializing Excel writer: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the runtime context related to this object.

        Closes the Excel writer when exiting the context.

        :param exc_type: The exception type.
        :type exc_type: type
        :param exc_val: The exception value.
        :type exc_val: Exception
        :param exc_tb: The traceback object.
        :type exc_tb: TracebackType
        :raises Exception: If there is an error closing the Excel writer.
        """
        try:
            self.writer.close()  # Ensure the Excel writer is closed to save the file
            logger.info("Excel writer closed")
        except Exception as e:
            logger.error(f"Error closing Excel writer: {e}")
            raise Exception(f"Error closing Excel writer: {e}")

    def export(self, dataframes: Dict[str, pd.DataFrame]) -> None:
        """
        Export dataframes to an Excel file.

        :param dataframes: A dictionary of pandas DataFrames to export.
        :type dataframes: Dict[str, pd.DataFrame]
        :raises Exception: If there is an error exporting data to Excel.
        """
        try:
            logger.info("Exporting dataframes to Excel")
            execution_date = datetime.now().strftime('%Y-%m-%d')
            execution_month = (datetime.now().replace(day=1) - pd.DateOffset(months=1)).strftime('%B %Y')

            worksheet = self.workbook.add_worksheet("All Projects")
            self.writer.sheets["All Projects"] = worksheet

            # Merge cells to create a title for the worksheet
            worksheet.merge_range('A1:G1', f'Retailer Performance (Jira Closure Codes) '
                                           f'Executed on: {execution_date}, for month: {execution_month}',
                                  self.workbook.add_format({
                                      'bold': True, 'align': 'center', 'valign': 'vcenter'
                                  }))

            current_row = 2  # Start writing data below the title
            format_border = self.workbook.add_format({
                'border': 1  # Apply border format to cells
            })

            for sheet_name, df in dataframes.items():
                # Write the project name or cumulative data title
                worksheet.write(current_row, 0, sheet_name, self.workbook.add_format({'bold': True}))
                current_row += 1

                # Write the DataFrame headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(current_row, col_num, value, format_border)
                    worksheet.set_column(col_num, col_num, self.column_width)  # Set column width

                # Write the DataFrame data
                for row_num in range(len(df)):
                    for col_num in range(len(df.columns)):
                        worksheet.write(current_row + 1 + row_num, col_num, df.iloc[row_num, col_num], format_border)

                current_row += len(df) + 3  # Move to the next start row with 2 rows spacing
        except Exception as e:
            logger.error(f"Error exporting data to Excel: {e}")
            raise Exception(f"Error exporting data to Excel: {e}")


def main() -> None:
    """
    Main function to execute the JIRA issue counting and export process.

    :raises Exception: If there is an error during the execution.
    """
    try:
        logger.info("Starting main execution")
        jira_base_url = config('JIRA_BASE_URL')  # Fetch the JIRA base URL from environment variables
        jira_api_token = config('JIRA_TOKEN')  # Fetch the JIRA API token from environment variables
        project_keys_list = PROJECT_KEYS  # Get the list of project keys from configuration

        # Use context manager to handle API client
        with JiraClient(jira_base_url, jira_api_token) as client:
            issue_counter = IssueCounter(client, project_keys_list)  # Create an IssueCounter instance
            issue_counts = issue_counter.get_issue_counts()  # Get the issue counts

        transformer = DataFrameTransformer()
        dataframes = transformer.transform_to_dataframes(issue_counts)  # Transform issue counts to DataFrames

        # Use context manager to handle Excel export
        with ExcelExporter("RetailerPerf.xlsx", column_width=20) as exporter:
            exporter.export(dataframes)  # Export DataFrames to an Excel file

        logger.info("Data has been exported to RetailerPerf.xlsx")
    except Exception as e:
        logger.error(f"An error occurred: {e}")  # Log any errors that occur during execution


if __name__ == "__main__":
    main()
