#!/usr/bin/env python3
"""
Port Scanner - Starter Template for Students
Assignment 2: Network Security

This is a STARTER TEMPLATE to help you get started.
You should expand and improve upon this basic implementation.

TODO for students:
1. Implement multi-threading for faster scans
2. Add banner grabbing to detect services
3. Add support for CIDR notation (e.g., 192.168.1.0/24)
4. Add different scan types (SYN scan, UDP scan, etc.)
5. Add output formatting (JSON, CSV, etc.)
6. Implement timeout and error handling
7. Add progress indicators
8. Add service fingerprinting
"""

import socket
import sys
import time
import argparse
import ipaddress
from concurrent.futures import ThreadPoolExecutor


def scan_port(target, port, timeout=.1):
    """
    Scan a single port on the target host

    Args:
        target (str): IP address or hostname to scan
        port (int): Port number to scan
        timeout (float): Connection timeout in seconds

    Returns:
        bool: True if port is open, False otherwise
    """
    # Stores the current time to calculate elapsed time for the scan of one port
    start_time = time.time()

    try:
        # Create a socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set timeout
        s.settimeout(timeout)
        # Try to connect to target:port
        result = s.connect_ex((target, port))
        # Measure elapsed time for the connection attempt
        elapsed = time.time() - start_time
        if result == 0:
            # Grab banner 
            try:
                s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = s.recv(1024).decode(errors="ignore").strip()
            except:
                banner = ""
            # Close the socket and return True
            s.close()
            return True, banner, elapsed
        # Close the socket and return False
        s.close()
        return False, None, elapsed

    except (socket.timeout, ConnectionRefusedError, OSError):
        return False, None, elapsed


def scan_range(target, start_port, end_port, threads=100):
    """
    Scan a range of ports on the target host

    Args:
        target (str): IP address or hostname to scan
        start_port (int): Starting port number
        end_port (int): Ending port number

    Returns:
        list: List of open ports
    """
    open_ports = []

    print(f"[*] Scanning {target} from port {start_port} to {end_port}")
    print(f"[*] This may take a while...")

    # Run one port scan in a separate thread
    def worker(port):
        open_flag, banner, elapsed = scan_port(target, port)
        if open_flag:
            print(f"[+] {target}:{port} OPEN ({elapsed:.4f}s)")
            open_ports.append((port, banner, elapsed))
            if banner:
                print(f"    Banner: {banner[:80]}")
        #else:
        #    print(f"[-] {target}:{port} CLOSED ({elapsed:.4f}s)")

    # Use ThreadPoolExecutor to scan ports in parallel
    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(worker, range(start_port, end_port + 1))

    return open_ports


def main():
    """Main function"""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Custom Port Scanner")
    parser.add_argument("--target", required=True, help="Target IP or CIDR (e.g. 172.20.0.0/24)")
    parser.add_argument("--ports", required=True, help="Port range (e.g. 1-10000)")
    parser.add_argument("--threads", type=int, default=100)

    args = parser.parse_args()

    start_port, end_port = map(int, args.ports.split("-"))

    # Handle CIDR or single IP
    targets = []
    if "/" in args.target:
        network = ipaddress.ip_network(args.target, strict=False)
        targets = [str(ip) for ip in network.hosts()]
    else:
        targets = [args.target]

    print(f"[*] Scanning {len(targets)} hosts...")

    # Loop through each target host and scan the specified port range
    for host in targets:
        print(f"\n[*] Scanning host {host}")
        scan_range(host, start_port, end_port, args.threads)

if __name__ == "__main__":
    main()
