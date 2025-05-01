
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_PATH = "/home/gafarybyh/elephant_agent_bot/logs/app.log"

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": LOG_FORMAT
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "level": "INFO",
            "filename": LOG_PATH
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        
        # 🔧 Limit log from external library
        # Level (DEBUG 10, INFO 20, WARNING 30, ERROR 40, CRITICAL 50)	
        "telegram": {"level": "INFO", "propagate": False}, # Only INFO until CRITICAL
    }
}

