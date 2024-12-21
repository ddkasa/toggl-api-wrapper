## General Cache Flow

```mermaid
{% include "static/mermaid/cache.mmd" %}
```

::: toggl_api.meta.cache.MissingParentError

::: toggl_api.meta.cache.TogglCache

---

# Querying

::: toggl_api.meta.cache.Comparison
    options:
        show_source: true

::: toggl_api.meta.cache.TogglQuery
    options:
        show_source: true

---

# SQLite

> [!INFO]
> Make sure to install SQLAlchemy if using SqliteCache with `pip install toggl-api-wrapper[sqlite]`

::: toggl_api.meta.cache.SqliteCache
    options:
        show_source: true

---

# JSON

::: toggl_api.meta.cache.JSONSession
    options:
        show_source: true

::: toggl_api.meta.cache.JSONCache
    options:
        show_source: true
