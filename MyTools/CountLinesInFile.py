def count_lines_in_file(filename: str) -> int:
    """
    Counts the number of lines in a file by using a
    generator expression (1 for line in f) to
    iterate through the lines in the file and count
    the number of lines.

    :param: filename (str): The name of the file.
    :return: int: The number of lines in the file.
    """
    with open(filename, encoding='utf-8') as my_file:
        return sum(1 for line in my_file)
