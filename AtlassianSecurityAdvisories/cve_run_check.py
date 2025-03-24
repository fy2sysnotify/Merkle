import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Any
from dataclasses import dataclass
from slack_messaging import slack_post
from my_logger import configure_logger
from cve_arg_list import track_cve_args


def get_json_value(json_file: str, json_element_key: str) -> Any:
    """
    Reads a JSON file and returns the value of the given key in the JSON object.

    :param: json_file (str): The file path of the JSON file to read from.
    :param: json_element_key (str): The key to look up in the JSON object.
    :return: The value associated with the given key in the JSON object.
    """
    with open(file=json_file, encoding='utf-8') as data:
        json_content = json.load(data)

    return json_content[json_element_key]


def replace_json_value(json_file: str, json_key: str, new_value: Any) -> None:
    """
    Replaces the value of a given key in a JSON object with a new value.

    :param: json_file (str): The file path of the JSON file to read from and write to.
    :param: json_key (str): The key to look up in the JSON object.
    :param: new_value (str): The new value to associate with the given key in the JSON object.
    :return: None
    """
    with open(json_file, encoding='utf-8') as target_json:
        json_content = json.load(target_json)

    json_content[json_key] = new_value

    with open(json_file, mode='w', encoding='utf-8') as target_json:
        json.dump(json_content, target_json)


def get_upper_cve_text(cve_url: str, element_h: str, upper_id: str) -> str:
    """
    Facilitates the handling of xml and html with Beautiful Soup library.
    Retrieves the text of the first li element within the first ul element
    that follows the element_h element with id=upper_id on the given cve_url.

    :param: cve_url (str): The URL of the page to scrape.
    :param: element_h (str): The name of the HTML element to search for.
    :param: upper_id (str): The value of the `id` attribute to search for in the HTML element.
    :return: The text of the first `li` element within the first `ul` element that follows the
         `element_h` element with `id=upper_id` on the given `cve_url`.
    """
    soup = BeautifulSoup(requests.get(cve_url).text, features='lxml')
    upper_cve_li_tag = soup.find(
        element_h, {'id': upper_id}
    ).find_next_sibling('ul').find('li')

    return upper_cve_li_tag.findChild().text


@dataclass
class TrackCVE:
    """
    Initializes the TrackCVE class with the given parameters.

    :param: product (str): The name of the product to track.
    :param: text_location (str): The file path of the JSON file containing the original text.
    :param: text_key (str): The key of the original text in the JSON object.
    :param: target_url (str): The URL of the page to scrape for new text.
    :param: script_name (str): The name of the script using this class.
    :param: element_h (str): The name of the HTML element to search for on the page.
    :param: upper_id (str): The value of the `id` attribute to search for in the HTML element.
    """
    product: str
    text_location: str
    text_key: str
    target_url: str
    script_name: str
    element_h: str
    upper_id: str

    def __post_init__(self) -> None:
        """
        Initializes logger configuration

        :return: None
        """
        self.logger = configure_logger(self.script_name)

    def check_cve(self) -> None:
        """
        Compares the original text with the text scraped from the target URL. If the text on the target URL has changed,
        replace old with the new text and posts a message to Slack.

        :return: None
        """
        upper_cve_text = get_upper_cve_text(self.target_url, self.element_h, self.upper_id)
        original_cve_text = get_json_value(self.text_location, self.text_key)

        if upper_cve_text == original_cve_text:
            self.logger.info(f'No change at: {self.target_url}. Upper CVE Text is: {upper_cve_text}.'
                             f' It is the same as Original CVE Text: {original_cve_text}.')
        else:
            self.logger.info(
                f'Check for new {self.product} CVE at {self.target_url}. New upper CVE Text is: {upper_cve_text}')
            slack_post(slack_channel='#atlassian-track-cve',
                       slack_message=f'Check for new {self.product} CVE at {self.target_url}\n'
                                     f'New upper CVE Text is: *{upper_cve_text}*')
            replace_json_value(self.text_location, self.text_key, upper_cve_text)


def main():
    """
    Instantiates a TrackCVE object for each argument in track_cve_args and calls its check_cve method.

    :return: None
    """
    for args in track_cve_args:
        track_cve = TrackCVE(**args, script_name=Path(__file__).stem)
        track_cve.check_cve()


if __name__ == "__main__":
    main()
