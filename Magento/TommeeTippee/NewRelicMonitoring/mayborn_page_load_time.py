import time
from pathlib import Path
from typing import Any, Tuple, Optional
from decouple import config
from browser_setup_chrome import my_browser
from mayborn_websites import websites_list
from my_logger import configure_logger
from slack_messaging import slack_post

logger = configure_logger(script_name=Path(__file__).stem)


def setup_browser() -> Any:
    """
    Set up a web browser using the `my_browser` function.

    :return: The initialized web browser instance.
    :raises: Exception, if there is an error during browser setup.
    """
    try:
        driver = my_browser()
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Performance.enable', {})
        driver.execute_cdp_cmd('Page.enable', {})
        return driver
    except Exception as e:
        logger.error(f"Error setting up browser: {str(e)}")
        raise


def measure_page_load_time(driver: Any, url: str) -> Tuple[Any, float]:
    """
    Measure the page load time for a given URL using the provided web browser.

    :param driver: The web browser instance.
    :param url: The URL of the page to measure.
    :return: A tuple containing timeline data and total load time.
    :raises: Exception, if there is an error during page load time measurement.
    """
    try:
        start_time = time.perf_counter()
        driver.get(url)
        timeline_data = driver.execute_cdp_cmd('Performance.getMetrics', {})
        total_load_time = time.perf_counter() - start_time
        return timeline_data, total_load_time
    except Exception as e:
        logger.error(f"Error measuring page load time: {str(e)}")
        raise


def extract_metrics(timeline_data: Any) -> Tuple[float, float, float, float, float]:
    """
    Extract specific metrics from the timeline data.

    :param timeline_data: Timeline data obtained during page load time measurement.
    :return: Metrics extracted from the timeline data.
    :raises: Exception, if there is an error during metric extraction.
    """
    try:
        return (
            timeline_data['metrics'][3]['value'],  # Request start
            timeline_data['metrics'][4]['value'],  # Response start
            timeline_data['metrics'][6]['value'],  # DOM loading start
            timeline_data['metrics'][11]['value'],  # DOM interactive
            timeline_data['metrics'][10]['value']  # First Paint
        )
    except Exception as e:
        logger.error(f"Error extracting metrics: {str(e)}")
        raise


def log_metrics(url: str, total_load_time: float, metrics: Tuple[float, float, float, float, float]) -> None:
    """
    Log the extracted metrics for a given URL.

    :param url: The URL of the page.
    :param total_load_time: The total page load time.
    :param metrics: Extracted metrics.
    :raises: Exception, if there is an error during metric logging.
    """
    try:
        request_start, response_start, dom_loading_start, dom_interactive, first_paint = metrics

        log_message = (
            f'\n{"=" * 77}\n'
            f'URL: {url}\n'
            f'Total page load time: {total_load_time:.2f} seconds\n'
            f'Request start: {request_start:.2f} ms\n'
            f'Response start: {response_start:.2f} ms\n'
            f'DOM loading start: {dom_loading_start:.2f} ms\n'
            f'DOM interactive: {dom_interactive:.2f} ms\n'
            f'First Paint: {first_paint:.2f} ms\n'
            f'{"=" * 77}\n'
        )
        logger.debug(log_message)
    except Exception as e:
        logger.error(f"Error logging metrics: {str(e)}")
        raise


def send_slack_message(url: str, total_load_time: float, metrics: Tuple[float, float, float, float, float]) -> None:
    """
    Send a Slack message with the extracted metrics for a given URL.

    :param url: The URL of the page.
    :param total_load_time: The total page load time.
    :param metrics: Extracted metrics.
    :raises: Exception, if there is an error during Slack message sending.
    """
    try:
        if total_load_time > 1:
            request_start, response_start, dom_loading_start, dom_interactive, first_paint = metrics

            slack_message = (
                f'{"=" * 50}\n'
                f'{url}\n\n'
                f'Total page load time: *{total_load_time:.2f} seconds*\n\n'
                f'Request start: {request_start:.2f} ms\n'
                f'Response start: {response_start:.2f} ms\n'
                f'DOM loading start: {dom_loading_start:.2f} ms\n'
                f'DOM interactive: {dom_interactive:.2f} ms\n'
                f'First Paint: {first_paint:.2f} ms\n\n'
                f'Please check {config("CUSTOMER_NAME", default="")} for ongoing release/deployment\n'
                f'Examine Website Performance Monitoring at New Relic\n'
                f'{"=" * 50}\n'
            )

            slack_post(slack_channel='#mayborn-infra-monitoring', slack_message=slack_message)
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        raise


def get_page_load_timeline(url: str) -> None:
    """
    Measure page load time, extract metrics, log metrics, and send a Slack message for a given URL.

    :param url: The URL of the page.
    :raises: Exception, if there is an error during the process.
    """
    driver: Optional[Any] = None
    try:
        driver = setup_browser()

        timeline_data, total_load_time = measure_page_load_time(driver, url)
        metrics = extract_metrics(timeline_data)

        log_metrics(url, total_load_time, metrics)
        send_slack_message(url, total_load_time, metrics)
    except Exception as e:
        logger.error(f"Error in get_page_load_timeline: {str(e)}")
    finally:
        if driver:
            driver.quit()


for website in websites_list:
    get_page_load_timeline(website)
