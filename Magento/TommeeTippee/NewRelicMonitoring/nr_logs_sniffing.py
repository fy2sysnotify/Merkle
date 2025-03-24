import httpx
from decouple import config
from pathlib import Path
from typing import List, Dict
from my_logger import configure_logger
from generate_nrql_query import count_all_client_ips, count_client_ip
from slack_messaging import slack_post, upload_to_slack
from slack_text import generate_slack_message
from white_lists import ip_list

# Configuring logger
logger = configure_logger(script_name=Path(__file__).stem)


def fetch_data_from_api(query: str) -> Dict[str, any]:
    """
    Fetch data from an API using HTTP POST request.

    This function sends a POST request to the specified GraphQL API endpoint with the provided query.
    It expects a JSON response and extracts the data from it.

    :param query: The NRQL query to be executed.
    :type query: str
    :return: The JSON response containing the queried data.
    :rtype: dict
    """
    try:
        # Fetching API endpoint URL and user API key from environment variables
        url = config('GRAPH_QL_API', default='')
        headers = {'Api-Key': config('USER_API_KEY', default='')}
        payload = {'query': query}

        # Sending HTTP POST request to the API endpoint
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload)

            # Extracting JSON data from the response
            return response.json()['data']['actor']['account']['nrql']['results']
    except httpx.HTTPError as e:
        logger.error(f"Error fetching data from API: {e}")
        slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                   slack_message=f'Error fetching data from API in "{Path(__file__).stem}". Examine logs...{e}')
        raise


def accumulate_counts(results: List[Dict[str, any]]) -> Dict[str, int]:
    """
    Accumulate counts of client IPs from the query results.

    This function takes a list of dictionaries containing query results.
    It accumulates the counts of client IPs from these results.

    :param results: List of dictionaries containing query results.
    :type results: list
    :return: A dictionary where keys are client IPs and values are counts.
    :rtype: dict
    """
    ip_counts = {}
    try:
        for result in results:
            client_ip = result['client_ip']
            count = result['count']

            # Accumulating counts for each client IP
            if client_ip in ip_counts:
                ip_counts[client_ip] += count
            else:
                ip_counts[client_ip] = count
        return ip_counts
    except Exception as e:
        logger.error(f"Error accumulating counts: {e}")
        slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                   slack_message=f'Error accumulating counts in "{Path(__file__).stem}". Examine logs...{e}')
        raise


def print_counts(ip_counts: Dict[str, int], interval: int) -> None:
    """
    Print counts of client IPs.

    This function takes a dictionary containing counts of client IPs and prints them.
    It also prints the specified time interval for which the counts are calculated.

    :param ip_counts: A dictionary where keys are client IPs and values are counts.
    :type ip_counts: dict
    :param interval: The time interval for which counts are calculated.
    :type interval: int
    """
    try:
        for ip, count in ip_counts.items():
            print("Client IP:", ip)
            print(f"Count for last {interval}:", count)
    except Exception as e:
        logger.error(f"Error printing counts: {e}")
        slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                   slack_message=f'Error printing counts in "{Path(__file__).stem}". Examine logs...{e}')


def process_data(interval_1: int, interval_2: int) -> None:
    """
    Process data for two different time intervals.

    This function processes data for two different time intervals.
    It retrieves data for the first interval, checks if the count for any client IP exceeds a threshold,
    and if so, retrieves additional data for the second interval and sends a Slack message.

    :param interval_1: The time interval in minutes for the first query.
    :type interval_1: int
    :param interval_2: The time interval in minutes for the second query.
    :type interval_2: int
    """
    try:
        account_id = config('ACCOUNT_ID', default='')

        # Generating NRQL query for the first interval and fetching data from the API
        query_1 = count_all_client_ips(account_id, interval_1, 'MINUTES')
        results_1 = fetch_data_from_api(query_1)

        # Accumulating counts for the first interval
        ip_counts_1 = accumulate_counts(results_1)

        # Iterating through each client IP and count for the first interval
        for ip, count_1 in ip_counts_1.items():
            # Checking if the count exceeds a threshold
            if count_1 > 300 and ip not in ip_list:
                print("Client IP:", ip)
                print("Count for last 10 minutes:", count_1)

                # Generating NRQL query for the second interval with the specific client IP
                query_2 = count_client_ip(account_id, interval_2, 'MINUTES', ip)

                # Fetching data for the second interval with the specific client IP
                results_2 = fetch_data_from_api(query_2)

                # Accumulating counts for the second interval
                ip_counts_2 = accumulate_counts(results_2)

                # Printing counts for the second interval
                print_counts(ip_counts_2, interval_2)

                try:
                    # Uploading data to Slack if available
                    upload_to_slack(
                        slack_channel=f'#{config("SLACK_MONITOR_CHANNEL", default="")}',
                        file_to_upload='nr_me.jpg',
                        slack_comment=generate_slack_message(count_1, ip_counts_2.get(ip, 0))
                    )
                except Exception as e:
                    logger.error(f'Could not upload to Slack. Sending only text to Slack.: {e}')
                    # Posting to Slack if uploading fails
                    slack_post(
                        slack_channel=f'#{config("SLACK_MONITOR_CHANNEL", default="")}',
                        slack_message=generate_slack_message(count_1, ip_counts_2.get(ip, 0))
                    )
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        slack_post(slack_channel=f'#{config("SLACK_ERRORS_CHANNEL", default="")}',
                   slack_message=f'Error processing data in "{Path(__file__).stem}". Examine logs...{e}')
        raise


def main() -> None:
    # Processing data for time intervals 10 minutes and 60 minutes
    process_data(10, 60)


if __name__ == '__main__':
    main()
