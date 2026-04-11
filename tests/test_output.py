"""Tests for the stylized output module."""

import io
import os
from unittest.mock import patch

from n8n_cli.output import Output, _supports_color, _visible_len


class TestColorDetection:
    def test_no_color_env_disables(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert _supports_color(io.StringIO()) is False

    def test_clicolor_force_enables(self):
        with patch.dict(os.environ, {"CLICOLOR_FORCE": "1"}, clear=False):
            os.environ.pop("NO_COLOR", None)
            assert _supports_color(io.StringIO()) is True

    def test_dumb_term_disables(self):
        with patch.dict(os.environ, {"TERM": "dumb"}, clear=False):
            os.environ.pop("NO_COLOR", None)
            os.environ.pop("CLICOLOR_FORCE", None)
            assert _supports_color(io.StringIO()) is False


class TestVisibleLen:
    def test_plain_text(self):
        assert _visible_len("hello") == 5

    def test_with_ansi(self):
        assert _visible_len("\033[32mhello\033[0m") == 5

    def test_empty(self):
        assert _visible_len("") == 0


class TestOutput:
    def _make_output(self):
        stream = io.StringIO()
        out = Output(stream=stream)
        out.color = False  # Consistent test output
        return out, stream

    def test_success(self):
        out, stream = self._make_output()
        out.success("it works")
        assert "+ it works" in stream.getvalue()

    def test_error(self):
        out, stream = self._make_output()
        out.error("something broke")
        assert "X something broke" in stream.getvalue()

    def test_warning(self):
        out, stream = self._make_output()
        out.warning("watch out")
        assert "! watch out" in stream.getvalue()

    def test_info(self):
        out, stream = self._make_output()
        out.info("fyi")
        assert "- fyi" in stream.getvalue()

    def test_heading(self):
        out, stream = self._make_output()
        out.heading("Test Section")
        text = stream.getvalue()
        assert "Test Section" in text

    def test_kv(self):
        out, stream = self._make_output()
        out.kv("Status", "OK")
        text = stream.getvalue()
        assert "Status" in text
        assert "OK" in text

    def test_table_with_data(self):
        out, stream = self._make_output()
        out.table(
            ["ID", "Name"],
            [["1", "Alpha"], ["2", "Beta"]],
        )
        text = stream.getvalue()
        assert "Alpha" in text
        assert "Beta" in text

    def test_table_empty(self):
        out, stream = self._make_output()
        out.table(["A", "B"], [])
        assert "no data" in stream.getvalue()

    def test_count_singular(self):
        out, _ = self._make_output()
        assert out.count(1, "workflow") == "1 workflow"

    def test_count_plural(self):
        out, _ = self._make_output()
        assert out.count(5, "workflow") == "5 workflows"

    def test_count_custom_plural(self):
        out, _ = self._make_output()
        assert out.count(0, "entry", "entries") == "0 entries"
