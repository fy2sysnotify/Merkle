from typing import Optional, List
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
    NewRelicChecker class for monitoring the health status of hosts in a New Relic application.

    :param application_id(str): The ID of the New Relic application.
    :param user_api_key(str): User API key for authentication.
    :param new_relic_api(str): URL of the New Relic API.
    :param customer_name(str): Name of the customer associated with the New Relic application.
    :param logger(configure_logger): Logger for logging messages (default is configured using script_name).
    """

    application_id: str
    user_api_key: str
    new_relic_api: str
    customer_name: str
    logger: configure_logger = configure_logger(script_name=Path(__file__).stem)

    def _get_hosts_status(self) -> Optional[dict]:
        """
        Private method to fetch the status of hosts from the New Relic API.

        :return: A dictionary containing the response JSON or None if the request fails.
        :rtype: Optional[dict]
        """
        with httpx.Client() as client:
            client.headers.update({'accept': 'application/json', 'X-Api-Key': self.user_api_key})
            try:
                response = client.get(
                    f"{self.new_relic_api}applications/{self.application_id}/hosts.json"
                )
                response.raise_for_status()
                return response.json()
            except HTTPStatusError as e:
                self.logger.debug(f"Request failed with status code {e.response.status_code}.")
                return None
            except Exception as e:
                self.logger.error(f"Error while fetching hosts status: {str(e)}")
                return None

    def _process_unhealthy_hosts(self, response_json: dict) -> List[dict]:
        """
        Private method to process the response JSON and identify unhealthy hosts.

        :param response_json(dict): The response JSON from the New Relic API.
        :return(List[dict]): A list of dictionaries representing unhealthy hosts.
        """
        unhealthy_hosts_list = []

        for application_host in response_json.get('application_hosts', []):
            self.logger.info(application_host.get('host', 'N/A'))
            if application_host['health_status'] != 'green':
                unhealthy_hosts_list.append(application_host)

        return unhealthy_hosts_list

    def _notify_unhealthy_hosts(self, hosts_list: List[dict]) -> None:
        """
        Private method to notify about unhealthy hosts.

        :param hosts_list(List[dict]): A list of dictionaries representing unhealthy hosts.
        """
        if not hosts_list:
            self.logger.info(f"All {self.customer_name} hosts are green.")
        else:
            self.logger.info(
                f'{self.customer_name} hosts: ' + ', '.join(host['host'] for host in hosts_list) +
                ' status is not green (healthy). Log in to New Relic, Infrastructure section and focus on CPU, Memory '
                'and Disk metrics. Examine Logs section for further system status investigation.'
            )
            try:
                slack_post(
                    slack_channel='#mayborn-infra-monitoring',
                    slack_message=f'*{self.customer_name}* hosts: ' +
                                  ', '.join(host['host'] for host in hosts_list) +
                                  ' status is not healthy. \n'
                                  'Log in to New Relic, Infrastructure section and focus '
                                  'on CPU, Memory, and Disk metrics.\n'
                                  'Examine Logs section for further system status investigation.'
                )
            except Exception as e:
                self.logger.error(f"Error while notifying Slack: {str(e)}")

    def check_and_notify(self) -> None:
        """
        Public method to check the health status of hosts and notify if any are unhealthy.
        """
        response_json = self._get_hosts_status()
        if response_json is not None:
            unhealthy_hosts = self._process_unhealthy_hosts(response_json)
            self._notify_unhealthy_hosts(unhealthy_hosts)


def main() -> None:
    """
    Main function to instantiate NewRelicChecker and trigger the health check.

    :raises Exception: Any exception raised during the process.
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
