import re


def remove_illegal_chars(input_file: str, output_file: str, encoding: str = 'utf-8') -> None:
    """
    Remove illegal characters from a file and write the modified content to a new file.

    :param: input_file (str): The path of the input file.
    :param: output_file (str): The path of the output file.
    :param: encoding (str, optional): The encoding to use when reading and writing the files. Defaults to 'utf-8'.
    :return: None
    """
    with open(input_file, 'r', encoding=encoding) as f:
        content = f.read()

    pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]')
    content = pattern.sub('', content)

    with open(output_file, mode='w', encoding=encoding) as f:
        f.write(content)


remove_illegal_chars('input.xml', 'output.xml')
