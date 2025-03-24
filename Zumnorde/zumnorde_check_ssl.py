import os
import socket
import ssl
import datetime
import logging_utility
from slack_messaging import slack_post

domains_url = [
    'host1',
    'host1',
    'etc',
]


def check_ssl_expiry(hostname: str, logger) -> None:
    """
    Check the expiration date of the SSL certificate for a given hostname.
    If the certificate is about to expire within 10 days, send a message
    to Slack and log the expiration date and number of days until expiration.
    Otherwise, just log the expiration date and number of days until expiration.

    :param: hostname (str): The hostname to check the SSL certificate for.
    :param: logger: The logger to use for logging messages.
    :return: None
    """
    ssl_dateformat = r'%b %d %H:%M:%S %Y %Z'

    context = ssl.create_default_context()
    context.check_hostname = False

    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )

    conn.settimeout(5.0)

    conn.connect((hostname, 443))
    ssl_info = conn.getpeercert()

    expire = datetime.datetime.strptime(ssl_info['notAfter'], ssl_dateformat)
    now = datetime.datetime.now()
    diff = expire - now

    if diff.days < 10:
        slack_post(
            f'SSL for Domain name: {hostname} Expiry Date: {expire.strftime("%Y-%m-%d")} Expiry Day: {diff.days}')
        logger.debug(
            f'SSL for Domain name: {hostname} Expiry Date: {expire.strftime("%Y-%m-%d")} Expiry Day: {diff.days}')
    else:
        logger.debug(
            f'SSL for Domain name: {hostname} Expiry Date: {expire.strftime("%Y-%m-%d")} Expiry Day: {diff.days}')


def main():
    """
    Check the expiration dates of the SSL certificates for all websites in
    the 'domains_url' list.

    :return: None
    """
    logger = logging_utility.get_logger(os.path.basename(__file__))
    for web_site in domains_url:
        try:
            check_ssl_expiry(web_site, logger)
        except Exception as e:
            logger.debug(e)


if __name__ == "__main__":
    main()
