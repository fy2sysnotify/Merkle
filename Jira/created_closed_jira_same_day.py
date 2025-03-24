import requests
from datetime import datetime, timedelta
from decouple import config
import pandas as pd

# Jira configuration
JIRA_BASE_URL = "https://jira-emea.merkle.com"
API_ENDPOINT = "/rest/api/2/search"


# Function to generate JQL queries for the previous month
def generate_jql_queries_for_previous_month():
    # Get the current date
    today = datetime.today()

    # Calculate the first day of the previous month
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = datetime(last_day_of_previous_month.year, last_day_of_previous_month.month, 1)

    # Initialize date range for the previous month
    start_date = first_day_of_previous_month
    end_date = last_day_of_previous_month

    jql_queries = []
    current_date = start_date

    # Loop through each day of the previous month
    while current_date <= end_date:
        # Calculate the next day
        next_date = current_date + timedelta(days=1)

        # Format dates in YYYY-MM-DD format
        current_date_str = current_date.strftime("%Y-%m-%d")
        next_date_str = next_date.strftime("%Y-%m-%d")

        # Construct the JQL query
        jql_query = (
            f'project = ASD AND issuetype = "Support Request" AND summary ~ FLS '
            f'AND created >= {current_date_str} AND created < {next_date_str} '
            f'AND status changed to closed during ({current_date_str}, {current_date_str})'
        )

        # Add the query to the list
        jql_queries.append(jql_query)

        # Move to the next day
        current_date = next_date

    return jql_queries


# Function to send a JQL query to the Jira API and fetch issues
def fetch_issues_from_jira(jql_query):
    url = f"{config('JIRA_BASE_URL')}/rest/api/2/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config('JIRA_TOKEN')}"  # Token-based authentication
    }
    params = {"jql": jql_query, "fields": "key,summary,created,resolutiondate",
              "maxResults": 500}  # Specify required fields

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get("issues", [])
    else:
        print(f"Failed to fetch issues for JQL: {jql_query}")
        print(f"Response Code: {response.status_code}, Response Text: {response.text}")
        return []


# Main script
def main():
    # DataFrame to store all issues
    df = pd.DataFrame(columns=["Key", "Summary", "Created", "Resolution Date"])

    # Generate JQL queries for the previous month
    queries = generate_jql_queries_for_previous_month()

    # Loop through each query and fetch matching issues
    for jql in queries:
        print(f"Executing JQL: {jql}")
        issues = fetch_issues_from_jira(jql)
        if issues:
            print(f"Found {len(issues)} issues:")
            for issue in issues:
                key = issue.get("key", "Unknown")
                fields = issue.get("fields", {})
                summary = fields.get("summary", "No Summary")
                created = fields.get("created", "Unknown")
                resolution_date = fields.get("resolutiondate", "Unknown")

                # Append issue data to the DataFrame
                df = pd.concat([df, pd.DataFrame([{
                    "Key": key,
                    "Summary": summary,
                    "Created": created,
                    "Resolution Date": resolution_date
                }])], ignore_index=True)

    # Export the DataFrame to an Excel file
    output_file = "jira_created_closed_issues.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Exported data to {output_file}")


# Run the script
if __name__ == "__main__":
    main()
