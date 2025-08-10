import logging

LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/app.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - [%(name)s] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "()": "logging.Formatter",
            "fmt": "%(levelname)s: %(asctime)s - [%(name)s] - %(module)s.%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "formatter": "file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE,
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 10,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
