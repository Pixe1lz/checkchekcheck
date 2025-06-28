FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y tzdata
ENV TZ=Europe/Moscow

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install
RUN playwright install-deps
RUN playwright install chrome

COPY . .

RUN mkdir -p /app/logs && chmod 777 /app/logs

CMD ["python", "-u", "app/main.py"]