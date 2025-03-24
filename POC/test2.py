import xml.dom.minidom as minidom
import pandas as pd

# Read the Excel file
excel_file_path = 'Case study page.xlsx'
df_excel = pd.read_excel(excel_file_path, sheet_name='Landing page briefing')

# Specify the substrings to search for
substring_to_search = 'Introduction image'

# Initialize extracted_text outside the loop
extracted_text = None
image_target_text = 'sartorius-introduction-image'

# Iterate over columns and find the index of the row where the cell contains the specified substring
for column in df_excel.columns:
    target_element_index = df_excel[df_excel[column].apply(lambda cell: substring_to_search in str(cell))].index

    # Check if the index is found and not at the last row
    if not target_element_index.empty and target_element_index[0] < len(df_excel) - 1:
        # Extract the text from the cell beneath the cell containing the specified substring
        extracted_text = df_excel.loc[target_element_index[0] + 1, column]
        print(f"Extracted Text from Excel Column '{column}':", extracted_text)
        break  # Stop the loop once the substring is found in a column
    else:
        print(f"No row containing '{substring_to_search}' found in Excel Column '{column}' or it is in the last row.")


def replace_substring_in_file(filepath, target_substring, replacement_string):
    try:
        # Read the content of the file
        with open(filepath, 'r',encoding='utf-8') as file:
            file_content = file.read()

        # Replace the target substring with the replacement string
        modified_content = file_content.replace(target_substring, replacement_string)

        # Write the modified content back to the file
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(modified_content)

        print(f"Substring '{target_substring}' replaced with '{replacement_string}' in '{filepath}'.")

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
file_path = '.content.xml'  # Replace with your file path
target_substring = image_target_text
replacement_string = extracted_text

replace_substring_in_file(file_path, target_substring, replacement_string)

substring_to_search = 'Introduction text'

# Iterate over columns and find the index of the row where the cell contains the specified substring
for column in df_excel.columns:
    target_element_index = df_excel[df_excel[column].apply(lambda cell: substring_to_search in str(cell))].index

    # Check if the index is found and not at the last row
    if not target_element_index.empty and target_element_index[0] < len(df_excel) - 1:
        # Extract the text from the cell beneath the cell containing the specified substring
        extracted_text = df_excel.loc[target_element_index[0] + 1, column]
        print(f"Extracted Text from Excel Column '{column}':", extracted_text)
        break  # Stop the loop once the substring is found in a column
    else:
        print(f"No row containing '{substring_to_search}' found in Excel Column '{column}' or it is in the last row.")

# Check if extracted_text is not None
if extracted_text is not None:
    xml_file_path = '.content.xml'

    # Parse the XML file using minidom
    dom = minidom.parse(xml_file_path)

    # Get the root element
    root = dom.documentElement

    # Find the specific gc08_teasercontainer_248922064 element
    gc08_teasercontainer_elements = root.getElementsByTagName("gc08_teasercontainer_248922064")

    if gc08_teasercontainer_elements:
        gc08_teasercontainer_element = gc08_teasercontainer_elements[0]

        # Find the specific cell1Component-gc11 element within the parent
        cell1Component_gc11_elements = gc08_teasercontainer_element.getElementsByTagName("cell1Component-gc11")

        if cell1Component_gc11_elements:
            cell1Component_gc11_element = cell1Component_gc11_elements[0]

            # Print the current "body" value before updating
            current_body_value = cell1Component_gc11_element.getAttribute("body")
            print(f"Current 'body' value: {current_body_value}")

            # Update the value of the body attribute
            cell1Component_gc11_element.setAttribute("body", extracted_text)

            # Overwrite the original XML file with the updated content
            with open(xml_file_path, 'w', encoding='utf-8') as file:
                dom.writexml(file, encoding='utf-8')

            print(f"Updated XML content saved to '{xml_file_path}'.")
        else:
            print("cell1Component-gc11 element not found within gc08_teasercontainer_248922064.")
    else:
        print("gc08_teasercontainer_248922064 element not found.")
else:
    print("No extracted text found.")


substring_to_search = 'Introduction heading'

# Iterate over columns and find the index of the row where the cell contains the specified substring
for column in df_excel.columns:
    target_element_index = df_excel[df_excel[column].apply(lambda cell: substring_to_search in str(cell))].index

    # Check if the index is found and not at the last row
    if not target_element_index.empty and target_element_index[0] < len(df_excel) - 1:
        # Extract the text from the cell beneath the cell containing the specified substring
        extracted_text = df_excel.loc[target_element_index[0] + 1, column]
        print(f"Extracted Text from Excel Column '{column}':", extracted_text)
        break  # Stop the loop once the substring is found in a column
    else:
        print(f"No row containing '{substring_to_search}' found in Excel Column '{column}' or it is in the last row.")

first_part = extracted_text

substring_to_search = 'City/Country'

# Iterate over columns and find the index of the row where the cell contains the specified substring
for column in df_excel.columns:
    target_element_index = df_excel[df_excel[column].apply(lambda cell: substring_to_search in str(cell))].index

    # Check if the index is found and not at the last row
    if not target_element_index.empty and target_element_index[0] < len(df_excel) - 1:
        # Extract the text from the cell beneath the cell containing the specified substring
        extracted_text = df_excel.loc[target_element_index[0] + 1, column]
        print(f"Extracted Text from Excel Column '{column}':", extracted_text)
        break  # Stop the loop once the substring is found in a column
    else:
        print(f"No row containing '{substring_to_search}' found in Excel Column '{column}' or it is in the last row.")

final_text = f'{first_part} {extracted_text}'
print(f'Final Text: {final_text}')

# Check if extracted_text is not None
if extracted_text is not None:
    xml_file_path = '.content.xml'

    # Parse the XML file using minidom
    dom = minidom.parse(xml_file_path)

    # Get the root element
    root = dom.documentElement

    # Find the specific gc08_teasercontainer_248922064 element
    gc08_teasercontainer_elements = root.getElementsByTagName("gc08_teasercontainer_248922064")

    if gc08_teasercontainer_elements:
        gc08_teasercontainer_element = gc08_teasercontainer_elements[0]

        # Find the specific cell1Component-gc11 element within the parent
        cell1Component_gc11_elements = gc08_teasercontainer_element.getElementsByTagName("cell1Component-gc11")

        if cell1Component_gc11_elements:
            cell1Component_gc11_element = cell1Component_gc11_elements[0]

            # Print the current "body" value before updating
            current_body_value = cell1Component_gc11_element.getAttribute("title")
            print(f"Current 'body' value: {current_body_value}")

            # Update the value of the body attribute
            cell1Component_gc11_element.setAttribute("title", final_text)

            # Overwrite the original XML file with the updated content
            with open(xml_file_path, 'w', encoding='utf-8') as file:
                dom.writexml(file, encoding='utf-8')

            print(f"Updated XML content saved to '{xml_file_path}'.")
        else:
            print("cell1Component-gc11 element not found within gc08_teasercontainer_248922064.")
    else:
        print("gc08_teasercontainer_248922064 element not found.")
else:
    print("No extracted text found.")
