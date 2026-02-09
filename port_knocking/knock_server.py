#!/usr/bin/env python3
"""Starter template for the port knocking server."""

import argparse
import logging
import socket
import time
import subprocess

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def open_protected_port(protected_port):
    """Open the protected port using firewall rules."""
    # TODO: Use iptables/nftables to allow access to protected_port.
    logging.info("[+] Opening protected port %s", protected_port)
    subprocess.run(
        ["iptables", "-I", "INPUT", "-p", "tcp", "--dport", str(protected_port), "-j", "ACCEPT"],
        stderr=subprocess.DEVNULL,
    )


def close_protected_port(protected_port):
    """Close the protected port using firewall rules."""
    # TODO: Remove firewall rules for protected_port.
    logging.info("[-] Closing protected port %s", protected_port)
    subprocess.run(
        ["iptables", "-D", "INPUT", "-p", "tcp", "--dport", str(protected_port), "-j", "ACCEPT"],
        stderr=subprocess.DEVNULL,
    )


def listen_for_knocks(sequence, window_seconds, protected_port):
    """Listen for knock sequence and open the protected port."""
    logger = logging.getLogger("KnockServer")
    logger.info("Listening for knocks: %s", sequence)
    logger.info("Protected port: %s", protected_port)


    # TODO: Create UDP or TCP listeners for each knock port.
    # TODO: Track each source IP and its progress through the sequence.
    # TODO: Enforce timing window per sequence.
    # TODO: On correct sequence, call open_protected_port().
    # TODO: On incorrect sequence, reset progress.

    # Track progress per IP
    client_state = {}

    def handle_knock(port):
        """Listen for knocks on a single port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", port))
        sock.listen(5)
        logger.info(f"Listening on knock port {port}")

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
                    logger.info(f"[+] {ip} completed knock sequence!")
                    open_protected_port(protected_port)
                    state["progress"] = 0
            else:
                logger.warning(f"[-] {ip} wrong knock {port}, resetting")
                state["progress"] = 0
                state["start"] = now

            conn.close()

    # Start listener threads for each knock port
    for port in sequence:
        import threading
        t = threading.Thread(target=handle_knock, args=(port,))
        t.daemon = True
        t.start()

    while True:
        time.sleep(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Port knocking server starter")
    parser.add_argument(
        "--sequence",
        default=",".join(str(port) for port in DEFAULT_KNOCK_SEQUENCE),
        help="Comma-separated knock ports",
    )
    parser.add_argument(
        "--protected-port",
        type=int,
        default=DEFAULT_PROTECTED_PORT,
        help="Protected service port",
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
        sequence = [int(port) for port in args.sequence.split(",")]
    except ValueError:
        raise SystemExit("Invalid sequence. Use comma-separated integers.")

    listen_for_knocks(sequence, args.window, args.protected_port)


if __name__ == "__main__":
    main()
