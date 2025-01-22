import os
import time
from collections import defaultdict
from datetime import date, datetime

import pandas as pd
import plotly.express as px

from toggl_api.config import generate_authentication
from toggl_api.reports import DetailedReportEndpoint, ReportBody

# Setup Endpoint
WORKSPACE_ID = int(os.environ.get("TOGGL_WORKSPACE_ID", "0"))
AUTH = generate_authentication()
detailed_report_endpoint = DetailedReportEndpoint(WORKSPACE_ID, AUTH)

start_date = date(2024, 1, 1)
end_date = date(2024, 11, 9)
body = ReportBody(
    start_date=start_date,
    end_date=end_date,
    project_ids=[202484947],
)

# Retrieve Data
print("Initial Request")
first = detailed_report_endpoint.search_time_entries(body)
next_page = first.next_options()
content = first.result
while next_page.next_id is not None and next_page.next_row is not None:
    time.sleep(1)
    print(f"Requesting id {next_page.next_id} and row {next_page.next_row}")
    search = detailed_report_endpoint.search_time_entries(body, next_page)
    content.extend(search.result)
    next_page = search.next_options()


# Process Target Data
aggregrate: defaultdict[str, int] = defaultdict(lambda: 0)
for tracker in content:
    time_data = tracker["time_entries"][0]
    start = datetime.strptime(time_data["at"], "%Y-%m-%dT%H:%M:%S%z")
    aggregrate[start.strftime("%B")] += time_data["seconds"] // 60

# Plot & View Data
monthly_minutes = pd.DataFrame(
    aggregrate.items(),
    index=aggregrate.keys(),
    columns=["month", "minutes"],
)
fig = px.bar(
    monthly_minutes,
    "month",
    "minutes",
    title="Total recorded monthly minutes spent on Toggl API Wrapper in 2024",
)
fig.show()
fig.write_image("total-minutes-may-to-october-2024.svg")
