- With environment variables setup correctly.

### Tracker Example
```python
{% include "examples/tracker_example.py" %}
```
**Outputs**:
```
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
```
>>> TogglProject(
        id=203366783, 
        name='My First Project', 
        workspace=2313123123,
        color='#d92b2b',
        client=65298912,
        active=True,
    )
```
