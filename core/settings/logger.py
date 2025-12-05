from enum import Enum
from logging.config import dictConfig


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def setup_logging(settings=None) -> None:

    # Define different format if it is DEBUG or not to see
    # more details on the log
    LOG_LEVEL = LogLevel.DEBUG

    if LOG_LEVEL == LogLevel.DEBUG:
        log_format = "%(log_color)s [%(levelname)s] (%(module)s): %(message)s"
    else:
        log_format = "%(log_color)s [%(levelname)s]: %(message)s"

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # Colors on console
            "colored": {
                "()": "colorlog.ColoredFormatter",
                # "format": "%(log_color)s[%(asctime)s] [%(levelname)-8s] (%(module)s): %(message)s",
                # "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": log_format,
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] %(module)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            # Technical console (for debugging and errors)
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "level": LOG_LEVEL.name,
            },
        },
        "loggers": {
            # Main logger
            "app": {
                "handlers": ["console"],
                "level": LOG_LEVEL.name,
                "propagate": False,
            },
        },
    }

    dictConfig(LOGGING_CONFIG)
