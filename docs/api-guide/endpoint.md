::: toggl_api.meta.RequestMethod
    options:
        show_source: true

***

::: toggl_api.meta.TogglEndpoint
    options:
        show_source: true
        members:
            - request
            - method
            - process_models
            - endpoint
            - model
            - api_status

::: toggl_api.asyncio.TogglAsyncEndpoint

***

::: toggl_api.meta.TogglCachedEndpoint
    options:
        show_source: true
        members:
            - request
            - load_cache
            - save_cache
            - cache
            - query

::: toggl_api.asyncio.TogglAsyncCachedEndpoint
