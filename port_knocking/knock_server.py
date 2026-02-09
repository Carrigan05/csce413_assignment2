#!/usr/bin/env python3
"""Starter template for the port knocking server."""

import argparse
import logging
import socket
import time
from collections import defaultdict

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0

client_state = defaultdict(lambda: {"index": 0, "start": 0})

def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(message)s")

def open_protected_port(port):
    logging.info(f"OPENING port {port}")
    # Allow SSH for that IP (for demo, open globally)
    import os
    os.system(f"iptables -I INPUT -p tcp --dport {port} -j ACCEPT")

def close_protected_port(port):
    logging.info(f"CLOSING port {port}")
    import os
    os.system(f"iptables -D INPUT -p tcp --dport {port} -j ACCEPT")

def listen_for_knocks(sequence, window, protected_port):
    logging.info(f"Listening for knock sequence {sequence}")

    sockets = []
    for port in sequence:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", port))
        s.listen(5)
        sockets.append((port, s))

    while True:
        for port, s in sockets:
            s.settimeout(0.1)
            try:
                conn, addr = s.accept()
                ip = addr[0]
                handle_knock(ip, port, sequence, window, protected_port)
                conn.close()
            except socket.timeout:
                pass

def handle_knock(ip, port, sequence, window, protected_port):
    state = client_state[ip]
    now = time.time()

    # Reset if timeout
    if state["start"] and now - state["start"] > window:
        logging.info(f"{ip} timeout reset")
        state["index"] = 0
        state["start"] = 0

    expected = sequence[state["index"]]

    if port == expected:
        logging.info(f"{ip} correct knock {port}")
        if state["index"] == 0:
            state["start"] = now
        state["index"] += 1

        if state["index"] == len(sequence):
            logging.info(f"{ip} FULL SEQUENCE COMPLETE!")
            open_protected_port(protected_port)
            state["index"] = 0
            state["start"] = 0
    else:
        logging.info(f"{ip} WRONG knock {port}, reset")
        state["index"] = 0
        state["start"] = 0

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence", default="1234,5678,9012")
    parser.add_argument("--protected-port", type=int, default=2222)
    parser.add_argument("--window", type=float, default=10)
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()
    sequence = [int(x) for x in args.sequence.split(",")]
    listen_for_knocks(sequence, args.window, args.protected_port)

if __name__ == "__main__":
    main()