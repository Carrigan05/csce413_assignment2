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

# Track allowed IPs
allowed_ips = set()
# Track knock progress per IP
client_state = {}

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

def handle_knock(port, sequence, window_seconds, protected_port):
    """Listen for knocks on a single port."""
    logger = logging.getLogger("KnockServer")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(5)
    logger.info(f"Listening for knocks on port {port}")

    while True:
        conn, addr = sock.accept()
        ip = addr[0]
        now = time.time()

        # Initialize state for IP
        if ip not in client_state:
            client_state[ip] = {"progress": 0, "start": now}

        state = client_state[ip]

        # Reset if timeout exceeded
        if now - state["start"] > window_seconds:
            state["progress"] = 0
            state["start"] = now

        expected = sequence[state["progress"]]

        if port == expected:
            state["progress"] += 1
            logger.info(f"[+] {ip} correct knock {port} ({state['progress']}/{len(sequence)})")

            # Completed sequence
            if state["progress"] == len(sequence):
                logger.info(f"[+] {ip} completed knock sequence! Access granted to port {protected_port}")
                allowed_ips.add(ip)
                state["progress"] = 0
        else:
            state["progress"] = 0
            state["start"] = now

        conn.close()

def protected_service(port):
    """Simple TCP service that only allows approved IPs."""
    logger = logging.getLogger("KnockServer")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(5)
    logger.info(f"Protected service listening on port {port}")

    while True:
        conn, addr = sock.accept()
        ip = addr[0]

        if ip in allowed_ips:
            logger.info(f"[+] {ip} connected to protected port!")
            conn.sendall(b"Welcome! You completed the knock sequence.\n")
        else:
            logger.warning(f"[-] {ip} blocked from protected port")
            conn.sendall(b"Access denied. Perform knock sequence first.\n")

        conn.close()

def listen_for_knocks(sequence, window_seconds, protected_port):
    """Start knock listeners and the protected service."""
    # Start protected service thread
    t = threading.Thread(target=protected_service, args=(protected_port,), daemon=True)
    t.start()

    # Start a listener thread per knock port
    for port in sequence:
        t = threading.Thread(target=handle_knock, args=(port, sequence, window_seconds, protected_port), daemon=True)
        t.start()

    # Keep main thread alive
    while True:
        time.sleep(1)

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
        help="Port to protect",
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
    sequence = [int(p) for p in args.sequence.split(",")]
    listen_for_knocks(sequence, args.window, args.protected_port)

if __name__ == "__main__":
    main()
