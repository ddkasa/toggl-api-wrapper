# Python Toggl API Wrapper

> [!WARNING]  
> *Alpha Stage: Anything might change without notice at any moment.*

Simple Python Toggl API wrapper for non-premium features primarily focused on creating a cached framework for developing custom commands.

***

## Installation

### Poetry

- `$ poetry add toggl-api-wrapper`

### PIP

- `$ pip install toggl-api-wrapper`

## Usage

- Currently supports interacting with Trackers, Projects, Clients & Tags and some extras.
- Designed to be rudimentary to allow simple development of custom commands.

- Most of the configuration relies on setting the environment variables.
1. **TOGGL_API_TOKEN**: Your Toggl API token or account email.
    - If using an email **TOGGL_PASSWORD** must be set as well.


## Development
See [CONTRIBUTING](about/CONTRIBUTING.md).

## License
MIT. Check [LICENSE](about/LICENSE.md) for more information.
