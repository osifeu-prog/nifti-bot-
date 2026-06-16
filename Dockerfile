FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV AIOHTTP_NO_VERIFY_SSL=1
CMD ["python", "bot.py"]
