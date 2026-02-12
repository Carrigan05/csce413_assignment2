#!/usr/bin/env python3
"""Starter template for the honeypot assignment."""

import socket
import threading
import time
from logger import create_logger, log_auth_attempt, log_command

HOST = "0.0.0.0"  
PORT = 22       

logger = create_logger()

BANNER = "SSH-2.0-OpenSSH_7.9p1 FakeSSH_1.0\r\n"

# Logs login attempts and fake shell commands
def handle_client(client_socket, address):
    ip, port = address
    logger.info(f"Connection from {ip}:{port}")
    
    try:
        # Send SSH banner
        client_socket.send(BANNER.encode())

        # Receive attempted username/password
        client_socket.send(b"Username: ")
        username = client_socket.recv(1024).decode().strip()

        client_socket.send(b"Password: ")
        password = client_socket.recv(1024).decode().strip()

        # Log authentication attempt (always fail for realism)
        log_auth_attempt(logger, ip, port, username, password, success=False)

        # Fake shell interaction
        client_socket.send(b"\r\nWelcome to FakeSSH!\r\n")
        while True:
            client_socket.send(b"$ ")
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break
            log_command(logger, ip, command)
            client_socket.send(b"Command not found\r\n")

    except Exception as e:
        logger.error(f"Error with {ip}:{port} - {e}")
    finally:
        client_socket.close()
        logger.info(f"Connection closed {ip}:{port}")


def run_honeypot():
    logger.info("Starting SSH honeypot...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    logger.info(f"Honeypot listening on {HOST}:{PORT}")

    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr))
            thread.start()
    except KeyboardInterrupt:
        logger.info("Honeypot shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    run_honeypot()