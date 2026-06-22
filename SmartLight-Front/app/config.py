import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev")
BACKEND_HOST = os.getenv("BACKEND_HOST", "http://127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8888")

# URL que usa el propio servidor del Front (httpx) para llamar al Back. En
# Docker Compose esto es el nombre del servicio (ej. "http://back:8888"),
# resoluble solo dentro de la red interna de contenedores.
BACKEND_URL = f"{BACKEND_HOST}:{BACKEND_PORT}"

# URL que se incrusta en el HTML para que el NAVEGADOR del usuario llegue al
# Back directo (snapshot de cámara, Socket.IO). Tiene que ser una dirección
# alcanzable desde fuera de la red de contenedores — por defecto, igual a
# BACKEND_URL (sirve para correr todo en localhost sin Docker), pero en
# despliegue real hay que pasar BACKEND_PUBLIC_URL con el host/IP público.
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", BACKEND_URL)
