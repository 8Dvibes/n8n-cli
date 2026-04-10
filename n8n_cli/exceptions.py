"""Exception classes for n8n-cli.

Domain modules raise these exceptions instead of calling sys.exit()
directly, so that:
  1. cli.py can format errors consistently (plain text or --json)
  2. The code is testable with pytest.raises()
  3. n8n-cli can be imported as a library without killing the process
"""


class N8nError(Exception):
    """Base exception for all n8n-cli errors."""
    pass


class N8nConnectionError(N8nError):
    """Raised when the n8n instance is unreachable."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Connection error: {reason}")


class N8nConfigError(N8nError):
    """Raised when configuration is missing or invalid."""
    pass


class N8nCatalogError(N8nError):
    """Raised when node catalog operations fail."""
    pass


class N8nApiError(N8nError):
    """Raised when the n8n API returns an HTTP error."""

    def __init__(self, status: int, message: str, body=None):
        self.status = status
        self.message = message
        self.body = body
        super().__init__(f"HTTP {status}: {message}")


class N8nValidationError(N8nError):
    """Raised when input validation fails."""
    pass
