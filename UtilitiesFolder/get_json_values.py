import json


def retrieve_json_values(file_path: str) -> None:
    """
    Retrieves all values from the specified JSON file and prints them to the console.

    :param: file_path: The file path of the JSON file.
    :return: None
    """
    with open(file=file_path, encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    for key, value in json_data.items():
        print(value)
