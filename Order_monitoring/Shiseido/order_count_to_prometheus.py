from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict
from decouple import config
import httpx
from slack_messaging import slack_post
from client_creds_token import get_access_token
from search_data_builder import build_search_data
from sites_ids import storefront_id_list


# Data class for managing access token retrieval
@dataclass
class AccessTokenProvider:
    """
    Manages retrieval of access token for authentication.

    This class facilitates the retrieval of an access token required for authentication
    with the retailer's API.

    :param client_id (str): The client ID used for authentication.
    :param client_secret (str): The client secret used for authentication.
    :param access_token_endpoint (str): The endpoint to retrieve the access token.
    """
    client_id: str
    client_secret: str
    access_token_endpoint: str

    def get_access_token(self) -> str:
        """
        Retrieves the access token.

        This method retrieves the access token using the provided client ID, client secret,
        and access token endpoint.

        :return: The retrieved access token as string.
        :raises Exception: If an error occurs during access token retrieval.
        """
        try:
            # Attempt to get the access token
            access_token = get_access_token(self.client_id, self.client_secret, self.access_token_endpoint)
            print('Access token retrieved successfully.')
            return access_token
        except Exception as e:
            # Log error and notify via Slack in case of failure
            print(f"Error getting access token: {e}")
            slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                       slack_message=f'Error getting access token in "{Path(__file__).stem}". Examine logs.')
            raise


# Data class for searching orders
@dataclass
class OrderSearcher:
    """
    Searches for orders on a retailer's website.

    This class is responsible for querying the retailer's API to search for orders
    based on specific criteria.

    :param retailer_website (str): The website of the retailer.
    :param search_order_endpoint (str): The endpoint for searching orders.
    :param token (str): The access token used for authentication.
    """
    retailer_website: str
    search_order_endpoint: str
    token: str

    def search_orders(self, site: str) -> int:
        """
        Searches for orders on the retailer's website for a specific site.

        This method performs a search for orders on the retailer's website for a
        specific site ID.

        :param: site (str): The ID of the site to search orders for.
        :return: The number of orders found as integer.
        :raises httpx.HTTPError: If an HTTP error occurs during the search.
        :raises Exception: For any other error during the search.
        """
        try:
            # Get current time and format it
            dt = (datetime.utcnow() - timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            print(f'Searching orders for site {site}...')
            print(f'Current time: {dt}')
            # Build search data
            search_data = build_search_data(dt)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            with httpx.Client() as client:
                # Make HTTP POST request to search for orders
                response = client.post(
                    f'{self.retailer_website}/s/{site}{self.search_order_endpoint}',
                    json=search_data,
                    headers=headers
                )
                response.raise_for_status()
                order_count = response.json()['hits']['total']
                print(f'Orders found for site {site}: {order_count}')
                return order_count
        except httpx.HTTPError as http_err:
            # Log HTTP error and notify via Slack
            print(f"HTTP error occurred: {http_err}")
            slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                       slack_message=f'HTTP error occurred in "{Path(__file__).stem}". Examine logs.')
            raise
        except Exception as e:
            # Log other errors and notify via Slack
            print(f"Error occurred during order search for site {site}: {e}")
            slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                       slack_message=f'Error occurred during order search for site {site} in '
                                     f'"{Path(__file__).stem}". Examine logs.')
            raise


# Data class for posting metrics
@dataclass
class MetricPoster:
    """
    Posts metrics to a Prometheus server.

    This class is responsible for posting metrics data to a Prometheus server.

    :param prometheus_metrics_url (str): The URL of the Prometheus server.
    """
    prometheus_metrics_url: str

    def post_metric(self, metric: str, value: int) -> None:
        """
        Posts a metric value to the Prometheus server.

        This method posts a metric value to the Prometheus server for monitoring.

        :param: metric (str): The name of the metric.
        :param: value (int): The value of the metric.
        :return: None
        :raises Exception: If an error occurs during metric posting.
        """
        try:
            # Prepare metric data
            metric_data = f"{metric} {value}"
            with httpx.Client() as client:
                # Post metric data to Prometheus
                client.post(self.prometheus_metrics_url, content=metric_data, headers={'Content-Type': 'text/plain'})
            print(f'Metric posted successfully: {metric} {value}')
        except Exception as e:
            # Log error and notify via Slack
            print(f"Error posting metric data: {e}")
            slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                       slack_message=f'Error posting metric data in "{Path(__file__).stem}". Examine logs.')
            raise


# Data class for processing orders
@dataclass
class OrderProcessor:
    """
    Processes orders for multiple sites.

    This class orchestrates the process of retrieving access tokens, searching for orders,
    and posting metrics for multiple sites.

    :param client_id (str): The client ID used for authentication.
    :param client_secret (str): The client secret used for authentication.
    :param access_token_endpoint (str): The endpoint for retrieving access token.
    :param website (str): The website of the retailer.
    :param search_order_endpoint (str): The endpoint for searching orders.
    :param prometheus_metrics_url (str): The URL of the Prometheus server for metrics posting.
    """
    client_id: str
    client_secret: str
    access_token_endpoint: str
    website: str
    search_order_endpoint: str
    prometheus_metrics_url: str

    def process_orders(self) -> None:
        """
        Processes orders for multiple sites.

        This method orchestrates the process of retrieving access tokens, searching for orders,
        and posting metrics for each site.

        :return: None
        """
        # Initialize AccessTokenProvider to get access token
        access_token_provider: AccessTokenProvider = AccessTokenProvider(
            self.client_id, self.client_secret, self.access_token_endpoint)
        token = access_token_provider.get_access_token()

        # Initialize OrderSearcher to search for orders
        order_searcher: OrderSearcher = OrderSearcher(self.website, self.search_order_endpoint, token)

        # Initialize MetricPoster to post metrics
        metric_poster: MetricPoster = MetricPoster(self.prometheus_metrics_url)

        # Iterate over sites and process orders
        for site in storefront_id_list:
            try:
                order_count = order_searcher.search_orders(site)
                metric = "metric_" + site
                metric_poster.post_metric(metric, order_count)
            except Exception as e:
                # Log error and notify via Slack, then continue with next site
                print(f"Error processing orders for site {site}: {e}")
                slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                           slack_message=f'Error processing orders for site {site} in '
                                         f'"{Path(__file__).stem}". Examine logs.')
                continue


# Main function to run the script
def main() -> None:
    """
    Main function to run the script.

    This function configures the logger, extracts configuration data, initializes the
    OrderProcessor, and processes orders.

    :return: None
    """

    # Extract configuration data
    config_data: Dict[str, str] = {
        'client_id': f'{config("CLIENT_ID", default="")}',
        'client_secret': f'{config("CLIENT_SECRET", default="")}',
        'access_token_endpoint': f'{config("DW_ACCESS_TOKEN_ENDPOINT", default="")}',
        'website': f'{config("WEBSITE", default="")}',
        'search_order_endpoint': f'{config("SEARCH_ORDER_ENDPOINT", default="")}',
        'prometheus_metrics_url': f'{config("PROMETHEUS_METRICS_URL", default="")}'
    }

    # Initialize OrderProcessor and process orders
    order_processor: OrderProcessor = OrderProcessor(**config_data)
    order_processor.process_orders()


# Entry point of the script
if __name__ == "__main__":
    main()
