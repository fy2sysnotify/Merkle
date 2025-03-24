import os
import requests
import pandas as pd
from typing import List
from dataclasses import dataclass


@dataclass
class JiraAPI:
    url: str
    username_jira: str
    password_jira: str

    def get_response(self) -> List:
        """Makes a GET request to the Jira API and returns the response as a dictionary.

        Returns:
            dict: The response from the Jira API as a dictionary.

        Raises:
            ValueError: If the request to API failed with status code other than 200.
        """

        headers = {'Content-Type': 'application/json'}

        with requests.Session() as session:
            session.auth = (self.username_jira, self.password_jira)
            session.headers.update(headers)
            response = session.get(self.url)

            if response.status_code not in (200, 201):
                raise ValueError(f'Request to API failed with status code {response.status_code}')

            return response.json()


@dataclass
class ExcelExporter:
    file_path: str

    def write_to_excel(self, data: List) -> None:
        """Writes the given data to an Excel file.

        Args:
            data (Dict): The data to write to the Excel file, as a dictionary.

        Returns:
            None: Returns nothing.

        Raises:
            ValueError: If data is not in dictionary format.
        """

        df = pd.DataFrame(data)
        df.to_excel(self.file_path, index=False)
        print(f'Successfully wrote data to Excel file at {self.file_path}')


@dataclass
class JiraUsersExporter:
    api_jira: JiraAPI
    exporter_excel: ExcelExporter

    def export(self) -> None:
        """Exports data from the Jira API to an Excel file.

        Returns:
            None: Returns nothing.

        Raises:
            ValueError: If data is not in dictionary format.
        """

        data = self.api_jira.get_response()
        self.exporter_excel.write_to_excel(data)


def main() -> None:
    """
    Exports data from the Jira API to an Excel file.
    Reads in credentials and file path from environment variables.

    Returns:
        None: Returns nothing.
    """

    url = (os.getenv('j_prd_url') +
           '/rest/api/2/user/search?username=.&includeInactive=true+&maxResults=1000'
           )
    username = os.getenv('j_prd_us')
    password = os.getenv('j_prd_ps')
    excel_file_path = 'jira_users.xlsx'

    jira_api = JiraAPI(url, username, password)
    excel_exporter = ExcelExporter(excel_file_path)
    jira_users_exporter = JiraUsersExporter(jira_api, excel_exporter)
    jira_users_exporter.export()


if __name__ == '__main__':
    main()
