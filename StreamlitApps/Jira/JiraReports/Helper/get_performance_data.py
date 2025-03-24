import pandas as pd
import requests
from decouple import config
from typing import List, Dict, Any
from projects_config import PROJECT_KEYS, PROJECT_NAMES
from fields_mapping import customfield_10200
from available_priorities import issue_priorities


class JiraClient:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url
        self.api_token = api_token

    def perform_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

        response = requests.get(
            self.base_url + endpoint,
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Failed to fetch data from JIRA. Status code: {response.status_code}, Response: {response.text}")


class JiraIssueCounter:
    def __init__(self, jira_client: JiraClient, project_keys: List[str], custom_field_mapping: Dict[str, str]):
        self.jira_client = jira_client
        self.project_keys = project_keys
        self.custom_field_mapping = custom_field_mapping
        self.priorities = issue_priorities

    def fetch_issues(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        projects_query = ','.join(self.project_keys)
        jql_query = (
            f'project IN ({projects_query}) '
            f'AND issuetype = "Support Request" '
            f'AND created >= {start_date} '
            f'AND created <= {end_date} '
            f'AND cf[10200] in ({", ".join(self.custom_field_mapping.keys())})'
        )

        print(jql_query)

        params = {
            "jql": jql_query,
            "maxResults": 1000
        }

        return self.jira_client.perform_request("/rest/api/2/search", params).get('issues', [])

    def count_issues_by_project_custom_field_and_priority(self, issues: List[Dict[str, Any]], custom_field_id: str) -> \
    Dict[str, Dict[str, Dict[str, int]]]:
        project_counts = {
            project: {
                key: {priority: 0 for priority in self.priorities}
                for key in self.custom_field_mapping.keys()
            } for project in self.project_keys
        }

        for issue in issues:
            project_key = issue['fields']['project']['key']
            priority_name = issue['fields']['priority']['name']
            if project_key in project_counts:
                custom_field_values = issue['fields'].get(custom_field_id)
                if custom_field_values:
                    for value in custom_field_values:
                        if isinstance(value, dict):
                            value = value.get('value')
                        if value in project_counts[project_key] and priority_name in project_counts[project_key][value]:
                            project_counts[project_key][value][priority_name] += 1

        return project_counts

    def save_to_excel(self, project_counts: Dict[str, Dict[str, Dict[str, int]]], filename: str):
        total_counts = {
            "Cumulative": {cf: 0 for cf in self.custom_field_mapping.values()},
            "Minor": {cf: 0 for cf in self.custom_field_mapping.values()},
            "Major": {cf: 0 for cf in self.custom_field_mapping.values()},
            "Critical": {cf: 0 for cf in self.custom_field_mapping.values()},
            "Blocker": {cf: 0 for cf in self.custom_field_mapping.values()}
        }

        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet("Performance Data")
            row_offset = 0

            border_format = workbook.add_format({
                'border': 1
            })

            for project_key, custom_field_dict in project_counts.items():
                project_name = PROJECT_NAMES.get(project_key, project_key)
                data = {
                    "Cumulative": {cf: 0 for cf in self.custom_field_mapping.values()},
                    "Minor": {cf: 0 for cf in self.custom_field_mapping.values()},
                    "Major": {cf: 0 for cf in self.custom_field_mapping.values()},
                    "Critical": {cf: 0 for cf in self.custom_field_mapping.values()},
                    "Blocker": {cf: 0 for cf in self.custom_field_mapping.values()}
                }

                for custom_field, priority_dict in custom_field_dict.items():
                    custom_field_name = self.custom_field_mapping[custom_field]
                    for priority, count in priority_dict.items():
                        data[priority][custom_field_name] += count
                        data["Cumulative"][custom_field_name] += count
                        total_counts[priority][custom_field_name] += count
                        total_counts["Cumulative"][custom_field_name] += count

                # Create DataFrame for this project
                df = pd.DataFrame(data).T.reset_index()
                df.columns = ["Priority"] + list(self.custom_field_mapping.values())

                # Ensuring A1 and B1 are empty
                worksheet.write(row_offset, 0, "")
                worksheet.write(row_offset, 1, "")

                # Project name in A2
                worksheet.write(row_offset + 1, 0, project_name)

                # Priorities in B2 to B6
                priorities = ["Cumulative", "Minor", "Major", "Critical", "Blocker"]
                for row_num, priority in enumerate(priorities, start=1):
                    worksheet.write(row_offset + row_num, 1, priority)

                # Custom field names in C1 to G1
                headers = list(self.custom_field_mapping.values())
                for col_num, header in enumerate(headers, start=2):
                    worksheet.write(row_offset, col_num, header, workbook.add_format({'bold': True}))

                # Writing the data starting from C2
                for row_num, priority in enumerate(priorities, start=1):
                    for col_num, header in enumerate(headers, start=2):
                        worksheet.write(row_offset + row_num, col_num, data[priority][header])

                # Add outside border
                start_row = row_offset + 1
                end_row = row_offset + len(priorities) + 1
                end_col = len(headers) + 1
                worksheet.conditional_format(start_row, 0, end_row, end_col,
                                             {'type': 'no_errors', 'format': border_format})

                # Adjust column width
                for col_num, header in enumerate(headers, start=2):
                    max_width = max(len(header), max(df[header].astype(str).map(len).max(), len(header))) + 2
                    worksheet.set_column(col_num, col_num, max_width)

                # Move row_offset down by the number of priorities plus the 2 empty rows
                row_offset += len(priorities) + 3

            # Write the total counts at the end
            df_total = pd.DataFrame(total_counts).T.reset_index()
            df_total.columns = ["Priority"] + list(self.custom_field_mapping.values())

            # Ensuring A1 and B1 are empty
            worksheet.write(row_offset, 0, "")
            worksheet.write(row_offset, 1, "")

            # Project name in A2
            worksheet.write(row_offset + 1, 0, "All Projects")

            # Priorities in B2 to B6
            for row_num, priority in enumerate(priorities, start=1):
                worksheet.write(row_offset + row_num, 1, priority)

            # Custom field names in C1 to G1
            for col_num, header in enumerate(headers, start=2):
                worksheet.write(row_offset, col_num, header, workbook.add_format({'bold': True}))

            # Writing the data starting from C2
            for row_num, priority in enumerate(priorities, start=1):
                for col_num, header in enumerate(headers, start=2):
                    worksheet.write(row_offset + row_num, col_num, total_counts[priority][header])

            # Add outside border for totals
            start_row = row_offset + 1
            end_row = row_offset + len(priorities) + 1
            worksheet.conditional_format(start_row, 0, end_row, end_col, {'type': 'no_errors', 'format': border_format})

            # Adjust column width
            for col_num, header in enumerate(headers, start=2):
                max_width = max(len(header), max(df_total[header].astype(str).map(len).max(), len(header))) + 2
                worksheet.set_column(col_num, col_num, max_width)


def main():
    # Load configuration from .env file
    jira_url = config('JIRA_BASE_URL')
    api_token = config('JIRA_TOKEN')

    # Create JiraClient instance
    jira_client = JiraClient(jira_url, api_token)

    # Create JiraIssueCounter instance
    jira_issue_counter = JiraIssueCounter(jira_client, PROJECT_KEYS, customfield_10200)

    # Define date range
    start_date = "startOfMonth(-1)"
    end_date = "endOfMonth(-1)"

    # Fetch and count issues
    issues = jira_issue_counter.fetch_issues(start_date, end_date)
    project_counts = jira_issue_counter.count_issues_by_project_custom_field_and_priority(issues, 'customfield_10200')

    # Save counts to Excel file
    jira_issue_counter.save_to_excel(project_counts, 'RetailerPerf.xlsx')


if __name__ == "__main__":
    main()
