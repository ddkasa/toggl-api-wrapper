# ruff: noqa: DTZ011

from datetime import date

import pytest

from toggl_api.reports import ReportBody


@pytest.fixture
def report_body(get_workspace_id):
    return ReportBody(date.today(), date.today())
