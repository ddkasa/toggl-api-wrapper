All Tracker, Client, Project & Tag endpoints will have most of these methods:

1. **collect**: Gathering models.
2. **get**: Retrieving a model.
3. **delete**: Deleting a model.
4. **edit**: Editing a model.
5. **add**: Creating a new model.

---

- With environment variables setup correctly.

### Tracker Example

```python
{% include "examples/tracker_example.py" %}
```

**Outputs**:

```python
>>> TogglTracker(
        id=3482231563,
        name="My First Tracker",
        workspace=2313123123,
        start=datetime.datetime(2024, 6, 10, 14, 59, 20, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(seconds=1, microseconds=179158),
        stop=None,
        project=None,
        tags=[],
    )
```

### Project Example

```python
{% include "examples/project_example.py" %}
```

**Outputs**:

```python
>>> TogglProject(
        id=203366783,
        name='My First Project',
        workspace=2313123123,
        color='#d92b2b',
        client=65298912,
        active=True,
    )
```

### Report Example

- With **Plotly**, **Pandas** and **Kaleidoscope** installed.

```python
{% include "examples/reports_example.py" %}
```

**Outputs**:

![Total recorded monthly minutes spent on Toggl API Wrapper in 2024](../static/images/total-minutes-may-to-october-2024.svg)

## Applications Using Toggl API Wrapper

- [Ulauncher Toggl Extension](https://github.com/ddkasa/ulauncher-toggl-extension)
