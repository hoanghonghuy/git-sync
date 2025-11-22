import os
import sys
from typing import Final

_RESET: Final[str] = "\033[0m"
_COLORS: Final[dict[str, str]] = {
    "info": "\033[36m",     # cyan
    "success": "\033[32m",  # green
    "warning": "\033[33m",  # yellow
    "error": "\033[31m",    # red
}


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def colorize(text: str, kind: str = "info") -> str:
    if not _supports_color():
        return text
    prefix = _COLORS.get(kind, "")
    if not prefix:
        return text
    return f"{prefix}{text}{_RESET}"
