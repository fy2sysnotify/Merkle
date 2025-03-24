import logging
from datetime import datetime


def configure_logger(script_name: str) -> logging.Logger:
    """
    Configures the logger with the given script name.

    Args:
        script_name (str): The name of the script for which to configure the logger.

    Returns:
        logging.Logger: The configured logger instance.
    """

    log_format = '%(levelname)s %(asctime)s - %(message)s'
    formatter = logging.Formatter(log_format)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    script_log_file = f'{script_name}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
    file_handler = logging.FileHandler(script_log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
