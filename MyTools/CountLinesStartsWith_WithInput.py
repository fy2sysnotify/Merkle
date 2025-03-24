def count_lines_starting_with(filename: str, start_string: str) -> int:
    """
    Counts the number of lines in a file that start with a certain string.

    :param: filename (str): The name of the file.
    :param: start_string (str): The string that the lines must start with.
    :return: int: The number of lines in the file that start with the specified string.
    """
    with open(filename, 'r') as f:
        return sum(1 for line in f if line.startswith(start_string))
