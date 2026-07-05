#!/usr/bin/env python3
"""Streamlit UI draft for HomeSetup.

Script:
    streamlit_ui.py
Purpose:
    HomeSetup application UI.
Created:
    Jun 25, 2026
Author:
    Hugo Saporetti Junior
Mailto:
    taius.hhs@gmail.com
License:
    Please refer to <https://opensource.org/licenses/MIT>
Copyright:
    Copyright (c) 2026, HomeSetup team
"""

from __future__ import annotations

import csv
import atexit
import hashlib
import html
import importlib
import json
import os
import posixpath
import re
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypeVar

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit import config as st_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hhs_ui
import hhs_ui.constants as hhs_ui_constants

hhs_ui_constants = importlib.reload(hhs_ui_constants)
hhs_ui = importlib.reload(hhs_ui)

PROCESS_RESOURCE_STATE_KEY = "_hhs_ui_process_resource_state"


def process_resource_state() -> dict[str, object]:
    """Return process-wide resources that must survive Streamlit reruns."""
    state = getattr(sys, PROCESS_RESOURCE_STATE_KEY, None)
    if not isinstance(state, dict):
        state = {}
        setattr(sys, PROCESS_RESOURCE_STATE_KEY, state)
    return state


def process_resource_registry(key: str) -> dict:
    """Return a process-wide mutable registry by key."""
    state = process_resource_state()
    registry = state.get(key)
    if not isinstance(registry, dict):
        registry = {}
        state[key] = registry
    return registry


TTYD_CLEANUP_REGISTRY: dict[str, dict[str, object]] = process_resource_registry(
    "ttyd_cleanup_registry"
)
TTYD_EVENT_REGISTRY: dict[str, list[dict[str, object]]] = process_resource_registry(
    "ttyd_event_registry"
)
_PROCESS_RESOURCE_STATE = process_resource_state()
_PROCESS_TTYD_CLEANUP_SERVER = _PROCESS_RESOURCE_STATE.get("ttyd_cleanup_server")
TTYD_CLEANUP_SERVER: ThreadingHTTPServer | None = (
    _PROCESS_TTYD_CLEANUP_SERVER
    if isinstance(_PROCESS_TTYD_CLEANUP_SERVER, ThreadingHTTPServer)
    else None
)
TTYD_CLEANUP_SERVER_PORT = (
    int(_PROCESS_RESOURCE_STATE.get("ttyd_cleanup_server_port") or 0)
    if TTYD_CLEANUP_SERVER is not None
    else 0
)
TTYD_EXIT_COMMANDS = {"exit", "logout"}


def resolve_run_shell() -> str:
    """Return the Bash executable used for all HomeSetup UI commands."""
    run_shell = ""
    brew_commands = (
        ["brew", "--prefix", "bash"],
        ["/opt/homebrew/bin/brew", "--prefix", "bash"],
        ["/usr/local/bin/brew", "--prefix", "bash"],
    )
    for brew_command in brew_commands:
        try:
            brew_result = subprocess.run(
                brew_command,
                capture_output=True,
                check=False,
                text=True,
                timeout=5,
            )
            if brew_result.returncode == 0:
                run_shell = brew_result.stdout.strip()
                break
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue

    candidates = []
    if run_shell:
        candidates.extend((Path(run_shell) / "bin" / "bash", Path(run_shell)))
    candidates.extend(
        (
            Path("/opt/homebrew/opt/bash/bin/bash"),
            Path("/usr/local/opt/bash/bin/bash"),
            Path("/bin/bash"),
        )
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return "/bin/bash"


def shell_version_command() -> str:
    """Return the command that prints the active target Bash version."""
    return r"${BASH:-bash} --version"


RUN_SHELL = resolve_run_shell()
os.environ[hhs_ui_constants.RUN_SHELL_ENV_KEY] = RUN_SHELL
SHOPT_DESCRIPTIONS = {
    "assoc_expand_once": "Suppresses repeated evaluation of associative array subscripts.",
    "autocd": "Runs a directory name as if it were the argument to cd.",
    "cdable_vars": "Treats a non-directory cd argument as a variable containing the target directory.",
    "cdspell": "Corrects minor spelling errors in directory names used with cd.",
    "checkhash": "Verifies hashed commands still exist before executing them.",
    "checkjobs": "Checks for stopped and running jobs before an interactive shell exits.",
    "checkwinsize": "Updates LINES and COLUMNS after each command when the terminal size changes.",
    "cmdhist": "Stores all lines of a multi-line command in one history entry.",
    "compat31": "Uses Bash 3.1 compatibility for quoted =~ conditional arguments.",
    "compat32": "Uses Bash 3.2 compatibility for conditional and locale-specific behavior.",
    "compat40": "Uses Bash 4.0 compatibility for conditional and locale-specific behavior.",
    "compat41": "Uses Bash 4.1 compatibility for conditional and POSIX mode behavior.",
    "compat42": "Uses Bash 4.2 compatibility for pattern replacement quote handling.",
    "compat43": "Uses Bash 4.3 compatibility for word expansion and loop state behavior.",
    "compat44": "Uses Bash 4.4 compatibility for expansion and unset behavior.",
    "complete_fullquote": "Quotes all shell metacharacters in completion results.",
    "direxpand": "Expands directory names during completion.",
    "dirspell": "Corrects directory name spelling during completion.",
    "dotglob": "Includes filenames beginning with a dot in pathname expansion.",
    "execfail": "Prevents a non-interactive shell from exiting when exec cannot run its target.",
    "expand_aliases": "Expands aliases before command execution.",
    "extdebug": "Enables debugger-oriented shell behavior and tracing.",
    "extglob": "Enables extended pathname pattern matching operators.",
    "extquote": "Enables ANSI-C and locale-specific quoting inside parameter expansions.",
    "failglob": "Makes non-matching pathname patterns raise an expansion error.",
    "force_fignore": "Applies FIGNORE suffixes even when they are the only completion matches.",
    "globasciiranges": "Uses ASCII ordering for bracket expression ranges in pattern matching.",
    "globstar": "Makes ** recursively match files and directories during pathname expansion.",
    "gnu_errfmt": "Formats shell error messages in GNU style.",
    "histappend": "Appends history to HISTFILE instead of overwriting it on shell exit.",
    "histreedit": "Lets readline re-edit a failed history substitution.",
    "histverify": "Loads history substitutions into readline before execution for review.",
    "hostcomplete": "Completes hostnames when a word containing @ is completed.",
    "huponexit": "Sends SIGHUP to jobs when an interactive login shell exits.",
    "inherit_errexit": "Preserves errexit in command substitutions.",
    "interactive_comments": "Allows # to begin comments in interactive shells.",
    "lastpipe": "Runs the last foreground pipeline command in the current shell when possible.",
    "lithist": "Stores multi-line history entries with embedded newlines when cmdhist is enabled.",
    "localvar_inherit": "Lets local variables inherit prior visible values and attributes.",
    "localvar_unset": "Makes unset local variables hide same-named outer variables.",
    "login_shell": "Indicates that the shell was started as a login shell.",
    "mailwarn": "Warns when a checked mail file has been read since the last check.",
    "no_empty_cmd_completion": "Skips PATH completion attempts on an empty command line.",
    "nocaseglob": "Matches filenames case-insensitively during pathname expansion.",
    "nocasematch": "Matches case and [[ patterns case-insensitively.",
    "noexpand_translation": "Prevents translated strings from being single-quoted.",
    "nullglob": "Expands non-matching pathname patterns to nothing.",
    "progcomp": "Enables programmable completion.",
    "progcomp_alias": "Tries programmable completion through an alias target.",
    "promptvars": "Expands variables and command substitutions in prompt strings.",
    "restricted_shell": "Indicates that the shell is running in restricted mode.",
    "shift_verbose": "Reports an error when shift exceeds the number of positional parameters.",
    "sourcepath": "Uses PATH to find files passed to source or dot.",
    "varredir_close": "Automatically closes file descriptors opened with varredir redirections.",
    "xpg_echo": "Makes echo expand backslash escape sequences by default.",
}
TableControlsResult = TypeVar("TableControlsResult")
UI_CACHE_MEMORY: dict[str, dict[str, object]] = {}
UI_CACHE_MEMORY_MTIME: float | None = None
HOME_TOOL_ACTION_JOB = "home_tool_action"
ALIAS_LIST_JOB = "alias_list"
SERVICE_LIST_JOB = "service_list"
SERVICE_ACTION_JOB = "service_action"
MONITOR_CPU_JOB = "monitor_cpu"
MONITOR_MEM_JOB = "monitor_mem"
MONITOR_PROCESS_LIST_JOB = "monitor_process_list"
AI_MODEL_SELECT_JOB = "ai_model_select"
AI_MODEL_DELETE_JOB = "ai_model_delete"
UPDATER_UPDATE_JOB = "updater_update"
UPDATER_CHECK_JOB = "updater_check"
AI_ASK_JOB = "ai_ask"
FOOTER_VERSION_JOB = "footer_hhs_version"
FOOTER_WORKING_DIR_JOB = "footer_working_dir"
SSH_CONNECT_JOB = "ssh_connect"
SSH_DISCONNECT_JOB = "ssh_disconnect"
SSH_FILE_TRANSFER_JOB = "ssh_file_transfer"
HOST_SWITCH_CACHE_TAGS = (
    "env",
    "services",
    "monitor_disk",
    "monitor_process",
    "ssh_files",
)
HOST_SWITCH_BACKGROUND_JOBS = (
    SSH_CONNECT_JOB,
    SSH_DISCONNECT_JOB,
    SSH_FILE_TRANSFER_JOB,
    SERVICE_LIST_JOB,
    SERVICE_ACTION_JOB,
    MONITOR_CPU_JOB,
    MONITOR_MEM_JOB,
    MONITOR_PROCESS_LIST_JOB,
)
CACHE_CLEAR_BACKGROUND_JOBS = (
    SSH_CONNECT_JOB,
    SSH_DISCONNECT_JOB,
    SSH_FILE_TRANSFER_JOB,
    FOOTER_VERSION_JOB,
    ALIAS_LIST_JOB,
    SERVICE_LIST_JOB,
    MONITOR_CPU_JOB,
    MONITOR_MEM_JOB,
    MONITOR_PROCESS_LIST_JOB,
)
HOST_SWITCH_STATE_KEYS = (
    "monitor_cpu_error",
    "monitor_mem_error",
    "monitor_process_action_message",
    "monitor_process_action_succeeded",
    "monitor_process_list_error",
    "service_list_error",
)


def file_mtime_token(file_path: Path) -> float:
    """Return a cache token that changes when a filesystem asset changes."""
    try:
        return file_path.stat().st_mtime
    except OSError:
        return 0.0


@lru_cache(maxsize=128)
def cached_text_file(file_path: str, mtime_token: float) -> str:
    """Return a UTF-8 text file body cached by path and modification time."""
    del mtime_token
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return ""


def load_text_file(file_path: Path) -> str:
    """Load a UTF-8 text file through the static asset cache."""
    return cached_text_file(str(file_path), file_mtime_token(file_path))


@lru_cache(maxsize=64)
def cached_data_uri(file_path: str, mime_type: str, mtime_token: float) -> str:
    """Return a browser data URI cached by path, MIME type, and modification time."""
    del mtime_token
    try:
        encoded_data = b64encode(Path(file_path).read_bytes()).decode("ascii")
    except OSError:
        encoded_data = ""
    return f"data:{mime_type};base64,{encoded_data}"


def load_data_uri(file_path: Path, mime_type: str) -> str:
    """Load a binary file as a browser data URI through the static asset cache."""
    return cached_data_uri(str(file_path), mime_type, file_mtime_token(file_path))


def load_app_css() -> str:
    """Load the HomeSetup Streamlit UI stylesheet."""
    return load_text_file(hhs_ui.APP_CSS_FILE)


def available_theme_options() -> tuple[str, ...]:
    """Return all selectable theme names from the themes folder."""
    return tuple(
        sorted(theme.stem for theme in hhs_ui.APP_THEME_CSS_FILE.parent.glob("*.css"))
    )


def default_theme_name(theme_options: tuple[str, ...] | None = None) -> str:
    """Return the default selectable HomeSetup UI theme name."""
    options = theme_options if theme_options is not None else available_theme_options()
    if hhs_ui.APP_THEME_CSS_FILE.stem in options:
        return hhs_ui.APP_THEME_CSS_FILE.stem
    return options[0] if options else ""


def validated_theme_name(
    theme_name: object, theme_options: tuple[str, ...] | None = None
) -> str:
    """Return a valid selectable theme name or an empty string."""
    selected_theme = str(theme_name or "").strip()
    options = theme_options if theme_options is not None else available_theme_options()
    return selected_theme if selected_theme in options else ""


def theme_css_file(theme_name: object) -> Path:
    """Return the stylesheet path for a selectable UI theme."""
    theme_options = available_theme_options()
    selected_theme = validated_theme_name(theme_name, theme_options)
    if not selected_theme:
        selected_theme = default_theme_name(theme_options)
    theme_file = hhs_ui.APP_THEME_CSS_FILE.with_name(f"{selected_theme}.css")
    if not theme_file.is_file():
        return hhs_ui.APP_THEME_CSS_FILE
    return theme_file


def css_custom_properties(css_source: str) -> dict[str, str]:
    """Return CSS custom property values from a stylesheet source string."""
    properties: dict[str, str] = {}
    for property_name, property_value in re.findall(
        r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);", css_source
    ):
        properties[property_name] = property_value.strip()
    return properties


@lru_cache(maxsize=32)
def cached_css_custom_properties(css_source: str) -> dict[str, str]:
    """Return parsed CSS custom properties cached by stylesheet source."""
    return css_custom_properties(css_source)


def theme_custom_properties(theme_name: object) -> dict[str, str]:
    """Return parsed CSS custom properties for a selectable UI theme."""
    return cached_css_custom_properties(load_text_file(theme_css_file(theme_name)))


def css_theme_bool(value: str) -> bool | str:
    """Return a boolean value for CSS boolean tokens or the original string."""
    normalized_value = value.strip().lower()
    if normalized_value == "true":
        return True
    if normalized_value == "false":
        return False
    return value


def theme_config_options(theme_name: object) -> dict[str, object]:
    """Return Streamlit native theme options parsed from a selectable CSS theme."""
    theme_properties = theme_custom_properties(theme_name)
    option_tokens = {
        "theme.base": "hhs-theme-base",
        "theme.primaryColor": "hhs-theme-primary-color",
        "theme.backgroundColor": "hhs-theme-background-color",
        "theme.secondaryBackgroundColor": "hhs-theme-secondary-background-color",
        "theme.textColor": "hhs-theme-text-color",
        "theme.linkColor": "hhs-theme-link-color",
        "theme.borderColor": "hhs-theme-border-color",
        "theme.dataframeBorderColor": "hhs-theme-dataframe-border-color",
        "theme.dataframeHeaderBackgroundColor": (
            "hhs-theme-dataframe-header-background-color"
        ),
        "theme.codeBackgroundColor": "hhs-theme-code-background-color",
        "theme.baseRadius": "hhs-theme-base-radius",
        "theme.buttonRadius": "hhs-theme-button-radius",
        "theme.showWidgetBorder": "hhs-theme-show-widget-border",
        "theme.showSidebarBorder": "hhs-theme-show-sidebar-border",
    }
    return {
        option_name: css_theme_bool(theme_properties[token_name])
        for option_name, token_name in option_tokens.items()
        if token_name in theme_properties
    }


def load_app_theme_css() -> str:
    """Load the selected HomeSetup Streamlit UI theme stylesheet."""
    selected_theme = st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    return load_text_file(theme_css_file(selected_theme))


def persist_theme_selection(theme_name: str) -> None:
    """Persist the selected theme directly into the UI state file."""
    selected_theme = validated_theme_name(theme_name)
    if not selected_theme:
        return
    if st.session_state.get(hhs_ui.THEME_SELECTED_KEY) != selected_theme:
        st.session_state[hhs_ui.THEME_SELECTED_KEY] = selected_theme
    data = load_ui_state()
    data[hhs_ui.THEME_SELECTED_KEY] = selected_theme
    hhs_ui.UI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    hhs_ui.UI_STATE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def request_theme_reload() -> None:
    """Persist the selected theme and schedule the theme loading overlay."""
    selected_theme = validated_theme_name(
        st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    )
    if selected_theme:
        persist_theme_selection(selected_theme)
        st.session_state["theme_reload_pending"] = True
        st.session_state["theme_reload_name"] = selected_theme


def load_app_font_data_uri() -> str:
    """Load the HomeSetup UI font as a browser-embeddable data URI."""
    return load_data_uri(hhs_ui.APP_FONT_FILE, "font/woff2")


def load_app_image_data_uri(image_file: Path, mime_type: str) -> str:
    """Load a HomeSetup UI image as a browser-embeddable data URI."""
    return load_data_uri(image_file, mime_type)


def load_app_font_face_css() -> str:
    """Load the HomeSetup UI font as an embeddable CSS font face."""
    return (
        "@font-face {"
        f'font-family: "{hhs_ui.APP_FONT_FAMILY}";'
        f'src: url("{load_app_font_data_uri()}") format("woff2");'
        "font-style: normal;"
        "font-weight: 400;"
        "font-display: swap;"
        "}"
    )


def configure_app_font_theme(theme_name: object = "") -> None:
    """Configure Streamlit's selected theme for native components."""
    for option_name, option_value in theme_config_options(theme_name).items():
        st_config.set_option(option_name, option_value)
    st_config.set_option(
        "theme.fontFaces",
        [
            {
                "family": hhs_ui.APP_FONT_FAMILY,
                "url": load_app_font_data_uri(),
                "weight": "400",
                "style": "normal",
            }
        ],
    )
    st_config.set_option("theme.font", hhs_ui.APP_FONT_FAMILY)
    st_config.set_option("theme.headingFont", hhs_ui.APP_FONT_FAMILY)
    st_config.set_option("theme.codeFont", hhs_ui.APP_FONT_FAMILY)


def render_styles() -> None:
    """Render app-level Streamlit styles."""
    st.markdown(
        (
            "<style>"
            f"{load_app_font_face_css()}"
            f"{hhs_ui.APP_CSS}"
            f"{load_app_css()}"
            f"{load_app_theme_css()}"
            "</style>"
        ),
        unsafe_allow_html=True,
    )


def format_datetime(value: datetime) -> str:
    """Format a datetime value for the HomeSetup UI."""
    return value.strftime(hhs_ui.DISPLAY_DATETIME_FORMAT)


def render_sidebar_clock() -> None:
    """Render the current datetime above the sidebar title."""
    current_date = html.escape(format_datetime(datetime.now()))
    st.markdown(
        f"""
        <div class="hhs-sidebar-clock">
          <span class="hhs-sidebar-clock-glyph"></span>
          <span>{current_date}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_title() -> None:
    """Render the sidebar HomeSetup title with the app logo."""
    logo_data_uri = load_app_image_data_uri(
        hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"
    )
    st.markdown(
        f"""
        <div class="hhs-sidebar-title">
          <img class="hhs-sidebar-title-logo" src="{logo_data_uri}" alt="" aria-hidden="true">
          <span>HomeSetup - UI v{html.escape(hhs_ui.VERSION)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def document_details(document_key: str) -> tuple[str, Path]:
    """Return the display title and file path for a document key."""
    title, relative_path = hhs_ui.DOCUMENTS.get(
        document_key, hhs_ui.DOCUMENTS["README"]
    )
    return title, homesetup_home() / relative_path


def open_document_view(document_key: str) -> None:
    """Open a document view in the main content panel."""
    if terminal_document_view_is_active() and document_key != "TERMINAL":
        deactivate_terminal_document_view()
    st.session_state[hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] = st.session_state.get(
        "active_view", "Home"
    )
    st.session_state[hhs_ui.DOCUMENT_SELECTED_KEY] = document_key
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = True
    if document_key == "TERMINAL":
        activate_terminal_document_view()
    save_ui_state()


def activate_terminal_document_view() -> None:
    """Set Terminal cwd to the same working directory shown in the footer."""
    st.session_state[hhs_ui.TERMINAL_CWD_KEY] = footer_working_directory()


def clear_ttyd_exit_request() -> None:
    """Drop any pending ttyd exit request for the current browser session."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    entry = TTYD_CLEANUP_REGISTRY.get(token)
    if isinstance(entry, dict):
        entry.pop("exit_requested", None)


def deactivate_terminal_document_view() -> None:
    """Stop ttyd resources when leaving the Terminal document view."""
    clear_ttyd_exit_request()
    stop_ttyd_session()
    st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = False


def restore_terminal_document_view(was_terminal_active: bool) -> None:
    """Restore the Terminal document view after a host-scoped state reset."""
    if not was_terminal_active:
        return
    previous_view = st.session_state.get(
        hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY,
        st.session_state.get("active_view", "Home"),
    )
    if previous_view not in hhs_ui.VIEWS:
        previous_view = "Home"
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = True
    st.session_state[hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] = previous_view
    st.session_state[hhs_ui.DOCUMENT_SELECTED_KEY] = "TERMINAL"
    activate_terminal_document_view()


def reconnect_view_state_snapshot() -> dict[str, object]:
    """Return persisted view state that should survive automatic SSH reconnect."""
    keys = (
        "active_view",
        "ai_view",
        "config_view",
        hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY,
        hhs_ui.DOCUMENT_SELECTED_KEY,
        hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY,
        "history_view",
        "home_view",
        "monitor_view",
        "ssh_explorer_local_path",
        "ssh_explorer_remote_path",
        "ssh_tunnel_filter",
        "ssh_tunnel_other_filter",
        "ssh_view",
    )
    return {
        key: st.session_state[key]
        for key in keys
        if key in st.session_state
        and is_persistable_ui_value(st.session_state.get(key))
    }


def restore_reconnect_view_state(snapshot: dict[str, object]) -> None:
    """Restore persisted view state after an automatic SSH reconnect reset."""
    for key, value in snapshot.items():
        st.session_state[key] = value


def close_document_view() -> None:
    """Close the document view and restore the previous main view."""
    previous_view = st.session_state.get(hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY, "Home")
    if terminal_document_view_is_active():
        deactivate_terminal_document_view()
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = False
    if previous_view in hhs_ui.VIEWS:
        st.session_state["active_view"] = previous_view
    save_ui_state()


def render_terminal_back_button_cleanup_script() -> None:
    """Attach browser-side ttyd iframe cleanup to the document Back button."""
    components.html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            const cleanup = () => {
              if (parentWindow.__hhsTtydFrameSyncCleanup) {
                parentWindow.__hhsTtydFrameSyncCleanup();
                parentWindow.__hhsTtydFrameSyncCleanup = null;
              }
              if (parentWindow.__hhsTtydExitBackHandler) {
                parentWindow.removeEventListener("message", parentWindow.__hhsTtydExitBackHandler);
                parentWindow.__hhsTtydExitBackHandler = null;
              }
              const frame = doc.getElementById("hhs-persistent-ttyd-frame");
              if (frame) {
                frame.remove();
              }
            };
            const triggerBack = () => {
              cleanup();
              const backButton = doc.querySelector(".st-key-document_back_button button");
              if (!backButton || backButton.dataset.hhsTtydBackRequested === "true") {
                return;
              }
              backButton.dataset.hhsTtydBackRequested = "true";
              backButton.click();
            };
            const previousHandler = parentWindow.__hhsTtydExitBackHandler;
            if (previousHandler) {
              parentWindow.removeEventListener("message", previousHandler);
            }
            const messageHandler = (event) => {
              const terminalFrame = doc.getElementById("hhs-persistent-ttyd-frame");
              if (terminalFrame && event.source !== terminalFrame.contentWindow) {
                return;
              }
              const data = event.data || {};
              const terminalEvent = data.event || {};
              if (data.type !== "hhs-ttyd-event" || terminalEvent.type !== "exit") {
                return;
              }
              triggerBack();
            };
            parentWindow.__hhsTtydExitBackHandler = messageHandler;
            parentWindow.addEventListener("message", messageHandler);
            const button = doc.querySelector(".st-key-document_back_button button");
            if (!button || button.dataset.hhsTtydCleanupAttached === "true") {
              return;
            }
            button.dataset.hhsTtydCleanupAttached = "true";
            button.addEventListener("click", cleanup, { capture: true });
          })();
        </script>
        """,
        height=1,
        width=1,
    )


def render_sidebar_terminal_button() -> None:
    """Render the sidebar shortcut that opens the Terminal view."""
    if terminal_document_view_is_active():
        return
    st.button(
        " Terminal",
        key="terminal_open_button",
        on_click=open_document_view,
        args=("TERMINAL",),
        width="stretch",
    )


def terminal_document_view_is_active() -> bool:
    """Return whether the Terminal document view is currently active."""
    return bool(st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY)) and (
        st.session_state.get(hhs_ui.DOCUMENT_SELECTED_KEY) == "TERMINAL"
    )


def clear_ai_chat_history() -> None:
    """Reset the backend ask history and clear the current AI chat history."""
    result = clear_ai_chat_history_data()
    if result.returncode == 0:
        push_floating_status("AI chat history cleared.", "info")
    else:
        push_floating_status("Unable to clear AI chat history.", "error")
    save_ui_state()


def clear_ai_chat_history_data() -> subprocess.CompletedProcess[str]:
    """Reset backend AI history and clear in-memory AI chat data."""
    result = run_hhs_ask_reset(close_dialogs=True)
    cache_delete_tag("ai")
    st.session_state["ai_chat_messages"] = []
    st.session_state["ai_context_output"] = ""
    st.session_state["ai_context_error"] = ""
    st.session_state["ai_clear_chat_pending"] = False
    st.session_state["ai_clear_chat_execute_pending"] = False
    return result


def clear_ai_context_history() -> None:
    """Reset the backend ask history and clear the current context display."""
    result = run_hhs_ask_reset(close_dialogs=True)
    cache_delete_tag("ai")
    st.session_state["ai_context_output"] = ""
    st.session_state["ai_context_error"] = ""
    if result.returncode == 0:
        push_floating_status("AI context history cleared.", "info")
    else:
        push_floating_status("Unable to clear AI context history.", "error")
    save_ui_state()


def confirm_ai_chat_clear() -> None:
    """Schedule the AI chat history reset after closing dialogs."""
    st.session_state["ai_clear_chat_execute_pending"] = True
    st.session_state["ai_clear_chat_pending"] = False
    save_ui_state()


def execute_pending_ai_chat_clear() -> None:
    """Execute a pending AI chat reset after dialogs are closed."""
    if st.session_state.get("ai_clear_chat_execute_pending"):
        clear_ai_chat_history()
    st.session_state["ai_clear_chat_execute_pending"] = False
    save_ui_state()


def request_ai_chat_clear_confirmation() -> None:
    """Show the AI chat clear confirmation prompt."""
    st.session_state["ai_clear_chat_pending"] = True


def cancel_ai_chat_clear_confirmation() -> None:
    """Hide the AI chat clear confirmation prompt."""
    st.session_state["ai_clear_chat_pending"] = False


def refresh_ai_context() -> None:
    """Fetch and store the current backend ask context for the Context tab."""
    result = run_hhs_ask_context()
    output = result.stdout if result.returncode == 0 else result.stderr or result.stdout
    clean_output = strip_ansi(output or "").strip()
    st.session_state["ai_context_output"] = (
        clean_output or "No Ollama context available."
    )
    st.session_state["ai_context_error"] = (
        ""
        if result.returncode == 0
        else clean_output or "Unable to load Ollama context."
    )
    save_ui_state()


def refresh_ai_prompt_file() -> None:
    """Fetch and store the editable backend ask prompt file for the Prompt panel."""
    result = run_hhs_ask_prompt_file()
    output = result.stdout if result.returncode == 0 else result.stderr or result.stdout
    clean_output = strip_ansi(output or "")
    if result.returncode == 0:
        st.session_state["ai_prompt_editor"] = clean_output
        st.session_state["ai_prompt_error"] = ""
        st.session_state["ai_prompt_loaded"] = True
    else:
        st.session_state["ai_prompt_error"] = (
            clean_output.strip() or "Unable to load Ollama prompt file."
        )
    save_ui_state()


def save_ai_prompt_file() -> None:
    """Persist the editable backend ask prompt file from the Prompt panel."""
    prompt_text = str(st.session_state.get("ai_prompt_editor", ""))
    result = run_hhs_save_ask_prompt_file(prompt_text)
    output = strip_ansi(result.stdout or result.stderr or "").strip()
    if result.returncode == 0:
        cache_delete_tag("ai")
        st.session_state["ai_prompt_error"] = ""
        st.session_state["ai_prompt_loaded"] = True
        push_floating_status(output or "Ollama prompt saved.", "info")
    else:
        st.session_state["ai_prompt_error"] = output or "Unable to save Ollama prompt."
        push_floating_status(st.session_state["ai_prompt_error"], "error")
    save_ui_state()


def revert_ai_prompt_file() -> None:
    """Restore the editable backend ask prompt file from the bundled source file."""
    result = run_hhs_revert_ask_prompt_file()
    output = strip_ansi(result.stdout or result.stderr or "")
    if result.returncode == 0:
        cache_delete_tag("ai")
        st.session_state["ai_prompt_editor"] = output
        st.session_state["ai_prompt_error"] = ""
        st.session_state["ai_prompt_loaded"] = True
        push_floating_status("Ollama prompt reverted.", "info")
    else:
        st.session_state["ai_prompt_error"] = (
            output.strip() or "Unable to revert Ollama prompt."
        )
        push_floating_status(st.session_state["ai_prompt_error"], "error")
    save_ui_state()


def uploaded_context_suffix(file_name: str) -> str:
    """Return a safe suffix for an uploaded AI context file."""
    suffix = Path(file_name).suffix.lower()
    if suffix.lstrip(".") in hhs_ui_constants.AI_CONTEXT_UPLOAD_TYPES:
        return suffix
    return ".txt"


def ingest_ai_context_upload(uploaded_file: object) -> None:
    """Ingest an uploaded text file into the backend ask context."""
    if uploaded_file is None:
        st.session_state["ai_context_error"] = "Choose a text file to ingest."
        save_ui_state()
        return

    file_name = str(getattr(uploaded_file, "name", "context.txt"))
    with tempfile.NamedTemporaryFile(
        "wb",
        delete=False,
        prefix="hhs-ai-context-",
        suffix=uploaded_context_suffix(file_name),
    ) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        result = run_hhs_ask_ingest(tmp_path)
        output = strip_ansi(result.stdout or result.stderr or "").strip()
        if result.returncode != 0:
            st.session_state["ai_context_error"] = output or "Unable to ingest context."
            st.session_state["ai_context_output"] = ""
            push_floating_status(st.session_state["ai_context_error"], "error")
            return
        st.session_state["ai_context_error"] = ""
        refresh_ai_context()
        push_floating_status(output or f"Ingested context: {file_name}", "info")
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass
        save_ui_state()


def request_ai_model_selection(
    old_model: str, new_model: str, model_status: str
) -> None:
    """Show the AI model selection confirmation prompt."""
    st.session_state["ai_model_select_error"] = ""
    st.session_state["ai_model_select_pending"] = {
        "old": old_model,
        "new": new_model,
        "status": model_status,
    }


def cancel_ai_model_selection() -> None:
    """Hide the AI model selection confirmation prompt."""
    st.session_state["ai_model_select_pending"] = None


def confirm_ai_model_selection() -> None:
    """Schedule the pending Ollama model selection after closing dialogs."""
    pending = st.session_state.get("ai_model_select_pending") or {}
    st.session_state["ai_model_select_execute_pending"] = pending
    st.session_state["ai_model_select_pending"] = None
    save_ui_state()


def execute_pending_ai_model_selection() -> None:
    """Start or complete the pending Ollama model selection."""
    pending = st.session_state.pop("ai_model_select_execute_pending", None) or {}
    new_model = str(pending.get("new", "")).strip()
    model_status = str(pending.get("status", "")).strip()
    if new_model:
        loader_message = (
            "Downloading model..." if not model_status else "Selecting Ollama model..."
        )
        started = start_background_bash_command(
            AI_MODEL_SELECT_JOB,
            build_hhs_ask_select_model_command(new_model),
            loader_message.rstrip("."),
            hhs_ui_constants.UI_COMMAND_MODEL_DOWNLOAD_TIMEOUT_SECONDS,
            metadata={"new_model": new_model, "model_status": model_status},
        )
        if started:
            push_floating_status(
                f"{loader_message.rstrip('.')} started: {new_model}", "info"
            )
        else:
            push_floating_status("Another AI model change is already running.", "warn")

    completed = background_job_result(AI_MODEL_SELECT_JOB)
    if completed is None:
        save_ui_state()
        return

    result, metadata = completed
    new_model = str(metadata.get("new_model", new_model)).strip()
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode != 0:
        st.session_state["ai_model_select_error"] = strip_ansi(
            status_message or "Unable to select model."
        )
        push_floating_status(
            st.session_state["ai_model_select_error"],
            "error",
        )
    else:
        st.session_state["ai_model_select_error"] = ""
        refresh_ai_model_listing()
        push_floating_status(
            status_message or f"Selected AI model: {new_model}", "info"
        )
    save_ui_state()


def request_ai_model_deletion(model_name: str, model_status: str) -> None:
    """Show the AI model deletion confirmation prompt."""
    st.session_state["ai_model_delete_error"] = ""
    st.session_state["ai_model_delete_pending"] = {
        "name": model_name,
        "status": model_status,
    }


def cancel_ai_model_deletion() -> None:
    """Hide the AI model deletion confirmation prompt."""
    st.session_state["ai_model_delete_pending"] = None


def confirm_ai_model_deletion() -> None:
    """Schedule the pending Ollama model deletion after closing dialogs."""
    pending = st.session_state.get("ai_model_delete_pending") or {}
    st.session_state["ai_model_delete_execute_pending"] = pending
    st.session_state["ai_model_delete_pending"] = None
    save_ui_state()


def execute_pending_ai_model_deletion() -> None:
    """Start or complete the pending Ollama model deletion flow."""
    pending = st.session_state.pop("ai_model_delete_execute_pending", None) or {}
    if isinstance(pending, str):
        pending = {"name": pending, "status": ""}
    model_name = str(pending.get("name", "")).strip()
    model_status = str(pending.get("status", "")).strip()
    if model_name:
        started = start_background_bash_command(
            AI_MODEL_DELETE_JOB,
            build_ollama_delete_model_command(model_name),
            "Deleting Ollama model",
            hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
            metadata={
                "phase": "delete",
                "model_name": model_name,
                "model_status": model_status,
            },
        )
        if started:
            push_floating_status(f"Deleting AI model: {model_name}", "info")
        else:
            st.session_state["ai_model_delete_execute_pending"] = pending
            push_floating_status(
                "Another AI model deletion is already running.", "warn"
            )

    completed = background_job_result(AI_MODEL_DELETE_JOB)
    if completed is None:
        save_ui_state()
        return

    result, metadata = completed
    phase = str(metadata.get("phase", "delete"))
    model_name = str(metadata.get("model_name", model_name)).strip()
    model_status = str(metadata.get("model_status", model_status)).strip()
    status_message = clean_command_status_message(result.stdout or result.stderr or "")

    if phase == "delete":
        if result.returncode == 0:
            refresh_ai_model_listing()
        complete_ai_model_delete_phase(result, model_name, model_status, status_message)
    elif phase == "fallback_list":
        complete_ai_model_delete_fallback_list_phase(result, model_name)
    elif phase == "fallback_select":
        fallback_model = str(metadata.get("fallback_model", "")).strip()
        complete_ai_model_delete_fallback_select_phase(
            result, fallback_model, status_message
        )
    save_ui_state()


def complete_ai_model_delete_phase(
    result: subprocess.CompletedProcess[str],
    model_name: str,
    model_status: str,
    status_message: str,
) -> None:
    """Complete the Ollama model deletion phase and start fallback discovery."""
    if result.returncode != 0:
        st.session_state["ai_model_delete_error"] = strip_ansi(
            status_message or "Unable to delete model."
        )
        push_floating_status(st.session_state["ai_model_delete_error"], "error")
        return

    st.session_state["ai_model_delete_error"] = ""
    refresh_ai_model_listing()
    push_floating_status(status_message or f"Deleted AI model: {model_name}", "info")
    if model_status != "Active":
        return

    start_background_bash_command(
        AI_MODEL_DELETE_JOB,
        build_hhs_ask_models_command(),
        "Loading fallback Ollama model",
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        metadata={"phase": "fallback_list", "model_name": model_name},
    )


def complete_ai_model_delete_fallback_list_phase(
    result: subprocess.CompletedProcess[str], model_name: str
) -> None:
    """Complete fallback model discovery after deleting an active model."""
    if result.returncode != 0:
        st.session_state["ai_model_delete_error"] = strip_ansi(
            result.stderr or result.stdout or "Unable to list fallback Ollama models."
        )
        push_floating_status(st.session_state["ai_model_delete_error"], "error")
        return

    cache_background_command_result(
        {
            **background_command_metadata(build_hhs_ask_models_command(), "ai_models"),
            "ttl_seconds": hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        },
        result,
    )
    fallback_model = first_downloaded_ollama_model(
        result.stdout, excluded_model=model_name
    )
    if not fallback_model:
        return
    start_background_bash_command(
        AI_MODEL_DELETE_JOB,
        build_hhs_ask_select_model_command(fallback_model),
        "Selecting fallback Ollama model",
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        metadata={
            "phase": "fallback_select",
            "model_name": model_name,
            "fallback_model": fallback_model,
        },
    )


def complete_ai_model_delete_fallback_select_phase(
    result: subprocess.CompletedProcess[str],
    fallback_model: str,
    status_message: str,
) -> None:
    """Complete fallback model selection after deleting the active model."""
    if result.returncode != 0:
        st.session_state["ai_model_delete_error"] = strip_ansi(
            status_message or "Unable to select fallback model."
        )
        push_floating_status(st.session_state["ai_model_delete_error"], "error")
        return

    refresh_ai_model_listing()
    push_floating_status(
        status_message or f"Selected fallback AI model: {fallback_model}",
        "info",
    )


def render_sidebar() -> None:
    """Render the closeable HomeSetup sidebar."""
    theme_options = available_theme_options()
    synchronize_selected_ssh_host_with_connection()
    host_options = host_selector_options()
    selected_host = selected_ssh_host()
    if not selected_host:
        st.session_state["ssh_host_selected"] = local_hostname()
        selected_host = selected_ssh_host()
    connected_host = connected_ssh_host()
    if connected_host:
        selected_host = connected_host
    selected_theme = validated_theme_name(
        st.session_state.get(hhs_ui.THEME_SELECTED_KEY, ""), theme_options
    )
    if not selected_theme:
        selected_theme = default_theme_name(theme_options)
        st.session_state[hhs_ui.THEME_SELECTED_KEY] = selected_theme
    previous_theme = st.session_state.get("theme_last_seen", selected_theme)
    with st.sidebar:
        render_sidebar_clock()
        render_sidebar_title()
        st.write("")
        host_kind = "Local" if selected_host_is_local() else "SSH"
        st.markdown(f"**Host ({host_kind}):**")
        if connected_host:
            connected_host_key = hashlib.sha256(
                connected_host.encode("utf-8")
            ).hexdigest()[:8]
            st.selectbox(
                f"Host ({host_kind})",
                options=(connected_host,),
                index=0,
                key=f"ssh_host_connected_display_{connected_host_key}",
                label_visibility="collapsed",
                disabled=True,
                width="stretch",
            )
        else:
            if st.session_state.get("ssh_host_selector") != selected_host:
                st.session_state["ssh_host_selector"] = selected_host
            selected_host = st.selectbox(
                f"Host ({host_kind})",
                options=host_options,
                key="ssh_host_selector",
                label_visibility="collapsed",
                on_change=select_ssh_host_from_widget,
                width="stretch",
            )
        if connected_host or not selected_host_is_local():
            if connected_host:
                st.button(
                    "ﮤ Disconnect",
                    key="ssh_disconnect_button",
                    on_click=request_ssh_host_disconnection,
                    width="stretch",
                )
            else:
                st.button(
                    "ﮣ Connect",
                    key="ssh_connect_button",
                    on_click=request_ssh_host_connect,
                    width="stretch",
                )
        st.markdown("**Theme**")
        selected_theme = st.selectbox(
            "Theme",
            options=theme_options,
            key=hhs_ui.THEME_SELECTED_KEY,
            placeholder="",
            disabled=False,
            label_visibility="collapsed",
            on_change=request_theme_reload,
            width="stretch",
        )
        if selected_theme != previous_theme and selected_theme in theme_options:
            persist_theme_selection(selected_theme)
            st.session_state["theme_last_seen"] = selected_theme
            st.session_state["theme_reload_pending"] = True
            st.session_state["theme_reload_name"] = selected_theme
            st.rerun()
        st.session_state["theme_last_seen"] = selected_theme
        st.markdown(
            '<hr class="hhs-sidebar-separator" />',
            unsafe_allow_html=True,
        )
        if st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY):
            st.button(
                "BACK",
                key="document_back_button",
                on_click=close_document_view,
                width="stretch",
            )
            if terminal_document_view_is_active():
                render_terminal_back_button_cleanup_script()
        else:
            render_ttyd_terminal_frame_cleanup_script()
            st.button(
                " README",
                key="readme_open_button",
                on_click=open_document_view,
                args=("README",),
                width="stretch",
            )
            st.button(
                " HANDBOOK",
                key="handbook_open_button",
                on_click=open_document_view,
                args=("HANDBOOK",),
                width="stretch",
            )
            render_sidebar_terminal_button()


def command_loader_html(
    message: str, loader_id: str, started_at_millis: int, timeout_seconds: int
) -> str:
    """Return reusable banner loader markup for command-data waits."""
    safe_message = html.escape(message.strip() or "Loading...")
    safe_loader_id = html.escape(loader_id, quote=True)
    safe_timeout = max(1, int(timeout_seconds))
    return f"""
    <div class="hhs-command-loader" data-loader-id="{safe_loader_id}" role="status" aria-live="polite">
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


def render_command_loader_timer(loader_id: str) -> None:
    """Start the elapsed-time updater for one in-flow command loader."""
    components.html(
        f"""
        <script>
          (() => {{
            const doc = window.parent.document;
            const loader_id = {json.dumps(loader_id)};
            const selector = `[data-loader-id="${{loader_id}}"] .hhs-command-loader-elapsed`;
            const node = doc.querySelector(selector);
            if (!node || node.dataset.timerStarted === "true") {{
              return;
            }}
            node.dataset.timerStarted = "true";
            const started_at = Number(node.dataset.startedAt || Date.now());
            const render_elapsed = () => {{
              const elapsed_seconds = Math.max(0, Math.floor((Date.now() - started_at) / 1000));
              const timeout_seconds = Math.max(1, Number(node.dataset.timeoutSeconds || 1));
              const elapsed_ratio = elapsed_seconds / timeout_seconds;
              const minutes = Math.floor(elapsed_seconds / 60);
              const seconds = String(elapsed_seconds % 60).padStart(2, "0");
              node.textContent = `time elapsed: ${{minutes}}m:${{seconds}}s`;
              node.classList.toggle("hhs-loader-elapsed-warning", elapsed_ratio >= 0.3 && elapsed_ratio < 0.6);
              node.classList.toggle("hhs-loader-elapsed-danger", elapsed_ratio >= 0.6);
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
    message: str, started_at: float | None = None, timeout_seconds: int | None = None
) -> None:
    """Render the reusable banner loader for command-data waits."""
    loader_id = f"hhs-command-loader-{secrets.token_hex(8)}"
    started_at_millis = int((started_at or time.time()) * 1000)
    safe_timeout = int(timeout_seconds or command_timeout_seconds())
    st.markdown(
        command_loader_html(message, loader_id, started_at_millis, safe_timeout),
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
    components.html(
        f"""
        <script>
          (() => {{
            const parentWindow = window.parent;
            const doc = window.parent.document;
            const createdAt = {created_at_millis};
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
            overlay.style.width = "100vw";
            overlay.style.height = "100dvh";
            overlay.style.display = "flex";
            overlay.style.alignItems = "center";
            overlay.style.justifyContent = "center";
            overlay.style.zIndex = "999999";
            overlay.innerHTML = `
              <div class="hhs-tab-loader-panel">
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
              const elapsed_seconds = Math.max(0, Math.floor((Date.now() - started_at) / 1000));
              const timeout_seconds = Math.max(1, Number(node.dataset.timeoutSeconds || 1));
              const elapsed_ratio = elapsed_seconds / timeout_seconds;
              const minutes = Math.floor(elapsed_seconds / 60);
              const seconds = String(elapsed_seconds % 60).padStart(2, "0");
              node.textContent = `time elapsed: ${{minutes}}m:${{seconds}}s`;
              node.classList.toggle("hhs-loader-elapsed-warning", elapsed_ratio >= 0.3 && elapsed_ratio < 0.6);
              node.classList.toggle("hhs-loader-elapsed-danger", elapsed_ratio >= 0.6);
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
    components.html(
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
    safe_theme_name = theme_name.strip() or hhs_ui.APP_THEME_CSS_FILE.stem
    st.session_state["theme_reload_pending"] = False
    render_preloader(f"Loading theme {safe_theme_name}", transient=False)
    components.html(
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


def close_all_dialogs() -> None:
    """Close every Streamlit dialog or inline confirmation controlled by this UI."""
    st.session_state.pop("_hhs_dialog_pending_callback", None)
    st.session_state.pop("_hhs_dialog_button_dismissal", None)
    st.session_state["ai_clear_chat_pending"] = False
    st.session_state["ai_model_select_pending"] = None
    st.session_state["ai_model_delete_pending"] = None
    st.session_state["home_tool_action_execute_pending"] = None
    st.session_state["ssh_explorer_delete_pending"] = None
    st.session_state["ssh_connection_dialog_title"] = ""
    st.session_state["footer_shell_version_dialog_title"] = ""
    st.session_state.pop("home_tool_action_operation", None)
    st.session_state.pop("home_tool_action_name", None)
    st.session_state.pop("home_tool_action_message", None)
    st.session_state.pop("home_tool_action_succeeded", None)
    st.session_state.pop("home_tool_tldr_name", None)
    st.session_state.pop("home_tool_tldr_output", None)
    st.session_state.pop("home_tool_tldr_succeeded", None)


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


def queue_dialog_callback(callback: Callable[[], None] | None) -> None:
    """Queue a dialog button callback for execution after the dialog is dismissed."""
    if callback:
        st.session_state["_hhs_dialog_pending_callback"] = callback


def execute_pending_dialog_callback() -> None:
    """Run one dialog callback that was queued before the dialog was dismissed."""
    callback = st.session_state.pop("_hhs_dialog_pending_callback", None)
    if callable(callback):
        callback()


def handle_dialog_button_click(
    callback: Callable[[], None] | None = None,
    close_callback: Callable[[], None] | None = None,
) -> None:
    """Dismiss the active dialog and defer the button callback until after dismissal."""
    if close_callback:
        close_callback()
    queue_dialog_callback(callback)
    st.session_state["_hhs_dialog_button_dismissal"] = True
    dismiss_streamlit_dialog()


def handle_dialog_dismiss(callback: Callable[[], None] | None = None) -> None:
    """Run native dialog-dismiss cleanup unless dismissal came from a dialog button."""
    if st.session_state.pop("_hhs_dialog_button_dismissal", False):
        return
    if callback:
        callback()


def pop_dialog(
    title: str,
    message: str = "",
    confirm_key: str = "",
    cancel_key: str = "",
    on_confirm: Callable[[], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    buttons: tuple[dict[str, object], ...] | None = None,
    body: Callable[[], None] | None = None,
    close_callback: Callable[[], None] | None = None,
    dismissible: bool = True,
) -> bool:
    """Render a reusable dialog that defers button callbacks until after dismissal."""
    dialog_buttons = buttons
    if dialog_buttons is None:
        dialog_buttons = (
            {
                "label": confirm_label,
                "key": confirm_key,
                "callback": on_confirm,
            },
            {
                "label": cancel_label,
                "key": cancel_key,
                "callback": on_cancel,
            },
        )

    dismiss_callback = close_callback or on_cancel
    on_dismiss = (
        (lambda: handle_dialog_dismiss(dismiss_callback))
        if dismiss_callback
        else "rerun"
    )

    @st.dialog(title, dismissible=dismissible, on_dismiss=on_dismiss)
    def render_dialog() -> None:
        """Render the configured dialog content and deferred-action buttons."""
        if body:
            body()
        elif message:
            st.write(message)
        visible_buttons = [button for button in dialog_buttons if button.get("key")]
        if not visible_buttons:
            return
        columns = st.columns(len(visible_buttons))
        for column, button in zip(columns, visible_buttons):
            label = str(button.get("label", "Close"))
            key = str(button.get("key", ""))
            callback = button.get("callback")
            with column:
                if st.button(label, key=key, width="stretch"):
                    handle_dialog_button_click(
                        callback if callable(callback) else None,
                        close_callback=close_callback,
                    )

    render_dialog()
    return True


def folder_picker_start_directory(value: str = "") -> str:
    """Return the best existing directory to open in the folder picker."""
    raw_value = str(value or "").strip() or os.getcwd()
    expanded_value = os.path.expandvars(os.path.expanduser(raw_value))
    candidate = Path(expanded_value)
    if candidate.is_file():
        candidate = candidate.parent
    if not candidate.is_dir():
        candidate = Path.home()
    return str(candidate.resolve())


def path_picker_mode() -> str:
    """Return the active path picker mode."""
    mode = str(st.session_state.get("_hhs_folder_picker_mode", "folder")).strip()
    return "file" if mode == "file" else "folder"


def path_picker_start_path(value: str = "", mode: str = "folder") -> str:
    """Return the best existing path to seed a folder or file picker."""
    raw_value = str(value or "").strip() or os.getcwd()
    expanded_value = os.path.expandvars(os.path.expanduser(raw_value))
    candidate = Path(expanded_value)
    if mode == "file" and candidate.is_file():
        return str(candidate.resolve())
    return folder_picker_start_directory(expanded_value)


def path_picker_current_directory(value: str = "", mode: str = "folder") -> str:
    """Return the browsing directory for a folder or file picker value."""
    selected_path = Path(path_picker_start_path(value, mode))
    if mode == "file" and selected_path.is_file():
        return str(selected_path.parent.resolve())
    return folder_picker_start_directory(str(selected_path))


def folder_picker_child_directories(
    directory: str, include_dot_folders: bool = False
) -> list[str]:
    """Return readable child directories for the folder picker."""
    current_directory = Path(folder_picker_start_directory(directory))
    try:
        return [
            str(path.resolve())
            for path in sorted(
                current_directory.iterdir(),
                key=lambda item: (not item.is_dir(), item.name.lower()),
            )
            if path.is_dir() and (include_dot_folders or not path.name.startswith("."))
        ]
    except OSError:
        return []


def path_picker_child_paths(
    directory: str, mode: str = "folder", include_dot_folders: bool = False
) -> list[str]:
    """Return readable child paths for a folder or file picker."""
    if mode == "folder":
        return folder_picker_child_directories(directory, include_dot_folders)
    current_directory = Path(folder_picker_start_directory(directory))
    try:
        return [
            str(path.resolve())
            for path in sorted(
                current_directory.iterdir(),
                key=lambda item: (not item.is_dir(), item.name.lower()),
            )
            if (path.is_dir() or path.is_file())
            and (include_dot_folders or not path.name.startswith("."))
        ]
    except OSError:
        return []


def folder_picker_label(directory: str) -> str:
    """Return the display label for a folder picker option."""
    path = Path(directory)
    return path.name or str(path)


def path_picker_label(path_value: str) -> str:
    """Return the display label for a folder or file picker option."""
    path = Path(path_value)
    return path.name or str(path)


def request_path_picker(
    target_key: str,
    fallback_value: str = "",
    mode: str = "folder",
) -> None:
    """Open the reusable path picker for a Streamlit input key."""
    picker_mode = "file" if mode == "file" else "folder"
    current_value = str(st.session_state.get(target_key, "") or fallback_value)
    start_path = path_picker_start_path(current_value, picker_mode)
    start_directory = path_picker_current_directory(start_path, picker_mode)
    st.session_state["_hhs_folder_picker_open"] = True
    st.session_state["_hhs_folder_picker_mode"] = picker_mode
    st.session_state["_hhs_folder_picker_target_key"] = target_key
    st.session_state["_hhs_folder_picker_current_dir"] = start_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = start_path
    st.session_state.setdefault("_hhs_folder_picker_include_dot_folders", False)
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def request_folder_picker(
    target_key: str,
    fallback_value: str = "",
) -> None:
    """Open the folder picker for a Streamlit input key."""
    request_path_picker(target_key, fallback_value, mode="folder")


def request_file_picker(
    target_key: str,
    fallback_value: str = "",
) -> None:
    """Open the file picker for a Streamlit input key."""
    request_path_picker(target_key, fallback_value, mode="file")


def close_folder_picker() -> None:
    """Close the folder picker dialog and clear transient selection state."""
    st.session_state["_hhs_folder_picker_open"] = False
    st.session_state.pop("_hhs_folder_picker_mode", None)
    st.session_state.pop("_hhs_folder_picker_target_key", None)
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def selected_folder_picker_path() -> str:
    """Return the selected path from the path picker current input."""
    typed_path = str(
        st.session_state.get("_hhs_folder_picker_current_dir_input", "")
    ).strip()
    mode = path_picker_mode()
    if typed_path:
        return path_picker_start_path(typed_path, mode)
    return path_picker_start_path(
        str(st.session_state.get("_hhs_folder_picker_current_dir", "")), mode
    )


def queue_folder_picker_selection(target_key: str, selected_path: str) -> None:
    """Queue a folder picker selection for the next page render."""
    if not target_key:
        return
    st.session_state["_hhs_folder_picker_pending_target_key"] = target_key
    st.session_state["_hhs_folder_picker_pending_value"] = selected_path


def apply_pending_folder_picker_selection() -> None:
    """Apply a queued folder picker selection before target inputs render."""
    target_key = str(
        st.session_state.pop("_hhs_folder_picker_pending_target_key", "")
    ).strip()
    selected_path = str(
        st.session_state.pop("_hhs_folder_picker_pending_value", "")
    ).strip()
    if target_key and selected_path:
        st.session_state[target_key] = selected_path


def set_folder_picker_current_directory(directory: str) -> None:
    """Set the folder picker current directory."""
    selected_directory = folder_picker_start_directory(directory)
    st.session_state["_hhs_folder_picker_current_dir"] = selected_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = selected_directory
    include_dot_folders = bool(
        st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
    )
    child_directories = path_picker_child_paths(
        selected_directory, path_picker_mode(), include_dot_folders
    )
    if child_directories:
        st.session_state["_hhs_folder_picker_selected_dir"] = child_directories[0]
    else:
        st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def apply_folder_picker_typed_directory() -> None:
    """Apply the manually typed path picker value."""
    typed_path = str(st.session_state.get("_hhs_folder_picker_current_dir_input", ""))
    mode = path_picker_mode()
    if mode == "folder":
        set_folder_picker_current_directory(typed_path)
        return
    selected_path = path_picker_start_path(typed_path, mode)
    current_directory = path_picker_current_directory(selected_path, mode)
    st.session_state["_hhs_folder_picker_current_dir"] = current_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = selected_path
    include_dot_folders = bool(
        st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
    )
    child_directories = path_picker_child_paths(
        current_directory, mode, include_dot_folders
    )
    if child_directories:
        st.session_state["_hhs_folder_picker_selected_dir"] = child_directories[0]
    else:
        st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def open_folder_picker_parent() -> None:
    """Move the folder picker to the parent directory."""
    current_directory = Path(
        folder_picker_start_directory(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
    )
    set_folder_picker_current_directory(str(current_directory.parent))


def open_folder_picker_selected_directory() -> None:
    """Move the path picker into the selected child or select a child file."""
    selected_path = str(st.session_state.get("_hhs_folder_picker_selected_dir", ""))
    if not selected_path:
        return
    selected_entry = Path(selected_path)
    if path_picker_mode() == "file" and selected_entry.is_file():
        st.session_state["_hhs_folder_picker_current_dir_input"] = str(
            selected_entry.resolve()
        )
        return
    set_folder_picker_current_directory(selected_path)


def apply_folder_picker_selection() -> None:
    """Assign the selected folder to the target Streamlit input key."""
    target_key = str(st.session_state.get("_hhs_folder_picker_target_key", ""))
    if target_key:
        selected_path = selected_folder_picker_path()
        st.session_state[target_key] = selected_path
        queue_folder_picker_selection(target_key, selected_path)
    close_folder_picker()


def apply_folder_picker_selection_and_dismiss() -> None:
    """Assign the selected folder and dismiss the folder picker dialog."""
    apply_folder_picker_selection()
    dismiss_streamlit_dialog()


def cancel_folder_picker_and_dismiss() -> None:
    """Close the folder picker dialog without changing the target input."""
    close_folder_picker()
    dismiss_streamlit_dialog()


def render_path_picker_dialog() -> bool:
    """Render the reusable single path picker dialog when requested."""
    if not st.session_state.get("_hhs_folder_picker_open"):
        return False

    def render_body() -> None:
        """Render the visual path picker controls."""
        mode = path_picker_mode()
        selected_label = "Selected file" if mode == "file" else "Selected folder"
        option_label = "Files" if mode == "file" else "Folders"
        empty_caption = (
            "No files or folders." if mode == "file" else "No child folders."
        )
        current_directory = folder_picker_start_directory(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
        st.text_input(
            selected_label,
            key="_hhs_folder_picker_current_dir_input",
            on_change=apply_folder_picker_typed_directory,
        )
        include_dot_folders = bool(
            st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
        )
        child_directories = path_picker_child_paths(
            current_directory, mode, include_dot_folders
        )
        selected_directory = st.session_state.get("_hhs_folder_picker_selected_dir")
        if selected_directory not in child_directories:
            st.session_state.pop("_hhs_folder_picker_selected_dir", None)
        if child_directories:
            st.selectbox(
                option_label,
                child_directories,
                key="_hhs_folder_picker_selected_dir",
                format_func=path_picker_label,
            )
        else:
            st.caption(empty_caption)
        st.checkbox(
            "Include .dot-folders",
            key="_hhs_folder_picker_include_dot_folders",
            value=False,
        )
        with st.container(key="folder_picker_action_grid"):
            st.button(
                "",
                key="folder_picker_parent_button",
                help="Parent",
                on_click=open_folder_picker_parent,
                width="stretch",
            )
            st.button(
                "",
                key="folder_picker_open_button",
                help="Open",
                disabled=not bool(child_directories),
                on_click=open_folder_picker_selected_directory,
                width="stretch",
            )
            st.button(
                "",
                key="folder_picker_select_button",
                help="Select",
                on_click=apply_folder_picker_selection_and_dismiss,
                width="stretch",
            )
            st.button(
                "ﰸ",
                key="folder_picker_cancel_button",
                help="Cancel",
                on_click=cancel_folder_picker_and_dismiss,
                width="stretch",
            )

    return pop_dialog(
        title="Select file" if path_picker_mode() == "file" else "Select folder",
        body=render_body,
        buttons=(),
        close_callback=close_folder_picker,
    )


def render_folder_picker_dialog() -> bool:
    """Render the reusable path picker dialog when requested."""
    return render_path_picker_dialog()


def homesetup_version(refresh_cache: bool = False) -> str:
    """Return the cached HomeSetup product version from the shell environment."""
    if refresh_cache:
        result = run_hhs_envs("^HHS_VERSION$", refresh_cache=refresh_cache)
        if result.returncode == 0:
            st.session_state["footer_hhs_version_cache_loaded"] = True
            for row in parse_rows_cached("env", result.stdout, parse_hhs_envs):
                if row["Name"] == "HHS_VERSION" and row["Value"]:
                    return row["Value"]

    command = build_hhs_envs_command("^HHS_VERSION$")
    complete_cached_background_command(
        FOOTER_VERSION_JOB,
        "footer_hhs_version_error",
        "Unable to load HomeSetup version.",
    )
    result, fresh_cache = cached_background_command_result(command, "env")
    if result is not None and result.returncode == 0:
        st.session_state["footer_hhs_version_cache_loaded"] = True
        for row in parse_rows_cached("env", result.stdout, parse_hhs_envs):
            if row["Name"] == "HHS_VERSION" and row["Value"]:
                return row["Value"]

    if not fresh_cache and not background_job_is_running(FOOTER_VERSION_JOB):
        start_cached_background_command(
            FOOTER_VERSION_JOB,
            command,
            "Loading HomeSetup version",
            "env",
            hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
            hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        )
    return os.environ.get("HHS_VERSION", "unknown")


def homesetup_home() -> Path:
    """Return the HomeSetup repository root used by this UI."""
    return Path(os.environ.get("HHS_HOME", hhs_ui.APP_DIR.parents[3])).expanduser()


def homesetup_config_dir() -> Path:
    """Return the HomeSetup runtime configuration directory used by this UI."""
    return Path(os.environ.get("HHS_DIR", Path.home() / ".config/hhs")).expanduser()


def ollama_history_file() -> Path:
    """Return the configured HomeSetup Ollama history file path."""
    return Path(
        os.environ.get(
            "HHS_OLLAMA_HISTORY_FILE", homesetup_config_dir() / ".ollama_history"
        )
    ).expanduser()


def ollama_prompt_file() -> Path:
    """Return the configured HomeSetup Ollama prompt file path."""
    return Path(
        os.environ.get(
            "HHS_OLLAMA_PROMPT_FILE", homesetup_config_dir() / "hhs-ask-ollama.md"
        )
    ).expanduser()


def monitor_default_disk_directory() -> str:
    """Return the default directory for the disk monitor."""
    if connected_ssh_host():
        return "${HHS_HOME}"
    return str(homesetup_home())


def monitor_disk_directory_is_hhs_home_token(directory: object) -> bool:
    """Return whether a disk monitor directory references HomeSetup home."""
    return str(directory or "").strip() in {"${HHS_HOME}", "$HHS_HOME"}


def normalized_monitor_top_n(value: object) -> int:
    """Return a valid monitor Top N value."""
    try:
        top_n = int(value)
    except (TypeError, ValueError):
        return 10
    if top_n < 1 or top_n > 100:
        return 10
    return top_n


def normalized_monitor_disk_top_n(value: object) -> int:
    """Return a valid monitor disk Top N value."""
    return normalized_monitor_top_n(value)


def monitor_process_top_n_state_key(metric: str) -> str:
    """Return the session key for the applied process monitor Top N value."""
    return f"monitor_{metric.lower()}_top_n"


def monitor_process_top_n_input_key(metric: str) -> str:
    """Return the session key for the pending process monitor Top N value."""
    return f"monitor_{metric.lower()}_top_n_input"


def normalized_monitor_process_top_n(metric: str) -> int:
    """Return the applied Top N value for a process monitor metric."""
    return normalized_monitor_top_n(
        st.session_state.get(monitor_process_top_n_state_key(metric))
    )


def handle_monitor_disk_top_n_change() -> None:
    """Persist the pending monitor disk Top N widget value."""
    st.session_state["monitor_disk_top_n_input"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n_input")
    )
    save_ui_state()


def handle_monitor_process_top_n_change(metric: str) -> None:
    """Persist the pending process monitor Top N widget value."""
    input_key = monitor_process_top_n_input_key(metric)
    st.session_state[input_key] = normalized_monitor_top_n(
        st.session_state.get(input_key)
    )
    save_ui_state()


def apply_monitor_disk_controls() -> None:
    """Apply pending disk monitor controls before the next command refresh."""
    directory = monitor_disk_directory_for_host(
        st.session_state.get("monitor_disk_directory", "")
    )
    st.session_state["monitor_disk_directory"] = directory
    st.session_state["monitor_disk_directory_applied"] = directory
    st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n_input")
    )
    cache_delete_tag("monitor_disk")
    save_ui_state()


def apply_monitor_process_controls(metric: str) -> None:
    """Apply pending process monitor controls before the next command refresh."""
    input_key = monitor_process_top_n_input_key(metric)
    state_key = monitor_process_top_n_state_key(metric)
    top_n = normalized_monitor_top_n(st.session_state.get(input_key))
    st.session_state[state_key] = top_n
    st.session_state[input_key] = top_n
    cache_delete_command(
        build_process_monitor_command(metric, top_n),
        "monitor_process",
    )
    st.session_state[f"monitor_{metric.lower()}_error"] = ""
    save_ui_state()


def applied_monitor_disk_directory() -> str:
    """Return the directory currently applied to the disk monitor command."""
    directory = str(
        st.session_state.get(
            "monitor_disk_directory_applied",
            st.session_state.get("monitor_disk_directory", ""),
        )
    ).strip()
    return directory or monitor_default_disk_directory()


def monitor_disk_directory_for_host(directory: object) -> str:
    """Return a disk monitor directory normalized for the active command host."""
    clean_directory = str(directory or "").strip()
    default_directory = monitor_default_disk_directory()
    if not clean_directory:
        return default_directory
    if not connected_ssh_host() and monitor_disk_directory_is_hhs_home_token(
        clean_directory
    ):
        return default_directory
    if connected_ssh_host() and expand_monitor_disk_directory(clean_directory) == str(
        homesetup_home()
    ):
        return default_directory
    return clean_directory


def synchronize_monitor_disk_directory_with_host() -> None:
    """Keep disk monitor path controls aligned with the current execution host."""
    host_key = command_remote_host() or "local"
    if st.session_state.get("monitor_disk_host_key") == host_key:
        return
    st.session_state["monitor_disk_host_key"] = host_key
    directory = monitor_disk_directory_for_host(
        st.session_state.get("monitor_disk_directory", "")
    )
    st.session_state["monitor_disk_directory"] = directory
    st.session_state["monitor_disk_directory_applied"] = directory
    cache_delete_tag("monitor_disk")


def hhs_log_dir() -> Path:
    """Return the HomeSetup log directory used by monitor logs."""
    return Path(
        os.environ.get(
            "HHS_LOG_DIR",
            Path(os.environ.get("HHS_DIR", Path.home() / ".config/hhs")) / "logs",
        )
    ).expanduser()


def hhs_log_files() -> list[str]:
    """Return available HomeSetup log file names."""
    log_dir = hhs_log_dir()
    if not log_dir.is_dir():
        return []
    return sorted(path.name for path in log_dir.glob("*.log") if path.is_file())


def hhs_log_file_path(log_file: str) -> Path:
    """Return the safe path for a HomeSetup log file name."""
    return hhs_log_dir() / Path(log_file).name


def selected_monitor_log_level() -> str:
    """Return the selected monitor log level normalized to a supported value."""
    level = str(st.session_state.get("monitor_log_level", "ALL_LEVELS")).strip().upper()
    if level not in hhs_ui.LOG_LEVELS:
        return "ALL_LEVELS"
    return level


def monitor_log_level_label(level: str) -> str:
    """Return the display label for a monitor log level."""
    return "All" if level == "ALL_LEVELS" else level


def clear_monitor_log_file() -> None:
    """Empty the selected monitor log file and keep it available for logging."""
    selected_log = str(st.session_state.get("monitor_log_file", "")).strip()
    log_path = hhs_log_file_path(selected_log)
    if not selected_log or log_path.name not in hhs_log_files():
        push_floating_status("Unable to clear log file.", "error")
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("", encoding="utf-8")
    except OSError as error:
        push_floating_status(f"Unable to clear log file: {error}", "error")
        return
    cache_delete_tag("monitor_logs")
    push_floating_status(f"Log file cleared: {log_path.name}", "info")


def toggle_monitor_logs_tail() -> None:
    """Toggle automatic monitor log tail refresh and persist the updated state."""
    st.session_state["monitor_logs_tail"] = not bool(
        st.session_state.get("monitor_logs_tail", True)
    )
    save_ui_state()


def is_persisted_ui_key(key: str) -> bool:
    """Return whether a Streamlit session key should be persisted."""
    if key.endswith("_button"):
        return False
    return key in hhs_ui.PERSISTED_UI_KEYS or key.startswith(
        hhs_ui.PERSISTED_UI_KEY_PREFIXES
    )


def is_persistable_ui_value(value: object) -> bool:
    """Return whether a Streamlit session value is safe for JSON UI persistence."""
    if isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, list):
        return all(
            isinstance(item, (str, bool, int, float))
            or (
                isinstance(item, dict)
                and all(
                    isinstance(key, str)
                    and isinstance(dict_value, (str, bool, int, float))
                    for key, dict_value in item.items()
                )
            )
            for item in value
        )
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and isinstance(item, (str, bool, int, float))
            for key, item in value.items()
        )
    return False


def load_ui_state() -> dict[str, object]:
    """Load persisted Streamlit UI selections from disk."""
    if not hhs_ui.UI_STATE_FILE.exists():
        return {}
    try:
        data = json.loads(hhs_ui.UI_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str)
        and is_persisted_ui_key(key)
        and is_persistable_ui_value(value)
    }


def persisted_theme_name() -> str:
    """Return the valid persisted UI theme or the default theme."""
    selected_theme = validated_theme_name(
        load_ui_state().get(hhs_ui.THEME_SELECTED_KEY, "")
    )
    if selected_theme:
        return selected_theme
    return default_theme_name()


def restore_persisted_theme_selection() -> str:
    """Restore the persisted UI theme into Streamlit session state."""
    selected_theme = validated_theme_name(
        st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    )
    if not selected_theme:
        selected_theme = validated_theme_name(
            load_ui_state().get(hhs_ui.THEME_SELECTED_KEY, "")
        )
    if not selected_theme:
        selected_theme = default_theme_name()
    st.session_state[hhs_ui.THEME_SELECTED_KEY] = selected_theme
    return selected_theme


def export_env_value_overrides(overrides: object) -> None:
    """Export persisted environment value overrides to the Streamlit process."""
    if not isinstance(overrides, dict):
        return
    for key, value in overrides.items():
        if isinstance(key, str) and isinstance(value, str):
            os.environ[key] = value


def export_path_value_overrides(overrides: object) -> None:
    """Export persisted PATH value overrides to the Streamlit process."""
    if not isinstance(overrides, dict):
        return
    path_entries = os.environ.get("PATH", "").split(":")
    for old_path, new_path in overrides.items():
        if not isinstance(old_path, str) or not isinstance(new_path, str):
            continue
        path_entries = [
            new_path if entry == old_path else entry for entry in path_entries
        ]
        if new_path not in path_entries:
            path_entries.append(new_path)
    os.environ["PATH"] = ":".join(path_entries)


def restore_ui_state() -> None:
    """Restore persisted UI selections into Streamlit session state."""
    if st.session_state.get("ui_state_restored"):
        return
    for key, value in load_ui_state().items():
        st.session_state[key] = value
    restore_persisted_theme_selection()
    export_env_value_overrides(st.session_state.get(hhs_ui.ENV_VALUE_OVERRIDES_KEY))
    export_path_value_overrides(st.session_state.get(hhs_ui.PATH_VALUE_OVERRIDES_KEY))
    st.session_state["ui_state_restored"] = True


def save_ui_state() -> None:
    """Persist selected Streamlit UI values to disk."""
    current_state = load_ui_state()
    persisted_theme = validated_theme_name(
        current_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    )
    data = {
        key: st.session_state[key]
        for key in sorted(st.session_state)
        if is_persisted_ui_key(key)
        and is_persistable_ui_value(st.session_state.get(key))
    }
    selected_theme = validated_theme_name(data.get(hhs_ui.THEME_SELECTED_KEY, ""))
    if selected_theme:
        data[hhs_ui.THEME_SELECTED_KEY] = selected_theme
    elif persisted_theme:
        data[hhs_ui.THEME_SELECTED_KEY] = persisted_theme
    else:
        data.pop(hhs_ui.THEME_SELECTED_KEY, None)
    if data == current_state:
        return
    hhs_ui.UI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    hhs_ui.UI_STATE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def push_floating_status(
    message: str, kind: str = "info", timeout_seconds: float = 5.0
) -> None:
    """Queue a compact floating status message for the next footer render."""
    clean_message = clean_command_status_message(str(message))
    if not clean_message:
        return
    status_queue = floating_status_queue()
    status_queue.append(
        {
            "message": clean_message,
            "kind": normalize_floating_status_kind(kind),
            "timeout_seconds": max(1.0, min(float(timeout_seconds), 30.0)),
        }
    )
    del status_queue[: -hhs_ui_constants.FLOATING_STATUS_QUEUE_LIMIT]
    st.session_state[hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY] = status_queue


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
        timeout = float(status.get("timeout_seconds", 5.0))
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


def floating_status_glyph(kind: str) -> str:
    """Return the glyph used by the floating status component."""
    return {
        "info": "",
        "error": "",
        "warn": "",
    }.get(kind, "")


def render_floating_status() -> None:
    """Render the compact floating status component above the footer."""
    status = current_floating_status()
    if not isinstance(status, dict):
        return
    message = html.escape(str(status.get("message", "")).strip())
    if not message:
        return
    kind = str(status.get("kind", "info"))
    timeout = float(status.get("timeout_seconds", 5.0))
    glyph = html.escape(floating_status_glyph(kind))
    st.markdown(
        f"""
        <div class="hhs-floating-status hhs-floating-status-kind-{html.escape(kind)}"
             style="--hhs-floating-status-timeout: {timeout:.2f}s;">
          <span class="hhs-floating-status-glyph">{glyph}</span>
          <span class="hhs-floating-status-message">{message}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer_cache_clear_menu_markup() -> str:
    """Return the native HTML footer cleanup menu."""
    clear_param = html.escape(hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM, quote=True)
    app_cache_param = html.escape(
        hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM,
        quote=True,
    )
    app_states_param = html.escape(
        hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM,
        quote=True,
    )
    ai_history_param = html.escape(
        hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM,
        quote=True,
    )
    return f"""
      <details class="hhs-footer-cache-clear-menu">
        <summary class="hhs-footer-cache-clear-trigger"
                 title="Clear application cache"
                 aria-label="Clear application cache">
          <span class="hhs-footer-cache-refresh-glyph">♻</span>
        </summary>
        <form class="hhs-footer-cache-clear-form" method="get">
          <input type="hidden" name="{clear_param}" value="1">
          <label>
            <input type="checkbox" name="{app_cache_param}" value="1">
            <span>Clear application cache</span>
          </label>
          <label>
            <input type="checkbox" name="{app_states_param}" value="1">
            <span>Clear application states</span>
          </label>
          <label>
            <input type="checkbox" name="{ai_history_param}" value="1">
            <span>Clear AI history</span>
          </label>
          <button type="submit">OK</button>
        </form>
      </details>
    """.strip()


def render_footer_cache_clear_menu_script() -> None:
    """Close the native footer cleanup menu locally when no option is selected."""
    components.html(
        """
        <script>
          (() => {
            const doc = window.parent.document;
            const form = doc.querySelector(".hhs-footer-cache-clear-form");
            if (!form || form.dataset.emptySubmitGuard === "true") {
              return;
            }
            form.dataset.emptySubmitGuard = "true";
            form.addEventListener("submit", (event) => {
              if (form.querySelector('input[type="checkbox"]:checked')) {
                return;
              }
              event.preventDefault();
              const menu = form.closest(".hhs-footer-cache-clear-menu");
              if (menu) {
                menu.removeAttribute("open");
              }
            });
          })();
        </script>
        """,
        height=0,
        width=0,
    )


def render_footer() -> None:
    """Render the HomeSetup UI footer."""
    version = homesetup_version()
    working_dir = html.escape(footer_working_directory())
    repository_url = html.escape(os.environ.get("HHS_GITHUB_URL", "#"), quote=True)
    working_dir_url = f"?{hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM}=1"
    update_url = f"?{hhs_ui.FOOTER_RUN_UPDATER_QUERY_PARAM}=1"
    shell_version_url = f"?{hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM}=1"
    updater_markup = ""
    if bool(st.session_state.get("updater_update_available", False)):
        updater_markup = (
            f'<a class="hhs-footer-update-link" href="{update_url}" target="_self" '
            'title="Update HomeSetup" aria-label="Update HomeSetup"></a>'
        )
    shell_name = html.escape(os.environ.get("HHS_MY_SHELL", "").strip().upper())
    shell_status_markup = ""
    cache_clear_markup = ""
    if shell_name:
        shell_status_markup = (
            f'<a class="hhs-footer-shell-status" href="{shell_version_url}" '
            f'target="_self" title="Show bash version" aria-label="Show bash version">'
            f'<span class="hhs-footer-glyph"></span>'
            f'<span class="hhs-footer-shell-name">{shell_name}</span></a>'
        )
        cache_clear_markup = (
            f'<span class="hhs-footer-glyph"></span>'
            f"{footer_cache_clear_menu_markup()}"
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
    shell_controls_markup = ""
    if shell_status_markup:
        shell_controls_markup = (
            f'<span class="hhs-footer-shell-group">'
            f"{shell_status_markup}{cache_clear_markup}</span>"
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
          <a class="hhs-footer-logo-link" href="{repository_url}" target="_blank" rel="noopener noreferrer" aria-label="HomeSetup repository">
            <img class="hhs-footer-logo" src="{logo_data_uri}" alt="" aria-hidden="true">
          </a>
          <span class="hhs-footer-version-group">
            <a class="hhs-footer-link hhs-footer-repository-link" href="{repository_url}" target="_blank" rel="noopener noreferrer">HomeSetup - v{version}</a>{updater_markup}
          </span>
          <span class="hhs-footer-glyph"></span>
          <a class="hhs-footer-link hhs-footer-working-dir-link" href="{working_dir_url}" target="_self">Working dir: <span class="hhs-footer-working-dir-value">{working_dir}</span></a>
          {status_group_markup}
        </footer>
        """)
    if shell_name:
        render_footer_cache_clear_menu_script()


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
    try:
        hhs_ui.UI_STATE_FILE.unlink(missing_ok=True)
    except OSError as error:
        push_floating_status(f"Unable to clear application states: {error}", "error")
    for state_key in list(st.session_state):
        if is_persisted_ui_key(str(state_key)):
            st.session_state.pop(state_key, None)


def selected_footer_cleanup_labels(
    clear_application_cache: bool,
    clear_application_states: bool,
    clear_ai_history: bool,
) -> list[str]:
    """Return footer cleanup labels selected in the native popup menu."""
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
    """Apply selected footer cleanup actions from query parameters."""
    labels = selected_footer_cleanup_labels(
        clear_application_cache,
        clear_application_states,
        clear_ai_history,
    )
    if not labels:
        push_floating_status("No cleanup option selected.", "warn")
        return

    failed_labels = []
    if clear_application_cache:
        clear_cached_ui_data_preserving_state(show_status=False)
    if clear_ai_history:
        result = clear_ai_chat_history_data()
        if result.returncode != 0:
            failed_labels.append("AI history")
    if clear_application_states:
        clear_application_state_data()

    if failed_labels:
        push_floating_status(f"Unable to clear {', '.join(failed_labels)}.", "error")
    else:
        push_floating_status(f"Cleared {', '.join(labels)}.", "info")


def remove_footer_cache_clear_query_params() -> None:
    """Remove footer cache clear query parameters from the browser URL."""
    for name in (
        hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM,
    ):
        remove_query_param(name)


def handle_footer_actions() -> None:
    """Run footer actions requested through Streamlit query parameters."""
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
                st.session_state["updater_last_check_epoch"] = time.time()
                st.session_state["updater_last_check_output"] = (
                    output or "HomeSetup update command completed."
                )
            st.session_state["updater_update_available"] = False
            st.session_state["updater_check_context"] = updater_context
            st.session_state["updater_remote_checked_context"] = updater_context
            cache_delete_tag("env")
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
            )
            push_floating_status("HomeSetup update started.", "info")

    if query_param_requested(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM)
        open_footer_working_directory()

    search_result_path = query_param_value(hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM)
    if search_result_path:
        remove_query_param(hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM)
        open_search_result_path(search_result_path)


def render_home_view() -> None:
    """Render the Home informational view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> System</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    home_view = st.segmented_control(
        "Home view",
        options=hhs_ui.HOME_VIEWS,
        default=st.session_state["home_view"],
        format_func=home_view_label,
        key="home_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    if home_view == "System":
        render_home_system_panel()
    elif home_view == "Docker":
        render_home_docker_panel()
    elif home_view == "Tools":
        render_home_tools_panel()
    elif home_view == "SHOPTS":
        render_home_shopts_panel()


def home_view_label(home_view: str) -> str:
    """Return the display label for a Home view key."""
    return hhs_ui.HOME_VIEW_LABELS.get(home_view, home_view)


def render_home_system_panel() -> None:
    """Render system information on the Home view."""
    result = render_cached_command_result(
        build_hhs_sysinfo_command(),
        "Loading system information",
        "system",
        hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to load system information.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or "Unable to load system information.")
        return
    st.markdown(format_hhs_sysinfo_markdown(result.stdout))


def render_home_docker_panel() -> None:
    """Render Docker container and image listings on the Home view."""
    agent_result = render_cached_command_result(
        build_docker_agent_check_command(),
        "Checking Docker agent",
        "docker",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        command_timeout_seconds(),
        "Unable to check Docker agent.",
    )
    if agent_result is None:
        return
    st.session_state["_hhs_docker_agent_is_running"] = agent_result.returncode == 0
    if not docker_agent_is_running():
        render_docker_agent_required_view(docker_agent_failure_message(agent_result))
        return
    containers_result = render_cached_command_result(
        build_docker_ps_command(),
        "Loading Docker containers",
        "docker",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        10,
        "Unable to load Docker containers.",
    )
    if containers_result is None:
        return
    images_result = render_cached_command_result(
        build_docker_images_command(),
        "Loading Docker images",
        "docker",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        10,
        "Unable to load Docker images.",
    )
    if images_result is None:
        return
    # Regression guard for the previous synchronous calls:
    # render_docker_container_table(run_docker_ps())
    # render_docker_image_table(run_docker_images())
    with st.container(key="home_docker_panel"):
        with st.expander("All Containers", expanded=True):
            render_docker_container_table(containers_result)
        with st.expander("Available Images", expanded=True):
            render_docker_image_table(images_result)


def docker_agent_is_running() -> bool:
    """Return whether the last Docker agent check succeeded."""
    return bool(st.session_state.get("_hhs_docker_agent_is_running", False))


def docker_agent_failure_message(result: subprocess.CompletedProcess[str]) -> str:
    """Return the user-facing message for a failed Docker agent check."""
    output = strip_ansi(result.stderr or result.stdout or "").strip()
    if result.returncode == 124 or "timed out" in output.lower():
        return "Docker command timedout"
    return "Docker agent is not running"


def render_docker_agent_required_view(
    message: str = "Docker agent is not running",
) -> None:
    """Render an empty Docker panel when the Docker daemon is unavailable."""
    safe_message = html.escape(message.strip() or "Docker agent is not running")
    st.markdown(
        f"""
        <section class="hhs-remote-connect-required">
          <h2>{safe_message}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_docker_command_table(
    result: subprocess.CompletedProcess[str],
    table_key: str,
    headers: list[str],
    omitted_columns: tuple[str, ...] = (),
    selected_label: Callable[[dict[str, str], int], str] | None = None,
    action_buttons: list[dict[str, object]] | None = None,
    reset_selection: Callable[[], None] | None = None,
) -> None:
    """Render a Docker command result using the shared dataframe component."""
    rows = docker_cli_table_rows(result.stdout, omitted_columns=omitted_columns)
    if result.returncode != 0:
        rows = []
    render_table(
        rows,
        key=table_key,
        empty_hint="Select a row to interact" if rows else "",
        headers=headers,
        table_data=pd.DataFrame(rows, columns=headers),
        selected_label=selected_label,
        action_buttons=action_buttons,
        reset_selection=reset_selection,
        use_container_width=True,
    )


def render_docker_container_table(result: subprocess.CompletedProcess[str]) -> None:
    """Render Docker containers with selected-row container actions."""
    render_docker_command_table(
        result,
        docker_container_table_key(),
        ["CONTAINER ID", "IMAGE", "NAMES", "STATUS", "CREATED AT"],
        omitted_columns=("COMMAND", "PORTS"),
        selected_label=lambda row, _index: (
            f"Selected: {row.get('NAMES') or row.get('CONTAINER ID', '')}"
        ),
        action_buttons=[
            {
                "label": "Start",
                "key_prefix": "docker_container_start_button",
                "help": "Start",
                "on_click": apply_docker_container_action,
                "args": lambda row, _index: ("start", row.get("CONTAINER ID", "")),
                "disabled": lambda row, _index: docker_container_is_up(row),
            },
            {
                "label": "Stop",
                "key_prefix": "docker_container_stop_button",
                "help": "Stop",
                "on_click": apply_docker_container_action,
                "args": lambda row, _index: ("stop", row.get("CONTAINER ID", "")),
                "disabled": lambda row, _index: not docker_container_is_up(row),
            },
            {
                "label": "Remove",
                "key_prefix": "docker_container_remove_button",
                "help": "Remove",
                "on_click": apply_docker_container_action,
                "args": lambda row, _index: ("rm", row.get("CONTAINER ID", "")),
                "disabled": lambda row, _index: docker_container_is_up(row),
            },
        ],
        reset_selection=reset_docker_container_table_selection,
    )


def render_docker_image_table(result: subprocess.CompletedProcess[str]) -> None:
    """Render Docker images with a selected-row image delete action."""
    render_docker_command_table(
        result,
        docker_image_table_key(),
        ["IMAGE ID", "REPOSITORY", "TAG", "SIZE", "CREATED AT"],
        selected_label=lambda row, _index: (
            f"Selected: {row.get('REPOSITORY', '')}:{row.get('TAG', '')}"
        ),
        action_buttons=[
            {
                "label": "Delete",
                "key_prefix": "docker_image_delete_button",
                "help": "Delete",
                "on_click": apply_docker_image_action,
                "args": lambda row, _index: (row.get("IMAGE ID", ""),),
            },
        ],
        reset_selection=reset_docker_image_table_selection,
    )


def home_shopt_is_on(row: dict[str, str]) -> bool:
    """Return whether a shell option row is currently enabled."""
    return row.get("State") == "ON"


def home_shopt_is_off(row: dict[str, str]) -> bool:
    """Return whether a shell option row is currently disabled."""
    return row.get("State") == "OFF"


def tool_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for tool check statuses."""
    value_text = str(value).lower()
    if "not found" in value_text:
        return "color: #ff5555; font-weight: 800;"
    if "not installed" in value_text:
        return "color: #ff5555; font-weight: 800;"
    if "installed" in value_text:
        return "color: #50fa7b; font-weight: 800;"
    if "aliased" in value_text:
        return "color: #8be9fd; font-weight: 800;"
    if "function" in value_text:
        return "color: #bd93f9; font-weight: 800;"
    return "color: #f8f8f2; font-weight: 800;"


def styled_tool_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return tool rows with styled Status cells."""
    dataframe = pd.DataFrame(rows)
    styler = dataframe.style
    if "Status" in dataframe:
        styler = styler.map(tool_status_cell_style, subset=["Status"])
    return styler


def shopt_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for shell option statuses."""
    value_text = str(value).lower()
    if "off" in value_text:
        return "color: #ff5555; font-weight: 800;"
    if "on" in value_text:
        return "color: #50fa7b; font-weight: 800;"
    return "color: #f8f8f2; font-weight: 800;"


def styled_shopt_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return shell option rows with styled Status cells."""
    dataframe = pd.DataFrame(rows)
    styler = dataframe.style
    if "Status" in dataframe:
        styler = styler.map(shopt_status_cell_style, subset=["Status"])
    return styler


def home_tool_status_text(row: dict[str, str]) -> str:
    """Return a normalized Home tool status for action button decisions."""
    return str(row.get("Status", "")).lower()


def home_tool_is_installed(row: dict[str, str]) -> bool:
    """Return whether a Home tool row is currently installed."""
    status = home_tool_status_text(row)
    return "installed" in status and "not installed" not in status


def home_tool_is_not_found(row: dict[str, str]) -> bool:
    """Return whether a Home tool row is currently missing."""
    status = home_tool_status_text(row)
    return "not found" in status or "not installed" in status


def home_tool_is_aliased(row: dict[str, str]) -> bool:
    """Return whether a Home tool row resolves through a shell alias."""
    return "aliased" in home_tool_status_text(row)


def selected_item_editing_key(table_key: str | None, selected_index: int) -> str:
    """Return the session key for a selected table row edit mode."""
    safe_key = table_key or "hhs_table"
    return f"{safe_key}_selected_editing_{selected_index}"


def table_component_key(table_key: str | None, suffix: str) -> str:
    """Return a stable Streamlit key for table-adjacent helper components."""
    safe_key = table_key or "hhs_table"
    return f"{safe_key}_{suffix}"


def enable_selected_item_edit(
    editing_key: str, edit_key: str | None = None, edit_value: str = ""
) -> None:
    """Enable inline editing for the current selected table row."""
    st.session_state[editing_key] = True
    if edit_key:
        st.session_state[edit_key] = edit_value


def cancel_selected_item_edit(
    editing_key: str,
    edit_key: str | None = None,
    reset_selection: Callable[[], None] | None = None,
) -> None:
    """Cancel inline editing and clear the current selected table row."""
    st.session_state[editing_key] = False
    if edit_key:
        st.session_state.pop(edit_key, None)
    if reset_selection:
        reset_selection()


def selected_label_parts(text: str) -> tuple[str, str]:
    """Return the selected label and value parts from display text."""
    label, separator, value = text.partition(":")
    if not separator:
        return text, ""
    return f"{label}:", value.strip()


def table_editable_flag(
    editable: bool | Callable[[dict[str, str], int], bool],
    row: dict[str, str],
    row_index: int,
) -> bool:
    """Return whether the selected table row supports inline editing."""
    if callable(editable):
        return bool(editable(row, row_index))
    return bool(editable)


def table_edit_args(
    edit_args: (
        Callable[[dict[str, str], int], tuple[object, ...]] | tuple[object, ...] | None
    ),
    row: dict[str, str],
    row_index: int,
) -> tuple[object, ...]:
    """Return callback args for a selected row edit widget."""
    if callable(edit_args):
        return edit_args(row, row_index)
    return edit_args or ()


def table_edit_key(
    edit_key: Callable[[dict[str, str], int], str] | str | None,
    row: dict[str, str],
    row_index: int,
) -> str:
    """Return the Streamlit key for a selected row edit widget."""
    if callable(edit_key):
        return edit_key(row, row_index)
    return str(edit_key or f"selected_table_edit_value_{row_index}")


def table_edit_value(
    edit_value: Callable[[dict[str, str], int], str] | str | None,
    row: dict[str, str],
    row_index: int,
) -> str:
    """Return the initial value for a selected row edit widget."""
    if callable(edit_value):
        return edit_value(row, row_index)
    if edit_value is not None:
        return str(edit_value)
    return str(row.get("Value", ""))


def render_selected_table_item(
    label: str,
    value: str,
    selected_index: int,
    table_key: str | None,
    editable: bool,
    edit_key: str | None = None,
    edit_value: str = "",
    edit_label: str = "Selected value",
    edit_height: int = hhs_ui.ENV_VALUE_EDITOR_HEIGHT,
    edit_max_chars: int | None = None,
    edit_on_change: Callable[..., None] | None = None,
    edit_args: tuple[object, ...] = (),
    edit_folder_picker: bool = False,
    reset_selection: Callable[[], None] | None = None,
    selected_actions: list[dict[str, object]] | None = None,
) -> None:
    """Render the normalized selected table row summary and optional editor."""
    editing_key = selected_item_editing_key(table_key, selected_index)
    is_editing = bool(st.session_state.get(editing_key, False)) and editable
    if editable and edit_key is not None:
        st.session_state.setdefault(edit_key, edit_value)
    visible_actions = selected_actions or []
    edit_action_count = 1 + len(visible_actions) + int(edit_folder_picker)
    action_weights = [0.035] * edit_action_count

    if is_editing and edit_key is not None:
        columns = st.columns(
            [1, *action_weights],
            vertical_alignment="center",
            gap="small",
            width="stretch",
        )
        with columns[0]:
            st.text_input(
                f"{value}:",
                key=edit_key,
                max_chars=edit_max_chars,
                on_change=edit_on_change,
                placeholder=edit_label,
                args=edit_args,
            )
        action_start_index = 1
        if edit_folder_picker:
            with columns[action_start_index]:
                st.button(
                    "",
                    key=f"{editing_key}_folder_picker_button",
                    help="Select folder",
                    on_click=request_folder_picker,
                    args=(edit_key, edit_value),
                    width="stretch",
                )
            action_start_index += 1
        with columns[action_start_index]:
            st.button(
                "ﰸ",
                key=f"{editing_key}_cancel_button",
                help="Cancel edit",
                on_click=cancel_selected_item_edit,
                args=(editing_key, edit_key, reset_selection),
                width="stretch",
            )
        render_selected_table_actions(
            visible_actions, columns[action_start_index + 1 :], selected_index
        )
        return

    if editable:
        columns = st.columns(
            [1, *action_weights],
            vertical_alignment="center",
            gap="small",
            width="stretch",
        )
        value_col = columns[0]
        action_cols = columns[1:]
    else:
        if visible_actions:
            columns = st.columns(
                [1, *[0.035] * len(visible_actions)],
                vertical_alignment="center",
                gap="small",
                width="stretch",
            )
            value_col = columns[0]
            action_cols = columns[1:]
        else:
            value_col = st.container()
            action_cols = []
    with value_col:
        st.markdown(
            (
                '<span class="hhs-selected-item-line">'
                f'<span class="hhs-selected-item-label">{html.escape(label)}</span>'
                f'<span class="hhs-selected-item-value">{html.escape(value)}</span>'
                "</span>"
            ),
            unsafe_allow_html=True,
        )
    if editable and action_cols:
        with action_cols[0]:
            st.button(
                "",
                key=f"{editing_key}_button",
                help="Edit",
                on_click=enable_selected_item_edit,
                args=(editing_key, edit_key, edit_value),
                width="stretch",
            )
        render_selected_table_actions(visible_actions, action_cols[1:], selected_index)
    elif action_cols:
        render_selected_table_actions(visible_actions, action_cols, selected_index)


def render_selected_table_actions(
    actions: list[dict[str, object]],
    columns: list[object],
    selected_index: int,
) -> None:
    """Render selected-row glyph action buttons beside edit controls."""
    for column, action in zip(columns, actions):
        label = str(action.get("glyph", action.get("label", "")))
        key_prefix = str(action.get("key_prefix", label.lower().replace(" ", "_")))
        with column:
            st.button(
                label,
                disabled=bool(action.get("disabled", False)),
                help=action.get("help") or str(action.get("label", "")),
                key=f"{key_prefix}_{selected_index}_selected",
                on_click=execute_selected_table_action,
                args=(
                    action.get("reset_selection"),
                    action.get("on_click"),
                    tuple(action.get("args", ())),
                ),
                width=str(action.get("width", "stretch")),
            )


def execute_selected_table_action(
    reset_selection: Callable[[], None] | None,
    callback: Callable[..., None] | None,
    callback_args: tuple[object, ...],
) -> None:
    """Run a selected-row action and optionally clear the table selection first."""
    if reset_selection:
        reset_selection()
    if callback:
        callback(*callback_args)


def env_path_aliases() -> list[tuple[str, str]]:
    """Return environment variables that can visually abbreviate absolute paths."""
    aliases = []
    for name, value in os.environ.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            continue
        if not value.startswith(os.sep) or os.pathsep in value or value == os.sep:
            continue
        aliases.append((name, value.rstrip(os.sep)))
    return sorted(aliases, key=lambda item: len(item[1]), reverse=True)


def display_path_value(value: str) -> str:
    """Return a display-only path value with environment-variable prefixes."""
    display_value = value
    for name, path_prefix in env_path_aliases():
        replacement = f"${{{name}}}"
        escaped_prefix = re.escape(path_prefix)
        display_value = re.sub(
            rf"(?<![A-Za-z0-9_.-]){escaped_prefix}(?=$|{re.escape(os.sep)}|[:\s'\"`])",
            replacement,
            display_value,
        )
    return display_value


def display_table_value(value: object) -> object:
    """Return the table-only representation for a row value."""
    if not isinstance(value, str):
        return value
    if os.sep not in value:
        return value
    return display_path_value(value)


def display_table_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Return table rows with visual-only path abbreviations applied."""
    return [
        {name: display_table_value(value) for name, value in row.items()}
        for row in rows
    ]


def table_selection_key_prefixes() -> tuple[str, ...]:
    """Return Streamlit dataframe key prefixes that represent selectable tables."""
    return (
        hhs_ui.AI_MODEL_TABLE_KEY,
        hhs_ui.ALIAS_TABLE_KEY,
        hhs_ui.CMD_TABLE_KEY,
        hhs_ui.DIR_TABLE_KEY,
        hhs_ui.DOCKER_CONTAINER_TABLE_KEY,
        hhs_ui.DOCKER_IMAGE_TABLE_KEY,
        hhs_ui.ENV_TABLE_KEY,
        hhs_ui.HISTORY_COMMAND_TABLE_KEY,
        hhs_ui.HISTORY_DIRECTORY_TABLE_KEY,
        hhs_ui.HOME_SHOPTS_TABLE_KEY,
        hhs_ui.HOME_TOOLS_TABLE_KEY,
        hhs_ui.PATH_TABLE_KEY,
        hhs_ui.PROCESS_TABLE_KEY,
        hhs_ui.SERVICE_TABLE_KEY,
        hhs_ui.SSH_TUNNEL_TABLE_KEY,
    )


def table_selection_widget_key(key: object) -> bool:
    """Return whether a Streamlit session key belongs to a selectable dataframe."""
    key_text = str(key)
    return any(
        key_text == prefix or key_text.startswith(f"{prefix}_")
        for prefix in table_selection_key_prefixes()
    )


def table_selection_rows(selection_state: object) -> tuple[int, ...]:
    """Return selected row indexes from a Streamlit dataframe selection state."""
    selection = getattr(selection_state, "selection", None)
    if selection is None and isinstance(selection_state, dict):
        selection = selection_state.get("selection", selection_state)
    rows = getattr(selection, "rows", None)
    if rows is None and isinstance(selection, dict):
        rows = selection.get("rows")
    if rows is None:
        return ()
    return tuple(int(row) for row in rows)


def table_selection_snapshots() -> dict[str, tuple[int, ...]]:
    """Return remembered dataframe selections keyed by Streamlit widget key."""
    snapshots = st.session_state.setdefault(
        hhs_ui_constants.TABLE_SELECTION_SNAPSHOT_KEY, {}
    )
    if not isinstance(snapshots, dict):
        snapshots = {}
        st.session_state[hhs_ui_constants.TABLE_SELECTION_SNAPSHOT_KEY] = snapshots
    return snapshots


def table_selection_rerun_in_progress() -> bool:
    """Return whether the current rerun was caused by a table row selection."""
    snapshots = table_selection_snapshots()
    for key in st.session_state:
        if not table_selection_widget_key(key):
            continue
        rows = table_selection_rows(st.session_state.get(key))
        previous_rows = tuple(snapshots.get(str(key), ()))
        if rows != previous_rows:
            return True
    return False


def remember_table_selection(key: str | None, selection_state: object) -> None:
    """Remember the latest dataframe selection after a table render."""
    if key is None:
        return
    snapshots = table_selection_snapshots()
    snapshots[str(key)] = table_selection_rows(selection_state)


def scroll_to_table_selection_content(anchor_key: str) -> None:
    """Scroll the browser viewport to the bottom of a selected table row component."""
    selector = f'div[class*="st-key-{anchor_key}"]'
    components.html(
        f"""
        <script>
          const selector = {selector!r};
          const scroll_to_table_selection = () => {{
            const doc = window.parent.document;
            const target = doc.querySelector(selector);
            if (!target) {{
              return;
            }}
            target.scrollIntoView({{
              behavior: "smooth",
              block: "end",
              inline: "nearest"
            }});
          }};
          window.setTimeout(scroll_to_table_selection, 75);
          window.setTimeout(scroll_to_table_selection, 250);
        </script>
        """,
        height=0,
    )


def render_table(
    rows: list[dict[str, str]],
    key: str | None,
    empty_hint: str = "Select a row to interact",
    action_hint: str = "",
    headers: list[str] | None = None,
    checkbox: bool = True,
    height: int | None = None,
    width: str | None = None,
    use_container_width: bool = False,
    hide_index: bool = True,
    table_data: object | None = None,
    row_style: Callable[[pd.Series], list[str]] | None = None,
    selected_label: Callable[[dict[str, str], int], str] | None = None,
    selected_editable: bool | Callable[[dict[str, str], int], bool] = False,
    selected_edit_key: Callable[[dict[str, str], int], str] | str | None = None,
    selected_edit_value: Callable[[dict[str, str], int], str] | str | None = None,
    selected_edit_label: str = "Selected value",
    selected_edit_height: int = hhs_ui.ENV_VALUE_EDITOR_HEIGHT,
    selected_edit_max_chars: int | None = None,
    selected_edit_on_change: Callable[..., None] | None = None,
    selected_edit_args: (
        Callable[[dict[str, str], int], tuple[object, ...]] | tuple[object, ...] | None
    ) = None,
    selected_edit_folder_picker: bool = False,
    reset_selection: Callable[[], None] | None = None,
    selected_action_buttons: list[dict[str, object]] | None = None,
    action_buttons: list[dict[str, object]] | None = None,
    action_column_weights: list[float] | None = None,
    on_select: Callable[[], None] | str = "rerun",
    column_config: dict[str, object] | None = None,
) -> tuple[int | None, dict[str, str] | None]:
    """Render a reusable HomeSetup table and return the selected row."""
    rendered_data = table_data if table_data is not None else display_table_rows(rows)
    if row_style is not None:
        rendered_data = pd.DataFrame(display_table_rows(rows)).style.apply(
            row_style, axis=1
        )

    dataframe_args: dict[str, object] = {"hide_index": hide_index}
    if key is not None:
        dataframe_args["key"] = key
    if headers is not None:
        dataframe_args["column_order"] = headers
    if column_config is not None:
        dataframe_args["column_config"] = column_config
    if height is not None:
        dataframe_args["height"] = table_height(height)
    if use_container_width:
        dataframe_args["use_container_width"] = True
    elif width is not None:
        dataframe_args["width"] = width
    else:
        dataframe_args["width"] = "stretch"
    if checkbox:
        dataframe_args["on_select"] = on_select
        dataframe_args["selection_mode"] = "single-row"

    selection = st.dataframe(rendered_data, **dataframe_args)
    if checkbox:
        remember_table_selection(key, selection)
    if not checkbox:
        return None, None

    selected_rows = selection.selection.rows if selection else []
    if not selected_rows or selected_rows[0] >= len(rows):
        if empty_hint:
            with st.container(key=table_component_key(key, "table_empty_hint")):
                st.caption(empty_hint)
        return None, None

    selected_index = selected_rows[0]
    selected_row = rows[selected_index]
    visible_selected_actions = selected_table_actions(
        selected_action_buttons or [], selected_row, selected_index, reset_selection
    )
    if action_hint:
        with st.container(
            key=table_component_key(key, f"table_action_hint_{selected_index}")
        ):
            st.caption(action_hint)
    if selected_label is not None:
        label = selected_label(selected_row, selected_index)
        selected_item_label, selected_item_value = selected_label_parts(label)
        with st.container(
            key=table_component_key(key, f"table_selected_panel_{selected_index}")
        ):
            render_selected_table_item(
                selected_item_label,
                selected_item_value,
                selected_index,
                key,
                table_editable_flag(selected_editable, selected_row, selected_index),
                edit_key=(
                    table_edit_key(selected_edit_key, selected_row, selected_index)
                    if selected_edit_key is not None
                    else None
                ),
                edit_value=table_edit_value(
                    selected_edit_value, selected_row, selected_index
                ),
                edit_label=selected_edit_label,
                edit_height=selected_edit_height,
                edit_max_chars=selected_edit_max_chars,
                edit_on_change=selected_edit_on_change,
                edit_args=table_edit_args(
                    selected_edit_args, selected_row, selected_index
                ),
                edit_folder_picker=selected_edit_folder_picker,
                reset_selection=reset_selection,
                selected_actions=visible_selected_actions,
            )

    visible_actions = [
        action
        for action in action_buttons or []
        if table_action_visible(action, selected_row, selected_index)
    ]
    if visible_actions:
        with st.container(
            key=table_component_key(key, f"table_actions_{selected_index}")
        ):
            weights = action_column_weights or [1.0] * len(visible_actions)
            columns = st.columns(weights)
            for column, action in zip(columns, visible_actions):
                label = str(action["label"])
                key_prefix = str(
                    action.get("key_prefix", label.lower().replace(" ", "_"))
                )
                with column:
                    st.button(
                        label,
                        disabled=table_action_disabled(
                            action, selected_row, selected_index
                        ),
                        help=action.get("help"),
                        key=f"{key_prefix}_{selected_index}",
                        on_click=action.get("on_click"),
                        args=table_action_args(action, selected_row, selected_index),
                        width=str(action.get("width", "stretch")),
                    )

    anchor_key = table_component_key(key, f"table_selected_bottom_{selected_index}")
    with st.container(key=anchor_key):
        st.markdown(
            '<span class="hhs-table-selected-bottom-anchor"></span>',
            unsafe_allow_html=True,
        )
    scroll_to_table_selection_content(anchor_key)
    return selected_index, selected_row


def selected_table_actions(
    actions: list[dict[str, object]],
    row: dict[str, str],
    index: int,
    reset_selection: Callable[[], None] | None = None,
) -> list[dict[str, object]]:
    """Return selected-row table actions with row-specific values resolved."""
    resolved_actions = []
    for action in actions:
        if not table_action_visible(action, row, index):
            continue
        resolved_action = {
            **action,
            "disabled": table_action_disabled(action, row, index),
            "args": table_action_args(action, row, index),
            "reset_selection": reset_selection,
        }
        resolved_actions.append(resolved_action)
    return resolved_actions


def table_height(height: int) -> int:
    """Return the app table height after applying the global viewport reduction."""
    return max(1, height - hhs_ui.TABLE_HEIGHT_REDUCTION)


def bar_chart_height(height: int = hhs_ui.BAR_CHART_HEIGHT) -> int:
    """Return the app bar chart height after applying the global viewport reduction."""
    return max(1, height - hhs_ui.BAR_CHART_HEIGHT_REDUCTION)


def bar_chart_container_height() -> str:
    """Return the Vega-Lite height mode for browser-aware chart containers."""
    return "container"


def render_bar_chart(
    rows: list[dict[str, object]],
    x: alt.X,
    y: alt.Y,
    tooltip: list[alt.Tooltip],
    color: str = "#ffb86c",
    height: int = hhs_ui.BAR_CHART_HEIGHT,
) -> None:
    """Render a reusable responsive bar chart with app-wide sizing."""
    fallback_height = bar_chart_height(height)
    chart = (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(color=color)
        .encode(
            x=x,
            y=y,
            tooltip=tooltip,
        )
        .properties(height=bar_chart_container_height())
        .configure_view(continuousHeight=fallback_height)
    )
    st.altair_chart(chart, width="stretch")


def table_action_visible(
    action: dict[str, object], row: dict[str, str], index: int
) -> bool:
    """Return whether a renderTable action button should be visible."""
    visible = action.get("visible", True)
    return bool(visible(row, index) if callable(visible) else visible)


def table_action_disabled(
    action: dict[str, object], row: dict[str, str], index: int
) -> bool:
    """Return whether a renderTable action button should be disabled."""
    disabled = action.get("disabled", False)
    return bool(disabled(row, index) if callable(disabled) else disabled)


def table_action_args(
    action: dict[str, object], row: dict[str, str], index: int
) -> tuple[object, ...]:
    """Return callback arguments for a renderTable action button."""
    args = action.get("args", ())
    if callable(args):
        args = args(row, index)
    return tuple(args) if isinstance(args, tuple | list) else (args,)


def render_table_controls_panel(
    render_controls: Callable[[], TableControlsResult],
) -> TableControlsResult:
    """Render table filters and entry controls inside the shared foldable panel."""
    with st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True):
        return render_controls()


def clear_table_other_filter(other_key: str) -> None:
    """Clear a typed Other table filter and persist the updated UI state."""
    st.session_state[other_key] = ""
    save_ui_state()


def render_table_filter_controls(
    options: tuple[str, ...],
    key: str,
    other_key: str,
    columns: list[float],
    index: int = 0,
    other_options: tuple[str, ...] = ("Other", "Others"),
    placeholder: str = "Type filter text",
) -> tuple[str, str]:
    """Render normalized table filter controls and return the selected filter text."""
    filter_col, other_filter_col, clear_filter_col = st.columns(
        [*columns, 0.18], vertical_alignment="center", gap="small"
    )
    with filter_col:
        selected_filter = st.radio(
            "Table filter",
            options,
            horizontal=True,
            index=index,
            key=key,
            label_visibility="collapsed",
            on_change=save_ui_state,
        )

    other_filter = ""
    if selected_filter in other_options:
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key=other_key,
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder=placeholder,
            )
        with clear_filter_col:
            st.button(
                "",
                key=f"{other_key}_clear",
                help="Clear filter text",
                on_click=clear_table_other_filter,
                args=(other_key,),
                disabled=not bool(str(other_filter)),
                width="content",
            )
    return selected_filter, other_filter


def render_env_add_controls() -> None:
    """Render the environment variable new-entry controls."""
    render_named_value_add_controls(
        "env",
        "Name",
        "Value",
        "Custom Variable",
        "Optional value",
        apply_env_add_form_value,
    )


def render_named_value_add_controls(
    key_prefix: str,
    name_label: str,
    value_label: str,
    name_placeholder: str,
    value_placeholder: str,
    on_submit: Callable[[], None],
    value_folder_picker: bool = False,
) -> None:
    """Render Enter-submitted Name and Value controls for a config listing."""
    # Layout reference for the paired name/value path picker:
    # name_col, value_col, _spacer_col, folder_col = st.columns(
    #     [1.25, 4.05, 0.012, 0.15], vertical_alignment="center"
    # )
    if value_folder_picker:
        form_col, folder_col = st.columns([1, 0.035], vertical_alignment="center")
    else:
        form_col = st.container()
        folder_col = None
    with form_col:
        with st.form(f"{key_prefix}_add_form", border=False):
            name_col, value_col = st.columns([1.25, 4.2], vertical_alignment="center")
            with name_col:
                st.text_input(
                    name_label,
                    key=f"{key_prefix}_add_name",
                    placeholder=name_placeholder,
                )
            with value_col:
                st.text_input(
                    value_label,
                    key=f"{key_prefix}_add_value",
                    placeholder=value_placeholder,
                )
            st.form_submit_button(
                "Add",
                key=f"{key_prefix}_add_submit",
                on_click=on_submit,
            )
    if folder_col is not None:
        with folder_col:
            st.button(
                "",
                key=f"{key_prefix}_folder_picker_button",
                help="Select folder",
                on_click=request_folder_picker,
                args=(f"{key_prefix}_add_value", value_placeholder),
                width="stretch",
            )


def render_value_add_controls(
    key_prefix: str,
    value_label: str,
    value_placeholder: str,
    on_submit: Callable[[], None],
    value_folder_picker: bool = False,
) -> None:
    """Render an Enter-submitted Value control for a config listing."""
    if value_folder_picker:
        form_col, folder_col = st.columns([1, 0.035], vertical_alignment="center")
    else:
        form_col = st.container()
        folder_col = None
    with form_col:
        with st.form(f"{key_prefix}_add_form", border=False):
            st.text_input(
                value_label,
                key=f"{key_prefix}_add_value",
                placeholder=value_placeholder,
            )
            st.form_submit_button(
                "Add",
                key=f"{key_prefix}_add_submit",
                on_click=on_submit,
            )
    if folder_col is not None:
        with folder_col:
            st.button(
                "",
                key=f"{key_prefix}_folder_picker_button",
                help="Select folder",
                on_click=request_folder_picker,
                args=(f"{key_prefix}_add_value", value_placeholder),
                width="stretch",
            )


def render_path_add_controls() -> None:
    """Render the PATH new-entry controls."""
    render_value_add_controls(
        "path",
        "Path",
        "Custom path",
        apply_path_add_form_value,
        value_folder_picker=True,
    )


def render_dir_add_controls() -> None:
    """Render the saved directory new-entry controls."""
    render_named_value_add_controls(
        "dir",
        "Name",
        "Path",
        "Directory alias",
        "Directory path",
        apply_dir_add_form_value,
        value_folder_picker=True,
    )


def render_cmd_add_controls() -> None:
    """Render the saved command new-entry controls."""
    render_named_value_add_controls(
        "cmd",
        "Name",
        "Command",
        "Command alias",
        "Command value",
        apply_cmd_add_form_value,
    )


def render_alias_add_controls() -> None:
    """Render the alias new-entry controls."""
    render_named_value_add_controls(
        "alias",
        "Name",
        "Expression",
        "Alias",
        "Alias expression",
        apply_alias_add_form_value,
    )


def render_home_tools_panel() -> None:
    """Render HomeSetup development tool checks on the Home view."""
    execute_pending_home_tool_action()
    home_tool_action_dialog_opened = render_home_tool_action_dialog()
    if not home_tool_action_dialog_opened:
        render_home_tool_tldr_dialog()
    render_background_job_status(HOME_TOOL_ACTION_JOB)

    result = render_cached_command_result(
        build_hhs_tools_command(),
        "Loading tool checks",
        "tools",
        hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to load tool checks.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to load tool checks.")
        return
    rows = parse_rows_cached("tools", result.stdout, parse_hhs_tools)
    if not rows:
        st.caption("No tool checks found.")
        return
    tools_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.HOME_TOOLS_FILTERS,
            "home_tools_filter",
            "home_tools_other_filter",
            hhs_ui.FIVE_OPTION_FILTER_COLUMNS,
        )
    )
    filtered_rows = filter_tool_rows(rows, tools_filter, other_filter)
    if not filtered_rows:
        st.caption("No tool checks match the current filter.")
        return
    render_table(
        filtered_rows,
        key=home_tools_table_key(),
        checkbox=True,
        selected_label=lambda row, _index: f"Selected: {row.get('Tool', '')}",
        table_data=styled_tool_rows(filtered_rows),
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        action_buttons=[
            {
                "label": "Install",
                "key_prefix": "home_tool_install_button",
                "on_click": apply_selected_tool_action,
                "disabled": lambda row, _index: home_tool_is_installed(row),
                "args": lambda row, _index: ("install", row.get("Tool", "")),
            },
            {
                "label": "Uninstall",
                "key_prefix": "home_tool_uninstall_button",
                "on_click": apply_selected_tool_action,
                "disabled": lambda row, _index: home_tool_is_not_found(row),
                "args": lambda row, _index: ("uninstall", row.get("Tool", "")),
            },
            {
                "label": "Reinstall",
                "key_prefix": "home_tool_reinstall_button",
                "on_click": apply_selected_tool_action,
                "disabled": lambda row, _index: home_tool_is_not_found(row),
                "args": lambda row, _index: ("reinstall", row.get("Tool", "")),
            },
            {
                "label": "TLDR",
                "key_prefix": "home_tool_tldr_button",
                "on_click": apply_selected_tool_tldr,
                "args": lambda row, _index: (row.get("Tool", ""),),
            },
        ],
    )


def render_home_shopts_panel() -> None:
    """Render shell options on the Home view."""
    result = render_cached_command_result(
        build_hhs_shopt_command(),
        "Loading shell options",
        "shopt",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load shell options.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to load shell options.")
        return
    rows = parse_rows_cached("shopt", result.stdout, parse_hhs_shopt)
    if not rows:
        st.caption("No shell options found.")
        return
    shopts_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.SHOPTS_FILTERS,
            "home_shopts_filter",
            "home_shopts_other_filter",
            hhs_ui.FOUR_OPTION_FILTER_COLUMNS,
        )
    )
    filtered_rows = filter_shopt_rows(rows, shopts_filter, other_filter)
    if not filtered_rows:
        st.caption("No shell options match the current filter.")
        return
    render_table(
        filtered_rows,
        key=home_shopts_table_key(),
        checkbox=True,
        headers=["Status", "Option", "Description"],
        selected_label=lambda row, _index: (
            f"Selected: {row.get('Option', '')} ({row.get('State', '')})"
        ),
        table_data=styled_shopt_rows(filtered_rows),
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        reset_selection=reset_home_shopts_table_selection,
        action_buttons=[
            {
                "label": " Turn ON",
                "key_prefix": "home_shopt_set_button",
                "on_click": apply_home_shopt_action,
                "disabled": lambda row, _index: home_shopt_is_on(row),
                "args": lambda row, _index: ("set", row.get("Option", "")),
            },
            {
                "label": " Turn OFF",
                "key_prefix": "home_shopt_unset_button",
                "on_click": apply_home_shopt_action,
                "disabled": lambda row, _index: home_shopt_is_off(row),
                "args": lambda row, _index: ("unset", row.get("Option", "")),
            },
        ],
        action_column_weights=[1, 1],
    )


def render_document_view() -> None:
    """Render the selected HomeSetup document."""
    document_key = str(st.session_state.get(hhs_ui.DOCUMENT_SELECTED_KEY, "README"))
    if document_key == "TERMINAL":
        render_terminal_document_view()
        return
    title, document = document_details(document_key)
    st.markdown(
        f"""
        <section class="hhs-view-heading">
          <h2>{html.escape(title)}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if not document.is_file():
        st.error(f"Document not found: {document}")
        return
    st.markdown(document.read_text(encoding="utf-8"), unsafe_allow_html=True)


def render_terminal_document_view() -> None:
    """Render the ttyd-backed terminal document view."""
    title = terminal_document_title()
    st.markdown(
        f"""
        <section class="hhs-view-heading">
          <h2> {html.escape(title)}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    initialize_terminal_session_state()
    ttyd_url = ensure_ttyd_session()
    if not ttyd_url:
        render_ttyd_unavailable()
        return
    render_ttyd_terminal_frame(ttyd_url)


def ttyd_binary() -> str:
    """Return the ttyd executable path when it is available to the UI process."""
    discovered = shutil.which("ttyd")
    if discovered:
        return discovered
    for candidate in (
        os.environ.get("TTYD", ""),
        "/opt/homebrew/bin/ttyd",
        "/opt/homebrew/opt/ttyd/bin/ttyd",
        "/usr/local/bin/ttyd",
        "/usr/local/opt/ttyd/bin/ttyd",
        "/usr/bin/ttyd",
    ):
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return ""


def ttyd_font_family() -> str:
    """Return the terminal font family backed by the bundled font asset."""
    if ttyd_font_file().is_file():
        return hhs_ui.APP_FONT_FAMILY
    return "monospace"


def ttyd_font_file() -> Path:
    """Return the preferred terminal font file for ttyd's isolated iframe."""
    if hhs_ui.APP_FONT_FILE.is_file():
        return hhs_ui.APP_FONT_FILE
    otf_file = (
        Path(os.environ.get("HHS_HOME", hhs_ui.APP_DIR.parents[4]))
        / "assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.otf"
    )
    if otf_file.is_file():
        return otf_file
    return hhs_ui.APP_FONT_FILE


def ttyd_font_mime_type(font_file: Path) -> str:
    """Return the MIME type for the ttyd terminal font file."""
    if font_file.suffix.lower() == ".otf":
        return "font/otf"
    return "font/woff2"


def ttyd_font_format(font_file: Path) -> str:
    """Return the CSS font format for the ttyd terminal font file."""
    if font_file.suffix.lower() == ".otf":
        return "opentype"
    return "woff2"


def ttyd_index_signature(binary: str, event_url: str = "") -> str:
    """Return a stable cache signature for the ttyd index and terminal font."""
    font_file = ttyd_font_file()
    parts = ["hhs-ttyd-font-index-v10-exit-v1", binary, event_url]
    for path in (Path(binary), font_file):
        try:
            stat = path.stat()
            parts.append(f"{path}:{stat.st_mtime_ns}:{stat.st_size}")
        except OSError:
            parts.append(f"{path}:missing")
    return "|".join(parts)


def ttyd_index_is_current(binary: str, event_url: str) -> bool:
    """Return whether the generated ttyd index matches the current font and binary."""
    try:
        first_line = hhs_ui.TTYD_INDEX_FILE.read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines()[0]
    except (IndexError, OSError):
        return False
    return first_line == f"<!-- {ttyd_index_signature(binary, event_url)} -->"


def fetch_ttyd_default_index(binary: str) -> str:
    """Fetch the default HTML index served by the installed ttyd binary."""
    port = allocate_ttyd_port()
    process = subprocess.Popen(
        [
            binary,
            "-i",
            hhs_ui.TTYD_HOST,
            "-p",
            str(port),
            "/bin/sh",
            "-lc",
            "sleep 30",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    try:
        url = f"http://{hhs_ui.TTYD_HOST}:{port}/"
        for _ in range(20):
            if not ttyd_process_is_running(process):
                return ""
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    return response.read().decode("utf-8")
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        return ""
    finally:
        stop_process(process)


def ttyd_font_face_style() -> str:
    """Return the CSS that loads the HomeSetup terminal font inside ttyd."""
    font_file = ttyd_font_file()
    if not font_file.is_file():
        return ""
    encoded_font = b64encode(font_file.read_bytes()).decode("ascii")
    family = html.escape(hhs_ui.APP_FONT_FAMILY, quote=True)
    mime_type = ttyd_font_mime_type(font_file)
    font_format = ttyd_font_format(font_file)
    return (
        "<style>"
        "@font-face{"
        f'font-family:"{family}";'
        f'src:url("data:{mime_type};base64,{encoded_font}") format("{font_format}");'
        "font-weight:normal;"
        "font-style:normal;"
        "font-display:block;"
        "}"
        "html,body,#terminal,.terminal,.xterm,.xterm-viewport,.xterm-screen,.xterm-rows{"
        f'font-family:"{family}",monospace!important;'
        "}"
        "html,body,#terminal,.terminal,.xterm,.xterm-viewport{"
        "background:#000000!important;"
        "}"
        ".xterm .xterm-screen,.xterm .xterm-rows{"
        "background:transparent!important;"
        "}"
        "#terminal,.terminal,.xterm{"
        "box-sizing:border-box!important;"
        "padding:0!important;"
        "}"
        ".xterm .xterm-viewport{"
        "left:0!important;"
        "top:0!important;"
        "right:0!important;"
        "bottom:0!important;"
        "scrollbar-gutter:stable!important;"
        "}"
        ".xterm .xterm-viewport::-webkit-scrollbar{"
        "background:#000000!important;"
        "width:12px!important;"
        "}"
        ".xterm .xterm-viewport::-webkit-scrollbar-track{"
        "background:#000000!important;"
        "}"
        ".xterm .xterm-viewport::-webkit-scrollbar-thumb{"
        "background:#6b7280!important;"
        "border:2px solid #000000!important;"
        "border-radius:999px!important;"
        "}"
        "</style>"
    )


def ttyd_bridge_script(event_url: str) -> str:
    """Return JavaScript that bridges ttyd terminal events back to the UI."""
    return (
        "<script>"
        "(()=>{"
        f"const eventUrl={json.dumps(event_url)};"
        "const prefix='HHS_TTYD_EVENT|';"
        "const decode=(value)=>{try{return decodeURIComponent(escape(atob(value)));}catch(_error){return '';}};"
        "const parse=(data)=>{"
        "if(!data||!data.startsWith(prefix)){return null;}"
        "const parts=data.split('|');"
        "if(parts.length<6){return null;}"
        "return {type:parts[1],command:parts[2],status:Number(parts[3]||0),cwd:decode(parts[4]),time:Number(parts[5]||Date.now())};"
        "};"
        "const publish=(event)=>{"
        "if(!event){return;}"
        "try{window.parent.postMessage({type:'hhs-ttyd-event',event},'*');}catch(_error){}"
        "try{fetch(eventUrl,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(event),keepalive:true}).catch(()=>{});}catch(_error){}"
        "};"
        "const install=()=>{"
        "const term=window.term;"
        "if(!term||!term.parser||window.__hhsTtydBridgeInstalled){return !!window.__hhsTtydBridgeInstalled;}"
        "window.__hhsTtydBridgeInstalled=true;"
        "term.parser.registerOscHandler(777,(data)=>{const event=parse(String(data||''));if(event){publish(event);return true;}return false;});"
        "window.addEventListener('keydown',(event)=>{"
        "if((event.metaKey||event.ctrlKey)&&String(event.key||'').toLowerCase()==='k'){"
        "event.preventDefault();event.stopPropagation();"
        "if(window.term&&typeof window.term.clear==='function'){window.term.clear();}"
        "}"
        "},true);"
        "return true;"
        "};"
        "if(!install()){const timer=window.setInterval(()=>{if(install()){window.clearInterval(timer);}},100);}"
        "})();"
        "</script>"
    )


def inject_ttyd_font(index_html: str, binary: str, event_url: str) -> str:
    """Return ttyd index HTML with HomeSetup terminal customizations injected."""
    signature = f"<!-- {ttyd_index_signature(binary, event_url)} -->\n"
    style = ttyd_font_face_style()
    script = ttyd_bridge_script(event_url)
    injection = style + script
    if not injection:
        return f"{signature}{index_html}"
    if "</head>" in index_html:
        return f"{signature}{index_html.replace('</head>', injection + '</head>', 1)}"
    return f"{signature}{injection}{index_html}"


def ensure_ttyd_index_file(binary: str, event_url: str) -> str:
    """Create or reuse the generated ttyd index that embeds the terminal font."""
    if ttyd_index_is_current(binary, event_url):
        return str(hhs_ui.TTYD_INDEX_FILE)
    index_html = fetch_ttyd_default_index(binary)
    if not index_html:
        return ""
    patched_index = inject_ttyd_font(index_html, binary, event_url)
    try:
        hhs_ui.TTYD_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = hhs_ui.TTYD_INDEX_FILE.with_suffix(".tmp")
        temporary_file.write_text(patched_index, encoding="utf-8")
        temporary_file.replace(hhs_ui.TTYD_INDEX_FILE)
        return str(hhs_ui.TTYD_INDEX_FILE)
    except OSError:
        return ""


def stop_process(process: object) -> None:
    """Terminate a process object if it is still running."""
    if not ttyd_process_is_running(process):
        return
    process_group = 0
    process_id = int(getattr(process, "pid", 0) or 0)
    if process_id:
        try:
            process_group = os.getpgid(process_id)
        except OSError:
            process_group = 0
    try:
        if process_group and process_group != os.getpgrp():
            os.killpg(process_group, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        if process_group and process_group != os.getpgrp():
            os.killpg(process_group, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=1)
    except OSError:
        return


def ttyd_process_is_running(process: object) -> bool:
    """Return whether a stored ttyd process is still alive."""
    if not hasattr(process, "poll"):
        return False
    try:
        return process.poll() is None
    except OSError:
        return False


def allocate_ttyd_port() -> int:
    """Return an available local TCP port for a ttyd session."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((hhs_ui.TTYD_HOST, 0))
        return int(server_socket.getsockname()[1])


def ttyd_session_signature(cwd: str, binary: str, event_url: str) -> str:
    """Return the session signature used to decide whether ttyd must restart."""
    host = connected_ssh_host()
    mode = f"ssh:{host}" if host else "local"
    return f"{mode}:{cwd}:{ttyd_index_signature(binary, event_url)}"


def ttyd_process_working_directory(cwd: str) -> str:
    """Return the local working directory used to launch the ttyd process."""
    if connected_ssh_host():
        return os.getcwd()
    if cwd and os.path.isdir(cwd):
        return cwd
    return os.getcwd()


def ttyd_shell_hook_script() -> str:
    """Return the Bash startup script that emits ttyd command hook events."""
    return r"""
if [[ -r "${HOME}/.bash_profile" ]]; then
  . "${HOME}/.bash_profile"
elif [[ -r "${HOME}/.bash_login" ]]; then
  . "${HOME}/.bash_login"
elif [[ -r "${HOME}/.profile" ]]; then
  . "${HOME}/.profile"
elif [[ -r "${HOME}/.bashrc" ]]; then
  . "${HOME}/.bashrc"
fi

__hhs_ttyd_base64() {
  if command -v base64 >/dev/null 2>&1; then
    printf "%s" "$1" | base64 | tr -d "\n"
  elif command -v python3 >/dev/null 2>&1; then
    HHS_TTYD_VALUE="$1" python3 - <<'PY'
import base64
import os
print(base64.b64encode(os.environ.get("HHS_TTYD_VALUE", "").encode()).decode(), end="")
PY
  else
    printf "%s" "$1"
  fi
}

__hhs_ttyd_emit_event() {
  local event_type="${1:-cwd}"
  local command_name="${2:-prompt}"
  local status_code="${3:-0}"
  local cwd_payload
  local event_time
  cwd_payload="$(__hhs_ttyd_base64 "${PWD}")"
  event_time="$(date +%s%3N 2>/dev/null || date +%s)"
  printf "\033]777;HHS_TTYD_EVENT|%s|%s|%s|%s|%s\007" \
    "${event_type}" "${command_name}" "${status_code}" "${cwd_payload}" "${event_time}"
}

__hhs_ttyd_emit_cwd() {
  local command_name="${1:-prompt}"
  local status_code="${2:-0}"
  __hhs_ttyd_emit_event "cwd" "${command_name}" "${status_code}"
}

__hhs_ttyd_emit_exit() {
  local status_code="${1:-0}"
  __hhs_ttyd_emit_event "exit" "exit" "${status_code}"
}

__hhs_ttyd_last_pwd="${PWD}"
__hhs_ttyd_emit_cwd "init" 0

cd() {
  builtin cd "$@"
  local status_code="$?"
  __hhs_ttyd_last_pwd="${PWD}"
  __hhs_ttyd_emit_cwd "cd" "${status_code}"
  return "${status_code}"
}

pushd() {
  builtin pushd "$@"
  local status_code="$?"
  __hhs_ttyd_last_pwd="${PWD}"
  __hhs_ttyd_emit_cwd "pushd" "${status_code}"
  return "${status_code}"
}

popd() {
  builtin popd "$@"
  local status_code="$?"
  __hhs_ttyd_last_pwd="${PWD}"
  __hhs_ttyd_emit_cwd "popd" "${status_code}"
  return "${status_code}"
}

__hhs_ttyd_after_command() {
  local status_code="$?"
  if [[ "${PWD}" != "${__hhs_ttyd_last_pwd}" ]]; then
    __hhs_ttyd_last_pwd="${PWD}"
    __hhs_ttyd_emit_cwd "prompt" "${status_code}"
  fi
  return "${status_code}"
}

if [[ -n "${PROMPT_COMMAND:-}" ]]; then
  PROMPT_COMMAND="__hhs_ttyd_after_command; ${PROMPT_COMMAND}"
else
  PROMPT_COMMAND="__hhs_ttyd_after_command"
fi

trap '__hhs_ttyd_emit_exit "$?"' EXIT
    """


def build_ttyd_hooked_bash_command(cwd: str, shell: str = "bash") -> str:
    """Build a Bash command that starts an interactive shell with ttyd hooks."""
    startup_script = ttyd_shell_hook_script()
    safe_cwd = shlex.quote(cwd)
    safe_shell = shlex.quote(shell)
    safe_script = shlex.quote(startup_script)
    return (
        f"cd {safe_cwd} 2>/dev/null || cd; "
        f"exec {safe_shell} --rcfile <(printf %s {safe_script}) -i"
    )


def ssh_config_option_args() -> list[str]:
    """Return OpenSSH config arguments for subprocess list commands."""
    return ["-F", str(Path.home() / ".ssh/config")]


def build_ttyd_remote_command(host: str, cwd: str) -> list[str]:
    """Build the SSH command run by ttyd for remote terminal sessions."""
    remote_command = build_ttyd_hooked_bash_command(cwd)
    ssh_options = [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "ConnectionAttempts=1",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "ServerAliveCountMax=1",
        "-o",
        f"ControlPath={ssh_control_path(host)}",
    ]
    return [
        "ssh",
        "-tt",
        *ssh_config_option_args(),
        *ssh_options,
        host,
        f"bash -lc {shlex.quote(remote_command)}",
    ]


def build_ttyd_shell_command(cwd: str) -> list[str]:
    """Build the shell command served by ttyd for the active execution host."""
    host = connected_ssh_host()
    if host:
        return build_ttyd_remote_command(host, cwd)
    return [RUN_SHELL, "-lc", build_ttyd_hooked_bash_command(cwd, RUN_SHELL)]


def build_ttyd_command(
    binary: str, port: int, cwd: str, index_file: str = ""
) -> list[str]:
    """Build the ttyd server command for the active terminal session."""
    command = [
        binary,
        "-W",
        "-q",
        "-i",
        hhs_ui.TTYD_HOST,
        "-p",
        str(port),
        "-w",
        ttyd_process_working_directory(cwd),
        "-t",
        f"fontFamily={ttyd_font_family()}, monospace",
        "-t",
        'theme={"background":"#000000"}',
        "-t",
        "fontSize=14",
        "-t",
        "cursorStyle=underline",
        "-t",
        "cursorBlink=true",
        "-t",
        "disableLeaveAlert=true",
        "-t",
        "disableResizeOverlay=true",
        "-t",
        "titleFixed=HomeSetup Terminal",
    ]
    if index_file:
        command.extend(("-I", index_file))
    command.extend(build_ttyd_shell_command(cwd))
    return command


def stop_ttyd_session() -> None:
    """Stop any ttyd process owned by the current Streamlit session."""
    process = st.session_state.pop(hhs_ui_constants.TTYD_PROCESS_KEY, None)
    st.session_state.pop(hhs_ui_constants.TTYD_PORT_KEY, None)
    st.session_state.pop(hhs_ui_constants.TTYD_SIGNATURE_KEY, None)
    stop_process(process)


def ensure_ttyd_session() -> str:
    """Start or reuse a ttyd server and return the iframe URL."""
    binary = ttyd_binary()
    if not binary:
        stop_ttyd_session()
        return ""
    cwd = footer_working_directory()
    event_url = ttyd_event_url()
    update_browser_cleanup_registration()
    signature = ttyd_session_signature(cwd, binary, event_url)
    process = st.session_state.get(hhs_ui_constants.TTYD_PROCESS_KEY)
    port = st.session_state.get(hhs_ui_constants.TTYD_PORT_KEY)
    if (
        ttyd_process_is_running(process)
        and isinstance(port, int)
        and st.session_state.get(hhs_ui_constants.TTYD_SIGNATURE_KEY) == signature
    ):
        return f"http://{hhs_ui.TTYD_HOST}:{port}/"

    stop_ttyd_session()
    port = allocate_ttyd_port()
    index_file = ensure_ttyd_index_file(binary, event_url)
    command = build_ttyd_command(binary, port, cwd, index_file)
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    time.sleep(0.15)
    if not ttyd_process_is_running(process):
        return ""
    st.session_state[hhs_ui_constants.TTYD_PROCESS_KEY] = process
    st.session_state[hhs_ui_constants.TTYD_PORT_KEY] = port
    st.session_state[hhs_ui_constants.TTYD_SIGNATURE_KEY] = signature
    update_browser_cleanup_registration()
    return f"http://{hhs_ui.TTYD_HOST}:{port}/"


def render_ttyd_terminal_frame(ttyd_url: str) -> None:
    """Render the active ttyd terminal in an iframe."""
    iframe_height = int(hhs_ui.TTYD_IFRAME_HEIGHT)
    st.markdown(
        f"""
        <div
          id="hhs-ttyd-terminal-anchor"
          class="hhs-ttyd-terminal-shell"
          style="--hhs-ttyd-max-height: {iframe_height}px;"
        >
          <div class="hhs-ttyd-terminal-placeholder"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    components.html(
        f"""
        <script>
          (() => {{
            const doc = window.parent.document;
            const src = {json.dumps(ttyd_url)};
            const frameId = "hhs-persistent-ttyd-frame";
            const anchor = doc.getElementById("hhs-ttyd-terminal-anchor");
            if (!anchor) {{
              return;
            }}
            let frame = doc.getElementById(frameId);
            if (!frame || frame.dataset.src !== src) {{
              if (frame) {{
                frame.remove();
              }}
              frame = doc.createElement("iframe");
              frame.id = frameId;
              frame.dataset.src = src;
              frame.src = src;
              frame.title = "HomeSetup Terminal";
              frame.loading = "eager";
              frame.className = "hhs-ttyd-terminal-frame hhs-ttyd-terminal-frame-persistent";
              frame.style.position = "fixed";
              frame.style.border = "0";
              frame.style.zIndex = "20";
              frame.style.display = "none";
              doc.body.appendChild(frame);
            }}
            const syncFrame = () => {{
              const rect = anchor.getBoundingClientRect();
              const inset = 5;
              const visible = rect.width > 0 && rect.height > 0;
              frame.style.display = visible ? "block" : "none";
              frame.style.left = `${{rect.left + inset}}px`;
              frame.style.top = `${{rect.top + inset}}px`;
              frame.style.width = `${{Math.max(0, rect.width - (inset * 2))}}px`;
              frame.style.height = `${{Math.max(0, rect.height - (inset * 2))}}px`;
            }};
            if (window.parent.__hhsTtydFrameSyncCleanup) {{
              window.parent.__hhsTtydFrameSyncCleanup();
            }}
            const observer = "ResizeObserver" in window.parent
              ? new window.parent.ResizeObserver(syncFrame)
              : null;
            if (observer) {{
              observer.observe(anchor);
            }}
            window.parent.addEventListener("resize", syncFrame);
            window.parent.addEventListener("scroll", syncFrame, true);
            window.parent.__hhsTtydFrameSyncCleanup = () => {{
              if (observer) {{
                observer.disconnect();
              }}
              window.parent.removeEventListener("resize", syncFrame);
              window.parent.removeEventListener("scroll", syncFrame, true);
            }};
            syncFrame();
          }})();
        </script>
        """,
        height=1,
        width=1,
    )


def render_ttyd_terminal_frame_cleanup_script() -> None:
    """Remove the browser-persistent ttyd iframe when Terminal is inactive."""
    components.html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsTtydFrameSyncCleanup) {
              parentWindow.__hhsTtydFrameSyncCleanup();
              parentWindow.__hhsTtydFrameSyncCleanup = null;
            }
            if (parentWindow.__hhsTtydExitBackHandler) {
              parentWindow.removeEventListener("message", parentWindow.__hhsTtydExitBackHandler);
              parentWindow.__hhsTtydExitBackHandler = null;
            }
            const frame = doc.getElementById("hhs-persistent-ttyd-frame");
            if (frame) {
              frame.remove();
            }
          })();
        </script>
        """,
        height=1,
        width=1,
    )


def render_ttyd_unavailable() -> None:
    """Render a dependency message when ttyd cannot be started."""
    st.error("ttyd is not available to the UI process.")


def cleanup_session_resources(token: str) -> None:
    """Close ttyd and SSH resources registered for a browser session token."""
    entry = TTYD_CLEANUP_REGISTRY.pop(token, None)
    if not entry:
        return
    stop_process(entry.get("ttyd_process"))
    ssh_host = str(entry.get("ssh_host", "")).strip()
    if ssh_host and not selected_host_is_local(ssh_host):
        run_cleanup_bash_command(build_ssh_disconnect_command(ssh_host), 10)
        clear_registered_ssh_connection()


def schedule_cleanup_session_resources(token: str) -> None:
    """Close browser-session resources without blocking the unload request."""
    clean_token = token.strip()
    if not clean_token:
        return
    thread = threading.Thread(
        target=cleanup_session_resources,
        args=(clean_token,),
        name=f"hhs-ttyd-session-cleanup-{clean_token[:8]}",
        daemon=True,
    )
    thread.start()


def store_ttyd_event(token: str, event: dict[str, object]) -> None:
    """Store a ttyd browser event for later UI synchronization."""
    if not token:
        return
    events = TTYD_EVENT_REGISTRY.setdefault(token, [])
    events.append(event)
    del events[:-25]
    event_requests_close = ttyd_event_requests_document_close(event)
    if event.get("type") != "cwd" and not event_requests_close:
        return
    entry = TTYD_CLEANUP_REGISTRY.setdefault(token, {})
    cwd = str(event.get("cwd", "")).strip()
    if cwd:
        entry["cwd"] = cwd
    if event_requests_close:
        entry["exit_requested"] = True
    entry["last_event"] = event


def ttyd_event_requests_document_close(event: dict[str, object]) -> bool:
    """Return whether a ttyd event should close the Terminal document view."""
    event_type = str(event.get("type", "")).strip().lower()
    command = str(event.get("command", "")).strip().lower()
    return event_type == "exit" or command in TTYD_EXIT_COMMANDS


def normalize_ttyd_event(value: object) -> dict[str, object]:
    """Return a sanitized ttyd event dictionary."""
    if not isinstance(value, dict):
        return {}
    event_type = re.sub(r"[^A-Za-z0-9_-]+", "", str(value.get("type", "")))
    command = re.sub(r"[^A-Za-z0-9_-]+", "", str(value.get("command", "")))
    cwd = str(value.get("cwd", "")).strip()
    try:
        status = int(value.get("status", 0) or 0)
    except (TypeError, ValueError):
        status = 0
    try:
        event_time = int(value.get("time", 0) or 0)
    except (TypeError, ValueError):
        event_time = int(time.time() * 1000)
    if not event_type:
        return {}
    return {
        "type": event_type,
        "command": command or "unknown",
        "status": status,
        "cwd": cwd,
        "time": event_time,
    }


def sync_ttyd_event_state() -> None:
    """Synchronize latest ttyd hook events into Streamlit session state."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    if not token:
        return
    entry = TTYD_CLEANUP_REGISTRY.get(token)
    if not isinstance(entry, dict):
        return
    if bool(entry.pop("exit_requested", False)):
        if terminal_document_view_is_active():
            close_document_view()
            st.rerun()
        return
    cwd = str(entry.get("cwd", "")).strip()
    if not cwd:
        return
    st.session_state[hhs_ui.TERMINAL_CWD_KEY] = cwd
    if connected_ssh_host():
        st.session_state[hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY] = cwd
    else:
        st.session_state[hhs_ui_constants.FOOTER_LOCAL_WORKING_DIR_KEY] = cwd


def run_cleanup_bash_command(
    command: str, timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    """Run a local cleanup command outside the normal Streamlit render flow."""
    try:
        return subprocess.run(
            [RUN_SHELL, "-lc", command],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        return subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command],
            124,
            error.stdout or "",
            error.stderr or f"Command timed out after {timeout_seconds} seconds.",
        )
    except OSError as error:
        return subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command],
            127,
            "",
            str(error),
        )


class TtydCleanupRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler used by browser unload beacons to close ttyd and SSH."""

    def log_message(self, _format: str, *_args: object) -> None:
        """Suppress cleanup server access logs."""
        return

    def end_headers(self) -> None:
        """Send CORS headers for browser unload beacons."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        """Handle browser preflight requests."""
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        """Handle image/fetch fallback cleanup requests."""
        self.handle_cleanup_request()

    def do_POST(self) -> None:
        """Handle navigator.sendBeacon cleanup requests."""
        if urllib.parse.urlparse(self.path).path == "/ttyd-event":
            self.handle_ttyd_event_request()
            return
        self.handle_cleanup_request()

    def handle_cleanup_request(self) -> None:
        """Close resources for the token provided in the request query string."""
        parsed_url = urllib.parse.urlparse(self.path)
        token = urllib.parse.parse_qs(parsed_url.query).get("token", [""])[0]
        self.send_response(204)
        self.end_headers()
        if token:
            schedule_cleanup_session_resources(token)

    def handle_ttyd_event_request(self) -> None:
        """Store a ttyd event sent by the browser bridge."""
        parsed_url = urllib.parse.urlparse(self.path)
        token = urllib.parse.parse_qs(parsed_url.query).get("token", [""])[0]
        try:
            content_length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            content_length = 0
        try:
            payload = self.rfile.read(content_length).decode("utf-8")
            event = normalize_ttyd_event(json.loads(payload or "{}"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            event = {}
        if token and event:
            store_ttyd_event(token, event)
        self.send_response(204)
        self.end_headers()


def cleanup_all_registered_sessions() -> None:
    """Close all registered ttyd and SSH resources on Streamlit process exit."""
    for token in list(TTYD_CLEANUP_REGISTRY):
        cleanup_session_resources(token)


def ensure_ttyd_cleanup_server() -> int:
    """Start the localhost cleanup server and return its port."""
    global TTYD_CLEANUP_SERVER, TTYD_CLEANUP_SERVER_PORT
    if TTYD_CLEANUP_SERVER is not None:
        return TTYD_CLEANUP_SERVER_PORT
    state = process_resource_state()
    cached_server = state.get("ttyd_cleanup_server")
    cached_port = int(state.get("ttyd_cleanup_server_port") or 0)
    if cached_server is not None and cached_port > 0:
        TTYD_CLEANUP_SERVER = cached_server
        TTYD_CLEANUP_SERVER_PORT = cached_port
        return TTYD_CLEANUP_SERVER_PORT
    server = ThreadingHTTPServer((hhs_ui.TTYD_HOST, 0), TtydCleanupRequestHandler)
    server.daemon_threads = True
    port = int(server.server_address[1])
    TTYD_CLEANUP_SERVER = server
    TTYD_CLEANUP_SERVER_PORT = port
    state["ttyd_cleanup_server"] = server
    state["ttyd_cleanup_server_port"] = port
    thread = threading.Thread(
        target=server.serve_forever,
        name="hhs-ttyd-cleanup",
        daemon=True,
    )
    thread.start()
    if not bool(state.get("ttyd_cleanup_atexit_registered", False)):
        atexit.register(cleanup_all_registered_sessions)
        state["ttyd_cleanup_atexit_registered"] = True
    return TTYD_CLEANUP_SERVER_PORT


def browser_cleanup_token() -> str:
    """Return the per-browser-session cleanup token."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    if not token:
        token = secrets.token_urlsafe(24)
        st.session_state[hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY] = token
    return token


def update_browser_cleanup_registration() -> str:
    """Register the current ttyd and SSH resources for browser unload cleanup."""
    token = browser_cleanup_token()
    entry = TTYD_CLEANUP_REGISTRY.setdefault(token, {})
    entry.update(
        {
            "ttyd_process": st.session_state.get(hhs_ui_constants.TTYD_PROCESS_KEY),
            "ssh_host": connected_ssh_host(),
        }
    )
    return token


def ttyd_event_url() -> str:
    """Return the local browser-to-UI ttyd event endpoint URL."""
    token = browser_cleanup_token()
    port = ensure_ttyd_cleanup_server()
    return f"http://{hhs_ui.TTYD_HOST}:{port}/ttyd-event?token={token}"


def render_browser_cleanup_script() -> None:
    """Install a browser unload hook that closes ttyd and SSH resources."""
    token = update_browser_cleanup_registration()
    port = ensure_ttyd_cleanup_server()
    cleanup_url = f"http://{hhs_ui.TTYD_HOST}:{port}/cleanup?token={token}"
    components.html(
        f"""
        <script>
          (() => {{
            const cleanupUrl = {cleanup_url!r};
            const parentWindow = window.parent;
            if (
              parentWindow.__hhsTtydCleanupUrl === cleanupUrl &&
              parentWindow.__hhsTtydCleanupHandler
            ) {{
              return;
            }}
            if (parentWindow.__hhsTtydCleanupHandler) {{
              parentWindow.removeEventListener(
                "pagehide",
                parentWindow.__hhsTtydCleanupHandler
              );
              parentWindow.removeEventListener(
                "beforeunload",
                parentWindow.__hhsTtydCleanupHandler
              );
              parentWindow.__hhsTtydCleanupHandler = null;
            }}
            parentWindow.__hhsTtydCleanupUrl = cleanupUrl;
            const cleanup = () => {{
              try {{
                if (parentWindow.__hhsTtydCleanupSent === cleanupUrl) {{
                  return;
                }}
                parentWindow.__hhsTtydCleanupSent = cleanupUrl;
                if (navigator.sendBeacon) {{
                  navigator.sendBeacon(cleanupUrl, "");
                  return;
                }}
                fetch(cleanupUrl, {{
                  method: "POST",
                  mode: "no-cors",
                  keepalive: true,
                }}).catch(() => {{}});
              }} catch (_error) {{
                const image = new Image();
                image.src = cleanupUrl;
              }}
            }};
            parentWindow.addEventListener("pagehide", cleanup, {{ once: true }});
            parentWindow.addEventListener("beforeunload", cleanup, {{ once: true }});
            parentWindow.__hhsTtydCleanupHandler = cleanup;
            if (!parentWindow.__hhsTtydEventListenerInstalled) {{
              parentWindow.__hhsTtydEventListenerInstalled = true;
              parentWindow.addEventListener("message", (event) => {{
                const data = event.data || {{}};
                if (data.type !== "hhs-ttyd-event" || !data.event || data.event.type !== "cwd") {{
                  return;
                }}
                const cwd = String(data.event.cwd || "").trim();
                if (!cwd) {{
                  return;
                }}
                const node = parentWindow.document.querySelector(".hhs-footer-working-dir-value");
                if (node) {{
                  node.textContent = cwd;
                }}
              }});
            }}
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def terminal_document_title() -> str:
    """Return the terminal document title for local or SSH-connected sessions."""
    if str(st.session_state.get("ssh_connection_status", "")).strip() == "connected":
        return "Remote Terminal"
    return "Terminal"


def initialize_terminal_session_state() -> None:
    """Initialize ttyd terminal working directory and ready status."""
    st.session_state.setdefault(hhs_ui.TERMINAL_CWD_KEY, footer_working_directory())
    if not bool(st.session_state.get(hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY, False)):
        push_floating_status("HomeSetup terminal is ready.", "info")
        st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = True


def terminal_output_line_is_noise(line: str) -> bool:
    """Return whether a terminal output line is SSH/HomeSetup wrapper chatter."""
    clean_line = strip_ansi(line).strip()
    if not clean_line:
        return False
    if clean_line == "exit":
        return True
    if clean_line.startswith("[bash] HomeSetup is starting"):
        return True
    if "Welcome " in clean_line and " to HomeSetup v" in clean_line:
        return True
    if re.fullmatch(r"Shell option \S+ set to (?:on|off)", clean_line):
        return True
    if re.fullmatch(
        r"(?:Shared )?Connection to .+ closed\.", clean_line, re.IGNORECASE
    ):
        return True
    if re.fullmatch(r"Shared connection to .+ closed\.", clean_line, re.IGNORECASE):
        return True
    return False


def filter_terminal_output_noise(value: str) -> str:
    """Return terminal output without SSH/HomeSetup wrapper chatter lines."""
    lines = [
        line for line in value.splitlines() if not terminal_output_line_is_noise(line)
    ]
    output = "\n".join(lines)
    if value.endswith("\n") and output:
        output += "\n"
    return output


def strip_ansi(value: str) -> str:
    """Remove terminal ANSI color escapes from command output."""
    return hhs_ui.ESCAPED_ANSI_ESCAPE_PATTERN.sub(
        "", hhs_ui.ANSI_ESCAPE_PATTERN.sub("", value)
    )


def clean_command_status_message(value: str) -> str:
    """Return command output suitable for compact UI status messages."""
    clean_value = strip_ansi(value).strip()
    clean_value = re.sub(r"^\s*[✘✖✗×]\s*", "", clean_value)
    clean_value = re.sub(r"^\s*Fatal:\s*", "", clean_value)
    clean_value = re.sub(r"^\s*__[A-Za-z0-9_]+\s*", "", clean_value)
    return clean_value.strip()


def service_action_success_message(operation: str, service_name: str) -> str:
    """Return a normalized success message for a completed service action."""
    labels = {
        "start": "Started",
        "stop": "Stopped",
        "restart": "Restarted",
    }
    label = labels.get(operation.strip().lower(), "Updated")
    return f"{label} service: {service_name}"


def clean_service_action_error(output: str, operation: str, service_name: str) -> str:
    """Return a concise error message from service-action command output."""
    clean_output = clean_command_status_message(output).replace("`", "").strip()
    clean_output = re.sub(
        rf'^\s*{re.escape(operation.title())}\s+service\s+"{re.escape(service_name)}"\.\.\.\s*',
        "",
        clean_output,
        flags=re.IGNORECASE,
    )
    clean_output = re.sub(r"\s*=>\s*", " ", clean_output)
    clean_output = re.sub(r"\s+OK\s+FAILED\s*$", "", clean_output, flags=re.IGNORECASE)
    clean_output = re.sub(r"\s+", " ", clean_output).strip()
    if clean_output and "successfully" not in clean_output.lower():
        return clean_output
    return f"Unable to {operation} service: {service_name}"


def service_action_status_message(
    result: subprocess.CompletedProcess[str], operation: str, service_name: str
) -> str:
    """Return the footer status message for a completed service action."""
    if result.returncode == 0:
        return service_action_success_message(operation, service_name)
    return clean_service_action_error(
        result.stderr or result.stdout or "", operation, service_name
    )


def updater_output_has_updates(output: str) -> bool:
    """Return whether updater command output reports available updates."""
    clean_output = strip_ansi(output).lower()
    no_update_markers = (
        "up-to-date",
        "up to date",
        "already latest",
        "latest version",
        "no update",
        "no updates",
    )
    if any(marker in clean_output for marker in no_update_markers):
        return False
    update_markers = (
        "updates available",
        "update available",
        "new version",
        "repository:",
    )
    return any(marker in clean_output for marker in update_markers)


def updater_check_due(now: float | None = None) -> bool:
    """Return whether the persisted updater check is missing or older than one day."""
    last_output = str(st.session_state.get("updater_last_check_output", "")).strip()
    if not last_output:
        return True
    try:
        last_check_epoch = float(
            st.session_state.get("updater_last_check_epoch", 0) or 0
        )
    except (TypeError, ValueError):
        return True
    if last_check_epoch <= 0:
        return True
    current_time = time.time() if now is None else now
    return (
        current_time - last_check_epoch
        >= hhs_ui_constants.UPDATER_CHECK_INTERVAL_SECONDS
    )


def updater_check_context() -> str:
    """Return the active updater check context for local or SSH execution."""
    host = connected_ssh_host()
    return f"ssh:{host}" if host else "local"


def restore_local_updater_status() -> None:
    """Restore the footer update icon state from the latest local daily check."""
    output = str(st.session_state.get("updater_last_check_output", ""))
    st.session_state["updater_update_available"] = updater_output_has_updates(output)
    st.session_state["updater_check_context"] = "local"


def reset_updater_remote_check_state() -> None:
    """Clear updater context state so the active SSH host is checked fresh."""
    st.session_state["updater_check_started_context"] = ""
    st.session_state["updater_remote_checked_context"] = ""
    st.session_state["updater_check_context"] = ""
    st.session_state["updater_update_available"] = False


def start_updater_check(context: str, force_local: bool) -> None:
    """Start a HomeSetup updater check for the given execution context."""
    started = start_background_bash_command(
        UPDATER_CHECK_JOB,
        build_hhs_updater_command("check"),
        "Checking HomeSetup updates",
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        force_local=force_local,
        metadata={"updater_context": context},
    )
    if started:
        st.session_state["updater_check_started_context"] = context


def store_updater_check_result(
    result: subprocess.CompletedProcess[str], context: str = "local"
) -> None:
    """Persist the latest updater check output and update-availability flag."""
    output = strip_ansi(f"{result.stdout or ''}\n{result.stderr or ''}").strip()
    if not output:
        output = "No HomeSetup updater output."
    st.session_state["updater_check_started_context"] = ""
    st.session_state["updater_check_context"] = context
    st.session_state["updater_update_available"] = (
        result.returncode == 0 and updater_output_has_updates(output)
    )
    if context == "local":
        st.session_state["updater_last_check_epoch"] = time.time()
        st.session_state["updater_last_check_output"] = output
        save_ui_state()
    else:
        st.session_state["updater_remote_checked_context"] = context
    if result.returncode == 0:
        return
    push_floating_status(output or "Unable to check HomeSetup updates.", "warn")


def execute_due_updater_check() -> None:
    """Start or complete the updater check when persisted check state is stale."""
    completed = background_job_result(UPDATER_CHECK_JOB)
    if completed is not None:
        result, metadata = completed
        context = str(metadata.get("updater_context", "local"))
        store_updater_check_result(result, context)

    current_context = updater_check_context()
    if st.session_state.get("updater_check_context") != current_context:
        if current_context == "local":
            restore_local_updater_status()
        else:
            st.session_state["updater_update_available"] = False
            st.session_state["updater_check_context"] = current_context

    if current_context != "local":
        if st.session_state.get("updater_check_started_context") == current_context:
            return
        if st.session_state.get("updater_remote_checked_context") == current_context:
            return
        start_updater_check(current_context, force_local=False)
        return

    if bool(st.session_state.get("updater_check_attempted", False)):
        return
    if not updater_check_due():
        return
    st.session_state["updater_check_attempted"] = True
    start_updater_check("local", force_local=True)


def overlaps_existing_range(
    start: int, end: int, ranges: list[tuple[int, int, str]]
) -> bool:
    """Return whether a candidate highlight range overlaps an existing range."""
    return any(
        start < existing_end and end > existing_start
        for existing_start, existing_end, _ in ranges
    )


def log_tailor_highlight_ranges(value: str) -> list[tuple[int, int, str]]:
    """Return highlight ranges using the same regex rules as __hhs_tailor."""
    ranges: list[tuple[int, int, str]] = []
    for pattern, css_class in hhs_ui.LOG_TAILOR_RULES:
        for match in pattern.finditer(value):
            start, end = match.span(1) if css_class == "thread" else match.span(0)
            if start == end or overlaps_existing_range(start, end, ranges):
                continue
            ranges.append((start, end, css_class))
    return sorted(ranges, key=lambda item: item[0])


def log_filter_highlight_ranges(
    value: str, text_filter: str = ""
) -> list[tuple[int, int, str]]:
    """Return highlight ranges for Monitor Logs containing-filter matches."""
    needle = text_filter.strip()
    if not needle:
        return []
    pattern = re.compile(re.escape(needle), flags=re.IGNORECASE)
    return [
        (match.start(), match.end(), "filter-match")
        for match in pattern.finditer(value)
        if match.start() != match.end()
    ]


def colorize_log_output(value: str, text_filter: str = "") -> str:
    """Return log output highlighted with __hhs_tailor-compatible CSS classes."""
    clean_value = strip_ansi(value)
    ranges = log_filter_highlight_ranges(clean_value, text_filter)
    for start, end, css_class in log_tailor_highlight_ranges(clean_value):
        if overlaps_existing_range(start, end, ranges):
            continue
        ranges.append((start, end, css_class))
    ranges = sorted(ranges, key=lambda item: item[0])
    html_parts: list[str] = []
    cursor = 0
    for start, end, css_class in ranges:
        if start > cursor:
            html_parts.append(html.escape(clean_value[cursor:start]))
        html_parts.append(
            f'<span class="hhs-log-{css_class}">{html.escape(clean_value[start:end])}</span>'
        )
        cursor = end
    html_parts.append(html.escape(clean_value[cursor:]))
    return "".join(html_parts).replace("\n", "<br>")


def filter_log_output(value: str, log_filter: str, text_filter: str = "") -> str:
    """Return log output matching the selected monitor log text filter."""
    needle = text_filter.strip().lower()
    if log_filter != "Containing" or not needle:
        return value
    return "\n".join(
        line for line in value.splitlines() if needle in strip_ansi(line).lower()
    )


def interpret_terminal_edit_sequences(output: str) -> str:
    """Return output after applying simple terminal cursor edit sequences."""
    lines: list[str] = []
    current: list[str] = []
    cursor = 0
    index = 0
    length = len(output)
    while index < length:
        char = output[index]
        if char in ("\n", "\r"):
            lines.append("".join(current))
            current = []
            cursor = 0
            index += 1
            continue
        if char != "\x1b":
            if cursor >= len(current):
                current.extend(" " for _ in range(cursor - len(current)))
                current.append(char)
            else:
                current[cursor] = char
            cursor += 1
            index += 1
            continue
        match = re.match(r"\x1b\[([0-9;?]*)([A-Za-z])", output[index:])
        if not match:
            index += 1
            continue
        params = match.group(1).replace("?", "")
        command = match.group(2)
        amount = int(params.split(";", 1)[0] or "1") if params else 1
        if command == "D":
            cursor = max(0, cursor - amount)
        elif command == "C":
            cursor += amount
        elif command == "G":
            cursor = max(0, amount - 1)
        elif command == "K":
            current = current[:cursor]
        index += len(match.group(0))
    lines.append("".join(current))
    return "\n".join(lines)


def clean_hhs_ask_output(output: str) -> str:
    """Return user-facing ask output without terminal control decoration."""
    final_output = output
    for marker in ("\x1b[H\x1b[2J\x1b[3J", "\033[H\033[2J\033[3J"):
        if marker in final_output:
            final_output = final_output.rsplit(marker, 1)[-1]
    clean_output = strip_ansi(interpret_terminal_edit_sequences(final_output))
    lines = []
    for line in clean_output.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("✨"):
            continue
        if re.match(r"^/.*/hhs-[^-]+-response\.", stripped):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def current_username() -> str:
    """Return the current UI username."""
    return os.environ.get("USER") or os.environ.get("LOGNAME") or "user"


def parse_current_ollama_model(output: str) -> str:
    """Parse the current Ollama model name from ask -m output."""
    for line in strip_ansi(output).splitlines():
        if "(current)" not in line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            return parts[1]
    return "unknown"


def parse_ollama_model_rows(
    output: str, current_model: str = ""
) -> list[dict[str, str]]:
    """Parse available Ollama model rows from the ask -m Markdown table."""
    rows: list[dict[str, str]] = []
    seen_models: set[str] = set()
    downloaded_models = parse_downloaded_ollama_models(output)
    for line in strip_ansi(output).splitlines():
        markdown_columns = [
            column.strip().strip("`") for column in line.strip().strip("|").split("|")
        ]
        if (
            len(markdown_columns) >= 6
            and markdown_columns[0]
            and markdown_columns[0] != "Pull Name"
            and not markdown_columns[0].startswith(":")
            and ":" in markdown_columns[0]
        ):
            model_name = markdown_columns[0]
            if model_name not in seen_models:
                rows.append(
                    {
                        "Name": model_name,
                        "Params": markdown_columns[2],
                        "Size": markdown_columns[3],
                        "Context": markdown_columns[4],
                        "Capabilities": markdown_columns[5],
                        "Status": ollama_model_status(
                            model_name, current_model, downloaded_models
                        ),
                    }
                )
                seen_models.add(model_name)
            continue
    return rows


def parse_downloaded_ollama_models(output: str) -> set[str]:
    """Return downloaded Ollama model names from the ask -m local model section."""
    models: set[str] = set()
    for line in strip_ansi(output).splitlines():
        parts = line.split()
        if (
            len(parts) >= 2
            and parts[0].isdigit()
            and parts[1] != "NAME"
            and ":" in parts[1]
        ):
            models.add(parts[1])
    return models


def first_downloaded_ollama_model(output: str, excluded_model: str = "") -> str:
    """Return the first downloaded Ollama model listed in the available models table."""
    downloaded_models = parse_downloaded_ollama_models(output)
    for row in parse_rows_cached("ollama_models", output, parse_ollama_model_rows):
        model_name = row["Name"]
        if model_name != excluded_model and model_name in downloaded_models:
            return model_name
    return ""


def ollama_model_status(
    model_name: str, current_model: str, downloaded_models: set[str]
) -> str:
    """Return the UI status for one Ollama model."""
    if model_name == current_model:
        return "Active"
    if model_name in downloaded_models:
        return "Downloaded"
    return ""


def ollama_model_context_size(ollama_model: str) -> str:
    """Return the context size for an Ollama model from HomeSetup model metadata."""
    models_file = (
        homesetup_home() / "bin/apps/bash/hhs-app/plugins/ask/ollama-models.md"
    )
    if not models_file.is_file():
        return "?"
    clean_model = ollama_model.strip("`")
    for line in models_file.read_text(encoding="utf-8").splitlines():
        columns = [
            column.strip().strip("`") for column in line.strip().strip("|").split("|")
        ]
        if len(columns) >= 5 and columns[0] == clean_model:
            return columns[4] or "?"
    return "?"


def parse_context_window_kib(context_size: str) -> int:
    """Return an Ollama context window label as KiB for history-file budgeting."""
    normalized_context = context_size.strip().upper().replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMG]?)", normalized_context)
    if not match:
        return 0
    value = float(match.group(1))
    unit = match.group(2)
    multiplier = {"": 1, "K": 1, "M": 1024, "G": 1024 * 1024}[unit]
    return max(int(value * multiplier), 0)


def file_size_bytes(file_path: Path) -> int:
    """Return a file size in bytes, or zero when the file is missing."""
    try:
        return file_path.stat().st_size if file_path.is_file() else 0
    except OSError:
        return 0


def percent_of_context(file_size: int, context_window_bytes: int) -> int:
    """Return a clamped percentage of an Ollama context window."""
    return max(0, min(round((file_size / context_window_bytes) * 100), 100))


def ai_context_usage_percentages(context_size: str) -> dict[str, int] | None:
    """Return prompt, history context, and total context usage percentages."""
    context_window_kib = parse_context_window_kib(context_size)
    if context_window_kib <= 0:
        return None
    context_window_bytes = context_window_kib * 1024
    prompt_size = file_size_bytes(ollama_prompt_file())
    history_size = file_size_bytes(ollama_history_file())
    return {
        "prompt": percent_of_context(prompt_size, context_window_bytes),
        "context": percent_of_context(history_size, context_window_bytes),
        "total": percent_of_context(prompt_size + history_size, context_window_bytes),
    }


def ai_context_used_percent(context_size: str) -> int | None:
    """Return the percent of the selected model context used by prompt and history."""
    usage_percentages = ai_context_usage_percentages(context_size)
    if usage_percentages is None:
        return None
    return usage_percentages["total"]


def ai_context_used_color(percent_used: int) -> str:
    """Return the CSS color token for an AI context usage percentage."""
    if percent_used >= 90:
        return "var(--hhs-danger)"
    if percent_used >= 40:
        return "var(--hhs-warning)"
    return "var(--hhs-success)"


def html_tooltip_chip(label: str, value_html: str, tooltip_html: str) -> str:
    """Return a chat metadata chip with an HTML tooltip."""
    return (
        f'<span class="hhs-tooltip" tabindex="0">{html.escape(label)}: '
        f"{value_html}"
        f'<span class="hhs-tooltip-content">{tooltip_html}</span></span>'
    )


def model_characteristics_tooltip_html(
    ollama_model: str, context_size: str, model_output: str
) -> str:
    """Return model characteristics tooltip HTML using the model table columns."""
    model_row = next(
        (
            row
            for row in parse_rows_cached(
                f"ollama_models_{ollama_model}",
                model_output,
                lambda output: parse_ollama_model_rows(output, ollama_model),
            )
            if row["Name"] == ollama_model
        ),
        {},
    )
    if not model_row:
        model_row = {"Name": ollama_model, "Context": context_size}
    return "<br>".join(
        f"{html.escape(column)}: {html.escape(str(value))}"
        for column, value in model_row.items()
        if str(value).strip()
    )


def ai_context_used_tooltip_html(context_size: str) -> str:
    """Return prompt and history context usage tooltip HTML."""
    usage_percentages = ai_context_usage_percentages(context_size)
    if usage_percentages is None:
        return "Prompt: -<br>Context: -"
    return (
        f"Prompt: {usage_percentages['prompt']}%<br>"
        f"Context: {usage_percentages['context']}%"
    )


def ai_context_used_meta_html(context_size: str) -> str:
    """Return the AI context usage meta row HTML."""
    percent_used = ai_context_used_percent(context_size)
    tooltip_html = ai_context_used_tooltip_html(context_size)
    if percent_used is None:
        return html_tooltip_chip(
            "Ctx Used",
            '<strong class="hhs-ai-chat-model hhs-ai-context-used">-</strong>',
            tooltip_html,
        )
    formatted_percent = html.escape(f"{percent_used}%")
    context_color = ai_context_used_color(percent_used)
    return html_tooltip_chip(
        "Ctx Used",
        '<strong class="hhs-ai-chat-model hhs-ai-context-used" '
        f'style="color: {context_color};">'
        f"{formatted_percent}</strong>",
        tooltip_html,
    )


def ai_model_performance_timings() -> list[dict[str, str | float]]:
    """Return the persisted AI request timing circular buffer."""
    timings = st.session_state.setdefault("ai_model_performance_timings", [])
    if not isinstance(timings, list):
        timings = []
    normalized_timings = [
        {"model": str(timing["model"]), "duration": float(timing["duration"])}
        for timing in timings
        if isinstance(timing, dict)
        and isinstance(timing.get("model"), str)
        and isinstance(timing.get("duration"), int | float)
        and float(timing["duration"]) >= 0
    ][-hhs_ui.AI_PERFORMANCE_TIMING_LIMIT :]
    st.session_state["ai_model_performance_timings"] = normalized_timings
    return normalized_timings


def ai_model_performance_averages() -> dict[str, float]:
    """Return cached average AI request durations by model."""
    averages = st.session_state.setdefault("ai_model_performance_averages", {})
    if not isinstance(averages, dict):
        averages = {}
    normalized_averages = {
        str(model): float(duration)
        for model, duration in averages.items()
        if isinstance(model, str)
        and isinstance(duration, int | float)
        and float(duration) >= 0
    }
    st.session_state["ai_model_performance_averages"] = normalized_averages
    return normalized_averages


def ai_model_performance_sample_counts() -> dict[str, int]:
    """Return total recorded AI request sample counts by model."""
    sample_counts = st.session_state.setdefault(
        "ai_model_performance_sample_counts", {}
    )
    if not isinstance(sample_counts, dict):
        sample_counts = {}
    normalized_counts = {
        str(model): int(count)
        for model, count in sample_counts.items()
        if isinstance(model, str) and isinstance(count, int | float) and int(count) >= 0
    }
    st.session_state["ai_model_performance_sample_counts"] = normalized_counts
    return normalized_counts


def timing_durations_for_model(model_name: str) -> list[float]:
    """Return timing durations from the circular buffer for a single model."""
    clean_model = model_name.strip() or "unknown"
    return [
        float(timing["duration"])
        for timing in ai_model_performance_timings()
        if timing.get("model") == clean_model
    ]


def record_ai_model_request_duration(model_name: str, duration_seconds: float) -> None:
    """Record one AI request duration and periodically recalculate its average."""
    clean_model = model_name.strip() or "unknown"
    timings = ai_model_performance_timings()
    timings.append({"model": clean_model, "duration": max(duration_seconds, 0.0)})
    st.session_state["ai_model_performance_timings"] = timings[
        -hhs_ui.AI_PERFORMANCE_TIMING_LIMIT :
    ]
    sample_counts = ai_model_performance_sample_counts()
    sample_counts[clean_model] = sample_counts.get(clean_model, 0) + 1
    model_sample_count = sample_counts[clean_model]
    if model_sample_count == hhs_ui.AI_PERFORMANCE_MIN_SAMPLES or (
        model_sample_count > hhs_ui.AI_PERFORMANCE_MIN_SAMPLES
        and model_sample_count % hhs_ui.AI_PERFORMANCE_RECALC_INTERVAL == 0
    ):
        model_durations = timing_durations_for_model(clean_model)
        if model_durations:
            ai_model_performance_averages()[clean_model] = sum(model_durations) / len(
                model_durations
            )


def ai_model_average_duration_seconds(model_name: str) -> float | None:
    """Return the cached AI request average duration once enough samples exist."""
    clean_model = model_name.strip() or "unknown"
    sample_count = ai_model_performance_sample_counts().get(clean_model, 0)
    if sample_count < hhs_ui.AI_PERFORMANCE_MIN_SAMPLES:
        return None
    return ai_model_performance_averages().get(clean_model)


def format_ai_request_duration(duration_seconds: float) -> str:
    """Return an AI request duration using millis, seconds, or minutes."""
    if duration_seconds < 1:
        return f"{max(round(duration_seconds * 1000), 1)} millis"
    if duration_seconds < 60:
        return f"{duration_seconds:.1f} sec"
    return f"{duration_seconds / 60:.1f} minutes"


def ai_model_recent_duration_tooltip_html(model_name: str) -> str:
    """Return the last five AI request durations as tooltip HTML."""
    recent_durations = timing_durations_for_model(model_name)[-5:]
    if not recent_durations:
        return "-"
    return "<br>".join(
        html.escape(format_ai_request_duration(duration))
        for duration in recent_durations
    )


def ai_model_performance_meta_html(model_name: str) -> str:
    """Return the AI model performance meta row HTML, or an empty string."""
    average_duration = ai_model_average_duration_seconds(model_name)
    if average_duration is None:
        formatted_duration = "-"
    else:
        formatted_duration = html.escape(format_ai_request_duration(average_duration))
    return html_tooltip_chip(
        "Latency",
        '<strong class="hhs-ai-chat-model hhs-ai-chat-duration">'
        f"{formatted_duration}</strong>",
        ai_model_recent_duration_tooltip_html(model_name),
    )


def ai_chat_meta_html(
    username: str, ollama_model: str, context_size: str, model_output: str
) -> str:
    """Return the AI chat metadata row HTML."""
    safe_username = html.escape(username)
    safe_model = html.escape(ollama_model)
    safe_context_size = html.escape(context_size)
    user_html = html_tooltip_chip(
        "User",
        f'<strong class="hhs-ai-chat-model hhs-ai-chat-user">{safe_username}</strong>',
        "Current logged user",
    )
    model_html = html_tooltip_chip(
        "Model",
        f'<strong class="hhs-ai-chat-model">{safe_model}[{safe_context_size}]</strong>',
        model_characteristics_tooltip_html(ollama_model, context_size, model_output),
    )
    performance_html = ai_model_performance_meta_html(ollama_model)
    context_used_html = ai_context_used_meta_html(context_size)
    return f"""
    <div class="hhs-ai-chat-meta">
      {user_html}
      {model_html}
      {context_used_html}
      {performance_html}
    </div>
    """


def format_ai_chat_prefix(
    role: str, username: str, ollama_model: str, context_size: str
) -> str:
    """Format an AI chat message with icon, speaker, and content."""
    if role == "assistant":
        return f'<span class="hhs-ai-assistant-text">{html.escape(ollama_model)}&#91;{html.escape(context_size)}&#93;:</span><br>'
    if role == "system":
        return '<span class="hhs-ai-system-text">HomeSetup:</span><br>'
    return (
        f'<span class="hhs-ai-user-text">{html.escape(username)}&#91;You&#93;:</span>'
    )


def wrap_ai_code_line(line: str) -> list[str]:
    """Wrap one code-block line to keep AI markdown inside the chat layout."""
    if len(line) <= hhs_ui.AI_CODE_BLOCK_WRAP_COLUMNS:
        return [line]
    indent = re.match(r"^\s*", line).group(0)
    wrapped = textwrap.wrap(
        line,
        width=hhs_ui.AI_CODE_BLOCK_WRAP_COLUMNS,
        initial_indent="",
        subsequent_indent=indent,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )
    return wrapped or [line]


def normalize_ai_code_blocks(content: str) -> str:
    """Normalize assistant Markdown code fences and wrap long code lines."""
    lines = content.splitlines()
    normalized: list[str] = []
    in_code_block = False
    fence_marker = "```"

    for line in lines:
        malformed_fence = re.match(r"^(```+|~~~+)([A-Za-z0-9_.+-]+)\s+(.+)$", line)
        if not in_code_block and malformed_fence:
            fence_marker = malformed_fence.group(1)
            normalized.append(f"{fence_marker}{malformed_fence.group(2)}")
            normalized.extend(wrap_ai_code_line(malformed_fence.group(3)))
            normalized.append(fence_marker)
            continue

        code_fence = re.match(r"^(```+|~~~+)(?:[A-Za-z0-9_.+-]+)?\s*$", line)
        if code_fence:
            in_code_block = not in_code_block
            fence_marker = code_fence.group(1)
            normalized.append(line)
            continue

        if in_code_block:
            normalized.extend(wrap_ai_code_line(line))
        else:
            normalized.append(line)

    if in_code_block:
        normalized.append(fence_marker)
    return "\n".join(normalized)


def prepare_ai_chat_content(role: str, content: str) -> str:
    """Return chat content normalized for the selected AI message role."""
    if role == "assistant":
        return normalize_ai_code_blocks(content)
    return content


def render_ai_chat_message(
    role: str, content: str, username: str, ollama_model: str, context_size: str
) -> None:
    """Render an AI chat message with a colored prefix and Markdown content."""
    separator = "\n" if role in ("assistant", "system") else " "
    st.markdown(
        f"{format_ai_chat_prefix(role, username, ollama_model, context_size)}{separator}{prepare_ai_chat_content(role, content)}",
        unsafe_allow_html=True,
    )


def human_size_to_bytes(value: str) -> float:
    """Convert a human-readable disk size into bytes for chart sorting."""
    match = re.match(r"^\s*([0-9.]+)\s*([A-Za-z]*)\s*$", value)
    if not match:
        return 0.0
    number = float(match.group(1))
    unit = match.group(2).lower().rstrip("b")
    unit_multipliers = {
        "": 1,
        "k": 1024,
        "ki": 1024,
        "m": 1024**2,
        "mi": 1024**2,
        "g": 1024**3,
        "gi": 1024**3,
        "t": 1024**4,
        "ti": 1024**4,
        "p": 1024**5,
        "pi": 1024**5,
    }
    return number * unit_multipliers.get(unit, 1)


def metric_value(value: str) -> float:
    """Convert a top/ps metric value into a numeric chart value."""
    clean_value = value.strip().replace("%", "")
    if re.search(r"[A-Za-z]", clean_value):
        return human_size_to_bytes(clean_value)
    try:
        return float(clean_value)
    except ValueError:
        return 0.0


def expand_monitor_disk_directory(directory: str) -> str:
    """Expand a disk monitor directory using the app's HomeSetup defaults."""
    default_directory = monitor_default_disk_directory()
    raw_directory = (directory or "").strip() or default_directory
    expanded_directory = raw_directory.replace(
        "${HHS_HOME}", default_directory
    ).replace("$HHS_HOME", default_directory)
    return os.path.expandvars(os.path.expanduser(expanded_directory))


def relative_disk_usage_path(path: str, directory: str) -> str:
    """Return a disk usage path label relative to the selected directory."""
    expanded_directory = expand_monitor_disk_directory(directory).rstrip(os.sep)
    clean_path = path.rstrip(os.sep)
    if clean_path == expanded_directory:
        return "."
    prefix = f"{expanded_directory}{os.sep}"
    if clean_path.startswith(prefix):
        return clean_path[len(prefix) :]
    return path


def parse_hhs_disk_usage_directory(output: str) -> str:
    """Parse the expanded directory from __hhs_du output."""
    for line in strip_ansi(output).splitlines():
        match = re.search(r"disk usage at:\s+\"?(.+?)\"?\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def monitor_disk_display_directory(directory: str, output: str) -> str:
    """Return the expanded disk monitor directory for UI display."""
    output_directory = parse_hhs_disk_usage_directory(output)
    if output_directory:
        return output_directory
    return expand_monitor_disk_directory(directory)


def escape_markdown_table_cell(value: str) -> str:
    """Return a cell value escaped for a Markdown table."""
    return value.replace("|", "\\|")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Return a Markdown table for the provided headers and rows."""
    if not headers or not rows:
        return ""
    safe_headers = [escape_markdown_table_cell(header) for header in headers]
    safe_rows = [
        [escape_markdown_table_cell(cell) for cell in row[: len(headers)]]
        for row in rows
    ]
    header_line = "| " + " | ".join(safe_headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in safe_rows]
    return "\n".join([header_line, separator_line, *row_lines])


def normalize_markdown_table_row(headers: list[str], parts: list[str]) -> list[str]:
    """Return a row normalized to the provided Markdown table headers."""
    if headers == ["NAME", "LINE", "TIME", "FROM"] and len(parts) >= 5:
        return [parts[0], parts[1], " ".join(parts[2:5]), " ".join(parts[5:])]
    if len(parts) > len(headers):
        return [*parts[: len(headers) - 1], " ".join(parts[len(headers) - 1 :])]
    return [*parts, *([""] * (len(headers) - len(parts)))]


def format_hhs_sysinfo_markdown(output: str) -> str:
    """Format __hhs_sysinfo terminal output as Markdown."""
    markdown_lines: list[str] = []
    table_headers: list[str] = []
    table_rows: list[list[str]] = []

    def flush_table() -> None:
        """Append any pending Markdown table to the output."""
        nonlocal table_headers, table_rows
        table = markdown_table(table_headers, table_rows)
        if table:
            markdown_lines.extend(["", table, ""])
        table_headers = []
        table_rows = []

    for raw_line in strip_ansi(output).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("-=-") or set(line) == {"-"}:
            continue

        section_match = hhs_ui.SYSINFO_SECTION_PATTERN.match(line)
        if section_match:
            flush_table()
            markdown_lines.extend(["", f"##### {section_match.group(1).strip()}", ""])
            continue

        key_value_match = hhs_ui.SYSINFO_KEY_VALUE_PATTERN.match(raw_line)
        if key_value_match:
            flush_table()
            name = key_value_match.group(1).strip()
            value = key_value_match.group(2).strip()
            markdown_lines.append(f"- **{name}**: `{value}`")
            continue

        parts = line.split()
        if len(parts) > 1:
            if not table_headers:
                table_headers = parts
            else:
                table_rows.append(normalize_markdown_table_row(table_headers, parts))
            continue

        flush_table()
        markdown_lines.append(line)

    flush_table()
    return "\n".join(markdown_lines).strip()


def parse_fixed_width_cli_table(output: str) -> tuple[list[str], list[list[str]]]:
    """Parse a whitespace-aligned command table into headers and rows."""
    lines = [
        line.rstrip()
        for line in strip_ansi(output).splitlines()
        if line.strip() and set(line.strip()) != {"-"}
    ]
    if not lines:
        return [], []

    headers = (
        [part.strip() for part in lines[0].split("\t")]
        if "\t" in lines[0]
        else re.split(r"\s{2,}", lines[0].strip())
    )
    if len(headers) < 2:
        return [], []

    rows: list[list[str]] = []
    for line in lines[1:]:
        parts = (
            [part.strip() for part in line.split("\t")]
            if "\t" in line
            else re.split(r"\s{2,}", line.strip(), maxsplit=len(headers) - 1)
        )
        rows.append(normalize_markdown_table_row(headers, parts))
    return headers, rows


def docker_cli_table_output(output: str) -> str:
    """Return Docker CLI table output with remote shell startup banners removed."""
    lines = [
        line.rstrip()
        for line in strip_ansi(output).splitlines()
        if line.strip() and set(line.strip()) != {"-"}
    ]
    for index, line in enumerate(lines):
        headers = (
            [part.strip() for part in line.split("\t")]
            if "\t" in line
            else re.split(r"\s{2,}", line.strip())
        )
        if headers and headers[0] in {"CONTAINER ID", "REPOSITORY"}:
            return "\n".join(lines[index:])
    return ""


def filter_markdown_table_columns(
    headers: list[str], rows: list[list[str]], omitted_columns: tuple[str, ...]
) -> tuple[list[str], list[list[str]]]:
    """Return Markdown table data without the named columns."""
    omitted_column_names = set(omitted_columns)
    if not omitted_column_names:
        return headers, rows

    kept_indexes = [
        index
        for index, header in enumerate(headers)
        if header not in omitted_column_names
    ]
    return (
        [headers[index] for index in kept_indexes],
        [
            [row[index] if index < len(row) else "" for index in kept_indexes]
            for row in rows
        ],
    )


def docker_cli_table_rows(
    output: str, omitted_columns: tuple[str, ...] = ()
) -> list[dict[str, str]]:
    """Return Docker CLI table output as row dictionaries."""
    headers, rows = parse_fixed_width_cli_table(docker_cli_table_output(output))
    headers, rows = filter_markdown_table_columns(headers, rows, omitted_columns)
    return [
        {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
        }
        for row in rows
    ]


def docker_container_is_up(row: dict[str, str]) -> bool:
    """Return whether a Docker container row reports a running status."""
    return row.get("STATUS", "").strip().lower().startswith("up")


def command_env() -> dict[str, str]:
    """Return the environment used by HomeSetup command subprocesses."""
    return {
        **os.environ,
        "COLUMNS": hhs_ui.COMMAND_COLUMNS,
        hhs_ui_constants.RUN_SHELL_ENV_KEY: RUN_SHELL,
        "TERM": os.environ.get("TERM", "xterm-256color"),
    }


def hhs_ask_timeout_seconds() -> int:
    """Return the timeout for an Ollama prompt based on the selected host."""
    return 180 if connected_ssh_host() else 90


def local_hostname() -> str:
    """Return the local host name shown by the sidebar host selector."""
    return os.uname().nodename.strip() or "localhost"


def ssh_config_file() -> Path:
    """Return the user's OpenSSH config file path."""
    return Path.home() / ".ssh" / "config"


def parse_ssh_config_hosts(config_text: str) -> tuple[str, ...]:
    """Return concrete Host aliases configured in an OpenSSH config file."""
    hosts: list[str] = []
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts and parts[0].lower() == "host":
            for host in parts[1:]:
                if any(char in host for char in "*?!"):
                    continue
                if host not in hosts:
                    hosts.append(host)
    return tuple(hosts)


def parse_ssh_config_hostnames(config_text: str) -> dict[str, str]:
    """Return concrete SSH Host aliases mapped to their configured HostName."""
    hostnames: dict[str, str] = {}
    active_hosts: list[str] = []
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        keyword = parts[0].lower()
        if keyword == "host":
            active_hosts = [
                host for host in parts[1:] if not any(char in host for char in "*?!")
            ]
            continue
        if keyword == "hostname" and len(parts) > 1:
            hostname = parts[1]
            for host in active_hosts:
                hostnames[host] = hostname
    return hostnames


def parse_ssh_config_ports(config_text: str) -> dict[str, str]:
    """Return concrete SSH Host aliases mapped to their configured Port."""
    ports: dict[str, str] = {}
    active_hosts: list[str] = []
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        keyword = parts[0].lower()
        if keyword == "host":
            active_hosts = [
                host for host in parts[1:] if not any(char in host for char in "*?!")
            ]
            continue
        if keyword == "port" and len(parts) > 1:
            port = parts[1]
            for host in active_hosts:
                ports[host] = port
    return ports


def ssh_config_hosts() -> tuple[str, ...]:
    """Return concrete SSH Host aliases configured in ~/.ssh/config."""
    config_file = ssh_config_file()
    if not config_file.exists():
        return ()
    try:
        return parse_ssh_config_hosts(config_file.read_text(encoding="utf-8"))
    except OSError:
        return ()


def ssh_config_hostname(host: str) -> str:
    """Return the configured HostName for an SSH Host alias."""
    config_file = ssh_config_file()
    if not config_file.exists():
        return host
    try:
        hostnames = parse_ssh_config_hostnames(config_file.read_text(encoding="utf-8"))
    except OSError:
        return host
    return hostnames.get(host, host)


def ssh_config_port(host: str) -> str:
    """Return the configured Port for an SSH Host alias."""
    config_file = ssh_config_file()
    if not config_file.exists():
        return "22"
    try:
        ports = parse_ssh_config_ports(config_file.read_text(encoding="utf-8"))
    except OSError:
        return "22"
    return ports.get(host, "22")


def ssh_connection_display(host: str) -> str:
    """Return the connected SSH host display value."""
    clean_host = host.strip()
    return f"{ssh_config_hostname(clean_host)}:{ssh_config_port(clean_host)}"


def host_selector_options() -> tuple[str, ...]:
    """Return local and SSH host options for the sidebar selector."""
    options = [local_hostname()]
    state_hosts = (
        st.session_state.get("ssh_host_selected", ""),
        st.session_state.get("ssh_connection_host", ""),
        registered_ssh_connection_host(),
    )
    for host_value in state_hosts:
        host = str(host_value).strip()
        if host and host not in options:
            options.append(host)
    for host in ssh_config_hosts():
        if host not in options:
            options.append(host)
    return tuple(options)


def selected_ssh_host() -> str:
    """Return the selected SSH host, or an empty string for local execution."""
    return str(st.session_state.get("ssh_host_selected", "")).strip()


def select_ssh_host_from_widget() -> None:
    """Persist the sidebar host widget selection as the canonical SSH host."""
    selected_host = str(st.session_state.get("ssh_host_selector", "")).strip()
    if not selected_host:
        selected_host = local_hostname()
    st.session_state["ssh_host_selected"] = selected_host
    save_ui_state()


def selected_host_is_local(host: str | None = None) -> bool:
    """Return whether the selected host should use local command execution."""
    host_name = (host if host is not None else selected_ssh_host()).strip()
    local_names = {"", "localhost", "127.0.0.1", "::1", local_hostname()}
    return host_name in local_names


def ssh_control_path(host: str) -> str:
    """Return the ControlMaster socket path for a selected SSH host."""
    host_hash = hashlib.sha256(host.encode("utf-8")).hexdigest()[:16]
    return f"/tmp/hhs-ui-ssh-{host_hash}.sock"


def ssh_config_option() -> str:
    """Return the OpenSSH config option used for UI-managed SSH commands."""
    return '-F "${HOME}/.ssh/config"'


def build_ssh_connect_command(host: str) -> str:
    """Build a local command that opens or validates a ControlMaster connection."""
    safe_host = shlex.quote(host)
    safe_control_path = shlex.quote(ssh_control_path(host))
    safe_config_option = ssh_config_option()
    ssh_options = (
        "-o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 "
        "-o ServerAliveInterval=5 -o ServerAliveCountMax=1"
    )
    return (
        f"ssh {safe_config_option} {ssh_options} -o ControlPath={safe_control_path} -O check {safe_host} "
        ">/dev/null 2>&1 || "
        f"ssh -MNf {safe_config_option} {ssh_options} "
        f"-o ControlMaster=yes -o ControlPersist=10m "
        f"-o ControlPath={safe_control_path} {safe_host}"
    )


def build_ssh_check_command(host: str) -> str:
    """Build a local command that checks an existing ControlMaster connection."""
    safe_host = shlex.quote(host)
    safe_control_path = shlex.quote(ssh_control_path(host))
    safe_config_option = ssh_config_option()
    ssh_options = (
        "-o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 "
        "-o ServerAliveInterval=5 -o ServerAliveCountMax=1"
    )
    return (
        f"ssh {safe_config_option} {ssh_options} "
        f"-o ControlPath={safe_control_path} -O check {safe_host}"
    )


def build_ssh_disconnect_command(host: str) -> str:
    """Build a local command that terminates a ControlMaster connection."""
    safe_host = shlex.quote(host)
    control_path = ssh_control_path(host)
    safe_control_path = shlex.quote(control_path)
    safe_control_path_pattern = shlex.quote(f"ControlPath={control_path}")
    safe_config_option = ssh_config_option()
    return (
        f"ssh {safe_config_option} -o BatchMode=yes "
        f"-o ControlPath={safe_control_path} -O exit {safe_host} >/dev/null 2>&1 || true; "
        f"if command -v pgrep >/dev/null 2>&1; then "
        f"for pid in $(pgrep -f -- {safe_control_path_pattern} 2>/dev/null || true); do "
        '[[ "${pid}" != "$$" ]] && kill -TERM "${pid}" 2>/dev/null || true; '
        "done; "
        "sleep 0.2; "
        f"for pid in $(pgrep -f -- {safe_control_path_pattern} 2>/dev/null || true); do "
        '[[ "${pid}" != "$$" ]] && kill -KILL "${pid}" 2>/dev/null || true; '
        "done; "
        "fi; "
        f"rm -f {safe_control_path}"
    )


def build_ssh_wrapped_command(command: str, host: str) -> str:
    """Build a command that executes the provided Bash command over interactive SSH Bash."""
    safe_host = shlex.quote(host)
    safe_control_path = shlex.quote(ssh_control_path(host))
    safe_config_option = ssh_config_option()
    ssh_options = (
        "-o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 "
        "-o ServerAliveInterval=5 -o ServerAliveCountMax=1"
    )
    safe_remote_command = shlex.quote(command)
    safe_remote_shell = shlex.quote(f"bash -ic {safe_remote_command}")
    return (
        f"ssh -tt {safe_config_option} {ssh_options} -o ControlPath={safe_control_path} "
        f"{safe_host} {safe_remote_shell}"
    )


def registered_ssh_connection_host() -> str:
    """Return the SSH host registered by a previous UI-managed connection."""
    cached_value = cache_get(hhs_ui.UI_CACHE_SSH_CONNECTION_KEY)
    cached_host = str(cached_value.get("host", "")).strip() if cached_value else ""
    if cached_host:
        return cached_host
    for legacy_file in legacy_ssh_connection_files():
        try:
            legacy_host = legacy_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if legacy_host:
            register_ssh_connection(legacy_host)
            unlink_legacy_ssh_connection_files()
            return legacy_host
    unlink_legacy_ssh_connection_files()
    return ""


def register_ssh_connection(host: str) -> None:
    """Persist the UI-managed SSH connection host for later cleanup."""
    clean_host = host.strip()
    if not clean_host:
        clear_registered_ssh_connection()
        return
    cache = load_ui_cache()
    cache[hhs_ui.UI_CACHE_SSH_CONNECTION_KEY] = {"value": {"host": clean_host}}
    save_ui_cache(cache)
    unlink_legacy_ssh_connection_files()


def clear_registered_ssh_connection() -> None:
    """Remove the UI-managed SSH connection cleanup marker."""
    cache = load_ui_cache()
    if hhs_ui.UI_CACHE_SSH_CONNECTION_KEY in cache:
        del cache[hhs_ui.UI_CACHE_SSH_CONNECTION_KEY]
        save_ui_cache(cache)
    unlink_legacy_ssh_connection_files()


def legacy_ssh_connection_files() -> tuple[Path, ...]:
    """Return older standalone SSH marker paths to migrate or remove."""
    return (
        hhs_ui.HHS_CACHE_DIR / ".streamlit-ui-ssh-connection",
        hhs_ui.HHS_DIR / ".streamlit-ui-ssh-connection",
    )


def unlink_legacy_ssh_connection_files() -> None:
    """Remove legacy standalone SSH marker files after cache migration."""
    for legacy_file in legacy_ssh_connection_files():
        try:
            legacy_file.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue


def ssh_connection_is_alive(host: str) -> bool:
    """Return whether the UI-managed ControlMaster connection still responds."""
    if selected_host_is_local(host):
        return False
    result = run_bash_command(
        build_ssh_check_command(host),
        f"Checking SSH host {host}...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=5,
        cache_tag="ssh",
    )
    return result.returncode == 0


def restore_registered_ssh_connection_on_session_start() -> None:
    """Restore or schedule a saved SSH connection when a Streamlit session starts."""
    if st.session_state.get("ssh_connection_restore_checked"):
        return
    st.session_state["ssh_connection_restore_checked"] = True
    reconnect_host = str(
        st.session_state.get(hhs_ui.SSH_RECONNECT_HOST_KEY, "")
    ).strip()
    host = registered_ssh_connection_host() or reconnect_host
    if not host:
        return
    if not ssh_connection_is_alive(host):
        clear_registered_ssh_connection()
        if reconnect_host and not selected_host_is_local(reconnect_host):
            st.session_state["ssh_host_selected"] = reconnect_host
            st.session_state["ssh_host_selector"] = reconnect_host
            st.session_state["ssh_connect_pending"] = reconnect_host
            st.session_state["ssh_disconnect_pending"] = ""
            st.session_state["ssh_reconnect_restore_view_state"] = True
            st.session_state["ssh_connect_pending_message"] = (
                f"Reconnecting to {ssh_connection_display(reconnect_host)}"
            )
        return
    reconnect_state = reconnect_view_state_snapshot()
    clear_host_scoped_session_state()
    restore_reconnect_view_state(reconnect_state)
    st.session_state["ssh_connection_status"] = "connected"
    st.session_state["ssh_connection_host"] = host
    st.session_state["ssh_host_selected"] = host
    st.session_state["ssh_host_selector"] = host
    st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = host
    st.session_state["ssh_connection_error"] = ""
    reset_updater_remote_check_state()
    update_remote_footer_working_directory()
    save_ui_state()


def effective_bash_command(command: str, force_local: bool = False) -> str:
    """Return the local or SSH-wrapped Bash command to execute."""
    host = selected_ssh_host()
    if (
        force_local
        or selected_host_is_local(host)
        or not selected_ssh_host_is_connected(host)
    ):
        return command
    return build_ssh_wrapped_command(command, host)


def command_remote_host(force_local: bool = False) -> str:
    """Return the connected SSH host that will execute a command, if any."""
    host = selected_ssh_host()
    if (
        force_local
        or selected_host_is_local(host)
        or not selected_ssh_host_is_connected(host)
    ):
        return ""
    return host


def command_timeout_seconds(force_local: bool = False) -> int:
    """Return the normalized command timeout for the selected execution host."""
    if command_remote_host(force_local=force_local):
        return hhs_ui.UI_COMMAND_REMOTE_TIMEOUT_SECONDS
    return hhs_ui.UI_COMMAND_LOCAL_TIMEOUT_SECONDS


def effective_command_timeout_seconds(
    timeout_seconds: int | None = None, force_local: bool = False
) -> int:
    """Return an explicit timeout, or the selected host default when unset."""
    if timeout_seconds is not None:
        return max(1, int(timeout_seconds))
    return command_timeout_seconds(force_local=force_local)


def selected_ssh_host_is_connected(host: str | None = None) -> bool:
    """Return whether the selected host has an active UI-managed SSH connection."""
    host_name = (host if host is not None else selected_ssh_host()).strip()
    return (
        bool(host_name)
        and st.session_state.get("ssh_connection_status") == "connected"
        and st.session_state.get("ssh_connection_host") == host_name
    )


def connected_ssh_host() -> str:
    """Return the active UI-managed SSH host, if one is connected."""
    host = str(st.session_state.get("ssh_connection_host", "")).strip()
    if st.session_state.get("ssh_connection_status") == "connected" and host:
        return host
    return ""


def synchronize_selected_ssh_host_with_connection() -> None:
    """Keep the sidebar host selection aligned with an active SSH connection."""
    host = connected_ssh_host()
    if host:
        previous_host = selected_ssh_host()
        st.session_state["ssh_host_selected"] = host
        st.session_state["ssh_host_selector"] = host
        if previous_host != host:
            save_ui_state()


def clear_disconnected_ssh_host(host: str) -> None:
    """Clear stale UI SSH connection state and select the local host."""
    stop_ttyd_session()
    expire_host_scoped_command_state()
    st.session_state["ssh_connection_status"] = ""
    st.session_state["ssh_connection_host"] = ""
    st.session_state["ssh_connection_error"] = ""
    st.session_state["ssh_connect_pending"] = ""
    st.session_state["ssh_disconnect_pending"] = ""
    st.session_state["ssh_host_selected"] = local_hostname()
    st.session_state["ssh_host_selector"] = local_hostname()
    st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""
    st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)
    clear_registered_ssh_connection()
    cache_clear()
    save_ui_state()


def clear_host_scoped_session_state() -> None:
    """Clear UI state that belongs to the previously selected execution host."""
    stop_ttyd_session()
    expire_host_scoped_command_state()
    preserved_keys = {
        hhs_ui.THEME_SELECTED_KEY,
        "theme_last_seen",
        "ssh_connect_pending",
        "ssh_disconnect_pending",
        "ssh_connection_status",
        "ssh_connection_host",
        "ssh_connection_error",
        "ssh_connection_dialog_title",
        "ssh_connection_restore_checked",
        "ssh_host_selected",
        "ssh_host_selector",
        "footer_hhs_version_cache_loaded",
        "footer_shell_version_dialog_title",
        "footer_shell_version_output",
    }
    table_keys = {
        hhs_ui.AI_MODEL_TABLE_KEY,
        hhs_ui.ALIAS_TABLE_KEY,
        hhs_ui.CMD_TABLE_KEY,
        hhs_ui.DIR_TABLE_KEY,
        hhs_ui.DOCKER_CONTAINER_TABLE_KEY,
        hhs_ui.DOCKER_IMAGE_TABLE_KEY,
        hhs_ui.ENV_TABLE_KEY,
        hhs_ui.HISTORY_COMMAND_TABLE_KEY,
        hhs_ui.HISTORY_DIRECTORY_TABLE_KEY,
        hhs_ui.HOME_SHOPTS_TABLE_KEY,
        hhs_ui.HOME_TOOLS_TABLE_KEY,
        hhs_ui.PATH_TABLE_KEY,
        hhs_ui.PROCESS_TABLE_KEY,
        hhs_ui.SERVICE_TABLE_KEY,
        hhs_ui.SSH_TUNNEL_TABLE_KEY,
    }
    for key in list(st.session_state.keys()):
        if key in preserved_keys:
            continue
        if (
            key in hhs_ui.PERSISTED_UI_KEYS
            or key in table_keys
            or key.startswith(hhs_ui.PERSISTED_UI_KEY_PREFIXES)
        ):
            st.session_state.pop(key, None)

    st.session_state["active_view"] = "Home"
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = False
    st.session_state[hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] = "Home"
    st.session_state[hhs_ui.DOCUMENT_SELECTED_KEY] = "README"
    st.session_state["ai_chat_messages"] = []
    st.session_state["ai_context_output"] = ""
    st.session_state["ai_context_error"] = ""
    st.session_state["ai_prompt_editor"] = ""
    st.session_state["ai_prompt_error"] = ""
    st.session_state["ai_prompt_loaded"] = False
    st.session_state["ai_view"] = "CHAT"
    st.session_state[hhs_ui.TERMINAL_CWD_KEY] = "."
    st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = False
    cache_clear()


def ssh_shared_connection_closed(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether a failed SSH command reports a closed shared connection."""
    if result.returncode != 255:
        return False
    output = strip_ansi(f"{result.stdout or ''}\n{result.stderr or ''}").lower()
    return "shared connection to " in output and " closed" in output


def strip_ssh_shared_connection_notice(value: str) -> str:
    """Return command output without OpenSSH ControlMaster close notices."""
    output_lines = []
    for line in value.splitlines(keepends=True):
        clean_line = strip_ansi(line).strip().lower()
        if clean_line.startswith("shared connection to ") and clean_line.endswith(
            " closed."
        ):
            continue
        output_lines.append(line)
    return "".join(output_lines)


def remote_command_startup_line_is_noise(line: str) -> bool:
    """Return whether a remote command line is HomeSetup shell startup chatter."""
    clean_line = strip_ansi(line).strip()
    if not clean_line:
        return False
    if clean_line.startswith("[bash] HomeSetup is starting"):
        return True
    if "Welcome " in clean_line and " to HomeSetup v" in clean_line:
        return True
    return bool(re.fullmatch(r"Shell option \S+ set to (?:on|off)", clean_line))


def strip_remote_command_startup_chatter(value: str) -> str:
    """Return remote command output without HomeSetup shell startup chatter."""
    output_lines: list[str] = []
    removed_chatter = False
    for line in value.splitlines(keepends=True):
        if remote_command_startup_line_is_noise(line):
            removed_chatter = True
            continue
        if removed_chatter and not output_lines and not strip_ansi(line).strip():
            continue
        output_lines.append(line)
    return "".join(output_lines)


def sanitize_remote_command_result(
    host: str, result: subprocess.CompletedProcess[str]
) -> subprocess.CompletedProcess[str]:
    """Return a remote command result with HomeSetup startup chatter stripped."""
    if not host:
        return result
    stdout = strip_remote_command_startup_chatter(result.stdout or "")
    stderr = strip_remote_command_startup_chatter(result.stderr or "")
    if stdout == (result.stdout or "") and stderr == (result.stderr or ""):
        return result
    return subprocess.CompletedProcess(result.args, result.returncode, stdout, stderr)


def ssh_output_is_only_shared_close(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether failed SSH output only contains the shared-close notice."""
    if not ssh_shared_connection_closed(result):
        return False
    lines = [
        line.strip().lower()
        for line in strip_ansi(
            f"{result.stdout or ''}\n{result.stderr or ''}"
        ).splitlines()
        if line.strip()
    ]
    remaining_lines = [
        line
        for line in lines
        if not (line.startswith("shared connection to ") and line.endswith(" closed."))
    ]
    return not remaining_lines


def completed_disconnected_ssh_process(
    command: str, host: str
) -> subprocess.CompletedProcess[str]:
    """Build a failed command result for a detected stale SSH connection."""
    return subprocess.CompletedProcess(
        [RUN_SHELL, "-lc", command],
        255,
        "",
        f"Shared connection to {ssh_config_hostname(host)} closed.",
    )


def handle_remote_command_result(
    host: str, result: subprocess.CompletedProcess[str]
) -> bool:
    """Synchronize UI state when a remote command shows the SSH connection closed."""
    if host and (
        ssh_output_is_only_shared_close(result) or ssh_shared_connection_closed(result)
    ):
        clear_disconnected_ssh_host(host)
        return True
    return False


def request_ssh_host_connect() -> None:
    """Schedule an SSH ControlMaster connection for the selected host."""
    host = selected_ssh_host()
    if selected_host_is_local(host):
        return
    st.session_state["ssh_connect_pending"] = host
    st.session_state["ssh_connect_pending_message"] = ""
    st.session_state["ssh_disconnect_pending"] = ""
    cache_clear()
    save_ui_state()


def request_ssh_host_disconnection() -> None:
    """Schedule an SSH ControlMaster disconnection for the selected host."""
    host = selected_ssh_host()
    connected_host = str(st.session_state.get("ssh_connection_host", "")).strip()
    if connected_host:
        host = connected_host
    if selected_host_is_local(host):
        return
    st.session_state["ssh_disconnect_pending"] = host
    st.session_state["ssh_connect_pending"] = ""
    st.session_state["ssh_connect_pending_message"] = ""


def execute_pending_ssh_connection() -> bool:
    """Open a pending SSH ControlMaster connection from the normal render flow."""
    if complete_ssh_connection():
        return True
    host = str(st.session_state.get("ssh_connect_pending", "")).strip()
    if not host:
        return False
    loader_message = str(
        st.session_state.get("ssh_connect_pending_message", "")
    ).strip()
    loader_message = loader_message or f"Connecting to SSH host {host}..."
    st.session_state.pop("ssh_reconnect_restore_view_state", False)
    reconnect_state = reconnect_view_state_snapshot()
    was_terminal_active = terminal_document_view_is_active()
    st.session_state["ssh_connect_pending"] = ""
    st.session_state["ssh_connect_pending_message"] = ""
    st.session_state["ssh_connection_status"] = "connecting"
    st.session_state["ssh_connection_host"] = host
    started = start_background_bash_command(
        SSH_CONNECT_JOB,
        build_ssh_connect_command(host),
        loader_message,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        force_local=True,
        metadata={
            "ssh_host": host,
            "reconnect_state": reconnect_state,
            "was_terminal_active": was_terminal_active,
        },
    )
    if started:
        render_background_job_status(SSH_CONNECT_JOB)
        return True
    else:
        push_floating_status(
            "Another SSH connection command is already running.",
            "warn",
        )
    return False


def complete_ssh_connection() -> bool:
    """Complete or render the active SSH connect background job."""
    job = background_job_state(SSH_CONNECT_JOB)
    if not job:
        return False
    completed = background_job_result(SSH_CONNECT_JOB)
    if completed is None:
        render_background_job_status(SSH_CONNECT_JOB)
        return True
    result, metadata = completed
    host = str(metadata.get("ssh_host", "")).strip()
    reconnect_state = metadata.get("reconnect_state")
    if not isinstance(reconnect_state, dict):
        reconnect_state = {}
    was_terminal_active = bool(metadata.get("was_terminal_active", False))
    if result.returncode == 0:
        clear_host_scoped_session_state()
        restore_reconnect_view_state(reconnect_state)
        st.session_state["ssh_connection_status"] = "connected"
        st.session_state["ssh_connection_host"] = host
        st.session_state["ssh_host_selected"] = host
        st.session_state["ssh_host_selector"] = host
        st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = host
        st.session_state["ssh_connection_error"] = ""
        st.session_state["ssh_connection_dialog_title"] = ""
        reset_updater_remote_check_state()
        update_remote_footer_working_directory()
        restore_terminal_document_view(was_terminal_active)
        push_floating_status(
            f"Connected to remote  {ssh_connection_display(host)}",
            "info",
        )
        register_ssh_connection(host)
        schedule_ollama_service_availability_refresh()
        save_ui_state()
    else:
        st.session_state["ssh_connection_status"] = "failed"
        st.session_state["ssh_connection_host"] = ""
        st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""
        st.session_state["ssh_connection_error"] = strip_ansi(
            result.stderr or result.stdout or f"Unable to connect to SSH host {host}."
        )
        st.session_state["ssh_connection_dialog_title"] = f"Failed to connect to {host}"
        push_floating_status(f"Failed to connect to remote: {host}", "error")
    return False


def clear_completed_ssh_disconnection(
    host: str, result: subprocess.CompletedProcess[str]
) -> None:
    """Clear UI connection state after an SSH disconnect command finishes."""
    disconnect_view_state = reconnect_view_state_snapshot()
    clear_host_scoped_session_state()
    restore_reconnect_view_state(disconnect_view_state)
    st.session_state["ssh_connection_status"] = ""
    st.session_state["ssh_connection_host"] = ""
    st.session_state["ssh_connection_error"] = ""
    st.session_state["ssh_connection_dialog_title"] = ""
    st.session_state["ssh_host_selected"] = local_hostname()
    st.session_state["ssh_host_selector"] = local_hostname()
    st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""
    st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)
    clear_registered_ssh_connection()
    cache_clear()
    if result.returncode == 124:
        push_floating_status(
            f"SSH disconnect cleanup timed out for {ssh_connection_display(host)}.",
            "warn",
        )
    elif result.returncode != 0:
        push_floating_status(
            clean_command_status_message(
                result.stderr
                or result.stdout
                or f"Unable to disconnect SSH host {host}."
            ),
            "warn",
        )
    schedule_ollama_service_availability_refresh()
    save_ui_state()


def complete_ssh_disconnection() -> bool:
    """Complete or render the active SSH disconnect background job."""
    job = background_job_state(SSH_DISCONNECT_JOB)
    if not job:
        return False
    completed = background_job_result(SSH_DISCONNECT_JOB)
    if completed is None:
        render_background_job_status(SSH_DISCONNECT_JOB)
        return True
    result, metadata = completed
    host = str(metadata.get("ssh_host", "")).strip()
    if not host:
        host = str(st.session_state.get("ssh_connection_host", "")).strip()
    clear_completed_ssh_disconnection(host, result)
    return False


def execute_pending_ssh_disconnection() -> bool:
    """Close a pending SSH ControlMaster connection from the normal render flow."""
    if complete_ssh_disconnection():
        return True
    host = str(st.session_state.get("ssh_disconnect_pending", "")).strip()
    if not host:
        return False
    stop_ttyd_session()
    st.session_state["ssh_disconnect_pending"] = ""
    st.session_state["ssh_connect_pending_message"] = ""
    st.session_state["ssh_connection_status"] = "disconnecting"
    st.session_state["ssh_connection_host"] = host
    expire_host_scoped_command_state()
    st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""
    st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)
    cache_clear()
    start_background_bash_command(
        SSH_DISCONNECT_JOB,
        build_ssh_disconnect_command(host),
        f"Disconnecting from SSH host {host}...",
        10,
        force_local=True,
        metadata={"ssh_host": host},
    )
    render_background_job_status(SSH_DISCONNECT_JOB)
    return True


def clear_ssh_connection_dialog() -> None:
    """Clear the SSH connection result dialog state."""
    st.session_state["ssh_connection_dialog_title"] = ""


def close_ssh_connection_dialog() -> None:
    """Close the SSH connection result dialog."""
    set_overlay(False)
    synchronize_selected_ssh_host_with_connection()
    clear_ssh_connection_dialog()


def dismiss_streamlit_dialog() -> None:
    """Dismiss the currently mounted Streamlit dialog in the browser."""
    components.html(
        """
        <script>
          const doc = window.parent.document;
          const dialog = doc.querySelector('[data-testid="stDialog"], [role="dialog"]');
          const close_button = dialog?.querySelector('button[aria-label="Close"]');
          if (close_button) {
            close_button.click();
          } else {
            doc.dispatchEvent(new KeyboardEvent("keydown", {
              bubbles: true,
              cancelable: true,
              key: "Escape"
            }));
          }
        </script>
        """,
        height=0,
    )


def render_ssh_connection_dialog() -> bool:
    """Render the SSH connection result dialog when a connection attempt completes."""
    title = str(st.session_state.get("ssh_connection_dialog_title", "")).strip()
    if not title:
        return False
    set_overlay(False)
    return pop_dialog(
        title=title,
        buttons=(
            {
                "label": "Close",
                "key": "ssh_connection_dialog_close_button",
            },
        ),
        close_callback=close_ssh_connection_dialog,
    )


def run_bash_command(
    command: str,
    loader_message: str,
    close_dialogs: bool = False,
    ttl_seconds: int = hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
    use_cache: bool = True,
    force_local: bool = False,
    timeout_seconds: int | None = None,
    cache_tag: str = "default",
    cache_key_override: str | None = None,
    show_overlay: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a Bash command with tagged command-result caching and a preloader."""
    remote_host = command_remote_host(force_local=force_local)
    command_to_run = effective_bash_command(command, force_local=force_local)
    selection_only_rerun = table_selection_rerun_in_progress()
    show_command_overlay = show_overlay and not selection_only_rerun
    effective_timeout = effective_command_timeout_seconds(
        timeout_seconds, force_local=force_local
    )
    cache_key = cache_key_override or command_cache_key(command_to_run, cache_tag)
    snapshot_value = (
        command_result_snapshot_get(cache_key) if selection_only_rerun else None
    )
    if snapshot_value is not None:
        return sanitize_remote_command_result(
            remote_host, completed_process_from_cache(command_to_run, snapshot_value)
        )

    cached_value = cache_get(cache_key) if use_cache else None
    if use_cache and cached_value is not None:
        command_result_snapshot_set(cache_key, cached_value)
        result = sanitize_remote_command_result(
            remote_host, completed_process_from_cache(command_to_run, cached_value)
        )
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result

    if remote_host and not ssh_connection_is_alive(remote_host):
        result = completed_disconnected_ssh_process(command_to_run, remote_host)
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result

    if show_command_overlay:
        set_overlay(
            True,
            loader_message,
            close_dialogs=close_dialogs,
            timeout_seconds=effective_timeout,
        )
    try:
        result = run_bash_subprocess(command_to_run, effective_timeout)
        result = sanitize_remote_command_result(remote_host, result)
        disconnected = handle_remote_command_result(remote_host, result)
        if not ssh_shared_connection_closed(result):
            command_result_snapshot_set(
                cache_key, cache_value_from_completed_process(result)
            )
        if use_cache and not ssh_shared_connection_closed(result):
            cache_set(
                cache_key, cache_value_from_completed_process(result), ttl_seconds
            )
        if disconnected:
            st.rerun()
        return result
    except subprocess.TimeoutExpired as error:
        result = subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command_to_run],
            124,
            error.stdout or "",
            error.stderr or f"Command timed out after {effective_timeout} seconds.",
        )
        result = sanitize_remote_command_result(remote_host, result)
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result
    finally:
        if show_command_overlay:
            set_overlay(False)


def run_bash_subprocess(
    command: str, timeout_seconds: int | None
) -> subprocess.CompletedProcess[str]:
    """Run a Bash command and kill the whole process group on timeout."""
    process = subprocess.Popen(
        [RUN_SHELL, "-lc", command],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=command_env(),
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        return subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command],
            int(process.returncode or 0),
            stdout,
            stderr,
        )
    except subprocess.TimeoutExpired as error:
        stop_process(process)
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            stdout = error.stdout or ""
            stderr = error.stderr or ""
        timeout_message = f"Command timed out after {timeout_seconds} seconds."
        return subprocess.CompletedProcess(
            [RUN_SHELL, "-lc", command],
            124,
            stdout or "",
            stderr or timeout_message,
        )


def background_job_state_key(job_name: str) -> str:
    """Return the Streamlit session key used for a background command job."""
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", job_name.strip())
    return f"_hhs_background_job_{safe_name or 'job'}"


def background_job_state(job_name: str) -> dict[str, object] | None:
    """Return the stored background job state for a named job."""
    value = st.session_state.get(background_job_state_key(job_name))
    return value if isinstance(value, dict) else None


def background_job_process(job: dict[str, object]) -> subprocess.Popen[str] | None:
    """Return the Popen object stored on a background job state."""
    process = job.get("process")
    return process if isinstance(process, subprocess.Popen) else None


def background_job_is_running(job_name: str) -> bool:
    """Return whether the named background job still has a live subprocess."""
    job = background_job_state(job_name)
    process = background_job_process(job) if job else None
    return bool(process is not None and process.poll() is None)


def background_job_timeout_seconds(job: dict[str, object]) -> float:
    """Return the configured timeout for one background command job."""
    try:
        return float(job.get("timeout_seconds", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def background_job_has_timed_out(job: dict[str, object]) -> bool:
    """Return whether one background command job has exceeded its timeout."""
    timeout_seconds = background_job_timeout_seconds(job)
    return (
        timeout_seconds > 0 and background_job_elapsed_seconds(job) >= timeout_seconds
    )


def stop_background_job(job_name: str) -> None:
    """Stop and forget one background job and its temporary output files."""
    job_key = background_job_state_key(job_name)
    job = background_job_state(job_name)
    if job is None:
        st.session_state.pop(job_key, None)
        return
    process = background_job_process(job)
    if process is not None:
        stop_process(process)
    st.session_state.pop(job_key, None)
    cleanup_background_job_files(job)


def stop_background_jobs(job_names: tuple[str, ...]) -> None:
    """Stop and forget each named background job."""
    for job_name in job_names:
        stop_background_job(job_name)


def stop_background_jobs_with_state_prefix(state_key_prefix: str) -> None:
    """Stop and forget background jobs whose Streamlit state key has a prefix."""
    for state_key in list(st.session_state):
        if not str(state_key).startswith(state_key_prefix):
            continue
        job = st.session_state.get(state_key)
        if not isinstance(job, dict):
            st.session_state.pop(state_key, None)
            continue
        process = background_job_process(job)
        if process is not None:
            stop_process(process)
        st.session_state.pop(state_key, None)
        cleanup_background_job_files(job)


def background_job_elapsed_seconds(job: dict[str, object]) -> float:
    """Return the elapsed runtime for a background command job."""
    try:
        started_at = float(job.get("started_at", 0.0) or 0.0)
    except (TypeError, ValueError):
        started_at = 0.0
    return max(0.0, time.time() - started_at) if started_at else 0.0


def start_background_bash_command(
    job_name: str,
    command: str,
    description: str,
    timeout_seconds: int,
    force_local: bool = False,
    metadata: dict[str, object] | None = None,
) -> bool:
    """Start a Bash command in the background and store its process state."""
    if background_job_is_running(job_name):
        return False

    stdout_file = tempfile.NamedTemporaryFile(
        "w", delete=False, prefix=f"{job_name}-stdout-", encoding="utf-8"
    )
    stderr_file = tempfile.NamedTemporaryFile(
        "w", delete=False, prefix=f"{job_name}-stderr-", encoding="utf-8"
    )
    stdout_path = stdout_file.name
    stderr_path = stderr_file.name
    stdout_file.close()
    stderr_file.close()

    remote_host = command_remote_host(force_local=force_local)
    effective_timeout = effective_command_timeout_seconds(
        timeout_seconds, force_local=force_local
    )
    command_to_run = effective_bash_command(command, force_local=force_local)
    stdout_handle = Path(stdout_path).open("w", encoding="utf-8")
    stderr_handle = Path(stderr_path).open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            [RUN_SHELL, "-lc", command_to_run],
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            env=command_env(),
            text=True,
            start_new_session=True,
        )
    finally:
        stdout_handle.close()
        stderr_handle.close()

    st.session_state[background_job_state_key(job_name)] = {
        "process": process,
        "command": command_to_run,
        "description": description,
        "remote_host": remote_host,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "started_at": time.time(),
        "timeout_seconds": effective_timeout,
        "metadata": metadata or {},
    }
    return True


def read_background_job_file(job: dict[str, object], key: str) -> str:
    """Return the captured output text for one background job output file."""
    raw_path = str(job.get(key, ""))
    if not raw_path:
        return ""
    file_path = Path(raw_path)
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def cleanup_background_job_files(job: dict[str, object]) -> None:
    """Remove temporary output files owned by a background command job."""
    for key in ("stdout_path", "stderr_path"):
        raw_path = str(job.get(key, ""))
        if not raw_path:
            continue
        file_path = Path(raw_path)
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            continue


def background_job_result(
    job_name: str,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]] | None:
    """Return a completed background job result, or None while it is running."""
    job_key = background_job_state_key(job_name)
    job = background_job_state(job_name)
    if job is None:
        return None

    process = background_job_process(job)
    if process is None:
        st.session_state.pop(job_key, None)
        cleanup_background_job_files(job)
        return None

    timeout_seconds = background_job_timeout_seconds(job)
    if process.poll() is None and background_job_has_timed_out(job):
        stop_process(process)

    if process.poll() is None:
        return None

    stdout = read_background_job_file(job, "stdout_path")
    stderr = read_background_job_file(job, "stderr_path")
    returncode = int(process.returncode or 0)
    if background_job_has_timed_out(job):
        if returncode != 0:
            returncode = 124
    if returncode == 124 and not stderr:
        stderr = f"Command timed out after {int(timeout_seconds)} seconds."
    command = str(job.get("command", ""))
    result = subprocess.CompletedProcess(
        [RUN_SHELL, "-lc", command],
        returncode,
        stdout,
        stderr,
    )
    remote_host = str(job.get("remote_host", ""))
    result = sanitize_remote_command_result(remote_host, result)
    st.session_state.pop(job_key, None)
    cleanup_background_job_files(job)
    metadata = job.get("metadata")
    return result, metadata if isinstance(metadata, dict) else {}


@st.fragment(run_every="2s")
def render_background_job_status(job_name: str, message: str = "") -> None:
    """Render and poll a compact status line for a background command."""
    job = background_job_state(job_name)
    if not job:
        return
    process = background_job_process(job)
    if (
        process is not None
        and process.poll() is None
        and background_job_has_timed_out(job)
    ):
        stop_process(process)
        st.rerun()
        return
    if not background_job_is_running(job_name):
        st.rerun()
        return
    description = message.strip() or str(job.get("description", "Command")).strip()
    try:
        started_at = float(job.get("started_at", 0.0) or 0.0)
    except (TypeError, ValueError):
        started_at = 0.0
    render_command_loader(
        description or "Command running...",
        started_at or None,
        int(background_job_timeout_seconds(job) or command_timeout_seconds()),
    )


@st.fragment(run_every="2s")
def poll_background_job_completion(job_name: str) -> None:
    """Poll one background job without rendering a visible loader."""
    job = background_job_state(job_name)
    if not job:
        return
    process = background_job_process(job)
    if (
        process is not None
        and process.poll() is None
        and background_job_has_timed_out(job)
    ):
        stop_process(process)
        st.rerun()
        return
    if not background_job_is_running(job_name):
        st.rerun()


def load_ui_cache() -> dict[str, dict[str, object]]:
    """Load the UI cache file and prune expired entries without writing on reads."""
    global UI_CACHE_MEMORY, UI_CACHE_MEMORY_MTIME
    cache_mtime = ui_cache_mtime()
    if UI_CACHE_MEMORY_MTIME == cache_mtime:
        UI_CACHE_MEMORY = prune_ui_cache_entries(UI_CACHE_MEMORY)
        return dict(UI_CACHE_MEMORY)
    if not hhs_ui.UI_CACHE_FILE.exists():
        UI_CACHE_MEMORY = {}
        UI_CACHE_MEMORY_MTIME = 0.0
        return {}
    try:
        data = json.loads(hhs_ui.UI_CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        UI_CACHE_MEMORY = {}
        UI_CACHE_MEMORY_MTIME = cache_mtime
        return {}
    if not isinstance(data, dict):
        UI_CACHE_MEMORY = {}
        UI_CACHE_MEMORY_MTIME = cache_mtime
        return {}
    cache = {
        key: value
        for key, value in data.items()
        if ui_cache_key_is_supported(key) and isinstance(value, dict)
    }
    pruned_cache = prune_ui_cache_entries(cache)
    UI_CACHE_MEMORY = dict(pruned_cache)
    UI_CACHE_MEMORY_MTIME = cache_mtime
    return pruned_cache


def ui_cache_mtime() -> float:
    """Return the UI cache file modification time used for memory cache coherency."""
    try:
        return hhs_ui.UI_CACHE_FILE.stat().st_mtime
    except OSError:
        return 0.0


def save_ui_cache(cache: dict[str, dict[str, object]]) -> None:
    """Persist the UI cache file."""
    global UI_CACHE_MEMORY, UI_CACHE_MEMORY_MTIME
    try:
        hhs_ui.UI_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        hhs_ui.UI_CACHE_FILE.write_text(
            json.dumps(cache, indent=2) + "\n", encoding="utf-8"
        )
        UI_CACHE_MEMORY = dict(cache)
        UI_CACHE_MEMORY_MTIME = ui_cache_mtime()
    except OSError:
        return


def ui_cache_key_is_supported(key: object) -> bool:
    """Return whether a persisted UI cache key belongs to the supported schema."""
    if not isinstance(key, str):
        return False
    return (
        key.startswith("command_hash:")
        or key.startswith("command_tag:")
        or key.startswith("search_terms:")
        or key == hhs_ui.UI_CACHE_SSH_CONNECTION_KEY
    )


def ui_cache_metadata_key(key: str) -> bool:
    """Return whether a UI cache key stores non-expiring UI metadata."""
    return key.startswith("ui:")


def ui_cache_preserved_on_clear_key(key: str) -> bool:
    """Return whether a UI cache key should survive broad command-cache clears."""
    return (
        ui_cache_metadata_key(key)
        or key == hhs_ui_constants.SEARCH_TERM_HISTORY_CACHE_KEY
    )


def prune_ui_cache_entries(
    cache: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Return cache entries whose TTL has not expired."""
    now = time.time()
    return {
        key: entry
        for key, entry in cache.items()
        if (
            ui_cache_metadata_key(key)
            or (
                isinstance(entry.get("expires_at"), int | float)
                and float(entry["expires_at"]) > now
            )
        )
    }


def format_cache_ttl(ttl_seconds: int | float | str) -> str:
    """Format cache TTL using the actual expiry unit."""
    return f"{int(parse_cache_ttl_seconds(ttl_seconds))}s"


def parse_cache_ttl_seconds(ttl: int | float | str) -> float:
    """Parse cache TTL strings that carry their expiry unit."""
    if isinstance(ttl, int | float):
        return float(ttl)
    clean_ttl = ttl.strip().lower()
    if clean_ttl.endswith("ms"):
        return float(clean_ttl[:-2] or 0) / 1000
    if clean_ttl.endswith("s"):
        return float(clean_ttl[:-1] or 0)
    if clean_ttl.endswith("m"):
        return float(clean_ttl[:-1] or 0) * 60
    if clean_ttl.endswith("h"):
        return float(clean_ttl[:-1] or 0) * 3600
    return float(clean_ttl or 0)


def cache_get(key: str) -> dict[str, object] | None:
    """Return a non-expired cache entry value."""
    entry = load_ui_cache().get(key)
    value = entry.get("value") if isinstance(entry, dict) else None
    return value if isinstance(value, dict) else None


def command_result_snapshots() -> dict[str, dict[str, object]]:
    """Return in-session command results used for table selection-only reruns."""
    snapshots = st.session_state.setdefault(
        hhs_ui_constants.COMMAND_RESULT_SNAPSHOT_KEY, {}
    )
    if not isinstance(snapshots, dict):
        snapshots = {}
        st.session_state[hhs_ui_constants.COMMAND_RESULT_SNAPSHOT_KEY] = snapshots
    return snapshots


def command_result_snapshot_get(key: str) -> dict[str, object] | None:
    """Return the last in-session command result for a command cache key."""
    value = command_result_snapshots().get(key)
    return value if isinstance(value, dict) else None


def command_result_snapshot_set(key: str, value: dict[str, object]) -> None:
    """Store an in-session command result for fast selection-only reruns."""
    snapshots = command_result_snapshots()
    snapshots[key] = value
    while len(snapshots) > hhs_ui_constants.COMMAND_RESULT_SNAPSHOT_LIMIT:
        snapshots.pop(next(iter(snapshots)))


def command_result_snapshot_delete(key_prefix: str) -> None:
    """Delete in-session command results that match a key or key prefix."""
    snapshots = command_result_snapshots()
    for key in list(snapshots):
        if key == key_prefix or key.startswith(f"{key_prefix}:"):
            snapshots.pop(key, None)


def command_result_snapshot_delete_tag(cache_tag: str) -> None:
    """Delete in-session command results for a command-result tag."""
    tag_prefix = f"command_tag:{safe_cache_tag(cache_tag)}:"
    command_result_snapshot_delete(tag_prefix.rstrip(":"))


def command_result_snapshot_clear() -> None:
    """Delete all in-session command results."""
    st.session_state[hhs_ui_constants.COMMAND_RESULT_SNAPSHOT_KEY] = {}


def parsed_rows_cache() -> dict[str, list[dict[str, object]]]:
    """Return the in-session parsed rows cache used across selection reruns."""
    cache = st.session_state.setdefault(hhs_ui_constants.PARSED_ROWS_CACHE_KEY, {})
    if not isinstance(cache, dict):
        cache = {}
        st.session_state[hhs_ui_constants.PARSED_ROWS_CACHE_KEY] = cache
    return cache


def parsed_rows_cache_key(parser_name: str, output: str) -> str:
    """Return a stable parsed-row cache key for one parser and command output."""
    output_hash = hashlib.sha256(output.encode("utf-8")).hexdigest()
    return f"{parser_name}:{output_hash}"


def parse_rows_cached(
    parser_name: str,
    output: str,
    parser: Callable[[str], list[dict[str, object]]],
) -> list[dict[str, object]]:
    """Return parsed rows from an in-session cache keyed by parser and output."""
    cache = parsed_rows_cache()
    cache_key = parsed_rows_cache_key(parser_name, output)
    cached_rows = cache.get(cache_key)
    if isinstance(cached_rows, list):
        return [dict(row) for row in cached_rows if isinstance(row, dict)]
    rows = parser(output)
    cache[cache_key] = [dict(row) for row in rows]
    while len(cache) > hhs_ui_constants.PARSED_ROWS_CACHE_LIMIT:
        cache.pop(next(iter(cache)))
    return [dict(row) for row in rows]


def clear_parsed_rows_cache() -> None:
    """Delete all in-session parsed command rows."""
    st.session_state[hhs_ui_constants.PARSED_ROWS_CACHE_KEY] = {}


def log_render_cache() -> dict[str, str]:
    """Return the in-session rendered log output cache."""
    cache = st.session_state.setdefault(hhs_ui_constants.LOG_RENDER_CACHE_KEY, {})
    if not isinstance(cache, dict):
        cache = {}
        st.session_state[hhs_ui_constants.LOG_RENDER_CACHE_KEY] = cache
    return cache


def rendered_log_output_cached(
    output: str, log_filter: str, log_text_filter: str
) -> str:
    """Return filtered and highlighted log output from an in-session cache."""
    filter_key = f"{log_filter}\0{log_text_filter}"
    output_hash = hashlib.sha256(output.encode("utf-8")).hexdigest()
    cache_key = f"{filter_key}:{output_hash}"
    cache = log_render_cache()
    cached_output = cache.get(cache_key)
    if isinstance(cached_output, str):
        return cached_output
    rendered_output = colorize_log_output(
        filter_log_output(output, log_filter, log_text_filter),
        log_text_filter if log_filter == "Containing" else "",
    )
    cache[cache_key] = rendered_output
    while len(cache) > hhs_ui_constants.LOG_RENDER_CACHE_LIMIT:
        cache.pop(next(iter(cache)))
    return rendered_output


def clear_render_caches() -> None:
    """Delete in-session render caches derived from command results."""
    clear_parsed_rows_cache()
    st.session_state[hhs_ui_constants.LOG_RENDER_CACHE_KEY] = {}


def cache_set(
    key: str,
    value: dict[str, object],
    ttl_seconds: int = hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
) -> None:
    """Store a value in the UI cache with a TTL."""
    cache = load_ui_cache()
    ttl = format_cache_ttl(ttl_seconds)
    cache[key] = {
        "ttl": ttl,
        "expires_at": time.time() + parse_cache_ttl_seconds(ttl),
        "value": value,
    }
    save_ui_cache(cache)


def cache_delete(key_prefix: str) -> None:
    """Delete cache entries matching a key or key prefix."""
    cache = load_ui_cache()
    updated_cache = {
        key: value
        for key, value in cache.items()
        if key != key_prefix and not key.startswith(f"{key_prefix}:")
    }
    if updated_cache != cache:
        save_ui_cache(updated_cache)
    command_result_snapshot_delete(key_prefix)


def cache_delete_tag(cache_tag: str) -> None:
    """Delete all UI cache entries for a specific command-result tag."""
    cache = load_ui_cache()
    tag_prefix = f"command_tag:{safe_cache_tag(cache_tag)}:"
    updated_cache = {
        key: value for key, value in cache.items() if not key.startswith(tag_prefix)
    }
    if updated_cache != cache:
        save_ui_cache(updated_cache)
    command_result_snapshot_delete_tag(cache_tag)


def cache_delete_command(command: str, cache_tag: str = "default") -> None:
    """Delete the UI cache entry for a specific command-result tag and command."""
    cache = load_ui_cache()
    cache_key = command_cache_key(effective_bash_command(command), cache_tag)
    if cache_key in cache:
        del cache[cache_key]
        save_ui_cache(cache)
    command_result_snapshot_delete(cache_key)


def cache_clear() -> None:
    """Delete all UI cache entries."""
    metadata_cache = {
        key: value
        for key, value in load_ui_cache().items()
        if ui_cache_preserved_on_clear_key(key)
    }
    save_ui_cache(metadata_cache)
    command_result_snapshot_clear()
    clear_render_caches()


def clear_cached_ui_data_preserving_state(show_status: bool = True) -> None:
    """Clear cached command data while preserving UI selections and metadata."""
    stop_background_jobs(CACHE_CLEAR_BACKGROUND_JOBS)
    stop_background_jobs_with_state_prefix(background_job_state_key("cached_"))
    cache_clear()
    st.session_state["footer_hhs_version_cache_loaded"] = False
    for state_key in list(st.session_state):
        if str(state_key).startswith("_hhs_cached_command_error_"):
            st.session_state.pop(state_key, None)
    if show_status:
        push_floating_status("Cache cleared.", "info")


def expire_host_scoped_command_state() -> None:
    """Expire command data and jobs that belong to the previous execution host."""
    stop_background_jobs(HOST_SWITCH_BACKGROUND_JOBS)
    for cache_tag in HOST_SWITCH_CACHE_TAGS:
        cache_delete_tag(cache_tag)
    clear_render_caches()
    for state_key in HOST_SWITCH_STATE_KEYS:
        st.session_state.pop(state_key, None)
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY] = False
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY] = False
    for table_key in (
        hhs_ui.ENV_TABLE_KEY,
        hhs_ui.PROCESS_TABLE_KEY,
        hhs_ui.SERVICE_TABLE_KEY,
    ):
        st.session_state.pop(table_key, None)
    for counter_key in (
        hhs_ui.ENV_TABLE_RESET_COUNTER_KEY,
        hhs_ui.SERVICE_TABLE_RESET_COUNTER_KEY,
    ):
        reset_counter = st.session_state.setdefault(counter_key, 0)
        st.session_state[counter_key] = (
            reset_counter + 1 if isinstance(reset_counter, int) else 1
        )


def completed_process_from_cache(
    command: str, cached_value: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    """Build a CompletedProcess from a cached command result."""
    return subprocess.CompletedProcess(
        [RUN_SHELL, "-lc", command],
        int(cached_value.get("returncode", 0)),
        str(cached_value.get("stdout", "")),
        str(cached_value.get("stderr", "")),
    )


def cache_value_from_completed_process(
    result: subprocess.CompletedProcess[str],
) -> dict[str, object]:
    """Return a JSON-safe cache value from a CompletedProcess."""
    return {
        "returncode": result.returncode,
        "stdout": result.stdout or "",
        "stderr": result.stderr or "",
    }


def safe_cache_tag(cache_tag: str) -> str:
    """Return a filesystem-safe cache tag token for command-result cache keys."""
    normalized_tag = re.sub(r"[^A-Za-z0-9_-]+", "_", cache_tag.strip())
    return normalized_tag or "default"


def command_cache_key(command: str, cache_tag: str = "default") -> str:
    """Return a stable tagged cache key based on the full command string."""
    command_hash = hashlib.sha256(command.encode("utf-8")).hexdigest()
    return f"command_tag:{safe_cache_tag(cache_tag)}:{command_hash}"


def cached_background_command_result(
    command: str, cache_tag: str, force_local: bool = False
) -> tuple[subprocess.CompletedProcess[str] | None, bool]:
    """Return a cached command result and whether it came from fresh cache."""
    command_to_run = effective_bash_command(command, force_local=force_local)
    remote_host = command_remote_host(force_local=force_local)
    cache_key = command_cache_key(command_to_run, cache_tag)
    cached_value = cache_get(cache_key)
    fresh_cache = cached_value is not None
    if cached_value is None:
        cached_value = command_result_snapshot_get(cache_key)
    if cached_value is None:
        return None, False
    command_result_snapshot_set(cache_key, cached_value)
    result = sanitize_remote_command_result(
        remote_host, completed_process_from_cache(command_to_run, cached_value)
    )
    return result, fresh_cache


def background_command_metadata(
    command: str, cache_tag: str, force_local: bool = False
) -> dict[str, object]:
    """Return metadata needed to cache a background command result."""
    command_to_run = effective_bash_command(command, force_local=force_local)
    return {
        "command_to_run": command_to_run,
        "remote_host": command_remote_host(force_local=force_local),
        "cache_key": command_cache_key(command_to_run, cache_tag),
        "cache_tag": cache_tag,
    }


def cache_background_command_result(
    metadata: dict[str, object],
    result: subprocess.CompletedProcess[str],
) -> None:
    """Store a completed background command result in snapshot and UI caches."""
    cache_key = str(metadata.get("cache_key", "")).strip()
    if not cache_key or ssh_shared_connection_closed(result):
        return
    cached_value = cache_value_from_completed_process(result)
    command_result_snapshot_set(cache_key, cached_value)
    ttl_seconds = int(
        metadata.get("ttl_seconds", hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS)
        or hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS
    )
    cache_set(cache_key, cached_value, ttl_seconds)


def start_cached_background_command(
    job_name: str,
    command: str,
    description: str,
    cache_tag: str,
    ttl_seconds: int,
    timeout_seconds: int,
    force_local: bool = False,
) -> bool:
    """Start a background command that will be written to command-result cache."""
    metadata = {
        **background_command_metadata(command, cache_tag, force_local=force_local),
        "ttl_seconds": ttl_seconds,
    }
    return start_background_bash_command(
        job_name,
        command,
        description,
        timeout_seconds,
        force_local=force_local,
        metadata=metadata,
    )


def complete_cached_background_command(
    job_name: str, error_state_key: str, fallback_error: str
) -> subprocess.CompletedProcess[str] | None:
    """Complete a cached background command and store its latest output."""
    completed = background_job_result(job_name)
    if completed is None:
        return None
    result, metadata = completed
    if result.returncode == 0:
        cache_background_command_result(metadata, result)
        st.session_state[error_state_key] = ""
    else:
        st.session_state[error_state_key] = strip_ansi(
            result.stderr or result.stdout or fallback_error
        )
    return result


def cached_command_job_name(command: str, cache_tag: str) -> str:
    """Return a stable background job name for a cached page-load command."""
    command_hash = hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]
    return f"cached_{safe_cache_tag(cache_tag)}_{command_hash}"


def cached_command_error_key(job_name: str) -> str:
    """Return the session key used for cached command load errors."""
    return f"_hhs_cached_command_error_{job_name}"


def render_cached_command_result(
    command: str,
    description: str,
    cache_tag: str,
    ttl_seconds: int,
    timeout_seconds: int,
    fallback_error: str,
    force_local: bool = False,
) -> subprocess.CompletedProcess[str] | None:
    """Render one banner while a page-load command refreshes in the background."""
    job_name = cached_command_job_name(command, cache_tag)
    error_key = cached_command_error_key(job_name)
    completed_result = complete_cached_background_command(
        job_name, error_key, fallback_error
    )
    result, fresh_cache = cached_background_command_result(
        command, cache_tag, force_local=force_local
    )
    if completed_result is not None:
        return completed_result
    if not fresh_cache and not background_job_is_running(job_name):
        start_cached_background_command(
            job_name,
            command,
            description,
            cache_tag,
            ttl_seconds,
            timeout_seconds,
            force_local=force_local,
        )
    command_running = background_job_is_running(job_name)
    render_background_job_status(job_name)
    if command_running and not fresh_cache:
        return None
    if result is not None:
        return result
    command_error = str(st.session_state.get(error_key, "")).strip()
    if command_error:
        st.error(command_error)
    elif not command_running:
        render_command_loader(description)
    return None


def cached_aliases_result() -> tuple[subprocess.CompletedProcess[str] | None, bool]:
    """Return a cached aliases list result."""
    return cached_background_command_result(build_hhs_aliases_command(), "aliases")


def start_aliases_list_refresh() -> bool:
    """Start a background refresh for the aliases list."""
    return start_cached_background_command(
        ALIAS_LIST_JOB,
        build_hhs_aliases_command(),
        "Loading custom aliases",
        "aliases",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
    )


def complete_aliases_list_refresh() -> subprocess.CompletedProcess[str] | None:
    """Complete a background refresh for the aliases list."""
    return complete_cached_background_command(
        ALIAS_LIST_JOB,
        "alias_list_error",
        "Unable to load aliases.",
    )


def hhs_services_command_context() -> tuple[str, str, str, str]:
    """Return the service-list command, effective command, host, and cache key."""
    command = build_hhs_services_command()
    command_to_run = effective_bash_command(command)
    remote_host = command_remote_host()
    cache_key = command_cache_key(command_to_run, "services")
    return command, command_to_run, remote_host, cache_key


def cached_hhs_services_result() -> (
    tuple[subprocess.CompletedProcess[str] | None, bool]
):
    """Return a cached service-list result and whether it came from fresh cache."""
    command, _command_to_run, _remote_host, _cache_key = hhs_services_command_context()
    result, fresh_cache = cached_background_command_result(command, "services")
    remember_ollama_service_availability(result)
    return result, fresh_cache


def start_hhs_services_list_refresh() -> bool:
    """Start a background refresh for the services list."""
    command, _command_to_run, _remote_host, _cache_key = hhs_services_command_context()
    return start_cached_background_command(
        SERVICE_LIST_JOB,
        command,
        "Loading services",
        "services",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
    )


def complete_hhs_services_list_refresh() -> subprocess.CompletedProcess[str] | None:
    """Complete a background services-list refresh and cache successful output."""
    result = complete_cached_background_command(
        SERVICE_LIST_JOB,
        "service_list_error",
        "Unable to list services.",
    )
    remember_ollama_service_availability(result)
    return result


def schedule_ollama_service_availability_refresh() -> None:
    """Start a fresh services refresh so AI tab visibility follows the active host."""
    stop_background_job(SERVICE_LIST_JOB)
    cache_delete_tag("services")
    st.session_state["service_list_error"] = ""
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY] = False
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY] = True
    start_hhs_services_list_refresh()


def update_ollama_service_availability_refresh() -> None:
    """Complete or poll the services refresh that drives AI tab visibility."""
    previous_availability = ollama_service_is_available()
    result = complete_hhs_services_list_refresh()
    if result is not None and ollama_service_is_available() != previous_availability:
        st.rerun()
    if background_job_is_running(SERVICE_LIST_JOB):
        poll_background_job_completion(SERVICE_LIST_JOB)


def monitor_metric_job_name(metric: str) -> str:
    """Return the background job name for a process metric chart."""
    return MONITOR_MEM_JOB if metric == "MEM" else MONITOR_CPU_JOB


def monitor_metric_command(metric: str) -> str:
    """Return the command used to load one process monitor metric."""
    return build_process_monitor_command(metric, normalized_monitor_process_top_n(metric))


def cached_monitor_metric_result(
    metric: str,
) -> tuple[subprocess.CompletedProcess[str] | None, bool]:
    """Return a cached process monitor metric result."""
    return cached_background_command_result(
        monitor_metric_command(metric), "monitor_process"
    )


def start_monitor_metric_refresh(metric: str) -> bool:
    """Start a background refresh for a process monitor metric."""
    title = "memory" if metric == "MEM" else "CPU"
    return start_cached_background_command(
        monitor_metric_job_name(metric),
        monitor_metric_command(metric),
        f"Loading {title} usage",
        "monitor_process",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
    )


def complete_monitor_metric_refresh(
    metric: str,
) -> subprocess.CompletedProcess[str] | None:
    """Complete a background refresh for a process monitor metric."""
    return complete_cached_background_command(
        monitor_metric_job_name(metric),
        f"monitor_{metric.lower()}_error",
        f"Unable to load {metric.lower()} usage.",
    )


def cached_monitor_process_list_result() -> (
    tuple[subprocess.CompletedProcess[str] | None, bool]
):
    """Return a cached process list result."""
    return cached_background_command_result(
        build_hhs_process_list_command("."), "monitor_process"
    )


def start_monitor_process_list_refresh() -> bool:
    """Start a background refresh for the monitor process list."""
    return start_cached_background_command(
        MONITOR_PROCESS_LIST_JOB,
        build_hhs_process_list_command("."),
        "Loading processes",
        "monitor_process",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
    )


def complete_monitor_process_list_refresh() -> subprocess.CompletedProcess[str] | None:
    """Complete a background refresh for the monitor process list."""
    return complete_cached_background_command(
        MONITOR_PROCESS_LIST_JOB,
        "monitor_process_list_error",
        "Unable to load processes.",
    )


def build_hhs_envs_command(prefix_filter: str | None) -> str:
    """Build the Bash command used to run the __hhs_envs HomeSetup function."""
    filter_arg = f' "{prefix_filter}"' if prefix_filter else ""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_envs{filter_arg}"
    )


def run_hhs_envs(
    prefix_filter: str | None = None, refresh_cache: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_envs command and return the completed process."""
    return run_bash_command(
        build_hhs_envs_command(prefix_filter),
        "Loading environment variables...",
        use_cache=not refresh_cache,
        cache_tag="env",
    )


def build_hhs_env_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a custom environment value."""
    safe_operation = "del" if operation == "del" else "add"
    safe_name = shlex.quote(name)
    if safe_operation == "del":
        action_args = f"--del {safe_name}"
    else:
        action_args = f"-a {shlex.quote(f'{name}={value}')}"
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_envs {action_args}"
    )


def build_hhs_sysinfo_command() -> str:
    """Build the Bash command used to run the __hhs_sysinfo HomeSetup function."""
    return (
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-sys-utils.bash"; '
        "__hhs_sysinfo"
    )


def build_open_directory_command(directory: str) -> str:
    """Build a POSIX-shell command that opens a directory in the OS file explorer."""
    safe_directory = shlex.quote(str(Path(directory).resolve()))
    return (
        f"target={safe_directory}; "
        'if [ "$(uname -s)" = "Darwin" ]; then '
        'open "$target"; '
        "elif command -v xdg-open >/dev/null 2>&1; then "
        'xdg-open "$target"; '
        "elif command -v gio >/dev/null 2>&1; then "
        'gio open "$target"; '
        "elif command -v sensible-browser >/dev/null 2>&1; then "
        'sensible-browser "$target"; '
        "else "
        'printf "%s\\n" "No supported file explorer opener found." >&2; '
        "exit 127; "
        "fi"
    )


def build_footer_working_directory_command() -> str:
    """Build the Bash command used to print the footer working directory."""
    return r'printf "__HHS_UI_PWD__"; \pwd'


def build_hhs_updater_command(operation: str) -> str:
    """Build the Bash command used to run the HomeSetup updater plug-in."""
    safe_operation = re.sub(r"[^A-Za-z_-]+", "", operation) or "check"
    update_prefix = 'printf "y\\n" | ' if safe_operation == "update" else ""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/updater/updater.bash"; '
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; exit "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "updater" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f'{update_prefix}__hhs updater execute "{safe_operation}"'
    )


def build_ssh_tunnels_command(host: str) -> str:
    """Build a local command that lists configured and active SSH tunnel data."""
    safe_host = shlex.quote(host)
    safe_config_option = ssh_config_option()
    return (
        'printf "%s\\n" "__HHS_SSH_CONFIG__"; '
        f"ssh {safe_config_option} -G {safe_host} 2>/dev/null || true; "
        'printf "%s\\n" "__HHS_SSH_PROCESSES__"; '
        "ps -axo pid=,command= 2>/dev/null || true"
    )


def run_ssh_tunnels(host: str) -> subprocess.CompletedProcess[str]:
    """Run the SSH tunnel listing command and return the completed process."""
    return run_bash_command(
        build_ssh_tunnels_command(host),
        "Loading SSH tunnels...",
        cache_tag="ssh",
    )


def run_open_working_directory() -> subprocess.CompletedProcess[str]:
    """Open the current working directory in the operating system file explorer."""
    return run_bash_command(
        build_open_directory_command(os.getcwd()),
        "Opening working directory...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="system",
    )


def open_footer_working_directory() -> None:
    """Open the footer working directory locally or in the remote SSH explorer."""
    if connected_ssh_host():
        working_dir = footer_working_directory()
        st.session_state["active_view"] = hhs_ui.SSH_VIEW
        st.session_state["ssh_view"] = "FILES"
        open_remote_explorer_path(working_dir)
        push_floating_status("Opened remote working directory in SSH Explorer.", "info")
        return

    result = run_open_working_directory()
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


def run_footer_working_directory() -> subprocess.CompletedProcess[str]:
    """Run the active host shell command used by the footer working-directory status."""
    return run_bash_command(
        build_footer_working_directory_command(),
        "Loading remote working dir",
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


def run_hhs_updater_check(
    refresh_cache: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup updater check after refreshing the installed version."""
    command = build_hhs_envs_command("^HHS_VERSION$")
    if refresh_cache:
        cache_delete_command(command, "env")
    run_hhs_envs("^HHS_VERSION$", refresh_cache=refresh_cache)
    return run_bash_command(
        build_hhs_updater_command("check"),
        "Checking HomeSetup updates...",
        use_cache=not refresh_cache,
        cache_tag="updater",
    )


def run_hhs_updater_update() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup updater update command and return the completed process."""
    return run_bash_command(
        build_hhs_updater_command("update"),
        "Updating HomeSetup...",
        ttl_seconds=0,
        use_cache=False,
        timeout_seconds=600,
        force_local=True,
        cache_tag="updater",
    )


def build_hhs_tools_command() -> str:
    """Build the Bash command used to run the __hhs_tools HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_OS="$(uname -s)"; '
        "unset HHS_ACTIVE_DOTFILES; "
        "shopt -s expand_aliases; "
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_icons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_env.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_aliases.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toolcheck.bash"; '
        "__hhs_tools"
    )


def build_hhs_shopt_setup_command() -> str:
    """Build the common Bash setup command used by __hhs_shopt UI calls."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_SHOPTS_FILE="${HHS_SHOPTS_FILE:-${HHS_DIR}/shell-opts.toml}"; '
        'mkdir -p "${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_icons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toml.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        'if [[ ! -s "${HHS_SHOPTS_FILE}" ]]; then '
        '\\shopt | awk \'{print $1" = "$2}\' >"${HHS_SHOPTS_FILE}"; '
        "fi; "
    )


def build_hhs_shopt_load_saved_command() -> str:
    """Build a Bash command that applies saved shell options to this process."""
    return (
        'if [[ -s "${HHS_SHOPTS_FILE}" ]]; then '
        "while IFS= read -r line; do "
        'if [[ "${line}" =~ ^([a-zA-Z0-9_]+)[[:space:]]*='
        "[[:space:]]*([Oo][Nn]|[Oo][Ff][Ff])$ ]]; then "
        'option="${BASH_REMATCH[1]}"; state="${BASH_REMATCH[2]}"; '
        'if [[ "${state}" =~ ^[Oo][Nn]$ ]]; then '
        'shopt -s "${option}" 2>/dev/null || true; '
        "else "
        'shopt -u "${option}" 2>/dev/null || true; '
        "fi; "
        "fi; "
        'done < "${HHS_SHOPTS_FILE}"; '
        "fi; "
    )


def build_hhs_shopt_command() -> str:
    """Build the Bash command used to run the __hhs_shopt listing function."""
    return (
        build_hhs_shopt_setup_command()
        + build_hhs_shopt_load_saved_command()
        + "__hhs_shopt -p"
    )


def build_hhs_shopt_action_command(operation: str, option_name: str) -> str:
    """Build the Bash command used to set or unset a shell option."""
    action = "-s" if operation == "set" else "-u"
    return (
        build_hhs_shopt_setup_command()
        + f"__hhs_shopt {action} {shlex.quote(option_name)}"
    )


def build_docker_ps_command() -> str:
    """Build the Bash command used to list Docker containers."""
    return (
        "docker ps -a --format "
        "'table {{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}'"
    )


def build_docker_images_command() -> str:
    """Build the Bash command used to list Docker images."""
    return (
        "docker images --format "
        "'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}'"
    )


def build_docker_agent_check_command() -> str:
    """Build the Bash command used to check whether Docker is running."""
    return "docker ps -q >/dev/null 2>&1"


def run_docker_ps() -> subprocess.CompletedProcess[str]:
    """Run the Docker container listing command and return the completed process."""
    return run_bash_command(
        build_docker_ps_command(),
        "Loading Docker containers...",
        cache_tag="docker",
    )


def run_docker_images() -> subprocess.CompletedProcess[str]:
    """Run the Docker image listing command and return the completed process."""
    return run_bash_command(
        build_docker_images_command(),
        "Loading Docker images...",
        cache_tag="docker",
    )


def build_docker_container_action_command(operation: str, container_id: str) -> str:
    """Build the Bash command used to run an action against a Docker container."""
    if operation not in {"start", "stop", "rm"}:
        raise ValueError(f"Unsupported Docker container operation: {operation}")
    return f"docker {operation} {shlex.quote(container_id)}"


def build_docker_image_delete_command(image_id: str) -> str:
    """Build the Bash command used to remove a Docker image."""
    return f"docker image rm -f {shlex.quote(image_id)}"


def build_hhs_hspm_command(operation: str, tool_name: str) -> str:
    """Build the Bash command used to run an hspm tool operation."""
    safe_operation = (
        operation if operation in {"install", "uninstall", "reinstall"} else ""
    )
    safe_tool_name = shlex.quote(tool_name.strip())
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_OS="$(uname -s)"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export PLUGINS_DIR="${HHS_HOME}/bin/apps/bash/hhs-app/plugins"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_colors.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_env.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/hspm/hspm.bash"; '
        'function __hhs() { if [[ "$1" == "hspm" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f"__hhs hspm execute {safe_operation} {safe_tool_name}"
    )


def build_tool_tldr_command(tool_name: str) -> str:
    """Build the Bash command used to read TLDR help for a tool."""
    return f"tldr {shlex.quote(tool_name.strip())}"


def build_hhs_history_command() -> str:
    """Build the Bash command used to run the __hhs_history HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        "__hhs_history"
    )


def build_hhs_history_dirs_command() -> str:
    """Build the Bash command used to run the __hhs_dirs HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_DIRS_FILE="${HHS_DIRS_FILE:-${HHS_DIR}/.dirs}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        "__hhs_dirs -l"
    )


def build_hhs_history_stats_command(top_n: int = 10) -> str:
    """Build the Bash command used to run the __hhs_hist_stats HomeSetup function."""
    safe_top_n = max(1, min(int(top_n), 100))
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        f"__hhs_hist_stats {safe_top_n}"
    )


def build_hhs_disk_usage_command(directory: str, top_n: int = 10) -> str:
    """Build the Bash command used to run the __hhs_du HomeSetup function."""
    hhs_home = homesetup_home()
    safe_top_n = max(1, min(int(top_n), 100))
    expanded_directory = expand_monitor_disk_directory(directory)
    directory_arg = (
        '"${HHS_HOME}"'
        if monitor_disk_directory_is_hhs_home_token(directory)
        or expanded_directory == str(hhs_home)
        else shlex.quote(expanded_directory)
    )
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-shell-utils.bash"; '
        f"__hhs_du {directory_arg} {safe_top_n}"
    )


def build_process_monitor_command(metric: str, top_n: int = 10) -> str:
    """Build the shell command used to load process monitor data."""
    safe_top_n = max(1, min(int(top_n), 100))
    sort_keys = hhs_ui.TOP_PROCESS_SORT_KEYS.get(
        metric, hhs_ui.TOP_PROCESS_SORT_KEYS["CPU"]
    )
    darwin_sort = sort_keys["darwin"]
    linux_sort = sort_keys["linux"]
    ps_sort = "-r" if metric == "CPU" else "-m"
    linux_ps_sort = "pcpu" if metric == "CPU" else "pmem"
    linux_top_sample = (
        f"top -b -n 2 -d 1 -o {linux_sort} -w 512"
        if metric == "CPU"
        else f"top -b -n 1 -o {linux_sort} -w 512"
    )
    return (
        'if [[ "$(uname -s)" == "Darwin" ]]; then '
        f"top -l 2 -s 1 -o {darwin_sort} -n {safe_top_n} 2>/dev/null || "
        f"ps -axo pid,user,%cpu,%mem,comm {ps_sort} 2>/dev/null | head -n {safe_top_n + 1}; "
        "else "
        f"{linux_top_sample} 2>/dev/null || "
        f"ps -eo pid,user,%cpu,%mem,comm --sort=-{linux_ps_sort} 2>/dev/null | head -n {safe_top_n + 1}; "
        "fi"
    )


def build_hhs_process_list_command(process_filter: str) -> str:
    """Build the Bash command used to list processes via HomeSetup."""
    safe_filter = process_filter.strip() or "."
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-sys-utils.bash"; '
        f"__hhs_process_list {shlex.quote(safe_filter)}"
    )


def build_hhs_process_kill_command(process_name: str) -> str:
    """Build the Bash command used to kill a process via HomeSetup."""
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-sys-utils.bash"; '
        f"__hhs_process_kill -f {shlex.quote(process_name)}"
    )


def build_hhs_logs_command(
    log_file: str, tail_lines: int = 200, log_level: str = "ALL_LEVELS"
) -> str:
    """Build the Bash command used to run the __hhs logs command."""
    safe_log_file = Path(log_file).name
    safe_tail_lines = max(1, min(int(tail_lines), 5000))
    safe_log_level = log_level if log_level in hhs_ui.LOG_LEVELS else "ALL_LEVELS"
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_LOG_FILE="${HHS_LOG_DIR}/hhs.log"; '
        'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-taylor.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/functions/built-ins.bash"; '
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; return "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "logs" ]]; then shift; logs "$@"; else return 127; fi; }; '
        f"__hhs logs -n {safe_tail_lines} {shlex.quote(safe_log_file)} {shlex.quote(safe_log_level)}"
    )


def run_hhs_logs(
    log_file: str, tail_lines: int = 200, log_level: str = "ALL_LEVELS"
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs logs command and return the completed process."""
    return run_bash_command(
        build_hhs_logs_command(log_file, tail_lines, log_level),
        "Loading logs...",
        cache_tag="monitor_logs",
    )


def build_hhs_ask_execute_command(arguments: list[str]) -> str:
    """Build the Bash command used to run the __hhs ask execute command."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
    return build_hhs_ask_plugin_command(
        'function __hhs() { if [[ "$1" == "ask" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f"__hhs ask execute {safe_arguments}"
    )


def build_hhs_ask_plugin_command(command: str) -> str:
    """Build a Bash command that loads the ask plugin support before running a command."""
    return (
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_SETUP_FILE="${HHS_SETUP_FILE:-${HHS_DIR}/.homesetup.toml}"; '
        'export HHS_LOG_DIR="${HHS_LOG_DIR:-${HHS_DIR}/log}"; '
        'export HHS_LOG_FILE="${HHS_LOG_FILE:-${HHS_LOG_DIR}/hhs-ui.log}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'export HHS_MY_OS="$(uname -s)"; '
        'export HHS_MY_OS_RELEASE="${HHS_MY_OS_RELEASE:-${HHS_MY_OS}}"; '
        'export HHS_OLLAMA_HISTORY_FILE="${HHS_OLLAMA_HISTORY_FILE:-${HHS_DIR}/.ollama_history}"; '
        "export HHS_OLLAMA_MD_VIEWER=cat; "
        'export APP_NAME="${APP_NAME:-hhs-ui}"; '
        "export IS_PIPED=0; "
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_colors.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-toml.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/app-commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"; '
        f"{command}"
    )


def build_hhs_ask_command(message: str) -> str:
    """Build the Bash command used to run the __hhs ask command."""
    return build_hhs_ask_execute_command(["-k", message])


def build_hhs_ask_context_command() -> str:
    """Build the Bash command used to show the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-c"])


def build_hhs_ask_prompt_file_command() -> str:
    """Build the Bash command used to read the editable Ollama ask prompt file."""
    return build_hhs_ask_plugin_command(
        '[[ -r "${HHS_OLLAMA_PROMPT_FILE}" ]] || { '
        'echo "Ollama prompt file not found: ${HHS_OLLAMA_PROMPT_FILE}" >&2; '
        "exit 2; "
        "}; "
        'cat "${HHS_OLLAMA_PROMPT_FILE}"'
    )


def build_hhs_ask_prompt_command() -> str:
    """Build the Bash command used to render the active Ollama prompt."""
    return build_hhs_ask_execute_command(["-p"])


def build_hhs_save_ask_prompt_file_command(prompt_text: str) -> str:
    """Build the Bash command used to save the editable Ollama ask prompt file."""
    encoded_prompt = b64encode(prompt_text.encode("utf-8")).decode("ascii")
    return build_hhs_ask_plugin_command(
        f"encoded_prompt={shlex.quote(encoded_prompt)}; "
        'prompt_file="${HHS_OLLAMA_PROMPT_FILE}"; '
        'mkdir -p "$(dirname "${prompt_file}")" || exit 2; '
        'tmp_prompt="$(mktemp "${TMPDIR:-/tmp}/hhs-ask-prompt.XXXXXX")" || exit 2; '
        'if printf "%s" "${encoded_prompt}" | base64 --decode >"${tmp_prompt}" 2>/dev/null '
        '|| printf "%s" "${encoded_prompt}" | base64 -d >"${tmp_prompt}" 2>/dev/null '
        '|| printf "%s" "${encoded_prompt}" | base64 -D >"${tmp_prompt}" 2>/dev/null; then '
        'mv "${tmp_prompt}" "${prompt_file}" || exit 2; '
        'printf "Saved prompt: %s\\n" "${prompt_file}"; '
        "else "
        'rm -f "${tmp_prompt}"; '
        'echo "Unable to decode prompt content." >&2; '
        "exit 2; "
        "fi"
    )


def build_hhs_revert_ask_prompt_file_command() -> str:
    """Build the Bash command used to restore the editable Ollama ask prompt file."""
    return build_hhs_ask_plugin_command(
        '[[ -r "${HHS_OLLAMA_PROMPT_SOURCE}" ]] || { '
        'echo "Ollama prompt source file not found: ${HHS_OLLAMA_PROMPT_SOURCE}" >&2; '
        "exit 2; "
        "}; "
        'mkdir -p "$(dirname "${HHS_OLLAMA_PROMPT_FILE}")" || exit 2; '
        'cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}" || exit 2; '
        'cat "${HHS_OLLAMA_PROMPT_FILE}"'
    )


def build_hhs_ask_reset_command() -> str:
    """Build the Bash command used to reset the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-r"])


def build_hhs_ask_ingest_command(file_path: str) -> str:
    """Build the Bash command used to ingest the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-i", file_path])


def build_hhs_ask_models_command() -> str:
    """Build the Bash command used to list Ollama ask models."""
    return build_hhs_ask_execute_command(["-m"])


def build_hhs_ask_select_model_command(model_name: str) -> str:
    """Build the Bash command used to select the active Ollama ask model."""
    return build_hhs_ask_execute_command(["-s", model_name])


def build_ollama_delete_model_command(model_name: str) -> str:
    """Build the Bash command used to delete an Ollama model."""
    return f"ollama rm {shlex.quote(model_name)}"


def build_hhs_paths_command() -> str:
    """Build the Bash command used to run the __hhs_paths HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-paths.bash"; '
        "__hhs_paths"
    )


def build_hhs_path_action_command(
    operation: str, path_value: str, old_path_value: str = ""
) -> str:
    """Build the Bash command used to add, edit, or delete a persistent PATH value."""
    safe_path = shlex.quote(path_value)
    if operation == "del":
        action_args = f"-r {safe_path}"
    elif operation == "edit" and old_path_value and old_path_value != path_value:
        safe_old_path = shlex.quote(old_path_value)
        action_args = f"-r {safe_old_path}; __hhs_paths -a {safe_path}"
    else:
        action_args = f"-a {safe_path}"
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-paths.bash"; '
        f"__hhs_paths {action_args}"
    )


def build_hhs_dirs_command() -> str:
    """Build the Bash command used to run the __hhs_load_dir HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        "__hhs_load_dir -l"
    )


def build_hhs_dir_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a saved directory."""
    safe_name = shlex.quote(name)
    if operation == "del":
        action_args = f"-r {safe_name}"
    else:
        action_args = f"{shlex.quote(value)} {safe_name}"
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        f"__hhs_save_dir {action_args}"
    )


def build_hhs_commands_command() -> str:
    """Build the Bash command used to run the __hhs_command HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-command.bash"; '
        "__hhs_command -l"
    )


def build_hhs_command_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a saved command."""
    safe_name = shlex.quote(name)
    if operation == "del":
        action_args = f"-r {safe_name}"
    else:
        action_args = f"-a {safe_name} {shlex.quote(value)}"
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-command.bash"; '
        f"__hhs_command {action_args}"
    )


def build_hhs_aliases_command() -> str:
    """Build the Bash command used to run the __hhs_aliases HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-aliases.bash"; '
        "__hhs_aliases -l"
    )


def build_hhs_alias_action_command(operation: str, name: str, value: str = "") -> str:
    """Build the Bash command used to add, edit, or delete a custom alias."""
    safe_name = shlex.quote(name)
    action_args = (
        f"-r {safe_name}" if operation == "del" else f"{safe_name} {shlex.quote(value)}"
    )
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-aliases.bash"; '
        f"__hhs_aliases {action_args}"
    )


def build_hhs_services_command(
    operation: str = "status", service_name: str = ""
) -> str:
    """Build the Bash command used to run the __hhs_services HomeSetup function."""
    safe_operation = re.sub(r"[^A-Za-z_-]+", "", operation) or "status"
    safe_service_name = service_name.replace("\\", "\\\\").replace('"', '\\"')
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'export HHS_HOME="${HHS_HOME}"; '
        'export HHS_MY_SHELL="${HHS_MY_SHELL:-bash}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/services/services.bash"; '
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; exit "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "services" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f'__hhs services execute "{safe_operation}" "{safe_service_name}"'
    )


def run_hhs_env_action(
    operation: str, name: str, value: str = ""
) -> subprocess.CompletedProcess[str]:
    """Run a persistent custom environment variable action."""
    return run_bash_command(
        build_hhs_env_action_command(operation, name, value),
        "Updating environment variables...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="env",
    )


def run_hhs_shopt_action(
    operation: str, option_name: str
) -> subprocess.CompletedProcess[str]:
    """Run a shell option set or unset action."""
    return run_bash_command(
        build_hhs_shopt_action_command(operation, option_name),
        "Updating shell option...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="shopt",
    )


def run_docker_container_action(
    operation: str, container_id: str
) -> subprocess.CompletedProcess[str]:
    """Run a Docker container action and return the completed process."""
    return run_bash_command(
        build_docker_container_action_command(operation, container_id),
        f"Running docker {operation}...",
        ttl_seconds=0,
        use_cache=False,
        timeout_seconds=20,
        cache_tag="docker",
    )


def run_docker_image_delete(image_id: str) -> subprocess.CompletedProcess[str]:
    """Run Docker image deletion and return the completed process."""
    return run_bash_command(
        build_docker_image_delete_command(image_id),
        "Deleting Docker image...",
        ttl_seconds=0,
        use_cache=False,
        timeout_seconds=30,
        cache_tag="docker",
    )


def run_tool_tldr(tool_name: str) -> subprocess.CompletedProcess[str]:
    """Run tldr for the selected Home tool."""
    return run_bash_command(
        build_tool_tldr_command(tool_name),
        f"Loading TLDR for {tool_name}...",
        use_cache=False,
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="tools",
    )


def run_hhs_process_kill(process_name: str) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup process kill command and return the completed process."""
    return run_bash_command(
        build_hhs_process_kill_command(process_name),
        "Killing process...",
        use_cache=False,
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="monitor_process",
    )


def run_hhs_ask_context() -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask context command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_context_command(),
        "Loading Ollama context...",
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_ask_prompt_file() -> subprocess.CompletedProcess[str]:
    """Read the editable Ollama prompt file and return the completed process."""
    return run_bash_command(
        build_hhs_ask_prompt_file_command(),
        "Loading Ollama prompt file...",
        use_cache=False,
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_save_ask_prompt_file(prompt_text: str) -> subprocess.CompletedProcess[str]:
    """Save the editable Ollama prompt file and return the completed process."""
    return run_bash_command(
        build_hhs_save_ask_prompt_file_command(prompt_text),
        "Saving Ollama prompt file...",
        use_cache=False,
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_revert_ask_prompt_file() -> subprocess.CompletedProcess[str]:
    """Revert the editable Ollama prompt file and return the completed process."""
    return run_bash_command(
        build_hhs_revert_ask_prompt_file_command(),
        "Reverting Ollama prompt file...",
        use_cache=False,
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_ask_reset(close_dialogs: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask reset command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_reset_command(),
        "Resetting Ollama context...",
        close_dialogs=close_dialogs,
        use_cache=False,
        timeout_seconds=hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_ask_ingest(file_path: str) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask ingest command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_ingest_command(file_path),
        "Ingesting Ollama context...",
        use_cache=False,
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_ask_select_model(model_name: str) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask model selection command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_select_model_command(model_name),
        "Selecting Ollama model...",
        use_cache=False,
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_ollama_delete_model(model_name: str) -> subprocess.CompletedProcess[str]:
    """Run the Ollama model deletion command and return the completed process."""
    return run_bash_command(
        build_ollama_delete_model_command(model_name),
        "Deleting Ollama model...",
        use_cache=False,
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        cache_tag="ai",
    )


def run_hhs_services_quietly(
    operation: str = "status", service_name: str = ""
) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup services command without command-result caching."""
    return run_bash_command(
        build_hhs_services_command(operation, service_name),
        "Loading services...",
        use_cache=False,
        cache_tag="services",
    )


def run_hhs_service_action(
    operation: str, service_name: str
) -> subprocess.CompletedProcess[str]:
    """Run a HomeSetup service action without command-result caching."""
    return run_bash_command(
        build_hhs_services_command(operation, service_name),
        f"Service {operation}: {service_name}",
        use_cache=False,
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SERVICE_ACTION_TIMEOUT_SECONDS,
        cache_tag="services",
    )


def run_hhs_path_action(
    operation: str, path_value: str, old_path_value: str = ""
) -> subprocess.CompletedProcess[str]:
    """Run a persistent PATH entry action."""
    return run_bash_command(
        build_hhs_path_action_command(operation, path_value, old_path_value),
        "Updating PATH entries...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="path",
    )


def run_hhs_dir_action(
    operation: str, name: str, value: str = ""
) -> subprocess.CompletedProcess[str]:
    """Run a persistent saved directory action."""
    return run_bash_command(
        build_hhs_dir_action_command(operation, name, value),
        "Updating saved directories...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="dirs",
    )


def run_hhs_command_action(
    operation: str, name: str, value: str = ""
) -> subprocess.CompletedProcess[str]:
    """Run a persistent saved command action."""
    return run_bash_command(
        build_hhs_command_action_command(operation, name, value),
        "Updating saved commands...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="cmds",
    )


def run_hhs_alias_action(
    operation: str, name: str, value: str = ""
) -> subprocess.CompletedProcess[str]:
    """Run a persistent custom alias action."""
    return run_bash_command(
        build_hhs_alias_action_command(operation, name, value),
        "Updating custom aliases...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="aliases",
    )


def env_filter_pattern(env_filter: str, other_filter: str = "") -> str | None:
    """Return the __hhs_envs filter pattern for the selected UI filter."""
    if env_filter == "HHS":
        return "^HHS_"
    if env_filter == "Other":
        clean_filter = other_filter.strip()
        return clean_filter or None
    return None


def row_matches_text_filter(row: dict[str, str], text_filter: str = "") -> bool:
    """Return whether any row value contains the text filter."""
    clean_filter = text_filter.strip().lower()
    if not clean_filter:
        return True
    return any(clean_filter in str(value).lower() for value in row.values())


def row_matches_text_filter(row: dict[str, str], text_filter: str) -> bool:
    """Return whether a row contains the selected free-text filter."""
    clean_filter = text_filter.strip().lower()
    if not clean_filter:
        return True
    searchable_value = " ".join(str(value).lower() for value in row.values())
    return clean_filter in searchable_value


def filter_tool_rows(
    rows: list[dict[str, str]], tools_filter: str = "All", other_filter: str = ""
) -> list[dict[str, str]]:
    """Return Home tools rows matching the selected UI filter."""
    if tools_filter == "Installed":
        return [row for row in rows if home_tool_is_installed(row)]
    if tools_filter in ("Not Installed", "Not Found"):
        return [row for row in rows if home_tool_is_not_found(row)]
    if tools_filter == "Aliased":
        return [row for row in rows if home_tool_is_aliased(row)]
    if tools_filter == "Other":
        return [row for row in rows if row_matches_text_filter(row, other_filter)]
    return rows


def filter_shopt_rows(
    rows: list[dict[str, str]], shopt_filter: str = "All", other_filter: str = ""
) -> list[dict[str, str]]:
    """Return shell option rows matching the selected UI filter."""
    if shopt_filter == "ON":
        return [row for row in rows if row.get("State") == "ON"]
    if shopt_filter == "OFF":
        return [row for row in rows if row.get("State") == "OFF"]
    if shopt_filter == "Other":
        return [row for row in rows if row_matches_text_filter(row, other_filter)]
    return rows


def path_row_matches_filter(
    row: dict[str, str], path_filter: str, other_filter: str = ""
) -> bool:
    """Return whether a PATH row matches the selected UI filter."""
    if path_filter == "All":
        return True
    searchable_name = row.get("Name", "").lower()
    if path_filter == "Shell":
        return "shell" in searchable_name
    if path_filter == "Private":
        return "private" in searchable_name
    if path_filter == "Custom":
        return "custom" in searchable_name
    if path_filter == "Other":
        return row_matches_text_filter(row, other_filter)
    return True


def filter_path_rows(
    rows: list[dict[str, str]],
    path_filter: str,
    other_filter: str = "",
) -> list[dict[str, str]]:
    """Return PATH rows that match the selected UI filter."""
    return [
        row for row in rows if path_row_matches_filter(row, path_filter, other_filter)
    ]


def filter_rows_by_text(
    rows: list[dict[str, str]], list_filter: str, text_filter: str = ""
) -> list[dict[str, str]]:
    """Return rows that match the selected All/Other filter."""
    if list_filter not in ("Other", "Others"):
        return rows
    return [row for row in rows if row_matches_text_filter(row, text_filter)]


def filter_service_rows(
    rows: list[dict[str, str]],
    service_filter: str,
    text_filter: str = "",
) -> list[dict[str, str]]:
    """Return service rows matching the selected service status filter."""
    if service_filter in ("Up", "Started"):
        return [row for row in rows if service_is_up(row)]
    if service_filter in ("Down", "Stopped"):
        return [row for row in rows if service_is_down(row)]
    if service_filter == "Other":
        return [row for row in rows if row_matches_text_filter(row, text_filter)]
    return rows


def filter_process_rows(
    rows: list[dict[str, str]],
    process_filter: str,
    text_filter: str = "",
) -> list[dict[str, str]]:
    """Return process rows matching the selected process status filter."""
    if process_filter == "Other":
        return [row for row in rows if row_matches_text_filter(row, text_filter)]
    if process_filter == "All":
        return rows
    return [
        row
        for row in rows
        if row.get("Status", "").lower() == process_filter.strip().lower()
    ]


def parse_hhs_envs(output: str) -> list[dict[str, str]]:
    """Parse __hhs_envs terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.ENV_LINE_PATTERN.match(line.strip())
        if match:
            rows.append({"Name": match.group(1), "Value": match.group(2).strip()})
    return rows


def parse_hhs_tools(output: str) -> list[dict[str, str]]:
    """Parse __hhs_tools terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.TOOL_LINE_PATTERN.match(line.strip())
        if match:
            status = match.group(4).strip()
            glyph = match.group(3).strip()
            rows.append(
                {
                    "Tool": match.group(2).strip(),
                    "Status": f"{glyph} {status}",
                    "Path": (match.group(5) or "").strip(),
                }
            )
    return rows


def shopt_status_value(state: str) -> str:
    """Return the visible shell option status with an on/off glyph."""
    clean_state = state.strip().upper()
    return f" {clean_state}" if clean_state == "ON" else f" {clean_state}"


def shopt_description(option_name: str) -> str:
    """Return a compact Bash shell option description."""
    return SHOPT_DESCRIPTIONS.get(
        option_name.strip(),
        "Shell option available in this Bash version.",
    )


def parse_hhs_shopt(output: str) -> list[dict[str, str]]:
    """Parse __hhs_shopt terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.SHOPT_LINE_PATTERN.match(line.strip())
        if match:
            state = match.group(2).strip().upper()
            rows.append(
                {
                    "Status": shopt_status_value(state),
                    "Option": match.group(3).strip(),
                    "Description": shopt_description(match.group(3).strip()),
                    "State": state,
                }
            )
    return rows


def parse_hhs_dirs(output: str) -> list[dict[str, str]]:
    """Parse __hhs_load_dir list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.DIR_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {"Name": match.group(1).strip(), "Value": match.group(2).strip()}
            )
    return rows


def parse_hhs_commands(output: str) -> list[dict[str, str]]:
    """Parse __hhs_command list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.COMMAND_LINE_PATTERN.match(line.strip())
        if match:
            command_name = re.sub(r"^Command\s+", "", match.group(2).strip())
            rows.append(
                {
                    "Index": match.group(1).strip(),
                    "Name": command_name,
                    "Value": match.group(3).strip(),
                }
            )
    return rows


def parse_hhs_aliases(output: str) -> list[dict[str, str]]:
    """Parse __hhs_aliases list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.ALIAS_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {"Name": match.group(1).strip(), "Value": match.group(2).strip()}
            )
    return rows


def parse_hhs_services(output: str) -> list[dict[str, str]]:
    """Parse HomeSetup services list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.SERVICE_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {
                    "Name": match.group(2).strip(),
                    "Value": f"{match.group(3).strip()} {match.group(4).strip()}",
                }
            )
    return rows


def split_ssh_command(command: str) -> list[str]:
    """Return shell tokens for an SSH process command."""
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def ssh_command_executable_name(args: list[str]) -> str:
    """Return the executable name from a parsed SSH command."""
    if not args:
        return ""
    return Path(args[0]).name


def ssh_forward_spec_parts(spec: str, dynamic: bool = False) -> tuple[str, str]:
    """Return display bind and destination values for an SSH forward spec."""
    if dynamic:
        return spec, "SOCKS"
    parts = spec.split(":")
    if len(parts) >= 4:
        return ":".join(parts[:-2]), ":".join(parts[-2:])
    if len(parts) == 3:
        return parts[0], ":".join(parts[1:])
    return spec, ""


def ssh_config_forward_parts(
    parts: list[str], dynamic: bool = False
) -> tuple[str, str]:
    """Return display bind and destination values from SSH config forward values."""
    if not parts:
        return "", ""
    if dynamic:
        return parts[0], "SOCKS"
    if len(parts) >= 2:
        return parts[0], parts[1]
    return ssh_forward_spec_parts(parts[0])


def ssh_process_host(args: list[str]) -> str:
    """Return the destination host argument for a parsed SSH command."""
    options_with_values = {
        "-B",
        "-b",
        "-c",
        "-D",
        "-E",
        "-e",
        "-F",
        "-I",
        "-i",
        "-J",
        "-L",
        "-l",
        "-m",
        "-O",
        "-o",
        "-p",
        "-Q",
        "-R",
        "-S",
        "-W",
        "-w",
    }
    index = 1
    while index < len(args):
        value = args[index]
        if value == "--":
            return args[index + 1] if index + 1 < len(args) else ""
        if value in options_with_values:
            index += 2
            continue
        if value.startswith("-"):
            index += 1
            continue
        return value
    return ""


def ssh_tunnel_row(
    forward_type: str,
    bind: str,
    destination: str,
    ssh_host: str,
    source: str,
    pid: str = "",
    command: str = "",
) -> dict[str, str]:
    """Return one SSH tunnel table row."""
    return {
        "Type": forward_type,
        "Bind": bind,
        "Destination": destination,
        "SSH Host": ssh_host,
        "Source": source,
        "Status": "",
        "PID": pid,
        "Command": command,
    }


def append_ssh_forward_row(
    rows: list[dict[str, str]],
    pid: str,
    command: str,
    ssh_host: str,
    option: str,
    spec: str,
) -> None:
    """Append one SSH forwarding row parsed from a process command."""
    forward_types = {
        "-L": "Local",
        "-R": "Remote",
        "-D": "Dynamic",
    }
    forward_type = forward_types.get(option, option)
    bind, destination = ssh_forward_spec_parts(spec, dynamic=option == "-D")
    rows.append(
        ssh_tunnel_row(
            forward_type, bind, destination, ssh_host, "Process", pid, command
        )
    )


def parse_ssh_config_tunnels(output: str, host: str) -> list[dict[str, str]]:
    """Parse SSH tunnel and port-forward rows from resolved OpenSSH config output."""
    rows: list[dict[str, str]] = []
    forward_types = {
        "localforward": "Local",
        "remoteforward": "Remote",
        "dynamicforward": "Dynamic",
    }
    for raw_line in strip_ansi(output).splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        keyword = parts[0].lower()
        if keyword not in forward_types:
            continue
        dynamic = keyword == "dynamicforward"
        bind, destination = ssh_config_forward_parts(parts[1:], dynamic=dynamic)
        if not bind:
            continue
        rows.append(
            ssh_tunnel_row(
                forward_types[keyword],
                bind,
                destination,
                host,
                "Config",
                command=str(ssh_config_file()),
            )
        )
    return rows


def parse_ssh_tunnel_process(pid: str, command: str) -> list[dict[str, str]]:
    """Parse SSH tunnel and port-forward rows from one process command."""
    args = split_ssh_command(command)
    if ssh_command_executable_name(args) != "ssh":
        return []
    rows: list[dict[str, str]] = []
    ssh_host = ssh_process_host(args)
    index = 1
    while index < len(args):
        value = args[index]
        if value in ("-L", "-R", "-D"):
            if index + 1 < len(args):
                append_ssh_forward_row(
                    rows, pid, command, ssh_host, value, args[index + 1]
                )
            index += 2
            continue
        if len(value) > 2 and value[:2] in ("-L", "-R", "-D"):
            append_ssh_forward_row(rows, pid, command, ssh_host, value[:2], value[2:])
        index += 1
    return rows


def merge_ssh_tunnel_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return SSH tunnel rows merged by forwarding endpoint."""
    merged: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("Type", ""),
            row.get("Bind", ""),
            row.get("Destination", ""),
            row.get("SSH Host", ""),
        )
        if key not in merged:
            merged[key] = dict(row)
            continue
        existing = merged[key]
        sources = {
            source.strip()
            for source in (existing.get("Source", ""), row.get("Source", ""))
            if source.strip()
        }
        existing["Source"] = ", ".join(sorted(sources))
        if row.get("PID"):
            existing["PID"] = row["PID"]
        if row.get("Command") and row.get("Source") == "Process":
            existing["Command"] = row["Command"]
    return list(merged.values())


def parse_ssh_tunnels(output: str, host: str = "") -> list[dict[str, str]]:
    """Parse configured and active SSH tunnel and port-forward rows."""
    config_lines: list[str] = []
    process_lines: list[str] = []
    section = "process"
    for line in strip_ansi(output).splitlines():
        if line.strip() == "__HHS_SSH_CONFIG__":
            section = "config"
            continue
        if line.strip() == "__HHS_SSH_PROCESSES__":
            section = "process"
            continue
        if section == "config":
            config_lines.append(line)
        else:
            process_lines.append(line)

    rows: list[dict[str, str]] = []
    rows.extend(parse_ssh_config_tunnels("\n".join(config_lines), host) if host else [])
    for line in process_lines:
        match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", line)
        if not match:
            continue
        rows.extend(parse_ssh_tunnel_process(match.group(1), match.group(2)))
    return merge_ssh_tunnel_rows(rows)


def normalized_bind_host(host: str) -> str:
    """Return a reachable host name for a tunnel bind address."""
    clean_host = host.strip().strip("[]")
    if clean_host in {"", "*", "0.0.0.0", "::", "::0"}:
        return "127.0.0.1"
    return clean_host


def split_bind_address(bind: str) -> tuple[str, int | None]:
    """Return host and port from a tunnel bind value."""
    clean_bind = bind.strip()
    if not clean_bind:
        return "127.0.0.1", None
    if clean_bind.startswith("[") and "]:" in clean_bind:
        host, port = clean_bind[1:].split("]:", 1)
        return normalized_bind_host(host), int(port) if port.isdigit() else None
    if ":" in clean_bind:
        host, port = clean_bind.rsplit(":", 1)
        return normalized_bind_host(host), int(port) if port.isdigit() else None
    return "127.0.0.1", int(clean_bind) if clean_bind.isdigit() else None


def split_host_port(value: str) -> tuple[str, int | None]:
    """Return host and port from a host:port value."""
    clean_value = value.strip()
    if not clean_value or clean_value.upper() == "SOCKS":
        return clean_value, None
    if clean_value.startswith("[") and "]:" in clean_value:
        host, port = clean_value[1:].split("]:", 1)
        return host, int(port) if port.isdigit() else None
    if ":" in clean_value:
        host, port = clean_value.rsplit(":", 1)
        return host, int(port) if port.isdigit() else None
    return clean_value, int(clean_value) if clean_value.isdigit() else None


@lru_cache(maxsize=1)
def default_port_kinds() -> dict[int, str]:
    """Return default port usage labels loaded from the bundled CSV asset."""
    port_kinds: dict[int, str] = {}
    try:
        with hhs_ui.PORTS_DEFAULT_FILE.open(newline="", encoding="utf-8") as csv_file:
            for row in csv.DictReader(csv_file):
                port = str(row.get("Port", "")).strip()
                kind = str(row.get("Kind", "")).strip()
                if port.isdigit() and kind:
                    port_kinds[int(port)] = kind
    except OSError:
        return {}
    return port_kinds


def ssh_tunnel_kind_port(row: dict[str, str]) -> int | None:
    """Return the service port used to identify an SSH tunnel kind."""
    if row.get("Type", "").lower() == "dynamic":
        _, bind_port = split_bind_address(row.get("Bind", ""))
        return bind_port
    _, destination_port = split_host_port(row.get("Destination", ""))
    if destination_port is not None:
        return destination_port
    _, bind_port = split_bind_address(row.get("Bind", ""))
    return bind_port


def ssh_tunnel_kind(row: dict[str, str]) -> str:
    """Return the default app usage label for an SSH tunnel row."""
    port = ssh_tunnel_kind_port(row)
    if port is None:
        return ""
    return default_port_kinds().get(port, "")


def local_port_is_reachable(host: str, port: int | None) -> bool:
    """Return whether a local TCP host and port accepts connections."""
    if port is None:
        return False
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except OSError:
        return False


def build_port_reachability_command(host: str, port: int) -> str:
    """Build a shell command that checks whether a TCP port is reachable."""
    safe_host = shlex.quote(host)
    safe_port = shlex.quote(str(port))
    return (
        f"host={safe_host}; port={safe_port}; "
        "if command -v nc >/dev/null 2>&1; then "
        'nc -z -w 1 "$host" "$port"; '
        "else "
        'bash -c "</dev/tcp/${host}/${port}" >/dev/null 2>&1; '
        "fi"
    )


def complete_cached_status_background_command(
    job_name: str,
) -> subprocess.CompletedProcess[str] | None:
    """Complete a cached status command and store success or failure output."""
    completed = background_job_result(job_name)
    if completed is None:
        return None
    result, metadata = completed
    cache_background_command_result(metadata, result)
    return result


def cached_remote_port_reachability(
    host: str, port: int | None
) -> tuple[bool | None, bool, str]:
    """Return cached remote port reachability and start a background refresh."""
    if port is None:
        return False, False, ""
    command = build_port_reachability_command(host, port)
    job_name = cached_command_job_name(command, "ssh_status")
    complete_cached_status_background_command(job_name)
    result, fresh_cache = cached_background_command_result(command, "ssh_status")
    if not fresh_cache and not background_job_is_running(job_name):
        start_cached_background_command(
            job_name,
            command,
            "Checking SSH tunnel statuses",
            "ssh_status",
            hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
            3,
        )
    checking = background_job_is_running(job_name) and not fresh_cache
    if result is None:
        return None, True, job_name
    return result.returncode == 0, checking, job_name


def ssh_tunnel_status_label(row: dict[str, str]) -> tuple[str, bool, str]:
    """Return the visible reachability label, refresh state, and job name."""
    host, port = split_bind_address(row.get("Bind", ""))
    if row.get("Type", "").lower() == "remote":
        reachable, checking, job_name = cached_remote_port_reachability(host, port)
        if reachable is None:
            return "Checking", checking, job_name
        return "Reachable" if reachable else "Not reachable", checking, job_name
    return (
        "Reachable" if local_port_is_reachable(host, port) else "Not reachable",
        False,
        "",
    )


def annotate_ssh_tunnel_statuses(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    """Return SSH tunnel rows with status values and running status job names."""
    annotated_rows: list[dict[str, str]] = []
    status_job_names: list[str] = []
    for row in rows:
        annotated_row = dict(row)
        status_label, checking, job_name = ssh_tunnel_status_label(row)
        annotated_row["Status"] = status_label
        if checking and job_name:
            status_job_names.append(job_name)
        annotated_rows.append(annotated_row)
    return annotated_rows, tuple(dict.fromkeys(status_job_names))


def ssh_tunnel_link(bind: str) -> str:
    """Return the local loopback link value for a tunnel bind value."""
    _, port = split_bind_address(bind)
    return f"http://127.0.0.1:{port}" if port is not None else ""


def display_ssh_tunnel_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return SSH tunnel rows shaped for the visible table columns."""
    return [
        {
            "Local Port": row.get("Bind", ""),
            "Remote Host:Port": row.get("Destination", ""),
            "Kind": ssh_tunnel_kind(row),
            "Status": row.get("Status", ""),
            "Link": ssh_tunnel_link(row.get("Bind", "")),
        }
        for row in rows
    ]


def filter_ssh_tunnel_rows(
    rows: list[dict[str, str]],
    tunnel_filter: str,
    text_filter: str = "",
) -> list[dict[str, str]]:
    """Return SSH tunnel rows matching the selected displayed Kind filter."""
    clean_filter = text_filter.strip().lower()
    if tunnel_filter == "Other":
        return [
            row
            for row in rows
            if not clean_filter or clean_filter in ssh_tunnel_kind(row).lower()
        ]
    if tunnel_filter == "All":
        return rows
    return [
        row
        for row in rows
        if ssh_tunnel_kind(row).lower() == tunnel_filter.strip().lower()
    ]


def ssh_tunnel_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for SSH tunnel status values."""
    value_text = str(value).strip().lower()
    base_style = "font-weight: 800;"
    if value_text == "reachable":
        return f"{base_style} color: #50fa7b;"
    if value_text == "not reachable":
        return f"{base_style} color: #ff5555;"
    if value_text == "checking":
        return f"{base_style} color: var(--hhs-comment);"
    return base_style


def styled_ssh_tunnel_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return SSH tunnel rows with styled Status cells."""
    dataframe = pd.DataFrame(display_table_rows(display_ssh_tunnel_rows(rows)))
    styler = dataframe.style
    if "Status" in dataframe:
        styler = styler.map(ssh_tunnel_status_cell_style, subset=["Status"])
    return styler


def parse_hhs_history(output: str) -> list[dict[str, str]]:
    """Parse __hhs_history terminal output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.HISTORY_COMMAND_LINE_PATTERN.match(line.strip())
        if match:
            command_value = match.group(2).strip()
            if re.fullmatch(r"#\d+", command_value):
                continue
            rows.append(
                {
                    "Index": match.group(1).strip(),
                    "Value": command_value,
                }
            )
    return rows


def parse_hhs_history_dirs(output: str) -> list[dict[str, str]]:
    """Parse __hhs_dirs list output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.HISTORY_DIRECTORY_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {
                    "Type": match.group(2).strip(),
                    "Value": match.group(3).strip(),
                }
            )
    return rows


def parse_hhs_history_stats(output: str) -> list[dict[str, int | str]]:
    """Parse __hhs_hist_stats output into chart rows."""
    rows: list[dict[str, int | str]] = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.HISTORY_STATS_LINE_PATTERN.match(line.strip())
        if match:
            rows.append(
                {
                    "Command": match.group(1).strip(),
                    "Count": int(match.group(2)),
                }
            )
    return rows


@st.fragment(run_every="2s")
def render_ssh_tunnel_status_loader(job_names: tuple[str, ...]) -> None:
    """Render one polling loader while SSH tunnel status jobs are running."""
    if any(background_job_is_running(job_name) for job_name in job_names):
        started_times: list[float] = []
        for job_name in job_names:
            job = background_job_state(job_name)
            if not job:
                continue
            try:
                started_at = float(job.get("started_at", 0.0) or 0.0)
            except (TypeError, ValueError):
                started_at = 0.0
            if started_at:
                started_times.append(started_at)
        render_command_loader(
            "Checking SSH tunnel statuses",
            min(started_times) if started_times else None,
        )
        return
    if job_names:
        st.rerun()


def parse_hhs_disk_usage(output: str) -> list[dict[str, float | str]]:
    """Parse __hhs_du output into disk usage chart rows."""
    rows: list[dict[str, float | str]] = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.DISK_USAGE_LINE_PATTERN.match(line)
        if match:
            size = match.group(2).strip()
            rows.append(
                {
                    "Path": match.group(1).strip(),
                    "Size": size,
                    "Bytes": human_size_to_bytes(size),
                }
            )
    return rows


def parse_process_monitor(output: str, metric: str) -> list[dict[str, float | str]]:
    """Parse top or ps process output into monitor chart rows."""
    rows: list[dict[str, float | str]] = []
    headers: list[str] = []
    selected_field = str(
        hhs_ui.TOP_PROCESS_SORT_KEYS.get(metric, hhs_ui.TOP_PROCESS_SORT_KEYS["CPU"])[
            "field"
        ]
    )
    for line in strip_ansi(output).splitlines():
        parts = line.split()
        if not parts:
            continue
        normalized_parts = [part.upper() for part in parts]
        if "PID" in normalized_parts and (
            "%CPU" in normalized_parts or "CPU" in normalized_parts
        ):
            headers = normalized_parts
            rows = []
            continue
        if not headers or not parts[0].isdigit():
            continue
        index_by_name = {name: index for index, name in enumerate(headers)}
        pid_index = index_by_name.get("PID", 0)
        user_index = index_by_name.get("USER")
        command_index = index_by_name.get("COMMAND", len(parts) - 1)
        cpu_index = index_by_name.get("%CPU", index_by_name.get("CPU"))
        mem_index = index_by_name.get("%MEM", index_by_name.get("MEM"))
        value_index = cpu_index if selected_field == "CPU" else mem_index
        if value_index is None or value_index >= len(parts):
            continue
        command = (
            " ".join(parts[command_index:])
            if command_index == len(headers) - 1
            else parts[command_index]
        )
        raw_value = parts[value_index]
        rows.append(
            {
                "PID": parts[pid_index] if pid_index < len(parts) else "",
                "User": (
                    parts[user_index]
                    if user_index is not None and user_index < len(parts)
                    else ""
                ),
                "Command": command,
                "CPU": (
                    parts[cpu_index]
                    if cpu_index is not None and cpu_index < len(parts)
                    else ""
                ),
                "MEM": (
                    parts[mem_index]
                    if mem_index is not None and mem_index < len(parts)
                    else ""
                ),
                "Value": metric_value(raw_value),
                "ValueLabel": raw_value,
            }
        )
    return rows


def process_monitor_chart_rows(
    output: str, metric: str, limit: int = 10
) -> list[dict[str, float | str]]:
    """Return sorted process monitor rows ready for charting."""
    rows = sorted(
        parse_rows_cached(
            f"process_monitor_{metric}",
            output,
            lambda parsed_output: parse_process_monitor(parsed_output, metric),
        ),
        key=lambda row: float(row["Value"]),
        reverse=True,
    )
    if metric == "CPU":
        rows = [row for row in rows if float(row["Value"]) > 0.0]
    return rows[: max(1, int(limit))]


def parse_hhs_process_list(output: str) -> list[dict[str, str]]:
    """Parse __hhs_process_list output into process rows."""
    rows: list[dict[str, str]] = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.PROCESS_LIST_LINE_PATTERN.match(line)
        if not match:
            continue
        rows.append(
            {
                "UID": match.group(1),
                "PID": match.group(2),
                "PPID": match.group(3),
                "Command": match.group(4).strip(),
                "Status": match.group(5).strip().title(),
            }
        )
    return rows


def path_sources(output: str) -> list[str]:
    """Parse __hhs_paths output into path source labels."""
    sources = []
    for line in strip_ansi(output).splitlines():
        match = hhs_ui.PATH_SOURCE_PATTERN.search(line.strip())
        if match:
            sources.append(match.group(1).strip())
    return sources


def path_types(output: str) -> list[str]:
    """Parse __hhs_paths output into path type glyphs."""
    types = []
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if not hhs_ui.PATH_SOURCE_PATTERN.search(clean_line):
            continue
        match = hhs_ui.PATH_TYPE_PATTERN.search(clean_line)
        if match:
            types.append(match.group(1).strip())
    return types


def path_entries() -> list[str]:
    """Return current PATH entries for the Streamlit process."""
    return [entry for entry in os.environ.get("PATH", "").split(":") if entry]


def parse_hhs_paths(output: str) -> list[dict[str, str]]:
    """Parse __hhs_paths terminal output into editable PATH rows."""
    sources = path_sources(output)
    types = path_types(output)
    rows = []
    for index, path_entry in enumerate(path_entries()):
        source = sources[index] if index < len(sources) else "PATH entry"
        path_type = types[index] if index < len(types) else ""
        rows.append({"Type": path_type, "Name": source, "Value": path_entry})
    return rows


def env_widget_key_fragment(name: str) -> str:
    """Return a safe Streamlit widget key fragment for an environment name."""
    safe_name = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    return safe_name or "unnamed"


def env_value_editor_key(name: str) -> str:
    """Return the Streamlit widget key for a selected environment value editor."""
    return f"{hhs_ui.ENV_VALUE_EDITOR_KEY_PREFIX}_{env_widget_key_fragment(name)}"


def path_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected PATH value editor."""
    return f"{hhs_ui.PATH_VALUE_EDITOR_KEY_PREFIX}_{index}"


def dir_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected directory value viewer."""
    return f"{hhs_ui.DIR_VALUE_EDITOR_KEY_PREFIX}_{index}"


def cmd_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected command value viewer."""
    return f"{hhs_ui.CMD_VALUE_EDITOR_KEY_PREFIX}_{index}"


def alias_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected alias value viewer."""
    return f"{hhs_ui.ALIAS_VALUE_EDITOR_KEY_PREFIX}_{index}"


def service_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected service value viewer."""
    return f"{hhs_ui.SERVICE_VALUE_EDITOR_KEY_PREFIX}_{index}"


def history_command_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected history command value viewer."""
    return f"{hhs_ui.HISTORY_COMMAND_VALUE_EDITOR_KEY_PREFIX}_{index}"


def history_directory_value_editor_key(index: int) -> str:
    """Return the Streamlit widget key for a selected history directory value viewer."""
    return f"{hhs_ui.HISTORY_DIRECTORY_VALUE_EDITOR_KEY_PREFIX}_{index}"


def ai_model_table_key() -> str:
    """Return the AI model dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.AI_MODEL_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.AI_MODEL_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.AI_MODEL_TABLE_KEY}_{reset_counter}"


def reset_ai_model_table_selection() -> None:
    """Reset the AI model dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.AI_MODEL_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.AI_MODEL_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def docker_container_table_key() -> str:
    """Return the Docker container dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY] = (
            reset_counter
        )
    return f"{hhs_ui.DOCKER_CONTAINER_TABLE_KEY}_{reset_counter}"


def reset_docker_container_table_selection() -> None:
    """Reset the Docker container dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY] = (
        reset_counter + 1
    )


def docker_image_table_key() -> str:
    """Return the Docker image dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.DOCKER_IMAGE_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.DOCKER_IMAGE_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.DOCKER_IMAGE_TABLE_KEY}_{reset_counter}"


def reset_docker_image_table_selection() -> None:
    """Reset the Docker image dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.DOCKER_IMAGE_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.DOCKER_IMAGE_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def home_tools_table_key() -> str:
    """Return the Home Tools dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault("home_tools_table_reset_counter", 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state["home_tools_table_reset_counter"] = reset_counter
    return f"home_tools_table_{reset_counter}"


def reset_home_tools_table_selection() -> None:
    """Reset the Home Tools dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault("home_tools_table_reset_counter", 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state["home_tools_table_reset_counter"] = reset_counter + 1


def home_shopts_table_key() -> str:
    """Return the Home SHOPTS dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.HOME_SHOPTS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.HOME_SHOPTS_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.HOME_SHOPTS_TABLE_KEY}_{reset_counter}"


def reset_home_shopts_table_selection() -> None:
    """Reset the Home SHOPTS dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.HOME_SHOPTS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.HOME_SHOPTS_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def env_table_key() -> str:
    """Return the Streamlit dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.ENV_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.ENV_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.ENV_TABLE_KEY}_{reset_counter}"


def reset_env_table_selection() -> None:
    """Reset the environment dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(hhs_ui.ENV_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.ENV_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def path_table_key() -> str:
    """Return the Streamlit PATH dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.PATH_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.PATH_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.PATH_TABLE_KEY}_{reset_counter}"


def reset_path_table_selection() -> None:
    """Reset the PATH dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(hhs_ui.PATH_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.PATH_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def dir_table_key() -> str:
    """Return the Streamlit directory dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.DIR_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.DIR_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.DIR_TABLE_KEY}_{reset_counter}"


def reset_dir_table_selection() -> None:
    """Reset the saved directory dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(hhs_ui.DIR_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.DIR_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def cmd_table_key() -> str:
    """Return the Streamlit command dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.CMD_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.CMD_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.CMD_TABLE_KEY}_{reset_counter}"


def reset_cmd_table_selection() -> None:
    """Reset the saved command dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(hhs_ui.CMD_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.CMD_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def alias_table_key() -> str:
    """Return the Streamlit alias dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.ALIAS_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.ALIAS_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.ALIAS_TABLE_KEY}_{reset_counter}"


def reset_alias_table_selection() -> None:
    """Reset the alias dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(hhs_ui.ALIAS_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.ALIAS_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def refresh_ai_model_listing() -> None:
    """Refresh cached AI model listings and reset the AI model selection."""
    cache_delete_tag("ai_models")
    cache_delete_tag("ai")
    reset_ai_model_table_selection()


def refresh_home_tools_listing() -> None:
    """Refresh cached Home tool listings and reset the tool selection."""
    cache_delete_tag("tools")
    reset_home_tools_table_selection()


def refresh_home_shopts_listing() -> None:
    """Refresh the cached Home SHOPTS listing after a shell option change."""
    cache_delete_tag("shopt")
    reset_home_shopts_table_selection()


def refresh_env_listing() -> None:
    """Refresh cached environment listings and reset the environment selection."""
    cache_delete_tag("env")
    reset_env_table_selection()


def refresh_path_listing() -> None:
    """Refresh cached PATH listings and reset the PATH selection."""
    cache_delete_tag("path")
    reset_path_table_selection()


def refresh_dir_listing() -> None:
    """Refresh cached saved directory listings and reset the directory selection."""
    cache_delete_tag("dirs")
    reset_dir_table_selection()


def refresh_cmd_listing() -> None:
    """Refresh cached saved command listings and reset the command selection."""
    cache_delete_tag("cmds")
    reset_cmd_table_selection()


def refresh_alias_listing() -> None:
    """Refresh cached alias listings and reset the alias selection."""
    cache_delete_tag("aliases")
    reset_alias_table_selection()


def refresh_service_listing() -> None:
    """Refresh cached service listings and reset the service selection."""
    cache_delete_tag("services")
    reset_service_table_selection()


def refresh_process_listing() -> None:
    """Refresh cached process monitor listings."""
    cache_delete_tag("monitor_process")


def service_table_key() -> str:
    """Return the Streamlit service dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.SERVICE_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.SERVICE_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.SERVICE_TABLE_KEY}_{reset_counter}"


def history_command_table_key() -> str:
    """Return the Streamlit history command dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.HISTORY_COMMAND_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.HISTORY_COMMAND_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.HISTORY_COMMAND_TABLE_KEY}_{reset_counter}"


def history_directory_table_key() -> str:
    """Return the Streamlit history directory dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.HISTORY_DIRECTORY_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.HISTORY_DIRECTORY_TABLE_RESET_COUNTER_KEY] = (
            reset_counter
        )
    return f"{hhs_ui.HISTORY_DIRECTORY_TABLE_KEY}_{reset_counter}"


def env_value_overrides() -> dict[str, str]:
    """Return session-scoped environment value overrides."""
    overrides = st.session_state.setdefault(hhs_ui.ENV_VALUE_OVERRIDES_KEY, {})
    if not isinstance(overrides, dict):
        overrides = {}
        st.session_state[hhs_ui.ENV_VALUE_OVERRIDES_KEY] = overrides
    return overrides


def path_value_overrides() -> dict[str, str]:
    """Return session-scoped PATH value overrides."""
    overrides = st.session_state.setdefault(hhs_ui.PATH_VALUE_OVERRIDES_KEY, {})
    if not isinstance(overrides, dict):
        overrides = {}
        st.session_state[hhs_ui.PATH_VALUE_OVERRIDES_KEY] = overrides
    return overrides


def apply_env_value_overrides(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return environment rows with session-scoped value overrides applied."""
    overrides = env_value_overrides()
    return [
        {
            **row,
            "Value": str(overrides.get(row["Name"], row["Value"])),
        }
        for row in rows
    ]


def apply_path_value_overrides(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return PATH rows with session-scoped value overrides applied."""
    overrides = path_value_overrides()
    return [
        {
            **row,
            "Value": str(overrides.get(row["Value"], row["Value"])),
        }
        for row in rows
    ]


def apply_selected_env_value(name: str, value: str) -> bool:
    """Persist a selected environment value and store it for table rerenders."""
    result = run_hhs_env_action("add", name, value)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    refresh_env_listing()
    if result.returncode == 0:
        os.environ[name] = value
        env_value_overrides()[name] = value
        push_floating_status(
            status_message or f'Environment variable saved: "{name}"',
            "info",
        )
    else:
        push_floating_status(
            status_message or f"Unable to save environment variable: {name}",
            "error",
        )
    save_ui_state()
    return result.returncode == 0


def apply_env_delete(name: str) -> None:
    """Delete a custom environment value and reset the table selection."""
    result = run_hhs_env_action("del", name)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    refresh_env_listing()
    if result.returncode == 0:
        os.environ.pop(name, None)
        env_value_overrides().pop(name, None)
        push_floating_status(
            status_message or f'Environment variable removed: "{name}"',
            "info",
        )
    else:
        push_floating_status(
            status_message or f"Unable to delete environment variable: {name}",
            "error",
        )
    save_ui_state()


def apply_env_add_form_value() -> None:
    """Persist the current custom environment form value."""
    name = str(st.session_state.get("env_add_name", "")).strip()
    value = str(st.session_state.get("env_add_value", ""))
    if not name:
        return
    if apply_selected_env_value(name, value):
        clear_add_form_fields("env")


def push_config_action_status(
    result: subprocess.CompletedProcess[str],
    success_fallback: str,
    error_fallback: str,
) -> None:
    """Push a config action status from command output or a fallback message."""
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        push_floating_status(status_message or success_fallback, "info")
    else:
        push_floating_status(status_message or error_fallback, "error")


def apply_selected_path_value(old_path: str, new_path: str) -> bool:
    """Persist an edited PATH entry and store it for table rerenders."""
    result = run_hhs_path_action("edit", new_path, old_path)
    refresh_path_listing()
    if result.returncode == 0:
        path_values = [entry for entry in path_entries() if entry != old_path]
        if new_path not in path_values:
            path_values.insert(0, new_path)
        os.environ["PATH"] = ":".join(path_values)
        path_value_overrides()[old_path] = new_path
    push_config_action_status(
        result,
        f'PATH entry saved: "{new_path}"',
        f"Unable to save PATH entry: {new_path}",
    )
    save_ui_state()
    return result.returncode == 0


def apply_path_delete(path_value: str) -> None:
    """Delete a PATH entry and reset the table selection."""
    result = run_hhs_path_action("del", path_value)
    refresh_path_listing()
    if result.returncode == 0:
        os.environ["PATH"] = ":".join(
            entry for entry in path_entries() if entry != path_value
        )
        path_value_overrides().pop(path_value, None)
    push_config_action_status(
        result,
        f'PATH entry removed: "{path_value}"',
        f"Unable to remove PATH entry: {path_value}",
    )
    save_ui_state()


def apply_selected_dir_value(name: str, value: str) -> bool:
    """Persist a saved directory value."""
    result = run_hhs_dir_action("add", name, value)
    refresh_dir_listing()
    push_config_action_status(
        result,
        f'Saved directory saved: "{name}"',
        f"Unable to save directory: {name}",
    )
    save_ui_state()
    return result.returncode == 0


def apply_dir_delete(name: str) -> None:
    """Delete a saved directory and reset the table selection."""
    result = run_hhs_dir_action("del", name)
    refresh_dir_listing()
    push_config_action_status(
        result,
        f'Saved directory removed: "{name}"',
        f"Unable to remove saved directory: {name}",
    )
    save_ui_state()


def apply_selected_cmd_value(name: str, value: str) -> bool:
    """Persist a saved command value."""
    result = run_hhs_command_action("add", name, value)
    refresh_cmd_listing()
    push_config_action_status(
        result,
        f'Saved command saved: "{name}"',
        f"Unable to save command: {name}",
    )
    save_ui_state()
    return result.returncode == 0


def apply_cmd_delete(name: str) -> None:
    """Delete a saved command and reset the table selection."""
    result = run_hhs_command_action("del", name)
    refresh_cmd_listing()
    push_config_action_status(
        result,
        f'Saved command removed: "{name}"',
        f"Unable to remove saved command: {name}",
    )
    save_ui_state()


def apply_selected_alias_value(name: str, value: str) -> bool:
    """Persist a custom alias value."""
    result = run_hhs_alias_action("add", name, value)
    refresh_alias_listing()
    push_config_action_status(
        result,
        f'Alias saved: "{name}"',
        f"Unable to save alias: {name}",
    )
    save_ui_state()
    return result.returncode == 0


def apply_alias_delete(name: str) -> None:
    """Delete a custom alias and reset the table selection."""
    result = run_hhs_alias_action("del", name)
    refresh_alias_listing()
    push_config_action_status(
        result,
        f'Alias removed: "{name}"',
        f"Unable to remove alias: {name}",
    )
    save_ui_state()


def apply_home_shopt_action(operation: str, option_name: str) -> None:
    """Set or unset a shell option from the Home SHOPTS table."""
    result = run_hhs_shopt_action(operation, option_name)
    refresh_home_shopts_listing()
    action_label = "set" if operation == "set" else "unset"
    push_config_action_status(
        result,
        f"Shell option {option_name} {action_label}.",
        f"Unable to {action_label} shell option: {option_name}",
    )
    save_ui_state()


def apply_docker_container_action(operation: str, container_id: str) -> None:
    """Run a Docker container action from the selected container table row."""
    clean_container_id = container_id.strip()
    if not clean_container_id:
        return
    result = run_docker_container_action(operation, clean_container_id)
    cache_delete_tag("docker")
    push_config_action_status(
        result,
        f"Docker container {operation} completed: {clean_container_id}",
        f"Docker container {operation} failed: {clean_container_id}",
    )
    reset_docker_container_table_selection()
    save_ui_state()


def apply_docker_image_action(image_id: str) -> None:
    """Delete a Docker image from the selected image table row."""
    clean_image_id = image_id.strip()
    if not clean_image_id:
        return
    result = run_docker_image_delete(clean_image_id)
    cache_delete_tag("docker")
    push_config_action_status(
        result,
        f"Docker image deleted: {clean_image_id}",
        f"Docker image deletion failed: {clean_image_id}",
    )
    reset_docker_image_table_selection()
    save_ui_state()


def apply_selected_env_editor_value(name: str, editor_key: str) -> None:
    """Export the current selected environment editor value."""
    apply_selected_env_value(name, str(st.session_state.get(editor_key, "")))


def apply_selected_path_editor_value(old_path: str, editor_key: str) -> None:
    """Persist the current selected PATH editor value."""
    apply_selected_path_value(old_path, str(st.session_state.get(editor_key, "")))


def apply_selected_dir_editor_value(name: str, editor_key: str) -> None:
    """Persist the current selected directory editor value."""
    apply_selected_dir_value(name, str(st.session_state.get(editor_key, "")))


def apply_selected_cmd_editor_value(name: str, editor_key: str) -> None:
    """Persist the current selected command editor value."""
    apply_selected_cmd_value(name, str(st.session_state.get(editor_key, "")))


def apply_selected_alias_editor_value(name: str, editor_key: str) -> None:
    """Persist the current selected alias editor value."""
    apply_selected_alias_value(name, str(st.session_state.get(editor_key, "")))


def clear_add_form_fields(key_prefix: str, include_name: bool = True) -> None:
    """Clear the new-entry form fields for a config listing after a successful add."""
    if include_name:
        st.session_state[f"{key_prefix}_add_name"] = ""
    st.session_state[f"{key_prefix}_add_value"] = ""


def apply_path_add_form_value() -> None:
    """Persist the current PATH add form value."""
    value = str(st.session_state.get("path_add_value", "")).strip()
    if not value:
        return
    if apply_selected_path_value(value, value):
        clear_add_form_fields("path", include_name=False)


def apply_dir_add_form_value() -> None:
    """Persist the current saved directory add form value."""
    name = str(st.session_state.get("dir_add_name", "")).strip()
    value = str(st.session_state.get("dir_add_value", "")).strip()
    if not name or not value:
        return
    if apply_selected_dir_value(name, value):
        clear_add_form_fields("dir")


def apply_cmd_add_form_value() -> None:
    """Persist the current saved command add form value."""
    name = str(st.session_state.get("cmd_add_name", "")).strip()
    value = str(st.session_state.get("cmd_add_value", ""))
    if not name:
        return
    if apply_selected_cmd_value(name, value):
        clear_add_form_fields("cmd")


def apply_alias_add_form_value() -> None:
    """Persist the current alias add form value."""
    name = str(st.session_state.get("alias_add_name", "")).strip()
    value = str(st.session_state.get("alias_add_value", ""))
    if not name:
        return
    if apply_selected_alias_value(name, value):
        clear_add_form_fields("alias")


def scroll_to_env_value_editor(editor_key: str) -> None:
    """Scroll the browser viewport to the selected environment value editor."""
    selector = f'div[class*="st-key-{editor_key}"] textarea'
    components.html(
        f"""
        <script>
          const selector = {selector!r};
          const scroll_to_editor = () => {{
            const target = window.parent.document.querySelector(selector);
            if (target) {{
              target.scrollIntoView({{ behavior: "smooth", block: "center" }});
              target.focus({{ preventScroll: true }});
            }}
          }};
          window.setTimeout(scroll_to_editor, 75);
        </script>
        """,
        height=hhs_ui.ENV_VALUE_EDITOR_SCROLL_HELPER_HEIGHT,
    )


def scroll_to_ai_model_actions(anchor_id: str) -> None:
    """Scroll the browser viewport to the selected AI model action buttons."""
    components.html(
        f"""
        <script>
          const anchor_id = {anchor_id!r};
          const scroll_to_actions = () => {{
            const doc = window.parent.document;
            const target = doc.getElementById(anchor_id);
            const scrollables = () => [
              doc.scrollingElement,
              doc.documentElement,
              doc.body,
              ...Array.from(doc.querySelectorAll("*")).filter((element) => {{
                const style = window.parent.getComputedStyle(element);
                const can_scroll = /(auto|scroll)/.test(style.overflowY + style.overflow);
                return can_scroll && element.scrollHeight > element.clientHeight;
              }})
            ].filter(Boolean);
            const scroll_bottom = () => {{
              const scroll_height = Math.max(
                doc.body.scrollHeight,
                doc.documentElement.scrollHeight
              );
              window.parent.scrollTo({{ top: scroll_height, behavior: "auto" }});
              for (const item of scrollables()) {{
                item.scrollTop = item.scrollHeight;
              }}
              if (target) {{
                target.scrollIntoView({{ behavior: "auto", block: "end", inline: "nearest" }});
              }}
            }};
            [0, 50, 150, 300, 600, 1000].forEach((delay) => {{
              window.setTimeout(scroll_bottom, delay);
            }});
            window.requestAnimationFrame(scroll_bottom);
          }};
          window.setTimeout(scroll_to_actions, 50);
        </script>
        """,
        height=hhs_ui.AI_MODEL_ACTION_SCROLL_HELPER_HEIGHT,
    )


def render_env_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable environment variable rows."""
    rows = apply_env_value_overrides(rows)
    render_table(
        rows,
        key=env_table_key(),
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        selected_editable=True,
        selected_edit_key=lambda row, _index: env_value_editor_key(row["Name"]),
        selected_edit_value=lambda row, _index: row["Value"],
        selected_edit_label="Selected value",
        selected_edit_max_chars=int(hhs_ui.COMMAND_COLUMNS),
        selected_edit_on_change=apply_selected_env_editor_value,
        selected_edit_args=lambda row, _index: (
            row["Name"],
            env_value_editor_key(row["Name"]),
        ),
        reset_selection=reset_env_table_selection,
        selected_action_buttons=[
            {
                "label": "Delete",
                "glyph": "",
                "key_prefix": "env_delete_button",
                "on_click": apply_env_delete,
                "args": lambda row, _index: (row["Name"],),
            },
        ],
    )


def render_path_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable PATH rows."""
    rows = apply_path_value_overrides(rows)
    render_table(
        rows,
        key=path_table_key(),
        height=hhs_ui.PATH_TABLE_HEIGHT,
        width=hhs_ui.PATH_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        selected_editable=True,
        selected_edit_key=lambda _row, index: path_value_editor_key(index),
        selected_edit_value=lambda row, _index: row["Value"],
        selected_edit_label="Selected PATH value",
        selected_edit_max_chars=int(hhs_ui.COMMAND_COLUMNS),
        selected_edit_on_change=apply_selected_path_editor_value,
        selected_edit_args=lambda row, index: (
            row["Value"],
            path_value_editor_key(index),
        ),
        selected_edit_folder_picker=True,
        reset_selection=reset_path_table_selection,
        selected_action_buttons=[
            {
                "label": "Delete",
                "glyph": "",
                "key_prefix": "path_delete_button",
                "on_click": apply_path_delete,
                "args": lambda row, _index: (row["Value"],),
            },
        ],
    )


def render_dir_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable saved directory rows."""
    render_table(
        rows,
        key=dir_table_key(),
        empty_hint="Select a row to interact",
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        selected_editable=True,
        selected_edit_key=lambda _row, index: dir_value_editor_key(index),
        selected_edit_value=lambda row, _index: row["Value"],
        selected_edit_label="Selected directory path",
        selected_edit_max_chars=int(hhs_ui.COMMAND_COLUMNS),
        selected_edit_on_change=apply_selected_dir_editor_value,
        selected_edit_args=lambda row, index: (
            row["Name"],
            dir_value_editor_key(index),
        ),
        selected_edit_folder_picker=True,
        reset_selection=reset_dir_table_selection,
        selected_action_buttons=[
            {
                "label": "Delete",
                "glyph": "",
                "key_prefix": "dir_delete_button",
                "on_click": apply_dir_delete,
                "args": lambda row, _index: (row["Name"],),
            },
        ],
    )


def render_cmd_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable saved command rows."""
    render_table(
        rows,
        key=cmd_table_key(),
        empty_hint="Select a row to interact",
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        selected_editable=True,
        selected_edit_key=lambda _row, index: cmd_value_editor_key(index),
        selected_edit_value=lambda row, _index: row["Value"],
        selected_edit_label="Selected command value",
        selected_edit_max_chars=int(hhs_ui.COMMAND_COLUMNS),
        selected_edit_on_change=apply_selected_cmd_editor_value,
        selected_edit_args=lambda row, index: (
            row["Name"],
            cmd_value_editor_key(index),
        ),
        reset_selection=reset_cmd_table_selection,
        selected_action_buttons=[
            {
                "label": "Delete",
                "glyph": "",
                "key_prefix": "cmd_delete_button",
                "on_click": apply_cmd_delete,
                "args": lambda row, _index: (row.get("Index") or row["Name"],),
            },
        ],
    )


def render_alias_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable alias rows."""
    render_table(
        rows,
        key=alias_table_key(),
        empty_hint="Select a row to interact",
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        selected_editable=True,
        selected_edit_key=lambda _row, index: alias_value_editor_key(index),
        selected_edit_value=lambda row, _index: row["Value"],
        selected_edit_label="Selected alias expression",
        selected_edit_max_chars=int(hhs_ui.COMMAND_COLUMNS),
        selected_edit_on_change=apply_selected_alias_editor_value,
        selected_edit_args=lambda row, index: (
            row["Name"],
            alias_value_editor_key(index),
        ),
        reset_selection=reset_alias_table_selection,
        selected_action_buttons=[
            {
                "label": "Delete",
                "glyph": "",
                "key_prefix": "alias_delete_button",
                "on_click": apply_alias_delete,
                "args": lambda row, _index: (row["Name"],),
            },
        ],
    )


def render_read_only_rows(
    rows: list[dict[str, str]],
    table_key: str,
    empty_caption: str = "Select a row to interact",
    selected_value: Callable[[dict[str, str], int], str] | None = None,
) -> None:
    """Render selectable read-only configuration rows."""
    render_table(
        rows,
        key=table_key,
        empty_hint=empty_caption,
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: (
            "Selected: "
            + (
                selected_value(row, _index)
                if selected_value is not None
                else row.get("Name") or row.get("Index") or row.get("Value", "")
            )
        ),
    )


def service_name_cell_style(_: object) -> str:
    """Return the dataframe cell style for service names."""
    return (
        "background-color: #21222c;"
        "border-radius: 3px;"
        "color: #8be9fd;"
        "font-weight: 800;"
    )


def service_value_cell_style(value: object) -> str:
    """Return the dataframe cell style for service status values."""
    value_text = str(value).lower()
    base_style = "background-color: #21222c; border-radius: 3px; font-weight: 800;"
    if "up" in value_text:
        return f"{base_style} color: #50fa7b;"
    if "down" in value_text:
        return f"{base_style} color: #ff5555;"
    return f"{base_style} color: #f8f8f2;"


def service_is_up(row: dict[str, str]) -> bool:
    """Return whether a service row is currently up."""
    return "up" in row.get("Value", "").lower()


def service_is_down(row: dict[str, str]) -> bool:
    """Return whether a service row is currently down."""
    return "down" in row.get("Value", "").lower()


def ollama_service_is_available_from_output(output: str) -> bool:
    """Return whether the parsed services output has a non-down Ollama service row."""
    for row in parse_rows_cached("services", output, parse_hhs_services):
        if row.get("Name", "").strip() == "ollama":
            return not service_is_down(row)
    return False


def remember_ollama_service_availability(
    result: subprocess.CompletedProcess[str] | None,
) -> bool:
    """Store Ollama service availability when a successful services result exists."""
    if result is None or result.returncode != 0:
        return bool(
            st.session_state.get(hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY, False)
        )
    available = ollama_service_is_available_from_output(result.stdout)
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY] = available
    return available


def ollama_service_is_available() -> bool:
    """Return the last known Ollama service availability without starting commands."""
    return bool(st.session_state.get(hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY, False))


def initialize_ollama_service_availability() -> None:
    """Seed AI tab visibility from cached service data without starting commands."""
    if st.session_state.get(hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY):
        return
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY] = True
    cached_hhs_services_result()


def main_views() -> tuple[str, ...]:
    """Return the visible main view names for the current environment and connection."""
    views = hhs_ui.VIEWS
    if connected_ssh_host():
        views = (*views, hhs_ui.SSH_VIEW)
    if ollama_service_is_available():
        views = (*views, hhs_ui.AI_VIEW)
    return views


def main_view_label(view: str) -> str:
    """Return the display label for a main view tab."""
    return hhs_ui.VIEW_LABELS.get(view, view)


def reset_service_table_selection() -> None:
    """Reset the service dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.SERVICE_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.SERVICE_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


def apply_selected_tool_action(operation: str, tool_name: str) -> None:
    """Schedule the selected Home tool install/uninstall action."""
    close_home_tool_tldr_dialog()
    st.session_state["home_tool_action_execute_pending"] = {
        "operation": operation,
        "tool_name": tool_name,
    }
    reset_home_tools_table_selection()


def execute_pending_home_tool_action() -> None:
    """Run a pending Home tool action from the normal render flow."""
    pending = st.session_state.pop("home_tool_action_execute_pending", None) or {}
    operation = str(pending.get("operation", "")).strip()
    tool_name = str(pending.get("tool_name", "")).strip()
    if operation and tool_name:
        started = start_background_bash_command(
            HOME_TOOL_ACTION_JOB,
            build_hhs_hspm_command(operation, tool_name),
            f"{home_tool_action_noun(operation)} of {tool_name}",
            hhs_ui_constants.UI_COMMAND_LONG_ACTION_TIMEOUT_SECONDS,
            metadata={"operation": operation, "tool_name": tool_name},
        )
        if started:
            push_floating_status(
                f"{home_tool_action_noun(operation)} started: {tool_name}",
                "info",
            )
        else:
            push_floating_status("Another tool action is already running.", "warn")

    completed = background_job_result(HOME_TOOL_ACTION_JOB)
    if completed is None:
        return

    result, metadata = completed
    operation = str(metadata.get("operation", operation)).strip()
    tool_name = str(metadata.get("tool_name", tool_name)).strip()
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    refresh_home_tools_listing()
    close_home_tool_tldr_dialog()
    st.session_state["home_tool_action_operation"] = operation
    st.session_state["home_tool_action_name"] = tool_name
    st.session_state["home_tool_action_message"] = result.stdout or result.stderr or ""
    st.session_state["home_tool_action_succeeded"] = result.returncode == 0
    if result.returncode == 0:
        push_floating_status(
            status_message
            or f"{home_tool_action_noun(operation)} completed: {tool_name}",
            "info",
        )
    else:
        push_floating_status(
            status_message or f"{home_tool_action_noun(operation)} failed: {tool_name}",
            "error",
        )


def home_tool_action_noun(operation: str) -> str:
    """Return the display noun for a Home tool action operation."""
    return {
        "install": "Installation",
        "uninstall": "Uninstallation",
        "reinstall": "Reinstallation",
    }.get(operation, "Operation")


def close_home_tool_action_dialog() -> None:
    """Close the selected Home tool action result dialog."""
    st.session_state.pop("home_tool_action_operation", None)
    st.session_state.pop("home_tool_action_name", None)
    st.session_state.pop("home_tool_action_message", None)
    st.session_state.pop("home_tool_action_succeeded", None)


def ssh_connection_dialog_is_open() -> bool:
    """Return whether the SSH connection result dialog is currently requested."""
    return bool(str(st.session_state.get("ssh_connection_dialog_title", "")).strip())


def render_home_tool_action_dialog() -> bool:
    """Render the selected Home tool action result dialog when requested."""
    tool_name = str(st.session_state.get("home_tool_action_name", "")).strip()
    if not tool_name or ssh_connection_dialog_is_open():
        return False

    operation = str(st.session_state.get("home_tool_action_operation", "")).strip()
    output = strip_ansi(
        str(st.session_state.get("home_tool_action_message", ""))
    ).strip()
    succeeded = bool(st.session_state.get("home_tool_action_succeeded", False))
    status = "succeeded" if succeeded else "failed"
    title = f"{home_tool_action_noun(operation)} of {tool_name} {status}"

    def render_body() -> None:
        """Render the selected Home tool action result body."""
        if output:
            render_terminal_output(
                output,
                css_classes="hhs-home-tool-action-output",
            )

    return pop_dialog(
        title=title,
        body=render_body,
        buttons=(
            {
                "label": "Close",
                "key": "home_tool_action_close_button",
            },
        ),
        close_callback=close_home_tool_action_dialog,
    )


def apply_selected_tool_tldr(tool_name: str) -> None:
    """Load TLDR output for the selected Home tool and open its dialog."""
    close_home_tool_action_dialog()
    result = run_tool_tldr(tool_name)
    st.session_state["home_tool_tldr_name"] = tool_name
    st.session_state["home_tool_tldr_output"] = result.stdout or result.stderr or ""
    st.session_state["home_tool_tldr_succeeded"] = result.returncode == 0
    if result.returncode == 0:
        push_floating_status(f"Loaded TLDR: {tool_name}", "info")
    else:
        push_floating_status(f"Unable to load TLDR: {tool_name}", "error")


def close_home_tool_tldr_dialog() -> None:
    """Close the selected Home tool TLDR dialog."""
    st.session_state.pop("home_tool_tldr_name", None)
    st.session_state.pop("home_tool_tldr_output", None)
    st.session_state.pop("home_tool_tldr_succeeded", None)


def render_home_tool_tldr_dialog() -> bool:
    """Render the selected Home tool TLDR output dialog when requested."""
    tool_name = str(st.session_state.get("home_tool_tldr_name", "")).strip()
    if not tool_name or ssh_connection_dialog_is_open():
        return False

    output = strip_ansi(str(st.session_state.get("home_tool_tldr_output", ""))).strip()
    succeeded = bool(st.session_state.get("home_tool_tldr_succeeded", False))

    def render_body() -> None:
        """Render the selected Home tool TLDR result body."""
        if succeeded:
            st.code(output or "No TLDR output found.", language="text")
        else:
            st.error(output or f"Unable to load TLDR for {tool_name}.")

    return pop_dialog(
        title=f"TLDR: {tool_name}",
        body=render_body,
        buttons=(
            {
                "label": "Close",
                "key": "home_tool_tldr_close_button",
            },
        ),
        close_callback=close_home_tool_tldr_dialog,
    )


def apply_selected_service_action(operation: str, service_name: str) -> None:
    """Schedule a service action and reset the service selection."""
    st.session_state["service_action_execute_pending"] = {
        "operation": operation,
        "service_name": service_name,
    }
    refresh_service_listing()


def execute_pending_service_action() -> None:
    """Start or complete a background service action."""
    pending = st.session_state.pop("service_action_execute_pending", None) or {}
    operation = str(pending.get("operation", "")).strip()
    service_name = str(pending.get("service_name", "")).strip()
    if operation and service_name:
        started = start_background_bash_command(
            SERVICE_ACTION_JOB,
            build_hhs_services_command(operation, service_name),
            f"Service {operation}: {service_name}",
            hhs_ui_constants.UI_COMMAND_SERVICE_ACTION_TIMEOUT_SECONDS,
            metadata={"operation": operation, "service_name": service_name},
        )
        if started:
            push_floating_status(f"Service {operation} started: {service_name}", "info")
        else:
            push_floating_status("Another service action is already running.", "warn")

    completed = background_job_result(SERVICE_ACTION_JOB)
    if completed is None:
        return

    result, metadata = completed
    operation = str(metadata.get("operation", operation)).strip()
    service_name = str(metadata.get("service_name", service_name)).strip()
    status_message = service_action_status_message(result, operation, service_name)
    refresh_service_listing()
    if result.returncode == 0:
        push_floating_status(
            status_message or f"Service {operation} completed: {service_name}",
            "info",
        )
    else:
        push_floating_status(
            status_message or f"Service {operation} failed: {service_name}",
            "error",
        )
    if service_name.lower() == "ollama":
        st.rerun()


def apply_selected_process_kill(process_name: str) -> None:
    """Kill the selected process name and store the action result."""
    result = run_hhs_process_kill(process_name)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    refresh_process_listing()
    st.session_state["monitor_process_action_message"] = status_message
    st.session_state["monitor_process_action_succeeded"] = result.returncode == 0
    if result.returncode == 0:
        push_floating_status(
            status_message or f"Killed process: {process_name}", "info"
        )
    else:
        push_floating_status(
            status_message or f"Unable to kill process: {process_name}", "error"
        )


def styled_service_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return service rows with styled Name and Value cells."""
    dataframe = pd.DataFrame(rows)
    styler = dataframe.style
    if "Name" in dataframe:
        styler = styler.map(service_name_cell_style, subset=["Name"])
    if "Value" in dataframe:
        styler = styler.map(service_value_cell_style, subset=["Value"])
    return styler


def render_service_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable read-only service rows with status styling."""
    _, selected_row = render_table(
        rows,
        key=service_table_key(),
        action_hint="",
        table_data=styled_service_rows(rows),
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        reset_selection=reset_ai_model_table_selection,
        action_buttons=[
            {
                "label": "Start",
                "key_prefix": "service_start_button",
                "on_click": apply_selected_service_action,
                "disabled": lambda row, _index: service_is_up(row),
                "args": lambda row, _index: ("start", row["Name"]),
            },
            {
                "label": "Stop",
                "key_prefix": "service_stop_button",
                "on_click": apply_selected_service_action,
                "disabled": lambda row, _index: service_is_down(row),
                "args": lambda row, _index: ("stop", row["Name"]),
            },
            {
                "label": "Restart",
                "key_prefix": "service_restart_button",
                "on_click": apply_selected_service_action,
                "args": lambda row, _index: ("restart", row["Name"]),
            },
        ],
        action_column_weights=[1, 1, 1],
    )
    if selected_row is None:
        return


def render_envs_table() -> None:
    """Render environment variables using __hhs_envs."""

    def render_env_controls() -> tuple[str, str]:
        """Render environment table controls and return the selected filter."""
        render_env_add_controls()
        return render_table_filter_controls(
            hhs_ui.ENV_FILTERS,
            "env_filter",
            "env_other_filter",
            hhs_ui.THREE_OPTION_FILTER_COLUMNS,
            index=1,
        )

    env_filter, other_filter = render_table_controls_panel(render_env_controls)

    result = render_cached_command_result(
        build_hhs_envs_command(env_filter_pattern(env_filter, other_filter)),
        "Loading environment variables",
        "env",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load environment variables.",
    )
    if result is None:
        return
    rows = (
        parse_rows_cached("env", result.stdout, parse_hhs_envs)
        if result.returncode == 0
        else []
    )
    render_env_rows(rows)


def render_paths_table() -> None:
    """Render PATH entries using __hhs_paths."""

    def render_path_controls() -> tuple[str, str]:
        """Render PATH table controls and return the selected filter."""
        render_path_add_controls()
        return render_table_filter_controls(
            hhs_ui.PATH_FILTERS,
            "path_filter",
            "path_other_filter",
            hhs_ui.PATH_FILTER_COLUMNS,
        )

    path_filter, other_filter = render_table_controls_panel(render_path_controls)
    result = render_cached_command_result(
        build_hhs_paths_command(),
        "Loading PATH entries",
        "path",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load PATH entries.",
    )
    if result is None:
        return
    rows = (
        parse_rows_cached("path", result.stdout, parse_hhs_paths)
        if result.returncode == 0
        else []
    )
    render_path_rows(filter_path_rows(rows, path_filter, other_filter))


def render_dirs_table() -> None:
    """Render saved directories using __hhs_load_dir."""

    def render_dir_controls() -> tuple[str, str]:
        """Render saved directory table controls and return the selected filter."""
        render_dir_add_controls()
        return render_table_filter_controls(
            hhs_ui.LIST_FILTERS,
            "dirs_filter",
            "dirs_other_filter",
            hhs_ui.TWO_OPTION_FILTER_COLUMNS,
        )

    dirs_filter, other_filter = render_table_controls_panel(render_dir_controls)
    result = render_cached_command_result(
        build_hhs_dirs_command(),
        "Loading saved directories",
        "dirs",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load saved directories.",
    )
    if result is None:
        return
    rows = (
        parse_rows_cached("dirs", result.stdout, parse_hhs_dirs)
        if result.returncode == 0
        else []
    )
    render_dir_rows(
        filter_rows_by_text(rows, dirs_filter, other_filter),
    )


def render_cmds_table() -> None:
    """Render saved commands using __hhs_command."""

    def render_cmd_controls() -> tuple[str, str]:
        """Render saved command table controls and return the selected filter."""
        render_cmd_add_controls()
        return render_table_filter_controls(
            hhs_ui.LIST_FILTERS,
            "cmds_filter",
            "cmds_other_filter",
            hhs_ui.TWO_OPTION_FILTER_COLUMNS,
        )

    cmds_filter, other_filter = render_table_controls_panel(render_cmd_controls)
    result = render_cached_command_result(
        build_hhs_commands_command(),
        "Loading saved commands",
        "cmds",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load saved commands.",
    )
    if result is None:
        return
    rows = (
        parse_rows_cached("cmds", result.stdout, parse_hhs_commands)
        if result.returncode == 0
        else []
    )
    render_cmd_rows(
        filter_rows_by_text(rows, cmds_filter, other_filter),
    )


def render_aliases_table() -> None:
    """Render custom aliases using __hhs_aliases."""
    complete_aliases_list_refresh()

    def render_alias_controls() -> tuple[str, str]:
        """Render alias table controls and return the selected filter."""
        render_alias_add_controls()
        return render_table_filter_controls(
            hhs_ui.LIST_FILTERS,
            "alias_filter",
            "alias_other_filter",
            hhs_ui.TWO_OPTION_FILTER_COLUMNS,
        )

    alias_filter, other_filter = render_table_controls_panel(render_alias_controls)
    result, fresh_cache = cached_aliases_result()
    if not fresh_cache and not background_job_is_running(ALIAS_LIST_JOB):
        start_aliases_list_refresh()
    alias_list_running = background_job_is_running(ALIAS_LIST_JOB)
    render_background_job_status(ALIAS_LIST_JOB)
    if alias_list_running and not fresh_cache:
        return
    if result is None:
        if not alias_list_running:
            render_command_loader("Loading custom aliases...")
        return
    rows = (
        parse_rows_cached("aliases", result.stdout, parse_hhs_aliases)
        if result.returncode == 0
        else []
    )
    render_alias_rows(
        filter_rows_by_text(rows, alias_filter, other_filter),
    )


def render_services_table() -> None:
    """Render HomeSetup services using __hhs_services status output."""
    execute_pending_service_action()
    complete_hhs_services_list_refresh()
    render_background_job_status(SERVICE_ACTION_JOB)
    service_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.SERVICE_FILTERS,
            "service_filter",
            "service_other_filter",
            hhs_ui.FOUR_OPTION_FILTER_COLUMNS,
        )
    )
    result, fresh_cache = cached_hhs_services_result()
    if not fresh_cache and not background_job_is_running(SERVICE_LIST_JOB):
        start_hhs_services_list_refresh()
    service_list_running = background_job_is_running(SERVICE_LIST_JOB)
    render_background_job_status(SERVICE_LIST_JOB)
    if service_list_running and not fresh_cache:
        return
    if result is None:
        service_list_error = str(st.session_state.get("service_list_error", "")).strip()
        if service_list_error:
            st.error(service_list_error)
        elif not service_list_running:
            render_command_loader("Loading services...")
        return
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list services.")
        return
    render_service_rows(
        filter_service_rows(
            parse_rows_cached("services", result.stdout, parse_hhs_services),
            service_filter,
            other_filter,
        )
    )


def render_history_commands_table() -> None:
    """Render shell command history using __hhs_history."""
    history_commands_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.HISTORY_FILTERS,
            "history_commands_filter",
            "history_commands_other_filter",
            hhs_ui.TWO_OPTION_FILTER_COLUMNS,
        )
    )
    result = render_cached_command_result(
        build_hhs_history_command(),
        "Loading command history",
        "history",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to list command history.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list command history.")
        return
    render_read_only_rows(
        filter_rows_by_text(
            parse_rows_cached("history", result.stdout, parse_hhs_history),
            history_commands_filter,
            other_filter,
        ),
        history_command_table_key(),
        selected_value=lambda row, _index: row.get("Value", ""),
    )


def render_history_directories_table() -> None:
    """Render directory history using __hhs_dirs."""
    history_directories_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.HISTORY_FILTERS,
            "history_directories_filter",
            "history_directories_other_filter",
            hhs_ui.TWO_OPTION_FILTER_COLUMNS,
        )
    )
    result = render_cached_command_result(
        build_hhs_history_dirs_command(),
        "Loading directory history",
        "history",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to list directory history.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list directory history.")
        return
    rows = filter_rows_by_text(
        parse_rows_cached("history_dirs", result.stdout, parse_hhs_history_dirs),
        history_directories_filter,
        other_filter,
    )
    if not rows:
        message = strip_ansi(result.stdout).strip() or "No directories recorded yet"
        st.info(message)
        return
    render_read_only_rows(
        rows,
        history_directory_table_key(),
        selected_value=lambda row, _index: row.get("Value", ""),
    )


def render_history_stats_chart() -> None:
    """Render command history stats using __hhs_hist_stats."""
    label_col, input_col, spacer_col = st.columns(
        [0.55, 0.7, 2.75], vertical_alignment="center"
    )
    with label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Top N</span>', unsafe_allow_html=True
        )
    with input_col:
        top_n = st.number_input(
            "Top N",
            min_value=1,
            max_value=100,
            step=1,
            key="history_stats_top_n",
            label_visibility="collapsed",
            on_change=save_ui_state,
        )
    st.markdown(f"##### Top {int(top_n)} most used commands")
    result = render_cached_command_result(
        build_hhs_history_stats_command(int(top_n)),
        "Loading history stats",
        "history",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to list history stats.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to list history stats.")
        return
    rows = sorted(
        parse_rows_cached("history_stats", result.stdout, parse_hhs_history_stats),
        key=lambda row: int(row["Count"]),
        reverse=True,
    )
    if not rows:
        st.caption("No history stats found.")
        return
    render_bar_chart(
        rows,
        x=alt.X("Count:Q", title="Count"),
        y=alt.Y(
            "Command:N",
            sort=alt.SortField(field="Count", order="descending"),
            title="Command",
        ),
        tooltip=[
            alt.Tooltip("Command:N", title="Command"),
            alt.Tooltip("Count:Q", title="Count"),
        ],
    )


def render_monitor_disk_chart() -> None:
    """Render disk usage monitor data using __hhs_du."""
    st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n")
    )
    st.session_state["monitor_disk_top_n_input"] = st.session_state.get(
        "monitor_disk_top_n_input",
        st.session_state["monitor_disk_top_n"],
    )
    (
        dir_label_col,
        dir_input_col,
        top_label_col,
        top_input_col,
        action_col,
    ) = st.columns(
        [0.85, 3.0, 0.55, 0.75, 0.45],
        vertical_alignment="center",
    )
    with dir_label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Directory</span>',
            unsafe_allow_html=True,
        )
    with dir_input_col:
        st.text_input(
            "Directory",
            key="monitor_disk_directory",
            label_visibility="collapsed",
            on_change=save_ui_state,
        )
    with top_label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Top N</span>', unsafe_allow_html=True
        )
    with top_input_col:
        st.number_input(
            "Top N",
            min_value=1,
            max_value=100,
            step=1,
            key="monitor_disk_top_n_input",
            label_visibility="collapsed",
            on_change=handle_monitor_disk_top_n_change,
        )
    with action_col:
        st.button(
            "",
            key="monitor_disk_apply_button",
            help="Apply",
            on_click=apply_monitor_disk_controls,
            width="stretch",
        )
    selected_directory = applied_monitor_disk_directory()
    applied_top_n = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n")
    )
    result = render_cached_command_result(
        build_hhs_disk_usage_command(selected_directory, applied_top_n),
        "Loading disk usage",
        "monitor_disk",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_DISK_TIMEOUT_SECONDS,
        "Unable to load disk usage.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load disk usage."
            )
        )
        return
    rows = sorted(
        parse_rows_cached("disk_usage", result.stdout, parse_hhs_disk_usage),
        key=lambda row: float(row["Bytes"]),
        reverse=True,
    )
    display_directory = monitor_disk_display_directory(selected_directory, result.stdout)
    for row in rows:
        row["Label"] = relative_disk_usage_path(str(row["Path"]), display_directory)
    if not rows:
        st.caption("No disk usage entries found.")
        return
    st.markdown(f"##### Top {applied_top_n} disk usage at `{display_directory}`")
    render_bar_chart(
        rows,
        x=alt.X(
            "Bytes:Q",
            title="Size",
            axis=alt.Axis(
                labelExpr=(
                    "datum.value >= 1099511627776 ? format(datum.value / 1099511627776, '.1f') + ' TB' : "
                    "datum.value >= 1073741824 ? format(datum.value / 1073741824, '.1f') + ' GB' : "
                    "datum.value >= 1048576 ? format(datum.value / 1048576, '.1f') + ' MB' : "
                    "datum.value >= 1024 ? format(datum.value / 1024, '.1f') + ' KB' : "
                    "format(datum.value, '.0f') + ' B'"
                )
            ),
        ),
        y=alt.Y(
            "Label:N",
            sort=alt.SortField(field="Bytes", order="descending"),
            title="Path",
        ),
        tooltip=[
            alt.Tooltip("Label:N", title="Path"),
            alt.Tooltip("Size:N", title="Size"),
        ],
    )


def render_process_monitor_chart(metric: str) -> None:
    """Render a process monitor chart for CPU or MEM usage."""
    job_name = monitor_metric_job_name(metric)
    top_n_key = monitor_process_top_n_state_key(metric)
    top_n_input_key = monitor_process_top_n_input_key(metric)
    st.session_state[top_n_key] = normalized_monitor_top_n(
        st.session_state.get(top_n_key)
    )
    st.session_state[top_n_input_key] = normalized_monitor_top_n(
        st.session_state.get(top_n_input_key, st.session_state[top_n_key])
    )
    complete_monitor_metric_refresh(metric)
    top_label_col, top_input_col, action_col = st.columns(
        [0.55, 0.75, 0.45],
        vertical_alignment="center",
    )
    with top_label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Top N</span>', unsafe_allow_html=True
        )
    with top_input_col:
        st.number_input(
            "Top N",
            min_value=1,
            max_value=100,
            step=1,
            key=top_n_input_key,
            label_visibility="collapsed",
            on_change=handle_monitor_process_top_n_change,
            args=(metric,),
        )
    with action_col:
        refresh_clicked = st.button(
            "",
            key=f"monitor_{metric.lower()}_refresh_button",
            help="Refresh",
            on_click=apply_monitor_process_controls,
            args=(metric,),
            width="stretch",
        )
    applied_top_n = normalized_monitor_process_top_n(metric)
    result, fresh_cache = cached_monitor_metric_result(metric)
    if (refresh_clicked or not fresh_cache) and not background_job_is_running(job_name):
        start_monitor_metric_refresh(metric)
    metric_running = background_job_is_running(job_name)
    render_background_job_status(job_name)
    if metric_running and (refresh_clicked or not fresh_cache):
        return
    if result is None:
        metric_error = str(
            st.session_state.get(f"monitor_{metric.lower()}_error", "")
        ).strip()
        if metric_error:
            st.error(metric_error)
        elif not metric_running:
            render_command_loader(f"Loading {metric.lower()} usage...")
        return
    if result.returncode != 0:
        st.error(
            strip_ansi(
                result.stderr
                or result.stdout
                or f"Unable to load {metric.lower()} usage."
            )
        )
        return
    rows = process_monitor_chart_rows(result.stdout, metric, applied_top_n)
    if not rows:
        if metric == "CPU":
            st.caption("No CPU usage above 0.0% found.")
        else:
            st.caption(f"No {metric.lower()} usage entries found.")
        return
    for row in rows:
        row["Label"] = row["Command"]
    has_byte_values = metric == "MEM" and any(
        re.search(r"[A-Za-z]", str(row["ValueLabel"])) for row in rows
    )
    axis = (
        alt.Axis(
            labelExpr=(
                "datum.value >= 1099511627776 ? format(datum.value / 1099511627776, '.1f') + ' TB' : "
                "datum.value >= 1073741824 ? format(datum.value / 1073741824, '.1f') + ' GB' : "
                "datum.value >= 1048576 ? format(datum.value / 1048576, '.1f') + ' MB' : "
                "datum.value >= 1024 ? format(datum.value / 1024, '.1f') + ' KB' : "
                "format(datum.value, '.0f') + ' B'"
            )
        )
        if has_byte_values
        else alt.Axis(format=".1f")
    )
    title = "Memory" if metric == "MEM" else "CPU"
    unit_suffix = "" if has_byte_values else " %"
    color = "#ffb86c"
    st.markdown(f"##### Top {applied_top_n} {title} processes")
    render_bar_chart(
        rows,
        x=alt.X("Value:Q", title=f"{title}{unit_suffix}", axis=axis),
        y=alt.Y(
            "Label:N",
            sort=alt.SortField(field="Value", order="descending"),
            title="Process",
        ),
        tooltip=[
            alt.Tooltip("Command:N", title="Command"),
            alt.Tooltip("PID:N", title="PID"),
            alt.Tooltip("User:N", title="User"),
            alt.Tooltip("CPU:N", title="CPU"),
            alt.Tooltip("MEM:N", title="MEM"),
        ],
        color=color,
    )


def render_monitor_processes_panel() -> None:
    """Render the HomeSetup process list monitor panel."""
    complete_monitor_process_list_refresh()
    action_message = st.session_state.pop("monitor_process_action_message", "")
    action_succeeded = st.session_state.pop("monitor_process_action_succeeded", None)
    if action_message:
        if action_succeeded:
            st.success(clean_command_status_message(action_message))
        else:
            st.error(clean_command_status_message(action_message))

    def render_process_controls() -> tuple[str, str]:
        """Render process table controls and return the selected filter."""
        return render_table_filter_controls(
            hhs_ui.PROCESS_FILTERS,
            "monitor_process_filter",
            "monitor_process_other_filter",
            hhs_ui.PROCESS_FILTER_COLUMNS,
            placeholder="Type process filter",
        )

    process_filter, other_filter = render_table_controls_panel(render_process_controls)
    result, fresh_cache = cached_monitor_process_list_result()
    if not fresh_cache and not background_job_is_running(MONITOR_PROCESS_LIST_JOB):
        start_monitor_process_list_refresh()
    process_list_running = background_job_is_running(MONITOR_PROCESS_LIST_JOB)
    render_background_job_status(MONITOR_PROCESS_LIST_JOB)
    if process_list_running and not fresh_cache:
        return
    if result is None:
        process_list_error = str(
            st.session_state.get("monitor_process_list_error", "")
        ).strip()
        if process_list_error:
            st.error(process_list_error)
        elif not process_list_running:
            render_command_loader("Loading processes...")
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load processes."
            )
        )
        return
    rows = filter_process_rows(
        parse_rows_cached("process_list", result.stdout, parse_hhs_process_list),
        process_filter,
        other_filter,
    )
    if not rows:
        st.caption("No processes found.")
        return

    _, selected_row = render_table(
        rows,
        key=hhs_ui.PROCESS_TABLE_KEY,
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Command']}",
        action_buttons=[
            {
                "label": "Kill",
                "key_prefix": "monitor_process_kill_button",
                "on_click": apply_selected_process_kill,
                "args": lambda row, _index: (row["Command"],),
            }
        ],
        action_column_weights=[1, 3],
    )
    if selected_row is None:
        return


def render_monitor_logs_panel() -> None:
    """Render the HomeSetup logs monitor panel."""
    log_files = hhs_log_files()
    if not log_files:
        st.caption(f"No .log files found in {hhs_log_dir()}.")
        return
    selected_log = st.session_state.get("monitor_log_file", "")
    if selected_log not in log_files:
        st.session_state["monitor_log_file"] = log_files[0]
    if selected_monitor_log_level() != st.session_state.get("monitor_log_level"):
        st.session_state["monitor_log_level"] = selected_monitor_log_level()

    def render_log_controls() -> tuple[str, str, bool, str, str]:
        """Render log controls and return the selected log viewing options."""
        with st.container(key="monitor_log_controls"):
            (
                label_col,
                input_col,
                level_label_col,
                level_col,
                tail_col,
                clear_col,
            ) = st.columns(
                [0.42, 1.0, 0.52, 1.0, 0.16, 0.16], vertical_alignment="center"
            )
            with label_col:
                st.markdown(
                    '<span class="hhs-inline-form-label">Log file:</span>',
                    unsafe_allow_html=True,
                )
            with input_col:
                selected_log_value = st.selectbox(
                    "Log file:",
                    options=log_files,
                    key="monitor_log_file",
                    label_visibility="collapsed",
                    on_change=save_ui_state,
                )
            with level_label_col:
                st.markdown(
                    '<span class="hhs-inline-form-label">Log level:</span>',
                    unsafe_allow_html=True,
                )
            with level_col:
                selected_level_value = st.selectbox(
                    "Log level:",
                    options=hhs_ui.LOG_LEVELS,
                    key="monitor_log_level",
                    format_func=monitor_log_level_label,
                    label_visibility="collapsed",
                    on_change=save_ui_state,
                )
            with tail_col:
                tail_enabled_value = bool(
                    st.session_state.get("monitor_logs_tail", True)
                )
                st.button(
                    "" if tail_enabled_value else "",
                    key="monitor_logs_tail_button",
                    help=(
                        "Disable tail refresh"
                        if tail_enabled_value
                        else "Enable tail refresh"
                    ),
                    on_click=toggle_monitor_logs_tail,
                    width="stretch",
                )
            with clear_col:
                st.button(
                    "",
                    key="monitor_log_clear_button",
                    help="Clear selected log file",
                    on_click=clear_monitor_log_file,
                    width="stretch",
                )
            selected_filter_value, text_filter_value = render_table_filter_controls(
                hhs_ui.LOG_FILTERS,
                "monitor_log_filter",
                "monitor_log_other_filter",
                hhs_ui.TWO_OPTION_FILTER_COLUMNS,
                other_options=("Containing",),
                placeholder="Type log filter text",
            )
        return (
            str(selected_log_value),
            str(selected_level_value),
            bool(tail_enabled_value),
            str(selected_filter_value),
            str(text_filter_value),
        )

    selected_log, selected_level, tail_enabled, log_filter, log_text_filter = (
        render_table_controls_panel(render_log_controls)
    )
    st.markdown(
        f'<div class="hhs-log-file-title"><code>{html.escape(selected_log)}</code></div>',
        unsafe_allow_html=True,
    )
    if tail_enabled:
        render_monitor_logs_tail(
            selected_log, selected_level, log_filter, log_text_filter
        )
    else:
        render_monitor_logs_once(
            selected_log, selected_level, log_filter, log_text_filter
        )


@st.fragment(run_every="5s")
def render_monitor_logs_tail(
    selected_log: str, selected_level: str, log_filter: str, log_text_filter: str
) -> None:
    """Render a tail-like log pane that refreshes only while LOGS is active."""
    render_monitor_logs_once(selected_log, selected_level, log_filter, log_text_filter)


def render_monitor_logs_once(
    selected_log: str,
    selected_level: str,
    log_filter: str = "All",
    log_text_filter: str = "",
) -> None:
    """Render the selected log once without automatic refresh."""
    if False:
        run_hhs_logs(selected_log, 200, selected_level)
    result = render_cached_command_result(
        build_hhs_logs_command(selected_log, 200, selected_level),
        "Loading logs",
        "monitor_logs",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load logs.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load logs."
            )
        )
        return
    render_terminal_output(
        rendered_log_output_cached(result.stdout, log_filter, log_text_filter),
        css_classes="hhs-log-output",
        content_is_html=True,
    )


def config_view_label(config_view: str) -> str:
    """Return the display label for a configuration view key."""
    return hhs_ui.CONFIG_VIEW_LABELS.get(config_view, config_view)


def render_configs_view() -> None:
    """Render the draft configurations view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> Dotfiles Configurations</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    config_view = st.segmented_control(
        "Configuration view",
        options=hhs_ui.CONFIG_VIEWS,
        default=st.session_state["config_view"],
        format_func=config_view_label,
        key="config_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    if config_view == "ENV":
        render_envs_table()
    elif config_view == "PATH":
        render_paths_table()
    elif config_view == "DIR":
        render_dirs_table()
    elif config_view == "CMD":
        render_cmds_table()
    elif config_view == "ALIAS":
        render_aliases_table()


def render_service_view() -> None:
    """Render the HomeSetup services view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> System Services</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_services_table()


def monitor_view_label(monitor_view: str) -> str:
    """Return the display label for a Monitor view key."""
    return hhs_ui.MONITOR_VIEW_LABELS.get(monitor_view, monitor_view)


def ssh_view_label(ssh_view: str) -> str:
    """Return the display label for an SSH subview key."""
    return hhs_ui.SSH_VIEW_LABELS.get(ssh_view, ssh_view)


def render_ssh_tunnels_panel(host: str) -> None:
    """Render the SSH tunnel and port-forward panel."""
    result = render_cached_command_result(
        build_ssh_tunnels_command(host),
        "Loading SSH tunnels",
        "ssh",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load SSH tunnels.",
        force_local=True,
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(result.stderr or "Unable to load SSH tunnels.")
        return
    rows, status_job_names = annotate_ssh_tunnel_statuses(
        parse_ssh_tunnels(result.stdout, host)
    )
    if status_job_names:
        render_ssh_tunnel_status_loader(status_job_names)
    tunnel_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.SSH_TUNNEL_FILTERS,
            "ssh_tunnel_filter",
            "ssh_tunnel_other_filter",
            hhs_ui.THREE_OPTION_FILTER_COLUMNS,
            placeholder="Type tunnel filter",
        )
    )
    rows = filter_ssh_tunnel_rows(rows, tunnel_filter, other_filter)
    headers = ["Local Port", "Remote Host:Port", "Kind", "Status", "Link"]
    render_table(
        rows,
        key=hhs_ui.SSH_TUNNEL_TABLE_KEY,
        headers=headers,
        checkbox=False,
        height=hhs_ui.ENV_TABLE_HEIGHT,
        table_data=(
            styled_ssh_tunnel_rows(rows) if rows else pd.DataFrame(columns=headers)
        ),
        column_config={
            "Link": st.column_config.LinkColumn(
                "Link",
                display_text=r"http://(127\.0\.0\.1:\d+)",
            )
        },
    )
    if not rows:
        st.caption("No active SSH tunnels or port forwards were found.")


def ssh_explorer_mtime_text(epoch_text: str) -> str:
    """Return a compact display timestamp from a Unix epoch string."""
    try:
        epoch = int(float(epoch_text))
    except (TypeError, ValueError):
        return ""
    if epoch <= 0:
        return ""
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


def ssh_explorer_size_text(size_text: str, kind: str) -> str:
    """Return a compact file size label for explorer rows."""
    if kind == "Dir":
        return "--"
    try:
        size = float(size_text)
    except (TypeError, ValueError):
        return ""
    units = ("B", "KB", "MB", "GB", "TB")
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def ssh_explorer_kind_label(kind: str) -> str:
    """Return the visible kind label for one explorer entry."""
    return "" if kind == "Dir" else ""


def ssh_explorer_entry_is_visible(name: str) -> bool:
    """Return whether an explorer entry name should be visible."""
    return bool(name) and name not in {".", ".."} and not name.startswith(".")


def ssh_explorer_row_style(row: pd.Series) -> list[str]:
    """Return dataframe row styles for SSH explorer file and folder entries."""
    if str(row.get("_kind", "")) == "Dir":
        return ["color: #38bdf8; font-weight: 800;"] * len(row)
    return ["color: #ffffff;"] * len(row)


def ssh_explorer_row(
    kind: str, name: str, size: str, modified: str, path: str
) -> dict[str, str]:
    """Return a normalized explorer row."""
    glyph = ssh_explorer_kind_label(kind)
    return {
        "Name": f"{glyph} {name}",
        "Size": ssh_explorer_size_text(size, kind),
        "Modified": ssh_explorer_mtime_text(modified),
        "Path": path,
        "_name": name,
        "_kind": kind,
    }


def ssh_explorer_sort_key(row: dict[str, str]) -> tuple[int, str]:
    """Return the folders-first alphabetical sort key for explorer rows."""
    kind_order = 0 if str(row.get("_kind", "")) == "Dir" else 1
    return (kind_order, str(row.get("_name", "")).casefold())


def local_explorer_directory(path_value: str) -> Path:
    """Return a usable local explorer directory."""
    path = Path(path_value or os.getcwd()).expanduser()
    if path.is_file():
        return path.parent.resolve()
    if path.is_dir():
        return path.resolve()
    return Path.home().resolve()


def local_explorer_rows(path_value: str) -> list[dict[str, str]]:
    """Return local filesystem entries for the explorer."""
    directory = local_explorer_directory(path_value)
    rows = []
    try:
        entries = list(directory.iterdir())
    except OSError as error:
        push_floating_status(f"Unable to list local files: {error}", "error")
        return rows
    for entry in entries:
        if not ssh_explorer_entry_is_visible(entry.name):
            continue
        try:
            stat_result = entry.stat()
        except OSError:
            continue
        kind = "Dir" if entry.is_dir() else "File"
        rows.append(
            ssh_explorer_row(
                kind,
                entry.name,
                str(stat_result.st_size),
                str(int(stat_result.st_mtime)),
                str(entry),
            )
        )
    return sorted(rows, key=ssh_explorer_sort_key)


def normalize_local_explorer_path(path_value: str, base_path: str | None = None) -> str:
    """Return an absolute local explorer path from a possibly relative path."""
    raw_path = str(path_value or ".").strip() or "."
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return str(path.resolve())
    base_directory = local_explorer_directory(base_path or os.getcwd())
    return str((base_directory / path).resolve())


def normalize_remote_explorer_path(path_value: str, base_path: str | None = None) -> str:
    """Return a normalized remote explorer path from a possibly relative path."""
    raw_path = str(path_value or ".").strip() or "."
    if raw_path.startswith("/") or raw_path.startswith("~"):
        return posixpath.normpath(raw_path)
    normalized_base = str(base_path or ".").strip() or "."
    if normalized_base.startswith("/"):
        return posixpath.normpath(posixpath.join(normalized_base, raw_path))
    return posixpath.normpath(raw_path)


def ssh_explorer_local_default_path() -> str:
    """Return the default local explorer directory path."""
    return str(Path.home().resolve())


def ssh_explorer_remote_default_path() -> str:
    """Return the default remote explorer directory path."""
    return "~"


def create_local_explorer_folder(local_path: str) -> None:
    """Create the requested local explorer folder path and parent folders."""
    folder_path = Path(normalize_local_explorer_path(local_path))
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        push_floating_status(f"Unable to create local folder: {error}", "error")
        return
    open_local_explorer_path(str(folder_path))
    created_name = folder_path.name or str(folder_path)
    push_floating_status(f"Folder created on local {created_name}", "info")


def remote_explorer_target_assignment(remote_path: str) -> str:
    """Return shell lines that resolve an explorer path into target."""
    safe_path = shlex.quote(remote_path.strip() or ssh_explorer_remote_default_path())
    return textwrap.dedent(
        f"""
        raw_target={safe_path}
        case "${{raw_target}}" in
          "~") target=${{HOME:-.}} ;;
          "~/"*) target="${{HOME:-.}}/${{raw_target#*/}}" ;;
          *) target="${{raw_target}}" ;;
        esac
        [ -n "${{target}}" ] || target=.
        """
    ).strip()


def build_remote_explorer_listing_command(remote_path: str) -> str:
    """Build a portable remote shell command that lists one directory."""
    return textwrap.dedent(
        f"""
        {remote_explorer_target_assignment(remote_path)}
        if [ ! -d "${{target}}" ]; then
          target=${{HOME:-.}}
        fi
        if [ ! -d "${{target}}" ]; then
          target=.
        fi
        abs_dir=$(cd "${{target}}" && pwd -P) || {{
          printf '__HHS_CWD__\\t%s\\n' .
          exit 0
        }}
        file_row='__HHS_FILE__\\t%s\\t%s\\t%s\\t%s\\t%s\\n'
        printf '__HHS_CWD__\\t%s\\n' "${{abs_dir}}"
        for entry in "${{abs_dir}}"/*; do
          [ -e "${{entry}}" ] || continue
          name=${{entry##*/}}
          case "${{name}}" in .*|"."|"..") continue ;; esac
          if [ -d "${{entry}}" ]; then
            kind=Dir
          else
            kind=File
          fi
          if stat -c %s "${{entry}}" >/dev/null 2>&1; then
            size=$(stat -c %s "${{entry}}" 2>/dev/null || printf '0')
            modified=$(stat -c %Y "${{entry}}" 2>/dev/null || printf '0')
          else
            size=$(stat -f %z "${{entry}}" 2>/dev/null || printf '0')
            modified=$(stat -f %m "${{entry}}" 2>/dev/null || printf '0')
          fi
          printf "${{file_row}}" "${{kind}}" "${{name}}" "${{size}}" "${{modified}}" "${{entry}}"
        done
        """
    ).strip()


def build_remote_explorer_create_folder_command(remote_path: str) -> str:
    """Build a remote shell command that creates the requested folder path."""
    return textwrap.dedent(
        f"""
        {remote_explorer_target_assignment(remote_path)}
        mkdir -p "${{target}}" || exit 1
        abs_dir=$(cd "${{target}}" && pwd -P) || exit 1
        printf '__HHS_CREATED_DIR__\\t%s\\n' "${{abs_dir}}"
        """
    ).strip()


def parse_remote_explorer_created_dir(output: str) -> str:
    """Parse the created remote explorer folder path from command output."""
    for line in strip_ansi(output).splitlines():
        if line.startswith("__HHS_CREATED_DIR__\t"):
            return line.split("\t", 1)[1].strip()
    return ""


def parse_remote_explorer_rows(output: str) -> list[dict[str, str]]:
    """Parse remote explorer command output into table rows."""
    rows = []
    for line in strip_ansi(output).splitlines():
        if not line.startswith("__HHS_FILE__\t"):
            continue
        parts = line.split("\t", 5)
        if len(parts) != 6:
            continue
        _marker, kind, name, size, modified, path = parts
        if not ssh_explorer_entry_is_visible(name):
            continue
        rows.append(ssh_explorer_row(kind, name, size, modified, path))
    return sorted(rows, key=ssh_explorer_sort_key)


def parse_remote_explorer_cwd(output: str) -> str:
    """Parse the resolved remote explorer directory from command output."""
    for line in strip_ansi(output).splitlines():
        if line.startswith("__HHS_CWD__\t"):
            return line.split("\t", 1)[1].strip()
    return ""


def set_remote_footer_working_directory(path: str) -> None:
    """Store the SSH footer working directory from remote explorer navigation."""
    clean_path = str(path or "").strip()
    if clean_path:
        st.session_state[hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY] = clean_path


def remote_explorer_rows(remote_path: str) -> list[dict[str, str]] | None:
    """Return remote filesystem entries, or None while loading."""
    result = render_cached_command_result(
        build_remote_explorer_listing_command(remote_path),
        "Loading remote files",
        "ssh_files",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to list remote files.",
    )
    if result is None:
        return None
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to list remote files.")
        return []
    resolved_remote_path = parse_remote_explorer_cwd(result.stdout)
    if resolved_remote_path:
        st.session_state["ssh_explorer_remote_path"] = resolved_remote_path
        set_remote_footer_working_directory(resolved_remote_path)
    return parse_remote_explorer_rows(result.stdout)


def open_local_explorer_path(path: str, base_path: str | None = None) -> None:
    """Open a local explorer directory."""
    normalized_path = normalize_local_explorer_path(path, base_path)
    st.session_state["ssh_explorer_local_path"] = str(
        local_explorer_directory(normalized_path)
    )
    save_ui_state()


def open_remote_explorer_path(path: str, base_path: str | None = None) -> None:
    """Open a remote explorer directory."""
    normalized_path = normalize_remote_explorer_path(path, base_path)
    st.session_state["ssh_explorer_remote_path"] = normalized_path
    set_remote_footer_working_directory(normalized_path)
    cache_delete_tag("ssh_files")
    save_ui_state()


def refresh_ssh_explorer_paths(
    local_path: str,
    local_base_path: str,
    remote_path: str,
    remote_base_path: str,
) -> None:
    """Refresh both local and remote explorer listings at their current paths."""
    normalized_local_path = normalize_local_explorer_path(local_path, local_base_path)
    st.session_state["ssh_explorer_local_path"] = str(
        local_explorer_directory(normalized_local_path)
    )
    normalized_remote_path = normalize_remote_explorer_path(
        remote_path,
        remote_base_path,
    )
    st.session_state["ssh_explorer_remote_path"] = normalized_remote_path
    set_remote_footer_working_directory(normalized_remote_path)
    cache_delete_tag("ssh_files")
    save_ui_state()


def remote_explorer_parent_path(path: str) -> str:
    """Return a POSIX parent directory path for the remote explorer."""
    clean_path = path.strip() or "."
    normalized_path = posixpath.normpath(clean_path)
    if normalized_path == "/":
        return "/"
    parent_path = posixpath.dirname(normalized_path)
    if parent_path:
        return parent_path
    if normalized_path in {"", "."}:
        return ".."
    return "."


def open_ssh_explorer_parent(panel: str, local_path: str, remote_path: str) -> None:
    """Open the parent directory for one SSH explorer panel."""
    if panel == "remote":
        open_remote_explorer_path(remote_explorer_parent_path(remote_path))
    else:
        open_local_explorer_path(str(local_explorer_directory(local_path).parent))


def open_ssh_explorer_selection(panel: str, path: str) -> None:
    """Open the selected SSH explorer row on the given panel."""
    if panel == "local":
        open_local_explorer_path(path)
    elif panel == "remote":
        open_remote_explorer_path(path)


def create_remote_explorer_folder(remote_path: str) -> None:
    """Create the requested remote explorer folder path and parent folders."""
    result = run_bash_command(
        build_remote_explorer_create_folder_command(remote_path),
        "Creating remote folder",
        use_cache=False,
        cache_tag="ssh_files",
    )
    if result.returncode != 0:
        push_floating_status(
            strip_ansi(result.stderr or result.stdout or "Unable to create folder."),
            "error",
        )
        return
    created_dir = parse_remote_explorer_created_dir(result.stdout)
    created_path = created_dir or remote_path
    created_name = posixpath.basename(created_path) or created_path
    open_remote_explorer_path(created_path)
    push_floating_status(f"Folder created on remote {created_name}", "info")


def create_ssh_explorer_folder(panel: str, local_path: str, remote_path: str) -> None:
    """Create a new folder in the active SSH explorer panel."""
    if panel == "remote":
        create_remote_explorer_folder(remote_path)
    else:
        create_local_explorer_folder(local_path)


def resolve_css_custom_property(
    properties: dict[str, str], property_name: str, fallback: str
) -> str:
    """Return a CSS custom property value with simple var references resolved."""
    value = properties.get(property_name, fallback).strip()
    visited = {property_name}
    while value.startswith("var(--") and value.endswith(")"):
        referenced_name = value[6:-1].strip()
        if "," in referenced_name:
            referenced_name, fallback_value = referenced_name.split(",", 1)
            fallback = fallback_value.strip()
        if referenced_name in visited:
            return fallback
        visited.add(referenced_name)
        value = properties.get(referenced_name, fallback).strip()
    return value or fallback


def ssh_explorer_component_theme() -> dict[str, str]:
    """Return CSS color tokens for the SSH explorer component iframe."""
    theme_name = st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    properties = theme_custom_properties(theme_name)
    return {
        "background": resolve_css_custom_property(
            properties, "hhs-background", "#19181f"
        ),
        "field": resolve_css_custom_property(
            properties, "hhs-theme-secondary-background-color", "#221f2b"
        ),
        "file": resolve_css_custom_property(
            properties, "hhs-theme-text-color", "#fcfcfa"
        ),
        "folder": resolve_css_custom_property(
            properties, "hhs-theme-link-color", "#78dce8"
        ),
        "border": resolve_css_custom_property(
            properties, "hhs-theme-dataframe-border-color", "#6c5f91"
        ),
        "primary": resolve_css_custom_property(
            properties, "hhs-theme-primary-color", "#bd93f9"
        ),
    }


def ssh_explorer_remote_spec(host: str, path: str) -> str:
    """Return an scp remote path spec for the active host and path."""
    return f"{shlex.quote(host)}:{shlex.quote(path)}"


def shell_array_assignment(name: str, values: list[str]) -> str:
    """Return a Bash array assignment for quoted string values."""
    quoted_values = " ".join(shlex.quote(value) for value in values if value)
    return f"{name}=({quoted_values})"


def build_scp_to_remote_command(
    local_paths: str | list[str], remote_dir: str, host: str
) -> str:
    """Build an scp command that copies local paths into the remote directory."""
    safe_control_path = shlex.quote(ssh_control_path(host))
    paths = [local_paths] if isinstance(local_paths, str) else local_paths
    quoted_paths = " ".join(shlex.quote(path) for path in paths if path)
    return (
        f"scp -r {ssh_config_option()} -o ControlPath={safe_control_path} -- "
        f"{quoted_paths} {ssh_explorer_remote_spec(host, remote_dir)}"
    )


def build_scp_to_local_command(
    remote_paths: str | list[str], local_dir: str, host: str
) -> str:
    """Build an scp command that copies remote paths into the local directory."""
    safe_control_path = shlex.quote(ssh_control_path(host))
    paths = [remote_paths] if isinstance(remote_paths, str) else remote_paths
    remote_specs = " ".join(
        ssh_explorer_remote_spec(host, path) for path in paths if path
    )
    return (
        f"scp -r {ssh_config_option()} -o ControlPath={safe_control_path} -- "
        f"{remote_specs} {shlex.quote(local_dir)}"
    )


def build_recoverable_delete_command(paths: list[str]) -> str:
    """Build a command that moves paths to a recoverable trash location."""
    return textwrap.dedent(
        f"""
        {shell_array_assignment("targets", paths)}
        if [ "${{#targets[@]}}" -eq 0 ]; then
          printf '%s\\n' 'No files selected.'
          exit 1
        fi
        trash_with_freedesktop() {{
          trash_home="${{XDG_DATA_HOME:-${{HOME}}/.local/share}}/Trash"
          files_dir="${{trash_home}}/files"
          info_dir="${{trash_home}}/info"
          mkdir -p "${{files_dir}}" "${{info_dir}}" || return 1
          for target in "$@"; do
            [ -e "${{target}}" ] || [ -L "${{target}}" ] || {{
              printf 'Path does not exist: %s\\n' "${{target}}" >&2
              return 1
            }}
            base=$(basename -- "${{target}}")
            destination="${{files_dir}}/${{base}}"
            suffix=0
            while [ -e "${{destination}}" ] || [ -L "${{destination}}" ]; do
              suffix=$((suffix + 1))
              destination="${{files_dir}}/${{base}}.${{suffix}}"
            done
            escaped_path=$(printf '%s' "${{target}}" | sed 's/%/%25/g; s/#/%23/g; s/ /%20/g')
            deletion_date=$(date '+%Y-%m-%dT%H:%M:%S')
            mv -- "${{target}}" "${{destination}}" || return 1
            {{
              printf '[Trash Info]\\n'
              printf 'Path=%s\\n' "${{escaped_path}}"
              printf 'DeletionDate=%s\\n' "${{deletion_date}}"
            }} > "${{info_dir}}/$(basename -- "${{destination}}").trashinfo"
          done
        }}
        if command -v gtrash >/dev/null 2>&1; then
          gtrash put -- "${{targets[@]}}" || gtrash -- "${{targets[@]}}"
        elif command -v trash-put >/dev/null 2>&1; then
          trash-put -- "${{targets[@]}}"
        elif command -v gio >/dev/null 2>&1; then
          gio trash "${{targets[@]}}"
        elif command -v kioclient5 >/dev/null 2>&1; then
          kioclient5 move "${{targets[@]}}" trash:/
        elif command -v kioclient >/dev/null 2>&1; then
          kioclient move "${{targets[@]}}" trash:/
        elif [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
          mkdir -p "${{HOME}}/.Trash" || exit 1
          for target in "${{targets[@]}}"; do
            [ -e "${{target}}" ] || [ -L "${{target}}" ] || {{
              printf 'Path does not exist: %s\\n' "${{target}}" >&2
              exit 1
            }}
            base=$(basename -- "${{target}}")
            destination="${{HOME}}/.Trash/${{base}}"
            suffix=0
            while [ -e "${{destination}}" ] || [ -L "${{destination}}" ]; do
              suffix=$((suffix + 1))
              destination="${{HOME}}/.Trash/${{base}}.${{suffix}}"
            done
            mv -- "${{target}}" "${{destination}}" || exit 1
          done
        else
          trash_with_freedesktop "${{targets[@]}}"
        fi
        """
    ).strip()


def start_ssh_explorer_transfer(command: str, description: str) -> None:
    """Start a background explorer file transfer."""
    if background_job_is_running(SSH_FILE_TRANSFER_JOB):
        push_floating_status("A file transfer is already running.", "warn")
        return
    started = start_background_bash_command(
        SSH_FILE_TRANSFER_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_REMOTE_TIMEOUT_SECONDS,
        force_local=True,
    )
    if not started:
        push_floating_status("A file transfer is already running.", "warn")


def copy_local_selection_to_remote(local_paths: list[str], remote_dir: str) -> None:
    """Copy the selected local paths into the current remote directory."""
    if not local_paths:
        push_floating_status("Select local files before copying.", "warn")
        return
    host = connected_ssh_host()
    if not host:
        push_floating_status("Connect to SSH before copying files.", "warn")
        return
    start_ssh_explorer_transfer(
        build_scp_to_remote_command(local_paths, remote_dir, host),
        "Copying local file(s)/folder(s) to remote",
    )


def copy_remote_selection_to_local(remote_paths: list[str], local_dir: str) -> None:
    """Copy the selected remote paths into the current local directory."""
    if not remote_paths:
        push_floating_status("Select remote files before copying.", "warn")
        return
    host = connected_ssh_host()
    if not host:
        push_floating_status("Connect to SSH before copying files.", "warn")
        return
    start_ssh_explorer_transfer(
        build_scp_to_local_command(remote_paths, local_dir, host),
        "Copying remote file(s)/folder(s) to local",
    )


def ssh_explorer_delete_name(panel: str, path: str) -> str:
    """Return a display name for one SSH explorer delete target."""
    if panel == "remote":
        return posixpath.basename(path.rstrip("/")) or path
    return Path(path).name or path


def ssh_explorer_delete_message(panel: str, paths: list[str]) -> str:
    """Return the confirmation message for selected explorer delete targets."""
    names = [
        ssh_explorer_delete_name(panel, path)
        for path in paths
        if str(path).strip()
    ]
    target_names = ", ".join(names) if names else "selected item(s)"
    return f"Are you sure you want to delete {target_names}?"


def request_ssh_explorer_delete_confirmation(
    panel: str,
    paths: list[str],
    local_path: str,
    remote_path: str,
) -> None:
    """Show the SSH explorer delete confirmation dialog."""
    if panel not in {"local", "remote"} or not paths:
        push_floating_status("Select files or folders before deleting.", "warn")
        return
    st.session_state["ssh_explorer_delete_pending"] = {
        "panel": panel,
        "paths": paths,
        "local_path": local_path,
        "remote_path": remote_path,
    }


def cancel_ssh_explorer_delete_confirmation() -> None:
    """Hide the SSH explorer delete confirmation dialog."""
    st.session_state["ssh_explorer_delete_pending"] = None


def confirm_ssh_explorer_delete() -> None:
    """Execute the pending SSH explorer delete request."""
    pending = st.session_state.get("ssh_explorer_delete_pending")
    st.session_state["ssh_explorer_delete_pending"] = None
    if not isinstance(pending, dict):
        return
    panel = str(pending.get("panel", ""))
    paths_value = pending.get("paths", [])
    paths = paths_value if isinstance(paths_value, list) else []
    clean_paths = [str(path) for path in paths if str(path).strip()]
    if panel not in {"local", "remote"} or not clean_paths:
        push_floating_status("Select files or folders before deleting.", "warn")
        return
    result = run_bash_command(
        build_recoverable_delete_command(clean_paths),
        "Deleting selected file(s)/folder(s)",
        ttl_seconds=0,
        use_cache=False,
        force_local=panel == "local",
        cache_tag="ssh_files",
    )
    if result.returncode != 0:
        push_floating_status(
            strip_ansi(result.stderr or result.stdout or "Unable to delete selection."),
            "error",
        )
        return
    cache_delete_tag("ssh_files")
    push_floating_status("Deleted selected file(s)/folder(s).", "info")


def render_ssh_explorer_delete_dialog() -> bool:
    """Render the SSH explorer delete confirmation dialog when pending."""
    pending = st.session_state.get("ssh_explorer_delete_pending")
    if not isinstance(pending, dict):
        return False
    panel = str(pending.get("panel", ""))
    paths_value = pending.get("paths", [])
    paths = paths_value if isinstance(paths_value, list) else []
    return pop_dialog(
        title="Confirm delete",
        message=ssh_explorer_delete_message(panel, [str(path) for path in paths]),
        confirm_key="ssh_explorer_confirm_delete_button",
        cancel_key="ssh_explorer_cancel_delete_button",
        on_confirm=confirm_ssh_explorer_delete,
        on_cancel=cancel_ssh_explorer_delete_confirmation,
        confirm_label="Delete",
    )


def complete_ssh_explorer_transfer() -> None:
    """Complete a background explorer file transfer and refresh listings."""
    completed = background_job_result(SSH_FILE_TRANSFER_JOB)
    if completed is None:
        return
    result, _metadata = completed
    if result.returncode == 0:
        cache_delete_tag("ssh_files")
        push_floating_status("File transfer completed.", "info")
    else:
        push_floating_status(
            strip_ansi(result.stderr or result.stdout or "File transfer failed."),
            "error",
        )


@lru_cache(maxsize=1)
def ssh_explorer_component() -> Callable[..., dict[str, object] | None]:
    """Return the registered SSH explorer Streamlit component."""
    return components.declare_component(
        "hhs_ssh_explorer",
        path=str(hhs_ui.SSH_EXPLORER_COMPONENT_DIR),
    )


def ssh_explorer_component_event_text(
    event: dict[str, object], key: str, default: str = ""
) -> str:
    """Return a string value from an SSH explorer component event."""
    value = event.get(key, default)
    if value is None:
        return default
    return str(value)


def ssh_explorer_component_event_paths(event: dict[str, object]) -> list[str]:
    """Return selected path values from an SSH explorer component event."""
    paths = event.get("paths", [])
    if not isinstance(paths, list):
        paths = []
    values = [str(path) for path in paths if str(path).strip()]
    if values:
        return values
    path = ssh_explorer_component_event_text(event, "path")
    return [path] if path else []


def handle_ssh_explorer_component_event(event: object) -> bool:
    """Handle one SSH explorer component command event."""
    if not isinstance(event, dict):
        return False
    event_id = ssh_explorer_component_event_text(event, "eventId")
    if not event_id:
        return False
    if st.session_state.get("ssh_explorer_component_last_event_id") == event_id:
        return False
    st.session_state["ssh_explorer_component_last_event_id"] = event_id

    action = ssh_explorer_component_event_text(event, "action")
    panel = ssh_explorer_component_event_text(event, "panel")
    path = ssh_explorer_component_event_text(event, "path")
    paths = ssh_explorer_component_event_paths(event)
    local_path = ssh_explorer_component_event_text(
        event,
        "localPath",
        str(
            st.session_state.get(
                "ssh_explorer_local_path", ssh_explorer_local_default_path()
            )
        ),
    )
    remote_path = ssh_explorer_component_event_text(
        event,
        "remotePath",
        str(
            st.session_state.get(
                "ssh_explorer_remote_path", ssh_explorer_remote_default_path()
            )
        ),
    )
    local_base_path = ssh_explorer_component_event_text(
        event,
        "localBasePath",
        str(
            st.session_state.get(
                "ssh_explorer_local_path", ssh_explorer_local_default_path()
            )
        ),
    )
    remote_base_path = ssh_explorer_component_event_text(
        event,
        "remoteBasePath",
        str(
            st.session_state.get(
                "ssh_explorer_remote_path", ssh_explorer_remote_default_path()
            )
        ),
    )
    normalized_local_path = normalize_local_explorer_path(local_path, local_base_path)
    normalized_remote_path = normalize_remote_explorer_path(
        remote_path, remote_base_path
    )

    if action == "parent":
        open_ssh_explorer_parent(panel, normalized_local_path, normalized_remote_path)
        return True
    if action == "create_folder":
        create_ssh_explorer_folder(panel, normalized_local_path, normalized_remote_path)
        return True
    if action == "open":
        open_ssh_explorer_selection(panel, path)
        return True
    if action == "refresh":
        refresh_ssh_explorer_paths(
            local_path,
            local_base_path,
            remote_path,
            remote_base_path,
        )
        return True
    if action == "submit_path" and panel == "local":
        open_local_explorer_path(local_path, local_base_path)
        return True
    if action == "submit_path" and panel == "remote":
        open_remote_explorer_path(remote_path, remote_base_path)
        return True
    if action == "copy_to_remote":
        copy_local_selection_to_remote(paths, normalized_remote_path)
        return True
    if action == "copy_to_local":
        copy_remote_selection_to_local(
            paths, str(local_explorer_directory(normalized_local_path))
        )
        return True
    if action == "delete":
        request_ssh_explorer_delete_confirmation(
            panel,
            paths,
            normalized_local_path,
            normalized_remote_path,
        )
        return True
    return False


def render_ssh_explorer_component(
    local_rows: list[dict[str, str]] | None,
    remote_rows: list[dict[str, str]] | None,
    local_path: str,
    remote_path: str,
    transfer_running: bool,
) -> dict[str, object] | None:
    """Render the SSH explorer component and return its command event."""
    component = ssh_explorer_component()
    component_height = table_height(hhs_ui.ENV_TABLE_HEIGHT)
    local_loading = local_rows is None
    remote_loading = remote_rows is None
    explorer_loading = local_loading or remote_loading
    return component(
        localRows=local_rows or [],
        remoteRows=remote_rows or [],
        localPath=local_path,
        remotePath=remote_path,
        loading=explorer_loading,
        localLoading=local_loading,
        remoteLoading=remote_loading,
        selectionHint=False,
        tableHeight=table_height(hhs_ui.ENV_TABLE_HEIGHT),
        theme=ssh_explorer_component_theme(),
        transferRunning=transfer_running,
        height=component_height,
        key="ssh_explorer_component",
        default=None,
    )


def render_ssh_files_panel() -> None:
    """Render a three-column local/remote file explorer using scp transfers."""
    complete_ssh_explorer_transfer()
    render_ssh_explorer_delete_dialog()
    st.session_state.setdefault(
        "ssh_explorer_local_path", ssh_explorer_local_default_path()
    )
    st.session_state.setdefault(
        "ssh_explorer_remote_path", ssh_explorer_remote_default_path()
    )
    local_path = str(
        st.session_state.get(
            "ssh_explorer_local_path", ssh_explorer_local_default_path()
        )
    )
    remote_path = str(
        st.session_state.get(
            "ssh_explorer_remote_path", ssh_explorer_remote_default_path()
        )
    )
    resolved_local_path = str(local_explorer_directory(local_path))
    if resolved_local_path != local_path:
        st.session_state["ssh_explorer_local_path"] = resolved_local_path
        local_path = resolved_local_path
    local_rows = local_explorer_rows(local_path)
    remote_rows = remote_explorer_rows(remote_path)
    remote_path = str(st.session_state.get("ssh_explorer_remote_path", remote_path))
    if background_job_is_running(SSH_FILE_TRANSFER_JOB):
        render_background_job_status(SSH_FILE_TRANSFER_JOB)

    transfer_running = background_job_is_running(SSH_FILE_TRANSFER_JOB)
    event = render_ssh_explorer_component(
        local_rows,
        remote_rows,
        local_path,
        remote_path,
        transfer_running,
    )
    if handle_ssh_explorer_component_event(event):
        st.rerun()


def render_ssh_view() -> None:
    """Render the SSH remote connection view."""
    host = connected_ssh_host()
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> Remote Connection</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    ssh_view = st.segmented_control(
        "SSH view",
        options=hhs_ui.SSH_VIEWS,
        default=st.session_state["ssh_view"],
        format_func=ssh_view_label,
        key="ssh_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    if ssh_view == "TUNNELS":
        render_ssh_tunnels_panel(host)
    elif ssh_view == "FILES":
        render_ssh_files_panel()


def history_view_label(history_view: str) -> str:
    """Return the display label for a History view key."""
    return hhs_ui.HISTORY_VIEW_LABELS.get(history_view, history_view)


def render_history_view() -> None:
    """Render the command and directory history view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> History</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    history_view = st.segmented_control(
        "History view",
        options=hhs_ui.HISTORY_VIEWS,
        default=st.session_state["history_view"],
        format_func=history_view_label,
        key="history_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    if history_view == "COMMANDS":
        render_history_commands_table()
    elif history_view == "DIRECTORIES":
        render_history_directories_table()
    elif history_view == "STATS":
        render_history_stats_chart()


def render_monitor_view() -> None:
    """Render the HomeSetup monitor view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> Activity Monitor</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    monitor_view = st.segmented_control(
        "Monitor view",
        options=hhs_ui.MONITOR_VIEWS,
        default=st.session_state["monitor_view"],
        format_func=monitor_view_label,
        key="monitor_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    if monitor_view == "DISK":
        render_monitor_disk_chart()
    elif monitor_view == "MEM":
        render_process_monitor_chart("MEM")
    elif monitor_view == "CPU":
        render_process_monitor_chart("CPU")
    elif monitor_view == "PROCESSES":
        render_monitor_processes_panel()
    elif monitor_view == "LOGS":
        render_monitor_logs_panel()


def search_type_label(search_type: str) -> str:
    """Return the display label for a Search type key."""
    return hhs_ui_constants.SEARCH_TYPE_LABELS.get(search_type, search_type)


def normalized_search_type(search_type: object) -> str:
    """Return a valid Search type key."""
    candidate = str(search_type or "").strip()
    if candidate in hhs_ui_constants.SEARCH_TYPES:
        return candidate
    return hhs_ui_constants.SEARCH_TYPES[0]


def search_glob_from_query(query: str) -> str:
    """Return the file or folder glob used for a Search query."""
    clean_query = query.strip()
    if any(character in clean_query for character in "*?[],"):
        return clean_query
    return f"*{clean_query}*"


def build_hhs_search_setup_command() -> str:
    """Build shell setup for HomeSetup Search helper functions."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-text.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-search.bash"; '
        "function __hhs_highlight() { cat -; }; "
    )


def build_hhs_search_modified_results_command(search_command: str) -> str:
    """Wrap a Search command so path results include metadata columns."""
    return (
        f"{search_command} | while IFS= read -r line; do "
        'case "${line}" in '
        '""|Searching\\ for*) printf "%s\\n" "${line}" ;; '
        '*) '
        'if [ -e "${line}" ]; then '
        'if modified=$(stat -c %Y "${line}" 2>/dev/null); then :; '
        'else modified=$(stat -f %m "${line}" 2>/dev/null || printf "0"); fi; '
        'if [ -f "${line}" ]; then '
        'if size=$(stat -c %s "${line}" 2>/dev/null); then :; '
        'else size=$(stat -f %z "${line}" 2>/dev/null || printf ""); fi; '
        'else size=""; fi; '
        'else modified=0; size=""; fi; '
        'printf "__HHS_SEARCH_RESULT__\\t%s\\t%s\\t%s\\n" "${line}" "${modified}" "${size}" ;; '
        "esac; "
        "done"
    )


def normalized_search_option_values(
    search_type: str,
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
) -> tuple[bool, bool, bool]:
    """Return Search option flags that apply to the selected Search type."""
    if normalized_search_type(search_type) != "Strings":
        return (False, False, False)
    return (bool(ignore_case), bool(words), bool(binary))


def search_string_option_flags(
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
) -> list[str]:
    """Return __hhs_search_string option flags for selected Search toggles."""
    flags: list[str] = []
    if ignore_case:
        flags.append("-i")
    if words:
        flags.append("-w")
    if binary:
        flags.append("-b")
    return flags


def build_hhs_search_command(
    search_type: str,
    query: str,
    search_path: str,
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
) -> str:
    """Build the HomeSetup search command for the selected Search type."""
    setup_command = build_hhs_search_setup_command()
    search_root = shlex.quote(search_path.strip() or ".")
    safe_query = shlex.quote(query.strip())
    if search_type == "Folders":
        safe_glob = shlex.quote(search_glob_from_query(query))
        search_command = f"{setup_command}__hhs_search_dir {search_root} {safe_glob}"
        return build_hhs_search_modified_results_command(search_command)
    if search_type == "Strings":
        option_values = normalized_search_option_values(
            search_type, ignore_case, words, binary
        )
        option_args = " ".join(
            shlex.quote(flag) for flag in search_string_option_flags(*option_values)
        )
        if option_args:
            option_args = f" {option_args}"
        return f"{setup_command}__hhs_search_string {search_root}{option_args} {safe_query}"
    safe_glob = shlex.quote(search_glob_from_query(query))
    search_command = f"{setup_command}__hhs_search_file {search_root} {safe_glob}"
    return build_hhs_search_modified_results_command(search_command)


def search_command_cache_key(
    search_type: str,
    query: str,
    search_path: str,
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
) -> str:
    """Return the tagged MD5 command cache key for one Search execution."""
    option_values = normalized_search_option_values(
        search_type, ignore_case, words, binary
    )
    key_material = "\n".join(
        (
            normalized_search_type(search_type),
            query.strip(),
            search_path.strip(),
            *(str(value) for value in option_values),
        )
    )
    search_hash = hashlib.md5(key_material.encode("utf-8")).hexdigest()
    return f"command_tag:{safe_cache_tag('search')}:{search_hash}"


def build_hhs_open_search_result_command(path: str) -> str:
    """Build the HomeSetup command used to open one Search result path."""
    safe_path = shlex.quote(path.strip())
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_open {safe_path}"
    )


def open_search_result_path(path: str) -> None:
    """Open one Search result path through the HomeSetup generic opener."""
    clean_path = path.strip()
    if not clean_path:
        return
    result = run_bash_command(
        build_hhs_open_search_result_command(clean_path),
        f"Opening {clean_path}",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="search",
    )
    if result.returncode != 0:
        push_floating_status(
            clean_command_status_message(result.stderr or result.stdout),
            "error",
        )


def search_relative_path(path: str, search_path: str) -> str:
    """Return a Search result path relative to the submitted Search folder."""
    clean_path = path.strip()
    clean_search_path = search_path.strip()
    if not clean_path or not clean_search_path:
        return clean_path
    normalized_path = posixpath.normpath(clean_path)
    normalized_search_path = posixpath.normpath(clean_search_path)
    if posixpath.isabs(normalized_path) != posixpath.isabs(normalized_search_path):
        return clean_path
    try:
        relative_path = posixpath.relpath(normalized_path, normalized_search_path)
    except ValueError:
        return clean_path
    if relative_path == ".":
        return "."
    if relative_path.startswith("../"):
        return clean_path
    return relative_path


def search_full_path(path: str, search_path: str) -> str:
    """Return the full path represented by a Search result path."""
    clean_path = path.strip()
    clean_search_path = search_path.strip()
    if not clean_path:
        return ""
    if posixpath.isabs(clean_path) or not clean_search_path:
        return posixpath.normpath(clean_path)
    return posixpath.normpath(posixpath.join(clean_search_path, clean_path))


def parse_hhs_search_results(
    output: str, search_type: str, search_path: str
) -> list[dict[str, str]]:
    """Parse HomeSetup search command output into table rows."""
    rows: list[dict[str, str]] = []
    result_type = "Folder" if search_type == "Folders" else search_type.rstrip("s")
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("Searching for "):
            continue
        row = {
            "Type": result_type,
            "Path": clean_line,
            "FullPath": search_full_path(clean_line, search_path),
            "Modified": "",
            "Size": "",
            "Line": "",
            "LineNumber": "",
            "Match": "",
        }
        if clean_line.startswith("__HHS_SEARCH_RESULT__\t"):
            parts = clean_line.split("\t", 3)
            if len(parts) >= 3:
                row["Path"] = search_relative_path(parts[1], search_path)
                row["FullPath"] = search_full_path(parts[1], search_path)
                row["Modified"] = ssh_explorer_mtime_text(parts[2])
                if len(parts) == 4 and search_type == "Files":
                    row["Size"] = ssh_explorer_size_text(parts[3], "File")
            rows.append(row)
            continue
        if search_type == "Strings":
            match = re.match(r"^(.+?):(\d+):(.*)$", clean_line)
            if match:
                row["Path"] = search_relative_path(match.group(1), search_path)
                row["FullPath"] = search_full_path(match.group(1), search_path)
                row["Line"] = match.group(2)
                row["Match"] = match.group(3).strip()
            else:
                row["Path"] = search_relative_path(clean_line, search_path)
                row["FullPath"] = search_full_path(clean_line, search_path)
        else:
            row["Path"] = search_relative_path(clean_line, search_path)
            row["FullPath"] = search_full_path(clean_line, search_path)
        rows.append(row)
    return rows


def filter_search_rows(
    rows: list[dict[str, str]], search_filter: str = "All", text_filter: str = ""
) -> list[dict[str, str]]:
    """Return Search result rows matching the selected result filter."""
    if search_filter != "Containing":
        return rows
    return [row for row in rows if row_matches_text_filter(row, text_filter)]


def colorize_search_result_line(value: str, text_filter: str = "") -> str:
    """Return a Search result line with matching text highlighted."""
    clean_value = strip_ansi(value)
    ranges = log_filter_highlight_ranges(clean_value, text_filter)
    html_parts: list[str] = []
    cursor = 0
    for start, end, css_class in ranges:
        if start > cursor:
            html_parts.append(html.escape(clean_value[cursor:start]))
        html_parts.append(
            f'<span class="hhs-log-{css_class}">{html.escape(clean_value[start:end])}</span>'
        )
        cursor = end
    html_parts.append(html.escape(clean_value[cursor:]))
    return "".join(html_parts)


def search_result_path_link(row: dict[str, str]) -> str:
    """Return a clickable Search result path link."""
    display_path = display_path_value(row.get("Path", ""))
    link_path = str(row.get("FullPath") or row.get("Path") or "").strip()
    full_path = posixpath.normpath(link_path) if link_path else ""
    query = urllib.parse.urlencode({hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM: full_path})
    safe_display_path = html.escape(display_path)
    safe_full_path = html.escape(full_path, quote=True)
    return (
        f'<a class="hhs-search-result-path-link" href="?{query}" target="_self" '
        f'title="{safe_full_path}" data-hhs-open-path="{safe_full_path}">'
        f"{safe_display_path}</a>"
    )


def render_search_string_results(
    rows: list[dict[str, str]], query: str, text_filter: str = ""
) -> None:
    """Render string Search results with highlighted matching text."""
    if not rows:
        st.caption("No search results.")
        return
    line_filter = query or text_filter
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td>{search_result_path_link(row)}</td>"
            f"<td>{html.escape(row.get('Line', ''))}</td>"
            f"<td>{colorize_search_result_line(row.get('Match', ''), line_filter)}</td>"
            "</tr>"
        )
    st.markdown(
        '<div class="hhs-search-results hhs-search-string-results">'
        "<table>"
        "<thead><tr><th>Path</th><th>Line</th><th>Match</th></tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_search_path_results(rows: list[dict[str, str]], search_type: str) -> None:
    """Render file and folder Search results with clickable paths."""
    if not rows:
        st.caption("No search results.")
        return
    headers = search_result_headers(search_type)
    header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    table_rows = []
    for row in rows:
        row_cells = [f"<td>{search_result_path_link(row)}</td>"]
        if "Size" in headers:
            row_cells.append(f"<td>{html.escape(row.get('Size', ''))}</td>")
        row_cells.append(f"<td>{html.escape(row.get('Modified', ''))}</td>")
        table_rows.append(f"<tr>{''.join(row_cells)}</tr>")
    st.markdown(
        '<div class="hhs-search-results hhs-search-string-results">'
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )


def increase_search_visible_count() -> None:
    """Increase the number of visible Search results by one page."""
    visible_count = int(
        st.session_state.get(
            "search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE
        )
    )
    st.session_state["search_visible_count"] = (
        visible_count + hhs_ui_constants.SEARCH_PAGE_SIZE
    )


def visible_search_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return the Search rows currently visible for incremental rendering."""
    visible_count = int(
        st.session_state.get(
            "search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE
        )
    )
    if visible_count < hhs_ui_constants.SEARCH_PAGE_SIZE:
        visible_count = hhs_ui_constants.SEARCH_PAGE_SIZE
    st.session_state["search_visible_count"] = visible_count
    return rows[:visible_count]


def render_search_load_more(total_count: int) -> None:
    """Render the Search load-more control when hidden rows remain."""
    visible_count = int(
        st.session_state.get(
            "search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE
        )
    )
    if visible_count >= total_count:
        return
    displayed_count = min(visible_count, total_count)
    with st.container(key="search_load_more"):
        st.button(
            f"Load more results ({displayed_count}/{total_count}) ...",
            key="search_load_more_button",
            help="Load more search results",
            on_click=increase_search_visible_count,
            width="stretch",
        )
    render_search_auto_load_more(displayed_count, total_count)


def render_search_auto_load_more(displayed_count: int, total_count: int) -> None:
    """Attach browser-side auto loading for Search results at page bottom."""
    render_token = json.dumps(f"{displayed_count}:{total_count}")
    components.html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsSearchAutoLoadCleanup) {
              parentWindow.__hhsSearchAutoLoadCleanup();
            }
            const renderToken = __HHS_SEARCH_AUTO_LOAD_TOKEN__;
            const buttonSelector = ".st-key-search_load_more_button button";
            const loadingMarkup = `
              <span class="hhs-search-load-more-preloader">
                <span class="hhs-search-load-more-preloader-spinner" aria-hidden="true"></span>
                <span class="hhs-search-load-more-preloader-label">Loading more results...</span>
              </span>
            `;
            let requested = false;
            const componentFrame = window.frameElement;
            const loadMoreContainer = doc.querySelector(".st-key-search_load_more");
            const sentinel = loadMoreContainer || componentFrame;
            const scrollCandidates = [
              parentWindow,
              doc,
              doc.scrollingElement,
              doc.documentElement,
              doc.body,
              doc.querySelector("[data-testid='stAppViewContainer']"),
              doc.querySelector("[data-testid='stMain']"),
              doc.querySelector(".stApp"),
            ].filter(Boolean);
            const scrollTargets = [...new Set(scrollCandidates)];
            const elementNearBottom = (element) => {
              if (element === parentWindow || element === doc) {
                const page = doc.scrollingElement || doc.documentElement;
                const scrollTop = parentWindow.scrollY || page.scrollTop || doc.body.scrollTop || 0;
                const viewportHeight = parentWindow.innerHeight || page.clientHeight || 0;
                const pageHeight = Math.max(page.scrollHeight, doc.body.scrollHeight);
                return scrollTop + viewportHeight >= pageHeight - 120;
              }
              return element.scrollTop + element.clientHeight >= element.scrollHeight - 120;
            };
            const nearBottom = () => {
              return scrollTargets.some(elementNearBottom);
            };
            const renderLoading = (button) => {
              if (!button || button.dataset.hhsLoadMoreLoading === "true") {
                return;
              }
              button.dataset.hhsLoadMoreLoading = "true";
              button.setAttribute("aria-busy", "true");
              button.innerHTML = loadingMarkup;
            };
            const bindButton = () => {
              const button = doc.querySelector(buttonSelector);
              if (!button) {
                return null;
              }
              if (button.dataset.hhsLoadMoreBound !== renderToken) {
                delete button.dataset.hhsLoadMoreLoading;
                button.removeAttribute("aria-busy");
                button.dataset.hhsLoadMoreBound = renderToken;
                button.addEventListener("click", () => renderLoading(button), { once: true });
              }
              return button;
            };
            const loadMore = (force = false) => {
              const button = bindButton();
              if (!button || button.disabled || requested) {
                return;
              }
              if (!force && !nearBottom()) {
                return;
              }
              requested = true;
              renderLoading(button);
              button.click();
            };
            const onScroll = () => {
              parentWindow.requestAnimationFrame(loadMore);
            };
            let observer = null;
            bindButton();
            if (sentinel && parentWindow.IntersectionObserver) {
              observer = new parentWindow.IntersectionObserver(
                (entries) => {
                  if (entries.some((entry) => entry.isIntersecting)) {
                    loadMore(true);
                  }
                },
                { root: null, rootMargin: "0px 0px 240px 0px", threshold: 0 }
              );
              observer.observe(sentinel);
            }
            scrollTargets.forEach((target) => {
              target.addEventListener("scroll", onScroll, { passive: true });
            });
            parentWindow.addEventListener("resize", onScroll, { passive: true });
            parentWindow.__hhsSearchAutoLoadCleanup = () => {
              if (observer) {
                observer.disconnect();
              }
              scrollTargets.forEach((target) => {
                target.removeEventListener("scroll", onScroll);
              });
              parentWindow.removeEventListener("resize", onScroll);
            };
            parentWindow.setTimeout(loadMore, 150);
          })();
        </script>
        """.replace("__HHS_SEARCH_AUTO_LOAD_TOKEN__", render_token),
        height=0,
    )


def search_result_headers(search_type: str) -> list[str]:
    """Return visible Search result table columns for one Search type."""
    if search_type == "Strings":
        return ["Path", "Line", "Match"]
    if search_type == "Files":
        return ["Path", "Size", "Modified"]
    return ["Path", "Modified"]


def search_loader_message(query: str, search_path: str) -> str:
    """Return the themed preloader message for one Search execution."""
    return (
        f"Searching for %primary_color%{query}%primary_color% "
        f"in %secondary_color%{search_path}%secondary_color%"
    )


def clean_recent_search_value(value: object) -> str:
    """Return a Search history value without converting None into text."""
    if value is None:
        return ""
    return str(value).strip()


def clean_search_term_value(value: object) -> str:
    """Return a Search term value, excluding Streamlit's empty selection marker."""
    clean_value = clean_recent_search_value(value)
    return "" if clean_value == "None" else clean_value


def normalize_recent_search_values(
    values: object,
    current_value: object = "",
    limit: int = 20,
    cleaner: Callable[[object], str] = clean_recent_search_value,
) -> list[str]:
    """Return de-duplicated recent Search values with the current value first."""
    value_list = values if isinstance(values, list) else []
    candidates = [current_value, *value_list]
    normalized: list[str] = []
    for candidate in candidates:
        clean_candidate = cleaner(candidate)
        if clean_candidate and clean_candidate not in normalized:
            normalized.append(clean_candidate)
        if len(normalized) >= limit:
            break
    return normalized


def normalize_search_directories(
    directories: object,
    current_directory: str = "",
) -> list[str]:
    """Return de-duplicated Search directories with the current directory first."""
    return normalize_recent_search_values(
        directories,
        current_directory,
        hhs_ui_constants.SEARCH_DIRECTORY_HISTORY_LIMIT,
    )


def normalize_search_terms(terms: object, current_term: str = "") -> list[str]:
    """Return de-duplicated Search terms with the current term first."""
    return normalize_recent_search_values(
        terms,
        current_term,
        hhs_ui_constants.SEARCH_TERM_HISTORY_LIMIT,
        clean_search_term_value,
    )


def remember_search_directory(search_path: object) -> str:
    """Store one Search directory in recent history and return its clean value."""
    clean_path = (
        clean_recent_search_value(search_path) or footer_working_directory() or "."
    )
    st.session_state["search_path"] = clean_path
    st.session_state["search_directories"] = normalize_search_directories(
        st.session_state.get("search_directories", []),
        clean_path,
    )
    return clean_path


def search_directory_options() -> list[str]:
    """Return Search directory select options including the current value."""
    remember_search_directory(st.session_state.get("search_path", ""))
    return list(st.session_state.get("search_directories", []))


def handle_search_directory_change() -> None:
    """Persist the selected Search directory and update recent directories."""
    remember_search_directory(st.session_state.get("search_path", ""))
    save_ui_state()


def cached_search_terms() -> list[str]:
    """Return recent Search terms from the TTL-backed UI cache."""
    cached_value = cache_get(hhs_ui_constants.SEARCH_TERM_HISTORY_CACHE_KEY)
    terms = cached_value.get("terms", []) if cached_value else []
    return normalize_search_terms(terms)


def remember_search_term(search_query: object) -> str:
    """Store one Search term in recent history and return its clean value."""
    clean_query = clean_search_term_value(search_query)
    if not clean_query:
        if "search_query" in st.session_state:
            st.session_state["search_query"] = None
        return ""
    st.session_state["search_query"] = clean_query
    cache_set(
        hhs_ui_constants.SEARCH_TERM_HISTORY_CACHE_KEY,
        {"terms": normalize_search_terms(cached_search_terms(), clean_query)},
        hhs_ui_constants.SEARCH_TERM_HISTORY_TTL_SECONDS,
    )
    return clean_query


def search_term_options() -> list[str]:
    """Return Search term select options including the current value."""
    clean_query = clean_search_term_value(st.session_state.get("search_query", ""))
    if st.session_state.get("search_query") and not clean_query:
        st.session_state["search_query"] = None
    return normalize_search_terms(
        cached_search_terms(),
        clean_query,
    )


def toggle_search_option(state_key: str) -> None:
    """Toggle one boolean Search option and persist the form state."""
    st.session_state[state_key] = not bool(st.session_state.get(state_key, False))
    save_ui_state()


def render_search_option_toggle(
    state_key: str, glyph: str, help_text: str, disabled: bool = False
) -> None:
    """Render one glyph Search option toggle with pressed-state styling."""
    selected = bool(st.session_state.get(state_key, False))
    selected_token = "selected" if selected else "idle"
    st.button(
        glyph,
        key=f"{state_key}_toggle_{selected_token}",
        help=help_text,
        on_click=toggle_search_option,
        args=(state_key,),
        disabled=disabled,
        width="stretch",
    )


def submit_search_query() -> None:
    """Persist the Search form values that should be executed."""
    query = clean_search_term_value(st.session_state.get("search_query", ""))
    search_path = clean_recent_search_value(st.session_state.get("search_path", ""))
    if not query:
        st.session_state["search_result_query"] = ""
        push_floating_status("Enter a search query before searching.", "warn")
        return
    query = remember_search_term(query)
    if not search_path:
        search_path = footer_working_directory() or "."
    search_path = remember_search_directory(search_path)
    search_type = normalized_search_type(st.session_state.get("search_type"))
    st.session_state["search_result_type"] = search_type
    st.session_state["search_result_path"] = search_path
    st.session_state["search_result_query"] = query
    st.session_state["search_result_ignore_case"] = bool(
        st.session_state.get("search_ignore_case", False)
    )
    st.session_state["search_result_words"] = bool(
        st.session_state.get("search_words", False)
    )
    st.session_state["search_result_binary"] = bool(
        st.session_state.get("search_binary", False)
    )
    st.session_state["search_visible_count"] = hhs_ui_constants.SEARCH_PAGE_SIZE
    cache_delete_tag("search")
    save_ui_state()


def render_search_controls() -> None:
    """Render the Search controls in one compact row."""
    with st.container(key="search_controls"):
        kind_column, term_column, path_column, picker_column, search_column = (
            st.columns([1.15, 3.0, 3.0, 0.22, 0.22], vertical_alignment="bottom")
        )
        with kind_column:
            st.selectbox(
                "Kind",
                options=hhs_ui_constants.SEARCH_TYPES,
                key="search_type",
                format_func=search_type_label,
            )
        with term_column:
            st.selectbox(
                "Search terms",
                options=search_term_options(),
                index=None,
                key="search_query",
                placeholder="Search for files, folders, or strings",
                accept_new_options=True,
                on_change=submit_search_query,
                width="stretch",
            )
        with path_column:
            st.selectbox(
                "Search directory",
                options=search_directory_options(),
                key="search_path",
                on_change=handle_search_directory_change,
                width="stretch",
            )
        with picker_column:
            st.button(
                "",
                key="search_path_folder_picker_button",
                help="Select search path",
                on_click=request_path_picker,
                args=("search_path", st.session_state.get("search_path", ""), "folder"),
                width="stretch",
            )
        with search_column:
            st.button(
                "",
                key="search_submit_button",
                help="Search",
                on_click=submit_search_query,
                width="stretch",
            )
    render_search_submit_preloader_script()


def render_search_submit_preloader_script() -> None:
    """Attach a delayed browser-side preloader for Search submit."""
    timeout_seconds = int(hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS)
    delay_ms = int(hhs_ui_constants.SEARCH_SUBMIT_PRELOADER_DELAY_MS)
    components.html(
        f"""
        <script>
          (() => {{
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsSearchSubmitPreloaderCleanup) {{
              parentWindow.__hhsSearchSubmitPreloaderCleanup();
            }}
            const buttonSelector = ".st-key-search_submit_button button";
            const querySelector = ".st-key-search_query [role='combobox'], .st-key-search_query input";
            const pathSelector = ".st-key-search_path [role='combobox'], .st-key-search_path input";
            const timeoutSeconds = {timeout_seconds};
            const delayMs = {delay_ms};
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
            const clearPendingSearchOverlay = () => {{
              if (parentWindow.__hhsSearchSubmitPreloaderDelayTimer) {{
                parentWindow.clearTimeout(parentWindow.__hhsSearchSubmitPreloaderDelayTimer);
                parentWindow.__hhsSearchSubmitPreloaderDelayTimer = null;
              }}
              const overlay = doc.getElementById("hhs-command-overlay");
              if (
                overlay &&
                String(overlay.dataset.hhsOverlayToken || "").startsWith("search-submit-")
              ) {{
                overlay.remove();
                doc.body.dataset.hhsCommandOverlayHidden = "true";
                parentWindow.__hhsCommandOverlayClearedAt = Date.now();
                parentWindow.__hhsCommandOverlayToken = "";
                clearOverlayTimers();
              }}
            }};
            const searchValue = (selector) => {{
              const node = doc.querySelector(selector);
              if (!node) {{
                return "";
              }}
              if ("value" in node) {{
                return String(node.value || "").trim();
              }}
              return String(node.textContent || "").trim();
            }};
            const renderElapsed = (overlay, startedAt) => {{
              const node = overlay.querySelector(".hhs-tab-loader-elapsed");
              if (!node) {{
                return;
              }}
              const elapsedSeconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
              const elapsedRatio = elapsedSeconds / Math.max(1, timeoutSeconds);
              const minutes = Math.floor(elapsedSeconds / 60);
              const seconds = String(elapsedSeconds % 60).padStart(2, "0");
              node.textContent = `time elapsed: ${{minutes}}m:${{seconds}}s`;
              node.classList.toggle("hhs-loader-elapsed-warning", elapsedRatio >= 0.3 && elapsedRatio < 0.6);
              node.classList.toggle("hhs-loader-elapsed-danger", elapsedRatio >= 0.6);
            }};
            const showOverlay = (query, searchPath) => {{
              if (!query) {{
                return;
              }}
              clearOverlayTimers();
              const createdAt = Date.now();
              const overlayToken = `search-submit-${{createdAt}}`;
              parentWindow.__hhsCommandOverlayToken = overlayToken;
              doc.body.dataset.hhsCommandOverlayHidden = "false";
              const existing = doc.getElementById("hhs-command-overlay");
              if (existing) {{
                existing.remove();
              }}
              const overlay = doc.createElement("div");
              overlay.id = "hhs-command-overlay";
              overlay.className = "hhs-tab-loader hhs-tab-loader-transient";
              overlay.dataset.hhsOverlayToken = overlayToken;
              overlay.dataset.hhsOverlayCreatedAt = String(createdAt);
              overlay.style.position = "fixed";
              overlay.style.inset = "0";
              overlay.style.width = "100vw";
              overlay.style.height = "100dvh";
              overlay.style.display = "flex";
              overlay.style.alignItems = "center";
              overlay.style.justifyContent = "center";
              overlay.style.zIndex = "999999";
              overlay.innerHTML = `
                <div class="hhs-tab-loader-panel">
                  <span class="hhs-tab-loader-spinner"></span>
                  <span class="hhs-tab-loader-copy">
                    <span class="hhs-tab-loader-label"></span>
                    <span class="hhs-tab-loader-elapsed" data-timeout-seconds="${{timeoutSeconds}}">
                      time elapsed: 0m:00s
                    </span>
                  </span>
                </div>
              `;
              const label = overlay.querySelector(".hhs-tab-loader-label");
              if (label) {{
                const queryNode = doc.createElement("span");
                queryNode.className = "hhs-loader-primary";
                queryNode.textContent = query;
                const pathNode = doc.createElement("span");
                pathNode.className = "hhs-loader-secondary";
                pathNode.textContent = searchPath;
                label.append("Searching for ", queryNode, " in ", pathNode);
              }}
              doc.body.appendChild(overlay);
              renderElapsed(overlay, createdAt);
              parentWindow.__hhsCommandOverlayTimer = parentWindow.setInterval(
                () => renderElapsed(overlay, createdAt),
                1000
              );
              parentWindow.__hhsCommandOverlayExpiryTimer = parentWindow.setTimeout(
                () => {{
                  const current = doc.getElementById("hhs-command-overlay");
                  if (current && current.dataset.hhsOverlayToken === overlayToken) {{
                    current.remove();
                    doc.body.dataset.hhsCommandOverlayHidden = "true";
                  }}
                  clearOverlayTimers();
                }},
                Math.max(1, timeoutSeconds + 2) * 1000
              );
            }};
            const scheduleOverlay = () => {{
              const query = searchValue(querySelector);
              if (!query) {{
                return;
              }}
              const searchPath = searchValue(pathSelector) || "current directory";
              if (parentWindow.__hhsSearchSubmitPreloaderDelayTimer) {{
                parentWindow.clearTimeout(parentWindow.__hhsSearchSubmitPreloaderDelayTimer);
              }}
              parentWindow.__hhsSearchSubmitPreloaderDelayTimer = parentWindow.setTimeout(
                () => showOverlay(query, searchPath),
                delayMs
              );
            }};
            const onClick = (event) => {{
              if (event.target && event.target.closest(buttonSelector)) {{
                scheduleOverlay();
              }}
            }};
            const onKeydown = (event) => {{
              if (
                event.key === "Enter" &&
                event.target &&
                event.target.closest(".st-key-search_query")
              ) {{
                scheduleOverlay();
              }}
            }};
            doc.addEventListener("click", onClick, true);
            doc.addEventListener("keydown", onKeydown, true);
            parentWindow.__hhsSearchSubmitPreloaderCleanup = () => {{
              doc.removeEventListener("click", onClick, true);
              doc.removeEventListener("keydown", onKeydown, true);
              clearPendingSearchOverlay();
            }};
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_search_filters() -> tuple[str, str]:
    """Render Search result filters and return selected filter values."""
    with st.container(key="search_filter_controls"):
        (
            filter_column,
            other_filter_column,
            ignore_case_column,
            words_column,
            binary_column,
            clear_column,
        ) = (
            st.columns(
                [1.15, 3.0, 0.22, 0.22, 0.22, 0.22],
                vertical_alignment="center",
            )
        )
        with filter_column:
            selected_filter = st.radio(
                "Table filter",
                hhs_ui.SEARCH_FILTERS,
                horizontal=True,
                key="search_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
            )
        other_filter = ""
        if selected_filter == "Containing":
            with other_filter_column:
                other_filter = st.text_input(
                    "Filters",
                    key="search_other_filter",
                    label_visibility="collapsed",
                    on_change=save_ui_state,
                    placeholder="Type result filter text",
                    width="stretch",
                )
        with ignore_case_column:
            render_search_option_toggle(
                "search_ignore_case", "Aa", "Ignore case (-i)"
            )
        with words_column:
            render_search_option_toggle("search_words", "", "Match words (-w)")
        with binary_column:
            render_search_option_toggle("search_binary", "", "Search binary files (-b)")
        with clear_column:
            st.button(
                "",
                key="search_other_filter_clear",
                help="Clear filter text",
                on_click=clear_table_other_filter,
                args=("search_other_filter",),
                disabled=not bool(str(other_filter)),
                width="stretch",
            )
        return selected_filter, other_filter


def render_search_results(search_filter: str = "All", text_filter: str = "") -> None:
    """Render the Search results table for the submitted query."""
    search_type = normalized_search_type(st.session_state.get("search_result_type"))
    search_path = str(st.session_state.get("search_result_path", "")).strip()
    query = str(st.session_state.get("search_result_query", "")).strip()
    if not query:
        return
    ignore_case = bool(st.session_state.get("search_result_ignore_case", False))
    words = bool(st.session_state.get("search_result_words", False))
    binary = bool(st.session_state.get("search_result_binary", False))
    result = run_bash_command(
        build_hhs_search_command(
            search_type, query, search_path, ignore_case, words, binary
        ),
        search_loader_message(query, search_path),
        ttl_seconds=hhs_ui.UI_CACHE_NORMAL_TTL_SECONDS,
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        cache_tag="search",
        cache_key_override=search_command_cache_key(
            search_type, query, search_path, ignore_case, words, binary
        ),
        show_overlay=False,
    )
    clear_preloader()
    with st.container(key="search_results"):
        if result.returncode != 0:
            st.error(clean_command_status_message(result.stderr or result.stdout))
            return
        rows = parse_rows_cached(
            "search",
            f"{search_type}\n{search_path}\n{result.stdout}",
            lambda output: parse_hhs_search_results(
                output.split("\n", 2)[2], search_type, search_path
            ),
        )
        rows = filter_search_rows(rows, search_filter, text_filter)
        visible_rows = visible_search_rows(rows)
        if search_type == "Strings":
            render_search_string_results(visible_rows, query, text_filter)
            render_search_load_more(len(rows))
            return
        render_search_path_results(visible_rows, search_type)
        render_search_load_more(len(rows))


def render_search_view() -> None:
    """Render the HomeSetup Search view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> Search</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Search", expanded=True):
        render_search_controls()
        search_filter, search_text_filter = render_search_filters()
    render_search_results(search_filter, search_text_filter)


def render_ai_models_result() -> subprocess.CompletedProcess[str] | None:
    """Render the cached/background AI model listing command result."""
    return render_cached_command_result(
        build_hhs_ask_models_command(),
        "Loading Ollama model",
        "ai_models",
        hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to load Ollama models.",
    )


def render_ai_chat_panel() -> None:
    """Render the HomeSetup Ollama chat panel."""
    if st.session_state.get("ai_clear_chat_pending", False):
        pop_dialog(
            title="Confirm chat clear",
            message="Clear the chat and reset AI context entirely?",
            confirm_key="ai_confirm_clear_button",
            cancel_key="ai_cancel_clear_button",
            on_confirm=confirm_ai_chat_clear,
            on_cancel=cancel_ai_chat_clear_confirmation,
        )
        return

    username = current_username()
    model_result = render_ai_models_result()
    if model_result is None:
        return
    ollama_model = (
        parse_current_ollama_model(model_result.stdout)
        if model_result.returncode == 0
        else "unknown"
    )
    context_size = ollama_model_context_size(ollama_model)
    meta_col, clear_col = st.columns([3.6, 0.4], vertical_alignment="center")
    with meta_col:
        meta_placeholder = st.empty()
        meta_placeholder.markdown(
            ai_chat_meta_html(
                username, ollama_model, context_size, model_result.stdout
            ),
            unsafe_allow_html=True,
        )
    completed = background_job_result(AI_ASK_JOB)
    if completed is not None:
        result, metadata = completed
        response_model = str(metadata.get("ollama_model", ollama_model)).strip()
        response_model = response_model or ollama_model
        try:
            ask_started_at = float(metadata.get("started_at", 0.0) or 0.0)
        except (TypeError, ValueError):
            ask_started_at = 0.0
        if ask_started_at:
            request_duration = max(0.0, time.perf_counter() - ask_started_at)
            record_ai_model_request_duration(ollama_model, request_duration)
            meta_placeholder.markdown(
                ai_chat_meta_html(
                    username, ollama_model, context_size, model_result.stdout
                ),
                unsafe_allow_html=True,
            )
        if result.returncode != 0:
            answer = strip_ansi(
                result.stderr or result.stdout or "Unable to ask Ollama."
            )
            push_floating_status("Ollama request failed.", "error")
        else:
            answer = clean_hhs_ask_output(result.stdout) or strip_ansi(result.stdout)
        st.session_state["ai_chat_messages"].append(
            {"role": "assistant", "content": answer}
        )
        save_ui_state()
    with clear_col:
        st.button(
            " Clear",
            key="ai_clear_chat_button",
            help="Clear chat and context",
            on_click=request_ai_chat_clear_confirmation,
            disabled=background_job_is_running(AI_ASK_JOB),
            width="stretch",
        )
    if not st.session_state["ai_chat_messages"]:
        st.markdown("### There is no chat history")
    for message in st.session_state["ai_chat_messages"]:
        if message["role"] == "assistant":
            avatar_file = hhs_ui.APP_AI_OLLAMA_AVATAR_FILE
            message_name = "Ollama"
        elif message["role"] == "system":
            avatar_file = hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE
            message_name = "HomeSetup"
        else:
            avatar_file = hhs_ui.APP_AI_USER_AVATAR_FILE
            message_name = "User"
        avatar = str(avatar_file) if avatar_file.is_file() else None
        with st.chat_message(message_name, avatar=avatar):
            render_ai_chat_message(
                message["role"],
                message["content"],
                username,
                ollama_model,
                context_size,
            )
    if background_job_is_running(AI_ASK_JOB):
        with st.chat_message(
            "Ollama",
            avatar=(
                str(hhs_ui.APP_AI_OLLAMA_AVATAR_FILE)
                if hhs_ui.APP_AI_OLLAMA_AVATAR_FILE.is_file()
                else None
            ),
        ):
            render_background_job_status(AI_ASK_JOB, "Generating response...")

    if prompt := st.chat_input("Ask Ollama through HomeSetup"):
        if background_job_is_running(AI_ASK_JOB):
            push_floating_status("Ollama is still generating a response.", "warn")
            return
        st.session_state["ai_chat_messages"].append({"role": "user", "content": prompt})
        save_ui_state()
        with st.chat_message(
            "User",
            avatar=(
                str(hhs_ui.APP_AI_USER_AVATAR_FILE)
                if hhs_ui.APP_AI_USER_AVATAR_FILE.is_file()
                else None
            ),
        ):
            render_ai_chat_message("user", prompt, username, ollama_model, context_size)
        ask_started_at = time.perf_counter()
        started = start_background_bash_command(
            AI_ASK_JOB,
            build_hhs_ask_command(prompt),
            "Asking Ollama",
            timeout_seconds=hhs_ask_timeout_seconds(),
            metadata={
                "prompt": prompt,
                "ollama_model": ollama_model,
                "context_size": context_size,
                "started_at": ask_started_at,
            },
        )
        if not started:
            push_floating_status("Ollama is still generating a response.", "warn")
            return
        with st.chat_message(
            "Ollama",
            avatar=(
                str(hhs_ui.APP_AI_OLLAMA_AVATAR_FILE)
                if hhs_ui.APP_AI_OLLAMA_AVATAR_FILE.is_file()
                else None
            ),
        ):
            render_background_job_status(AI_ASK_JOB, "Generating response...")


def style_ai_model_row(row: pd.Series) -> list[str]:
    """Return dataframe row styles for the active Ollama model."""
    status = str(row.get("Status", ""))
    if status == "Active":
        return [
            "background-color: rgba(139, 233, 253, 0.18); color: #8be9fd; font-weight: 800;"
        ] * len(row)
    if status == "Downloaded":
        return [
            "color: #4da3ff; font-weight: 800;" if column == "Status" else ""
            for column in row.index
        ]
    return [""] * len(row)


def render_ai_prompt_file_panel() -> None:
    """Render the editable runtime Ollama prompt file panel."""
    if not st.session_state.get("ai_prompt_loaded"):
        result = render_cached_command_result(
            build_hhs_ask_prompt_file_command(),
            "Loading Ollama prompt file",
            "ai",
            hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
            hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
            "Unable to load Ollama prompt file.",
        )
        if result is None:
            return
        output = (
            result.stdout if result.returncode == 0 else result.stderr or result.stdout
        )
        clean_output = strip_ansi(output or "")
        if result.returncode == 0:
            st.session_state["ai_prompt_editor"] = clean_output
            st.session_state["ai_prompt_error"] = ""
            st.session_state["ai_prompt_loaded"] = True
        else:
            st.session_state["ai_prompt_error"] = (
                clean_output.strip() or "Unable to load Ollama prompt file."
            )

    load_col, save_col, revert_col = st.columns(
        [0.8, 0.75, 0.8], vertical_alignment="center"
    )
    with load_col:
        st.button(
            " Load",
            key="ai_prompt_load_button",
            help="Reload the runtime Ollama prompt file",
            on_click=refresh_ai_prompt_file,
            width="stretch",
        )
    with save_col:
        st.button(
            " Save",
            key="ai_prompt_save_button",
            help="Save changes to the runtime Ollama prompt file",
            on_click=save_ai_prompt_file,
            width="stretch",
        )
    with revert_col:
        st.button(
            " Revert",
            key="ai_prompt_revert_button",
            help="Restore the runtime Ollama prompt file from the bundled template",
            on_click=revert_ai_prompt_file,
            width="stretch",
        )

    prompt_error = str(st.session_state.get("ai_prompt_error", "")).strip()
    if prompt_error:
        st.error(prompt_error)

    prompt_text = str(st.session_state.get("ai_prompt_editor", ""))
    prompt_line_count = max(prompt_text.count("\n") + 1, 10)
    st.text_area(
        "Prompt",
        key="ai_prompt_editor",
        height=max(280, min(620, prompt_line_count * 22)),
        label_visibility="collapsed",
    )


def render_ai_context_output_panel() -> None:
    """Render the current HomeSetup Ollama context output panel."""
    upload_col, ingest_col, clear_col, refresh_col = st.columns(
        [1.35, 0.7, 0.7, 0.8], vertical_alignment="center"
    )
    with upload_col:
        uploaded_context = st.file_uploader(
            "Ingest context",
            type=hhs_ui_constants.AI_CONTEXT_UPLOAD_TYPES,
            key="ai_context_upload",
            label_visibility="collapsed",
        )
    with ingest_col:
        if st.button(
            " Ingest",
            key="ai_ingest_context_button",
            help="Ingest uploaded text into Ollama context",
            width="stretch",
        ):
            ingest_ai_context_upload(uploaded_context)
    with clear_col:
        st.button(
            " Clear",
            key="ai_clear_context_button",
            help="Clear current Ollama context history",
            on_click=clear_ai_context_history,
            width="stretch",
        )
    with refresh_col:
        st.button(
            " Refresh",
            key="ai_refresh_context_button",
            help="Refresh current Ollama context",
            on_click=refresh_ai_context,
            width="stretch",
        )

    context_error = str(st.session_state.get("ai_context_error", "")).strip()
    context_output = str(st.session_state.get("ai_context_output", "")).strip()
    if context_error:
        st.error(context_error)
        return
    if not context_output:
        st.markdown("### AI context is clear")
        return
    render_terminal_output(context_output)


def render_ai_context_panel() -> None:
    """Render foldable AI prompt and context panels."""
    with st.expander("Prompt", expanded=False):
        render_ai_prompt_file_panel()
    with st.expander("History", expanded=True):
        render_ai_context_output_panel()


def render_ai_model_select_dialog(old_model: str, new_model: str) -> None:
    """Render the AI model selection confirmation dialog."""
    pop_dialog(
        title="Confirm model change",
        message=f"Change active model from '{old_model}' to '{new_model}'?",
        confirm_key="ai_confirm_model_select_button",
        cancel_key="ai_cancel_model_select_button",
        on_confirm=confirm_ai_model_selection,
        on_cancel=cancel_ai_model_selection,
    )


def render_ai_model_delete_dialog(model_name: str) -> None:
    """Render the AI model deletion confirmation dialog."""
    pop_dialog(
        title="Confirm model deletion",
        message=f"Delete Ollama model '{model_name}'?",
        confirm_key="ai_confirm_model_delete_button",
        cancel_key="ai_cancel_model_delete_button",
        on_confirm=confirm_ai_model_deletion,
        on_cancel=cancel_ai_model_deletion,
    )


def render_ai_settings_panel() -> None:
    """Render the HomeSetup Ollama settings panel."""
    pending = st.session_state.get("ai_model_select_pending")
    if pending:
        old_model = str(pending.get("old", ""))
        new_model = str(pending.get("new", ""))
        render_ai_model_select_dialog(old_model, new_model)
        return

    pending_delete = st.session_state.get("ai_model_delete_pending")
    if pending_delete:
        if isinstance(pending_delete, dict):
            pending_delete_name = str(pending_delete.get("name", ""))
        else:
            pending_delete_name = str(pending_delete)
        render_ai_model_delete_dialog(pending_delete_name)
        return
    if background_job_is_running(AI_MODEL_SELECT_JOB) or background_job_is_running(
        AI_MODEL_DELETE_JOB
    ):
        return

    model_result = render_ai_models_result()
    if model_result is None:
        return
    if model_result.returncode != 0:
        st.error(
            strip_ansi(
                model_result.stderr
                or model_result.stdout
                or "Unable to load Ollama models."
            )
        )
        return

    current_model = parse_current_ollama_model(model_result.stdout)
    current_context = ollama_model_context_size(current_model)
    st.markdown(
        f"""
        <div class="hhs-ai-settings-current-model">
          <span>Selected Model: <strong>{html.escape(current_model)}[{html.escape(current_context)}]</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("##### Available Models")
    rows = parse_rows_cached(
        f"ollama_models_{current_model}",
        model_result.stdout,
        lambda output: parse_ollama_model_rows(output, current_model),
    )
    if not rows:
        st.caption("No Ollama models found.")
        return

    selected_index, selected_row = render_table(
        rows,
        key=ai_model_table_key(),
        use_container_width=True,
        row_style=style_ai_model_row,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
        action_buttons=[
            {
                "label": "Select Model",
                "key_prefix": "ai_select_model_button",
                "on_click": request_ai_model_selection,
                "disabled": lambda row, _index: row["Name"] == current_model,
                "args": lambda row, _index: (
                    current_model,
                    row["Name"],
                    str(row.get("Status", "")),
                ),
            },
        ],
        selected_action_buttons=[
            {
                "label": "Delete Model",
                "glyph": "",
                "key_prefix": "ai_delete_model_button",
                "on_click": request_ai_model_deletion,
                "visible": lambda row, _index: str(row.get("Status", ""))
                in ("Active", "Downloaded"),
                "args": lambda row, _index: (row["Name"], str(row.get("Status", ""))),
            },
        ],
        action_column_weights=[1],
    )
    if selected_index is not None:
        actions_anchor_id = f"hhs-ai-model-actions-{selected_index}"
        st.markdown(
            f"""
            <div class="hhs-ai-model-action-footer-guard"></div>
            <div id="{actions_anchor_id}"></div>
            """,
            unsafe_allow_html=True,
        )
        scroll_to_ai_model_actions(actions_anchor_id)

    if st.session_state.get("ai_model_select_error"):
        st.error(st.session_state["ai_model_select_error"])
    if st.session_state.get("ai_model_delete_error"):
        st.error(st.session_state["ai_model_delete_error"])


def ai_view_label(ai_view: str) -> str:
    """Return the display label for an AI view key."""
    return hhs_ui.AI_VIEW_LABELS.get(ai_view, ai_view)


def render_ai_view() -> None:
    """Render the HomeSetup Ollama AI view."""
    if st.session_state.get("ai_clear_chat_execute_pending"):
        execute_pending_ai_chat_clear()
    if st.session_state.get("ai_model_select_execute_pending") or background_job_state(
        AI_MODEL_SELECT_JOB
    ):
        execute_pending_ai_model_selection()
    if st.session_state.get("ai_model_delete_execute_pending") or background_job_state(
        AI_MODEL_DELETE_JOB
    ):
        execute_pending_ai_model_deletion()

    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2> Ask Ollama HomeSetup AI</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    ai_view = st.segmented_control(
        "AI view",
        options=hhs_ui.AI_VIEWS,
        default=st.session_state["ai_view"],
        format_func=ai_view_label,
        key="ai_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    if ai_view == "CHAT":
        render_ai_chat_panel()
    elif ai_view == "CONTEXT":
        render_ai_context_panel()
    elif ai_view == "SETTINGS":
        render_background_job_status(AI_MODEL_SELECT_JOB)
        render_background_job_status(AI_MODEL_DELETE_JOB)
        render_ai_settings_panel()


def selected_remote_host_requires_connection() -> bool:
    """Return whether a remote host is selected without an active SSH connection."""
    host = selected_ssh_host()
    return not selected_host_is_local(host) and not selected_ssh_host_is_connected(host)


def render_remote_connection_required_view() -> None:
    """Render an empty main page that asks the user to connect the remote host."""
    selected_host = selected_ssh_host()
    host = html.escape(selected_host)
    host_address = html.escape(ssh_config_hostname(selected_host))
    st.markdown(
        f"""
        <section class="hhs-remote-connect-required">
          <h1>Remote host: {host} -&gt; {host_address}</h1>
          <hr />
          <br />
          <h2>Connect to the remote host to interact</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_main_view() -> None:
    """Render the active HomeSetup UI view."""
    if not terminal_document_view_is_active():
        render_ttyd_terminal_frame_cleanup_script()
        stop_ttyd_session()
    if selected_remote_host_requires_connection():
        render_remote_connection_required_view()
        return
    if st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY):
        render_document_view()
        return
    visible_views = main_views()
    if st.session_state.get("active_view") not in visible_views:
        st.session_state["active_view"] = "Home"
    active_view = st.radio(
        "View",
        visible_views,
        horizontal=True,
        key="active_view",
        label_visibility="collapsed",
        format_func=main_view_label,
        on_change=save_ui_state,
    )
    if active_view == "Home":
        render_home_view()
    elif active_view == "Configs":
        render_configs_view()
    elif active_view == "Services":
        render_service_view()
    elif active_view == hhs_ui.SSH_VIEW:
        render_ssh_view()
    elif active_view == "History":
        render_history_view()
    elif active_view == "Monitor":
        render_monitor_view()
    elif active_view == "Search":
        render_search_view()
    elif active_view == hhs_ui.AI_VIEW:
        render_ai_view()


def main() -> None:
    """Configure and render the HomeSetup Streamlit UI."""
    selected_theme = persisted_theme_name()
    configure_app_font_theme(selected_theme)
    st.set_page_config(
        page_title=f"HomeSetup - UI v{hhs_ui.VERSION}",
        page_icon=str(hhs_ui.APP_FAVICON_FILE),
        layout="wide",
    )
    restore_ui_state()
    restore_persisted_theme_selection()
    st.session_state.setdefault("updater_last_check_epoch", 0.0)
    st.session_state.setdefault("updater_last_check_output", "")
    st.session_state.setdefault("updater_update_available", False)
    st.session_state.setdefault("updater_check_context", "local")
    st.session_state.setdefault("updater_check_started_context", "")
    st.session_state.setdefault("updater_remote_checked_context", "")
    st.session_state.setdefault("footer_hhs_version_cache_loaded", False)
    st.session_state.setdefault("footer_shell_version_dialog_title", "")
    st.session_state.setdefault("footer_shell_version_output", "")
    render_styles()
    execute_due_updater_check()
    if st.session_state.get("theme_reload_pending"):
        render_theme_reload_overlay()
    st.session_state.setdefault("active_view", "Home")
    st.session_state.setdefault("ai_chat_messages", [])
    st.session_state.setdefault(hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY, False)
    st.session_state.setdefault(
        hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY,
        False,
    )
    if not isinstance(st.session_state["ai_chat_messages"], list):
        st.session_state["ai_chat_messages"] = []
    st.session_state.setdefault("ai_clear_chat_pending", False)
    st.session_state.setdefault("ai_clear_chat_execute_pending", False)
    st.session_state.setdefault("ai_model_select_pending", None)
    st.session_state.setdefault("ai_model_select_execute_pending", None)
    st.session_state.setdefault("ai_model_select_error", "")
    st.session_state.setdefault("ai_model_delete_pending", None)
    st.session_state.setdefault("ai_model_delete_execute_pending", None)
    st.session_state.setdefault("ai_model_delete_error", "")
    st.session_state.setdefault("ai_model_performance_timings", [])
    if not isinstance(st.session_state["ai_model_performance_timings"], list):
        st.session_state["ai_model_performance_timings"] = []
    st.session_state.setdefault("ai_model_performance_averages", {})
    if not isinstance(st.session_state["ai_model_performance_averages"], dict):
        st.session_state["ai_model_performance_averages"] = {}
    st.session_state.setdefault("ai_model_performance_sample_counts", {})
    if not isinstance(st.session_state["ai_model_performance_sample_counts"], dict):
        st.session_state["ai_model_performance_sample_counts"] = {}
    st.session_state.setdefault("ai_context_output", "")
    st.session_state.setdefault("ai_context_error", "")
    st.session_state.setdefault("ai_prompt_editor", "")
    if not isinstance(st.session_state["ai_prompt_editor"], str):
        st.session_state["ai_prompt_editor"] = ""
    st.session_state.setdefault("ai_prompt_error", "")
    if not isinstance(st.session_state["ai_prompt_error"], str):
        st.session_state["ai_prompt_error"] = ""
    st.session_state.setdefault("ai_prompt_loaded", False)
    if not isinstance(st.session_state["ai_prompt_loaded"], bool):
        st.session_state["ai_prompt_loaded"] = False
    st.session_state.setdefault("ai_view", "CHAT")
    if st.session_state["ai_view"] not in hhs_ui.AI_VIEWS:
        st.session_state["ai_view"] = "CHAT"
    st.session_state.setdefault(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY, False)
    st.session_state.setdefault(hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY, "Home")
    st.session_state.setdefault(hhs_ui.DOCUMENT_SELECTED_KEY, "README")
    st.session_state.setdefault("ssh_host_selected", local_hostname())
    st.session_state.setdefault("ssh_connect_pending", "")
    st.session_state.setdefault("ssh_connect_pending_message", "")
    st.session_state.setdefault("ssh_disconnect_pending", "")
    st.session_state.setdefault("ssh_connection_status", "")
    st.session_state.setdefault("ssh_connection_host", "")
    st.session_state.setdefault("ssh_connection_error", "")
    st.session_state.setdefault("ssh_connection_dialog_title", "")
    st.session_state.setdefault("ssh_explorer_delete_pending", None)
    st.session_state.setdefault(hhs_ui.SSH_RECONNECT_HOST_KEY, "")
    restore_registered_ssh_connection_on_session_start()
    synchronize_selected_ssh_host_with_connection()
    if selected_host_is_local():
        st.session_state["ssh_connection_status"] = ""
        st.session_state["ssh_connection_host"] = ""
        st.session_state["ssh_connection_error"] = ""
        st.session_state["ssh_connect_pending"] = ""
        st.session_state["ssh_disconnect_pending"] = ""
    if execute_pending_ssh_disconnection():
        return
    if execute_pending_ssh_connection():
        return
    if render_ssh_connection_dialog():
        return
    initialize_ollama_service_availability()
    update_ollama_service_availability_refresh()
    if st.session_state["active_view"] not in main_views():
        st.session_state["active_view"] = "Home"
    handle_footer_actions()
    render_background_job_status(UPDATER_UPDATE_JOB)
    render_footer_shell_version_dialog()
    st.session_state.setdefault("home_view", "System")
    if st.session_state["home_view"] not in hhs_ui.HOME_VIEWS:
        st.session_state["home_view"] = "System"
    st.session_state.setdefault("home_tools_filter", "All")
    if st.session_state["home_tools_filter"] == "Not Found":
        st.session_state["home_tools_filter"] = "Not Installed"
    if st.session_state["home_tools_filter"] not in hhs_ui.HOME_TOOLS_FILTERS:
        st.session_state["home_tools_filter"] = "All"
    st.session_state.setdefault("home_tools_other_filter", "")
    st.session_state.setdefault("home_tools_table_reset_counter", 0)
    st.session_state.setdefault("home_shopts_filter", "All")
    if st.session_state["home_shopts_filter"] not in hhs_ui.SHOPTS_FILTERS:
        st.session_state["home_shopts_filter"] = "All"
    st.session_state.setdefault("home_shopts_other_filter", "")
    st.session_state.setdefault(hhs_ui.HOME_SHOPTS_TABLE_RESET_COUNTER_KEY, 0)
    st.session_state.setdefault("home_tool_action_execute_pending", None)
    st.session_state.setdefault("config_view", "ENV")
    if st.session_state["config_view"] not in hhs_ui.CONFIG_VIEWS:
        st.session_state["config_view"] = "ENV"
    st.session_state.setdefault("history_view", "COMMANDS")
    if st.session_state["history_view"] not in hhs_ui.HISTORY_VIEWS:
        st.session_state["history_view"] = "COMMANDS"
    st.session_state.setdefault("monitor_view", "DISK")
    if st.session_state["monitor_view"] not in hhs_ui.MONITOR_VIEWS:
        st.session_state["monitor_view"] = "DISK"
    st.session_state.setdefault("search_type", "Files")
    st.session_state["search_type"] = normalized_search_type(
        st.session_state.get("search_type")
    )
    st.session_state.setdefault("search_path", footer_working_directory())
    if not str(st.session_state.get("search_path", "")).strip():
        st.session_state["search_path"] = footer_working_directory() or "."
    st.session_state.setdefault("search_directories", [])
    st.session_state["search_directories"] = normalize_search_directories(
        st.session_state.get("search_directories", []),
        str(st.session_state.get("search_path", "")),
    )
    st.session_state.setdefault("search_query", "")
    st.session_state.setdefault("search_ignore_case", False)
    st.session_state.setdefault("search_words", False)
    st.session_state.setdefault("search_binary", False)
    st.session_state.setdefault("search_result_type", st.session_state["search_type"])
    st.session_state["search_result_type"] = normalized_search_type(
        st.session_state.get("search_result_type")
    )
    st.session_state.setdefault("search_result_path", st.session_state["search_path"])
    if not str(st.session_state.get("search_result_path", "")).strip():
        st.session_state["search_result_path"] = st.session_state["search_path"]
    st.session_state.setdefault("search_result_query", "")
    st.session_state.setdefault("search_result_ignore_case", False)
    st.session_state.setdefault("search_result_words", False)
    st.session_state.setdefault("search_result_binary", False)
    st.session_state.setdefault("search_filter", "All")
    if st.session_state["search_filter"] not in hhs_ui.SEARCH_FILTERS:
        st.session_state["search_filter"] = "All"
    st.session_state.setdefault("search_other_filter", "")
    st.session_state.setdefault(
        "search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE
    )
    st.session_state.setdefault("ssh_view", "TUNNELS")
    if st.session_state["ssh_view"] not in hhs_ui.SSH_VIEWS:
        st.session_state["ssh_view"] = "TUNNELS"
    st.session_state.setdefault("ssh_tunnel_filter", "All")
    if st.session_state["ssh_tunnel_filter"] not in hhs_ui.SSH_TUNNEL_FILTERS:
        st.session_state["ssh_tunnel_filter"] = "All"
    st.session_state.setdefault("ssh_tunnel_other_filter", "")
    st.session_state.setdefault("monitor_process_filter", "All")
    st.session_state.setdefault("monitor_process_other_filter", "")
    monitor_process_filter = str(st.session_state["monitor_process_filter"]).strip()
    if not monitor_process_filter:
        st.session_state["monitor_process_filter"] = "All"
    elif monitor_process_filter not in hhs_ui.PROCESS_FILTERS:
        st.session_state["monitor_process_other_filter"] = monitor_process_filter
        st.session_state["monitor_process_filter"] = "Other"
    st.session_state.setdefault(
        "monitor_disk_directory", monitor_default_disk_directory()
    )
    if not str(st.session_state["monitor_disk_directory"]).strip():
        st.session_state["monitor_disk_directory"] = monitor_default_disk_directory()
    st.session_state.setdefault(
        "monitor_disk_directory_applied",
        st.session_state["monitor_disk_directory"],
    )
    synchronize_monitor_disk_directory_with_host()
    st.session_state.setdefault("monitor_disk_top_n", 10)
    st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n")
    )
    for metric in ("CPU", "MEM"):
        top_n_key = monitor_process_top_n_state_key(metric)
        st.session_state.setdefault(top_n_key, 10)
        st.session_state[top_n_key] = normalized_monitor_top_n(
            st.session_state.get(top_n_key)
        )
    st.session_state.setdefault("monitor_log_file", "")
    st.session_state.setdefault("monitor_log_filter", "All")
    if st.session_state["monitor_log_filter"] not in hhs_ui.LOG_FILTERS:
        st.session_state["monitor_log_filter"] = "All"
    st.session_state.setdefault("monitor_log_other_filter", "")
    st.session_state.setdefault("monitor_log_level", "ALL_LEVELS")
    st.session_state["monitor_log_level"] = selected_monitor_log_level()
    st.session_state.setdefault("monitor_logs_tail", True)
    st.session_state.setdefault("alias_filter", "All")
    if st.session_state["alias_filter"] not in hhs_ui.LIST_FILTERS:
        st.session_state["alias_filter"] = "All"
    st.session_state.setdefault("path_filter", "All")
    if st.session_state["path_filter"] not in hhs_ui.PATH_FILTERS:
        st.session_state["path_filter"] = "All"
    st.session_state.setdefault("dirs_filter", "All")
    if st.session_state["dirs_filter"] not in hhs_ui.LIST_FILTERS:
        st.session_state["dirs_filter"] = "All"
    st.session_state.setdefault("cmds_filter", "All")
    if st.session_state["cmds_filter"] not in hhs_ui.LIST_FILTERS:
        st.session_state["cmds_filter"] = "All"
    st.session_state.setdefault("service_filter", "All")
    if st.session_state["service_filter"] == "Started":
        st.session_state["service_filter"] = "Up"
    elif st.session_state["service_filter"] == "Stopped":
        st.session_state["service_filter"] = "Down"
    if st.session_state["service_filter"] not in hhs_ui.SERVICE_FILTERS:
        st.session_state["service_filter"] = "All"
    st.session_state.setdefault("history_commands_filter", "All")
    if st.session_state["history_commands_filter"] not in hhs_ui.HISTORY_FILTERS:
        st.session_state["history_commands_filter"] = "All"
    st.session_state.setdefault("history_directories_filter", "All")
    if st.session_state["history_directories_filter"] not in hhs_ui.HISTORY_FILTERS:
        st.session_state["history_directories_filter"] = "All"
    st.session_state.setdefault("history_stats_top_n", 10)
    if not isinstance(st.session_state["history_stats_top_n"], int):
        st.session_state["history_stats_top_n"] = 10
    execute_pending_dialog_callback()
    apply_pending_folder_picker_selection()
    render_sidebar()
    render_main_view()
    render_folder_picker_dialog()
    render_footer()
    render_floating_status()
    render_browser_cleanup_script()


if __name__ == "__main__":
    main()
