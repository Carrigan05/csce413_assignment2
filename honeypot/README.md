### Honeypot Design

The honeypot is a decoy ssh service that is designed to trick users into believing it is real and monitor unauthorized access attempts. It listens on a designated port and presents realistic things for the user to interact with. The honeypot consists of two main components, honeypot.py and  logger.py. The honeypot accepts incoming connections, records authentication attempts, and simulates an environment to capture an attacker's commands. All the logs are written to the honeypot.log file in the logs folder of honeypot. The logger records the user's IP address, timestamp, authentication attempts, and any commands attempted by the attacker. This design supports the detection of brute force attacks and reconnaissance activity.

