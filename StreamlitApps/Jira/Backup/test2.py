from pathlib import Path
import datetime
import MySQLdb
import pandas as pd
import streamlit as st
from decouple import config
from openpyxl import Workbook


class JiraData:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.db = None

    def connect(self):
        try:
            self.db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.database)
        except MySQLdb.Error as e:
            st.error(f'Error connecting to the JIRA database: {e}')
            self.db = None

    def close_connection(self):
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
    def __init__(self, filename):
        self.filename = filename
        self.workbook = Workbook()
        self.workbook.remove(self.workbook.active)  # Remove the default sheet

    def export_to_excel(self, dataframe, sheet_name):
        worksheet = self.workbook.create_sheet(title=sheet_name)

        column_names = list(dataframe.columns)
        worksheet.append(column_names)

        for row in dataframe.itertuples(index=False):
            worksheet.append(row)

    def save_and_close(self):
        self.workbook.save(self.filename)
        self.workbook.close()


class StreamlitApp:
    project_mapping = {
        'Asda': 10090,
        'Clarins': 13032,
        'CCHQwell': 15833,
        'Mayborn': 17431,
        'Zwilling': 15032
    }

    def __init__(self):
        st.title('Jira First Response Time')

        self.host = config('JIRA_DB_HOST', default='')
        self.user = config('JIRA_DB_USER', default='')
        self.password = config('JIRA_DB_PASSWORD', default='', cast=str)
        self.database = config('JIRA_DATABASE', default='')

        self.selected_projects = []

        st.sidebar.title('Project Selection')
        for project_name, _ in self.project_mapping.items():
            selected = st.sidebar.checkbox(project_name, False)
            if selected:
                self.selected_projects.append(project_name)

        self.days_interval = st.number_input('Days Interval', step=1)

        self.first_response_time = JiraData(host=self.host, user=self.user, password=self.password,
                                            database=self.database)
        self.first_response_time.connect()

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.excel_exporter = ExcelExporter(
            filename=f"JIRA_FRT_{timestamp}.xlsx"
        )

    def run(self):
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

    def display_download_button(self):
        if Path(self.excel_exporter.filename).is_file():
            st.download_button(
                label='Download Excel File with FRT',
                data=open(self.excel_exporter.filename, 'rb').read(),
                file_name=self.excel_exporter.filename,
                mime='application/octet-stream'
            )


def main():
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
