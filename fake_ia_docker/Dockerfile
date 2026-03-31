FROM python:3.11-slim

RUN apt-get update
RUN apt-get install -y --no-install-recommends gcc postgresql-client
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]