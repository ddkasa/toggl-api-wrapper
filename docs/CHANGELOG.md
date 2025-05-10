---
hide:
- navigation
---

# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - 2025-05-10

### 🚀 Features

- *(utility)* Implement fake data generator

### 🐛 Bug Fixes

- *(clean-account)* Check if file exists before removing

### 🚜 Refactor

- *(models)* Remove `str` type from `TogglTracker.stop`
- *(models)* Remove automatic generation of `TogglTracker.duration`
- *(scripts)* Move clean_account script to utility module
- *(utility)* Move helpers into utility module
- *(utility)* Convert `clean_account` to private module
- *(generate-fake-data)* Add additional checks for cache type
- *(clean-account)* Move `ArgumentParser` into separate function

### 📚 Documentation

- *(utility)* Add documentation for utility scripts

### ⚙️ Miscellaneous Tasks

- *(actions)* Allow Windows in *3.10* configs
- *(scripts)* Add scripts into configuration
- *(coverage)* Omit utility scripts

### 🧪 Testing

- *(detail-report)* Ignore partial coverage

## [2.1.0] - 2025-04-15

### 🚀 Features

- *(models)* Add `TogglTracker.description` property
- *(models)* Add `TogglTracker.running_duration` property

### 🐛 Bug Fixes

- *(async-sqlite-cache)* Add `metadata` attribute type to class

### 🚜 Refactor

- *(async-sqlite-cache)* Remove unnecessary *E402* noqa code
- *(utils)* Add return type to `cleanup` functionx

### 📚 Documentation

- *(schema)* Add docstring to `register_tables` function
- *(cache)* Add `register_tabels` function
- *(models)* Update `as_dict_custom` helper function
- *(models)* Add `as_dict_custom` function
- *(utils)* Add docstring to module and `cleanup` function

### ⚡ Performance

- *(schema)* Index all high variance columns

### 🎨 Styling

- *(schema)* Remove unncessary *E402* code

### ⚙️ Miscellaneous Tasks

- *(tox)* Add `--cov` parameter to tests
- *(actions)* Run all tests on both os *3.10* configs
- *(tox)* Only check coverage on *3.10* tests
- *(coverage)* Remove `requires` option

### 🧪 Testing

- *(cache)* Add small delay on windows

## [2.0.0] - 2025-04-08

### 🚀 Features

- *(cached-endpoint)* Allow for no cache to be assigned
- *(reports)* Abstract report methods
- *(config)* Add workspace missing error exception
- *(sqlite_cache)* Allow for an external engine param
- *(cache)* Allow for pathlike & strings objects to be passed in
- *(reports)* Custom invalid extension error
- *(sqlite_cache)* Allow for an external engine param
- *(cache)* Allow for pathlike & strings objects to be passed in
- *(reports)* Custom invalid extension error
- *(async)* Implement abstract endpoints
- *(async)* Implement abstract cache
- *(async)* Implement sqlite cache
- *(async-tracker)* Implement async tracker endpoint
- *(async-project)* Implement async project endpoint
- *(async-client)* Implement async client endpoint
- *(async-org)* Implement async org endpoint
- *(async-tag)* Implement async tag endpoint
- *(async-workspace)* Implement async workspace endpoint
- *(async-user)* Implement async user endpoint
- *(async-reports)* Implement async report endpoints
- *(endpoints)* Implement custom client parameter

### 🐛 Bug Fixes

- *(scripts)* Include scripts directory in pyproject
- *(tracker)* Body not converting timedeltas correctly
- *(endpoints)* Remove wrong types
- Small endpoint & cache changes
- *(scripts)* Remove cache from utility script
- Implement basic import fixes
- *(typing)* Deal with extra mypy warnings
- *(typing)* Add generic and extra typing checks
- *(typing)* Add callable typing
- *(typing)* Remove all implicity re-exports
- *(async-sqlite-cache)* Make sure entry exists before deleting
- *(models)* Revert `TogglClass.from_kwargs` changes

### 🚜 Refactor

- *(cache)* [**breaking**] Simplify abstract cache methods
- *(endpoints)* Use new caching methods
- *(body)* [**breaking**] Replace ValueError with KeyError
- *(body)* [**breaking**] Convert BaseBody class into mapping
- *(body)* [**breaking**] Make verify_endpoint_parameter method private
- *(user)* [**breaking**] Remove deprecated check_authentication method
- *(base_endpoint)* [**breaking**] Remove 'workspace_id' parameter
- *(base_endpoint)* [**breaking**] Remove 'model' property
- *(base_endpoint)* [**breaking**] Remove 'endpoint' property
- *(base_endpoint)* [**breaking**] Remove 'method' helper method
- *(tracker_endpoint)* [**breaking**] Remove typeerror from add method
- *(tracker)* [**breaking**] Move 'current' method to tracker endpoint
- *(tracker)* [**breaking**] Move 'collect' method to tracker endpoint
- *(user)* User actual object for 'get_details' method
- *(tracker)* [**breaking**] Move 'get' method to tracker endpoint
- *(user)* [**breaking**] Remove tracker related info and attributes
- *(endpoints)* Use endpoint property within method
- *(workspaces)* [**breaking**] Remove deprecated workspace id param
- *(reports)* [**breaking**] Remove deprecated methods
- *(trackers)* [**breaking**] Remove start_date parameter from body
- *(tags)* [**breaking**] Remove deprecated optional type from 'edit' endpoint method
- *(config)* [**breaking**] Remove deprecated authentication error
- *(config)* [**breaking**] Togglrc helper function using workspace missing error
- *(base_cache)* [**breaking**] Remove deprecated value error from missing parent error exception
- *(reports)* Use invalid extension error for extension exceptions
- *(reports)* Use invalid extension error for extension exceptions
- *(reports)* [**breaking**] Move reports module into main folder
- [**breaking**] Make most modules private
- [**breaking**] Adjust imports to new directory structure
- *(scripts)* Remove cache requirement from cleanup utility
- *(cache)* Update schema generation
- *(async)* Update __init__ file
- *(workspace)* [**breaking**] Make workspace module private
- *(async)* All async endpoints accept client
- *(exceptions)* Move exceptions into seperate module
- *(project)* [**breaking**] Convert 'active' param default to a boolean
- Use a src folder for the library
- *(typing)* Cast any returns to correct type
- Update all modules to new ruff rules
- *(endpoint)* Cast model to generic class
- *(metadata)* Convert _version.py to __about__.py

### 📚 Documentation

- *(user, tracker)* Split up tracker & user endpoint pages
- *(user, tracker)* Split up tracker & user endpoint pages
- *(scripts)* Utility for generating project diagrams
- Update to project structure
- Small fixes & config improvements
- *(async)* Add references for classes
- *(examples)* Add async example
- *(examples)* Fix outdated imports
- *(contributing)* Update contrib docs
- *(api)* Update diagrams
- *(mkdocs)* Update configurate for src layout
- *(api-guide)* Fix bad relative links
- *(scripts)* Update diagram script to new src layout
- *(api-guide)* Update diagrams
- *(contributing)* Update contributing guideline to uv
- *(installation)* Include aiosqlite in optional dependencies
- *(mkdocs)* Add inventories to mkdocstrings

### ⚙️ Miscellaneous Tasks

- *(dev-deps)* Add pytest asyncio
- *(pytest)* Set asyncio mode
- *(dev-deps)* Added ruff formatter
- *(dev-deps)* Update mkdocstrings-python dependency
- *(coverage)* Keep coverage for tests
- *(tox)* Make sure to install all extras
- *(actions)* Do not run slow tests on most matrix combos
- *(pre-commit)* Update ruff & mypy pre-commit
- *(pre-commit)* Update pre-commit configuration
- *(git)* Update .gitignore file
- *(pre-commit)* Add uv to configuration
- *(ruff)* Refactor configuration
- *(ruff)* Refactor ruff configuration
- *(mypy)* Remove unnecessary errors codes from tests
- *(pre-commit)* Make sure to fix in ruff pre-commit
- *(ruff)* Ignore ARG code in tests
- *(tox)* Update tox config to toml format
- *(actions)* Update actions to use uv
- *(git-cliff)* Handle ref type as a refactor
- *(git-cliff)* Add build section to commit parser
- *(pyproject)* Add keywords section to pyproject.toml

### 🏗  Build

- *(project)* Convert project management to uv
- *(lint,type-check)* Change target python version
- *(pre-commit)* Add SQLAlchemy stubs to pre-commit

### 🧪 Testing

- Replace removed methods with alternatives
- *(async)* Base fixtures setup
- Tracker factory fixture
- *(async-sqlite)* All cache functionality
- Implement generator function fixtures
- Fix minor issues
- *(tags)* Tag get method
- *(org)* Mark organization tests slow
- *(async)* Set default fixture loop scope
- 100% test suite usage
- *(coverage)* Add source folders
- Adjust tests to new linting rules
- *(async-trackers)* Use utc timezone with `datetime.now`

## [1.6.0] - 2024-12-19

### 🚀 Features

- *(endpoints)* Build request private helper method
- *(cache)* Model helper property

### 🚜 Refactor

- *(endpoints)* Remove unnecessary ruff ignore flag
- *(endpoints)* Convert process_models into clasmethod
- *(endpoints)* Make client attribute public
- *(endpoints)* Request handle error helper private method
- *(endpoints)* Process_response private helper method
- *(endpoints)* Improve request method readability
- *(json-cache)* Uses new model property
- *(sqlite-cache)* Uses new model property
- *(reports)* Adjust report endpoint to base
- *(endpoints)* Use MODEL classvar instead of property
- *(cached_endpoint)* Adjust subclass to new structure
- *(cached_endpoint)* Log info about cache expiration
- Remove all optional types

### 🕸 Deprecations

- *(endpoints)* Deprecate 'method' helper method in favour of build_request
- *(endpoints)* Deprecate model property in favour of class variable
- *(endpoints)* Deprecate 'endpoint' property in favour of 'BASE_ENDPOINT' ClassVar

### 📚 Documentation

- *(json_cache)* Encoder & decoder docstrings

### ⚙️ Miscellaneous Tasks

- *(ruff)* Ignore tc006 code
- *(cliff)* Ignore merge commits
- *(cliff)* Merge cliff.toml with pyproject

## [1.5.1] - 2024-11-26

### 🐛 Bug Fixes

- *(models)* From_kwargs not incorporating organization id

### 📚 Documentation

- *(endpoints)* Correct and improve docstrings
- *(cache, config)* Remove unnecessary type on return value in docstrings

## [1.5.0] - 2024-11-25

### 🚀 Features

- *(workspace)* Organization id accepts a model
- *(utility)* Deprecation helper method
- *(tags)* Single get endpoint convenience method
- *(models)* Add start and end date to project model
- *(utility)* Get_timestamp helper function
- *(models)* Project status enum
- *(models)* Project get_status method
- *(projects)* Status to query helper method
- *(endpoints)* Implement re_raise parameter
- *(endpoints)* Implement retries parameter
- *(trackers)* Bulk edit item typed dict
- *(trackers)* Edit named tuple data structure
- *(trackers)* Bulk edit patch endpoint method

### 🐛 Bug Fixes

- *(projects)* Default color for using old gray hex code
- *(models)* Missing pound sign on project default color
- *(projects)* Edit & add method return type had none

### 🚜 Refactor

- *(workspace)* Deprecate workspace_id argument correctly
- *(user)* Add workspace_id param to endpoint + model type
- *(tracker)* Add workspace_id param to endpoint + model type
- *(projects)* Add workspace_id param to endpoint + model type
- *(clients)* Add workspace_id param to endpoint + model type
- *(tags)* Add workspace_id param to endpoint + model type
- *(user)* Current endpoint will try refresh if no tracker is running
- *(clients)* Properly implement collect endpoint cache queries
- *(cache)* Json serializer formating date objects
- *(user)* Collect method uses get_timestamp helper
- *(workspace)* Collect method uses get_timestamp helper
- *(projects)* Add collect endpoint method body attributes
- *(projects)* Collect method endpoint format method helper
- *(projects)* Implement new body attributes into format method
- *(projects)* Update project collect method to include querying cache
- *(models)* Prevent unnecessary datetime call
- *(endpoints)* Change default timeout parameter
- *(utility)* [**breaking**] Turn requires into a private function
- *(tracker)* Improve edit endpoint method
- *(endpoints)* Request method accepts lists as a body
- *(trackers)* Update body parameters

### 🕸 Deprecations

- *(meta)* Base endpoint workspace_id argument removal
- *(projects)* Get color argument name
- *(trackers)* Body start_date parameter

### 📚 Documentation

- *(user)* Update current endpoint docstring
- *(tags)* Update get method docstring
- *(models)* Helper method docstrngs
- *(projects)* Update basic color docstrings
- *(projects)* Add and update all endpoint + body docstrings
- *(cache)* Remove docstring newlines
- *(endpoints)* Improve all endpoint parameter documentation
- *(trackers)* Add new functionality
- *(mermaid)* Update package diagrams
- *(models)* Improve docstring parameters
- *(models)* Document from_kwargs classmethod

### ⚙️ Miscellaneous Tasks

- *(actions)* Change release & documentation workflow dependency
- *(ruff)* Ignore PLR0913 code
- *(ruff)* Ignore C901 code

### 🧪 Testing

- *(projects)* Validate new body params
- *(projects)* Validate status_to_query method
- *(projects)* Sample data fixture
- *(projects)* Check collect method endpoint parameters
- *(user)* Validate re_raise works with current tracker
- *(trackers)* Validate bulk edit endpoint
- *(utils)* Improve version testing

## [1.4.0] - 2024-11-11

### 🚀 Features

- *(exceptions)* Custom exceptions for commonly raised value errors
- *(cache)* Custom missing parent error

### 🐛 Bug Fixes

- *(project)* Wrong hex code for gray color
- *(utils)* Remove unnecessary import

### 🚜 Refactor

- *(tag)* Edit endpoint method accepts seperate name argument
- *(tag)* Validate minimum name length
- *(endpoint)* Use generics with base endpoint
- *(cache)* User generic type with cache
- *(endpoint)* Assign generics to all endpoints
- *(endpoint)* Cache query method always returns list
- *(typing)* Generics implementation
- *(workspace)* Use custom exceptions for raised errors
- *(user)* Use custom exceptions for raised errors
- *(user)* Use custom exceptions for raised errors
- *(tag)* Use custom exceptions for raised errors
- *(project)* Use custom exceptions for raised errors
- *(client)* Use custom exceptions for raised errors
- *(models)* Use naming error instead of value error
- *(cache)* Implement new error subclass

### 🕸 Deprecations

- *(tag)* Remove the internal usage of a modified name in a tag
- *(trackers)* Change exception type in add endpoint method

### 📚 Documentation

- *(tag)* Update edit endpoint docstring
- *(tag)* Improve delete endpoint docstring
- *(tag)* Improve add endpoint method docstring
- *(tag)* Improve endpoint class docstring
- *(organization)* Use custom exceptions for raised errors docstring
- *(exceptions)* Document new exception classes
- *(mkdocs)* Enable symbols in table of contents
- *(config)* Reconfigure headings

### 🧪 Testing

- *(tag)* Validate tag name length
- *(conftest)* Rate limit trackers teardown
- *(utility)* Make sure version is updated

## [1.3.2] - 2024-11-05

### 🐛 Bug Fixes

- *(cache)* Json query hashable type error
- *(cache)* Check for all sequences

### 📚 Documentation

- *(endpoint)* Improve cached endpoint docstrings
- *(cache)* Improve base cache docstring
- *(cache)* Improve json cache docstrings
- *(cache)* Improve sqlite cache docstrings

### 🧪 Testing

- *(cache)* Test for distinct flag and unhashable types

## [1.3.1] - 2024-11-02

### 🐛 Bug Fixes

- *(user)* Refresh not getting passed to request
- *(cache)* Json query distinct & list comparisons

### 🚜 Refactor

- *(endpoints)* Add future type import

### 📚 Documentation

- *(tracker)* Add examples to docstrings

## [1.3.0] - 2024-10-31

### 🚀 Features

- *(workspace)* Workspace body dataclass
- *(workspace)* Add workspace endpoint
- *(workspace)* Collect workspaces endpoint
- *(workspace)* Edit workspace endpoint
- *(workspace)* Get time constraints
- *(workspace)* Statistics endpoint
- *(models)* Organization model
- *(schema)* Added organization model
- *(endpoint)* Added organization endpoint
- *(organization)* Add endpoint method
- *(organization)* Get endpoint method
- *(models)* Validate organization name
- *(models)* Validate workspace name
- *(organization)* Edit endpoint method
- *(organization)* Collect endpoint method
- *(organization)* Delete endpoint method
- *(workspace)* Organization id property
- *(utility)* Add org endpoint to cleanup
- Add organization objects to __init__

### 🐛 Bug Fixes

- *(endpoint)* Api status not catching json decode error
- *(body)* Verifying wrong variable
- *(organization)* Make sure edit method stores and returns model

### 🚜 Refactor

- *(workspace)* Use a blank endpoint property
- *(endpoint)* [**breaking**] Remove unnecessary class variables
- *(workspace)* Improve get method error handling

### 🕸 Deprecations

- *(workspace)* Accept organization instead of workspace
- *(workspace)* Turn get method workspace argument optional

### 📚 Documentation

- *(examples)* Improve authentication information
- *(workspace)* Document new workspace features
- *(workspace)* Improve docstrings
- *(api)* Update project structure and mermaid
- *(organization)* Add organization to api reference
- *(workspace)* Add typed dicts to api documentation
- *(config)* Reword deprecation
- *(models)* Improve model documentation

### ⚙️ Miscellaneous Tasks

- *(dev-deps)* Pytest dependency added
- *(actions)* Add new secrets to environment

### 🧪 Testing

- *(conftest)* Organization id fixture
- *(workspace)* Cover new endpoint methods
- *(tags)* Extra delete method validation
- *(user)* Fix test date creation
- *(workspace)* Use org id instead
- *(organization)* Test all functionality
- *(conftest)* User id fixture

## [1.2.0] - 2024-10-27

### 🚀 Features

- *(user)* User details endpoint
- *(user)* Verify authentication static method

### 🐛 Bug Fixes

- *(user)* Authentication verifier using wrong endpoint

### 🚜 Refactor

- *(endpoint)* User httpx error codes
- *(user)* Remove endpoint property forward slash

### 🕸 Deprecations

- *(user)* Check authentication method convert to staticmethod

### 📚 Documentation

- *(user)* Update documentation

## [1.1.1] - 2024-10-25

### 🐛 Bug Fixes

- *(config)* Revert exception type change
- *(cache)* Check if the model has been deleted already

### ⚙️ Miscellaneous Tasks

- *(actions)* Documentation requires test to pass

## [1.1.0] - 2024-10-25

### 🚀 Features

- *(cache)* Json session refresh method
- *(config)* Get workspace helper function
- *(config)* Togglrc workspace retrieve helper function

### 🐛 Bug Fixes

- *(cache)* Json session diff method not including completely new models

### 🚜 Refactor

- *(config)* Extract togglrc retriever

### 📚 Documentation

- *(config)* Add example to config helper functions
- *(config)* Add new helper functions

### 🧪 Testing

- *(cache)* Test session refresh method and diffing
- Validate more errors

## [1.0.4] - 2024-10-24

### 🐛 Bug Fixes

- *(cache)* Json commit not syncing correctly

### 📚 Documentation

- *(cache)* Improve json docstring

## [1.0.3] - 2024-10-22

### 🐛 Bug Fixes

- *(client)* Collect method not passing on refresh
- *(endpoint)* Methods are abiding refresh argument
- *(user)* Current tracker actually using cache
- *(cache)* Json not refreshing in find method

### 📚 Documentation

- *(contributing)* Add more references
- *(endpoint)* Add a note for methods using external api every time
- *(api)* Update mermaid graphs
- *(api)* Project structure

### 🧪 Testing

- *(conftest)* Change number fixture

## [1.0.2] - 2024-10-18

### 🕸 Deprecations

- *(reports)* Rename methods to be consistent across reports

### 📚 Documentation

- *(readme)* Add changelog to links
- *(reports)* Add raises to docstrings
- *(api)* Small formatting changes

### ⚙️ Miscellaneous Tasks

- *(config)* Coverage url
- *(cliff)* Fix toml escape characters

## [1.0.1] - 2024-10-16

### 🐛 Bug Fixes

- *(endpoint)* Logger name
- *(user)* Collect endpoint not returning anything without parameters

### 📚 Documentation

- *(cache)* Fix docstring

### ⚙️ Miscellaneous Tasks

- *(precommit)* Added gitleaks
- *(config)* Additional urls

### 🧪 Testing

- *(user)* Collect method with no parameters

## [1.0.0] - 2024-10-15

### 🚀 Features

- *(utility)* Requires decorator
- Python 3.13 support
- *(cache)* Comparison enumeration
- *(cache)* Toggl query dataclass

### 🐛 Bug Fixes

- *(tracker)* Adjust error type
- *(utility)* Swap datetime conditional
- *(endpoint)* Refactor server error retry logic
- *(endpoints)* Return none on 404
- *(cache)* Sqlite delete method
- *(user)* Collect method not correctly formatting time arguments

### 🚜 Refactor

- [**breaking**] Merge modules with toggl_api
- *(endpoints)* [**breaking**] Remove deprecated methods
- *(body)* [**breaking**] Remove deprecated workspace_id parameter
- *(deps)* [**breaking**] Convert sqlalchemy to optional dependency
- *(workspace)* Improved get endpoint
- *(client)* Use literal for typing status strings
- *(tag)* Delete endpoint typing
- *(reports)* Make pagination options optional
- *(cache)* [**breaking**] Remove inverse flag
- *(cache)* Abstract class query method
- *(cache)* Json query method
- *(cache)* Sqlite query method
- *(user)* Fully implement collect method cache retrieval
- *(endpoints)* Logging for caught exceptions
- Additional debug logging
- *(models)* Remove optional type from timestamp
- *(cache)* Fix typing issues

### 📚 Documentation

- *(readme)* Update readme
- *(api)* Update docs to new directory structure
- Update examples
- *(mermaid)* Update diagrams
- *(cache)* Improved metaclass
- *(panzoom)* Full screen enabled
- *(endpoints)* Add official api links
- Show source on endpoints
- *(example)* Reports example
- *(readme)* Add examples
- *(cache)* Query docstrings added
- *(example)* Logging example
- *(contributing)* Additional instructions

### 🎨 Styling

- *(cache)* Remove optional type annotation as return

### ⚙️ Miscellaneous Tasks

- Update coverage config
- *(precommit)* Added mypy
- *(nvim)* Function for generating official docstrings
- *(actions)* Simplify workflows
- *(typing)* Add py.typed file

### 🧪 Testing

- *(user)* Additional status code tests
- *(endpoints)* Additional argument types
- *(reports)* Validate extensions
- *(tracker)* Mock http status code logic
- *(sqlite)* Additional tests
- *(conftest)* Only delay on integration tests
- *(tracker)* Verify creation dates logic
- More coverage
- *(cache)* Query conversion

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
