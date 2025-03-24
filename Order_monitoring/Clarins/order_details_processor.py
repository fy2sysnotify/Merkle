import logging
from datetime import datetime
import urllib3
from slack_sdk import WebClient
from webdav3.client import Client as WebDAVClient
from set_email import send_email
from decouple import config
from typing import Optional, List, Dict

# Log format for the logging system
log_format = '%(levelname)s %(asctime)s - %(message)s'


# Configuration class to store and manage script configuration details
class Config:
    """
    Stores configuration details for the script.

    Attributes:
        SCRIPT_NAME (Optional[str]): The name of the script.
        SLACK_TOKEN (str): Slack API token for authentication.
        EMAIL_RECIPIENT (str): Email address for sending notifications.
        WEBDAV_TIMEOUT (int): Timeout duration for WebDAV connections.
        WEBDAV_LOGIN (str): Username for WebDAV authentication.
        WEBDAV_PASSWORD (str): Password for WebDAV authentication.
    """

    SCRIPT_NAME: Optional[str] = None
    SLACK_TOKEN: str = config('SLACK_TOKEN')  # Load the Slack token from environment variables
    EMAIL_RECIPIENT: str = config('EMAIL_RECIPIENT')  # Load the Email recipient for notifications from environment variables
    WEBDAV_TIMEOUT: int = 300  # Default timeout for WebDAV connections
    WEBDAV_LOGIN: str = config('WEBDAV_LOGIN')  # Load the WebDAV login credentials from environment variables
    WEBDAV_PASSWORD: str = config('WEBDAV_PASSWORD')  # Load the WebDAV password credentials from environment variables

    @staticmethod
    def set_script_name(name: str) -> None:
        """
        Sets the script name and initializes logging.

        Args:
            name (str): The name of the script.

        Raises:
            Exception: If an error occurs while setting the script name.
        """

        try:
            # Set the script name and create a log file based on the current time
            Config.SCRIPT_NAME = name
            Config.SCRIPT_LOG_FILE = f'{name}_{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
            logging.basicConfig(filename=Config.SCRIPT_LOG_FILE, level=logging.DEBUG,
                                format=log_format)  # Initialize logging
        except Exception as e:
            print(f"Error setting script name: {e}")


# Create a logger instance for logging messages
logger = logging.getLogger()

# Disable SSL warnings for urllib3 (commonly used with WebDAV)
urllib3.disable_warnings()


# Logger Utility class for logging and printing messages
class Logger:
    """
    Provides utility methods for logging and printing messages.
    """

    @staticmethod
    def log_and_print(message: str) -> None:
        """
        Logs and prints a message.

        Args:
            message (str): The message to log and print.
        """
        try:
            print(message)  # Print the message to the console
            logger.info(message)  # Log the message using the logger
        except Exception as e:
            print(f"Error logging message: {e}")  # In case of error while logging


# Slack Notification Service class to handle sending Slack messages
class SlackNotifier:
    """
    Handles Slack notifications.

    Args:
        token (str): The Slack API token.
        channel (str): The Slack channel to send messages to.

    Attributes:
        client (WebClient): Slack WebClient instance.
        channel (str): The target Slack channel.
    """

    def __init__(self, token: str, channel: str) -> None:
        try:
            # Initialize the Slack WebClient with the provided API token
            self.client = WebClient(token=token)
            self.channel = channel
        except Exception as e:
            Logger.log_and_print(f"Error initializing SlackNotifier: {e}")  # Log any initialization errors

    def post_message(self, message: str) -> None:
        """
        Sends a message to the specified Slack channel.

        Args:
            message (str): The message to send.

        Raises:
            Exception: If the Slack API call fails.
        """

        try:
            # Send the message to the Slack channel
            self.client.chat_postMessage(channel=self.channel, text=message)
        except Exception as e:
            Logger.log_and_print(e)  # Log the error if Slack message fails
            try:
                # If Slack notification fails, try sending an email to the recipient
                send_email(
                    Config.EMAIL_RECIPIENT,
                    f'Slack bot in {Config.SCRIPT_NAME} failed',
                    f'{e}\nSlack bot in {Config.SCRIPT_NAME} failed. Please investigate.'
                )
            except Exception as email_error:
                Logger.log_and_print(f"Error sending email: {email_error}")  # Log if email fails


# WebDAV Service class to handle interactions with the WebDAV server
class WebDAVService:
    """
    Handles interactions with a WebDAV server.

    Args:
        hostname (str): The WebDAV server hostname.
        login (str): The WebDAV username.
        password (str): The WebDAV password.
        timeout (int): The timeout for WebDAV operations.

    Attributes:
        client (WebDAVClient): WebDAV client instance.
    """

    def __init__(self, hostname: str, login: str, password: str, timeout: int) -> None:
        try:
            # Initialize WebDAV client with the provided configuration
            self.client = WebDAVClient({
                'webdav_hostname': hostname,
                'webdav_login': login,
                'webdav_password': password,
                'webdav_timeout': timeout,
            })
            self.client.verify = False  # Disable SSL verification for WebDAV connections
        except Exception as e:
            Logger.log_and_print(f"Error initializing WebDAVService: {e}")  # Log initialization errors

    def get_filenames_with_info(self) -> List[Dict]:
        """
        Retrieves file information from the WebDAV server.

        Returns:
            List[Dict]: A list of file information dictionaries.

        Raises:
            Exception: If there is an error fetching filenames.
        """

        try:
            # Fetch and return the list of filenames with additional file information
            return self.client.list(get_info=True)
        except Exception as e:
            Logger.log_and_print(f"Error fetching filenames from WebDAV: {e}")  # Log any errors
            return []  # Return an empty list if fetching fails


# Order Processing class to check order status and inactivity
# noinspection PyDeprecation
class OrderChecker:
    """
    Checks the status of orders for a specific site.

    Args:
        site_id (str): The site identifier.
        orders_url (str): The URL for accessing orders.
        threshold (int): The time threshold for order inactivity.

    Attributes:
        site_id (str): The site identifier.
        orders_url (str): The orders URL.
        threshold (int): The inactivity threshold in hours.
        webdav_service (WebDAVService): WebDAV service instance.
    """

    def __init__(self, site_id: str, orders_url: str, threshold: int) -> None:
        try:
            # Initialize site ID, orders URL, threshold, and WebDAV service for file retrieval
            self.site_id = site_id
            self.orders_url = orders_url
            self.threshold = threshold
            self.webdav_service = WebDAVService(
                hostname=orders_url,
                login=Config.WEBDAV_LOGIN,
                password=Config.WEBDAV_PASSWORD,
                timeout=Config.WEBDAV_TIMEOUT
            )
        except Exception as e:
            Logger.log_and_print(f"Error initializing OrderChecker: {e}")  # Log initialization errors

    def get_last_order_timestamp(self) -> Optional[str]:
        """
        Gets the timestamp of the most recent order.

        Returns:
            Optional[str]: The timestamp of the last order, or None if no orders are found.
        """

        try:
            # Fetch the filenames with info and extract their creation timestamps
            filenames = self.webdav_service.get_filenames_with_info()
            timestamps = [item['created'] for item in filenames]
            return max(sorted(timestamps)) if timestamps else None  # Return the latest timestamp
        except Exception as e:
            Logger.log_and_print(f"Error retrieving last order timestamp: {e}")  # Log errors
            return None  # Return None if no orders found

    def check_time_difference(self) -> Optional[float]:
        """
        Calculates the time difference between the last order and the current time.

        Returns:
            Optional[float]: The time difference in hours, or None if no orders are found.
        """

        try:
            last_timestamp = self.get_last_order_timestamp()
            if not last_timestamp:
                return None  # Return None if no last order timestamp is found

            # Parse the last order timestamp and calculate the time difference in hours
            order_time = datetime.strptime(last_timestamp, '%Y-%m-%dT%H:%M:%SZ')
            Logger.log_and_print(f"Last order time for {self.site_id.upper()} is {order_time}.")
            current_time = datetime.utcnow()  # Get the current time in UTC
            return (current_time - order_time).total_seconds() / 3600  # Convert time difference to hours
        except Exception as e:
            Logger.log_and_print(f"Error calculating time difference: {e}")  # Log errors
            return None  # Return None in case of failure


# Main Execution class to monitor orders and send notifications
class OrderMonitor:
    """
    Monitors order activity and sends notifications for inactivity.

    Args:
        instances (Dict[str, int]): A dictionary mapping site IDs to inactivity thresholds.
        notifier (SlackNotifier): The SlackNotifier instance.
        orders_url (str): The URL for accessing orders.

    Attributes:
        instances (Dict[str, int]): Site IDs and their thresholds.
        notifier (SlackNotifier): SlackNotifier instance.
        orders_url (str): Orders URL.
    """

    def __init__(self, instances: Dict[str, int], notifier: SlackNotifier, orders_url: str) -> None:
        try:
            # Initialize the OrderMonitor with site IDs, thresholds, and Slack notifier
            self.instances = instances
            self.notifier = notifier
            self.orders_url = orders_url
        except Exception as e:
            Logger.log_and_print(f"Error initializing OrderMonitor: {e}")  # Log errors during initialization

    def run(self) -> None:
        """
        Executes the order monitoring process, checking each site for order activity.

        Raises:
            Exception: If an error occurs during monitoring.
        """

        try:
            # Iterate over each site and its threshold, and check for order inactivity
            for site_id, threshold in self.instances.items():
                checker: OrderChecker = OrderChecker(site_id, self.orders_url, threshold)

                Logger.log_and_print(f"Checking orders for {site_id.upper()}...")  # Log the start of the check
                time_difference = checker.check_time_difference()  # Get the time difference since the last order

                if time_difference is None:
                    Logger.log_and_print(f"No orders found for {site_id.upper()}.")  # Log if no orders are found
                    continue

                Logger.log_and_print(
                    f"Time difference for {site_id.upper()} is {time_difference:.2f} hours.")  # Log the time difference

                # If the inactivity exceeds the threshold, send a Slack message
                if time_difference > threshold:
                    message = (
                        f"No orders has been archived in Clarins *{site_id.removeprefix('clarins').upper()}* for more "
                        f"than *{int(time_difference)}* hours.\n"
                        "Please check the order flow as soon as possible.\n"
                        "Keep in mind that server and order timestamps are GMT."
                    )
                    self.notifier.post_message(message)  # Send the notification to Slack
        except Exception as e:
            Logger.log_and_print(f"Error in OrderMonitor run method: {e}")  # Log errors during the monitoring process
