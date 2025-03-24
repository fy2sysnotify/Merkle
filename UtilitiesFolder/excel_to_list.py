import pandas as pd


def convert_excel_column_to_list(file_name: str = None, column_name: str = None) -> list:
    """
    Convert the specified column of an Excel file to a list.

    :param: file_name (str): The name of the Excel file.
    :param: column_name (str): The name of the column to be converted to a list.
    :return: list: A list containing the values from the specified column.
    """
    df = pd.read_excel(file_name, sheet_name=0)
    return df[column_name].tolist()
