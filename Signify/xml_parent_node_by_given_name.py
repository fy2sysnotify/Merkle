from typing import List, Union
from bs4 import BeautifulSoup, PageElement


def print_parent_nodes(xml_file: str, tag_name: str) -> None:
    """
    Print the parent nodes of elements with a given tag name in an XML file.

    :param xml_file: The path to the XML file to be parsed.
    :type xml_file: str
    :param tag_name: The tag name to search for in the XML file.
    :type tag_name: str
    :return: None
    """
    try:
        with open(xml_file, 'r', encoding='utf-8') as file:
            # Parse the XML file using BeautifulSoup
            soup = BeautifulSoup(file, 'xml')

            # Find all elements with the given tag name
            elements = soup.find_all(tag_name)

            for element in elements:
                parents: List[Union[str, None]] = []
                parent: Union[PageElement, None] = element

                # Traverse the tree upward and collect parent node names
                while parent is not None and getattr(parent, 'name', None) != '[document]':
                    parents.append(parent.name) if hasattr(parent, 'name') else parents.append(None)
                    parent = parent.find_parent()

                parents.reverse()
                print("Parent nodes for '{}' element: {}".format(tag_name, " -> ".join(str(p) for p in parents)))

    except Exception as e:
        print("Error parsing XML file: {}".format(e))


if __name__ == "__main__":
    xml_file_name = ".content.xml"
    tag_to_search = 'cell1Component-gc11'
    print_parent_nodes(xml_file_name, tag_to_search)
