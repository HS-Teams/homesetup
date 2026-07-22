#!/usr/bin/env python3
"""Footer UI and footer action helpers for the HomeSetup Streamlit app."""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import time
from collections.abc import Callable

import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.core.alert_history import (
    clear_footer_alerts,
    footer_alert_glyph,
    footer_alert_priority,
    footer_alerts_file,
    today_footer_alerts,
)
from hhs_ui.execution.cache_runtime import (
    background_command_metadata,
    cache_background_command_result,
    cache_delete_command,
    cache_delete_tag,
    cached_background_command_result,
    clear_cached_ui_data_preserving_state,
)
from hhs_ui.execution.command_catalog import (
    build_footer_working_directory_command,
    build_hhs_updater_command,
    build_homesetup_version_command,
    clean_command_status_message,
    open_file,
    strip_ansi,
)
from hhs_ui.execution.command_runtime import (
    background_job_is_running,
    background_job_result,
    run_bash_command,
    start_background_bash_command,
    stop_background_job_by_preloader_token,
)
from hhs_ui.widgets.dialog_ui import pop_dialog
from hhs_ui.widgets.feedback_ui import render_terminal_output
from hhs_ui.core.paths import homesetup_home
from hhs_ui.core.runtime import shell_version_command
from hhs_ui.features.ssh_core import ssh_connection_display
from hhs_ui.features.ssh_runtime import connected_ssh_host
from hhs_ui.widgets.status_ui import (
    drain_footer_status_log_records,
    push_floating_status,
    render_floating_status,
)
from hhs_ui.widgets.terminal_ui import (
    browser_cleanup_token,
    ensure_ttyd_cleanup_server,
    sync_ttyd_event_state,
    update_browser_cleanup_registration,
)
from hhs_ui.core.theme_assets import load_app_image_data_uri
from hhs_ui.core.ui_definitions import (
    FOOTER_VERSION_CACHE_TAG,
    FOOTER_VERSION_JOB,
    FOOTER_VERSION_OUTPUT_MARKER,
    FOOTER_WORKING_DIR_JOB,
    TERMINAL_AI_DEFAULT_PROMPT,
    UPDATER_UPDATE_JOB,
)
from hhs_ui.core.ui_state import is_persisted_ui_key, save_ui_state, ui_state_files


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"footer UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
execute_due_updater_check = _unconfigured_dependency("execute_due_updater_check")
terminal_document_view_is_active = _unconfigured_dependency(
    "terminal_document_view_is_active"
)
updater_check_context = _unconfigured_dependency("updater_check_context")
clear_ai_chat_history = _unconfigured_dependency("clear_ai_chat_history")
open_remote_explorer_path = _unconfigured_dependency("open_remote_explorer_path")
open_search_result_path = _unconfigured_dependency("open_search_result_path")


def configure_footer_ui(
    *,
    render_script_html: Callable[..., None],
    execute_due_updater_check: Callable[[], None],
    terminal_document_view_is_active: Callable[[], bool],
    updater_check_context: Callable[[], str],
    clear_ai_chat_history: Callable[[], None],
    open_remote_explorer_path: Callable[[str], None],
    open_search_result_path: Callable[[str], None],
) -> None:
    """Configure callbacks required by footer helpers."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "execute_due_updater_check": execute_due_updater_check,
            "terminal_document_view_is_active": terminal_document_view_is_active,
            "updater_check_context": updater_check_context,
            "clear_ai_chat_history": clear_ai_chat_history,
            "open_remote_explorer_path": open_remote_explorer_path,
            "open_search_result_path": open_search_result_path,
        }
    )


def footer_version_context() -> str:
    """Return the command context used by the footer HomeSetup version probe."""
    return connected_ssh_host() or "local"


def local_homesetup_version() -> str:
    """Return the local HomeSetup version without issuing shell or SSH commands."""
    version = os.environ.get("HHS_VERSION", "").strip()
    if version:
        return version
    try:
        version = (homesetup_home() / ".VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        version = ""
    return version or "loading"


def parse_homesetup_version_output(output: str) -> str:
    """Return the marker-delimited HomeSetup version from command output."""
    clean_output = strip_ansi(output or "").replace("\r", "")
    marker_index = clean_output.rfind(FOOTER_VERSION_OUTPUT_MARKER)
    if marker_index < 0:
        return ""
    marker_output = clean_output[marker_index + len(FOOTER_VERSION_OUTPUT_MARKER) :]
    return marker_output.splitlines()[0].strip()


def remember_footer_homesetup_version(version: str, context: str) -> str:
    """Store the last known footer HomeSetup version for the active context."""
    clean_version = version.strip()
    if not clean_version:
        return ""
    st.session_state["footer_hhs_version"] = clean_version
    st.session_state["footer_hhs_version_context"] = context
    st.session_state["footer_hhs_version_error"] = ""
    st.session_state["footer_hhs_version_cache_loaded"] = True
    return clean_version


def fallback_footer_homesetup_version(context: str) -> str:
    """Return the best available footer HomeSetup version while refresh is pending."""
    if st.session_state.get("footer_hhs_version_context") == context:
        version = str(st.session_state.get("footer_hhs_version", "")).strip()
        if version:
            return version
    return local_homesetup_version()


def footer_homesetup_version_retry_allowed(context: str) -> bool:
    """Return whether a failed footer version refresh can be retried now."""
    if st.session_state.get("footer_hhs_version_error_context") != context:
        return True
    try:
        failed_at = float(st.session_state.get("footer_hhs_version_error_at", 0.0))
    except (TypeError, ValueError):
        failed_at = 0.0
    retry_seconds = max(60, int(hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS))
    return failed_at <= 0.0 or time.time() - failed_at >= retry_seconds


def record_footer_homesetup_version_error(
    context: str, result: subprocess.CompletedProcess[str]
) -> None:
    """Remember a failed footer version refresh without clearing SSH state."""
    st.session_state["footer_hhs_version_error_context"] = context
    st.session_state["footer_hhs_version_error_at"] = time.time()
    st.session_state["footer_hhs_version_error"] = clean_command_status_message(
        result.stderr or result.stdout or "Unable to load HomeSetup version."
    )
    st.session_state["footer_hhs_version_cache_loaded"] = True


def complete_footer_homesetup_version_refresh(context: str) -> str:
    """Complete one footer version background refresh for the active context."""
    completed = background_job_result(FOOTER_VERSION_JOB)
    if completed is None:
        return ""
    result, metadata = completed
    completed_context = str(metadata.get("footer_version_context", "") or context)
    version = parse_homesetup_version_output(result.stdout or "")
    if result.returncode == 0 and version:
        cache_background_command_result(metadata, result)
        if completed_context == context:
            return remember_footer_homesetup_version(version, completed_context)
        return ""
    if completed_context == context:
        record_footer_homesetup_version_error(context, result)
    return ""


def start_footer_homesetup_version_refresh(command: str, context: str) -> None:
    """Start a host-aware footer version refresh in the background."""
    metadata = {
        **background_command_metadata(command, FOOTER_VERSION_CACHE_TAG),
        "ttl_seconds": hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        "footer_version_context": context,
    }
    start_background_bash_command(
        FOOTER_VERSION_JOB,
        command,
        "Loading HomeSetup version",
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        metadata=metadata,
    )


def homesetup_version(refresh_cache: bool = False) -> str:
    """Return the cached HomeSetup product version for the active command host."""
    context = footer_version_context()
    command = build_homesetup_version_command()
    if st.session_state.get("footer_hhs_version_context") != context:
        st.session_state["footer_hhs_version_cache_loaded"] = False

    completed_version = complete_footer_homesetup_version_refresh(context)
    if completed_version:
        return completed_version

    if refresh_cache:
        cache_delete_command(command, FOOTER_VERSION_CACHE_TAG)

    result, fresh_cache = cached_background_command_result(
        command, FOOTER_VERSION_CACHE_TAG
    )
    if result is not None and result.returncode == 0:
        version = parse_homesetup_version_output(result.stdout or "")
        if version:
            return remember_footer_homesetup_version(version, context)

    if (
        not fresh_cache
        and not background_job_is_running(FOOTER_VERSION_JOB)
        and footer_homesetup_version_retry_allowed(context)
    ):
        start_footer_homesetup_version_refresh(command, context)
    return fallback_footer_homesetup_version(context)


def render_footer_client_error_bridge_script() -> None:
    """Mirror client-side Streamlit errors and alerts into the footer status UI."""
    alert_endpoint = footer_alert_endpoint_url()
    script = """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (!doc?.body) {
              return;
            }
            const alertEndpoint = __HHS_FOOTER_ALERT_ENDPOINT__;
            parentWindow.__hhsRecordFooterAlert = (message, kind) => {
              const payload = JSON.stringify({ message, kind });
              const blob = new Blob([payload], { type: "text/plain;charset=UTF-8" });
              if (parentWindow.navigator.sendBeacon(alertEndpoint, blob)) {
                return;
              }
              void parentWindow.fetch(alertEndpoint, {
                method: "POST",
                body: payload,
                headers: { "Content-Type": "text/plain;charset=UTF-8" },
                keepalive: true,
              }).catch(() => undefined);
            };
            if (typeof parentWindow.__hhsCopyFooterStatusText !== "function") {
              parentWindow.__hhsCopyFooterStatusText = async (value) => {
                const copyValue = String(value ?? "");
                try {
                  await parentWindow.navigator.clipboard.writeText(copyValue);
                  return true;
                } catch (_clipboardError) {
                  const textarea = doc.createElement("textarea");
                  textarea.value = copyValue;
                  textarea.setAttribute("readonly", "");
                  textarea.style.position = "fixed";
                  textarea.style.opacity = "0";
                  doc.body.append(textarea);
                  textarea.select();
                  const copied = doc.execCommand("copy");
                  textarea.remove();
                  return copied;
                }
              };
            }
            if (parentWindow.__hhsFooterErrorBridgeInstalled) {
              return;
            }
            parentWindow.__hhsFooterErrorBridgeInstalled = true;

            const normalize = (value) => String(value ?? "").replace(/\\s+/g, " ").trim();
            const recentMessages = new Map();

            const remember = (message) => {
              const now = Date.now();
              for (const [knownMessage, createdAt] of recentMessages.entries()) {
                if (now - createdAt > 10000) {
                  recentMessages.delete(knownMessage);
                }
              }
              if (recentMessages.has(message)) {
                return false;
              }
              recentMessages.set(message, now);
              return true;
            };

            const updateAlertsControl = (message, kind, glyphText) => {
              const control = doc.querySelector(".hhs-footer-alerts-control");
              const menu = control?.querySelector(".hhs-footer-alerts-menu");
              const list = control?.querySelector(".hhs-footer-alerts-list");
              if (!control || !menu || !list) {
                return;
              }
              control.hidden = false;
              if (kind === "error") {
                menu.classList.remove("hhs-footer-alerts-menu--warn");
                menu.classList.add("hhs-footer-alerts-menu--error");
              }
              const triggerGlyph = menu.querySelector(".hhs-footer-glyph-button");
              if (triggerGlyph && (
                kind === "error"
                || !menu.classList.contains("hhs-footer-alerts-menu--error")
              )) {
                triggerGlyph.textContent = glyphText;
              }
              const timestamp = new Date();
              const lastItem = list.lastElementChild;
              const lastTimestamp = new Date(
                lastItem?.dataset.alertTimestamp || ""
              );
              if (
                lastItem?.dataset.alertKind === kind
                && lastItem.dataset.alertMessage === message
                && timestamp - lastTimestamp <= 10000
              ) {
                return;
              }
              const item = doc.createElement("li");
              item.className =
                `hhs-footer-alerts-item hhs-footer-alerts-item--${kind}`;
              item.title = message;
              item.dataset.alertKind = kind;
              item.dataset.alertMessage = message;
              item.dataset.alertTimestamp = timestamp.toISOString();

              const date = doc.createElement("time");
              date.dateTime = timestamp.toISOString();
              date.dataset.hhsLocalDate = timestamp.toISOString();
              date.textContent = new Intl.DateTimeFormat(undefined, {
                dateStyle: "short",
              }).format(timestamp);
              const itemGlyph = doc.createElement("span");
              itemGlyph.className = "hhs-footer-alerts-item-glyph";
              itemGlyph.setAttribute("aria-hidden", "true");
              itemGlyph.textContent = glyphText;
              const itemMessage = doc.createElement("span");
              itemMessage.className = "hhs-footer-alerts-item-message";
              itemMessage.textContent = message;
              item.append(date, itemGlyph, itemMessage);
              list.append(item);
            };

            const showStatus = (message, kind = "error") => {
              const cleanMessage = normalize(message);
              if (!cleanMessage || !remember(cleanMessage)) {
                return;
              }
              const glyphText = kind === "error" ? "" : "";
              parentWindow.__hhsRecordFooterAlert(cleanMessage, kind);
              updateAlertsControl(cleanMessage, kind, glyphText);
              doc.getElementById("hhs-client-floating-status")?.remove();
              const status = doc.createElement("div");
              status.id = "hhs-client-floating-status";
              status.className = `hhs-floating-status hhs-floating-status-kind-${kind} hhs-floating-status--stable`;
              status.style.setProperty("--hhs-floating-status-timeout", "10s");

              const glyph = doc.createElement("span");
              glyph.className = "hhs-floating-status-glyph";
              glyph.textContent = glyphText;

              const text = doc.createElement("span");
              text.className = "hhs-floating-status-message";
              text.textContent = cleanMessage;

              const dismiss = doc.createElement("button");
              dismiss.className = "hhs-floating-status-dismiss";
              dismiss.type = "button";
              dismiss.setAttribute("aria-label", "Dismiss status message");
              dismiss.title = "Dismiss status message";
              dismiss.textContent = "x";
              dismiss.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                status.classList.add("hhs-floating-status--disposing");
                parentWindow.clearTimeout(parentWindow.__hhsFooterErrorBridgeTimer);
                parentWindow.setTimeout(() => status.remove(), 240);
              });

              status.append(glyph, text);
              if (kind === "error") {
                const copy = doc.createElement("button");
                copy.className = "hhs-floating-status-copy";
                copy.type = "button";
                copy.setAttribute("aria-label", "Copy error details");
                copy.title = "Copy error details";
                copy.textContent = "";
                copy.addEventListener("click", async (event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  await parentWindow.__hhsCopyFooterStatusText(cleanMessage);
                });
                status.append(copy);
              }
              status.append(dismiss);
              doc.body.append(status);
              parentWindow.clearTimeout(parentWindow.__hhsFooterErrorBridgeTimer);
              parentWindow.__hhsFooterErrorBridgeTimer = parentWindow.setTimeout(() => {
                status.remove();
              }, 11000);
            };

            const scanAlerts = () => {
              doc.querySelectorAll('[data-testid="stAlert"]').forEach((alert) => {
                const message = normalize(alert.textContent);
                const mirrorsError = [
                  /missing submit button/i,
                  /warning/i,
                  /exception/i,
                  /traceback/i,
                  /error/i,
                  /failed/i,
                  /unable/i,
                  /not found/i,
                  /cannot/i,
                  /can't/i,
                ].some((pattern) => pattern.test(message));
                if (!message || !mirrorsError) {
                  return;
                }
                const kind = /warning|missing submit button/i.test(message)
                  ? "warn"
                  : "error";
                showStatus(message, kind);
              });
            };

            const observer = new MutationObserver(scanAlerts);
            observer.observe(doc.body, {
              childList: true,
              subtree: true,
              characterData: true,
            });
            scanAlerts();

            const originalConsoleError = parentWindow.console.error.bind(
              parentWindow.console
            );
            parentWindow.console.error = (...args) => {
              showStatus(args.map(normalize).filter(Boolean).join(" "), "error");
              originalConsoleError(...args);
            };
            parentWindow.addEventListener("error", (event) => {
              showStatus(event.message, "error");
            });
            parentWindow.addEventListener("unhandledrejection", (event) => {
              showStatus(event.reason?.message || event.reason, "error");
            });
          })();
        </script>
        """
    render_script_html(
        script.replace("__HHS_FOOTER_ALERT_ENDPOINT__", json.dumps(alert_endpoint))
    )


def footer_cache_clear_menu_markup() -> str:
    """Return the footer cleanup menu using button-based checkbox controls."""
    clear_param = html.escape(hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM, quote=True)
    options = (
        (
            hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM,
            "Clear application cache",
            "Clear cached command data and refresh it when next needed",
        ),
        (
            hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM,
            "Clear application states",
            "Clear saved UI selections and preferences",
        ),
        (
            hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM,
            "Clear AI history",
            "Clear the HomeSetup AI conversation history",
        ),
    )
    option_markup = "".join(
        (
            '<button class="hhs-footer-cache-clear-option" type="button" '
            'role="checkbox" aria-checked="false" '
            f'data-param="{html.escape(param, quote=True)}" '
            f'title="{html.escape(tooltip, quote=True)}">'
            '<span class="hhs-footer-cache-clear-option-mark" aria-hidden="true"></span>'
            f'<span>{html.escape(label)}</span></button>'
        )
        for param, label, tooltip in options
    )
    return (
        '<details class="hhs-footer-cache-clear-menu">'
        '<summary class="hhs-footer-cache-clear-trigger" '
        'title="Open cleanup options" aria-label="Open cleanup options">'
        '<span class="hhs-footer-glyph-button">♻</span></summary>'
        f'<div class="hhs-footer-cache-clear-panel" data-clear-param="{clear_param}">'
        f'{option_markup}'
        '<button class="hhs-footer-cache-clear-submit" type="button" '
        'title="Apply the selected cleanup options">OK</button>'
        '</div></details>'
    )


def render_footer_cache_clear_menu_script() -> None:
    """Manage safe button-based cleanup selections and submit them by query string."""
    render_script_html(
        """
        <script>
          (() => {
            const doc = window.parent.document;
            const panel = doc.querySelector(".hhs-footer-cache-clear-panel");
            if (!panel) {
              return;
            }
            const menu = panel.closest(".hhs-footer-cache-clear-menu");
            const closeMenu = () => menu?.removeAttribute("open");
            if (panel.dataset.handlersInstalled !== "true") {
              panel.dataset.handlersInstalled = "true";
              panel.querySelectorAll('.hhs-footer-cache-clear-option[role="checkbox"]')
                .forEach((option) => {
                  option.addEventListener("click", () => {
                    const selected = option.getAttribute("aria-checked") === "true";
                    option.setAttribute("aria-checked", selected ? "false" : "true");
                  });
                });
              panel.querySelector(".hhs-footer-cache-clear-submit")
                ?.addEventListener("click", () => {
                  const selectedOptions = Array.from(
                    panel.querySelectorAll(
                      '.hhs-footer-cache-clear-option[role="checkbox"][aria-checked="true"]'
                    )
                  );
                  if (!selectedOptions.length) {
                    closeMenu();
                    return;
                  }
                  const params = new URLSearchParams(window.parent.location.search);
                  params.set(panel.dataset.clearParam, "1");
                  selectedOptions.forEach((option) => {
                    params.set(option.dataset.param, "1");
                  });
                  window.parent.location.search = params.toString();
                });
              menu?.addEventListener("toggle", () => {
                if (!menu.open) {
                  return;
                }
                panel.querySelectorAll('.hhs-footer-cache-clear-option[role="checkbox"]')
                  .forEach((option) => option.setAttribute("aria-checked", "false"));
                doc.querySelectorAll(
                  ".hhs-footer-terminal-ai-menu[open], "
                  + ".hhs-footer-alerts-menu[open]"
                ).forEach((otherMenu) => otherMenu.removeAttribute("open"));
              });
            }
            if (window.parent.__hhsFooterCacheClearOutsideHandler) {
              doc.removeEventListener(
                "pointerdown",
                window.parent.__hhsFooterCacheClearOutsideHandler,
                true
              );
            }
            const outsideHandler = (event) => {
              if (menu?.open && !menu.contains(event.target)) {
                closeMenu();
              }
            };
            window.parent.__hhsFooterCacheClearOutsideHandler = outsideHandler;
            doc.addEventListener("pointerdown", outsideHandler, true);
          })();
        </script>
        """,
        height=0,
        width=0,
    )


def footer_terminal_ai_menu_markup(enabled: bool) -> str:
    """Return the native HTML footer terminal AI prompt menu."""
    default_prompt = html.escape(TERMINAL_AI_DEFAULT_PROMPT, quote=True)
    if not enabled:
        return """
      <span class="hhs-footer-terminal-ai-menu hhs-footer-terminal-ai-menu--disabled"
            title="Open Terminal to ask AI about any terminal content"
            aria-disabled="true">
        <span class="hhs-footer-terminal-ai-trigger hhs-footer-terminal-ai-trigger--disabled"
              aria-label="Ask AI about any terminal content disabled"
              title="Open Terminal to ask AI about any terminal content">
          <span class="hhs-footer-glyph-button"></span>
        </span>
      </span>
    """.strip()
    return f"""
      <details class="hhs-footer-terminal-ai-menu">
        <summary class="hhs-footer-terminal-ai-trigger"
                 title="Ask AI about any terminal content"
                 aria-label="Ask AI about any terminal content">
          <span class="hhs-footer-glyph-button"></span>
        </summary>
        <div class="hhs-footer-terminal-ai-panel" data-default-prompt="{default_prompt}">
          <label>
            <span>Prompt</span>
            <input
              class="hhs-footer-terminal-ai-prompt-input"
              type="text"
              value=""
              placeholder="{default_prompt}"
              aria-label="Terminal AI prompt"
              title="Describe how HomeSetup should analyze the captured terminal output"
            >
          </label>
          <label class="hhs-footer-terminal-ai-context-preview">
            <span>Terminal text</span>
            <input
              class="hhs-footer-terminal-ai-context-input"
              type="text"
              value=""
              placeholder="Terminal text"
              aria-label="Captured terminal text"
              title="Terminal output that will be sent to HomeSetup AI"
              readonly
            >
          </label>
          <button type="button" title="Send this terminal output to HomeSetup AI">OK</button>
        </div>
      </details>
    """.strip()


def render_footer_terminal_ai_menu_script() -> None:
    """Submit terminal context prompt choices directly into the ttyd terminal."""
    render_script_html(
        f"""
        <script>
          (async () => {{
            const doc = window.parent.document;
            const panelWaitTimeoutMs = 5000;
            const waitForTerminalAiPanel = () => {{
              const currentPanel = doc.querySelector(".hhs-footer-terminal-ai-panel");
              if (currentPanel) {{
                return Promise.resolve(currentPanel);
              }}
              return new Promise((resolve) => {{
                let timeoutId = 0;
                const observer = new window.parent.MutationObserver(() => {{
                  const panel = doc.querySelector(".hhs-footer-terminal-ai-panel");
                  if (panel) {{
                    finish(panel);
                  }}
                }});
                const finish = (panel) => {{
                  observer.disconnect();
                  window.parent.clearTimeout(timeoutId);
                  resolve(panel);
                }};
                timeoutId = window.parent.setTimeout(() => finish(null), panelWaitTimeoutMs);
                observer.observe(doc.body, {{ childList: true, subtree: true }});
              }});
            }};
            const panel = await waitForTerminalAiPanel();
            if (!panel || panel.dataset.clickHandlerInstalled === "true") {{
              return;
            }}
            panel.dataset.clickHandlerInstalled = "true";
            const menu = panel.closest(".hhs-footer-terminal-ai-menu");
            const trigger = menu?.querySelector(".hhs-footer-terminal-ai-trigger");
            const input = panel.querySelector(".hhs-footer-terminal-ai-prompt-input");
            const contextInput = panel.querySelector(".hhs-footer-terminal-ai-context-input");
            const button = panel.querySelector("button");
            const defaultPrompt = {json.dumps(TERMINAL_AI_DEFAULT_PROMPT)};
            const contextDelayMs = 700;
            const contextWaitIntervalMs = 50;
            const contextPreviewMaxChars = 180;
            let currentTerminalContextEvent = null;
            let ignoreTerminalContextUntil = 0;
            const cleanTerminalContent = (value) => String(value || "")
              .replace(/\\r\\n?/g, "\\n")
              .trim();
            const cleanTerminalPreview = (value) => cleanTerminalContent(value).replace(/\\s+/g, " ");
            const contextPreviewText = (value) => {{
              const cleanValue = cleanTerminalPreview(value);
              if (cleanValue.length <= contextPreviewMaxChars) {{
                return cleanValue;
              }}
              return `${{cleanValue.slice(0, contextPreviewMaxChars - 1)}}…`;
            }};
            const terminalEventMatchesRequest = (terminalEvent) => {{
              const activeRequestId = panel.dataset.requestId || "";
              const eventRequestId = String(terminalEvent.requestId || "");
              return !activeRequestId || eventRequestId === activeRequestId;
            }};
            const setTerminalContextPreview = (value) => {{
              if (!contextInput) {{
                return;
              }}
              const cleanValue = cleanTerminalPreview(value);
              contextInput.value = contextPreviewText(cleanValue);
              contextInput.title = cleanValue;
              contextInput.dataset.empty = cleanValue ? "false" : "true";
            }};
            const requestTerminalContext = (force = false) => {{
              if (!force && panel.dataset.requestId) {{
                return panel.dataset.requestId;
              }}
              const requestId = `${{Date.now()}}-${{Math.random().toString(36).slice(2)}}`;
              panel.dataset.requestId = requestId;
              currentTerminalContextEvent = null;
              setTerminalContextPreview("");
              const frame = doc.getElementById("hhs-persistent-ttyd-frame");
              if (frame && frame.contentWindow) {{
                frame.contentWindow.postMessage({{
                  type: "hhs-ttyd-context-request",
                  requestId,
                }}, "*");
              }}
              return requestId;
            }};
            const applyTerminalContextEvent = (terminalEvent) => {{
              if (Date.now() < ignoreTerminalContextUntil) {{
                return false;
              }}
              if (!terminalEvent || terminalEvent.type !== "terminal-context") {{
                return false;
              }}
              if (!terminalEventMatchesRequest(terminalEvent)) {{
                return false;
              }}
              currentTerminalContextEvent = terminalEvent;
              setTerminalContextPreview(terminalEvent.content || "");
              return true;
            }};
            const matchingTerminalContextEvent = () => {{
              if (Date.now() < ignoreTerminalContextUntil) {{
                return null;
              }}
              const terminalEvent = currentTerminalContextEvent || window.parent.__hhsTtydTerminalContextEvent;
              if (!terminalEvent || terminalEvent.type !== "terminal-context") {{
                return null;
              }}
              if (terminalEventMatchesRequest(terminalEvent)) {{
                return terminalEvent;
              }}
              return terminalEvent.content ? terminalEvent : null;
            }};
            const refreshTerminalContextPreview = () => {{
              applyTerminalContextEvent(window.parent.__hhsTtydTerminalContextEvent);
            }};
            const waitForTerminalContextEvent = async (timeoutMs = contextDelayMs) => {{
              const deadline = Date.now() + timeoutMs;
              while (Date.now() < deadline) {{
                refreshTerminalContextPreview();
                const terminalEvent = matchingTerminalContextEvent();
                if (terminalEvent?.content) {{
                  currentTerminalContextEvent = terminalEvent;
                  setTerminalContextPreview(terminalEvent.content || "");
                  return terminalEvent;
                }}
                await new Promise((resolve) => window.setTimeout(resolve, contextWaitIntervalMs));
              }}
              refreshTerminalContextPreview();
              return matchingTerminalContextEvent();
            }};
            const closeMenu = () => {{
              if (menu) {{
                menu.removeAttribute("open");
              }}
            }};
            const resetTerminalInputs = () => {{
              if (input) {{
                input.value = "";
              }}
              ignoreTerminalContextUntil = Date.now() + 1200;
              currentTerminalContextEvent = null;
              delete panel.dataset.requestId;
              setTerminalContextPreview("");
            }};
            const shellSingleQuote = (value) => (
              "'" + String(value || "").replace(/'/g, "'\\\\''") + "'"
            );
            const shellDoubleQuote = (value) => JSON.stringify(String(value || ""))
              .replace(/\\$/g, "\\\\$")
              .replace(/`/g, "\\\\`");
            const buildTerminalAskPrompt = (instruction) => (
              String(instruction || defaultPrompt).trim() || defaultPrompt
            );
            const buildTerminalAskContext = (terminalEvent) => {{
              const eventContent = terminalEvent?.content || "";
              const previewContent = contextInput?.title || contextInput?.value || "";
              const content = cleanTerminalContent(eventContent || previewContent);
              return `${{content}}\\n\\n`;
            }};
            const buildTerminalAskCommand = (instruction, terminalEvent) => (
              `echo ${{shellSingleQuote(buildTerminalAskContext(terminalEvent))}} | __hhs ask execute ${{shellDoubleQuote(buildTerminalAskPrompt(instruction))}}`
            );
            const submitTerminalCommand = (command) => {{
              const frame = doc.getElementById("hhs-persistent-ttyd-frame");
              if (!frame || !frame.contentWindow) {{
                return false;
              }}
              frame.contentWindow.postMessage({{
                type: "hhs-ttyd-command-submit",
                command,
              }}, "*");
              return true;
            }};
            const terminalContextHandler = (event) => {{
              const data = event.data || {{}};
              if (data.type !== "hhs-ttyd-event") {{
                return;
              }}
              applyTerminalContextEvent(data.event || {{}});
            }};
            if (window.parent.__hhsFooterTerminalAiContextHandler) {{
              window.parent.removeEventListener(
                "message",
                window.parent.__hhsFooterTerminalAiContextHandler
              );
            }}
            window.parent.__hhsFooterTerminalAiContextHandler = terminalContextHandler;
            window.parent.addEventListener("message", terminalContextHandler);
            if (window !== window.parent) {{
              window.addEventListener("message", terminalContextHandler);
            }}
            const outsidePointerHandler = (event) => {{
              if (!menu || !menu.open || menu.contains(event.target)) {{
                return;
              }}
              closeMenu();
            }};
            const outsideFocusHandler = () => {{
              window.setTimeout(() => {{
                const activeElement = doc.activeElement;
                if (!menu || !menu.open || !activeElement || menu.contains(activeElement)) {{
                  return;
                }}
                closeMenu();
              }}, 0);
            }};
            if (window.parent.__hhsFooterTerminalAiOutsideHandler) {{
              doc.removeEventListener(
                "pointerdown",
                window.parent.__hhsFooterTerminalAiOutsideHandler,
                true
              );
              doc.removeEventListener(
                "focusin",
                window.parent.__hhsFooterTerminalAiOutsideHandler,
                true
              );
            }}
            if (window.parent.__hhsFooterTerminalAiOutsideFocusHandler) {{
              window.parent.removeEventListener(
                "blur",
                window.parent.__hhsFooterTerminalAiOutsideFocusHandler,
                true
              );
            }}
            window.parent.__hhsFooterTerminalAiOutsideHandler = outsidePointerHandler;
            window.parent.__hhsFooterTerminalAiOutsideFocusHandler = outsideFocusHandler;
            doc.addEventListener("pointerdown", outsidePointerHandler, true);
            doc.addEventListener("focusin", outsidePointerHandler, true);
            window.parent.addEventListener("blur", outsideFocusHandler, true);
            const focusInput = () => {{
              if (!input) {{
                return;
              }}
              input.focus();
              input.select();
            }};
            trigger?.addEventListener("pointerdown", () => {{
              if (!menu || !menu.open) {{
                requestTerminalContext(true);
              }}
            }}, {{ capture: true }});
            if (menu) {{
              menu.addEventListener("toggle", () => {{
                if (menu.open) {{
                  ignoreTerminalContextUntil = 0;
                  doc.querySelectorAll(".hhs-footer-cache-clear-menu[open]").forEach((otherMenu) => {{
                    otherMenu.removeAttribute("open");
                  }});
                  doc.querySelectorAll(".hhs-footer-alerts-menu[open]").forEach((otherMenu) => {{
                    otherMenu.removeAttribute("open");
                  }});
                  requestTerminalContext(false);
                  window.setTimeout(() => {{
                    void waitForTerminalContextEvent(contextDelayMs);
                  }}, 0);
                  window.setTimeout(refreshTerminalContextPreview, 80);
                  window.setTimeout(refreshTerminalContextPreview, 220);
                  window.setTimeout(focusInput, 120);
                }} else {{
                  delete panel.dataset.requestId;
                  currentTerminalContextEvent = null;
                  setTerminalContextPreview("");
                }}
              }});
            }}
            button?.addEventListener("click", async () => {{
              requestTerminalContext(false);
              const prompt = (input?.value || defaultPrompt).trim() || defaultPrompt;
              const terminalEvent = await waitForTerminalContextEvent(contextDelayMs);
              const command = buildTerminalAskCommand(prompt, terminalEvent);
              const submitted = submitTerminalCommand(command);
              if (submitted) {{
                resetTerminalInputs();
              }}
              closeMenu();
            }});
            input?.addEventListener("keydown", (event) => {{
              if (event.key === "Enter") {{
                event.preventDefault();
                button?.click();
              }}
              if (event.key === "Escape" && menu) {{
                event.preventDefault();
                menu.removeAttribute("open");
              }}
            }});
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def browser_ui_endpoint_url(endpoint: str) -> str:
    """Return one authenticated local browser-to-UI endpoint URL."""
    update_browser_cleanup_registration()
    token = browser_cleanup_token()
    port = ensure_ttyd_cleanup_server()
    clean_endpoint = endpoint.strip("/")
    return f"http://{hhs_ui.TTYD_HOST}:{port}/{clean_endpoint}?token={token}"


def open_working_directory_endpoint_url() -> str:
    """Return the local browser-to-UI endpoint URL for opening the working directory."""
    return browser_ui_endpoint_url("open-working-directory")


def footer_alert_endpoint_url() -> str:
    """Return the local browser-to-UI endpoint URL for persisting client alerts."""
    return browser_ui_endpoint_url("footer-alert")


def render_footer_working_directory_open_script() -> None:
    """Install the no-navigation footer working-directory opener."""
    open_url = open_working_directory_endpoint_url()
    render_script_html(
        f"""
        <script>
          (() => {{
            const doc = window.parent.document;
            const openUrl = {json.dumps(open_url)};
            if (window.parent.__hhsFooterWorkingDirOpenHandler) {{
              doc.removeEventListener(
                "click",
                window.parent.__hhsFooterWorkingDirOpenHandler,
                true
              );
            }}
            const handler = (event) => {{
              const target = event.target;
              const selector = ".hhs-footer-working-dir-link[data-open-working-dir-url]";
              const link = target?.closest?.(selector);
              if (!link) {{
                return;
              }}
              const fallback = () => {{
                const href = String(link.getAttribute("href") || "");
                if (href && href !== "#") {{
                  window.parent.location.href = href;
                }}
              }};
              event.preventDefault();
              event.stopPropagation();
              fetch(link.dataset.openWorkingDirUrl || openUrl, {{
                method: "POST",
                keepalive: true,
              }})
                .then((response) => {{
                  if (!response.ok) {{
                    fallback();
                  }}
                }})
                .catch(fallback);
            }};
            window.parent.__hhsFooterWorkingDirOpenHandler = handler;
            doc.addEventListener("click", handler, true);
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def footer_alert_items_markup(alerts: list[dict[str, object]]) -> str:
    """Return today's footer alerts as localized-date popover rows."""
    items = []
    for alert in alerts:
        kind = str(alert.get("kind", "warn"))
        message = str(alert.get("message", ""))
        timestamp_iso = str(alert.get("timestamp_iso", ""))
        fallback_date = timestamp_iso.partition("T")[0]
        items.append(
            f'<li class="hhs-footer-alerts-item hhs-footer-alerts-item--{kind}" '
            f'title="{html.escape(message, quote=True)}" '
            f'data-alert-kind="{html.escape(kind, quote=True)}" '
            f'data-alert-message="{html.escape(message, quote=True)}" '
            f'data-alert-timestamp="{html.escape(timestamp_iso, quote=True)}">'
            f'<time datetime="{html.escape(timestamp_iso, quote=True)}" '
            f'data-hhs-local-date="{html.escape(timestamp_iso, quote=True)}">'
            f"{html.escape(fallback_date)}</time>"
            f'<span class="hhs-footer-alerts-item-glyph" aria-hidden="true">'
            f"{footer_alert_glyph(kind)}</span>"
            f'<span class="hhs-footer-alerts-item-message">'
            f"{html.escape(message)}</span></li>"
        )
    return f'<ol class="hhs-footer-alerts-list">{"".join(items)}</ol>'


def footer_alerts_menu_markup(alerts: list[dict[str, object]]) -> str:
    """Return the footer alert list using the native footer popover pattern."""
    alerts_kind = footer_alert_priority(alerts)
    hidden_attribute = "" if alerts else " hidden"
    view_param = html.escape(hhs_ui.FOOTER_VIEW_ALERTS_QUERY_PARAM, quote=True)
    clear_param = html.escape(hhs_ui.FOOTER_CLEAR_ALERTS_QUERY_PARAM, quote=True)
    return (
        f'<span class="hhs-footer-alerts-control"{hidden_attribute}>'
        '<span class="hhs-footer-glyph"></span>'
        f'<details class="hhs-footer-alerts-menu hhs-footer-alerts-menu--{alerts_kind}">'
        '<summary class="hhs-footer-alerts-trigger" '
        'title="Show today\'s alerts" aria-label="Show today\'s warnings and errors">'
        f'<span class="hhs-footer-glyph-button">'
        f"{footer_alert_glyph(alerts_kind)}</span></summary>"
        '<div class="hhs-footer-alerts-panel">'
        f"{footer_alert_items_markup(alerts)}"
        '<div class="hhs-footer-alerts-actions">'
        f'<button type="button" data-param="{view_param}" '
        'title="Open the complete alerts file">View</button>'
        f'<button type="button" data-param="{clear_param}" '
        'title="Clear the alerts file">Clear</button>'
        '</div></div></details></span>'
    )


def render_footer_alerts_menu_script() -> None:
    """Manage the native footer alert list and its View and Clear actions."""
    render_script_html(
        """
        <script>
          (() => {
            const doc = window.parent.document;
            const panel = doc.querySelector(".hhs-footer-alerts-panel");
            if (!panel) {
              return;
            }
            const menu = panel.closest(".hhs-footer-alerts-menu");
            const closeMenu = () => menu?.removeAttribute("open");
            const formatter = new Intl.DateTimeFormat(undefined, {
              dateStyle: "short",
            });
            doc.querySelectorAll("[data-hhs-local-date]").forEach((element) => {
              const timestamp = new Date(element.dataset.hhsLocalDate || "");
              if (!Number.isNaN(timestamp.getTime())) {
                element.textContent = formatter.format(timestamp);
              }
            });
            if (panel.dataset.handlersInstalled !== "true") {
              panel.dataset.handlersInstalled = "true";
              panel.querySelectorAll(".hhs-footer-alerts-actions button")
                .forEach((button) => {
                  button.addEventListener("click", () => {
                    const params = new URLSearchParams(
                      window.parent.location.search
                    );
                    params.set(button.dataset.param, "1");
                    window.parent.location.search = params.toString();
                  });
                });
              menu?.addEventListener("toggle", () => {
                if (!menu.open) {
                  return;
                }
                doc.querySelectorAll(
                  ".hhs-footer-cache-clear-menu[open], "
                  + ".hhs-footer-terminal-ai-menu[open]"
                ).forEach((otherMenu) => otherMenu.removeAttribute("open"));
              });
            }
            if (window.parent.__hhsFooterAlertsOutsideHandler) {
              doc.removeEventListener(
                "pointerdown",
                window.parent.__hhsFooterAlertsOutsideHandler,
                true
              );
            }
            const outsideHandler = (event) => {
              if (menu?.open && !menu.contains(event.target)) {
                closeMenu();
              }
            };
            window.parent.__hhsFooterAlertsOutsideHandler = outsideHandler;
            doc.addEventListener("pointerdown", outsideHandler, true);
          })();
        </script>
        """,
        height=0,
        width=0,
    )


def open_footer_alerts_file() -> None:
    """Open the local footer alerts cache file with the configured system opener."""
    alert_path = footer_alerts_file()
    try:
        alert_path.parent.mkdir(parents=True, exist_ok=True)
        alert_path.touch(exist_ok=True)
    except OSError as error:
        push_floating_status(f"Unable to open alerts file: {error}", "error")
        return
    result = run_bash_command(
        open_file(str(alert_path)),
        "Opening alerts file...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        cache_tag="system",
        show_overlay=False,
    )
    if result.returncode != 0:
        push_floating_status(
            result.stderr or "Unable to open alerts file.", "error"
        )


def clear_footer_alerts_file() -> None:
    """Wipe the footer alerts cache file while preserving the file itself."""
    if clear_footer_alerts():
        push_floating_status("Cleared footer alerts.", "info")
        return
    push_floating_status("Unable to clear footer alerts.", "error")


def render_footer() -> None:
    """Render the HomeSetup UI footer."""
    version = homesetup_version()
    working_dir = html.escape(footer_working_directory())
    repository_url = html.escape(os.environ.get("HHS_GITHUB_URL", "#"), quote=True)
    connected_to_ssh = bool(connected_ssh_host())
    working_dir_url = f"?{hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM}=1"
    working_dir_attrs = ""
    if not connected_to_ssh:
        working_dir_open_url = html.escape(
            open_working_directory_endpoint_url(), quote=True
        )
        working_dir_attrs = (
            f' data-open-working-dir-url="{working_dir_open_url}" role="button"'
        )
    update_url = f"?{hhs_ui.FOOTER_RUN_UPDATER_QUERY_PARAM}=1"
    shell_version_url = f"?{hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM}=1"
    alerts = today_footer_alerts()
    alerts_markup = footer_alerts_menu_markup(alerts)
    updater_markup = ""
    if bool(st.session_state.get("updater_update_available", False)):
        updater_markup = (
            f'<a class="hhs-footer-update-link" href="{update_url}" target="_self" '
            'title="Update HomeSetup" aria-label="Update HomeSetup"></a>'
        )
    shell_name = html.escape(os.environ.get("HHS_MY_SHELL", "").strip().upper())
    shell_status_markup = ""
    cache_clear_markup = ""
    terminal_ai_markup = ""
    terminal_ai_enabled = terminal_document_view_is_active()
    if shell_name:
        shell_status_markup = (
            f'<a class="hhs-footer-shell-status" href="{shell_version_url}" '
            f'target="_self" title="Show shell version" aria-label="Show shell version">'
            f'<span class="hhs-footer-glyph"></span>'
            f'<span class="hhs-footer-shell-name">{shell_name}</span></a>'
        )
        cache_clear_markup = (
            f'<span class="hhs-footer-glyph"></span>'
            f"{footer_cache_clear_menu_markup()}"
        )
        terminal_ai_markup = (
            f'<span class="hhs-footer-glyph"></span>'
            f"{footer_terminal_ai_menu_markup(terminal_ai_enabled)}"
        )
    connected_host = str(st.session_state.get("ssh_connection_host", "")).strip()
    remote_status_markup = ""
    if (
        str(st.session_state.get("ssh_connection_status", "")).strip() == "connected"
        and connected_host
    ):
        connected_host_display = html.escape(ssh_connection_display(connected_host))
        remote_status_markup = (
            f'<span class="hhs-footer-remote-status">'
            f'<span class="hhs-footer-glyph"></span>'
            f"<span>Connected to remote  {connected_host_display}</span></span>"
        )
    shell_controls_markup = (
        f'<span class="hhs-footer-shell-group">'
        f"{shell_status_markup}{cache_clear_markup}{terminal_ai_markup}"
        f"{alerts_markup}</span>"
    )
    status_group_markup = (
        f'<span class="hhs-footer-status-group">'
        f"{remote_status_markup}{shell_controls_markup}"
        f"</span>"
    )
    logo_data_uri = load_app_image_data_uri(
        hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"
    )
    st.html(f"""
        <footer class="hhs-app-footer">
          <a class="hhs-footer-logo-link" href="{repository_url}" target="_blank" rel="noopener noreferrer" title="Open the HomeSetup repository" aria-label="HomeSetup repository">
            <img class="hhs-footer-logo" src="{logo_data_uri}" alt="" aria-hidden="true">
          </a>
          <span class="hhs-footer-version-group">
            <a class="hhs-footer-link hhs-footer-repository-link" href="{repository_url}" target="_blank" rel="noopener noreferrer" title="Open the HomeSetup repository">HomeSetup - v{version}</a>{updater_markup}
          </span>
          <span class="hhs-footer-glyph"></span>
          <a class="hhs-footer-link hhs-footer-working-dir-link"
             href="{working_dir_url}"
             target="_self" title="Open the working directory"{working_dir_attrs}>Working dir: <span class="hhs-footer-working-dir-value">{working_dir}</span></a>
          {status_group_markup}
        </footer>
        """)
    if not connected_to_ssh:
        render_footer_working_directory_open_script()
    render_footer_alerts_menu_script()
    if shell_name:
        render_footer_cache_clear_menu_script()
        if terminal_ai_enabled:
            render_footer_terminal_ai_menu_script()


def render_footer_status_fragment() -> None:
    """Poll updater/status state and render the footer status area."""
    execute_due_updater_check()
    drain_footer_status_log_records()
    render_footer()
    render_floating_status()


def query_param_requested(name: str) -> bool:
    """Return whether a Streamlit query parameter was requested."""
    value = st.query_params.get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).lower() in {"1", "true", "yes"}


def query_param_value(name: str) -> str:
    """Return a Streamlit query parameter value as text."""
    value = st.query_params.get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "")


def remove_query_param(name: str) -> None:
    """Remove a Streamlit query parameter if it exists."""
    if name in st.query_params:
        del st.query_params[name]


def clear_footer_shell_version_dialog() -> None:
    """Clear the footer shell version dialog state."""
    st.session_state["footer_shell_version_dialog_title"] = ""
    st.session_state["footer_shell_version_output"] = ""


def shell_version_output_html(output: str) -> str:
    """Return shell version output escaped with visible HTML line breaks."""
    escaped_output = html.escape(output)
    return re.sub(r"\r\n|\n|\r", "<br>", escaped_output)


def render_footer_shell_version_dialog() -> bool:
    """Render the footer shell version dialog when requested."""
    title = str(st.session_state.get("footer_shell_version_dialog_title", "")).strip()
    if not title:
        return False

    def render_body() -> None:
        """Render the shell version command output inside the dialog."""
        output = str(st.session_state.get("footer_shell_version_output", "")).strip()
        render_terminal_output(
            shell_version_output_html(output or "No output."),
            css_classes="hhs-shell-version-output",
            content_is_html=True,
        )

    return pop_dialog(
        title=title,
        buttons=(
            {
                "label": "Close",
                "key": "footer_shell_version_dialog_close_button",
            },
        ),
        body=render_body,
        close_callback=clear_footer_shell_version_dialog,
    )


def clear_application_state_data() -> None:
    """Delete persisted UI state and remove persistable selections from this session."""
    for state_file in ui_state_files():
        try:
            state_file.unlink(missing_ok=True)
        except OSError as error:
            push_floating_status(
                f"Unable to clear application states: {error}", "error"
            )
    for state_key in list(st.session_state):
        if is_persisted_ui_key(str(state_key)):
            st.session_state.pop(state_key, None)


def selected_footer_cleanup_labels(
    clear_application_cache: bool,
    clear_application_states: bool,
    clear_ai_history: bool,
) -> list[str]:
    """Return the selected footer cleanup labels."""
    labels = []
    if clear_application_cache:
        labels.append("application cache")
    if clear_application_states:
        labels.append("application states")
    if clear_ai_history:
        labels.append("AI history")
    return labels


def apply_footer_cache_clear_options(
    clear_application_cache: bool,
    clear_application_states: bool,
    clear_ai_history: bool,
) -> None:
    """Apply selected footer cleanup actions."""
    labels = selected_footer_cleanup_labels(
        clear_application_cache,
        clear_application_states,
        clear_ai_history,
    )
    if not labels:
        push_floating_status("No cleanup option selected.", "warn")
        return

    completed_labels = []
    if clear_application_cache:
        clear_cached_ui_data_preserving_state(show_status=False)
        completed_labels.append("application cache")
    if clear_ai_history:
        clear_ai_chat_history()
    if clear_application_states:
        clear_application_state_data()
        completed_labels.append("application states")

    if clear_ai_history and completed_labels:
        push_floating_status(
            f"Cleared {', '.join(completed_labels)}. AI history clear queued.",
            "info",
        )
    elif clear_ai_history:
        push_floating_status("AI history clear queued.", "info")
    else:
        push_floating_status(f"Cleared {', '.join(completed_labels)}.", "info")


def remove_footer_cache_clear_query_params() -> None:
    """Remove footer cache clear query parameters from the browser URL."""
    clear_param_names = {
        hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM,
    }
    remaining_params = {
        name: st.query_params.get_all(name)
        for name in st.query_params
        if name not in clear_param_names
    }
    st.query_params.from_dict(remaining_params)


def handle_command_preloader_cancel_action() -> None:
    """Cancel a background command requested by the overlay close button."""
    preloader_token = query_param_value(hhs_ui.COMMAND_PRELOADER_CANCEL_QUERY_PARAM)
    if not preloader_token:
        return
    remove_query_param(hhs_ui.COMMAND_PRELOADER_CANCEL_QUERY_PARAM)
    if stop_background_job_by_preloader_token(preloader_token):
        push_floating_status("Command interrupted.", "warn")


def handle_footer_actions() -> None:
    """Run footer actions requested through Streamlit query parameters."""
    handle_command_preloader_cancel_action()
    updater_completed = background_job_result(UPDATER_UPDATE_JOB)
    if updater_completed is not None:
        result, metadata = updater_completed
        updater_context = str(metadata.get("updater_context", "local"))
        output = strip_ansi(result.stdout or result.stderr or "").strip()
        if result.returncode != 0:
            message = output or "Unable to update HomeSetup."
            push_floating_status(message, "error")
            st.error(message)
        else:
            if updater_context == "local":
                st.session_state["updater_last_check_output"] = (
                    output or "HomeSetup update command completed."
                )
            st.session_state["updater_update_available"] = False
            st.session_state["updater_check_context"] = updater_context
            st.session_state["updater_remote_checked_context"] = updater_context
            cache_delete_tag("env")
            cache_delete_tag(FOOTER_VERSION_CACHE_TAG)
            st.session_state["footer_hhs_version_cache_loaded"] = False
            save_ui_state()
            push_floating_status("HomeSetup update command completed.", "info")

    if query_param_requested(hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM)
        clear_footer_shell_version_dialog()
        result = run_shell_version()
        output = strip_ansi(result.stdout or result.stderr or "").strip()
        st.session_state["footer_shell_version_output"] = (
            output or "bash --version returned no output."
        )
        st.session_state["footer_shell_version_dialog_title"] = "Shell version"

    if query_param_requested(hhs_ui.FOOTER_VIEW_ALERTS_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_VIEW_ALERTS_QUERY_PARAM)
        open_footer_alerts_file()

    if query_param_requested(hhs_ui.FOOTER_CLEAR_ALERTS_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_CLEAR_ALERTS_QUERY_PARAM)
        clear_footer_alerts_file()

    if query_param_requested(hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM):
        clear_application_cache = query_param_requested(
            hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM
        )
        clear_application_states = query_param_requested(
            hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM
        )
        clear_ai_history = query_param_requested(
            hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM
        )
        remove_footer_cache_clear_query_params()
        apply_footer_cache_clear_options(
            clear_application_cache,
            clear_application_states,
            clear_ai_history,
        )

    if query_param_requested(hhs_ui.FOOTER_RUN_UPDATER_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_RUN_UPDATER_QUERY_PARAM)
        if background_job_is_running(UPDATER_UPDATE_JOB):
            push_floating_status("HomeSetup update is already running.", "warn")
        else:
            start_background_bash_command(
                UPDATER_UPDATE_JOB,
                build_hhs_updater_command("update"),
                "Updating HomeSetup",
                600,
                force_local=not bool(connected_ssh_host()),
                metadata={"updater_context": updater_check_context()},
                show_preloader_event=True,
            )
            push_floating_status("HomeSetup update started.", "info")

    if query_param_requested(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM)
        open_footer_working_directory()

    search_result_path = query_param_value(hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM)
    if search_result_path:
        remove_query_param(hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM)
        open_search_result_path(search_result_path)


def run_open_working_directory(directory: str) -> subprocess.CompletedProcess[str]:
    """Open a local working directory through HomeSetup."""
    return run_bash_command(
        open_file(directory),
        "Opening working directory...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="system",
    )


def open_footer_working_directory() -> None:
    """Open the footer working directory locally or in the remote SSH explorer."""
    working_dir = footer_working_directory()
    if connected_ssh_host():
        st.session_state["active_view"] = hhs_ui.SSH_VIEW
        st.session_state["ssh_view"] = "FILES"
        open_remote_explorer_path(working_dir)
        push_floating_status("Opened remote working directory in SSH Explorer.", "info")
        return

    result = run_open_working_directory(working_dir)
    if result.returncode != 0:
        message = result.stderr or "Unable to open working directory."
        push_floating_status(message, "error")
        st.error(message)
    else:
        push_floating_status("Opened working directory.", "info")


def run_shell_version() -> subprocess.CompletedProcess[str]:
    """Run the active host Bash version command used by the footer shell status."""
    return run_bash_command(
        shell_version_command(),
        "Checking shell version...",
        ttl_seconds=0,
        use_cache=False,
        timeout_seconds=10,
        cache_tag="system",
    )


def parse_footer_working_directory_output(output: str) -> str:
    """Return the marked working directory from noisy local or remote shell output."""
    clean_output = strip_ansi(output or "").replace("\r", "")
    marker = "__HHS_UI_PWD__"
    marker_index = clean_output.rfind(marker)
    if marker_index < 0:
        return ""
    marker_output = clean_output[marker_index + len(marker) :]
    return marker_output.splitlines()[0].strip()


def update_remote_footer_working_directory() -> None:
    """Start a background refresh of the connected SSH host working directory."""
    complete_remote_footer_working_directory_refresh()
    if not connected_ssh_host():
        st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)
        return
    if background_job_is_running(FOOTER_WORKING_DIR_JOB):
        return
    start_background_bash_command(
        FOOTER_WORKING_DIR_JOB,
        build_footer_working_directory_command(),
        "Loading remote working dir",
        10,
    )


def complete_remote_footer_working_directory_refresh() -> None:
    """Store a completed remote footer working-directory refresh."""
    completed = background_job_result(FOOTER_WORKING_DIR_JOB)
    if completed is None:
        return
    result, _metadata = completed
    output = parse_footer_working_directory_output(result.stdout or "")
    if result.returncode == 0 and output:
        st.session_state[hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY] = output
        return
    st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)


def footer_working_directory() -> str:
    """Return the footer working directory from state or the local process cwd."""
    sync_ttyd_event_state()
    try:
        complete_remote_footer_working_directory_refresh()
    except NameError:
        pass
    if str(st.session_state.get("ssh_connection_status", "")).strip() == "connected":
        remote_cwd = str(
            st.session_state.get(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, "")
        ).strip()
        if remote_cwd:
            return remote_cwd
    else:
        local_cwd = str(
            st.session_state.get(hhs_ui_constants.FOOTER_LOCAL_WORKING_DIR_KEY, "")
        ).strip()
        if local_cwd:
            return local_cwd
    return os.getcwd()
