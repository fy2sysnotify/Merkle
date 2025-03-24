import tempfile
import base64
from typing import Optional, Tuple
import xml.dom.minidom as minidom
import pandas as pd
import openpyxl
import streamlit as st


def read_excel_to_dict(file_path, sheet, key_column, value_column):
    """
    Read an Excel file and create a dictionary based on specified columns.

    :param file_path: Path to the Excel file.
    :param sheet: Sheet name in the Excel file.
    :param key_column: Column containing keys.
    :param value_column: Column containing values.
    :return: Dictionary created from the specified columns.
    """
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet)

        # Check if key_column and value_column exist in the DataFrame
        if key_column not in df.columns or value_column not in df.columns:
            st.error(f"Error: Key column '{key_column}' or value column '{value_column}' not found in the DataFrame.")
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
                    st.error(f"Warning: Empty cell in Sheet: '{sheet}', Column '{key_column}' at row {index + 2}.")
                if pd.isnull(value):
                    st.error(f"Warning: Empty cell in Sheet: '{sheet}', Column '{value_column}' at row {index + 2}.")
        return result_dict

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None


def get_excel_cell_value(excel_file_name, target_sheet, target_cell_number):
    """
    Get the concatenated value of specified cells in an Excel sheet.

    :param excel_file_name: Path to the Excel file.
    :param target_sheet: Sheet name in the Excel file.
    :param target_cell_number: Cell numbers separated by "\\".
    :return: Concatenated value of specified cells.
    """
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
        st.error(f"Error: {e}")
        return None


def parse_path(path: str) -> Tuple[str, str]:
    """
    Parse the path into element tag and attribute name.

    :param path: Path in the format "tag/attribute".
    :return: Tuple containing element tag and attribute name.
    """
    parsed_element_tag, parsed_attribute_name = path.split('/', 1)
    return parsed_element_tag, parsed_attribute_name


def set_xml_attribute_value(xml_file_path: str, path: str, new_value: str) -> Optional[None]:
    """
    Set the value of an attribute in an XML file.

    :param xml_file_path: Path to the XML file.
    :param path: Path in the format "tag/attribute".
    :param new_value: New value for the attribute.
    :return: None.
    """
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

            st.info(f"Attribute value for {path} set to: {new_value}")
        else:
            st.info(f"{tag_name} element not found.")
    except FileNotFoundError:
        st.error(f"Error: File '{xml_file_path}' not found.")
    except Exception as e:
        st.error(f"An error occurred: {e}")


def main():
    """
    Main function for the XML Attribute Setter Streamlit app.
    """
    st.title("XML Attribute Setter")
    st.sidebar.header("File Upload")
    file_name = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
    xml_file = st.sidebar.file_uploader("Upload XML File", type=["xml"])

    uploaded_files = {"Excel File": file_name, "XML File": xml_file}
    st.sidebar.text("Uploaded Files:")
    for file_type, file_upload in uploaded_files.items():
        if file_upload is not None:
            st.sidebar.text(f"{file_type}: {file_upload.name}")

    if file_name and xml_file:
        # Save the uploaded XML file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as temp_xml:
            temp_xml.write(xml_file.read())
            xml_file_path = temp_xml.name

        sheet_name = st.text_input("Enter Sheet Name", value="Landing page briefing")
        process_files_button = st.button("Process Files")
        if process_files_button:
            try:
                result_dict_outer = read_excel_to_dict(file_name, "Mapping", "Source", "Destination")

                if result_dict_outer is not None:
                    # Create a new dictionary to store the modified values
                    modified_result_dict = {}

                    # Loop through all keys in the dictionary
                    for key_outer in result_dict_outer.keys():
                        # Map the key from the dictionary as a cell number
                        cell_number = key_outer

                        # Find the value of the cell number
                        founded_cell_value = get_excel_cell_value(file_name, sheet_name, cell_number)

                        if founded_cell_value is not None:
                            # Replace the original key with the value found below the substring
                            modified_result_dict[founded_cell_value] = result_dict_outer[key_outer]
                        else:
                            st.warning(f"Cell number '{cell_number}' not found in the Excel sheet.")

                    # Print the modified dictionary
                    st.info(modified_result_dict)

                    for key_result_dict, value_result_dict in modified_result_dict.items():
                        # Iterate through the modified dictionary to set XML attribute values
                        set_xml_attribute_value(
                            xml_file_path=xml_file_path,  # Path to the modified XML file
                            path=value_result_dict,  # Path in the format "tag/attribute" from the modified dictionary
                            new_value=key_result_dict  # New value for the attribute from the modified dictionary
                        )

                    # Download button for the modified XML
                    download_link(xml_file_path)

                else:
                    st.error("Error: Unable to process Excel file.")
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")


def download_link(file_path):
    """
    Create a download link for the modified XML file.

    :param file_path: Path to the modified XML file.
    """
    try:
        with open(file_path, 'rb') as file:
            contents = file.read()
            b64 = base64.b64encode(contents).decode('utf-8')
            href = f'<a href="data:application/xml;base64,{b64}" download="modified.xml">Click here to download the modified XML file</a>'
            st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error occurred during download link creation: {e}")


if __name__ == "__main__":
    main()
