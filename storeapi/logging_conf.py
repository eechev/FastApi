from logging.config import dictConfig

from storeapi.config import DevConfig, config


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "filename": "storeapi.log",
                    "formatter": "file",
                    "maxBytes": 1024 * 1024,  # 1 MB
                    "backupCount": 5,  # # of file to keep before deleting
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "storeapi": {
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,  # this will prevent the logger from propagating to the root logger
                },
                "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
                "databases": {
                    "handlers": ["default", "rotating_file"],
                    "level": "WARNING",
                },
                "aiosqlite": {
                    "handlers": ["default", "rotating_file"],
                    "level": "WARNING",
                },
            },
        }
    )
