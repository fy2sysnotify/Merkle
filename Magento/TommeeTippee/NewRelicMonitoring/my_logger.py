import logging
from datetime import datetime


def configure_logger(script_name: str) -> logging.Logger:
    """
    Configures the logger with the given script name.

    :rtype: object
    :param: script_name: The name of the script for which to configure the logger.
    :return: The configured logger instance.
    """
    log_format = '%(levelname)s %(asctime)s - %(message)s'
    script_log_file = f'{script_name}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
    logging.basicConfig(filename=script_log_file,
                        level=logging.DEBUG,
                        format=log_format)

    return logging.getLogger()
