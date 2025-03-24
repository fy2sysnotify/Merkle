import requests
import pandas as pd
import ast
from dataclasses import dataclass
from typing import Dict, List, Optional
import url_links
from get_totp_headless_browsing import get_access_token


@dataclass
class User:
    """A data class representing a user with various attributes.

    Attributes:
        mail (str): The email address of the user.
        firstName (str): The first name of the user.
        lastName (str): The last name of the user.
        displayName (str): The display name of the user - first and last name combined.
        businessPhone (Optional[str]): The business phone number of the user, if available.
        homePhone (Optional[str]): The home phone number of the user, if available.
        mobilePhone (Optional[str]): The mobile phone number of the user, if available.
        roles (List[str]): A list of roles that the user has.
        organizations (List[str]): A list of organizations that the user belongs to.
        primaryOrganization (str): The user's primary organization.
        roleTenantFilter (str): A filter that specifies the tenant associated with the user's roles.
        roleTenantFilterMap (Dict[str, str]): A mapping of role names to their corresponding tenant filters.
    """
    mail: str
    firstName: str
    lastName: str
    displayName: str
    businessPhone: Optional[str]
    homePhone: Optional[str]
    mobilePhone: Optional[str]
    roles: List[str]
    organizations: List[str]
    primaryOrganization: str
    roleTenantFilter: str
    roleTenantFilterMap: Dict[str, str]


@dataclass
class ExcelMigration:
    """A class representing an Excel file migration tool.

    Attributes:
        filename (str): The name of the Excel file to migrate.
        df (pandas.DataFrame): The contents of the Excel file as a Pandas DataFrame.

    Methods:
        read_excel_file() -> pandas.DataFrame:
            Reads the Excel file specified in the `filename` attribute and returns its contents as a DataFrame.
    """
    filename: str

    def __post_init__(self):
        self.df = self.read_excel_file()

    def read_excel_file(self) -> pd.DataFrame:
        """Reads the Excel file specified in the `filename` attribute and returns its contents as a DataFrame.

        Returns:
            pandas.DataFrame: The contents of the Excel file as a Pandas DataFrame.
        """
        df = pd.read_excel(self.filename)
        return df

    @staticmethod
    def create_data_dict(row: pd.Series) -> User:
        """Converts a row of data from a Pandas DataFrame to a `User` object.

        Args:
            row (pandas.Series): A row of data from a Pandas DataFrame.

        Returns:
            User: A `User` object with attributes based on the data in the row.
        """
        email = row['mail']
        employee_names, domain = email.rsplit('@', 1)
        email = f'{employee_names}@merkle.com'
        first_name, last_name = employee_names.split('.')
        first_name = first_name.capitalize()
        last_name = f'{last_name.capitalize()} - Merkle'
        display_name = first_name + last_name

        # This lines checks if the value of rows ['Roles'], ['Organizations'], ['RoleTenantFilterMap'] are a string
        # using the isinstance() function. If it is a string, it uses ast.literal_eval() to evaluate the string
        # as a Python expression and assigns the result to the roles/organizations/roleTenantFilterMap variable.
        # ast.literal_eval() is a function that safely evaluates a string containing a Python literal
        # (such as a dictionary, list, tuple, number, or string) and returns the corresponding Python object.
        roles = ast.literal_eval(row['roles']) if isinstance(row['roles'], str) else []
        organizations = ast.literal_eval(row['organizations']) if isinstance(row['organizations'], str) else []
        roleTenantFilterMap = ast.literal_eval(row['roleTenantFilterMap']) if isinstance(row['roleTenantFilterMap'],
                                                                                         str) else {}

        data = User(
            mail=email,
            firstName=first_name,
            lastName=last_name,
            displayName=display_name,
            businessPhone=None,
            homePhone=None,
            mobilePhone=None,
            roles=roles,
            organizations=organizations,
            primaryOrganization=row['primaryOrganization'],
            roleTenantFilter=row['roleTenantFilter'],
            roleTenantFilterMap=roleTenantFilterMap
        )

        return data

    @staticmethod
    def send_request(data: User) -> Dict[str, str]:
        """Sends a POST request to a specified URL with a `User` object as the payload.

        Args:
            data (User): A `User` object representing the user to be migrated.

        Returns:
            Dict[str, str]: A dictionary containing the response from the server.
        """
        headers = {
            'Authorization': f'Bearer {get_access_token()}',
            'Content-Type': 'application/json'
        }

        with requests.Session() as session:
            try:
                response = session.post(url_links.users_endpoint, headers=headers, json=data.__dict__).json()
            except Exception as conn_error:
                print(conn_error)
                raise

        return response

    def migrate_users(self) -> None:
        """Iterates over the rows of an Excel file, creates `User` objects from the data in each row, and sends a
        migration request to a server for each user.

        Returns:
            None.
        """
        for index, row in self.df.iterrows():
            data = self.create_data_dict(row)
            response = self.send_request(data)
            print(response)


def main() -> None:
    """
    Entry point of the script for migrating users from an Excel file.

    This function initializes an instance of the ExcelMigration class, reads the migration list from an Excel file,
    and triggers the user migration process.

    Returns:
        None

    Raises:
        None
    """

    migration = ExcelMigration('migration_list.xlsx')
    migration.migrate_users()


if __name__ == '__main__':
    main()
