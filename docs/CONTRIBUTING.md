- Setup authentication through environment variables
- Preferably a testing account for integration testing

## Basic Environment

- Development is ran through Poetry.

1. `git clone https://github.com/ddkasa/toggl-api-wrapper`
2. `cd toggl-api-wrapper`
3. `poetry shell`
4. `poetry install`

- Lint with `ruff toggl_api`
- Check typing with `mypy toggl_api`
- Make sure to install pre-commit hook with `pre-commit install`

## Testing

- Make sure to set the environment variables plus the correct workspace id through the **TOGGL_WORKSPACE_ID**
- All tests are run through `pytest`
- Basic unit tests through `pytest -m unit`
- Integration tests through `pytest -m integration`
- Slow tests are marked as well `pytest -m slow`
- Test all supported python versions through `tox`
  - _Alternate python version are set through Pyenv in .python-version so make sure those are installed_
- Test a specific version with the `-e` flag: `tox -e py310`

## Git

- Commit messages are based on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
- Versioning follows [Semver](https://semver.org) conventions

## Documentation

- Run `mkdocs serve --strict` to build and preview documentation
- Run `git cliff -o docs/CHANGELOG.md` to generate new changelog. _Requires git-cliff to be installed._
- Use Google [styleguide](https://google.github.io/styleguide/pyguide.html) for docstring format
