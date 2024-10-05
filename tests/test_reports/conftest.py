# ruff: noqa: DTZ011

import time
from datetime import date, datetime, timezone

import pytest

from toggl_api import TrackerBody
from toggl_api.modules.reports import ReportBody


@pytest.fixture
def add_multiple_trackers(tracker_object, faker, create_project):
    trackers = []
    for i in range(5, 10):
        time.sleep(1)
        body = TrackerBody(
            tracker_object.workspace_id,
            description=faker.name(),
            project_id=create_project.id,
            start=datetime.now(tz=timezone.utc).replace(hour=i),
            stop=datetime.now(tz=timezone.utc).replace(hour=i + 1),
        )
        trackers.append(tracker_object.add(body=body))

    yield trackers
    for tracker in trackers:
        tracker_object.delete(tracker)


@pytest.fixture
def report_body(get_workspace_id):
    return ReportBody(date.today(), date.today())
