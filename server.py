import argparse
import os
from pathlib import Path

import dotenv
import socketio


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=["frontend", "backend"])

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    dotenv.load_dotenv()
    secret_key = os.getenv("SECRET_KEY")

    match args.type:
        case "frontend":
            import frontend

            port = os.getenv("FRONTEND_PORT")
            port = int(port) if port else None

            backend_port = os.getenv("BACKEND_PORT")
            backend_host = os.getenv("BACKEND_HOST")

            if not backend_host:
                exit()
            if not backend_port:
                exit()

            backend_url = backend_host + ":" + backend_port

            base_path = Path()
            print(base_path)
            if secret_key:
                app = frontend.create_app(base_path, backend_url, secret_key)
            else:
                app = frontend.create_app(base_path, backend_url)

            app.run(port=port, debug=True)
        case "backend":
            import backend

            port = os.getenv("BACKEND_PORT")
            port = int(port) if port else None

            base_path = Path()
            print(base_path)
            if secret_key:
                app, socketio = backend.create_app(base_path, secret_key)
            else:
                app, socketio = backend.create_app(base_path)

            socketio.run(app, port=port, debug=True)
        case _:
            exit()
