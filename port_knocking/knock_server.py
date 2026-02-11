#!/usr/bin/env python3
"""Starter template for the port knocking server."""

import argparse
import logging
import socket
import time
import subprocess
import threading

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0

client_states = {}


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def open_protected_port(protected_port, ip):
    """Open the protected port for the client IP."""
    logging.info(f"[+] Opening port {protected_port} for {ip}")
    subprocess.run([
        "iptables", "-I", "INPUT", "-p", "tcp",
        "--dport", str(protected_port), "-s", ip, "-j", "ACCEPT"
    ])


def close_protected_port(protected_port, ip):
    """Close the protected port (optional)."""
    logging.info(f"[-] Closing port {protected_port} for {ip}")
    subprocess.run([
        "iptables", "-D", "INPUT", "-p", "tcp",
        "--dport", str(protected_port), "-s", ip, "-j", "ACCEPT"
    ])


def handle_knock(ip, port, sequence, window, protected_port):
    now = time.time()

    if ip not in client_states:
        client_states[ip] = []

    # Remove old knocks
    client_states[ip] = [(p, t) for p, t in client_states[ip] if now - t < window]

    # Add new knock
    client_states[ip].append((port, now))
    current_sequence = [p for p, _ in client_states[ip]]

    logging.info(f"{ip} knocked on {port} | Progress: {current_sequence}")

    # Check correct sequence
    if current_sequence == sequence:
        logging.info(f"[+] Correct knock sequence from {ip}")
        open_protected_port(protected_port, ip)
        client_states[ip] = []  # reset


def listen_port(port, sequence, window, protected_port):
    """Listen for knocks on a specific port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    logging.info(f"Listening on knock port {port}")

    while True:
        conn, addr = s.accept()
        ip = addr[0]
        conn.close()
        handle_knock(ip, port, sequence, window, protected_port)


def listen_for_knocks(sequence, window_seconds, protected_port):
    logging.info(f"Knock sequence: {sequence}")
    logging.info(f"Protected port: {protected_port}")
    logging.info(f"Window: {window_seconds} seconds")

    # Block SSH by default
    subprocess.run([
        "iptables", "-A", "INPUT", "-p", "tcp",
        "--dport", str(protected_port), "-j", "DROP"
    ])

    # Start listeners for each knock port
    for port in sequence:
        threading.Thread(
            target=listen_port,
            args=(port, sequence, window_seconds, protected_port),
            daemon=True
        ).start()

    # Keep main thread alive
    while True:
        time.sleep(10)


def parse_args():
    parser = argparse.ArgumentParser(description="Port knocking server")
    parser.add_argument("--sequence", default="1234,5678,9012")
    parser.add_argument("--protected-port", type=int, default=2222)
    parser.add_argument("--window", type=float, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging()
    sequence = [int(p) for p in args.sequence.split(",")]
    listen_for_knocks(sequence, args.window, args.protected_port)


if __name__ == "__main__":
    main()