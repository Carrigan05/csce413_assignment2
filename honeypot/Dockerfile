FROM python:3.11-slim

WORKDIR /app

COPY honeypot.py .

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 22222

CMD ["python3", "-u", "honeypot.py"]


