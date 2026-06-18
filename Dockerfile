# Stage 1: Build Frontend
FROM node:18 AS build-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.10-slim
WORKDIR /app
COPY . .
COPY --from=build-frontend /app/frontend/dist /app/frontend/dist
RUN pip install --no-cache-dir -r requirements.txt
ENV AIOHTTP_NO_VERIFY_SSL=1
CMD ["python", "server.py"]
