import pytest
from httpx import HTTPStatusError

from toggl_api.asyncio import AsyncWeeklyReportEndpoint


@pytest.fixture
def aweekly_rep_ep(get_workspace_id, config_setup):
    return AsyncWeeklyReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.unit
def test_verify_endpoint_url(aweekly_rep_ep, get_workspace_id):
    assert aweekly_rep_ep.workspace_id == get_workspace_id
    assert aweekly_rep_ep.endpoint.endswith(f"{get_workspace_id}/weekly/time_entries")


@pytest.mark.integration
async def test_search_time_entries(aweekly_rep_ep, report_body):
    assert isinstance(await aweekly_rep_ep.search_time_entries(report_body), list)


@pytest.mark.parametrize(
    ("extension"),
    [
        pytest.param(
            "pdf",
            marks=pytest.mark.xfail(
                raises=HTTPStatusError,
                reason="Issue with the Toggl API server.",
            ),
        ),
        "csv",
    ],
)
@pytest.mark.integration
async def test_export_report(extension, aweekly_rep_ep, report_body, add_multiple_trackers):
    assert isinstance(await aweekly_rep_ep.export_report(report_body, extension), bytes)
