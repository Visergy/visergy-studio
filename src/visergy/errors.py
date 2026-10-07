"""Error types. The CLI prints any VisergyError as `error: <message>` and exits 1."""


class VisergyError(Exception):
    """Base class for expected, user-facing errors."""


class ConfigError(VisergyError):
    pass


class MoneyError(VisergyError):
    pass


class DatabaseNotFound(VisergyError):
    pass


class SchemaOutOfDate(VisergyError):
    pass


class ProjectNotFound(VisergyError):
    pass


class InvalidTransition(VisergyError):
    pass


class QuoteNotAccepted(VisergyError):
    pass


class OverInvoiceError(VisergyError):
    pass


class TaxInvoiceNotAllowed(VisergyError):
    pass


class RenderError(VisergyError):
    pass


class ReportSourceError(VisergyError):
    pass
