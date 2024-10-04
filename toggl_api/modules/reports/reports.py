"""Module for various report endpoints."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Generic, Literal, Optional, TypeVar

from toggl_api.modules.meta import BaseBody, TogglEndpoint
from toggl_api.modules.meta.enums import RequestMethod
from toggl_api.modules.models.models import TogglProject
from toggl_api.utility import format_iso

REPORT_FORMATS = Literal["pdf", "csv"]


def _validate_extension(extension: REPORT_FORMATS) -> None:
    if extension not in {"pdf", "csv"}:
        msg = "Extension argument needs to be 'pdf' or 'csv'."
        raise ValueError(msg)


@dataclass
class ReportBody(BaseBody):
    """Body for summary endpoint which turns into a JSON body."""

    workspace_id: Optional[int] = field(default=None)
    start_date: Optional[date | str] = field(default=None)
    """Start date, example time.DateOnly. Should be less than End date."""
    end_date: Optional[date | str] = field(default=None)
    """End date, example time. DateOnly. Should be greater than Start date."""
    client_ids: list[int | None] = field(default_factory=list)
    """Client IDs, optional, filtering attribute. To filter records with no clients, use [None]."""
    description: Optional[str] = field(default=None)
    """Description, optional, filtering attribute."""
    grouping_ids: list[int] = field(default_factory=list)
    """Group IDs, optional, filtering attribute."""
    grouping: Optional[str] = field(default=None)
    """Grouping option, optional."""
    include_time_entry_ids: bool = field(default=True)  # NOTE: API default is False. Wrapper sets it as True.
    """Whether time entry IDs should be included in the results, optional, default true. Not applicable for export."""
    max_duration_seconds: Optional[int] = field(default=None)
    """Max duration seconds, optional, filtering attribute. Time Audit only,
    should be greater than min_duration_seconds."""
    min_duration_seconds: Optional[int] = field(default=None)
    """Min duration seconds, optional, filtering attribute. Time Audit only,
    should be less than max_duration_seconds."""
    project_ids: list[int | None] = field(default_factory=list)
    """Project IDs, optional, filtering attribute. To filter records with no projects, use [None]."""
    rounding: Optional[int] = field(default=None)
    """Whether time should be rounded, optional, default from user preferences."""
    rounding_minutes: Optional[Literal[0, 1, 5, 6, 10, 12, 15, 30, 60, 240]] = field(default=None)
    """Rounding minutes value, optional, default from user preferences.
    Should be 0, 1, 5, 6, 10, 12, 15, 30, 60 or 240."""
    sub_grouping: Optional[str] = field(default=None)
    """SubGrouping option, optional."""
    tag_ids: list[int | None] = field(default_factory=list)
    """Tag IDs, optional, filtering attribute. To filter records with no tags, use [None]."""
    time_entry_ids: list[int] = field(default_factory=list)
    """TimeEntryIDs filters by time entries."""
    user_ids: list[int] = field(default_factory=list)
    """User IDs, optional, filtering attribute."""
    date_format: Literal[
        "MM/DD/YYYY",
        "DD-MM-YYYY",
        "MM-DD-YYYY",
        "YYYY-MM-DD",
        "DD/MM/YYYY",
        "DD.MM.YYYY",
    ] = field(default="YYYY-MM-DD")  # NOTE: API Default is 'MM/DD/YYYY'
    """Date format, optional, default 'YYYY-MM-DD'."""
    duration_format: Literal["classic", "decimal", "improved"] = field(default="classic")
    """Duration format, optional, default "classic". Can be "classic", "decimal" or "improved"."""
    order_by: Optional[Literal["title", "duration"]] = field(default=None)
    """Order by option, optional, default title. Can be title or duration."""
    order_dir: Optional[Literal["ASC", "DESC"]] = field(default=None)
    """Order direction, optional. Can be ASC or DESC."""
    resolution: Optional[str] = field(default=None)
    """Graph resolution, optional. Allow clients to explicitly request a resolution."""
    collapse: bool = field(default=False)
    """Whether collapse others, optional, default false."""

    def format(self, workspace_id: int) -> dict[str, Any]:  # noqa: C901, PLR0912
        body: dict[str, Any] = {
            "workspace_id": self.workspace_id or workspace_id,
            "include_time_entry_ids": self.include_time_entry_ids,
            "client_ids": self.client_ids,
            "project_ids": self.project_ids,
            "tag_ids": self.tag_ids,
            "time_entry_ids": self.time_entry_ids,
            "user_ids": self.user_ids,
            "date_format": self.date_format,
            "duration_format": self.duration_format,
            "collapse": self.collapse,
        }

        if self.start_date is not None:
            body["start_date"] = format_iso(self.start_date)

        if self.end_date is not None:
            body["end_date"] = format_iso(self.end_date)

        if self.description is not None:
            body["description"] = self.description

        if self.grouping_ids:
            body["grouping_ids"] = self.grouping_ids

        if self.grouping:
            body["grouping"] = self.grouping

        if isinstance(self.max_duration_seconds, int):
            body["max_duration_seconds"] = self.max_duration_seconds

        if isinstance(self.min_duration_seconds, int):
            body["min_duration_seconds"] = self.min_duration_seconds

        if isinstance(self.rounding, int):
            body["rounding"] = self.rounding

        if isinstance(self.rounding_minutes, int):
            body["rounding_minutes"] = self.rounding_minutes

        if self.sub_grouping is not None:
            body["sub_grouping"] = self.sub_grouping

        if self.order_by is not None:
            body["order_by"] = self.order_by

        if self.order_dir is not None:
            body["order_dir"] = self.order_dir

        if self.resolution is not None:
            body["resolution"] = self.resolution

        return body


class ReportEndpoint(TogglEndpoint):
    """Abstract baseclass for the reports endpoint that overrides BASE_ENDPOINT."""

    BASE_ENDPOINT = "https://api.track.toggl.com/reports/api/v3/"

    @property
    def model(self) -> None:  # type: ignore[override]
        return None


class SummaryReportEndpoint(ReportEndpoint):
    """Summary reports endpoints.

    [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports)
    """

    def project_summary(
        self,
        project: TogglProject | int,
        start_date: date | str,
        end_date: date | str,
    ) -> list[dict[str, int]]:
        """Returns a specific projects summary within the parameters provided.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-load-project-summary)

        Args:
            project: Project to retrieve summaries about.
            start_date: The date to gather project summary data from.
            end_date: The date to gather project summary data to.


        Returns:
            list: A list of dictionary with the summary data.
        """

        return self.request(
            f"projects/{project.id if isinstance(project, TogglProject) else project}/summary",
            method=RequestMethod.POST,
            body={
                "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
                "end_date": end_date.isoformat() if isinstance(end_date, date) else end_date,
            },
        )

    def project_summaries(
        self,
        start_date: date | str,
        end_date: date | str,
    ) -> list[dict[str, int]]:
        """Returns a summary of user projects according to parameters provided.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-list-project-users)

        Args:
            start_date: The date to gather project summaries from.
            end_date: The date to gather project summaries data to.

        Returns:
            list: A list of dictionary with the summary data.
        """

        return self.request(
            "projects/summary",
            method=RequestMethod.POST,
            body={
                "start_date": format_iso(start_date),
                "end_date": format_iso(end_date),
            },
        )

    def time_entries(
        self,
        body: ReportBody,
    ) -> list[dict[str, int]]:
        """Returns a list of time entries within the parameters specified.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-search-time-entries)

        Args:
            body: Body parameters to filter time entries by.

        Returns:
            list: A list of dictionaries with the filtered tracker data.
        """
        return self.request(
            "summary/time_entries",
            method=RequestMethod.POST,
            body=body.format(self.workspace_id),
        )

    def export_summary(
        self,
        body: ReportBody,
        extension: REPORT_FORMATS,
    ) -> bytes:
        """Downloads summary report in the specified in the specified format: csv or pdf.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-export-summary-report)

        Args:
            body: Body parameters to filter the report by.
            extension: What format to use for the report. CSV or PDF.

        Returns:
            object: A format ready to be saved as a file or used for further processing.
        """
        _validate_extension(extension)

        return self.request(
            f"summary/time_entries.{extension}",
            method=RequestMethod.POST,
            body=body.format(self.workspace_id),
            raw=True,
        )

    @property
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT + f"workspace/{self.workspace_id}/"


T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """Generic dataclass for paginated results."""

    result: T = field()
    next_id: int = field()
    next_row: int = field()


class DetailedReportEndpoint(ReportEndpoint):
    """Detailed reports endpoint.

    [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports)
    """

    def search_time_entries(
        self,
        body: ReportBody,
        next_id: Optional[int] = None,
        next_row: Optional[int] = None,
    ) -> PaginatedResult:
        """Returns time entries for detailed report according to the given filters.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-search-time-entries)

        Args:
            body: JSON body with filters for time entries.
            next_id: Next id of the time entry for pagination.
            next_row: Next row of pagination functionality.

        Returns:
            PaginatedResult: data with pagination information if required.
        """
        data = self.request(
            "",
            body=body.format(self.workspace_id),
            method=RequestMethod.POST,
        )

        return PaginatedResult(data)

    def export_report(self, body: ReportBody, extension: REPORT_FORMATS) -> bytes:
        """Downloads detailed report in pdf or csv format.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-export-detailed-report)

        Args:
            body: JSON body for formatting and filtering the report.
            extension: Format of the exported report. PDF or CSV.

        Returns:
            bytes: Report ready to be saved or further processed in python.
        """
        _validate_extension(extension)
        return self.request(
            f".{extension}",
            body=body.format(self.workspace_id),
            method=RequestMethod.POST,
            raw=True,
        )

    def totals_report(self, body: ReportBody) -> dict[str, int]:
        """Returns totals sums for detailed report.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-load-totals-detailed-report)

        Args:
            body: JSON body for filtering the report.

        Returns:
            dict: With the totals relevant to the provided filters.

        """
        return self.request(
            "/totals",
            body=body.format(self.workspace_id),
            method=RequestMethod.POST,
        )

    @property
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT + f"workspace/{self.workspace_id}/search/time_entries"
