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

# Sync environment, but exclude torch-related deps already present in the base image
RUN uv sync --locked --exclude torch --exclude torchvision --exclude torchaudio

# some more preparation ...

CMD ["uv", "run", "uvicorn"]
