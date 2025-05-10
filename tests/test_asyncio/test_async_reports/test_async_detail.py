import pytest

from toggl_api.asyncio import AsyncDetailedReportEndpoint
from toggl_api.reports import PaginatedResult, PaginationOptions


@pytest.fixture
def adetail_rep_ep(get_workspace_id, config_setup):
    return AsyncDetailedReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.unit
def test_verify_detail_summary_url(get_workspace_id, adetail_rep_ep):
    assert adetail_rep_ep.workspace_id == get_workspace_id
    assert adetail_rep_ep.endpoint.endswith(f"{get_workspace_id}/search/time_entries")


@pytest.mark.integration
async def test_search_time(adetail_rep_ep, add_multiple_trackers, report_body):
    assert isinstance(
        await adetail_rep_ep.search_time_entries(
            report_body,
            PaginationOptions(),
        ),
        PaginatedResult,
    )


@pytest.mark.integration
async def test_search_time_pagination(adetail_rep_ep, add_multiple_trackers, report_body):
    result = await adetail_rep_ep.search_time_entries(report_body, PaginationOptions(1))
    assert isinstance(result, PaginatedResult)
    assert isinstance(result.next_id, int)
    assert isinstance(result.next_row, int)
    for _ in range(3):  # pragma: no cover  # NOTE: If loop breaks beforehand.
        result = await adetail_rep_ep.search_time_entries(
            report_body,
            result.next_options(1),
        )
        assert isinstance(result, PaginatedResult)
        if result.next_id is None or result.next_row is None:
            break


@pytest.mark.integration
async def test_totals_report(adetail_rep_ep, add_multiple_trackers, report_body):
    report = await adetail_rep_ep.totals_report(report_body)
    assert isinstance(report, dict)
    assert isinstance(report.get("seconds"), int)


@pytest.mark.parametrize(
    ("extension"),
    [
        "pdf",
        "csv",
    ],
)
@pytest.mark.integration
async def test_export_report(extension, adetail_rep_ep, report_body, add_multiple_trackers):
    summ = await adetail_rep_ep.export_report(report_body, extension, PaginationOptions())
    assert isinstance(summ, PaginatedResult)
    assert isinstance(summ.result, bytes)
