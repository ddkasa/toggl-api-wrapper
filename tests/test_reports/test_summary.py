# ruff: noqa: DTZ011

from datetime import date, timedelta

import pytest

from toggl_api.reports import ReportBody, SummaryReportEndpoint


@pytest.fixture
def summary_report(get_workspace_id, config_setup):
    return SummaryReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.unit
def test_verify_summary_endpoint_url(summary_report, get_workspace_id):
    assert summary_report.workspace_id == get_workspace_id
    assert summary_report.endpoint.endswith(f"workspace/{get_workspace_id}")


@pytest.mark.unit
def test_report_body(report_body, get_workspace_id):
    format_body = report_body.format("endpoint")
    assert isinstance(format_body, dict)
    report_body.start_date = date.today()
    report_body.end_date = date.today() + timedelta(2)
    format_body = report_body.format("endpoint")

    assert isinstance(format_body["start_date"], str)
    assert format_body["start_date"] == report_body.start_date.isoformat()

    assert isinstance(format_body["end_date"], str)
    assert format_body["end_date"] == report_body.end_date.isoformat()


@pytest.mark.integration
def test_project_summary(summary_report, gen_proj):
    summ = summary_report.project_summary(gen_proj, date.today(), date.today())
    assert isinstance(summ, dict)


@pytest.mark.integration
def test_project_summaries(summary_report, gen_proj):
    summ = summary_report.project_summaries(date.today(), date.today())
    assert isinstance(summ, list)


@pytest.mark.integration
def test_time_entries(
    summary_report: SummaryReportEndpoint,
    report_body,
    add_multiple_trackers,
):
    trackers = summary_report.search_time_entries(report_body)
    assert isinstance(trackers, dict)


@pytest.mark.parametrize(
    ("extension"),
    [
        "pdf",
        "csv",
    ],
)
@pytest.mark.integration
def test_export_summary(
    extension,
    summary_report: SummaryReportEndpoint,
    report_body: ReportBody,
    add_multiple_trackers,
):
    assert isinstance(summary_report.export_report(report_body, extension), bytes)
