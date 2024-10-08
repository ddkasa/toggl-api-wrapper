import pytest
from httpx import HTTPStatusError

from toggl_api.reports import WeeklyReportEndpoint


@pytest.fixture
def weekly_report_endpoint(get_workspace_id, config_setup):
    return WeeklyReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.unit
def test_verify_endpoint_url(weekly_report_endpoint, get_workspace_id):
    assert weekly_report_endpoint.workspace_id == get_workspace_id
    assert weekly_report_endpoint.endpoint.endswith(f"{get_workspace_id}/weekly/time_entries")


@pytest.mark.integration
def test_search_time_entries(weekly_report_endpoint, report_body):
    assert isinstance(weekly_report_endpoint.search_time_entries(report_body), list)


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
def test_export_report(extension, weekly_report_endpoint, report_body, add_multiple_trackers):
    assert isinstance(weekly_report_endpoint.export_report(report_body, extension), bytes)
