::: toggl_api.modules.tracker.TrackerBody
    options:
        members:
            - format_body

::: toggl_api.modules.tracker.TrackerEndpoint 
    options:
        members:
            - edit_tracker
            - delete_tracker
            - stop_tracker
            - add_tracker

::: toggl_api.modules.user.UserEndpoint
    options:
        show_source: true
        members:
            - current_tracker
            - get_trackers
            - get_tracker
            - check_authentication
