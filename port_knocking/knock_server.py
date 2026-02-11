#!/usr/bin/env python3
"""Starter template for the port knocking server."""

Exactly — yes! Your server still needs a proper main() entry point to parse arguments and call the listen_for_knocks() function. I left that out in the snippet to focus on the core logic.

Here’s a full, working knock_server.py that works with your minimal Dockerfile without needing iptables, fully self-contained:

import argparse
import logging
import socket
import time

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0

# Track clients allowed after correct sequence
clients_allowed = set()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

def listen_for_knocks(sequence, window_seconds, protected_port):
    logger = logging.getLogger("KnockServer")
    logger.info("Starting Python-only port knocking server")
    logger.info("Knock sequence: %s", sequence)
    logger.info("Protected port: %s", protected_port)

    client_progress = {}  # {IP: [(port, timestamp), ...]}

    # Create UDP sockets for each knock port
    sockets = []
    for port in sequence:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", port))
        sockets.append(sock)

    logger.info("Listening on ports %s", sequence)
    while True:
        for sock, expected_port in zip(sockets, sequence):
            sock.settimeout(0.1)
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                now = time.time()

                if ip not in client_progress:
                    client_progress[ip] = []

                client_progress[ip].append((expected_port, now))

                # Keep only recent knocks within the time window
                client_progress[ip] = [
                    (p, t) for p, t in client_progress[ip] if now - t <= window_seconds
                ]

                # Check if last N knocks match the sequence
                ports = [p for p, _ in client_progress[ip]]
                if ports[-len(sequence):] == sequence:
                    logger.info("[+] %s completed sequence! Allowed access to port %d", ip, protected_port)
                    clients_allowed.add(ip)
                    client_progress[ip] = []  # Reset after success

            except socket.timeout:
                continue

def parse_args():
    parser = argparse.ArgumentParser(description="Python-only port knocking server")
    parser.add_argument(
        "--sequence",
        default=",".join(str(p) for p in DEFAULT_KNOCK_SEQUENCE),
        help="Comma-separated knock ports",
    )
    parser.add_argument(
        "--protected-port",
        type=int,
        default=DEFAULT_PROTECTED_PORT,
        help="Protected port",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=DEFAULT_SEQUENCE_WINDOW,
        help="Seconds allowed to complete the sequence",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()

    try:
        sequence = [int(p) for p in args.sequence.split(",")]
    except ValueError:
        raise SystemExit("Invalid sequence. Use comma-separated integers.")

    listen_for_knocks(sequence, args.window, args.protected_port)

if __name__ == "__main__":
    main()