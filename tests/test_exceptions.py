"""Tests for the exception hierarchy."""

from n8n_cli.exceptions import (
    N8nError,
    N8nApiError,
    N8nCatalogError,
    N8nConfigError,
    N8nConnectionError,
    N8nValidationError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_base(self):
        for cls in (N8nApiError, N8nConnectionError, N8nConfigError,
                     N8nCatalogError, N8nValidationError):
            assert issubclass(cls, N8nError), f"{cls.__name__} not subclass of N8nError"

    def test_api_error_fields(self):
        err = N8nApiError(404, "Not found", {"detail": "x"})
        assert err.status == 404
        assert err.message == "Not found"
        assert err.body == {"detail": "x"}
        assert isinstance(err, N8nError)

    def test_connection_error_reason(self):
        err = N8nConnectionError("refused")
        assert err.reason == "refused"
        assert "refused" in str(err)

    def test_recovery_hints_present(self):
        assert N8nConnectionError("x").recovery_hint != ""
        assert N8nConfigError("x").recovery_hint != ""
        assert N8nCatalogError("x").recovery_hint != ""
        assert N8nValidationError("x").recovery_hint != ""

    def test_api_error_status_hints(self):
        assert "config show" in N8nApiError(401, "x").recovery_hint.lower()
        assert N8nApiError(404, "x").recovery_hint != ""
        assert N8nApiError(200, "x").recovery_hint == ""
