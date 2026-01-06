from dotenv import dotenv_values
from os import getenv, environ


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self._data = {}
        env_vals = dotenv_values(".env")

        self._data = {k: v for k, v in env_vals.items()}
        if not self._data:
            self._data = dict(environ)

    def __getitem__(self, key):
        return str(self._data[key])

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        """Get a config value with optional default."""
        if key in self._data:
            return str(self._data[key])
        return default
