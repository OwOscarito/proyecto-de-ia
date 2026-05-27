import os
from pathlib import Path

import dotenv

from . import create_app

BASE_PATH = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_PATH.parent

dotenv.load_dotenv(PROJECT_ROOT / ".env")

secret_key = os.getenv("SECRET_KEY")

if secret_key:
    app, socketio = create_app(BASE_PATH, secret_key)
else:
    app, socketio = create_app(BASE_PATH)

application = app
