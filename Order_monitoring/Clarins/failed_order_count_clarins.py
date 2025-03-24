import os
from pathlib import Path
import json
import requests
from typing import Dict, Any
from my_logger import configure_logger
from slack_messaging import slack_post
from client_creds_token import get_access_token
from instances_config import clarins_instances
from request_orders_config import json_data

logger = configure_logger(Path(__file__).stem)

access_token = get_access_token(
    os.getenv("CLARINS_CLIENT_ID"),
    os.getenv("CLARINS_CLIENT_PASS")
)

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}',
}


def get_failed_orders(site_id: str) -> Dict[str, Any]:
    """
    Returns a dictionary of failed orders from the specified site.
    This function makes a request to the Clarins website to search for failed orders,
    and returns the results as a dictionary.

    :param site_id: The ID of the site to search for failed orders.
    :return: A dictionary of failed orders, with the order ID as the key and
             the order details as the value.
    """
    with requests.Session() as session:
        try:
            json_str = json.dumps(json_data)
            response = session.post(
                f'https://www.clarins.fr/s/{site_id}/dw/shop/v22_10/order_search',
                headers=headers, data=json_str)

            order_count = response.json()
        except requests.RequestException as e:
            logger.error(f'An error occurred while making the request: {e}')

    return order_count


def main() -> None:
    """
    The main function of the script.

    The function iterates through the clarins_instances and retrieves the failed orders for each site.
    It then counts the number of failed orders for each site and compares it to the corresponding
    value in the clarins_instances dict. If the number of failed orders is greater than the corresponding
    value in clarins_instances, it logs a message and sends a Slack notification with the details.
    :return: None
    """
    for site_id in clarins_instances:
        failed_orders = get_failed_orders(site_id)
        failed_orders_count = str(failed_orders).count("failed")

        if failed_orders_count > clarins_instances[site_id]:
            country_id = site_id.removeprefix('clarins')
            logger.info(f'{site_id} = {failed_orders}\nNumber of failed orders in {site_id} = {failed_orders_count}')
            slack_post(slack_channel='orders-monitor-clarins',
                       slack_message=f'There were *{failed_orders_count}* failed orders in '
                                     f'Clarins *{str(country_id).upper()}*\n'
                                     f'in the past *1* hour. Please investigate order flow.\n'
                                     f'Keep in mind time zones difference.')
        else:
            logger.info(f'{site_id} = {failed_orders}\nNumber of failed orders in {site_id} = {failed_orders_count}')


if __name__ == '__main__':
    main()
