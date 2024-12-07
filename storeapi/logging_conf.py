import logging
from logging.config import dictConfig

from storeapi.config import DevConfig, config


def obfuscated(email: str, obfuscated_length: int) -> str:
    characters = email[:obfuscated_length]
    first, last = email.split("@")
    return characters + ("*" * (len(first) - obfuscated_length)) + "@" + last


class EmailObfuscationFilter(logging.Filter):
    def __init__(self, name: str = "", obfuscated_length: int = 2) -> None:
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__:
            record.email = obfuscated(record.email, self.obfuscated_length)  # type: ignore
        return True


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(config, DevConfig) else 32,
                    "default_value": "-",
                },
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "obfuscated_length": 2 if isinstance(config, DevConfig) else 0,
                },
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "[%(correlation_id)s] %(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s %(msecs)03d %(levelname)-8s %(correlation_id)s %(name)s %(lineno)d %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "filename": "storeapi.log",
                    "formatter": "file",
                    "maxBytes": 1024 * 1024,  # 1 MB
                    "backupCount": 5,  # # of file to keep before deleting
                    "encoding": "utf-8",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
                "seq": {
                    "class": "seqlog.SeqLogHandler",
                    "level": "DEBUG",
                    "server_url": "http://localhost:5341",
                    "formatter": "file",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
            },
            "loggers": {
                "storeapi": {
                    "handlers": ["default", "rotating_file", "seq"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,  # this will prevent the logger from propagating to the root logger
                },
                "uvicorn": {
                    "handlers": ["default", "rotating_file", "seq"],
                    "level": "INFO",
                },
                "databases": {
                    "handlers": ["default", "rotating_file", "seq"],
                    "level": "WARNING",
                },
                "aiosqlite": {
                    "handlers": ["default", "rotating_file", "seq"],
                    "level": "WARNING",
                },
            },
        }
    )
