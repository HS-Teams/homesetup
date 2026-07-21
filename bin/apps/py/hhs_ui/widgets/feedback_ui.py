#!/usr/bin/env python3
"""Shared Streamlit feedback helpers for HomeSetup."""

from __future__ import annotations

import html
import json
import secrets
import time
from collections.abc import Callable

import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.core.process_resources import process_resource_registry
from hhs_ui.core.theme_catalog import theme_option_from_path, theme_option_label
from hhs_ui.core.ui_definitions import (
    COMMAND_PRELOADER_BUS,
    COMMAND_PRELOADER_EVENT_BUS_REGISTRY_KEY,
    COMMAND_PRELOADER_EVENT_QUEUE_KEY,
    COMMAND_PRELOADER_FINISH_EVENT,
    COMMAND_PRELOADER_START_EVENT,
    COMMAND_PRELOADER_SUBSCRIBER_MARKER,
)
from hhs_ui.widgets.dialog_ui import close_all_dialogs


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"feedback UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
command_timeout_seconds = _unconfigured_dependency("command_timeout_seconds")
save_ui_state = _unconfigured_dependency("save_ui_state")


def configure_feedback_runtime(
    *,
    render_script_html: Callable[..., None],
    command_timeout_seconds: Callable[[], int],
    save_ui_state: Callable[[], None],
) -> None:
    """Configure callbacks required by shared feedback helpers."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "command_timeout_seconds": command_timeout_seconds,
            "save_ui_state": save_ui_state,
        }
    )


def command_loader_html(
    message: str,
    loader_id: str,
    started_at_millis: int,
    timeout_seconds: int,
    preloader_token: str = "",
) -> str:
    """Return reusable banner loader markup for command-data waits."""
    safe_message = loader_label_html(message)
    safe_loader_id = html.escape(loader_id, quote=True)
    safe_preloader_token = html.escape(str(preloader_token or "").strip(), quote=True)
    safe_timeout = max(1, int(timeout_seconds))
    return f"""
    <div class="hhs-command-loader" data-loader-id="{safe_loader_id}"
         data-hhs-preloader-token="{safe_preloader_token}" role="status" aria-live="polite">
      <button class="hhs-command-loader-close" type="button"
              title="Interrupt command" aria-label="Interrupt command"
              data-hhs-preloader-token="{safe_preloader_token}">x</button>
      <span class="hhs-command-loader-spinner" aria-hidden="true"></span>
      <span class="hhs-command-loader-copy">
        <span class="hhs-command-loader-label">{safe_message}</span>
        <span class="hhs-command-loader-elapsed hhs-tab-loader-elapsed"
              data-started-at="{started_at_millis}"
              data-timeout-seconds="{safe_timeout}">time elapsed: 0m:00s</span>
      </span>
    </div>
    """


def loader_label_html(message: str) -> str:
    """Return escaped loader label markup with optional theme color markers."""
    marker_classes = {
        "%primary_color%": "hhs-loader-primary",
        "%secondary_color%": "hhs-loader-secondary",
    }
    raw_message = str(message or "Loading...").strip() or "Loading..."
    cursor = 0
    active_class = ""
    html_parts: list[str] = []
    markers = tuple(marker_classes)
    while cursor < len(raw_message):
        next_marker = ""
        next_index = len(raw_message)
        for marker in markers:
            marker_index = raw_message.find(marker, cursor)
            if 0 <= marker_index < next_index:
                next_marker = marker
                next_index = marker_index
        html_parts.append(html.escape(raw_message[cursor:next_index]))
        if not next_marker:
            break
        next_class = marker_classes[next_marker]
        if active_class == next_class:
            html_parts.append("</span>")
            active_class = ""
        else:
            if active_class:
                html_parts.append("</span>")
            html_parts.append(f'<span class="{next_class}">')
            active_class = next_class
        cursor = next_index + len(next_marker)
    if active_class:
        html_parts.append("</span>")
    return "".join(html_parts)


def command_preloader_event_queue() -> list[dict[str, object]]:
    """Return the queued browser command preloader events for this session."""
    queued_events = st.session_state.setdefault(COMMAND_PRELOADER_EVENT_QUEUE_KEY, [])
    if not isinstance(queued_events, list):
        queued_events = []
        st.session_state[COMMAND_PRELOADER_EVENT_QUEUE_KEY] = queued_events
    return queued_events


def command_preloader_event_arg(
    event: object, name: str, default_value: object = ""
) -> object:
    """Return one EventBus argument value from an hspylib event object."""
    event_args = getattr(event, "args", None)
    return getattr(event_args, name, default_value)


def command_preloader_event_payload(event: object) -> dict[str, object]:
    """Return the browser payload for one command preloader EventBus event."""
    event_name = str(getattr(event, "name", "")).strip()
    message = str(command_preloader_event_arg(event, "message", "Loading...")).strip()
    status = str(command_preloader_event_arg(event, "status", "")).strip()
    token = str(command_preloader_event_arg(event, "token", "")).strip()
    try:
        timeout_seconds = int(command_preloader_event_arg(event, "timeout_seconds", 1))
    except (TypeError, ValueError):
        timeout_seconds = 1
    return {
        "event": event_name,
        "messageHtml": loader_label_html(message or "Loading..."),
        "status": status,
        "timeoutSeconds": max(1, timeout_seconds),
        "token": token,
    }


def enqueue_command_preloader_event(event: object) -> None:
    """Append one command preloader EventBus event to the session render queue."""
    queued_events = command_preloader_event_queue()
    queued_events.append(command_preloader_event_payload(event))
    del queued_events[: -hhs_ui_constants.FLOATING_STATUS_QUEUE_LIMIT]


def create_command_preloader_event_bus() -> object:
    """Create the hspylib FluidEventBus used by the UI command preloader."""
    from hspylib.modules.eventbus.fluid import FluidEvent, FluidEventBus

    return FluidEventBus(
        COMMAND_PRELOADER_BUS,
        start=FluidEvent(
            COMMAND_PRELOADER_START_EVENT,
            token="",
            message="",
            timeout_seconds=1,
        ),
        finish=FluidEvent(
            COMMAND_PRELOADER_FINISH_EVENT,
            token="",
            status="success",
        ),
    )


def command_preloader_event_bus() -> object:
    """Return the hspylib FluidEventBus for command preloader events."""
    registry = process_resource_registry(COMMAND_PRELOADER_EVENT_BUS_REGISTRY_KEY)
    event_bus = registry.get("event_bus")
    if event_bus is None:
        event_bus = create_command_preloader_event_bus()
        registry["event_bus"] = event_bus
    return event_bus


def command_preloader_events() -> object:
    """Return the fluid command preloader events namespace."""
    return command_preloader_event_bus().events


def command_preloader_bus() -> object:
    """Return the raw hspylib EventBus behind the fluid command event bus."""
    return command_preloader_event_bus().bus


def remove_command_preloader_subscribers() -> None:
    """Remove older HomeSetup command preloader EventBus callbacks."""
    event_bus_class = command_preloader_bus().__class__
    for event_name in (COMMAND_PRELOADER_START_EVENT, COMMAND_PRELOADER_FINISH_EVENT):
        cache_key = f"{COMMAND_PRELOADER_BUS}.{event_name}"
        subscriber = event_bus_class._subscribers.get(cache_key)  # noqa: SLF001
        if not isinstance(subscriber, dict):
            continue
        callbacks = subscriber.get("callbacks", [])
        if not isinstance(callbacks, list):
            subscriber["callbacks"] = []
            continue
        subscriber["callbacks"] = [
            callback
            for callback in callbacks
            if not getattr(callback, COMMAND_PRELOADER_SUBSCRIBER_MARKER, False)
        ]


def ensure_command_preloader_event_bus() -> None:
    """Subscribe the current session-safe command preloader EventBus callback."""
    registry = process_resource_registry(COMMAND_PRELOADER_EVENT_BUS_REGISTRY_KEY)
    callback_id = id(enqueue_command_preloader_event)
    if registry.get("callback_id") == callback_id:
        return
    remove_command_preloader_subscribers()
    setattr(enqueue_command_preloader_event, COMMAND_PRELOADER_SUBSCRIBER_MARKER, True)
    events = command_preloader_events()
    events.start.subscribe(cb_event_handler=enqueue_command_preloader_event)
    events.finish.subscribe(cb_event_handler=enqueue_command_preloader_event)
    registry["callback_id"] = callback_id


def emit_command_preloader_start(
    token: str, message: str, timeout_seconds: int | None = None
) -> None:
    """Emit an EventBus command preloader start event."""
    clean_token = token.strip()
    if not clean_token:
        return
    ensure_command_preloader_event_bus()
    events = command_preloader_events()
    events.start.emit(
        token=clean_token,
        message=message.strip() or "Loading...",
        timeout_seconds=int(timeout_seconds or command_timeout_seconds()),
    )


def emit_command_preloader_finish(token: str, status: str = "success") -> None:
    """Emit an EventBus command preloader finish event."""
    clean_token = token.strip()
    if not clean_token:
        return
    ensure_command_preloader_event_bus()
    events = command_preloader_events()
    events.finish.emit(
        token=clean_token,
        status=status.strip() or "success",
    )


def command_elapsed_helper_js() -> str:
    """Return the shared browser helper for command elapsed-time display."""
    return """
            if (typeof parentWindow.__hhsRenderCommandElapsed !== "function") {
              parentWindow.__hhsRenderCommandElapsed = (node, startedAt) => {
                if (!node) {
                  return;
                }
                const elapsedSeconds = Math.max(
                  0,
                  Math.floor((Date.now() - Number(startedAt || Date.now())) / 1000)
                );
                const minutes = Math.floor(elapsedSeconds / 60);
                const seconds = String(elapsedSeconds % 60).padStart(2, "0");
                node.textContent = `time elapsed: ${minutes}m:${seconds}s`;
                node.classList.toggle(
                  "hhs-loader-elapsed-warning",
                  elapsedSeconds > 25 && elapsedSeconds < 60
                );
                node.classList.toggle("hhs-loader-elapsed-danger", elapsedSeconds >= 60);
              };
            }
    """.rstrip()


def command_overlay_close_button_html() -> str:
    """Return the micro close button markup for command overlay preloaders."""
    return (
        '<button class="hhs-tab-loader-close" type="button" '
        'title="Interrupt command" aria-label="Interrupt command">x</button>'
    )


def command_overlay_close_helper_js() -> str:
    """Return shared browser helpers for dismissing command overlay preloaders."""
    cancel_param = json.dumps(hhs_ui.COMMAND_PRELOADER_CANCEL_QUERY_PARAM)
    return f"""
            if (typeof parentWindow.__hhsClearCommandOverlayTimers !== "function") {{
              parentWindow.__hhsClearCommandOverlayTimers = () => {{
                if (parentWindow.__hhsCommandOverlayTimer) {{
                  parentWindow.clearInterval(parentWindow.__hhsCommandOverlayTimer);
                  parentWindow.__hhsCommandOverlayTimer = null;
                }}
                if (parentWindow.__hhsCommandOverlayExpiryTimer) {{
                  parentWindow.clearTimeout(parentWindow.__hhsCommandOverlayExpiryTimer);
                  parentWindow.__hhsCommandOverlayExpiryTimer = null;
                }}
              }};
            }}
            if (typeof parentWindow.__hhsDismissCommandOverlay !== "function") {{
              parentWindow.__hhsDismissCommandOverlay = (token = "") => {{
                const cleanToken = String(token || "").trim();
                parentWindow.__hhsCommandOverlayClearedAt = Date.now();
                parentWindow.__hhsCommandOverlayToken = "";
                parentWindow.__hhsClearCommandOverlayTimers();
                doc.body.dataset.hhsCommandOverlayHidden = "true";
                const overlay = doc.getElementById("hhs-command-overlay");
                if (overlay) {{
                  overlay.remove();
                }}
                if (!cleanToken || !cleanToken.includes(":")) {{
                  return;
                }}
                const url = new parentWindow.URL(parentWindow.location.href);
                url.searchParams.set({cancel_param}, cleanToken);
                parentWindow.location.href = url.toString();
              }};
            }}
            const bindCommandOverlayClose = (overlay) => {{
              const closeButton = overlay?.querySelector(".hhs-tab-loader-close");
              if (!closeButton || closeButton.dataset.closeHandlerInstalled === "true") {{
                return;
              }}
              closeButton.dataset.closeHandlerInstalled = "true";
              closeButton.addEventListener("click", (event) => {{
                event.preventDefault();
                event.stopPropagation();
                parentWindow.__hhsDismissCommandOverlay(
                  String(overlay.dataset.hhsOverlayToken || "")
                );
              }});
            }};
            const bindCommandLoaderClose = (loader) => {{
              const closeButton = loader?.querySelector(".hhs-command-loader-close");
              if (!closeButton || closeButton.dataset.closeHandlerInstalled === "true") {{
                return;
              }}
              closeButton.dataset.closeHandlerInstalled = "true";
              closeButton.addEventListener("click", (event) => {{
                event.preventDefault();
                event.stopPropagation();
                const token = String(
                  closeButton.dataset.hhsPreloaderToken ||
                  loader.dataset.hhsPreloaderToken ||
                  ""
                );
                loader.remove();
                parentWindow.__hhsDismissCommandOverlay(token);
              }});
            }};
    """.rstrip()


def render_command_preloader_events() -> None:
    """Flush queued command preloader events to browser CustomEvents."""
    queued_events = command_preloader_event_queue()
    if not queued_events:
        return
    events = list(queued_events)
    queued_events.clear()
    render_script_html(
        f"""
        <script>
          (() => {{
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            const events = {json.dumps(events)};
{command_elapsed_helper_js()}
{command_overlay_close_helper_js()}
            const clearOverlayTimers = () => {{
              if (parentWindow.__hhsCommandOverlayTimer) {{
                parentWindow.clearInterval(parentWindow.__hhsCommandOverlayTimer);
                parentWindow.__hhsCommandOverlayTimer = null;
              }}
              if (parentWindow.__hhsCommandOverlayExpiryTimer) {{
                parentWindow.clearTimeout(parentWindow.__hhsCommandOverlayExpiryTimer);
                parentWindow.__hhsCommandOverlayExpiryTimer = null;
              }}
            }};
            const removeOverlay = (token) => {{
              const overlay = doc.getElementById("hhs-command-overlay");
              if (!overlay) {{
                clearOverlayTimers();
                return;
              }}
              const currentToken = String(overlay.dataset.hhsOverlayToken || "");
              if (token && currentToken && currentToken !== token) {{
                return;
              }}
              overlay.remove();
              doc.body.dataset.hhsCommandOverlayHidden = "true";
              parentWindow.__hhsCommandOverlayToken = "";
              parentWindow.__hhsCommandOverlayClearedAt = Date.now();
              clearOverlayTimers();
            }};
            const renderElapsed = (overlay, startedAt, timeoutSeconds) => {{
              const node = overlay.querySelector(".hhs-tab-loader-elapsed");
              if (!node) {{
                return;
              }}
              parentWindow.__hhsRenderCommandElapsed(node, startedAt);
            }};
            const showOverlay = (detail) => {{
              const token = String(detail.token || "");
              if (!token) {{
                return;
              }}
              clearOverlayTimers();
              const timeoutSeconds = Math.max(1, Number(detail.timeoutSeconds || 1));
              const createdAt = Date.now();
              let overlay = doc.getElementById("hhs-command-overlay");
              if (!overlay) {{
                overlay = doc.createElement("div");
                overlay.id = "hhs-command-overlay";
                overlay.className = "hhs-tab-loader";
                overlay.style.position = "fixed";
                overlay.style.inset = "0";
                overlay.style.width = "auto";
                overlay.style.height = "100dvh";
                overlay.style.display = "flex";
                overlay.style.alignItems = "center";
                overlay.style.justifyContent = "center";
                overlay.style.zIndex = "1000010";
                overlay.innerHTML = `
                  <div class="hhs-tab-loader-panel">
                    {command_overlay_close_button_html()}
                    <span class="hhs-tab-loader-spinner"></span>
                    <span class="hhs-tab-loader-copy">
                      <span class="hhs-tab-loader-label"></span>
                      <span class="hhs-tab-loader-elapsed" data-timeout-seconds="${{timeoutSeconds}}">
                        time elapsed: 0m:00s
                      </span>
                    </span>
                  </div>
                `;
                doc.body.appendChild(overlay);
              }}
              overlay.classList.remove("hhs-tab-loader-transient");
              bindCommandOverlayClose(overlay);
              overlay.dataset.hhsOverlayToken = token;
              overlay.dataset.hhsOverlayCreatedAt = String(createdAt);
              overlay.dataset.hhsOverlayStartedAt = String(createdAt);
              parentWindow.__hhsCommandOverlayToken = token;
              doc.body.dataset.hhsCommandOverlayHidden = "false";
              const label = overlay.querySelector(".hhs-tab-loader-label");
              if (label) {{
                label.innerHTML = String(detail.messageHtml || "Loading...");
              }}
              renderElapsed(overlay, createdAt, timeoutSeconds);
              parentWindow.__hhsCommandOverlayTimer = parentWindow.setInterval(
                () => renderElapsed(overlay, createdAt, timeoutSeconds),
                1000
              );
            }};
            if (!parentWindow.__hhsCommandPreloaderEventHandler) {{
              parentWindow.__hhsCommandPreloaderEventHandler = (event) => {{
                const detail = event.detail || {{}};
                if (detail.event === {json.dumps(COMMAND_PRELOADER_START_EVENT)}) {{
                  showOverlay(detail);
                }} else if (
                  detail.event === {json.dumps(COMMAND_PRELOADER_FINISH_EVENT)}
                ) {{
                  removeOverlay(String(detail.token || ""));
                }}
              }};
              parentWindow.addEventListener(
                "hhs:command-preloader",
                parentWindow.__hhsCommandPreloaderEventHandler
              );
            }}
            for (const detail of events) {{
              parentWindow.dispatchEvent(
                new parentWindow.CustomEvent("hhs:command-preloader", {{ detail }})
              );
            }}
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_command_loader_timer(loader_id: str) -> None:
    """Start the elapsed-time updater for one in-flow command loader."""
    render_script_html(
        f"""
        <script>
          (() => {{
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            const loader_id = {json.dumps(loader_id)};
{command_elapsed_helper_js()}
{command_overlay_close_helper_js()}
            const selector = `[data-loader-id="${{loader_id}}"]`;
            const loader = doc.querySelector(selector);
            if (loader) {{
              bindCommandLoaderClose(loader);
            }}
            const node = loader?.querySelector(".hhs-command-loader-elapsed");
            if (!node || node.dataset.timerStarted === "true") {{
              return;
            }}
            node.dataset.timerStarted = "true";
            const started_at = Number(node.dataset.startedAt || Date.now());
            const render_elapsed = () => {{
              parentWindow.__hhsRenderCommandElapsed(node, started_at);
            }};
            render_elapsed();
            window.setInterval(render_elapsed, 1000);
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_command_loader(
    message: str,
    started_at: float | None = None,
    timeout_seconds: int | None = None,
    preloader_token: str = "",
) -> None:
    """Render the reusable banner loader for command-data waits."""
    loader_id = f"hhs-command-loader-{secrets.token_hex(8)}"
    started_at_millis = int((started_at or time.time()) * 1000)
    safe_timeout = int(timeout_seconds or command_timeout_seconds())
    st.markdown(
        command_loader_html(
            message,
            loader_id,
            started_at_millis,
            safe_timeout,
            preloader_token,
        ),
        unsafe_allow_html=True,
    )
    render_command_loader_timer(loader_id)


def render_preloader(
    message: str = "Loading...",
    transient: bool = True,
    timeout_seconds: int | None = None,
) -> None:
    """Render a full-page overlay preloader."""
    loader_class = (
        "hhs-tab-loader hhs-tab-loader-transient" if transient else "hhs-tab-loader"
    )
    safe_timeout = int(timeout_seconds or command_timeout_seconds())
    created_at_millis = int(time.time() * 1000)
    overlay_token = secrets.token_hex(8)
    safe_message_html = loader_label_html(message)
    render_script_html(
        f"""
        <script>
          (() => {{
            const parentWindow = window.parent;
            const doc = window.parent.document;
            const createdAt = {created_at_millis};
{command_elapsed_helper_js()}
{command_overlay_close_helper_js()}
            const clearedAt = Number(parentWindow.__hhsCommandOverlayClearedAt || 0);
            if (clearedAt && createdAt <= clearedAt) {{
              return;
            }}
            if (parentWindow.__hhsCommandOverlayTimer) {{
              parentWindow.clearInterval(parentWindow.__hhsCommandOverlayTimer);
              parentWindow.__hhsCommandOverlayTimer = null;
            }}
            if (parentWindow.__hhsCommandOverlayExpiryTimer) {{
              parentWindow.clearTimeout(parentWindow.__hhsCommandOverlayExpiryTimer);
              parentWindow.__hhsCommandOverlayExpiryTimer = null;
            }}
            const overlayToken = {json.dumps(overlay_token)};
            parentWindow.__hhsCommandOverlayToken = overlayToken;
            doc.body.dataset.hhsCommandOverlayHidden = "false";
            const existing = doc.getElementById("hhs-command-overlay");
            if (existing) {{
              existing.remove();
            }}
            const overlay = doc.createElement("div");
            overlay.id = "hhs-command-overlay";
            overlay.className = {json.dumps(loader_class)};
            overlay.dataset.hhsOverlayToken = overlayToken;
            overlay.dataset.hhsOverlayCreatedAt = String(createdAt);
            overlay.style.position = "fixed";
            overlay.style.inset = "0";
            overlay.style.width = "auto";
            overlay.style.height = "100dvh";
            overlay.style.display = "flex";
            overlay.style.alignItems = "center";
            overlay.style.justifyContent = "center";
            overlay.style.zIndex = "1000010";
            overlay.innerHTML = `
              <div class="hhs-tab-loader-panel">
                {command_overlay_close_button_html()}
                <span class="hhs-tab-loader-spinner"></span>
                <span class="hhs-tab-loader-copy">
                  <span class="hhs-tab-loader-label"></span>
                  <span class="hhs-tab-loader-elapsed" data-start-time="0"
                        data-timeout-seconds="{safe_timeout}">time elapsed: 0m:00s</span>
                </span>
              </div>
            `;
            const label = overlay.querySelector(".hhs-tab-loader-label");
            if (label) {{
              label.innerHTML = {json.dumps(safe_message_html)};
            }}
            bindCommandOverlayClose(overlay);
            doc.body.appendChild(overlay);
            const node = overlay.querySelector(".hhs-tab-loader-elapsed");
            if (!node || node.dataset.timerStarted === "true") {{
              return;
            }}
            node.dataset.timerStarted = "true";
            const started_at = Date.now();
            const remove_if_current = () => {{
              const current = doc.getElementById("hhs-command-overlay");
              if (
                current &&
                current.dataset.hhsOverlayToken === overlayToken &&
                parentWindow.__hhsCommandOverlayToken === overlayToken
              ) {{
                current.remove();
                doc.body.dataset.hhsCommandOverlayHidden = "true";
                parentWindow.__hhsCommandOverlayClearedAt = Math.max(
                  Number(parentWindow.__hhsCommandOverlayClearedAt || 0),
                  Date.now()
                );
              }}
              if (parentWindow.__hhsCommandOverlayTimer) {{
                parentWindow.clearInterval(parentWindow.__hhsCommandOverlayTimer);
                parentWindow.__hhsCommandOverlayTimer = null;
              }}
              if (parentWindow.__hhsCommandOverlayExpiryTimer) {{
                parentWindow.clearTimeout(parentWindow.__hhsCommandOverlayExpiryTimer);
                parentWindow.__hhsCommandOverlayExpiryTimer = null;
              }}
            }};
            const render_elapsed = () => {{
              if (!doc.body.contains(overlay)) {{
                remove_if_current();
                return;
              }}
              parentWindow.__hhsRenderCommandElapsed(node, started_at);
            }};
            render_elapsed();
            parentWindow.__hhsCommandOverlayTimer = parentWindow.setInterval(render_elapsed, 1000);
            parentWindow.__hhsCommandOverlayExpiryTimer = parentWindow.setTimeout(
              remove_if_current,
              {max(1, safe_timeout + 2) * 1000}
            );
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def clear_preloader() -> None:
    """Remove the browser-level command overlay."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = window.parent.document;
            parentWindow.__hhsCommandOverlayClearedAt = Date.now();
            parentWindow.__hhsCommandOverlayToken = "";
            if (parentWindow.__hhsCommandOverlayTimer) {
              parentWindow.clearInterval(parentWindow.__hhsCommandOverlayTimer);
              parentWindow.__hhsCommandOverlayTimer = null;
            }
            if (parentWindow.__hhsCommandOverlayExpiryTimer) {
              parentWindow.clearTimeout(parentWindow.__hhsCommandOverlayExpiryTimer);
              parentWindow.__hhsCommandOverlayExpiryTimer = null;
            }
            doc.body.dataset.hhsCommandOverlayHidden = "true";
            const remove_overlay = () => {
              const overlay = doc.getElementById("hhs-command-overlay");
              if (!overlay) {
                return;
              }
              const overlayCreatedAt = Number(overlay.dataset.hhsOverlayCreatedAt || 0);
              const clearedAt = Number(parentWindow.__hhsCommandOverlayClearedAt || 0);
              if (clearedAt && overlayCreatedAt > clearedAt) {
                return;
              }
              overlay.remove();
            };
            if (parentWindow.__hhsCommandOverlayClearObserver) {
              parentWindow.__hhsCommandOverlayClearObserver.disconnect();
              parentWindow.__hhsCommandOverlayClearObserver = null;
            }
            const observer = new parentWindow.MutationObserver(remove_overlay);
            observer.observe(doc.body, { childList: true });
            parentWindow.__hhsCommandOverlayClearObserver = observer;
            remove_overlay();
            parentWindow.setTimeout(remove_overlay, 50);
            parentWindow.setTimeout(remove_overlay, 250);
            parentWindow.setTimeout(remove_overlay, 1000);
            parentWindow.setTimeout(() => {
              observer.disconnect();
              if (parentWindow.__hhsCommandOverlayClearObserver === observer) {
                parentWindow.__hhsCommandOverlayClearObserver = null;
              }
            }, 2000);
          })();
        </script>
        """,
        height=0,
        width=0,
    )


def render_theme_reload_overlay() -> None:
    """Render the theme loading overlay and reload the browser after a short delay."""
    theme_name = str(
        st.session_state.get("theme_reload_name")
        or st.session_state.get(hhs_ui.THEME_SELECTED_KEY)
        or ""
    )
    default_theme = theme_option_from_path(
        hhs_ui.APP_THEME_CSS_FILE,
        hhs_ui.APP_THEMES_DIR,
    )
    safe_theme_name = theme_option_label(theme_name or default_theme)
    st.session_state["theme_reload_pending"] = False
    render_preloader(f"Loading theme {safe_theme_name}", transient=False)
    render_script_html(
        """
        <script>
          window.setTimeout(() => {
            window.parent.location.reload();
          }, 2000);
        </script>
        """,
        height=0,
    )
    st.stop()


def render_terminal_output(
    content: str, css_classes: str = "", content_is_html: bool = False
) -> None:
    """Render reusable terminal-style output with optional pre-rendered HTML content."""
    panel_classes = "hhs-terminal-panel"
    if css_classes:
        panel_classes = f"{panel_classes} {css_classes}"
    safe_content = content if content_is_html else html.escape(content)
    st.markdown(
        f'<div class="{panel_classes}">{safe_content}</div>', unsafe_allow_html=True
    )


def set_overlay(
    active: bool,
    message: str = "Loading...",
    transient: bool = False,
    close_dialogs: bool = False,
    timeout_seconds: int | None = None,
) -> None:
    """Show or hide the reusable full-page command overlay."""
    if active:
        if close_dialogs:
            close_all_dialogs()
        save_ui_state()
        render_preloader(message, transient=transient, timeout_seconds=timeout_seconds)
        time.sleep(0.1)
        return

    clear_preloader()
