import json


def json_values_to_list(file_path: str) -> list:
    """
    Retrieves all values from the specified JSON file and append them to a list.

    :param: file_path: The file path of the JSON file.
    :return: A list of all values in the JSON file.
    """
    with open(file=file_path, encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    return [value for key, value in json_data.items()]
