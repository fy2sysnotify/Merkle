import os
from pathlib import Path
import json
import requests
import pandas as pd
from typing import Dict, Any
import logging
from my_logger import configure_logger
from slack_messaging import upload_to_slack
from client_creds_token import get_access_token
from instances_config import zwilling_instances
from request_orders_config import json_data


class OrderMonitor:
    """A class that monitors order information from Zwilling websites."""

    def __init__(self, site_id: str, logger: logging.Logger, excel_file_name: str):
        """
        Initializes an OrderMonitor instance.

        Args:
            site_id (str): The ID of the Zwilling instance to get order information from.
            logger (logging.Logger): A logger to use for logging events.
            excel_file_name (str): The name of the Excel file to save the order information to.
        """

        self.site_id = site_id
        self.logger = logger
        self.excel_file_name = excel_file_name
        self.access_token = get_access_token(
            os.getenv('ZWILLING_CLIENT_ID'),
            os.getenv('ZWILLING_CLIENT_PASS')
        )
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
        }

    def get_failed_orders(self) -> Dict[str, Any]:
        """
        Get a dictionary of failed orders.

        Returns:
            Dict[str, Any]: A dictionary containing the failed orders.
        """

        with requests.Session() as session:
            try:
                json_str = json.dumps(json_data)
                response = session.post(
                    f'https://www.zwilling.com/s/{self.site_id}/dw/shop/v22_10/order_search',
                    headers=self.headers, data=json_str)

                order_count = response.json()
            except requests.RequestException as e:
                self.logger.error(f'An error occurred while making the request: {e}')

        return order_count

    def export_failed_to_excel(self, data: dict) -> None:
        """
        Export the failed orders to an Excel file with Pandas library.

        Args:
            data (dict): A dictionary containing the failed orders to export.
        Returns:
            None
        """

        hits = data.get('hits')
        if hits:
            order_numbers = [hit['data']['order_no'] for hit in hits]
            df = pd.DataFrame(order_numbers, columns=['order_no'])
            df.to_excel(self.excel_file_name, index=False)
        else:
            self.logger.info('No hits found in data')

    def slack_notifier(self, failed_orders_count: int, country_id: str):
        """
        Notify the specified Slack channel about the failed orders in the given country.

        Args:
            failed_orders_count (int): The number of failed orders.
            country_id (str): The ID of the country.
        Returns:
            None
        """

        upload_to_slack(
            slack_channel='orders-monitor-zwilling',
            file_to_upload=self.excel_file_name,
            slack_comment=f'There were {failed_orders_count} failed orders in '
                          f'Zwilling {str(country_id).upper()}\n'
                          f'in the past 1 hour. Please investigate order flow.\n'
                          f'Keep in mind time zones difference.'
        )

    def cleanup_local_file(self) -> None:
        """
        Remove the Excel file containing the failed orders.

        Returns:
            None
        """

        os.remove(self.excel_file_name)

    def run_monitor(self) -> None:
        """
        Monitors the failed orders on the Zwilling instance
        specified by self.site_id and logs the results. If the
        number of failed orders exceeds the specified threshold,
        it exports the failed orders to an Excel file, uploads
        the file to Slack and remove it from local file system.

        Returns:
            None
        """

        failed_orders = self.get_failed_orders()
        failed_orders_count = str(failed_orders).count('failed')

        if failed_orders_count > zwilling_instances[self.site_id]:
            country_id = self.site_id.removeprefix('zwilling-')
            self.logger.info(
                f'{self.site_id} = {failed_orders}\nNumber of failed orders in '
                f'{self.site_id} = {failed_orders_count}'
            )
            self.export_failed_to_excel(failed_orders)
            self.slack_notifier(failed_orders_count, country_id)
            self.cleanup_local_file()
        else:
            self.logger.info(
                f'{self.site_id} = {failed_orders}\nNumber of failed orders in '
                f'{self.site_id} = {failed_orders_count}'
            )


def main() -> None:
    """
    Main entry point of the script. Initializes a logger and
    creates an OrderMonitor instance for each Zwilling website
    specified in zwilling_instances.

    Returns:
            None
    """
    logger = configure_logger(Path(__file__).stem)
    for site_id in zwilling_instances:
        order_monitor = OrderMonitor(site_id, logger, f'failed_orders_{site_id}.xlsx')
        order_monitor.run_monitor()


if __name__ == "__main__":
    main()
