import httpx
import asyncio
from typing import Any
from get_totp_headless_browsing import get_access_token


class AccountManagerClient:
    """
    A client for interacting with the Account Manager API.

    Attributes:
        access_token (str): The OAuth2 access token used for authentication.
        headers (dict): HTTP headers containing authorization information.
    """

    def __init__(self, access_token: str) -> None:
        """
        Initializes the AccountManagerClient.

        Args:
            access_token (str): The OAuth2 access token to use for authentication.
        """
        self.access_token = access_token
        self.headers = {'Authorization': f'Bearer {self.access_token}'}

    def get_merkle_users(self) -> list[tuple[Any, Any, Any]]:
        """
        Retrieves a list of Merkle users.

        Returns:
            list[tuple]: A list of tuples containing information about Merkle users.
                Each tuple includes user details such as user ID, email, and state.
        """

        async def fetch_users():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://account.demandware.com/dw/rest/v1/users?page=0&size=5000',
                    headers=self.headers)
                response.raise_for_status()
                am_response = response.json()
                return [
                    item
                    for item in am_response['content']
                    # if item['userState'] == 'ENABLED'
                ]

        return asyncio.run(fetch_users())


def main() -> None:
    """
    Retrieves a list of enabled Merkle users from the Account Manager API
    and prints their email addresses.

    Returns:
        None
    """
    access_token = get_access_token()
    client = AccountManagerClient(access_token)
    try:
        merkle_users = client.get_merkle_users()
        for user in merkle_users:
            print(user)
        print("Number of Merkle users:", len(merkle_users))
    except httpx.HTTPStatusError as e:
        print("HTTP error:", e)
    except httpx.RequestError as e:
        print("Request error:", e)
    finally:
        pass


if __name__ == '__main__':
    main()
