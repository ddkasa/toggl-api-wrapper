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

## Usage

- Currently supports interacting with Trackers, Projects, Clients, Tags, Reports and some extras.
- Designed to be rudimentary to allow simple development of custom commands.

## Examples

<details>
  <summary>Tracker Endpoint</summary>

```python
from datetime import timedelta
from pathlib import Path

from toggl_api import (
    TrackerBody,
    TrackerEndpoint,
    generate_authentication,
    JSONCache
)

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
  <summary>User Endpoint</summary>

```python
from datetime import timedelta
from pathlib import Path

from toggl_api import (
    UserEndpoint,
    generate_authentication,
    JSONCache,
)
from toggl_api.config import retrieve_workspace_id

WORKSPACE_ID = retrieve_workspace_id()
AUTH = generate_authentication()
cache = JSONCache(Path("cache"), timedelta(weeks=1))
endpoint = UserEndpoint(workspace_id, AUTH, CACHE)

tracker = endpoint.get(3482231563, refresh=True)
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

## Documentation

- [Examples](https://ddkasa.github.io/toggl-api-wrapper/user-guide/examples.html)
- [API Documentation](https://ddkasa.github.io/toggl-api-wrapper/api-guide/)
- [User Guide](https://ddkasa.github.io/toggl-api-wrapper/index.html)
- [Changelog](https://ddkasa.github.io/toggl-api-wrapper/CHANGELOG.html)

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md).

## License

MIT. Check [LICENSE](LICENSE.md) for more information.
