import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.secret_key = secret_key


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == "__main__":
    port = os.getenv("BACKEND_PORT")
    port = int(port) if port else None
    app.run(port=port)
