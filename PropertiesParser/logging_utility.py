from abc import ABCMeta, abstractmethod
import logging
import threading
from pathlib import Path
from datetime import datetime


class SingletonMeta(metaclass=ABCMeta):
    """
    Metaclass for implementing the Singleton design pattern.

    This metaclass ensures that only one instance of a class is created and
    provides thread-safe access to that instance.

    Attributes:
        _instances (dict): A dictionary that holds the instances of the classes.
        _lock (threading.Lock): A lock object for thread-safety.
    """

    _instances: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs) -> object:
        """
        Callable method that creates and returns the instance of the class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The instance of the class.
        """
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseLogger(SingletonMeta):
    """
    Abstract base class for loggers.

    This class defines the interface for loggers and enforces the Singleton pattern
    so that only one instance of each logger subclass can exist.
    """

    @abstractmethod
    def debug(cls, message: str) -> None:
        """
        Log a debug message.

        Args:
            message (str): The message to be logged.
        """
        pass

    @abstractmethod
    def info(cls, message: str) -> None:
        """
        Log an info message.

        Args:
            message (str): The message to be logged.
        """
        pass

    @abstractmethod
    def warning(cls, message: str) -> None:
        """
        Log a warning message.

        Args:
            message (str): The message to be logged.
        """
        pass

    @abstractmethod
    def error(cls, message: str) -> None:
        """
        Log an error message.

        Args:
            message (str): The message to be logged.
        """
        pass

    @abstractmethod
    def critical(cls, message: str) -> None:
        """
        Log a critical message.

        Args:
            message (str): The message to be logged.
        """
        pass


class MyLogger(BaseLogger):
    """
    Concrete logger implementation.

    This class provides logging capabilities using the Python logging module.

    Attributes:
        _logger (logging.Logger): The logger object.
    """

    def __init__(self, module_name: str, log_filename: str) -> None:
        """
        Initialize the MyLogger instance.

        Args:
            module_name (str): The name of the module.
            log_filename (str): The path to the log file.
        """
        self._logger: logging.Logger = logging.getLogger(module_name)
        self._logger.setLevel(logging.DEBUG)
        file_handler: logging.FileHandler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message (str): The message to be logged.
        """
        self._logger.debug(message)

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message (str): The message to be logged.
        """
        self._logger.info(message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message (str): The message to be logged.
        """
        self._logger.warning(message)

    def error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message (str): The message to be logged.
        """
        self._logger.error(message)

    def critical(self, message: str) -> None:
        """
        Log a critical message.

        Args:
            message (str): The message to be logged.
        """
        self._logger.critical(message)


# Example usage:
logger: MyLogger = MyLogger(
    module_name=Path(__file__).stem,
    log_filename=f'{Path(__file__).stem}_{datetime.now().strftime("%Y%m%d")}.log'
)
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')
