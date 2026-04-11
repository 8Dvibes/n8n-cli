"""Stylized terminal output for n8n-cli.

Provides Ink-inspired visual formatting using only Python stdlib:
  - ANSI color output with automatic fallback for non-TTY
  - Semantic output markers (success, error, warning, info)
  - Smart table formatting that adapts to terminal width
  - Section headers with rules
  - Key-value display with aligned columns
  - Threaded spinner context manager for long operations

Respects:
  - NO_COLOR env var (https://no-color.org/)
  - CLICOLOR_FORCE env var
  - TERM=dumb
  - Pipe/redirect detection via isatty()

Zero external dependencies. Works with Python 3.9+.
"""

from __future__ import annotations

import itertools
import os
import re
import shutil
import sys
import threading
from typing import IO, Optional, Sequence

# ── ANSI escape codes ──────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "gray": "\033[90m",
}

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _visible_len(s: str) -> int:
    """Character count ignoring ANSI escape sequences."""
    return len(_ANSI_RE.sub("", s))


# ── Color support detection ────────────────────────────────────────

def _supports_color(stream: IO = sys.stderr) -> bool:
    """Detect ANSI color support on a stream."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("CLICOLOR_FORCE", "") not in ("", "0"):
        return True
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return stream.isatty()
    except (AttributeError, ValueError):
        return False


class Output:
    """Ink-inspired terminal output with automatic color fallback.

    All methods write to stderr by default, keeping stdout clean
    for machine-readable JSON output (consistent with --json mode).

    Usage::

        out = Output()
        out.heading("Workflow Status")
        out.success("Connected to n8n cloud")
        out.table(["ID", "Name", "Active"], rows)
        out.error("Credential expired")
    """

    def __init__(self, stream: IO = sys.stderr):
        self.stream = stream
        self.color = _supports_color(stream)
        self.width = shutil.get_terminal_size((80, 24)).columns

    # ── Core formatting ────────────────────────────────────────────

    def _c(self, code: str, text: str) -> str:
        """Apply ANSI code if color is enabled."""
        return f"{code}{text}{_RESET}" if self.color else text

    def bold(self, t: str) -> str:
        return self._c(_BOLD, t)

    def dim(self, t: str) -> str:
        return self._c(_DIM, t)

    def green(self, t: str) -> str:
        return self._c(_COLORS["green"], t)

    def red(self, t: str) -> str:
        return self._c(_COLORS["red"], t)

    def yellow(self, t: str) -> str:
        return self._c(_COLORS["yellow"], t)

    def cyan(self, t: str) -> str:
        return self._c(_COLORS["cyan"], t)

    def gray(self, t: str) -> str:
        return self._c(_COLORS["gray"], t)

    # ── Semantic output ────────────────────────────────────────────

    def success(self, msg: str) -> None:
        """Green checkmark + message."""
        mark = self.green("\u2713") if self.color else "+"
        print(f"  {mark} {msg}", file=self.stream)

    def error(self, msg: str) -> None:
        """Red X + message."""
        mark = self.red("\u2717") if self.color else "X"
        print(f"  {mark} {msg}", file=self.stream)

    def warning(self, msg: str) -> None:
        """Yellow ! + message."""
        mark = self.yellow("!") if self.color else "!"
        print(f"  {mark} {msg}", file=self.stream)

    def info(self, msg: str) -> None:
        """Cyan bullet + message."""
        mark = self.cyan("\u2022") if self.color else "-"
        print(f"  {mark} {msg}", file=self.stream)

    # ── Layout ─────────────────────────────────────────────────────

    def heading(self, title: str) -> None:
        """Bold section header with rule underneath."""
        print(file=self.stream)
        print(f"  {self.bold(title)}", file=self.stream)
        rule_len = min(len(title) + 4, self.width - 2)
        print(f"  {self.dim('\u2500' * rule_len)}", file=self.stream)

    def rule(self, char: str = "\u2500") -> None:
        """Horizontal rule spanning available width."""
        w = min(self.width - 4, 72)
        print(f"  {self.dim(char * w)}", file=self.stream)

    def kv(self, key: str, value: str, key_width: int = 14) -> None:
        """Key-value pair with aligned columns."""
        k = self.cyan(f"{key + ':':<{key_width}}")
        print(f"  {k} {value}", file=self.stream)

    def blank(self) -> None:
        """Empty line."""
        print(file=self.stream)

    def count(self, n: int, singular: str, plural: str = "") -> str:
        """Format a count with proper pluralization."""
        word = singular if n == 1 else (plural or f"{singular}s")
        return f"{n} {word}"

    # ── Table ──────────────────────────────────────────────────────

    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[str]],
        max_col: int = 40,
    ) -> None:
        """Print a formatted table adapting to terminal width.

        Shrinks the widest column first if the table exceeds terminal
        width. Truncates cells with ellipsis when needed.
        """
        if not rows:
            print("  (no data)", file=self.stream)
            return

        ncols = len(headers)
        str_rows = [[str(c) for c in row] for row in rows]

        # Calculate column widths
        col_w = [len(h) for h in headers]
        for row in str_rows:
            for i, cell in enumerate(row[:ncols]):
                col_w[i] = max(col_w[i], len(cell))

        # Cap and shrink
        col_w = [min(w, max_col) for w in col_w]
        padding = 2
        total = sum(col_w) + padding * (ncols - 1) + 4
        while total > self.width and max(col_w) > 6:
            widest = col_w.index(max(col_w))
            col_w[widest] -= 1
            total -= 1

        sep = " " * padding

        def _fmt(cells: Sequence[str], widths: Sequence[int]) -> str:
            parts = []
            for cell, w in zip(cells, widths):
                s = str(cell)
                if len(s) > w:
                    s = s[: w - 1] + "\u2026"
                parts.append(f"{s:<{w}}")
            return sep.join(parts)

        # Header
        hdr = _fmt(headers, col_w)
        print(f"  {self.bold(self.cyan(hdr))}", file=self.stream)
        print(f"  {self.dim('\u2500' * _visible_len(hdr))}", file=self.stream)

        # Rows
        for row in str_rows:
            padded = list(row[:ncols]) + [""] * max(0, ncols - len(row))
            print(f"  {_fmt(padded, col_w)}", file=self.stream)

    # ── Spinner ────────────────────────────────────────────────────

    def spinner(self, message: str) -> "Spinner":
        """Create a threaded spinner context manager.

        Usage::

            with out.spinner("Downloading catalog..."):
                ensure_catalog(force=True)
            # Shows: + Downloading catalog... done
        """
        return Spinner(message, output=self)


class Spinner:
    """Threaded terminal spinner with automatic cleanup.

    Renders braille animation on TTY, plain text on non-TTY.
    Thread-safe: all writes protected by a lock.
    """

    _FRAMES = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"

    def __init__(self, message: str, output: Output, interval: float = 0.08):
        self.message = message
        self.out = output
        self.interval = interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _run(self) -> None:
        stream = self.out.stream
        tty = self.out.color  # Color implies TTY
        cycle = itertools.cycle(self._FRAMES)

        while not self._stop.is_set():
            if tty:
                frame = next(cycle)
                with self._lock:
                    stream.write(
                        f"\r\033[?25l{self.out.cyan(frame)} {self.message}"
                    )
                    stream.flush()
            self._stop.wait(self.interval)

        # Clear spinner line
        if tty:
            with self._lock:
                clear = " " * (_visible_len(self.message) + 10)
                stream.write(f"\r{clear}\r\033[?25h")
                stream.flush()

    def __enter__(self) -> "Spinner":
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

        failed = exc_type is not None
        if self.out.color:
            if failed:
                self.out.error(f"{self.message} failed")
            else:
                self.out.success(f"{self.message} done")
        else:
            label = "FAIL" if failed else "OK"
            print(f"  [{label}] {self.message}", file=self.out.stream)
