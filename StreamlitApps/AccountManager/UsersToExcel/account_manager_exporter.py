from datetime import datetime
from typing import List, Dict, Union, Optional
import requests
from requests.exceptions import RequestException, HTTPError
import pandas as pd
from decouple import config
from client_creds_token import get_access_token


class AccountManagerUsersExporter:
    """
    Provides functionality to export user details from Account Manager to an Excel file.

    This class leverages the Strategy Design Pattern by accepting different strategies
    for access token extraction encapsulated within AccessTokenExtractor.

    Attributes:
        excel_file (str): The name of the Excel file where user data will be saved.
    """

    def __init__(self) -> None:
        """
        Initializes the AccountManagerUsersExporter with a specific access token extraction strategy.
        """

        self.excel_file = f'AccountManagerUsers_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx'
        self.users_api_endpoint = config('USERS_API_ENDPOINT', default='')

    def get_users(self) -> Optional[List[Dict[str, Union[int, str]]]]:
        """
        Fetches user details from the Account Manager using the access token.

        Returns:
            Optional[List[Dict[str, Union[int, str]]]]: A list of user details represented as dictionaries.
            Returns None in case of errors.
        """

        try:
            access_token = get_access_token()
        except Exception as e:
            print(f'Error extracting access token: {e}')
            return None

        headers = {"Authorization": f"Bearer {access_token}"}

        with requests.get(
                self.users_api_endpoint,
                headers=headers
        ) as response:
            try:
                response.raise_for_status()
            except HTTPError as status_error:
                print(f'HTTP status error: {status_error}')
                return None
            except RequestException as request_error:
                print(f'Request error: {request_error}')
                return None
            except ValueError:
                print('Invalid JSON response')
                return None

            am_response = response.json()

        return am_response.get('content')

    def export_users_to_excel(self) -> None:
        """
        Exports the user details fetched from the Account Manager to an Excel file.

        Only users with the userState values Enabled, Deleted, and Initial will be exported.
        """

        users = self.get_users()
        if not users:
            print('Failed to retrieve users. No data to export.')
            return

        try:
            df = pd.DataFrame(users)
            df.to_excel(self.excel_file, index=False)
        except Exception as e:
            print(f'Error exporting users to Excel: {e}')


if __name__ == "__main__":
    exporter = AccountManagerUsersExporter()
    exporter.export_users_to_excel()
