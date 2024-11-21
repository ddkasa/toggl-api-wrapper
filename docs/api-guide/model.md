## Abstract Classes

::: toggl_api.models.TogglClass
    options:
        show_source: true

::: toggl_api.models.WorkspaceChild
    options:
        show_source: true

---

## Main Models

::: toggl_api.TogglOrganization
    options:
        show_source: true
        members:
            - validate_name

::: toggl_api.TogglWorkspace
    options:
        show_source: true
        members:
            - validate_name

::: toggl_api.TogglClient
    options:
        show_source: true

::: toggl_api.TogglProject
    options:
        show_source: true
        members:
            - Status
            - get_status

::: toggl_api.TogglTracker
    options:
        show_source: true
        members:
            - running

::: toggl_api.TogglTag
    options:
        show_source: true
