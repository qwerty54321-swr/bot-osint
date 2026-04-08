FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
RUN pip install python-telegram-bot==20.7

# Копируем бота
COPY bot.py .

# Запускаем бота
CMD ["python", "bot.py"]
