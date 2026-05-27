import os
from pathlib import Path

import dotenv

from . import create_app

BASE_PATH = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_PATH.parent

dotenv.load_dotenv(PROJECT_ROOT / ".env")

backend_host = os.getenv("BACKEND_HOST")
backend_port = os.getenv("BACKEND_PORT")

if not backend_host or not backend_port:
    raise RuntimeError("BACKEND_HOST and BACKEND_PORT must be set for frontend WSGI")

backend_url = backend_host + ":" + backend_port

secret_key = os.getenv("SECRET_KEY")

if secret_key:
    application = create_app(BASE_PATH, backend_url, secret_key)
else:
    application = create_app(BASE_PATH, backend_url)
