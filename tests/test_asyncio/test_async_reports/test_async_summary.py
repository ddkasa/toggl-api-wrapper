from datetime import date

import pytest

from toggl_api.asyncio import AsyncSummaryReportEndpoint
from toggl_api.reports import ReportBody


@pytest.fixture
def asummary_report_ep(get_workspace_id, config_setup):
    return AsyncSummaryReportEndpoint(get_workspace_id, config_setup)


@pytest.mark.integration
async def test_project_summary(asummary_report_ep, gen_proj):
    summ = await asummary_report_ep.project_summary(gen_proj, date.today(), date.today())  # noqa: DTZ011
    assert isinstance(summ, dict)


@pytest.mark.integration
async def test_project_summaries(asummary_report_ep, gen_proj):
    summ = await asummary_report_ep.project_summaries(date.today(), date.today())  # noqa: DTZ011
    assert isinstance(summ, list)


@pytest.mark.integration
async def test_time_entries(
    asummary_report_ep: AsyncSummaryReportEndpoint,
    report_body,
    add_multiple_trackers,
):
    trackers = await asummary_report_ep.search_time_entries(report_body)
    assert isinstance(trackers, dict)


@pytest.mark.parametrize(
    ("extension"),
    [
        "pdf",
        "csv",
    ],
)
@pytest.mark.integration
async def test_export_summary(
    extension,
    asummary_report_ep: AsyncSummaryReportEndpoint,
    report_body: ReportBody,
    add_multiple_trackers,
):
    assert isinstance((await asummary_report_ep.export_report(report_body, extension)), bytes)
