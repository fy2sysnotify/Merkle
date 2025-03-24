# Import the requests library for making HTTP requests to the Jira API
import requests

# Import the datetime module for handling and manipulating date and time data
from datetime import datetime

# Import the config function from the decouple library to load environment variables or .env file configurations
from decouple import config

# Import pandas for working with structured data (DataFrames) and exporting to Excel
import pandas as pd

# Import typing for type annotations, including List, Dict, and Optional types
from typing import List, Dict, Optional


# Define headers to authenticate Jira API requests
HEADERS: Dict[str, str] = {
    "Accept": "application/json",  # Specify the expected response format
    "Authorization": f"Bearer {config('JIRA_TOKEN')}",  # Retrieve Jira token from environment configuration
}

# Define JQL queries to fetch issues based on specific criteria
JQL_QUERIES: Dict[str, str] = {
    "Created FLS": 'project = ASD AND issuetype = "Support Request" AND created >= startOfMonth(-1) AND created <= endOfMonth(-1) AND summary ~ "FLS" AND resolutiondate is not EMPTY',
    "Resolved FLS": 'project = ASD AND issuetype = "Support Request" AND resolved >= startOfMonth(-1) AND resolved <= endOfMonth(-1) AND summary ~ "FLS"',
    "Closed FLS": 'project = ASD AND issuetype = "Support Request" AND status changed TO closed DURING (startOfMonth(-1), startOfMonth()) AND summary ~ "FLS"'
}

# Template for API request parameters
PARAMS_TEMPLATE: Dict[str, str] = {
    "fields": "key,summary,created,resolutiondate",  # Specify fields to fetch for each issue
    "maxResults": 500,  # Maximum number of results to fetch per query
}


def calculate_resolved_time_minutes(created: str, resolution_date: str) -> int:
    """
    Calculate the time in minutes between created and resolution dates.

    Args:
        created (str): ISO 8601 datetime string representing the creation time.
        resolution_date (str): ISO 8601 datetime string representing the resolution time.

    Returns:
        int: Time difference in minutes.
    """
    # Parse created and resolution dates from strings to datetime objects
    created_date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%f%z")
    resolved_date = datetime.strptime(resolution_date, "%Y-%m-%dT%H:%M:%S.%f%z")

    # Calculate the time difference between created and resolved dates
    time_difference = resolved_date - created_date

    # Convert time difference to minutes and return it as an integer
    return int(time_difference.total_seconds() // 60)


def fetch_issues(jql: str) -> List[Dict]:
    """
    Fetch issues from Jira using a JQL query.

    Args:
        jql (str): JQL query string.

    Returns:
        List[Dict]: List of issues returned from Jira.
    """
    # Create a copy of the template parameters and add the JQL query
    params = PARAMS_TEMPLATE.copy()
    params["jql"] = jql

    try:
        # Make a GET request to the Jira API with headers and parameters
        response = requests.get(f"{config('JIRA_BASE_URL')}/rest/api/2/search", headers=HEADERS, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Return the list of issues from the API response
        return response.json().get("issues", [])
    except requests.exceptions.RequestException as e:
        # Handle request errors and print the exception message
        print(f"Error fetching issues for JQL: {jql}\n{e}")
        return []


def main() -> None:
    """
    Main function to process JQL queries, fetch Jira issues, and export them to an Excel file.
    """
    # Dictionary to store DataFrames for each JQL query
    excel_data: Dict[str, pd.DataFrame] = {}

    # Iterate through each JQL query and corresponding sheet name
    for sheet_name, jql in JQL_QUERIES.items():
        print(f"Processing JQL Query: {sheet_name}")  # Log the current query being processed

        # Fetch issues for the current JQL query
        issues = fetch_issues(jql)
        if not issues:
            # Log and skip if no issues were found
            print(f"No issues found for {sheet_name}")
            continue

        # Initialize a list to store issue data for the current query
        data: List[Dict[str, Optional[any]]] = []

        # Process each issue returned by the Jira API
        for issue in issues:
            # Extract relevant fields from the issue
            key = issue.get("key")  # Unique issue key
            summary = issue.get("fields", {}).get("summary")  # Summary or title of the issue
            created = issue.get("fields", {}).get("created")  # Creation date of the issue
            resolution_date = issue.get("fields", {}).get("resolutiondate")  # Resolution date of the issue

            # Calculate resolution times if both created and resolution dates are available
            if created and resolution_date:
                resolved_minutes = calculate_resolved_time_minutes(created, resolution_date)  # Time in minutes
                resolved_hours = resolved_minutes // 60  # Convert minutes to hours
                resolved_days = resolved_minutes // (60 * 24)  # Convert minutes to days
            else:
                # If either date is missing, set resolution times to None
                resolved_minutes = None
                resolved_hours = None
                resolved_days = None

            # Append processed issue data to the list
            data.append({
                "Key": key,
                "Summary": summary,
                "Created": created,
                "Resolution Date": resolution_date,
                "Resolved Time (Minutes)": resolved_minutes,
                "Resolved Time (Hours)": resolved_hours,
                "Resolved Time (Days)": resolved_days
            })

        # Convert the list of issue data into a DataFrame
        df = pd.DataFrame(data)

        # Sort the DataFrame by the 'Created' column in ascending order
        df = df.sort_values(by="Created", ascending=True)

        # Store the DataFrame in the dictionary with the sheet name as the key
        excel_data[sheet_name] = df

    # Export all DataFrames to a single Excel file if data is available
    if excel_data:
        excel_file = "jira_asda_fls_issues_report.xlsx"  # File name for the Excel report

        # Use pandas ExcelWriter to write multiple sheets to one Excel file
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            for sheet_name, df in excel_data.items():
                # Write each DataFrame to a separate sheet in the Excel file
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Log success message with the file name
        print(f"Data exported to {excel_file}")


# Entry point of the script
if __name__ == "__main__":
    main()
