FROM python:3.11

WORKDIR /app

RUN apt-get update && \
    apt-get install -y iptables iproute2 iptables-legacy netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*
RUN update-alternatives --set iptables /usr/sbin/iptables-legacy && \
    update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

COPY knock_server.py knock_client.py ./

CMD ["python3", "knock_server.py"]
