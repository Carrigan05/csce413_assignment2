FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 2222

CMD ["python3", "-u", "honeypot.py"]



