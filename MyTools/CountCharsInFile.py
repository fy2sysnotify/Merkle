def count_chars_in_file(filename: str) -> int:
    """
    Counts the number of characters in a file by using a
    generator expression (len(line) for line in my_file)
    to iterate through the lines in the file and
    compute the total length of all the lines.

    :param: filename (str): The name of the file.
    :return: int: The number of characters in the file.
    """
    with open(filename, encoding='utf-8') as my_file:
        return sum(len(line) for line in my_file)


print(count_chars_in_file('input.json'))
