## Abstract Classes

::: toggl_api.models.TogglClass
    options:
        show_source: true
        members: 
            - from_kwargs

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
            - from_kwargs

::: toggl_api.TogglWorkspace
    options:
        show_source: true
        members:
            - validate_name
            - from_kwargs

::: toggl_api.TogglClient
    options:
        show_source: true
        members:
          - from_kwargs

::: toggl_api.TogglProject
    options:
        show_source: true
        members:
            - Status
            - get_status
            - from_kwargs

::: toggl_api.TogglTracker
    options:
        show_source: true
        members:
            - running
            - from_kwargs

::: toggl_api.TogglTag
    options:
        show_source: true
        members:
            - from_kwargs

::: toggl_api.models.as_dict_custom
    options:
        show_source: true
