"""Exception classes for n8n-cli.

Domain modules raise these exceptions instead of calling sys.exit()
directly, so that:
  1. cli.py can format errors consistently (plain text or --json)
  2. The code is testable with pytest.raises()
  3. n8n-cli can be imported as a library without killing the process

Each exception can carry a recovery_hint -- a human/agent-readable
suggestion for what to do next. This is especially valuable for AI
agents operating n8n-cli via bash, as they can parse the hint from
the JSON error response and self-correct.
"""


class N8nError(Exception):
    """Base exception for all n8n-cli errors."""

    def __init__(self, message: str, recovery_hint: str = ""):
        self.recovery_hint = recovery_hint
        super().__init__(message)


class N8nConnectionError(N8nError):
    """Raised when the n8n instance is unreachable."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(
            f"Connection error: {reason}",
            recovery_hint="Check n8n instance URL with: n8n-cli config show",
        )


class N8nConfigError(N8nError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str):
        super().__init__(
            message,
            recovery_hint=(
                "Configure with: n8n-cli config set-profile <name> "
                "--url <url> --key <key>"
            ),
        )


class N8nCatalogError(N8nError):
    """Raised when node catalog operations fail."""

    def __init__(self, message: str):
        super().__init__(
            message,
            recovery_hint="Try: n8n-cli nodes update",
        )


class N8nApiError(N8nError):
    """Raised when the n8n API returns an HTTP error."""

    def __init__(self, status: int, message: str, body=None):
        self.status = status
        self.message = message
        self.body = body

        # Status-specific recovery hints
        hints = {
            401: "API key may be invalid or expired. Check with: n8n-cli config show",
            403: "Insufficient permissions for this operation.",
            404: "Resource not found. Verify the ID with: n8n-cli <resource> list",
            400: "Invalid request body. Check field names and types.",
            429: "Rate limited. Wait and retry.",
            500: "n8n server error. Check the n8n instance logs.",
        }
        hint = hints.get(status, "")

        super().__init__(f"HTTP {status}: {message}", recovery_hint=hint)


class N8nValidationError(N8nError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message, recovery_hint="Check command usage with: n8n-cli <command> --help")
