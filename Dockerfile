#1단계: 빌드
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc build-essential libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

COPY main.py .
COPY env.py .

RUN pyinstaller --onefile main.py

#2단계: 실행
FROM debian:bookworm-slim

WORKDIR /app

COPY .env .
COPY --from=builder /app/dist/main .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]