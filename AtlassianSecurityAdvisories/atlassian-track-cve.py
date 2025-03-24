import os
import requests
from datetime import datetime
from pathlib import Path
from my_logger import configure_logger
from slack_messaging import slack_post

OLD_FILE: str = f'old_source_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html'
ORIGINAL_FILE: str = 'original_source.html'
TARGET_SUBSTRING: str = 'CVE'
logger = configure_logger(script_name=Path(__file__).stem)
url = 'https://www.atlassian.com/trust/security/advisories'


def count_substring_in_string(my_string: str, my_substring: str) -> int:
    """
    Count the number of times a substring appears in a string.

    :param: my_string (str): The string to search in.
    :param: my_substring (str): The substring to search for.
    :return: The number of times the substring appears in the string.
    """
    return my_string.count(my_substring)


def write_new_file(file_name: str, text: str) -> None:
    """
    Write the given text to a new file with the given file name.

    :param: file_name (str): The name of the file to create.
    :param: text (str): The text to write to the file.
    :return: None
    """
    with open(file_name, 'w', encoding='utf-8') as file_to_write:
        file_to_write.write(text)


def update_original_source() -> None:
    """
    Compare the HTML code of the original source file to the code at a given URL.
    If the code is different and substring 'CVE' is different, send a message to
    a Slack channel and update the original source file.

    :return: None
    """
    with requests.Session() as session:
        atlassian_response = session.get(url)
        atlassian_text = atlassian_response.text

        with open(ORIGINAL_FILE, 'r', encoding='utf-8') as original_source:
            source_data = original_source.read()
            if source_data == atlassian_text:
                logger.debug('Original source and new source look identical')
            else:
                logger.debug(f'There is a change in HTML code at {url}')
                count_cve_atlassian = count_substring_in_string(atlassian_text, TARGET_SUBSTRING)
                logger.debug(f'CVE count in atlassian HTML source is {count_cve_atlassian}')
                count_cve_source = count_substring_in_string(source_data, TARGET_SUBSTRING)
                logger.debug(f'CVE count in local HTML source is {count_cve_source}')
                if count_cve_atlassian > count_cve_source:
                    slack_post(slack_channel='#atlassian-track-cve',
                               slack_message=f'There is a change in HTML code at {url}. '
                                             f'Please load the page and check for new CVE.')

        os.rename(ORIGINAL_FILE, OLD_FILE)
        write_new_file(ORIGINAL_FILE, atlassian_text)


def main() -> None:
    """
    Run the main logic of the program.

    :return: None
    """
    update_original_source()


if __name__ == '__main__':
    main()
