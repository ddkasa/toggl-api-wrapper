## General Cache Flow

```mermaid
{% include "static/mermaid/cache.mmd" %}
```

::: toggl_api.meta.cache.TogglCache

---

# Querying

::: toggl_api.Comparison
    options:
        show_source: true

::: toggl_api.TogglQuery
    options:
        show_source: true

---

# SQLite

> [!INFO]
> Make sure to install sqlalchemy if using SqliteCache with `pip install toggl-api-wrapper[sqlite]`

::: toggl_api.meta.cache.sqlite_cache.SqliteCache

---

# JSON

::: toggl_api.meta.cache.json_cache.JSONSession

::: toggl_api.JSONCache
