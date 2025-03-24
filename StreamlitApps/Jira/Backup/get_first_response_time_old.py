from pathlib import Path
import datetime
import MySQLdb
import pandas as pd
import streamlit as st
from decouple import config


class JiraData:
    """
    A class for retrieving JIRA data from a MySQL database using MySQLdb and pandas.

    Args:
        host (str): MySQL database host.
        user (str): MySQL database user.
        password (str): MySQL database password.
        database (str): JIRA database name.

    Attributes:
        host (str): MySQL database host.
        user (str): MySQL database user.
        password (str): MySQL database password.
        database (str): JIRA database name.
        db (MySQLdb.Connection): MySQL database connection object.

    Methods:
        connect(): Establishes a connection to the MySQL database.
        close_connection(): Closes the connection to the MySQL database.
        get_first_response_time(project_number, days_interval): Retrieves first response time data from JIRA database.
    """

    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.db = None  # Initialize db as None

    def connect(self):
        """
        Establishes a connection to the MySQL database using MySQLdb.

        Returns:
            None
        """

        try:
            self.db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.database)
        except MySQLdb.Error as e:
            st.error(f'Error connecting to the JIRA database: {e}')
            self.db = None

    def close_connection(self):
        """
        Closes the connection to the MySQL database.

        Returns:
            None
        """

        if self.db is not None:
            self.db.close()

    def get_first_response_time(self, project_number: int, days_interval: int) -> pd.DataFrame:
        """
        Retrieves first response time data from the JIRA database using MySQLdb and pandas.

        Args:
            project_number (int): JIRA project number.
            days_interval (int): Number of days to consider for the data retrieval.

        Returns:
            pd.DataFrame: DataFrame containing first response time data.
        """

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
                        jiradb4.jiraissue ji
                        JOIN
                        jiradb4.jiraaction ja ON ji.id = ja.issueid
                        JOIN
                        jiradb4.priority p ON ji.priority = p.id
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
    A class for exporting a DataFrame to an Excel file using pandas.

    Args:
        filename (str): Name of the Excel file to be created.

    Attributes:
        filename (str): Name of the Excel file to be created.

    Methods:
        export_to_excel(dataframe): Exports a DataFrame to an Excel file.
    """

    def __init__(self, filename: str):
        self.filename = filename

    def export_to_excel(self, dataframe: pd.DataFrame):
        """
        Exports a DataFrame to an Excel file using pandas.

        Args:
            dataframe (pd.DataFrame): DataFrame to be exported.

        Returns:
            None
        """

        try:
            dataframe.to_excel(self.filename, index=False)
        except Exception as e:
            st.error(f'Error exporting DataFrame to Excel: {e}')


class StreamlitApp:
    """
    A class representing the Streamlit application for interacting with the user interface and displaying results.

    Attributes:
        host (str): JIRA DB host retrieved from the environment configuration using decouple.
        user (str): JIRA DB user retrieved from the environment configuration using decouple.
        password (str): JIRA DB password retrieved from the environment configuration using decouple.
        database (str): JIRA database retrieved from the environment configuration using decouple.
        project_number (int): JIRA project number input from the user using streamlit.
        days_interval (int): Days interval input from the user using streamlit.
        first_response_time (JiraData): An instance of JiraData for retrieving data from the database.
        excel_exporter (ExcelExporter): An instance of ExcelExporter for exporting data to an Excel file.

    Methods:
        run(): Runs the Streamlit application.
        display_download_button(): Displays the download button for the exported Excel file.
    """

    def __init__(self):
        """
        Initializes the Streamlit application.

        Retrieves JIRA DB host, user, password, and database from environment configuration using decouple.
        Initializes attributes for user inputs, data retrieval, and Excel exporting.
        """

        st.title('Jira First Response Time')

        self.host = config('JIRA_DB_HOST', default='')
        self.user = config('JIRA_DB_USER', default='')
        self.password = config('JIRA_DB_PASSWORD', default='', cast=str)
        self.database = config('JIRA_DATABASE', default='')

        self.project_number = st.number_input('Project Number', step=1)
        self.days_interval = st.number_input('Days Interval', step=1)

        self.first_response_time = JiraData(host=self.host, user=self.user, password=self.password,
                                            database=self.database)
        self.first_response_time.connect()
        self.excel_exporter = ExcelExporter(
            filename=f"JIRA_FRT{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        )

    def run(self):
        """
        Runs the Streamlit application.

        Retrieves data from the JIRA database, exports to Excel, and displays download button.
        """

        if st.button('Get First Response Time'):
            with st.spinner('Retrieving data from JIRA database...'):
                df = self.first_response_time.get_first_response_time(project_number=self.project_number,
                                                                      days_interval=self.days_interval)
                if not df.empty:
                    self.excel_exporter.export_to_excel(df)
                    st.success('Data exported to Excel.')
                else:
                    st.warning('No data available to export.')
            self.display_download_button()

    def display_download_button(self):
        """
        Displays the download button for the exported Excel file.
        """

        if Path(self.excel_exporter.filename).is_file():
            st.download_button(
                label='Download Excel File with FRT',
                data=open(self.excel_exporter.filename, 'rb').read(),
                file_name=self.excel_exporter.filename,
                mime='application/octet-stream',
            )


def main():
    """
    Main function to start the Streamlit application.

    Returns:
        None
    """
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
