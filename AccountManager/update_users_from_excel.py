from requests.exceptions import HTTPError, JSONDecodeError
import requests
import pandas as pd
from get_totp_headless_browsing import get_access_token
import url_links
from typing import List, Dict, Union


def convert_excel_to_list(file_name: str, column_name: str) -> List[str]:
    """
    Convert the specified column of an Excel file to a list.

    :param file_name: str: The name of the Excel file.
    :param column_name: str: The name of the column to be converted to a list.
    :return: List[str]: A list containing the values from the specified column.
    """
    # Read the Excel file and extract the specified column as a list
    df = pd.read_excel(file_name, sheet_name=0)
    return df[column_name].tolist()


def update_user_data(users_to_update: List[str], headers: Dict[str, str]) -> None:
    """
    Update user data in the Demandware system.

    :param users_to_update: List[str]: A list of user emails to update.
    :param headers: Dict[str, str]: HTTP headers for the request.
    :return: None
    """
    try:
        # Retrieve user data from the Demandware system
        am_response = requests.get(f'{url_links.users_endpoint}?page=0&size=5000',
                                   headers=headers).json()
    except Exception as conn_error:
        # Handle connection errors
        print(conn_error)
        raise

    counter = 0
    for email in users_to_update:
        for user_data in am_response['content']:
            if user_data['mail'] == email:
                counter += 1
                user_id = user_data['id']
                role_tenant_filter = user_data['roleTenantFilter']

                # Modify roleTenantFilter to include additional roles
                role_tenant_filter = role_tenant_filter.replace('ECOM_ADMIN:',
                                                                'ECOM_ADMIN:blcx_dev,blcx_prd,blcx_sbx,blcx_stg,')
                user_data = {'roleTenantFilter': role_tenant_filter}
                print(user_data)

                try:
                    # Update user data using PUT method with the specific user's email address
                    update_response = requests.put(f'{url_links.users_endpoint}/{user_id}', headers=headers,
                                                   json=user_data)
                    update_response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

                    try:
                        json_response = update_response.json()
                        print("JSON Response:", json_response)
                    except JSONDecodeError:
                        # Handle cases where the response is not in JSON format
                        print("Response is not in JSON format.")
                except HTTPError as http_err:
                    # Handle HTTP errors
                    print(f"HTTP error occurred: {http_err}")
                except Exception as err:
                    # Handle other unexpected errors
                    print(f"An error occurred: {err}")

    print(f'{counter} users were updated')


def main() -> None:
    """
    Main function to execute the user data update process.

    :return: None
    """

    # Retrieve user emails from the Excel file
    users_to_update = convert_excel_to_list(file_name='users_to_update.xlsx', column_name='users')

    headers: Dict[str, Union[str, int]] = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json'
    }

    # Perform the user data update process
    update_user_data(users_to_update, headers)


if __name__ == "__main__":
    main()
