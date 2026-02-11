import logging

from django.conf import settings


def get_logger() -> logging.Logger:
    """
    Get logger with name from settings or default to 'getpaid_elavon'.
    """
    elavon_settings = getattr(settings, "GETPAID_BACKEND_SETTINGS", {}).get("getpaid_elavon", {})
    logger_name = elavon_settings.get("logger_name", "getpaid_elavon")
    return logging.getLogger(logger_name)
