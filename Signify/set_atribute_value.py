from typing import Optional, Tuple
import xml.dom.minidom as minidom
import pandas as pd


def read_excel_to_dict(file_path, sheet, key_column, value_column):
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet)

        # Check if key_column and value_column exist in the DataFrame
        if key_column not in df.columns or value_column not in df.columns:
            print(f"Error: Key column '{key_column}' or value column '{value_column}' not found in the DataFrame.")
            return None

        # Create a dictionary by pairing only key and value from the same row where both are present
        result_dict = {}
        for index, row in df.iterrows():
            key = row[key_column]
            value = row[value_column]

            # Skip pairs with missing key or value
            if pd.notnull(key) and pd.notnull(value):
                result_dict[key] = value
            else:
                # Print warning for empty cells
                if pd.isnull(key):
                    print(f"Warning: Empty cell in Sheet: '{sheet}', Column '{key_column}' at row {index + 2}.")
                if pd.isnull(value):
                    print(f"Warning: Empty cell in Sheet: '{sheet}', Column '{value_column}' at row {index + 2}.")

        return result_dict

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None


def cell_value_below_found_substring(file_path, sheet, substring):
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)

        # Iterate through the DataFrame
        for col_name in df.columns:
            for index, cell_value in enumerate(df[col_name]):
                # Check if the cell contains the substring
                if pd.notna(cell_value) and substring in str(cell_value):
                    # Check if the substring is in the last row
                    if index == len(df) - 1:
                        return None  # Substring found in the last row, no cell below
                    # Get the value from the cell below the found substring
                    below_value = df.at[index + 1, col_name]
                    return str(below_value) if pd.notna(below_value) else None

        # If the substring is not found, return None
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def parse_path(path: str) -> Tuple[str, str]:
    parsed_element_tag, parsed_attribute_name = path.split('/', 1)
    return parsed_element_tag, parsed_attribute_name


def set_xml_attribute_value(xml_file_path: str, path: str, new_value: str) -> Optional[None]:
    try:
        # Parse the XML file using minidom
        dom = minidom.parse(xml_file_path)
        root = dom.documentElement

        # Parse the path using the separate function
        tag_name, attribute_name = parse_path(path)

        # Find the specific XML element
        element_list = root.getElementsByTagName(tag_name)

        if element_list:
            # Get the first occurrence of the specified XML element
            target_element = element_list[0]

            # Set the attribute value
            target_element.setAttribute(attribute_name, new_value)

            # Save the modified XML back to the file
            with open(xml_file_path, 'w', encoding='utf-8') as file:
                dom.writexml(file)

            print(f"Attribute value for {path} set to: {new_value}")
        else:
            print(f"{tag_name} element not found.")
    except FileNotFoundError:
        print(f"Error: File '{xml_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Example usage:
    file_name = "Case study page.xlsx"
    sheet_name = "Landing page briefing"

    result_dict_outer = read_excel_to_dict(file_name, "Mapping", "Source", "Destination")
    print(result_dict_outer)

    if result_dict_outer is not None:
        # Create a new dictionary to store the modified values
        modified_result_dict = {}

        # Loop through all keys in the dictionary
        for key_outer in result_dict_outer.keys():
            # Do something with each key
            substring_to_search = key_outer

            # Find the value below the substring in the sheet
            result_below_substring = cell_value_below_found_substring(file_name, sheet_name, substring_to_search)

            if result_below_substring is not None:
                # Replace the original key with the value found below the substring
                modified_result_dict[result_below_substring] = result_dict_outer[key_outer]
                print(f"Modified Value below '{substring_to_search}': {result_below_substring}")
            else:
                print(f"Substring '{substring_to_search}' not found in the Excel sheet.")

        # Print the modified dictionary
        print("Modified Dictionary:", modified_result_dict)
        for key_result_dict, value_result_dict in modified_result_dict.items():
            print(f"KEY: '{key_result_dict}', VALUE: '{value_result_dict}'")
            set_xml_attribute_value(xml_file_path='.content.xml', path=value_result_dict, new_value=key_result_dict)
