#!/usr/bin/env python3
"""Starter template for the honeypot assignment."""

import logging
import os
import socket
import time

LOG_PATH = "/app/logs/honeypot.log"


def setup_logging():
    os.makedirs("/app/logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    )


def run_honeypot():
    logger = logging.getLogger("Honeypot")
    logger.info("SSH Honeypot starting...")

    HOST = "0.0.0.0"
    PORT = 22

    # Create fake SSH server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)

    logger.info(f"Listening on {HOST}:{PORT}")

    while True:
        client, addr = s.accept()
        start_time = time.time()
        logger.info(f"Connection from {addr[0]}:{addr[1]}")

        try:
            # Send fake SSH banner
            client.send(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n")
            time.sleep(1)

            # Fake login prompts
            client.send(b"login: ")
            username = client.recv(1024).decode(errors="ignore").strip()

            client.send(b"Password: ")
            password = client.recv(1024).decode(errors="ignore").strip()

            # Log credentials
            logger.warning(f"AUTH ATTEMPT user={username} pass={password} from {addr[0]}")

            # Fake rejection
            client.send(b"Permission denied, please try again.\r\n")

        except Exception as e:
            logger.error(f"Error handling {addr}: {e}")

        finally:
            client.close()
            duration = time.time() - start_time
            logger.info(f"Connection from {addr[0]} closed after {duration:.2f}s")


if __name__ == "__main__":
    setup_logging()
    run_honeypot()