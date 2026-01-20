from logging.config import dictConfig
from core.config.settings import Settings


def setup_logging(settings: Settings | None = None) -> None:

    # Define different format if it is DEBUG or not to see
    # more details on the log
    settings = settings or Settings()
    LOG_LEVEL = settings.LOG_LEVEL

    log_format = (
        "%(log_color)s [%(levelname)s] (%(module)s): %(message)s"
        if LOG_LEVEL.value == "DEBUG"
        else "%(log_color)s [%(levelname)s]: %(message)s"
    )

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # Colors on console
            "colored": {
                "()": "colorlog.ColoredFormatter",
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
            "core": {"handlers": ["console"], "level": LOG_LEVEL.name, "propagate": False},
            "mining": {"handlers": ["console"], "level": LOG_LEVEL.name, "propagate": False},
            "__main__": {"handlers": ["console"], "level": LOG_LEVEL.name, "propagate": False},
        },
    }

    dictConfig(LOGGING_CONFIG)
