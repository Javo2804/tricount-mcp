FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY tricount_client.py server.py ./

# Cloud Run define PORT; con PORT presente, server.py usa streamable HTTP en /mcp.
RUN useradd --create-home app
USER app
CMD ["python", "server.py"]
