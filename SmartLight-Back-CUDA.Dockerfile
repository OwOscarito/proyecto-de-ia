FROM nvcr.io/nvidia/pytorch:26.05-py3

WORKDIR /app

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
# Omit development dependencies
ENV UV_NO_DEV=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY SmartLight-Back/pyproject.toml ./

RUN uv sync --no-install-package torch --no-install-package torchvision

COPY SmartLight-Back/app ./app

# Rutas por defecto para la BD y los videos subidos. En producción deben
# apuntar a un volumen montado (ver docker-compose.yml) para que sobrevivan
# a un reinicio del contenedor.
ENV DB_PATH=/data/smartlight.db
ENV UPLOADS_DIR=/data/uploads

EXPOSE 8888

CMD ["uv", "run", "uvicorn", "app.main:asgi_app", "--host", "0.0.0.0", "--port", "8888"]
