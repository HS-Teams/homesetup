"""Persistent warning and error history displayed by the UI footer."""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime
from pathlib import Path

from . import constants as hhs_ui_constants
from .process_resources import process_resource_registry

_ALERT_FILE_LOCK = threading.RLock()
_ALERT_KIND_GLYPHS = {"warn": "", "error": ""}


def footer_alerts_file() -> Path:
    """Return the persistent footer alert history path."""
    return hhs_ui_constants.FOOTER_ALERTS_FILE.expanduser()


def normalize_footer_alert_message(message: str) -> str:
    """Return one whitespace-normalized alert message suitable for one file line."""
    return re.sub(r"\s+", " ", str(message)).strip()


def normalize_footer_alert_kind(kind: str) -> str:
    """Return a persisted footer alert kind, or an empty string when unsupported."""
    normalized_kind = {"warning": "warn", "critical": "error"}.get(kind, kind)
    return normalized_kind if normalized_kind in _ALERT_KIND_GLYPHS else ""


def footer_alert_glyph(kind: str) -> str:
    """Return the warning or error glyph used by the footer status bar."""
    return _ALERT_KIND_GLYPHS.get(normalize_footer_alert_kind(kind), "")


def append_footer_alert(
    message: str,
    kind: str,
    *,
    created_at: datetime | None = None,
) -> bool:
    """Append one non-duplicate warning or error to the footer alert history."""
    clean_message = normalize_footer_alert_message(message)
    clean_kind = normalize_footer_alert_kind(kind)
    if not clean_message or not clean_kind:
        return False

    registry = process_resource_registry("footer_alert_history")
    now_monotonic = time.monotonic()
    with _ALERT_FILE_LOCK:
        last_alert = registry.get("last_alert")
        if isinstance(last_alert, dict):
            last_key = (last_alert.get("kind"), last_alert.get("message"))
            elapsed = now_monotonic - float(last_alert.get("recorded_at", 0.0) or 0.0)
            if (
                last_key == (clean_kind, clean_message)
                and elapsed <= hhs_ui_constants.FOOTER_ALERT_DEDUPLICATION_SECONDS
            ):
                return False

        timestamp = (created_at or datetime.now().astimezone()).astimezone()
        alert_path = footer_alerts_file()
        try:
            alert_path.parent.mkdir(parents=True, exist_ok=True)
            with alert_path.open("a", encoding="utf-8") as alerts_stream:
                alerts_stream.write(
                    f"{timestamp.isoformat(timespec='milliseconds')}\t"
                    f"{clean_kind}\t{clean_message}\n"
                )
        except OSError:
            return False
        registry["last_alert"] = {
            "kind": clean_kind,
            "message": clean_message,
            "recorded_at": now_monotonic,
        }
    return True


def parse_footer_alert_line(line: str) -> dict[str, object] | None:
    """Return one parsed alert history line, ignoring malformed content."""
    fields = line.rstrip("\r\n").split("\t", 2)
    if len(fields) != 3:
        return None
    timestamp_text, kind, message = fields
    clean_kind = normalize_footer_alert_kind(kind)
    clean_message = normalize_footer_alert_message(message)
    if not clean_kind or not clean_message:
        return None
    try:
        timestamp = datetime.fromisoformat(timestamp_text).astimezone()
    except ValueError:
        return None
    return {
        "timestamp": timestamp,
        "timestamp_iso": timestamp.isoformat(timespec="milliseconds"),
        "kind": clean_kind,
        "message": clean_message,
    }


def read_footer_alerts() -> list[dict[str, object]]:
    """Return every valid persisted footer alert in file order."""
    with _ALERT_FILE_LOCK:
        try:
            lines = footer_alerts_file().read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except FileNotFoundError:
            return []
        except OSError:
            return []
    parsed_alerts = (parse_footer_alert_line(line) for line in lines)
    return [alert for alert in parsed_alerts if alert is not None]


def today_footer_alerts(now: datetime | None = None) -> list[dict[str, object]]:
    """Return footer alerts recorded on the current local calendar day."""
    local_today = (now or datetime.now().astimezone()).astimezone().date()
    return [
        alert
        for alert in read_footer_alerts()
        if isinstance(alert.get("timestamp"), datetime)
        and alert["timestamp"].astimezone().date() == local_today
    ]


def footer_alert_priority(alerts: list[dict[str, object]]) -> str:
    """Return error when any alert is an error, otherwise warning."""
    return "error" if any(alert.get("kind") == "error" for alert in alerts) else "warn"


def clear_footer_alerts() -> bool:
    """Truncate the alert history file without deleting it."""
    registry = process_resource_registry("footer_alert_history")
    with _ALERT_FILE_LOCK:
        try:
            alert_path = footer_alerts_file()
            alert_path.parent.mkdir(parents=True, exist_ok=True)
            alert_path.write_text("", encoding="utf-8")
        except OSError:
            return False
        registry.pop("last_alert", None)
    return True
