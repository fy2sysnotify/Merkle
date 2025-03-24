from pathlib import Path
import streamlit as st
from account_manager_exporter import AccountManagerUsersExporter


class StreamlitApp:
    """
    A Streamlit application that provides an interface for users to retrieve Account Manager users
    and offers a download button for an Excel file containing the user data.

    This class is responsible for setting up and running the Streamlit application.

    Attributes:
        am_users_exporter (AccountManagerUsersExporter): An instance responsible for exporting
            user data to an Excel file.
    """

    def __init__(self, am_users_exporter: AccountManagerUsersExporter) -> None:
        """
        Initializes the StreamlitApp class with the provided AccountManagerUsersExporter instance.

        Args:
            am_users_exporter (AccountManagerUsersExporter): An instance responsible for managing
                the export of user data to an Excel file.
        """

        try:
            st.title('Get Account Manager Users')
            st.write('Get Account Manager Users')
            self.am_users_exporter = am_users_exporter
        except Exception as e:
            st.error(f'An error occurred while initializing the application: {e}')

    def run(self) -> None:
        """
        Executes the Streamlit app. Displays a button to fetch and download user data.

        This method is responsible for running the Streamlit application and handling the user interface.
        When the 'Get Users' button is clicked, it fetches and exports user data and provides a download
        button for the generated Excel file.
        """

        try:
            if st.button('Get Users'):
                with st.spinner('Getting access token, fetching and exporting users...'):
                    self.am_users_exporter.export_users_to_excel()
                self.display_download_button()
        except Exception as e:
            st.error(f'An error occurred while running the application: {e}')

    def display_download_button(self) -> None:
        """
        Displays a download button for the Excel file if it exists.

        This method is responsible for displaying the download button for the Excel file if it's available.
        It may raise errors if the file is not found or if there are permission issues.
        """

        try:
            if Path(self.am_users_exporter.excel_file).is_file():
                with open(self.am_users_exporter.excel_file, 'rb') as file:
                    st.download_button(
                        label='Download Excel File with users',
                        data=file.read(),
                        file_name=self.am_users_exporter.excel_file,
                        mime='application/octet-stream',
                    )
            else:
                st.warning('Excel file does not exist.')
        except FileNotFoundError:
            st.error('Excel file was not found.')
        except PermissionError:
            st.error('Permission denied while accessing the Excel file.')
        except Exception as e:
            st.error(f'An error occurred while displaying the download button: {e}')


def main() -> None:
    """
    The main function that initializes and runs the Streamlit app.

    This function sets up the AccountManagerUsersExporter, initializes the StreamlitApp, and runs
    the Streamlit application to provide access to Account Manager users.
    """

    try:
        am_users_exporter: AccountManagerUsersExporter = AccountManagerUsersExporter()
        app: StreamlitApp = StreamlitApp(am_users_exporter)
        app.run()
    except Exception as e:
        st.error(f'An unexpected error occurred: {e}')


if __name__ == "__main__":
    main()
