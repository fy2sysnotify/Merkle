from pathlib import Path
import datetime
import MySQLdb
import pandas as pd
import streamlit as st
from decouple import config
from openpyxl import Workbook


class JiraData:
    """
    Class for interacting with a Jira database to retrieve first response time data.

    Args:
        host (str): The hostname of the Jira database.
        user (str): The username for connecting to the database.
        password (str): The password for connecting to the database.
        database (str): The name of the Jira database.

    Attributes:
        host (str): The hostname of the Jira database.
        user (str): The username for connecting to the database.
        password (str): The password for connecting to the database.
        database (str): The name of the Jira database.
        db: MySQL database connection object.

    Methods:
        connect(): Establish a connection to the Jira database.
        close_connection(): Close the database connection.
        get_first_response_time(project_number: int, days_interval: int) -> pd.DataFrame:
            Retrieve first response time data for a specific project.

    Example:
        jira = JiraData(host='localhost', user='user', password='password', database='jira_db')
        jira.connect()
        data = jira.get_first_response_time(project_number=1001, days_interval=7)
        jira.close_connection()
    """

    def __init__(self, host: str, user: str, password: str, database: str) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.db = None

    def connect(self) -> None:
        try:
            self.db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.database)
        except MySQLdb.Error as e:
            st.error(f'Error connecting to the JIRA database: {e}')
            self.db = None

    def close_connection(self) -> None:
        if self.db is not None:
            self.db.close()

    def get_first_response_time(self, project_number: int, days_interval: int) -> pd.DataFrame:
        if self.db is None:
            return pd.DataFrame()

        try:
            with self.db.cursor() as cursor:
                sql_query = f"""
                    SELECT 
                        ji.issuenum,
                        ji.summary,
                        ji.created AS issue_created,
                        ji.reporter,
                        ji.assignee,
                        p.pname AS priority,
                        MIN(ja.created) AS first_response,
                        TIMESTAMPDIFF(MINUTE, ji.created, MIN(ja.created)) AS time_to_first_response_minutes
                    FROM
                        jiradb.jiraissue ji
                        JOIN
                        jiradb.jiraaction ja ON ji.id = ja.issueid
                        JOIN
                        jiradb.priority p ON ji.priority = p.id
                    WHERE
                        ji.created >= CURDATE() - INTERVAL {days_interval} DAY
                        AND ji.PROJECT = {project_number}
                        AND ji.issuetype = 10
                        AND ja.actiontype = 'comment'
                    GROUP BY
                        ji.issuenum, ji.summary, ji.created, ji.reporter, ji.assignee, p.pname
                    ORDER BY ji.issuenum DESC;
                    """

                cursor.execute(sql_query)
                results = cursor.fetchall()
                df = pd.DataFrame(list(results), columns=[i[0] for i in cursor.description])
            return df
        except MySQLdb.Error as e:
            st.error(f'Error retrieving data from the JIRA database: {e}')
            return pd.DataFrame()


class ExcelExporter:
    """
     Class for exporting data to an Excel file.

    Args:
        filename (str): The name of the Excel file to create.

    Attributes:
        filename (str): The name of the Excel file.
        workbook: An openpyxl Workbook object.

    Methods:
        export_to_excel(dataframe: pd.DataFrame, sheet_name: str) -> None:
            Export a DataFrame to a specified sheet in the Excel file.
        save_and_close() -> None:
            Save the Excel file and close the workbook.

    Example:
        exporter = ExcelExporter(filename='output.xlsx')
        exporter.export_to_excel(dataframe, sheet_name='Sheet1')
        exporter.save_and_close()
    """

    def __init__(self, filename) -> None:
        self.filename = filename
        self.workbook = Workbook()
        self.workbook.remove(self.workbook.active)

    def export_to_excel(self, dataframe, sheet_name) -> None:
        worksheet = self.workbook.create_sheet(title=sheet_name)

        column_names = list(dataframe.columns)
        worksheet.append(column_names)

        for row in dataframe.itertuples(index=False):
            worksheet.append(row)

    def save_and_close(self) -> None:
        self.workbook.save(self.filename)
        self.workbook.close()


class StreamlitApp:
    """
    Streamlit application for retrieving and exporting Jira first response time data.

    This class enables users to interact with the application by selecting projects and defining a days interval for data retrieval.

    Attributes:
        project_mapping (dict): A mapping of project names to their corresponding project numbers.

    Methods:
        __init__(): Initialize the Streamlit application.
            - Initializes the Streamlit app title.
            - Reads Jira database connection information from environment variables using `decouple`.
            - Presents a user interface for selecting projects and specifying the days interval.

        run(): Main method to run the Streamlit application.
            - Validates user input, ensuring at least one project is selected and the days interval is greater than 0.
            - Handles the button click to retrieve data, export it to an Excel file, and display a download button.
            - Displays success or error messages as appropriate.

        display_download_button(): Display a download button for the exported Excel file.
            - Checks if the Excel file exists, and if so, provides a button for the user to download it.

    Example:
        app = StreamlitApp()
        app.run()

    Usage:
        1. Create an instance of StreamlitApp.
        2. Run the application using the `run` method.
        3. Select one or more projects and specify a days interval.
        4. Click the "Get First Response Time" button to retrieve data.
        5. If successful, an Excel file with the data will be available for download.
    """

    project_mapping = {
        'Asda': 10090,
        'Clarins': 13032,
        'CCHQwell': 15833,
        'Mayborn': 17431,
        'Zwilling': 15032
    }

    def __init__(self) -> None:
        st.title('Jira First Response Time')

        self.host = config('JIRA_DB_HOST', default='')
        self.user = config('JIRA_DB_USER', default='')
        self.password = config('JIRA_DB_PASSWORD', default='', cast=str)
        self.database = config('JIRA_DATABASE', default='')

        # Use project names as options
        self.project_list = list(self.project_mapping.keys())
        self.selected_projects = st.multiselect('Select Projects', self.project_list)

        self.days_interval = st.number_input('Days Interval', step=1)

        self.first_response_time = JiraData(host=self.host, user=self.user, password=self.password,
                                            database=self.database)
        self.first_response_time.connect()

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.excel_exporter = ExcelExporter(
            filename=f"JIRA_FRT_{timestamp}.xlsx"
        )

    def run(self) -> None:
        if not self.selected_projects:
            st.warning('Please select at least one project.')
        elif self.days_interval < 1:
            st.warning('Please specify a valid number of days (must be 1 or more).')
        else:
            if st.button('Get First Response Time'):
                with st.spinner('Retrieving data from JIRA database...'):
                    try:
                        for project_name in self.selected_projects:
                            project_number = self.project_mapping[project_name]
                            df = self.first_response_time.get_first_response_time(project_number=project_number,
                                                                                  days_interval=self.days_interval)
                            if not df.empty:
                                sheet_name = f"{project_name}_{project_number}"
                                self.excel_exporter.export_to_excel(df, sheet_name)

                        self.excel_exporter.save_and_close()
                        st.success('Data exported to Excel.')
                        self.display_download_button()
                    except Exception as e:
                        st.error(f'An error occurred: {e}')

    def display_download_button(self) -> None:
        if Path(self.excel_exporter.filename).is_file():
            st.download_button(
                label='Download Excel File with FRT',
                data=open(self.excel_exporter.filename, 'rb').read(),
                file_name=self.excel_exporter.filename,
                mime='application/octet-stream'
            )


def main() -> None:
    """
    Main function to run the Streamlit application.

    Example:
    if __name__ == "__main__":
        main()
    """

    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
