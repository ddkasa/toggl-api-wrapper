import enum


class RequestMethod(enum.Enum):
    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    DELETE = enum.auto()
    PATCH = enum.auto()
