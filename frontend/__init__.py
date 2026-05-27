from flask import Flask, render_template


def create_app(base_path, backend_url, secret_key="dev"):

    app = Flask(
        __name__,
        template_folder=base_path / "templates",
        static_folder=base_path / "static",
    )
    app.config.from_mapping(
        SECRET_KEY=secret_key,
    )

    @app.route("/")
    def index():
        return render_template("index.html", backend_url=backend_url)

    return app
