"""
Python code for processing Excel data and updating an XML file.

This script reads data from an Excel file, extracts specific information based on predefined substrings,
and updates an XML file with the extracted information.

"""

import xml.dom.minidom as minidom
import pandas as pd


def find_target_text(df: pd.DataFrame, substring_to_search: str) -> str:
    """
    Find the text in the DataFrame cell below the cell containing the specified substring.

    :param df: The DataFrame to search for the substring.
    :type df: pd.DataFrame

    :param substring_to_search: The substring to search for in the DataFrame.
    :type substring_to_search: str

    :return: The extracted text from the cell beneath the cell containing the specified substring,
             or an empty string if not found.
    :rtype: str
    """
    for column in df.columns:
        # Check if the substring is present in any cell of the column
        target_element_index = df[df[column].apply(lambda cell: substring_to_search in str(cell))].index
        if not target_element_index.empty and target_element_index[0] < len(df) - 1:
            # Extract the text from the cell beneath the cell containing the specified substring
            return str(df.loc[target_element_index[0] + 1, column])
    return ''


def replace_substring_in_file(filepath: str, target_substring: str, replacement_string: str) -> None:
    """
    Replace a specified substring in the content of a file and save the modified content back to the file.

    :param filepath: The path to the file.
    :type filepath: str

    :param target_substring: The substring to replace.
    :type target_substring: str

    :param replacement_string: The string to replace the target substring with.
    :type replacement_string: str

    :return(None): None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            file_content = file.read()
        # Replace the target substring with the replacement string
        modified_content = file_content.replace(target_substring, replacement_string)
        with open(filepath, 'w', encoding='utf-8') as file:
            # Write the modified content back to the file
            file.write(modified_content)
        print(f"Substring '{target_substring}' replaced with '{replacement_string}' in '{filepath}'.")
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def update_xml_attribute(xml_file_path: str, element_tag: str, attribute_name: str, new_value: str) -> None:
    """
    Update the value of an attribute in an XML file for a specific XML element.

    :param xml_file_path: The path to the XML file.
    :type xml_file_path: str

    :param element_tag: The tag of the XML element to update.
    :type element_tag: str

    :param attribute_name: The name of the attribute to update.
    :type attribute_name: str

    :param new_value: The new value for the attribute.
    :type new_value: str

    :return(None): None
    """
    try:
        # Parse the XML file using minidom
        dom = minidom.parse(xml_file_path)
        root = dom.documentElement
        # Find the specific XML element
        element_list = root.getElementsByTagName(element_tag)

        if element_list:
            # Get the first occurrence of the specified XML element
            target_element = element_list[0]
            # Update the value of the specified attribute
            target_element.setAttribute(attribute_name, new_value)

            with open(xml_file_path, 'w', encoding='utf-8') as file:
                # Overwrite the original XML file with the updated content
                dom.writexml(file, encoding='utf-8')

            print(f"Updated {attribute_name} attribute in {element_tag}. XML content saved to '{xml_file_path}'.\n"
                  f"New value is: {new_value}")
        else:
            print(f"{element_tag} element not found.")
    except FileNotFoundError:
        print(f"Error: File '{xml_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Read the Excel file
excel_file_path = 'Case study page.xlsx'
df_excel: pd.DataFrame = pd.read_excel(excel_file_path, sheet_name='Landing page briefing')

# Specify the substrings to search for
substring_to_search_image: str = 'Introduction image'
substring_to_search_text: str = 'Introduction text'
substring_to_search_heading: str = 'Introduction heading'
substring_to_search_country: str = 'City/Country'

# Find the target text for each substring
extracted_text_image: str = find_target_text(df_excel, substring_to_search_image)
extracted_text_text: str = find_target_text(df_excel, substring_to_search_text)
extracted_text_heading: str = find_target_text(df_excel, substring_to_search_heading)
extracted_text_country: str = find_target_text(df_excel, substring_to_search_country)

# Combine extracted texts
final_text: str = f'{extracted_text_heading} {extracted_text_country}'

# Replace substrings in XML file
replace_substring_in_file('.content.xml', 'sartorius-introduction-image', extracted_text_image)
update_xml_attribute('.content.xml', 'cell1Component-gc11', 'body', extracted_text_text)
update_xml_attribute('.content.xml', 'cell1Component-gc11', 'title', final_text)
