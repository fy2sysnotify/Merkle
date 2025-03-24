from pathlib import Path
from typing import List, Dict, Union
import pandas as pd
import httpx
import streamlit as st
import constants as const
import url_links
from get_totp_headless_browsing import get_access_token
from my_logger import configure_logger


class AccountManagerUsersExporter:
    """Class to export Account Manager users to an Excel file."""

    def __init__(self):
        """Initialize the AccountManagerUsersExporter.

        Initializes the class attributes, such as the logger,
        today's date, Excel file name, and headers for HTTP requests.
        """

        script_name: str = 'AccountManagerUsers'
        self.logger = configure_logger(script_name)
        today_is: str = const.today_is
        self.excel_file: str = f"{script_name}_{today_is}.xlsx"
        self.headers: Dict[str, str] = {"Authorization": f"Bearer {get_access_token()}"}

    def get_users(self) -> List[Dict[str, Union[int, str]]]:
        """Fetches user data from the Account Manager API.

        Returns:
            List[Dict[str, Union[int, str]]]: A list of user dictionaries
                containing user information.
        """

        with httpx.Client() as client:
            try:
                response = client.get(
                    f"{url_links.users_endpoint}?page=0&size=5000",
                    headers=self.headers,
                )
                response.raise_for_status()
                am_response: Dict[str, Union[int, str]] = response.json()
            except httpx.HTTPError as conn_error:
                self.logger.error(conn_error)
                raise

            return am_response["content"]

    def export_users_to_excel(self) -> None:
        """Exports Account Manager users to an Excel file.

        Fetches users, filters enabled users, and creates
        an Excel file containing user information.
        """

        users: List[Dict[str, Union[int, str]]] = self.get_users()
        df: pd.DataFrame = pd.DataFrame(users)
        df = df[df["userState"] == "ENABLED"]
        df.to_excel(self.excel_file, index=False)


class StreamlitApp:
    """Streamlit application for exporting Account Manager users."""

    def __init__(self):
        """Initialize the StreamlitApp.

        Sets up the Streamlit application and creates an instance
        of AccountManagerUsersExporter.
        """

        st.title('Get Account Manager Users')
        st.write('Get Account Manager Users')
        self.am_users: AccountManagerUsersExporter = AccountManagerUsersExporter()

    def run(self) -> None:
        """Runs the Streamlit application.

        Displays a button to fetch and export users when clicked.
        """

        if st.button('Get Users'):
            with st.spinner('Fetching and exporting users...'):
                self.am_users.export_users_to_excel()
            self.display_download_button()

    def display_download_button(self) -> None:
        """Displays a download button for the generated Excel file.

        Displays a download button if the Excel file is available.
        """

        if Path(self.am_users.excel_file).is_file():
            st.download_button(
                label="Download Excel File with users",
                data=open(self.am_users.excel_file, 'rb'),
                file_name=self.am_users.excel_file,
                mime="application/octet-stream",
            )


def main() -> None:
    """Main function to run the Streamlit application."""

    app: StreamlitApp = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
