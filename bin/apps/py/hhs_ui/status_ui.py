#!/usr/bin/env python3
"""Floating status helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable

import streamlit as st

import hhs_ui.constants as hhs_ui_constants
from hhs_ui.command_catalog import clean_command_status_message
from hhs_ui.paths import hhs_log_dir
from hhs_ui.process_resources import process_resource_registry


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"status UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")


def configure_status_runtime(*, render_script_html: Callable[..., None]) -> None:
    """Configure callbacks required by floating status helpers."""
    globals().update({"render_script_html": render_script_html})


def push_floating_status(
    message: str, kind: str = "info", timeout_seconds: float = 5.0
) -> None:
    """Queue a compact floating status message for the next footer render."""
    clean_message = clean_command_status_message(str(message))
    if not clean_message:
        return
    normalized_kind = normalize_floating_status_kind(kind)
    log_footer_status_message(clean_message, normalized_kind)
    status_queue = floating_status_queue()
    status_queue.append(
        {
            "message": clean_message,
            "kind": normalized_kind,
            "timeout_seconds": max(1.0, min(float(timeout_seconds), 30.0)),
        }
    )
    del status_queue[: -hhs_ui_constants.FLOATING_STATUS_QUEUE_LIMIT]
    st.session_state[hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY] = status_queue


def log_footer_status_message(message: str, kind: str) -> None:
    """Append one footer status message to the Streamlit server log."""
    logger = footer_status_file_logger()
    if logger is not None:
        logger.info("Footer status [%s]: %s", kind.upper(), message)


def footer_status_file_logger() -> logging.Logger | None:
    """Return the non-propagating logger used for footer status messages."""
    log_path = (hhs_log_dir() / "streamlit-ui.log").resolve()
    registry = process_resource_registry(
        hhs_ui_constants.FOOTER_STATUS_FILE_LOG_HANDLER_REGISTRY_KEY
    )
    logger = logging.getLogger("hhs_ui.footer_status")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = registry.get("handler")
    if isinstance(handler, logging.FileHandler) and handler.baseFilename != str(log_path):
        logger.removeHandler(handler)
        handler.close()
        handler = None
    if not isinstance(handler, logging.FileHandler):
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_path, encoding="utf-8")
        except OSError:
            return None
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        registry["handler"] = handler
    elif handler not in logger.handlers:
        logger.addHandler(handler)
    return logger


def normalize_floating_status_kind(kind: str) -> str:
    """Return a supported floating status kind from a user-facing alias."""
    kind_aliases = {"success": "info", "warning": "warn"}
    clean_kind = kind_aliases.get(kind, kind)
    if clean_kind not in {"info", "warn", "error"}:
        clean_kind = "info"
    return clean_kind


def floating_status_queue() -> list[dict[str, object]]:
    """Return the floating status queue, migrating legacy single-message state."""
    queue = st.session_state.get(hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY)
    if not isinstance(queue, list):
        queue = []
    legacy_status = st.session_state.pop(
        hhs_ui_constants.FLOATING_STATUS_LEGACY_KEY, None
    )
    if isinstance(legacy_status, dict):
        queue.append(legacy_status)
    normalized_queue = [item for item in queue if isinstance(item, dict)]
    st.session_state[hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY] = normalized_queue
    return normalized_queue


def pop_floating_status() -> dict[str, object] | None:
    """Remove and return the oldest queued floating status message."""
    queue = floating_status_queue()
    if not queue:
        return None
    status = queue.pop(0)
    st.session_state[hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY] = queue
    return status


def current_floating_status() -> dict[str, object] | None:
    """Return the visible floating status, starting its timer on first render."""
    queue = floating_status_queue()
    while queue:
        status = queue[0]
        message = str(status.get("message", "")).strip()
        if not message:
            pop_floating_status()
            queue = floating_status_queue()
            continue
        timeout = effective_floating_status_timeout(status)
        displayed_at = status.get("displayed_at")
        if not isinstance(displayed_at, (int, float)):
            status["displayed_at"] = time.time()
            st.session_state[hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY] = queue
            return status
        if time.time() - float(displayed_at) > timeout + 1.0:
            pop_floating_status()
            queue = floating_status_queue()
            continue
        return status
    return None


def effective_floating_status_timeout(status: dict[str, object]) -> float:
    """Return the visible timeout for a floating status."""
    timeout = float(status.get("timeout_seconds", 5.0))
    return timeout + hhs_ui_constants.FLOATING_STATUS_AUTO_DISPOSE_EXTENSION_SECONDS


def floating_status_glyph(kind: str) -> str:
    """Return the glyph used by the floating status component."""
    return {
        "info": "",
        "error": "",
        "warn": "",
    }.get(kind, "")


def floating_status_dom_id(status: dict[str, object], message: str, kind: str) -> str:
    """Return a stable browser-side identity for one rendered floating status."""
    displayed_at = status.get("displayed_at", "")
    raw_status = f"{kind}|{message}|{displayed_at}"
    return hashlib.sha256(raw_status.encode("utf-8")).hexdigest()[:16]


def render_floating_status_dispose_script(
    status_id: str,
    message: str,
    kind: str,
    glyph: str,
    timeout: float,
    remaining_timeout: float,
) -> None:
    """Render or update the browser-persistent floating status element."""
    safe_status_id = json.dumps(status_id)
    safe_message = json.dumps(message)
    safe_kind = json.dumps(kind)
    safe_glyph = json.dumps(glyph)
    render_script_html(f"""
        <script>
        (() => {{
          const statusId = {safe_status_id};
          const message = {safe_message};
          const kind = {safe_kind};
          const glyphText = {safe_glyph};
          const timeout = {timeout:.2f};
          const remainingTimeout = {remaining_timeout:.2f};
          const parentWindow = window.parent || window;
          const parentDocument = parentWindow.document;
          const disposedStatuses = parentWindow.__hhsDisposedFloatingStatuses;
          if (!(disposedStatuses instanceof Set)) {{
            parentWindow.__hhsDisposedFloatingStatuses = new Set();
          }}
          let status = parentDocument.querySelector(
            `.hhs-floating-status[data-hhs-floating-status-id="${{statusId}}"]`
          );
          if (parentWindow.__hhsDisposedFloatingStatuses.has(statusId)) {{
            if (status) {{
              status.remove();
            }}
            return;
          }}
          parentDocument
            .querySelectorAll(".hhs-floating-status[data-hhs-floating-status-id]")
            .forEach((node) => {{
              if (node.dataset.hhsFloatingStatusId !== statusId) {{
                node.remove();
              }}
            }});
          const statusClass = `hhs-floating-status hhs-floating-status-kind-${{kind}} hhs-floating-status--stable`;
          if (!status) {{
            status = parentDocument.createElement("div");
            status.dataset.hhsFloatingStatusId = statusId;
            status.className = statusClass;
            status.style.setProperty(
              "--hhs-floating-status-timeout",
              `${{timeout.toFixed(2)}}s`
            );

            const glyph = parentDocument.createElement("span");
            glyph.className = "hhs-floating-status-glyph";
            const text = parentDocument.createElement("span");
            text.className = "hhs-floating-status-message";
            const button = parentDocument.createElement("button");
            button.className = "hhs-floating-status-dismiss";
            button.type = "button";
            button.setAttribute("aria-label", "Dispose footer status");
            button.title = "Dispose footer status";
            button.textContent = "x";
            status.append(glyph, text, button);
            parentDocument.body.append(status);
          }} else if (status.className !== statusClass) {{
            status.className = statusClass;
          }}
          const glyph = status.querySelector(".hhs-floating-status-glyph");
          if (glyph && glyph.textContent !== glyphText) {{
            glyph.textContent = glyphText;
          }}
          const text = status.querySelector(".hhs-floating-status-message");
          if (text && text.textContent !== message) {{
            text.textContent = message;
          }}
          const button = status.querySelector(".hhs-floating-status-dismiss");
          const dispose = () => {{
            parentWindow.__hhsDisposedFloatingStatuses.add(statusId);
            status.classList.add("hhs-floating-status--disposing");
            parentWindow.setTimeout(() => status.remove(), 240);
          }};
          if (button && button.dataset.hhsDisposeAttached !== "true") {{
            button.dataset.hhsDisposeAttached = "true";
            button.addEventListener("click", (event) => {{
              event.preventDefault();
              event.stopPropagation();
              if (parentWindow.__hhsFloatingStatusTimer) {{
                parentWindow.clearTimeout(parentWindow.__hhsFloatingStatusTimer);
              }}
              dispose();
            }});
          }}
          if (parentWindow.__hhsFloatingStatusTimer) {{
            parentWindow.clearTimeout(parentWindow.__hhsFloatingStatusTimer);
          }}
          parentWindow.__hhsFloatingStatusTimer = parentWindow.setTimeout(
            dispose,
            Math.max(100, remainingTimeout * 1000)
          );
        }})();
        </script>
        """)


def render_floating_status() -> None:
    """Render the compact floating status component above the footer."""
    status = current_floating_status()
    if not isinstance(status, dict):
        return
    message = str(status.get("message", "")).strip()
    if not message:
        return
    kind = normalize_floating_status_kind(str(status.get("kind", "info")))
    timeout = effective_floating_status_timeout(status)
    displayed_at = float(status.get("displayed_at", time.time()) or time.time())
    remaining_timeout = max(0.1, timeout - max(0.0, time.time() - displayed_at))
    glyph = floating_status_glyph(kind)
    status_id = floating_status_dom_id(status, message, kind)
    render_floating_status_dispose_script(
        status_id,
        message,
        kind,
        glyph,
        timeout,
        remaining_timeout,
    )


def drain_footer_status_log_records() -> None:
    """Move captured warning/error log records into the floating status queue."""
    registry = process_resource_registry(
        hhs_ui_constants.FOOTER_STATUS_LOG_RECORDS_REGISTRY_KEY
    )
    records = registry.get("records")
    if not isinstance(records, list) or not records:
        return
    registry["records"] = []
    seen_messages: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        message = clean_command_status_message(str(record.get("message", "")))
        if not message or message in seen_messages:
            continue
        seen_messages.add(message)
        level = str(record.get("level", "")).upper()
        kind = "error" if level in {"ERROR", "CRITICAL"} else "warn"
        push_floating_status(message, kind)
