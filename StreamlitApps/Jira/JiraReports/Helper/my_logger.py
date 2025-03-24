import logging
from datetime import datetime


def configure_logger(script_name: str) -> logging.Logger:
    """
    Configures the logger with the given script name.

    :param script_name: The name of the script for which to configure the logger.
    :type script_name: str

    :return: The configured logger instance.
    :rtype: logging.Logger

    This function configures a logger for a script and sets up the logging format.
    It creates a log file specific to the script with a timestamp in the filename.
    The logger is configured to write log messages to the specified log file and has a level of DEBUG.
    """

    log_format = '%(levelname)s %(asctime)s - %(message)s'
    script_log_file = f'{script_name}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
    logging.basicConfig(filename=script_log_file,
                        level=logging.DEBUG,
                        format=log_format)

    return logging.getLogger()
