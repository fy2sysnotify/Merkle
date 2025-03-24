import os
import time
import requests
import pandas as pd


class JiraUserFetcher:
    """
    A class for fetching users from a Jira server.
    """

    def __init__(self, jira_server: str, jira_user: str, jira_pass: str) -> None:
        """
        Initialize a JiraUserFetcher instance with the given
                Jira server url, user, and password.

        :param: jira_server (str): The url of the Jira server.
        :param: jira_user (str): The username to use for
                authenticating with the Jira server.
        :param: jira_pass (str): The password to use for
                authenticating with the Jira server.
        """
        self.jira_server = jira_server
        self.jira_user = jira_user
        self.jira_pass = jira_pass
        self.headers = {
            'Content-Type': 'application/json',
        }

    def fetch_users_with_empty_email(self) -> list:
        """
        Fetch all users from the Jira server who have
                an empty email address.

        :return: A list of dictionaries representing
                the users with empty email addresses.
        """
        users = []
        with requests.Session() as session:
            session.auth = (self.jira_user, self.jira_pass)

            startAt = 0
            maxResults = 1000
            all_users_endpoint = '/rest/api/2/user/search?username=.&includeInactive=true'

            while True:
                params = {
                    'startAt': startAt,
                    'maxResults': maxResults,
                }

                response = session.get(
                    self.jira_server + all_users_endpoint,
                    params=params, headers=self.headers
                )
                results = response.json()

                if not results:
                    break
                for item in results:
                    if item['emailAddress'] == '':
                        users.append(item)
                startAt += maxResults

        return users


class DataExporter:
    """
    A class for exporting data to Excel.
    """

    def __init__(self, data: list) -> None:
        """
        Initialize a DataExporter instance with the given data.

        :param: data (list): The list with data to be exported.
        :return: None
        """
        self.data = data

    def export_to_excel(self, filepath: str) -> None:
        """
        Converts the data to a Pandas dataframe and
        then uses the 'to_excel' method to save it
        to an Excel file at the given filepath.

        :param: filepath (str): The filepath where
                the Excel file should be saved.
        :return: None
        """
        df = pd.DataFrame(self.data)
        df.to_excel(filepath, index=False)


def main() -> None:
    """
    Fetch users with empty email addresses from a
            Jira server and export them to an Excel file.

    :return: None
    """
    jira_user = os.getenv('j_prd_us_la')
    jira_pass = os.getenv('j_prd_ps_la')
    jira_server = os.getenv('j_prd_url_la')

    script_start_time = time.perf_counter()

    jira_fetcher = JiraUserFetcher(jira_server, jira_user, jira_pass)
    users = jira_fetcher.fetch_users_with_empty_email()
    exporter = DataExporter(users)
    exporter.export_to_excel('empty_email_users_la_jira.xlsx')

    script_finish_time = time.perf_counter()
    print(f'Script execution time is '
          f'{round(script_finish_time - script_start_time, 2)} seconds.'
          )


if __name__ == '__main__':
    main()
