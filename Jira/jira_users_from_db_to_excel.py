import os
import MySQLdb
import pandas as pd
from dataclasses import dataclass


@dataclass
class JiraData:
    """A class to connect to JIRA database and retrieve the data of active users.

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

    def get_active_users_data(self) -> pd.DataFrame:
        """Retrieves the data of active users from JIRA database and returns it as a DataFrame.

        Returns:
            pandas.DataFrame: DataFrame of active users' data.
        """

        sql_query = """
                SELECT cwd_user.user_name, cwd_user.display_name, cwd_user.email_address, cwd_user.updated_date, 
                GROUP_CONCAT(cwd_membership.parent_name SEPARATOR '|') as group_membership
                FROM cwd_user
                LEFT JOIN cwd_membership
                ON cwd_user.id = cwd_membership.child_id
                WHERE cwd_user.active = 1
                GROUP BY cwd_user.user_name, cwd_user.display_name, cwd_user.email_address, cwd_user.updated_date
                ORDER BY lower(cwd_user.user_name);
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
        df = jira_data.get_active_users_data()

    exporter = ExcelExporter(filename='jira_users.xlsx')
    exporter.export_to_excel(df)


if __name__ == '__main__':
    main()
