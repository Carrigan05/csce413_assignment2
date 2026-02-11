FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        iptables \
        iproute2 \
        iptables-legacy \
        netcat-openbsd \
        ca-certificates \
        gnupg \
        dirmngr \
        lsb-release \
        apt-transport-https \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Force legacy iptables
RUN update-alternatives --set iptables /usr/sbin/iptables-legacy && \
    update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

COPY knock_server.py knock_client.py ./

CMD ["python3", "knock_server.py"]
