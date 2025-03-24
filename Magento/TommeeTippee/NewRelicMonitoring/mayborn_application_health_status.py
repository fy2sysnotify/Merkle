from typing import Optional
from dataclasses import dataclass
from pathlib import Path
import httpx
from httpx import HTTPStatusError
from decouple import config
from my_logger import configure_logger
from slack_messaging import slack_post


@dataclass
class NewRelicChecker:
    """
    NewRelicChecker class for checking the health status of an application on New Relic.

    Attributes:
    - application_id (str): The ID of the application on New Relic.
    - user_api_key (str): User API key for authentication.
    - new_relic_api (str): Base URL for the New Relic API.
    - customer_name (str): Name of the customer for logging and messaging.
    - logger (configure_logger): Logger instance for logging.
    """

    application_id: str
    user_api_key: str
    new_relic_api: str
    customer_name: str
    logger: configure_logger = configure_logger(script_name=Path(__file__).stem)

    def _get_application_status(self) -> Optional[str]:
        """
        Get the health status of the application from New Relic using a context manager.

        Returns:
        - str: The health status of the application, or None if an error occurs.
        """
        with httpx.Client() as client:
            client.params.merge({'filter[ids]': self.application_id})
            client.headers.update({'Accept': 'application/json', 'X-Api-Key': self.user_api_key})
            try:
                response = client.get(f"{self.new_relic_api}/applications.json")
                response.raise_for_status()
                app_data = response.json()
                return app_data['applications'][0]['health_status'] if app_data else None
            except HTTPStatusError as e:
                self.logger.debug(f"Request failed with status code {e.response.status_code}.")
                return None
            except Exception as e:
                self.logger.error(f"Error while fetching application status: {str(e)}")
                return None

    def check_and_notify(self):
        """
        Check the application status on New Relic and notify if necessary.

        Logs the application status and sends a notification to Slack if the status is not 'green'.
        """
        app_status = self._get_application_status()

        if app_status == 'green' or app_status.lower() == 'none':
            self.logger.info(f"Application status of {self.customer_name} is {app_status}")
        else:
            self.logger.info(f"Application status of {self.customer_name} is {app_status}")
            self._notify_slack(app_status)

    def _notify_slack(self, app_status: str):
        """
        Notify Slack about the application status.

        Parameters:
        - app_status (str): The health status of the application.
        """
        try:
            slack_post(
                slack_channel='#mayborn-infra-monitoring',
                slack_message=f"Application status of {self.customer_name} is *{app_status}*.\n"
                              f"Check email for updates on deployment/release.\n"
                              f"Log in to New Relic, Infrastructure section and focus on CPU, Memory, Disk metrics\n"
                              f"Examine Logs section for system status."
            )
        except Exception as e:
            self.logger.error(f"Error while notifying Slack: {str(e)}")


def main() -> None:
    """
    Entry point of the script for checking and notifying about the New Relic application status.

    Reads configuration values for New Relic API authentication and the target application.
    Initializes NewRelicChecker, checks the application status, logs the status, and notifies Slack if necessary.

    Handles exceptions during initialization, logging, and HTTP client usage.
    """
    checker: NewRelicChecker = NewRelicChecker(
        application_id=config('APPLICATION_ID', default=''),
        user_api_key=config('USER_API_KEY', default=''),
        new_relic_api=config('NEW_RELIC_API', default=''),
        customer_name=config('CUSTOMER_NAME', default='')
    )

    try:
        checker.check_and_notify()
    except Exception as e:
        print(f"Error in main function: {str(e)}")


if __name__ == "__main__":
    main()
