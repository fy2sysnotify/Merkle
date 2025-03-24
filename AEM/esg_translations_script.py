from typing import List, Union
import pandas as pd
from dataclasses import dataclass


@dataclass
class TranslationRecord:
    original: str
    translations: List[str]


@dataclass
class TranslationConfig:
    excel_file_path: str
    cols: List[Union[str, None]]
    skip_rows: int


class Translator:
    """
    A class for translating text based on an Excel file with language translations.
    """

    def __init__(self, config: TranslationConfig) -> None:
        """
        Initialize a Translator instance with the provided configuration.

        Args:
            config (TranslationConfig): Configuration for the Translator.
        """
        self.excel_file_path = config.excel_file_path
        self.cols: List[Union[str, None]] = config.cols
        self.translations: List[TranslationRecord] = []

    def process_translations(self, page: dict, lang: int) -> None:
        """
        Process translations for a specific language.

        Args:
            page (dict): A dictionary representing a page or content to be translated.
            lang (int): The index of the target language in the 'cols' list.

        This method processes translations for a specific language and updates the content accordingly.
        """
        for key, value in page.items():
            if value is not None:
                val = value.lower()
                for record in self.translations:
                    if record.original is not None and record.translations[lang] is not None:
                        if val.find(record.original.lower()) != -1 and not record.original == record.translations[lang]:
                            print(f"Replacing {record.original} with {record.translations[lang]}")
                            value = value.replace(record.original, record.translations[lang])
                            page[key] = value

    def process_words(self, current: List[List[Union[str, None]]], value: str, pos: int) -> None:
        """
        Process words within a cell value.

        Args:
            current (List[List[Union[str, None]]]): A list of current translations.
            value (str): The cell value containing text to be processed.
            pos (int): The position (language index) in the 'cols' list.

        This method processes words within a cell value and updates the 'current' list with translated words.
        """
        parts = value.split("\n")
        for part in parts:
            if len(part) > 3:
                if len(current) <= pos:
                    current.append([None] * len(self.cols))
                current[pos][pos] = part.strip()

    def translate(self) -> None:
        """
        Entry point for translation processing.

        This method is responsible for reading the Excel file, processing translations,
        and managing the translation lists.
        """
        try:
            df = pd.read_excel(self.excel_file_path, header=None, skiprows=TranslationConfig.skip_rows)
            for index, row in df.iterrows():
                english_bits = row[4]
                if pd.notna(english_bits):
                    current: List[List[Union[str, None]]] = []
                    self.process_words(current, english_bits, 0)
                    for col, col_name in enumerate(self.cols[1:], start=1):
                        cell = row[col + 5]
                        if pd.notna(cell):
                            self.process_words(current, cell, col)
                    for words in current:
                        if words[0] and words[0] not in [record.original for record in self.translations]:
                            self.translations.append(TranslationRecord(words[0], words[1:]))
            self.translations.sort(key=lambda x: x.original if x.original else "")
            # You can print or further process the translations list as needed

        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """
    The main function for translating text using the Translator class.

    This function initializes the Translator with custom configuration and uses it to translate text.
    """
    # Customize the configuration
    custom_config: TranslationConfig = TranslationConfig(
        excel_file_path="/path/to/your/excel/file.xlsx",
        cols=["", "en", "", "uk", "fr", "", "de", "nl", "el", "",
              "da", "no", "fi", "sv", "is", "lt", "et", "lv", "hr",
              "mk", "sr", "sq", "bg", "cs", "hu", "sk", "sl", "ro", "",
              "pl", "es", "pt", "it"],
        skip_rows=7
    )

    # Create an instance of the Translator class with the custom configuration
    translator: Translator = Translator(custom_config)

    # Call the translate method to perform the translation
    translator.translate()


if __name__ == "__main__":
    main()
