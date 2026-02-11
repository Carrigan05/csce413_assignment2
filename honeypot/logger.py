"""Logging helpers for the honeypot."""

import logging
import os

LOG_DIR = "/app/logs"
LOG_FILE = os.path.join(LOG_DIR, "honeypot.log")

def create_logger():
    """Create and return a configured logger object."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("Honeypot")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if reloaded
    if logger.handlers:
        return logger

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialized.")
    return logger

def log_auth_attempt(logger, ip, port, username, password, success=False):
    status = "SUCCESS" if success else "FAIL"
    logger.info(
        f"Authentication attempt from {ip}:{port} | "
        f"user='{username}' password='{password}' | {status}"
    )

def log_command(logger, ip, command):
    logger.info(f"Command from {ip}: {command}")
