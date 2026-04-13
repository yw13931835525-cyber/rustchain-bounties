FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
ENV RPC_URL="${RPC_URL:-https://50.28.86.131}"

CMD ["python", "bot.py"]
