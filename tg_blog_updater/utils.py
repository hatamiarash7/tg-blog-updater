"""Process configuration loaded from the environment."""

import os


class MissingEnvironmentVariable(Exception):
    """A required environment variable is missing or blank."""


def get_env(key: str, default: str | None = None) -> str:
    """Return an environment variable.

    Surrounding whitespace is removed. A missing or blank value raises
    ``MissingEnvironmentVariable`` unless ``default`` is provided.
    """

    value = os.environ.get(key)
    if value is not None and value.strip():
        return value.strip()

    if default is not None:
        return default

    raise MissingEnvironmentVariable(f"Environment variable {key} not defined")
