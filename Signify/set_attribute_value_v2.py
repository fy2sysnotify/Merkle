from typing import Optional, Tuple
import xml.dom.minidom as minidom
import pandas as pd
import openpyxl


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


def get_excel_cell_value(excel_file_name, target_sheet, target_cell_number):
    try:
        # Load the Excel workbook
        workbook = openpyxl.load_workbook(excel_file_name)

        # Select the specified sheet
        sheet = workbook[target_sheet]

        # Split the target cell numbers by "\"
        cells = target_cell_number.split("\\")

        # Get values for each specified cell and concatenate them
        cell_values = [sheet[cell].value for cell in cells]

        # Close the workbook
        workbook.close()

        # Concatenate values with "\"
        content_value = " ".join(str(cell_value) for cell_value in cell_values)

        return content_value

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
            # Map the key from dictionary as a cell number
            cell_number = key_outer

            # Find the value of the cell number
            founded_cell_value = get_excel_cell_value(file_name, sheet_name, cell_number)

            if founded_cell_value is not None:
                # Replace the original key with the value found below the substring
                modified_result_dict[founded_cell_value] = result_dict_outer[key_outer]
                print(f"Modified Value of '{cell_number}': {founded_cell_value}")
            else:
                print(f"Cell number '{cell_number}' not found in the Excel sheet.")

        # Print the modified dictionary
        print("Modified Dictionary:", modified_result_dict)
        for key_result_dict, value_result_dict in modified_result_dict.items():
            print(f"KEY: '{key_result_dict}', VALUE: '{value_result_dict}'")
            set_xml_attribute_value(xml_file_path='.content.xml', path=value_result_dict, new_value=key_result_dict)
