import xml.dom.minidom as minidom
import pandas as pd
from typing import Optional


class ExcelProcessor:
    def __init__(self, excel_file_path: str, sheet_name: str, substring_to_search: str):
        """
        Initialize an ExcelProcessor instance.

        :param excel_file_path(str): Path to the Excel file.
        :param sheet_name(str): Name of the sheet in the Excel file.
        :param substring_to_search(str): Substring to search in the Excel columns.
        """
        self.df_excel = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        self.substring_to_search = substring_to_search
        self.extracted_text: Optional[str] = None

    def find_extracted_text(self) -> None:
        """
        Find the extracted text based on the provided substring in the Excel columns.
        Set the extracted_text attribute with the found text.
        """
        for column in self.df_excel.columns:
            option_b_index = self.df_excel[
                self.df_excel[column].apply(lambda cell: self.substring_to_search in str(cell))
            ].index

            if not option_b_index.empty and option_b_index[0] < len(self.df_excel) - 1:
                self.extracted_text = self.df_excel.loc[option_b_index[0] + 1, column]
                print(f"Extracted Text from Column '{column}':", self.extracted_text)
                break
            else:
                print(
                    f"No row containing '{self.substring_to_search}' found in Column '{column}' or it is in the last row."
                )

    def get_extracted_text(self) -> Optional[str]:
        """
        Get the extracted text.

        :return: Extracted text(Optional[str]).
        """
        return self.extracted_text


class XMLUpdater:
    def __init__(self, xml_file_path: str, extracted_text: str):
        """
        Initialize an XMLUpdater instance.

        :param xml_file_path(str): Path to the XML file.
        :param extracted_text(str): Text to be updated in the XML file.
        """
        self.xml_file_path = xml_file_path
        self.extracted_text = extracted_text

    def update_xml_content(self) -> None:
        """
        Update the XML content with the extracted text.
        """
        dom = minidom.parse(self.xml_file_path)
        root = dom.documentElement

        gc08_teasercontainer_elements = root.getElementsByTagName("gc08_teasercontainer_1572797269")

        if gc08_teasercontainer_elements:
            gc08_teasercontainer_element = gc08_teasercontainer_elements[0]
            cell1Component_gc11_elements = gc08_teasercontainer_element.getElementsByTagName("cell1Component-gc11")

            if cell1Component_gc11_elements:
                cell1Component_gc11_element = cell1Component_gc11_elements[0]

                current_body_value = cell1Component_gc11_element.getAttribute("body")
                print(f"Current 'body' value: {current_body_value}")

                cell1Component_gc11_element.setAttribute("body", self.extracted_text)

                with open(self.xml_file_path, 'w', encoding='utf-8') as file:
                    dom.writexml(file, encoding='utf-8')

                print(f"Updated XML content saved to '{self.xml_file_path}'.")
            else:
                print("cell1Component-gc11 element not found within gc08_teasercontainer_1572797269.")
        else:
            print("gc08_teasercontainer_1572797269 element not found.")


def main() -> None:
    """
    Main function to demonstrate the usage of ExcelProcessor and XMLUpdater classes.
    """
    excel_file_path = 'Case study page.xlsx'
    sheet_name = 'Landing page briefing'
    substring_to_search = 'Option B - text'
    xml_file_path = '.content.xml'

    excel_processor = ExcelProcessor(excel_file_path, sheet_name, substring_to_search)
    excel_processor.find_extracted_text()
    extracted_text = excel_processor.get_extracted_text()

    if extracted_text is not None:
        xml_updater = XMLUpdater(xml_file_path, extracted_text)
        xml_updater.update_xml_content()
    else:
        print("No extracted text found.")


if __name__ == "__main__":
    main()
