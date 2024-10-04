# ruff: noqa: DTZ011

import random
from datetime import date, timedelta

import pytest

from toggl_api.modules.reports.reports import ReportBody, SummaryReportEndpoint


@pytest.fixture
def summary_report(get_workspace_id, config_setup):
    return SummaryReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.unit
def test_verify_summary_endpoint_url(summary_report, get_workspace_id):
    assert summary_report.workspace_id == get_workspace_id
    assert summary_report.endpoint.endswith(f"workspace/{get_workspace_id}/")


@pytest.mark.unit
def test_report_body(report_body, get_workspace_id):
    format_body = report_body.format(get_workspace_id)

    assert isinstance(format_body, dict)
    assert format_body["workspace_id"] == get_workspace_id

    report_body.start_date = date.today()
    report_body.end_date = date.today() + timedelta(2)
    format_body = report_body.format(random.randint(100000, 999999))
    assert format_body["workspace_id"] == get_workspace_id
    assert format_body["start_date"] == report_body.start_date.isoformat()
    assert format_body["end_date"] == report_body.end_date.isoformat()


@pytest.mark.integration
def test_project_summary(summary_report, create_project):
    summ = summary_report.project_summary(create_project, date.today(), date.today())
    assert isinstance(summ, dict)


@pytest.mark.integration
def test_project_summaries(summary_report, create_project):
    summ = summary_report.project_summaries(date.today(), date.today())
    assert isinstance(summ, list)


@pytest.mark.integration
def test_time_entries(
    summary_report: SummaryReportEndpoint,
    report_body,
    add_multiple_trackers,
):
    trackers = summary_report.time_entries(report_body)
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
    assert isinstance(summary_report.export_summary(report_body, extension), bytes)
