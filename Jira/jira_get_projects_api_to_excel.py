import os
import pandas as pd
import httpx
from httpx import HTTPStatusError
from typing import List
from dataclasses import dataclass


@dataclass
class ServerInfo:
    """
    A dataclass representing the server URL, username, and password.

    Attributes:
        url (str): The URL of the server.
        username (str): The username to access the server.
        password (str): The password to access the server.
    """

    url: str
    username: str
    password: str


@dataclass
class JiraProjects:
    """
    A class representing the Jira projects.

    Attributes:
        server_info (ServerInfo): The server information containing the URL, username and password.
    """

    server_info: ServerInfo

    def get_project_data(self) -> List[dict]:
        """
        Returns a list of project data from the given server.

        Returns:
            List[dict]: A list of dictionaries containing project data.
        """

        with httpx.Client() as client:
            client.auth = (self.server_info.username, self.server_info.password)
            client.headers.update({'Content-Type': 'application/json'})
            try:
                response = client.get(f'{self.server_info.url}/rest/api/2/project')
                response.raise_for_status()
                return response.json()
            except HTTPStatusError as e:
                print(f"Request failed with status code {e.response.status_code}.")
                return []

    @staticmethod
    def write_data_to_excel(data: List[dict], filename: str, columns: List[str] = None) -> None:
        """
        Writes the given data to an Excel file with the specified filename.

        Args:
            data (List[dict]): A list of dictionaries containing the data to write to the Excel file.
            filename (str): The name of the target Excel file.
            columns (List[str], optional): A list of strings representing
                the keys in the data dictionaries that will be used as column names in the Excel file.
                If None, all keys will be used. Defaults to None.
        """

        pd.DataFrame(data).to_excel(filename, columns=columns, index=False)


def main() -> None:
    """
    The main function of the script.

    It retrieves Jira project data from a server and writes it to an Excel file.
    """

    # Get server information from environment variables
    server_info = ServerInfo(os.getenv('j_prd_url'), os.getenv('j_prd_us'), os.getenv('j_prd_ps'))

    # Create a JiraProjects object with the server information
    jira_projects = JiraProjects(server_info)

    # Get the project data from the Jira server
    project_data = jira_projects.get_project_data()

    # Write the project data to an Excel file
    JiraProjects.write_data_to_excel(project_data, 'Jira_Projects.xlsx')


if __name__ == '__main__':
    main()
