"""Module for various report endpoints."""

import warnings
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Generic, Literal, Optional, TypeVar

from httpx import Response

from toggl_api.meta import BaseBody, TogglEndpoint
from toggl_api.meta.enums import RequestMethod
from toggl_api.models.models import TogglProject
from toggl_api.utility import format_iso

REPORT_FORMATS = Literal["pdf", "csv"]


T = TypeVar("T")


@dataclass(frozen=True)
class PaginationOptions:
    """Dataclass for paginate endpoints."""

    page_size: int = field(default=50)
    next_id: Optional[int] = field(default=None)
    next_row: Optional[int] = field(default=None)


@dataclass
class PaginatedResult(Generic[T]):
    """Generic dataclass for paginated results."""

    result: T = field()
    next_id: Optional[int] = field(default=None)
    next_row: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        # NOTE: Header types are strings so post init converts to integer.
        if self.next_id:
            self.next_id = int(self.next_id)
        if self.next_row:
            self.next_row = int(self.next_row)

    def next_options(self, page_size: int = 50) -> PaginationOptions:
        return PaginationOptions(page_size, self.next_id, self.next_row)


def _validate_extension(extension: REPORT_FORMATS) -> None:
    if extension not in {"pdf", "csv"}:
        msg = "Extension argument needs to be 'pdf' or 'csv'."
        raise ValueError(msg)


@dataclass
class ReportBody(BaseBody):
    """Body for summary endpoint which turns into a JSON body."""

    start_date: Optional[date] = field(default=None)
    """Start date, example time.DateOnly. Should be less than End date."""

    end_date: Optional[date] = field(default=None)
    """End date, example time. DateOnly. Should be greater than Start date."""

    client_ids: list[int | None] = field(default_factory=list)
    """Client IDs, optional, filtering attribute. To filter records with no clients, use [None]."""

    description: Optional[str] = field(default=None)
    """Description, optional, filtering attribute."""

    group_ids: list[int] = field(default_factory=list)
    """Group IDs, optional, filtering attribute."""

    grouping: Optional[str] = field(
        default=None,
        metadata={
            "endpoints": frozenset(
                (
                    "summary_time_entries",
                    "summary_report_pdf",
                    "summary_report_csv",
                ),
            ),
        },
    )
    """Grouping option, optional."""

    grouped: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(
                (
                    "detail_search_time",
                    "detail_report_pdf",
                    "detail_report_csv",
                    "detail_totals",
                ),
            ),
        },
    )
    """Whether time entries should be grouped, optional, default false."""

    include_time_entry_ids: bool = field(
        default=True,  # NOTE: API default is False. Wrapper sets it as True.
        metadata={
            "endpoints": frozenset(
                (
                    "summary_time_entries",
                    "summary_report_pdf",
                    "summary_report_csv",
                ),
            ),
        },
    )
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

    sub_grouping: Optional[str] = field(
        default=None,
        metadata={
            "endpoints": frozenset(
                (
                    "summary_time_entries",
                    "summary_report_pdf",
                    "summary_report_csv",
                ),
            ),
        },
    )
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
    ] = field(
        default="YYYY-MM-DD",  # NOTE: API Default is 'MM/DD/YYYY'
        metadata={
            "endpoints": frozenset(
                (
                    "summary_report_pdf",
                    "detail_report_pdf",
                    "weekly_report_pdf",
                ),
            ),
        },
    )
    """Date format, optional, default 'YYYY-MM-DD'."""

    duration_format: Literal["classic", "decimal", "improved"] = field(
        default="classic",
        metadata={
            "endpoints": frozenset(
                (
                    "summary_report_pdf",
                    "summary_report_csv",
                    "detailed_report_pdf",
                    "detailed_report_csv",
                    "weekly_report_pdf",
                ),
            ),
        },
    )
    """Duration format, optional, default "classic". Can be "classic", "decimal" or "improved"."""

    order_by: Optional[Literal["title", "duration"]] = field(
        default=None,
        metadata={
            "endpoints": frozenset(
                (
                    "summary_report_pdf",
                    "summary_report_csv",
                    "detail_search_time",
                    "detail_report_pdf",
                    "detail_report_csv",
                ),
            ),
        },
    )
    """Order by option, optional, default title. Can be title or duration."""

    order_dir: Optional[Literal["ASC", "DESC"]] = field(
        default=None,
        metadata={
            "endpoints": frozenset(
                (
                    "summary_report_pdf",
                    "summary_report_csv",
                    "detail_search_time",
                    "detail_report_pdf",
                    "detail_report_csv",
                ),
            ),
        },
    )
    """Order direction, optional. Can be ASC or DESC."""

    resolution: Optional[str] = field(
        default=None,
        metadata={
            "endpoints": frozenset(
                (
                    "summary_report_pdf",
                    "detail_totals",
                ),
            ),
        },
    )
    """Graph resolution, optional. Allow clients to explicitly request a resolution."""

    enrich_response: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(
                (
                    "detail_search_time",
                    "detail_report",
                ),
            ),
        },
    )
    """It will force the detailed report to return as much information as possible, as it does for the export."""

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:  # noqa: C901, PLR0912
        body.update(
            {
                "client_ids": self.client_ids,
                "project_ids": self.project_ids,
                "tag_ids": self.tag_ids,
                "time_entry_ids": self.time_entry_ids,
                "user_ids": self.user_ids,
            },
        )

        if self.start_date:
            body["start_date"] = format_iso(self.start_date)
            if self.end_date is not None and self.start_date > self.end_date:
                msg = "Start date needs to be on or before the end date!"
                raise AttributeError(msg)

        if self.end_date:
            body["end_date"] = format_iso(self.end_date)

        if self.verify_endpoint_parameter("date_format", endpoint):
            body["date_format"] = self.date_format

        if self.verify_endpoint_parameter("duration_format", endpoint):
            body["duration_format"] = self.duration_format

        if self.include_time_entry_ids and self.verify_endpoint_parameter("include_time_entry_ids", endpoint):
            body["include_time_entry_ids"] = self.include_time_entry_ids

        if self.description is not None:
            body["description"] = self.description

        if self.group_ids:
            body["group_ids"] = self.group_ids

        if self.grouping and self.verify_endpoint_parameter("grouping", endpoint):
            body["grouping"] = self.grouping

        if self.grouped and self.verify_endpoint_parameter("grouped", endpoint):
            body["grouped"] = self.grouped

        if isinstance(self.max_duration_seconds, int):
            body["max_duration_seconds"] = self.max_duration_seconds

        if isinstance(self.min_duration_seconds, int):
            body["min_duration_seconds"] = self.min_duration_seconds

        if isinstance(self.rounding, int):
            body["rounding"] = self.rounding

        if isinstance(self.rounding_minutes, int):
            body["rounding_minutes"] = self.rounding_minutes

        if self.sub_grouping is not None and self.verify_endpoint_parameter("sub_grouping", endpoint):
            body["sub_grouping"] = self.sub_grouping

        if self.order_by is not None and self.verify_endpoint_parameter("order_by", endpoint):
            body["order_by"] = self.order_by

        if self.order_dir is not None and self.verify_endpoint_parameter("order_dir", endpoint):
            body["order_dir"] = self.order_dir

        if self.resolution is not None and self.verify_endpoint_parameter("resolution", endpoint):
            body["resolution"] = self.resolution

        if self.enrich_response and self.verify_endpoint_parameter("enrich_response", endpoint):
            body["enrich_response"] = self.enrich_response

        return body


class ReportEndpoint(TogglEndpoint):
    """Abstract baseclass for the reports endpoint that overrides BASE_ENDPOINT."""

    BASE_ENDPOINT = "https://api.track.toggl.com/reports/api/v3/"

    @property
    def model(self) -> None:  # type: ignore[override]
        return


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
                "start_date": format_iso(start_date),
                "end_date": format_iso(end_date),
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

    def search_time_entries(self, body: ReportBody) -> list[dict[str, int]]:
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
            body=body.format(
                "summary_time_entries",
                workspace_id=self.workspace_id,
            ),
        )

    def time_entries(self, body: ReportBody) -> list[dict[str, int]]:
        """Returns a list of time entries within the parameters specified.

        DEPRECATED: Use ['search_time_entries'][toggl_api.reports.SummaryReportEndpoint.search_time_entries] instead.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-search-time-entries)

        Args:
            body: Body parameters to filter time entries by.

        Returns:
            list: A list of dictionaries with the filtered tracker data.
        """
        warnings.warn(
            "Deprecated: Use 'search_time_entries' instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        return self.search_time_entries(body)

    def export_report(
        self,
        body: ReportBody,
        extension: REPORT_FORMATS,
        *,
        collapse: bool = False,
    ) -> bytes:
        """Downloads summary report in the specified in the specified format: csv or pdf.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-export-summary-report)

        Args:
            body: Body parameters to filter the report by.
            extension: What format to use for the report. CSV or PDF.
            collapse: Whether collapse others. Inserted into body.

        Raises:
            ValueError: If extension is not pdf or csv.

        Returns:
            object: A format ready to be saved as a file or used for further processing.
        """
        _validate_extension(extension)

        return self.request(
            f"summary/time_entries.{extension}",
            method=RequestMethod.POST,
            body=body.format(
                f"summary_report_{extension}",
                workspace_id=self.workspace_id,
                collapse=collapse,
            ),
            raw=True,
        ).content

    def export_summary(
        self,
        body: ReportBody,
        extension: REPORT_FORMATS,
        *,
        collapse: bool = False,
    ) -> bytes:
        """Downloads summary report in the specified in the specified format: csv or pdf.

        DEPRECATED: Use ['export_report'][toggl_api.reports.SummaryReportEndpoint.export_report] instead.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-export-summary-report)

        Args:
            body: Body parameters to filter the report by.
            extension: What format to use for the report. CSV or PDF.
            collapse: Whether collapse others. Inserted into body.

        Raises:
            ValueError: If extension is not pdf or csv.

        Returns:
            object: A format ready to be saved as a file or used for further processing.
        """
        warnings.warn(
            "Deprecated: Use 'export_report' instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        return self.export_report(body, extension, collapse=collapse)

    @property
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT + f"workspace/{self.workspace_id}/"


class DetailedReportEndpoint(ReportEndpoint):
    """Detailed reports endpoint.

    [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports)
    """

    @staticmethod
    def _paginate(request: Response, *, raw: bool = False) -> PaginatedResult:
        return PaginatedResult(
            request.content if raw else request.json(),
            request.headers.get("x-next-id"),
            request.headers.get("x-next-row-number"),
        )

    @staticmethod
    def _paginate_body(
        body: dict[str, Any],
        pagination: PaginationOptions,
    ) -> dict[str, Any]:
        body["page_size"] = pagination.page_size
        if pagination.next_id is not None and pagination.next_row is not None:
            body["first_id"] = pagination.next_id
            body["first_row_number"] = pagination.next_row

        return body

    def search_time_entries(
        self,
        body: ReportBody,
        pagination: Optional[PaginationOptions] = None,
        *,
        hide_amounts: bool = False,
    ) -> PaginatedResult[list]:
        """Returns time entries for detailed report according to the given filters.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-search-time-entries)

        Args:
            body: JSON body with filters for time entries.
            pagination: Pagination options containing page size, next_id and next_row.
            hide_amounts: Whether amounts should be hidden.

        Returns:
            PaginatedResult: data with pagination information if required.
        """

        pagination = pagination or PaginationOptions()

        request: Response = self.request(
            "",
            body=self._paginate_body(
                body.format(
                    "detail_search_time",
                    workspace_id=self.workspace_id,
                    hide_amounts=hide_amounts,
                ),
                pagination,
            ),
            method=RequestMethod.POST,
            raw=True,
        )

        return self._paginate(request)

    def export_report(
        self,
        body: ReportBody,
        extension: REPORT_FORMATS,
        pagination: Optional[PaginationOptions] = None,
        *,
        hide_amounts: bool = False,
    ) -> PaginatedResult[bytes]:
        """Downloads detailed report in pdf or csv format.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-export-detailed-report)

        Args:
            body: JSON body for formatting and filtering the report.
            extension: Format of the exported report. PDF or CSV.
            pagination: Pagination options containing page size, next_id and next_row.
            hide_amounts: Whether amounts should be hidden.

        Raises:
            ValueError: If extension is not pdf or csv.

        Returns:
            bytes: Report ready to be saved or further processed in python.
        """
        _validate_extension(extension)

        pagination = pagination or PaginationOptions()
        request = self.request(
            f".{extension}",
            body=self._paginate_body(
                body.format(
                    f"detail_report_{extension}",
                    workspace_id=self.workspace_id,
                    hide_amounts=hide_amounts,
                ),
                pagination,
            ),
            method=RequestMethod.POST,
            raw=True,
        )
        return self._paginate(request, raw=True)

    def totals_report(
        self,
        body: ReportBody,
        *,
        granularity: Literal["day", "week", "month"] = "day",
        with_graph: bool = False,
    ) -> dict[str, int]:
        """Returns totals sums for detailed report.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-load-totals-detailed-report)

        Args:
            body: JSON body for filtering the report.
            granularity: Totals granularity, optional, overrides resolution values.
            with_graph: Whether Graph information should be loaded.

        Returns:
            dict: With the totals relevant to the provided filters.
        """
        return self.request(
            "/totals",
            body=body.format(
                "detail_totals",
                workspace_id=self.workspace_id,
                granularity=granularity,
                with_graph=with_graph,
            ),
            method=RequestMethod.POST,
        )

    @property
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT + f"workspace/{self.workspace_id}/search/time_entries"


class WeeklyReportEndpoint(ReportEndpoint):
    """Weekly reports endpoint.

    [Official Documentation](https://engineering.toggl.com/docs/reports/weekly_reports)
    """

    def search_time_entries(self, body: ReportBody) -> list[dict[str, Any]]:
        """Returns time entries for weekly report according to the given filters.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-search-time-entries)

        Args:
            body: JSON body for filtering time entries.

        Returns:
            list: A List of time entries filted by the formatted body.
        """
        return self.request(
            "",
            body=body.format(
                "weekly_time_entries",
                workspace_id=self.workspace_id,
            ),
            method=RequestMethod.POST,
        )

    def export_report(self, body: ReportBody, extension: REPORT_FORMATS) -> bytes:
        """Downloads weekly report in pdf or csv format.

        [Official Documentation](https://engineering.toggl.com/docs/reports/weekly_reports#post-export-weekly-report)

        Args:
            body: JSON body for filtering time entries.
            extension: extension: Format of the exported report. PDF or CSV.

        Raises:
            ValueError: If extension is not pdf or csv.

        Returns:
            bytes: Report ready to be saved or further processed in python.
        """
        _validate_extension(extension)
        return self.request(
            f".{extension}",
            body=body.format(
                f"weekly_report_{extension}",
                workspace_id=self.workspace_id,
            ),
            method=RequestMethod.POST,
            raw=True,
        ).content

    @property
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT + f"workspace/{self.workspace_id}/weekly/time_entries"
