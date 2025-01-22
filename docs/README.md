# Python Toggl API Wrapper

<a href="https://pypi.org/project/toggl-api-wrapper">![PyPI - Version](https://img.shields.io/pypi/v/toggl-api-wrapper?link=https%3A%2F%2Fpypi.org%2Fproject%2Ftoggl-api-wrapper%2F)</a>
<a href="https://pypi.org/project/toggl-api-wrapper">![PyPI - Python Version](https://img.shields.io/pypi/pyversions/toggl-api-wrapper)</a>
<a href="https://github.com/ddkasa/toggl-api-wrapper/actions/workflows/publish.yaml">![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ddkasa/toggl-api-wrapper/publish.yaml)</a>
<a href="https://app.codecov.io/gh/ddkasa/toggl-api-wrapper">![Codecov](https://img.shields.io/codecov/c/github/ddkasa/toggl-api-wrapper)</a>
<a href="https://pypistats.org/packages/toggl-api-wrapper">![PyPI - Downloads](https://img.shields.io/pypi/dm/toggl-api-wrapper)</a>

> Simple Toggl API wrapper for non-premium features primarily focused on creating a cached framework for developing custom commands.

---

## Installation

Install with pip:

```bash
pip install toggl-api-wrapper
```

Or if using SQLite cache:

```bash
pip install "toggl-api-wrapper[sqlite]"
```

Or if using async classes:

```bash
pip install "toggl-api-wrapper[async]"
```

## Usage

- Currently supports interacting with Trackers, Projects, Clients, Tags, Reports and some extras.
- Designed to be rudimentary to allow simple development of custom commands.

## Examples

<details>
  <summary>Tracker Endpoint</summary>

```python
from datetime import timedelta
from pathlib import Path

from toggl_api.config import generate_authentication
from toggl_api import TrackerBody, TrackerEndpoint, JSONCache


WORKSPACE_ID = 2313123123
AUTH = generate_authentication()
cache = JSONCache(Path("cache"), timedelta(hours=24))
endpoint = TrackerEndpoint(WORKSPACE_ID, AUTH, cache)

body = TrackerBody("My First Tracker", tags=["My First Tag"])
tracker = endpoint.add(body)
print(tracker)
```

<strong>Outputs:</strong>

```python
>>> TogglTracker(
        id=3482231563,
        name="My First Tracker",
        workspace=2313123123,
        start=datetime.datetime(2024, 6, 10, 14, 59, 20, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(seconds=1, microseconds=179158),
        stop=None,
        project=None,
        tags=[],
    )
```

</details>

<details>
  <summary>Project Endpoint</summary>

```python
from datetime import timedelta
from pathlib import Path

from toggl_api import ProjectBody, ProjectEndpoint, TogglProject
from toggl_api.config import retrieve_togglrc_workspace_id, use_togglrc
from toggl_api.meta.cache import JSONCache

WORKSPACE_ID = retrieve_togglrc_workspace_id()
AUTH = use_togglrc()
cache = JSONCache[TogglProject](Path("cache"), timedelta(hours=24))
endpoint = ProjectEndpoint(WORKSPACE_ID, AUTH, cache)

color = ProjectEndpoint.get_color("red")
body = ProjectBody(
    "My First Project",
    client_name="My First Client",
    color=color,
)
project = endpoint.add(body)
print(project)
```

<strong>Outputs:</strong>

```python
>>> TogglProject(
        id=203366783,
        name='My First Project',
        workspace=2313123123,
        color='#d92b2b',
        client=65298912,
        active=True,
    )
```

</details>

## Documentation

- [Examples](https://ddkasa.github.io/toggl-api-wrapper/user-guide/examples.html)
- [API Documentation](https://ddkasa.github.io/toggl-api-wrapper/api-guide/)
- [User Guide](https://ddkasa.github.io/toggl-api-wrapper/index.html)
- [Changelog](https://ddkasa.github.io/toggl-api-wrapper/CHANGELOG.html)

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md).

## License

MIT. Check [LICENSE](LICENSE.md) for more information.
