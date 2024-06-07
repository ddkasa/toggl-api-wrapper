import enum


class RequestMethod(enum.Enum):
    """Self explanatory enumerations describing the different request types
    primarily for selecting request methods."""

    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    DELETE = enum.auto()
    PATCH = enum.auto()
