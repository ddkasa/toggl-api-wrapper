- Setup authentication through environment variables
- Preferably a testing account for integration testing

## Basic Environment

- Development is ran through UV.

```sh
# Clone Repository
git clone https://github.com/ddkasa/toggl-api-wrapper &&
# Change Directory Into Repository
cd toggl-api-wrapper &&
# Install all required dependencies
uv sync --all-groups --all-extras &&
# Activate the virtual environment
source .venv/bin/activate
```

- Lint with `uv run ruff check src/toggl_api`
- Check typing with `uv run mypy src/toggl_api`
- Make sure to install pre-commit hook with `pre-commit install`

## Testing

- Make sure to set the environment variables plus the correct workspace id through the **TOGGL_WORKSPACE_ID**
- All tests are run through `pytest`
- Basic unit tests through `pytest -m unit`
- Integration tests through `pytest -m integration`
- Slow tests are marked as well `pytest -m slow`
- Test all supported python versions through `tox`
- Test a specific version with the `-e` flag: `tox -e test-py310`

## Git

- Commit messages are based on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
- Versioning follows [Semver](https://semver.org) conventions

## Documentation

- Run `uv sync --group docs` to install doc dependencies.
- Run `mkdocs serve --strict` to build and preview documentation
- Run `git cliff -o docs/CHANGELOG.md` to generate new changelog. _Requires git-cliff to be installed._
- Use Google [styleguide](https://google.github.io/styleguide/pyguide.html) for docstring format
- Run `sh ./scripts/create_diagrams.sh` to generate documentation mermaid diagrams and file tree.
