import urllib3
from datetime import datetime
from pathlib import Path
from typing import List
from webdav3.client import Client as webdavClient
from my_logger import configure_logger
import constants as const
from slack_messaging import slack_post


zwilling_instances = dict(us=2, jp=8)


def webdav_get_filenames() -> List:
    """
    This function connects to the WebDAV directory using the specified
    hostname, login, password, and timeout in the `webdav_options` dictionary.

    :return: A list of nested files and directories for remote WebDAV directory by path.
    """
    urllib3.disable_warnings()
    webdav_options = {
        'webdav_hostname': site_orders_url,
        'webdav_login': const.my_ods_email,
        'webdav_password': const.my_ods_pass,
        'webdav_timeout': 300
    }
    webdav = webdavClient(webdav_options)
    webdav.verify = False

    return webdav.list(get_info=True)


def last_order_timestamp() -> str:
    """
    Returns the timestamp of the last order in the webdav storage.

    :return: String
    """
    timestamps_list: List[str] = [item['created'] for item in webdav_get_filenames()]
    return sorted(timestamps_list)[-1]


def check_time_difference() -> float:
    """
    Calculate the time difference in hours between the timestamp of the last order and the current time.

    :return: Difference in float
    """
    order_timestamp = datetime.strptime(last_order_timestamp(), '%Y-%m-%dT%H:%M:%SZ')
    current_timestamp = datetime.now()
    difference = current_timestamp - order_timestamp
    return difference.total_seconds() / 3600


for site_id in zwilling_instances:
    logger = configure_logger(Path(__file__).stem)
    site_orders_url = f'{const.zwilling_prod}{const.orders_url}{site_id}{const.order_archive}'
    time_difference = check_time_difference()
    logger.info(f'Time difference for Zwilling {site_id.upper()} is {time_difference}')

    if time_difference > zwilling_instances[site_id]:
        slack_post(slack_channel='orders-monitor-zwilling',
                   slack_message=f'No orders has been archived in Zwilling *{str(site_id).upper()}* '
                                 f'for more than *{int(time_difference)}* hours.\n '
                                 f'Please check the order flow as soon as possible.\n '
                                 f'Keep in mind that server and orders timestamps are GMT.')
    else:
        logger.info(f'Last order timestamp in Zwilling '
                    f'{str(site_id).upper()} is {last_order_timestamp()}')
