import pytest

from toggl_api.reports import DetailedReportEndpoint, PaginatedResult, PaginationOptions


@pytest.fixture
def detail_summary_endpoint(get_workspace_id, config_setup):
    return DetailedReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.unit
def test_paginated_results():
    res = PaginatedResult([])
    assert isinstance(res.result, list)
    assert res.next_row is None
    assert res.next_id is None

    res = PaginatedResult([], 1, "1212")
    assert res.next_id == 1
    assert res.next_row == 1212  # noqa: PLR2004


@pytest.mark.unit
def test_verify_detail_summary_url(get_workspace_id, detail_summary_endpoint):
    assert detail_summary_endpoint.workspace_id == get_workspace_id
    assert detail_summary_endpoint.endpoint.endswith(f"{get_workspace_id}/search/time_entries")


@pytest.mark.integration
def test_search_time(detail_summary_endpoint, add_multiple_trackers, report_body):
    assert isinstance(
        detail_summary_endpoint.search_time_entries(
            report_body,
            PaginationOptions(),
        ),
        PaginatedResult,
    )


@pytest.mark.integration
def test_search_time_pagination(
    detail_summary_endpoint,
    add_multiple_trackers,
    report_body,
):
    result = detail_summary_endpoint.search_time_entries(report_body, PaginationOptions(1))
    assert isinstance(result, PaginatedResult)
    assert isinstance(result.next_id, int)
    assert isinstance(result.next_row, int)
    for _ in range(3):  # pragma: no cover  # NOTE: If loop breaks beforehand.
        result = detail_summary_endpoint.search_time_entries(
            report_body,
            result.next_options(1),
        )
        assert isinstance(result, PaginatedResult)
        if result.next_id is None or result.next_row is None:
            break


@pytest.mark.integration
def test_totals_report(detail_summary_endpoint, add_multiple_trackers, report_body):
    report = detail_summary_endpoint.totals_report(report_body)
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
def test_export_report(extension, detail_summary_endpoint, report_body, add_multiple_trackers):
    summ = detail_summary_endpoint.export_report(report_body, extension, PaginationOptions())
    assert isinstance(summ, PaginatedResult)
    assert isinstance(summ.result, bytes)
