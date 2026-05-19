# Preparar env

## venv

```sh
python -m venv venv
source venv/bin/activate
pip install requirements.txt
```

## Conda

```sh
conda create -f conda-env.yml
conda activate proyecto-de-ia
```

# Ejecutar

# venv / conda

```sh
flask run frontend
flask run backend
```

# uv

```sh
uv run flask --app frontend run
uv run flask --app backend run
```
