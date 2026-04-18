import os
from urllib.parse import quote_plus


def _build_database_uri() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    return "postgresql://{}:{}@{}:{}/{}".format(
        os.environ.get("DB_USER"),
        quote_plus(os.environ.get("DB_PASSWORD", "")),
        os.environ.get("DB_HOST"),
        os.environ.get("DB_PORT"),
        os.environ.get("DB_NAME"),
    )


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
