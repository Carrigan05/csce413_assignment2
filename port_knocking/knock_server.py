#!/usr/bin/env python3
"""Starter template for the port knocking server."""

import argparse
import logging
import socket
import threading
import time
import subprocess

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

def block_port(port):
    """Block the protected SSH port for all IPs initially."""
    subprocess.run(["iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "DROP"])
    logging.info(f"[*] Port {port} blocked for all IPs")

def allow_ip(ip, port):
    """Allow a specific IP to access the SSH port."""
    subprocess.run(["iptables", "-I", "INPUT", "-p", "tcp", "-s", ip, "--dport", str(port), "-j", "ACCEPT"])
    logging.info(f"[+] {ip} is now allowed to access port {port}")

def knock_listener(sequence, window_seconds, protected_port):
    """Listen for knock sequence on UDP ports."""
    logger = logging.getLogger("KnockServer")

    # Create UDP sockets for each knock port
    sockets = []
    for port in sequence:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", port))
        sockets.append(sock)

    logger.info(f"[*] Listening for knocks on ports {sequence}")

    while True:
        for sock, expected_port in zip(sockets, sequence):
            sock.settimeout(0.1)
            try:
                _, addr = sock.recvfrom(1024)
                ip = addr[0]
                now = time.time()

                with lock:
                    if ip not in clients_progress:
                        clients_progress[ip] = []

                    clients_progress[ip].append((expected_port, now))
                    # Keep only recent knocks in the window
                    clients_progress[ip] = [(p, t) for p, t in clients_progress[ip] if now - t <= window_seconds]

                    ports = [p for p, _ in clients_progress[ip]]
                    if ports[-len(sequence):] == sequence and ip not in clients_allowed:
                        logger.info(f"[+] {ip} completed knock sequence!")
                        clients_allowed.add(ip)
                        allow_ip(ip, protected_port)
                        clients_progress[ip] = []

            except socket.timeout:
                continue

def parse_args():
    parser = argparse.ArgumentParser(description="Port knocking server for SSH")
    parser.add_argument(
        "--sequence",
        default=",".join(str(p) for p in DEFAULT_KNOCK_SEQUENCE),
        help="Comma-separated knock ports",
    )
    parser.add_argument(
        "--protected-port",
        type=int,
        default=DEFAULT_PROTECTED_PORT,
        help="Protected SSH port",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=DEFAULT_SEQUENCE_WINDOW,
        help="Seconds allowed to complete the knock sequence",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()

    try:
        sequence = [int(p) for p in args.sequence.split(",")]
    except ValueError:
        raise SystemExit("Invalid sequence. Use comma-separated integers.")

    # Block SSH port initially
    block_port(args.protected_port)

    # Listen for knock sequence (main thread)
    knock_listener(sequence, args.window, args.protected_port)

if __name__ == "__main__":
    main()