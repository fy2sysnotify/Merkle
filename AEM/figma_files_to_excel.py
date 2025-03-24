import os
import requests
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Union


@dataclass
class FigmaAPIResponse:
    """
        Represents a response from the Figma API.

        Attributes:
            status_code (int): The HTTP status code of the response.
            json_data (Dict[str, Union[str, List[Dict[str, Union[str, int]]]]): The JSON data returned by the API.
    """

    status_code: int
    json_data: Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]


@dataclass
class FigmaAPI:
    """
        Provides methods to interact with the Figma API.

        Attributes:
            api_token (str): The API token for authenticating with the Figma API.
    """

    api_token: str

    def get_project_files(self, project_url: str) -> FigmaAPIResponse:
        """
                Fetches project files from Figma using the provided project URL.

                Args:
                    project_url (str): The URL of the Figma project.

                Returns:
                    FigmaAPIResponse: An object representing the API response.

                Example:
                    figma_api = FigmaAPI('your_api_token')
                    response = figma_api.get_project_files('https://api.figma.com/v1/projects/figma_project_id/files')
        """

        headers = {'X-Figma-Token': self.api_token}
        response = requests.get(project_url, headers=headers)
        return FigmaAPIResponse(response.status_code, response.json())

    def get_file_data(self, file_url: str) -> FigmaAPIResponse:
        """
                Fetches data for a specific Figma file using the provided file URL.

                Args:
                    file_url (str): The URL of the Figma file.

                Returns:
                    FigmaAPIResponse: An object representing the API response.

                Example:
                    figma_api = FigmaAPI('your_api_token')
                    response = figma_api.get_file_data('https://api.figma.com/v1/files/your_file_key')
        """

        headers = {'X-Figma-Token': self.api_token}
        response = requests.get(file_url, headers=headers)
        return FigmaAPIResponse(response.status_code, response.json())


@dataclass
class FigmaDataCollector:
    """
        Collects data from Figma using the Figma API.

        Attributes:
            api_token (str): The API token for authenticating with the Figma API.
            all_data (List[Dict[str, Union[str, int]]]): A list to store collected data.
    """

    api_token: str
    all_data: List[Dict[str, Union[str, int]]]

    def collect_data(self, project_url: str) -> None:
        """
                Collects data from Figma project files and stores it in the 'all_data' attribute.

                Args:
                    project_url (str): The URL of the Figma project.

                Returns:
                    None

                Example:
                    collector = FigmaDataCollector('your_api_token', [])
                    collector.collect_data('https://api.figma.com/v1/projects/figma_project_id/files')
        """

        figma_api = FigmaAPI(self.api_token)
        response = figma_api.get_project_files(project_url)
        if response.status_code == 200:
            data = response.json_data
            for item in data['files']:
                key_value = item['key']
                file_url = f'https://api.figma.com/v1/files/{key_value}'
                file_response = figma_api.get_file_data(file_url)
                if file_response.status_code == 200:
                    file_data = file_response.json_data
                    self.all_data.append(file_data)


@dataclass
class DataExporter:
    """
        Exports collected data to an Excel file.

        Attributes:
            data (List[Dict[str, Union[str, int]]]): The data to be exported.
            excel_filename (str): The filename for the Excel export.
    """

    data: List[Dict[str, Union[str, int]]]
    excel_filename: str

    def export_to_excel(self) -> None:
        """
                Exports the collected data to an Excel file with the specified filename.

                Returns:
                    None

                Example:
                    data_exporter = DataExporter([], 'figma_data.xlsx')
                    data_exporter.export_to_excel()
        """

        if self.data:
            df = pd.json_normalize(self.data)
            df.to_excel(self.excel_filename, index=False)
            print(f"Data exported to {self.excel_filename}")
        else:
            print("No valid data found.")


def main() -> None:
    """
        The main function that orchestrates the data collection and export process.

        Returns:
            None

        Example:
            if __name__ == '__main__':
                main()
    """

    figma_api_token: str | None = os.getenv('FIGMA_API_TOKEN')
    figma_project_id: str | None = os.getenv('FIGMA_PROJECT_ID')
    figma_project_url: str = f'https://api.figma.com/v1/projects/{figma_project_id}/files'
    all_data: list = []
    collector: FigmaDataCollector = FigmaDataCollector(figma_api_token, all_data)
    collector.collect_data(figma_project_url)
    data_exporter: DataExporter = DataExporter(all_data, 'figma_data.xlsx')
    data_exporter.export_to_excel()


if __name__ == '__main__':
    main()
