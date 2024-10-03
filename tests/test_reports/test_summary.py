# ruff: noqa: DTZ011

import random
from datetime import date, datetime, timedelta, timezone

import pytest

from toggl_api import TrackerBody
from toggl_api.modules.reports.reports import ReportBody, SummaryReportEndpoint


@pytest.fixture
def summary_report(get_workspace_id, config_setup):
    return SummaryReportEndpoint(get_workspace_id, config_setup)


@pytest.fixture
def summary_body(get_workspace_id):
    return ReportBody(get_workspace_id, date.today(), date.today())


@pytest.fixture
def add_multiple_trackers(tracker_object, faker, create_project):
    for i in range(5, 10):
        body = TrackerBody(
            tracker_object.workspace_id,
            description=faker.name(),
            project_id=create_project.id,
            start=datetime.now(tz=timezone.utc).replace(hour=i),
            stop=datetime.now(tz=timezone.utc).replace(hour=i + 1),
        )
        tracker_object.add(body=body)


@pytest.mark.unit
def test_summary_body(summary_body, get_workspace_id):
    format_body = summary_body.format(get_workspace_id)

    assert isinstance(format_body, dict)
    assert format_body["workspace_id"] == get_workspace_id

    summary_body.start_date = date.today()
    summary_body.end_date = date.today() + timedelta(2)
    format_body = summary_body.format(random.randint(100000, 999999))
    assert format_body["workspace_id"] == get_workspace_id
    assert format_body["start_date"] == summary_body.start_date.isoformat()
    assert format_body["end_date"] == summary_body.end_date.isoformat()


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
    summary_body,
    add_multiple_trackers,
):
    trackers = summary_report.time_entries(summary_body)
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
    summary_body: ReportBody,
    add_multiple_trackers,
):
    assert isinstance(summary_report.export_summary(summary_body, extension), bytes)
