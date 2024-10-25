import configparser
import logging
import os
from pathlib import Path
from typing import Optional

from httpx import BasicAuth

log = logging.getLogger("toggl-api-wrapper")


class AuthenticationError(ValueError):
    """Authentication failed or was not provided."""


def generate_authentication() -> BasicAuth:
    """Gathers credentials from environment variables.

    If using an API token as authentication: `TOGGL_API_TOKEN`.

    If using email as authentication: `TOGGL_API_TOKEN` & `TOGGL_PASSWORD`.

    Examples:
        >>> generate_authentication()
        <httpx.BasicAuth object at 0x...>

    Raises:
        AuthenticationError: If credentials are not set or invalid.

    Returns:
        BasicAuth: BasicAuth object that is used with httpx client.
    """
    api_token = os.getenv("TOGGL_API_TOKEN")
    if api_token is None:
        msg = "Email or API Key not set."
        raise AuthenticationError(msg)

    password = os.getenv("TOGGL_PASSWORD", "api_token")

    if password == "api_token":  # noqa: S105
        log.info("Detected an api token as authentication.")
    else:
        log.info("Detected an email and password combo as authentication.")

    return BasicAuth(api_token, password)


# NOTE: For .togglrc compatibility.
def use_togglrc(config_path: Optional[Path] = None) -> BasicAuth:
    """Gathers credentials from a .togglrc file.

    Mainly here for togglcli backwards compatibility.

    Examples:
        >>> use_togglrc()
        <httpx.BasicAuth object at 0x...>

        >>> use_togglrc(Path("home/dk/.config/"))
        <httpx.BasicAuth object at 0x...>

    Args:
        config_path: Path to .togglrc folder not file. If None, will use
            $HOME/.togglrc for the default location.

    Raises:
        AuthenticationError: If credentials are not set or invalid.

    Returns:
        BasicAuth: BasicAuth object that is used with httpx client.
    """
    if config_path is None:
        log.debug("Using default path for .togglrc configuration.")
        config_path = Path.home()

    config_path /= ".togglrc"
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise AuthenticationError(msg)

    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path, encoding="utf-8")

    if not config.has_section("auth"):
        msg = "No auth section in config file"
        raise AuthenticationError(msg)

    try:
        api_token = config.get("auth", "api_token")
        if api_token:
            return BasicAuth(api_token, "api_token")
    except configparser.NoOptionError:
        pass

    try:
        email = config.get("auth", "email")
    except configparser.NoOptionError as err:
        msg = "No email in config file"
        raise AuthenticationError(msg) from err

    try:
        password = config.get("auth", "password")
    except configparser.NoOptionError as err:
        msg = "No password set in config file"
        raise AuthenticationError(msg) from err

    return BasicAuth(email, password)


def retrieve_workspace_id(default: Optional[int] = None) -> int:
    """Helper function that collect the default workspace from the environment.

    Examples:
        >>> retrieve_workspace_id()

        >>> retrieve_workspace_id(214812815)

    Args:
        default: Workspace id alternative if not set through environment.

    Raises:
        ValueError: If no workspace was found at the **TOGGL_WORKSPACE_ID**
            variable or the workspace set is not an integer.

    Returns:
        int: The id of the workspace.
    """

    workspace = os.environ.get("TOGGL_WORKSPACE_ID", default)
    if workspace is None:
        msg = "Default workspace has not been set in the environment variables."
        raise ValueError(msg)

    return int(workspace)


if __name__ == "__main__":
    pass
