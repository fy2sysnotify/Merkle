import pandas as pd
import requests
from typing import List, Tuple, Any
from get_totp_headless_browsing import get_access_token


class AccountManagerClient:
    """
    A client for interacting with the Account Manager API.
    """

    def __init__(self, access_token: str) -> None:
        """
        Initialize the client.

        :param: access_token (str): The OAuth2 access token to use for authentication.
        """
        self.access_token = access_token
        self.headers = {'Authorization': f'Bearer {self.access_token}'}
        self.session = requests.Session()

    def get_merkle_users(self) -> List[Tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]]:
        """
        Get a list of Merkle users.

        :return: A list of email addresses of Merkle users.
        """
        am_response = self.session.get(
            'https://account.demandware.com/dw/rest/v1/users?page=0&size=5000',
            headers=self.headers).json()

        return [
            (
                item['mail'], item['firstName'], item['lastName'], item['displayName'], item['id'],
                item['userState'], item['lastLoginDate'],  item['passwordExpirationTimestamp'],
                item['roles'], item['organizations'], item['primaryOrganization'], item['roleTenantFilter'],
                item['roleTenantFilterMap']
            )
            for item in am_response['content']
        ]

    def save_merkle_users_to_excel(self, file_path: str) -> None:
        """
        Save the Merkle users to an Excel file.

        :param file_path: The file path to save the Excel file to.
        """
        merkle_users = self.get_merkle_users()
        df = pd.DataFrame(
            merkle_users, columns=[
                'Email', 'FirstName', 'LastName', 'DisplayName', 'id', 'userState',
                'lastLoginDate', 'passwordExpirationTimestamp', 'Roles', 'Organizations',
                'PrimaryOrganization', 'RoleTenantFilter', 'RoleTenantFilterMap'
            ]
        )
        df.to_excel(file_path, index=False)


def main() -> None:
    """
    Get a list of users and save their email addresses to an Excel file.

    :return: None
    """
    access_token = get_access_token()
    client = AccountManagerClient(access_token)
    try:
        client.save_merkle_users_to_excel('ам_users.xlsx')
    finally:
        client.session.close()


if __name__ == '__main__':
    main()
