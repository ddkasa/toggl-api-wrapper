# Changelog

All notable changes to this project will be documented in this file.

## [0.5.1] - 2024-10-07

### 🐛 Bug Fixes

- *(config)* Removed interpolation

### 📚 Documentation

- Update contributing
- *(endpoints)* Improve docstrings

### ⚙️ Miscellaneous Tasks

- *(actions)* Fix release workflow
- *(precommit)* Add gh action validator to pre commit
- *(precommit)* Upgrade ruff

## [0.5.0] - 2024-10-06

### 🚀 Features

- *(endpoint)* Api status endpoint
- *(reports)* Summary report endpoints
- *(reports)* Detailed report endpoints
- *(reports)* Weekly report endpoints
- *(reports)* Module level imports
- *(body)* Validate parameter classmethod

### 🐛 Bug Fixes

- *(endpoint)* Cache parent logic
- *(utility)* Date override

### 🚜 Refactor

- *(meta)* Basebody abstract class
- *(endpoint)* Remove final type from base endpoint
- *(endpoint)* Adjust to allow for more flexible models
- *(reports)* Adjust responses
- *(util)* Default cleanup delay
- *(reports)* Report body improvements
- *(endpoints)* Adjust to new body format signature

### 🕸 Deprecations

- Modules namespace
- *(deps)* Convert sqlalchemy to optional dependency
- *(body)* Workspace_id parameter

### 📚 Documentation

- Show symbol type headings
- *(reports)* Documentation update
- Improve user guide
- Move about folder
- Update mermaid diagrams
- Update changelog

### 🎨 Styling

- *(endpoint)* Removed optional as a return type

### ⚙️ Miscellaneous Tasks

- Omit scripts folder from coverage
- *(actions)* Remove macos from matrix
- Git cliff configuration

### 🧪 Testing

- Fix config encoding
- *(reports)* All endpoints

## [0.4.0] - 2024-09-23

### 🚀 Features

- *(scripts)* Clean toggl script

### 🚜 Refactor

- *(endpoint)* Rename methods
- Cleanup utils
- *(tags)* Delete method accepts int

### 📚 Documentation

- Fix config docstring
- Update documentation

### ⚙️ Miscellaneous Tasks

- *(nvim)* .nvim.lua file
- Bump version 0.4.0

### 🧪 Testing

- *(client)* Delete method int arg

## [0.3.1] - 2024-08-13

### 🚜 Refactor

- Get custom workspace

### ⚙️ Miscellaneous Tasks

- Fix urls
- Bump version 0.3.1

### 🧪 Testing

- Extra coverage

## [0.3.0] - 2024-06-26

### 🚜 Refactor

- *(cache)* Allowing no expiration
- *(cache)* Json cache syncing
- *(cache)* Int allowed as argument

### ⚙️ Miscellaneous Tasks

- Bump version 0.3.0

## [0.2.3] - 2024-06-22

### 🐛 Bug Fixes

- Tracker tag conversion

### 📚 Documentation

- Other applications

### ⚙️ Miscellaneous Tasks

- Updated ruff rules
- Bump version 0.2.3

### 🧪 Testing

- Refactor conftest

## [0.2.2] - 2024-06-21

### 🐛 Bug Fixes

- *(endpoints)* Single model get methods
- Config issues

### 🚜 Refactor

- Flexible arguments

### 📚 Documentation

- Remove release notes

### ⚙️ Miscellaneous Tasks

- Bump version 0.2.2

## [0.2.1] - 2024-06-21

### 🐛 Bug Fixes

- *(tracker)* Tag action only needed when editing
- Cached response inside list

### 🚜 Refactor

- Logging

### ⚙️ Miscellaneous Tasks

- Bump version 0.2.1

### 🧪 Testing

- Sqlite workspace id set to random

## [0.2.0] - 2024-06-20

### 🚀 Features

- *(cache)* Json max length
- *(cache)* Query method
- *(cache)* Connection close on delete

### 🐛 Bug Fixes

- *(tracker)* Bad body conditonal brackets
- *(user)* Missing raise

### 🚜 Refactor

- *(model)* Better str representation

### 📚 Documentation

- Update readme

### ⚙️ Miscellaneous Tasks

- Update httpx
- Bump version 0.2.0

## [0.1.1] - 2024-06-11

### 🐛 Bug Fixes

- Tracker start error handling
- *(endpoint)* Retry on server error

### 🚜 Refactor

- Removed unnecessary method
- Base url added to client

### 📚 Documentation

- Improved api documentation

### 🎨 Styling

- Various changes

### ⚙️ Miscellaneous Tasks

- Fix release drafter
- Version 0.1.1

## [0.1.0] - 2024-06-10

### 🚀 Features

- Basic project structure
- Toggl client metaclass
- Tracker api
- Dataclasses
- User endpoint
- Project api
- Workspace api
- Tag api
- Client api
- Config utility
- Added classes to init
- Utility functions
- Workspace utility
- Sql schema
- Cache model
- *(trackers)* Body dataclass
- *(projects)* Body dataclass
- *(clients)* Body dataclass
- *(trackers)* Add tracker value checking

### 🐛 Bug Fixes

- *(client)* Wrong workspace id
- Python 3.10 compatibility
- Typing logic
- Python 3.10 datetime parsing
- *(user)* Missing refresh arg
- *(models)* Timezone issues with sechma
- *(cache)* Sqlite caching changes
- *(trackers)* Stop endpoint

### 🚧 Work In Progress

- Caching mechanism
- Cache mechanism

### 🚜 Refactor

- *(meta)* Cleaner classes
- Remove debugging code
- Renamed src directory
- Sql schema
- Model creation
- *(models)* Foreign keys & dict converter
- *(endpoint)* Merged endpoints
- Endpoint changes
- Cache adjustments
- Model adjustments
- *(cache)* Various changes
- General typing
- *(models)* Missing timezone schema
- Small changes
- Simplified config utility
- *(tags)* Improved json body
- Typing

### 📚 Documentation

- Readme
- Added license
- Class & package layout
- Mkdocs config
- Documentation boilerplate
- Cache flowchart
- Moved images
- Updated class graph
- Docstring
- Api documentation
- Api documentation
- User guide
- Examples
- Changelog
- Coverage badge
- Readme badge

### 🎨 Styling

- Small changes
- Typing & version

### ⚙️ Miscellaneous Tasks

- Basic setup
- Added gitignore
- Basic data
- Ignore direnv
- Lsp & lint config
- Pytest env dependency
- Pytest config
- Pytest order dependency
- Tracker cache
- Ci dependencies & config
- Github publishing workflow
- Tox gh actions tweaks
- Sqlalchemy dependency
- Docs generation
- Doc dependencies
- Release notes
- Test dependencies
- Mypy config
- Sqlalchemy type stubs
- Added pre commit
- Mkdocstrings depedency
- Mkdocs dependencies
- Coverage
- Pygments dependency
- Mkdocs changelog dependency
- Poetry urls
- Mkdocs callout dependency
- Coverage

### 🧪 Testing

- Conftest
- Metaclasses
- Conftest
- Teardown fixture
- Workspace id
- Refactor directory structure
- Endpoint refactor
- Pytest configuration
- Sqlite cache

<!-- generated by git-cliff -->
