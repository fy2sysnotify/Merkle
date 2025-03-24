import os
import MySQLdb
import pandas as pd
from dataclasses import dataclass


@dataclass
class JiraData:
    """A class to connect to JIRA database and retrieve the data of first response time.

    Attributes:
        host (str): The host of the JIRA database.
        user (str): The username to connect to the JIRA database.
        password (str): The password to connect to the JIRA database.
        database (str): The JIRA database name.
        db (MySQLdb.Connection): The connection to the JIRA database.
    """

    host: str
    user: str
    password: str
    database: str
    db: MySQLdb.Connection = None

    def __post_init__(self):
        """Initializes a JiraData object."""

        self.db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.database)

    def get_first_response_time(self) -> pd.DataFrame:
        """Retrieves the data of First Response Time for issues from JIRA database and returns it as a DataFrame.

        Returns:
            pandas.DataFrame: DataFrame of First Response Time data.
        """

        # Get first response time in minutes for project Clarins Group V3 (13032)
        # and issue of type Support Request (10)
        # for the last 90 days
        # SQL can be adjusted to serve other queries
        sql_query = """
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
                    ji.created >= CURDATE() - INTERVAL 90 DAY
                    AND ji.PROJECT = 13032
                    AND ji.issuetype = 10
                    AND ja.actiontype = 'comment' -- Adjust if necessary to include other action types
                GROUP BY
                    ji.issuenum, ji.summary, ji.created, ji.reporter, ji.assignee, p.pname
                ORDER BY ji.issuenum DESC;
                """
        cursor = self.db.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        df = pd.DataFrame(list(results), columns=[i[0] for i in cursor.description])
        cursor.close()

        return df

    def close_connection(self) -> None:
        """Closes the connection to the JIRA database.

        Returns:
            None
        """

        self.db.close()


@dataclass
class ExcelExporter:
    """A class to export a DataFrame to an Excel file.

    Attributes:
        filename (str): The name of the Excel file to be exported.
    """

    filename: str

    def export_to_excel(self, dataframe: pd.DataFrame) -> None:
        """Exports the DataFrame to an Excel file.

        Args:
            dataframe (pandas.DataFrame): The DataFrame to be exported.

        Returns:
            None
        """

        dataframe.to_excel(self.filename, index=False)


def main() -> None:
    """The main function that connects to the JIRA database, gets the required data of active users,
    inserts the data into a Pandas DataFrame, exports the data to an Excel file, and closes the connection
    to the JIRA database.

    Returns:
        None
    """

    jira_data = JiraData(
        host=os.getenv('JIRA_DB_HOST'),
        user=os.getenv('JIRA_DB_USER'),
        password=os.getenv('JIRA_DB_PASSWORD'),
        database=os.getenv('JIRA_DATABASE')
    )
    with jira_data.db:
        df = jira_data.get_first_response_time()

    exporter = ExcelExporter(filename='JIRA_FRT.xlsx')
    exporter.export_to_excel(df)


if __name__ == '__main__':
    main()
