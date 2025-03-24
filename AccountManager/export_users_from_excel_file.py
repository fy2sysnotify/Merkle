import pandas as pd
from pathlib import Path
import constants as const
import url_links
from get_totp_headless_browsing import get_access_token
from my_logger import configure_logger
import httpx


def convert_excel_to_set(file_name: str, column_name: str) -> set:
    """
    Convert the specified column of an Excel file to a set.

    Args:
        file_name (str): The name of the Excel file.
        column_name (str): The name of the column to be converted to a set.

    Returns:
        set: A set containing the unique values from the specified column.
    """
    df = pd.read_excel(file_name, sheet_name=0)
    return set(df[column_name])


class AccountManagerUsersExporter:
    """
    Exports user data from Account Manager to an Excel file.
    """

    def __init__(self):
        """
        Initialize the AccountManagerUsersExporter object.
        """
        script_name = Path(__file__).stem
        self.logger = configure_logger(script_name)
        today_is = const.today_is
        self.excel_file = f"{script_name}_{today_is}.xlsx"
        self.headers = {"Authorization": f"Bearer {get_access_token()}"}

    def get_users(self) -> list:
        """
        Get a list of all users from Account Manager.

        Returns:
            list: A list of user dictionaries containing user data.
        """
        with httpx.Client() as client:
            try:
                response = client.get(
                    f"{url_links.users_endpoint}?page=0&size=5000",
                    headers=self.headers,
                )
                response.raise_for_status()
                am_response = response.json()
            except httpx.HTTPError as conn_error:
                self.logger.error(conn_error)
                raise

            return am_response["content"]

    def export_users_to_excel(self, user_list: list) -> None:
        """
        Export a list of users to an Excel file with Pandas library.

        Args:
            user_list (list): A list of user dictionaries to export.
        """
        df = pd.DataFrame(user_list)
        df.to_excel(self.excel_file, index=False)


def main() -> None:
    """
    Main function to export user data from Account Manager to an Excel file.

    Usage:
    - Get all users from Account Manager.
    - Export all user data to a new Excel file.

    """
    am_users = AccountManagerUsersExporter()
    all_users = am_users.get_users()

    initial_list_file = 'initial_list.xlsx'
    column_name = 'mail'
    excel_data = convert_excel_to_set(initial_list_file, column_name)

    filtered_users = [user for user in all_users if user.get(column_name) in excel_data]

    am_users.export_users_to_excel(filtered_users)


if __name__ == "__main__":
    main()
