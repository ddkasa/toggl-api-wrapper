### Install using pip:

```bash
pip install toggl-api-wrapper
```

### Or if using SQLite cache:

```bash
pip install "toggl-api-wrapper[sqlite]"
```

### Or if using Async classes:

```bash
pip install "toggl-api-wrapper[async]"
```

## Dependencies

### Main

- [HTTPX](https://www.python-httpx.org) - _For requests_

### Optional

- [SQLAlchemy](https://www.sqlalchemy.org) - _For Sqlite cache_
- [Greenlet](https://github.com/python-greenlet/greenlet) - _For Async functionality_
- [AIOSQLite](https://github.com/omnilib/aiosqlite) - _For Async SQLite cache_
