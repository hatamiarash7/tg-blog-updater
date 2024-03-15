import os


def get_env(key: str, default: str = None) -> str:
    """Get environment variable

    Args:
        key (str): Environment variable name
        default (str, optional): Default value if not found. Defaults to None.

    Returns:
        str: Environment variable value
    """

    if key in os.environ:
        return os.environ[key]

    if default:
        return default

    # pylint: disable=W0719
    raise Exception(f"Environment variable {key} not defined")
