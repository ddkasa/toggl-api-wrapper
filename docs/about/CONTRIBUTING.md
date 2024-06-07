- Setup authentication through environment variables. Preferably a testing account for integration testing.

## Basic Environment
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
