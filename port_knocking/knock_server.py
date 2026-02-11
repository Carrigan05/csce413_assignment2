#!/usr/bin/env python3
"""Starter template for the port knocking server."""

import argparse
import logging
import socket
import threading
import time

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0

# Track which clients completed the knock sequence
clients_allowed = set()
clients_progress = {}  # {IP: [(port, timestamp), ...]}

lock = threading.Lock()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

def protected_port_server(protected_port):
    """Simulated protected port server (just TCP listener)."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("", protected_port))
    server_sock.listen(5)
    logging.info(f"[*] Protected port {protected_port} listening (simulation)")

    while True:
        client_sock, addr = server_sock.accept()
        ip = addr[0]
        with lock:
            if ip in clients_allowed:
                client_sock.sendall(b"Access granted!\n")
                logging.info(f"[+] Allowed access from {ip}")
            else:
                client_sock.sendall(b"Access denied!\n")
                logging.info(f"[-] Denied access from {ip}")
        client_sock.close()

def knock_listener(sequence, window_seconds):
    """Listen for knock sequence on UDP ports."""
    logger = logging.getLogger("KnockServer")

    # Create UDP sockets for each knock port
    sockets = []
    for port in sequence:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", port))
        sockets.append(sock)

    logger.info(f"Listening for knocks on ports {sequence}")
    while True:
        for sock, expected_port in zip(sockets, sequence):
            sock.settimeout(0.1)
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                now = time.time()

                with lock:
                    if ip not in clients_progress:
                        clients_progress[ip] = []

                    clients_progress[ip].append((expected_port, now))
                    # Keep only recent knocks in the window
                    clients_progress[ip] = [
                        (p, t) for p, t in clients_progress[ip] if now - t <= window_seconds
                    ]

                    ports = [p for p, _ in clients_progress[ip]]
                    if ports[-len(sequence):] == sequence:
                        logger.info(f"[+] {ip} completed knock sequence!")
                        clients_allowed.add(ip)
                        clients_progress[ip] = []

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

    # Start protected port server in a separate thread
    t = threading.Thread(target=protected_port_server, args=(args.protected_port,), daemon=True)
    t.start()

    # Start knock listener (main thread)
    knock_listener(sequence, args.window)

if __name__ == "__main__":
    main()