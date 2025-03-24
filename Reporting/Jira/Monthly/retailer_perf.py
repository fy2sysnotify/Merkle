import requests
from decouple import config
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from projects_config import PROJECT_KEYS, PROJECT_NAMES
from available_priorities import issue_priorities
from fields_mapping import customfield_10200


class ApiClient:
    """
    A client for interacting with an API using HTTP requests.

    :param base_url: The base URL of the API.
    :type base_url: str
    :param api_token: The API token used for authentication.
    :type api_token: str
    """

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url
        self.api_token = api_token
        self.session: Optional[requests.Session] = None

    def __enter__(self) -> 'ApiClient':
        """
        Initialize the session for making HTTP requests.

        :return: The API client instance.
        :rtype: ApiClient
        """
        self.session = requests.Session()  # Create a new session for HTTP requests
        self.session.headers.update({
            "Content-Type": "application/json",  # Set content type to JSON
            "Accept": "application/json",  # Accept JSON responses
            "Authorization": f"Bearer {self.api_token}"  # Use the API token for authorization
        })
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """
        Close the session when exiting the context.

        :param exc_type: The exception type, if any.
        :type exc_type: Optional[type]
        :param exc_val: The exception instance, if any.
        :type exc_val: Optional[Exception]
        :param exc_tb: The traceback, if any.
        :type exc_tb: Optional[Any]
        """
        if self.session:
            self.session.close()  # Close the session to free up resources

    def perform_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a GET request to the specified API endpoint with the given parameters.

        :param endpoint: The API endpoint to call.
        :type endpoint: str
        :param params: The query parameters for the request.
        :type params: Dict[str, Any]
        :return: The JSON response from the API.
        :rtype: Dict[str, Any]
        :raises Exception: If the request fails.
        """
        try:
            response = self.session.get(self.base_url + endpoint, params=params)  # Make the GET request
            response.raise_for_status()  # Raise an error for bad status codes

            return response.json()  # Return the response as JSON
        except requests.RequestException as e:
            print(f"Failed to fetch data from JIRA: {e}")
            raise Exception(f"Failed to fetch data from JIRA: {e}")


class JiraClient(ApiClient):
    """
    A client for interacting with the JIRA API.
    """

    def fetch_issues(self, jql_query: str, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch issues from JIRA using a JQL query.

        :param jql_query: The JQL query string.
        :type jql_query: str
        :param max_results: The maximum number of results to return.
        :type max_results: int
        :return: A list of issues from JIRA.
        :rtype: List[Dict[str, Any]]
        """
        params = {
            "jql": jql_query,  # Set the JQL query parameter
            "maxResults": max_results  # Limit the number of results
        }

        return self.perform_request("/rest/api/2/search", params).get('issues', [])


class IssueCounter:
    """
    A class for counting and categorizing issues from JIRA per project.

    :param jira_client: An instance of JiraClient to fetch issues.
    :type jira_client: JiraClient
    :param project_keys: A list of project keys to count issues for.
    :type project_keys: List[str]
    """

    def __init__(self, jira_client: JiraClient, project_keys: List[str]) -> None:
        self.jira_client = jira_client
        self.project_keys = project_keys
        self.jql_query = self.get_jql_query()  # Generate JQL query on initialization

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
            f'AND created >= startOfMonth(-1) '  # Issues created from the start of last month
            f'AND created <= endOfMonth(-1)'  # Issues created until the end of last month
        )

        print(jql_query)

        return jql_query

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch issues from JIRA based on the JQL query.

        :return: A list of issues from JIRA.
        :rtype: List[Dict[str, Any]]
        """

        return self.jira_client.fetch_issues(self.jql_query)  # Fetch issues using the JiraClient

    def count_issues_per_project(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Count and categorize issues per project by priority and custom fields.

        :param issues: A list of issues fetched from JIRA.
        :type issues: List[Dict[str, Any]]
        :return: A dictionary with issue counts per project.
        :rtype: Dict[str, Any]
        """
        # Initialize the structure to hold issue counts
        issue_count = {
            project: {
                "total": 0,  # Total number of issues
                "priority": {priority: 0 for priority in issue_priorities},  # Count by priority
                "customfield": {value: {"total": 0, "priority": {priority: 0 for priority in issue_priorities}}
                                for value in customfield_10200.values()}  # Count by custom fields
            }
            for project in self.project_keys
        }

        for issue in issues:  # Iterate over each issue
            try:
                project_key = issue['fields']['project']['key']  # Get the project key
                priority = issue['fields']['priority']['name']  # Get the priority of the issue
                custom_field_values = issue['fields'].get('customfield_10200', [])  # Get custom field values

                # Ensure custom_field_values is a list
                if not isinstance(custom_field_values, list):
                    custom_field_values = [custom_field_values]

                if project_key in issue_count:  # If the project key is in the issue count structure
                    issue_count[project_key]["total"] += 1  # Increment the total count

                    if priority in issue_count[project_key]["priority"]:
                        issue_count[project_key]["priority"][priority] += 1  # Increment the priority-specific count

                    for custom_field in custom_field_values:  # Iterate over custom field values
                        if custom_field is None:
                            continue  # Skip None values

                        if isinstance(custom_field, dict):
                            custom_field_value = custom_field.get('value')  # Get the custom field value
                            custom_field_label = customfield_10200.get(custom_field_value, "Unknown")  # Map to label

                            if custom_field_label not in issue_count[project_key]["customfield"]:
                                continue  # Skip if the custom field label is unknown

                            issue_count[project_key]["customfield"][custom_field_label]["total"] += 1  # Increment total

                            if priority in issue_count[project_key]["customfield"][custom_field_label]["priority"]:
                                issue_count[project_key]["customfield"][custom_field_label]["priority"][
                                    priority] += 1  # Increment priority

            except KeyError as e:
                print(f"KeyError for issue {issue['key']}: {e}")  # Provide insight into missing keys
            except Exception as e:
                print(f"Error processing issue {issue['key']}: {e}")  # General error handling

        return issue_count

    def get_issue_counts(self) -> Dict[str, Any]:
        """
        Get the counts of issues per project and cumulative counts.

        :return: A dictionary with issue counts per project and cumulative counts.
        :rtype: Dict[str, Any]
        :raises Exception: If there is an error fetching or counting issues.
        """
        try:
            issues = self.fetch_issues()  # Fetch issues from JIRA
            issue_count_per_project = self.count_issues_per_project(issues)  # Count issues per project
            cumulative_count = {
                "total": 0,
                "priority": {priority: 0 for priority in issue_priorities},
                "customfield": {value: {"total": 0, "priority": {priority: 0 for priority in issue_priorities}} for
                                value in customfield_10200.values()}
            }

            for counts in issue_count_per_project.values():  # Aggregate counts across all projects
                cumulative_count["total"] += counts["total"]
                for priority, count in counts["priority"].items():
                    cumulative_count["priority"][priority] += count
                for custom_field, custom_counts in counts["customfield"].items():
                    cumulative_count["customfield"][custom_field]["total"] += custom_counts["total"]
                    for priority, count in custom_counts["priority"].items():
                        cumulative_count["customfield"][custom_field]["priority"][priority] += count

            return {
                "per_project": issue_count_per_project,
                "cumulative": cumulative_count
            }
        except Exception as e:
            print(f"Error in getting issue counts: {e}")
            raise Exception(f"Error in getting issue counts: {e}")


class DataFrameTransformer:
    """
    A class to transform issue counts into pandas DataFrames.
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
            dataframes: Dict[str, pd.DataFrame] = {}
            for project_key, counts in issue_counts["per_project"].items():
                data: Dict[str, List[Any]] = {
                    "Priority": list(issue_priorities),  # List of priorities
                    "Total": [counts["priority"][priority] for priority in issue_priorities]  # Total counts
                }
                for custom_field in customfield_10200.values():
                    data[custom_field] = [counts["customfield"][custom_field]["priority"].get(priority, 0) for priority
                                          in issue_priorities]  # Custom field counts
                df = pd.DataFrame(data)
                df.loc["Total"] = df.sum(numeric_only=True)  # Add a total row
                df.loc["Total", "Priority"] = "Total"

                df.columns = ["" if col in ["Total", "Priority"] else col for col in df.columns]  # Clean column names

                dataframes[PROJECT_NAMES[project_key]] = df  # Map to project name

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

            dataframes["All Projects"] = cumulative_df  # Add cumulative data

            return dataframes
        except Exception as e:
            print(f"Error in transforming data to dataframes: {e}")
            raise Exception(f"Error in transforming data to dataframes: {e}")

    @staticmethod
    def create_issue_specific_dataframe(issues: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Create a DataFrame for issues with `customfield_10200` set to a non-null, non-zero value.

        :param issues: A list of issues fetched from JIRA.
        :type issues: List[Dict[str, Any]]
        :return: A DataFrame containing issues with specific `customfield_10200` values.
        :rtype: pd.DataFrame
        """
        data: List[Dict[str, Any]] = []
        for issue in issues:
            custom_field_value = issue['fields'].get('customfield_10200')
            if custom_field_value and custom_field_value != 0:  # Check for valid custom field values
                issue_key = issue['key']
                issue_summary = issue['fields']['summary']
                issue_priority = issue['fields']['priority']['name']
                data.append({
                    "Issue Key": issue_key,
                    "Summary": issue_summary,
                    "Priority": issue_priority
                })
        return pd.DataFrame(data)


class ExcelExporter:
    """
    A class for exporting DataFrames to an Excel file.

    :param file_name: The name of the Excel file to export.
    :type file_name: str
    :param column_width: The width of the columns in the Excel file.
    :type column_width: int
    """

    def __init__(self, file_name: str, column_width: int = 15) -> None:
        self.file_name = file_name
        self.column_width = column_width
        self.writer: Optional[pd.ExcelWriter] = None
        self.workbook: Optional[Any] = None

    def __enter__(self) -> 'ExcelExporter':
        """
        Initialize the Excel writer.

        :return: The ExcelExporter instance.
        :rtype: ExcelExporter
        :raises Exception: If there is an error initializing the Excel writer.
        """
        try:
            self.writer = pd.ExcelWriter(self.file_name, engine='xlsxwriter')  # Create an Excel writer
            self.workbook = self.writer.book  # Access the workbook
            return self
        except Exception as e:
            print(f"Error initializing Excel writer: {e}")
            raise Exception(f"Error initializing Excel writer: {e}")

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """
        Close the Excel writer when exiting the context.

        :param exc_type: The exception type, if any.
        :type exc_type: Optional[type]
        :param exc_val: The exception instance, if any.
        :type exc_val: Optional[Exception]
        :param exc_tb: The traceback, if any.
        :type exc_tb: Optional[Any]
        """
        try:
            if self.writer:
                self.writer.close()  # Close the writer to save the file
        except Exception as e:
            print(f"Error closing Excel writer: {e}")
            raise Exception(f"Error closing Excel writer: {e}")

    def export(self, dataframes: Dict[str, pd.DataFrame], specific_dataframe: pd.DataFrame) -> None:
        """
        Export DataFrames to an Excel file.

        :param dataframes: A dictionary of pandas DataFrames to export.
        :type dataframes: Dict[str, pd.DataFrame]
        :param specific_dataframe: A DataFrame containing specific issues.
        :type specific_dataframe: pd.DataFrame
        :raises Exception: If there is an error exporting data to Excel.
        """
        try:
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

            current_row = 2
            format_border = self.workbook.add_format({
                'border': 1  # Apply border format to cells
            })

            for sheet_name, df in dataframes.items():
                worksheet.write(current_row, 0, sheet_name,
                                self.workbook.add_format({'bold': True}))  # Write project name
                current_row += 1

                # Write DataFrame headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(current_row, col_num, value, format_border)
                    worksheet.set_column(col_num, col_num, self.column_width)

                # Write DataFrame data
                for row_num in range(len(df)):
                    for col_num in range(len(df.columns)):
                        worksheet.write(current_row + 1 + row_num, col_num, df.iloc[row_num, col_num], format_border)

                current_row += len(df) + 3  # Move to the next start row with spacing

            if not specific_dataframe.empty:
                specific_dataframe.to_excel(self.writer, sheet_name="Specific Issues", index=False)
                worksheet = self.writer.sheets["Specific Issues"]
                for col_num, value in enumerate(specific_dataframe.columns.values):
                    worksheet.set_column(col_num, col_num, self.column_width)

        except Exception as e:
            print(f"Error exporting data to Excel: {e}")
            raise Exception(f"Error exporting data to Excel: {e}")


def main() -> None:
    """
    The main function to execute the JIRA issue counting and export process.

    :raises Exception: If there is an error during the execution.
    """
    try:
        jira_base_url = config('JIRA_BASE_URL')  # Fetch the JIRA base URL from environment variables
        jira_api_token = config('JIRA_TOKEN')  # Fetch the JIRA API token from environment variables
        project_keys_list = PROJECT_KEYS  # Get the list of project keys from configuration

        with JiraClient(jira_base_url, jira_api_token) as client:  # Initialize JIRA client
            issue_counter: IssueCounter = IssueCounter(client, project_keys_list)  # Create an IssueCounter instance
            issue_counts = issue_counter.get_issue_counts()  # Get issue counts
            issues = issue_counter.fetch_issues()  # Fetch issues

        transformer: DataFrameTransformer = DataFrameTransformer()
        dataframes = transformer.transform_to_dataframes(issue_counts)  # Transform issue counts to DataFrames
        specific_dataframe = transformer.create_issue_specific_dataframe(issues)  # Create DataFrame for specific issues

        with ExcelExporter(
                f'RetailerPerf_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                column_width=20
        ) as exporter:  # Initialize ExcelExporter
            exporter.export(dataframes, specific_dataframe)  # Export DataFrames to an Excel file

    except Exception as e:
        print(f"An error occurred: {e}")  # Log any errors that occur during execution


if __name__ == "__main__":
    main()
