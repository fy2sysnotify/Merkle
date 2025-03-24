import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Union
import constants as const
import url_links
from slack_messaging import upload_to_slack
from get_totp_headless_browsing import get_access_token
from my_logger import configure_logger
import httpx


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

    def get_users(self) -> List[Dict[str, Union[int, str]]]:
        """
        Get a list of users from Account Manager.

        :return: List[Dict[str, Union[int, str]]]: A list of user
                dictionaries containing user data.
        """
        with httpx.Client() as client:
            try:
                response = client.get(
                    f'{url_links.users_endpoint}?page=0&size=5000',
                    headers=self.headers,
                )
                response.raise_for_status()
                am_response = response.json()
            except httpx.HTTPError as conn_error:
                self.logger.error(conn_error)
                raise

            return am_response["content"]

    def export_users_to_excel(self) -> None:
        """
        Export a list of users to an Excel file with Pandas library. The list of users
        is filtered to only include users with a 'userState' of 'ENABLED'.
        The exported data includes the user's 'mail', 'firstName', and 'lastName'.

        :return: None
        """
        users = self.get_users()

        df = pd.DataFrame(users)
        # df = df[(df["userState"] == "ENABLED") & (df["mail"] == "konstantin.yanev@merkle.com")]
        # df = df[df["userState"] == "ENABLED"]
        # df = df[["mail", "firstName", "lastName"]]
        df.to_excel(self.excel_file, index=False)

    def upload_to_slack(self) -> None:
        """
        Upload the Excel file containing user data to a Slack channel.

        :Args:
            slack_channel (str): The Slack channel to upload the file to.
            file_to_upload (str): The path to the file to upload.
            slack_comment (str): The message to include with the file upload.
        :return: None
        """
        upload_to_slack(
            slack_channel="#account-manager",
            file_to_upload=self.excel_file,
            slack_comment="Hi, this is report for all active "
            "users in Account Manager as of today",
        )

    def cleanup_local_file(self) -> None:
        """
        Delete the Excel file containing user data from the local file system.

        :return: None
        """
        os.remove(self.excel_file)


def main() -> None:
    """
    Export user data from Account Manager, upload the data to Slack,
    and delete the local file containing the data.

    :return: None
    """
    am_users = AccountManagerUsersExporter()
    am_users.export_users_to_excel()
    # am_users.upload_to_slack()
    # am_users.cleanup_local_file()


if __name__ == "__main__":
    main()
