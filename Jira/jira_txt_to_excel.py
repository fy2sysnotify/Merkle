import json
import pandas as pd
from typing import List


def read_json_data(filename: str) -> List:
    """
    Reads JSON data from the given file and returns a list of dictionaries.

    :param filename: Source file to read from
    :return: List
    """
    with open(file=filename, encoding='utf-8') as input_file:
        data = input_file.read()
        return json.loads(data)


def write_data_to_excel(data: List, filename: str, columns=None) -> None:
    """
    Writes the given data to an Excel file with the specified filename.
    Transformation is processed by Pandas Library

    :param data: Source List with data
    :param filename: The name of the target Excel file
    :param columns: None by Default or List of strings representing
           name of keys in source txt file and name of columns in target Excel file
    :return: None
    """
    df = pd.DataFrame(data)
    df.to_excel(filename, columns=columns, index=False)


def main() -> None:
    data = read_json_data('LA_projects.txt')
    write_data_to_excel(data, 'Jira_Projects.xlsx')


if __name__ == '__main__':
    main()
