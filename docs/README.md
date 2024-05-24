# Python Toggl API Wrapper

*Under Development: Anything might change without notice at the moment.*

Simple Python Toggl API wrapper for none premium features primarily created for usage with some of my projects.


## Installation

- `$ pip install toggl-api-wrapper`

## Usage

- Currently supports interacting with Trackers, Projects, Clients & Tags and some extras.
- Designed to stay rudimentary to allow easy development of custom commands.

```
import toggl_api
from toggl_api import TogglClient
...
```

- Most of the configuration relies on setting the environment variables.
1. **TOGGL_API_TOKEN**: Your Toggl API token.
2. Or **TOGGL_EMAIL** + **TOGGL_PASSWORD**: Your Toggl email and password.



## Development

### Basic Environment

- Development is ran through Poetry.
 
1. `$ git clone https://github.com/ddkasa/toggl-api-wrapper`
2. `$ cd toggl-api-wrapper`
3. `$ poetry shell` 
    1. *Setup .envrc for automatic environment and local testing variables.*
4. `$ poetry install`

- Lint with `$ ruff toggl_api`
- Check typing with `$ mypy toggl_api`

### Testing

- Make sure to set the environment variables plus the correct workspace id through the **TOGGL_WORKSPACE_ID**.
- All tests are run through `$ pytest`.
- Basic unit tests through `$ pytest -m unit`.
- Integration tests through `$ pytest -m integration`.
- Slow tests are marked as well `$ pytest -m slow`.
- Test all supported python versions through `$ tox`.
    - *Alternate python version are set through Pyenv in .python-version so make sure those are installed.*
- Test a specific version with the `-e` flag: `$ tox -e py310`.


## License
MIT. Check [LICENSE](about/LICENSE.md) for more information.
