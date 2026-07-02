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
import hashlib
import html
import importlib
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from base64 import b64encode
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
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

UPDATER_CHECK_INTERVAL_SECONDS = 7 * 24 * 60 * 60
FLOATING_STATUS_QUEUE_KEY = "_hhs_floating_status_queue"
FLOATING_STATUS_LEGACY_KEY = "_hhs_floating_status"
FLOATING_STATUS_QUEUE_LIMIT = 20
FOOTER_REMOTE_WORKING_DIR_KEY = "_hhs_footer_remote_working_dir"
FOOTER_LOCAL_WORKING_DIR_KEY = "_hhs_footer_local_working_dir"
TABLE_SELECTION_SNAPSHOT_KEY = "_hhs_table_selection_snapshots"
COMMAND_RESULT_SNAPSHOT_KEY = "_hhs_command_result_snapshots"
COMMAND_RESULT_SNAPSHOT_LIMIT = 100
TERMINAL_DIR_STACK_KEY = "_hhs_terminal_dir_stack"
TERMINAL_PREVIOUS_CWD_KEY = "_hhs_terminal_previous_cwd"
AI_CONTEXT_UPLOAD_TYPES = (
    "txt",
    "md",
    "markdown",
    "csv",
    "tsv",
    "json",
    "jsonl",
    "yaml",
    "yml",
    "toml",
    "ini",
    "conf",
    "cfg",
    "log",
    "xml",
    "html",
    "css",
    "js",
    "ts",
    "py",
    "sh",
    "bash",
    "zsh",
    "java",
    "kt",
    "go",
    "rs",
    "rb",
    "php",
    "sql",
)
RUN_SHELL_ENV_KEY = "RUN_SHELL"


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
    """Return the command that prints the resolved command shell version."""
    return f"{shlex.quote(RUN_SHELL)} --version"


RUN_SHELL = resolve_run_shell()
os.environ[RUN_SHELL_ENV_KEY] = RUN_SHELL
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


def selected_theme_custom_property(property_name: str, default: str = "") -> str:
    """Return a resolved custom property value from the selected HomeSetup UI theme."""
    selected_theme = st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    theme_properties = theme_custom_properties(selected_theme)
    property_value = theme_properties.get(property_name, default)
    visited_properties: set[str] = set()
    while True:
        variable_match = re.fullmatch(r"var\(\s*--([A-Za-z0-9_-]+)\s*\)", property_value)
        if not variable_match:
            return property_value
        referenced_property = variable_match.group(1)
        if (
            referenced_property in visited_properties
            or referenced_property not in theme_properties
        ):
            return default
        visited_properties.add(referenced_property)
        property_value = theme_properties[referenced_property]


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


def restore_terminal_document_view(was_terminal_active: bool) -> None:
    """Restore the Terminal document view after a host-scoped state reset."""
    if not was_terminal_active:
        return
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = True
    st.session_state[hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] = "Home"
    st.session_state[hhs_ui.DOCUMENT_SELECTED_KEY] = "TERMINAL"
    activate_terminal_document_view()


def close_document_view() -> None:
    """Close the document view and restore the previous main view."""
    previous_view = st.session_state.get(hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY, "Home")
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = False
    if previous_view in hhs_ui.VIEWS:
        st.session_state["active_view"] = previous_view
    save_ui_state()


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
    result = run_hhs_ask_reset(close_dialogs=True)
    cache_delete_tag("ai")
    st.session_state["ai_chat_messages"] = []
    st.session_state["ai_context_output"] = ""
    st.session_state["ai_context_error"] = ""
    st.session_state["ai_clear_chat_pending"] = False
    if result.returncode == 0:
        push_floating_status("AI chat history cleared.", "info")
    else:
        push_floating_status("Unable to clear AI chat history.", "error")
    save_ui_state()


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


def refresh_ai_prompt() -> None:
    """Fetch and store the backend ask prompt for the Context tab."""
    result = run_hhs_ask_prompt()
    output = result.stdout if result.returncode == 0 else result.stderr or result.stdout
    clean_output = strip_ansi(output or "").strip()
    st.session_state["ai_context_output"] = (
        clean_output or "No Ollama prompt available."
    )
    st.session_state["ai_context_error"] = (
        ""
        if result.returncode == 0
        else clean_output or "Unable to load Ollama prompt."
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
    if suffix.lstrip(".") in AI_CONTEXT_UPLOAD_TYPES:
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
    """Execute the pending Ollama model selection after dialogs are closed."""
    pending = st.session_state.get("ai_model_select_execute_pending") or {}
    new_model = str(pending.get("new", "")).strip()
    model_status = str(pending.get("status", "")).strip()
    if new_model:
        loader_message = (
            "Downloading model..." if not model_status else "Selecting Ollama model..."
        )
        result = run_hhs_ask_select_model(new_model, loader_message, close_dialogs=True)
        status_message = clean_command_status_message(
            result.stdout or result.stderr or ""
        )
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
            cache_delete_tag("ai_models")
            cache_delete_tag("ai")
            refresh_ai_model_listing()
            reset_ai_model_table_selection()
            push_floating_status(
                status_message or f"Selected AI model: {new_model}", "info"
            )
    st.session_state["ai_model_select_execute_pending"] = None
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
    """Execute the pending Ollama model deletion after dialogs are closed."""
    pending = st.session_state.get("ai_model_delete_execute_pending") or {}
    if isinstance(pending, str):
        pending = {"name": pending, "status": ""}
    model_name = str(pending.get("name", "")).strip()
    model_status = str(pending.get("status", "")).strip()
    if model_name:
        result = run_ollama_delete_model(model_name, close_dialogs=True)
        status_message = clean_command_status_message(
            result.stdout or result.stderr or ""
        )
        if result.returncode != 0:
            st.session_state["ai_model_delete_error"] = strip_ansi(
                status_message or "Unable to delete model."
            )
            push_floating_status(
                st.session_state["ai_model_delete_error"],
                "error",
            )
        else:
            st.session_state["ai_model_delete_error"] = ""
            cache_delete_tag("ai_models")
            cache_delete_tag("ai")
            model_result = refresh_ai_model_listing()
            push_floating_status(
                status_message or f"Deleted AI model: {model_name}", "info"
            )
            if model_status == "Active":
                fallback_model = first_downloaded_ollama_model(
                    model_result.stdout, excluded_model=model_name
                )
                if fallback_model:
                    fallback_result = run_hhs_ask_select_model(
                        fallback_model, close_dialogs=True
                    )
                    fallback_status = strip_ansi(
                        fallback_result.stdout or fallback_result.stderr or ""
                    ).strip()
                    if fallback_result.returncode != 0:
                        st.session_state["ai_model_delete_error"] = strip_ansi(
                            fallback_status or "Unable to select fallback model."
                        )
                        push_floating_status(
                            st.session_state["ai_model_delete_error"],
                            "error",
                        )
                    else:
                        cache_delete_tag("ai_models")
                        cache_delete_tag("ai")
                        refresh_ai_model_listing()
                        push_floating_status(
                            fallback_status
                            or f"Selected fallback AI model: {fallback_model}",
                            "info",
                        )
            reset_ai_model_table_selection()
    st.session_state["ai_model_delete_execute_pending"] = None
    save_ui_state()


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
        else:
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


def render_preloader(message: str = "Loading...", transient: bool = True) -> None:
    """Render a full-page overlay preloader."""
    render_footer_visibility_script(hidden=True)
    safe_message = html.escape(message)
    loader_class = (
        "hhs-tab-loader hhs-tab-loader-transient" if transient else "hhs-tab-loader"
    )
    st.markdown(
        f'<div class="{loader_class}">'
        '<div class="hhs-tab-loader-panel">'
        '<span class="hhs-tab-loader-spinner"></span>'
        '<span class="hhs-tab-loader-copy">'
        f'<span class="hhs-tab-loader-label">{safe_message}</span>'
        '<span class="hhs-tab-loader-elapsed" data-start-time="0">time elapsed: 0m:00s</span>'
        "</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    components.html(
        """
        <script>
          (() => {
            const elapsed_nodes = window.parent.document.querySelectorAll(".hhs-tab-loader-elapsed");
            elapsed_nodes.forEach((node) => {
              if (node.dataset.timerStarted === "true") {
                return;
              }
              node.dataset.timerStarted = "true";
              const started_at = Date.now();
              const render_elapsed = () => {
                const elapsed_seconds = Math.max(0, Math.floor((Date.now() - started_at) / 1000));
                const minutes = Math.floor(elapsed_seconds / 60);
                const seconds = String(elapsed_seconds % 60).padStart(2, "0");
                node.textContent = `time elapsed: ${minutes}m:${seconds}s`;
              };
              render_elapsed();
              window.setInterval(render_elapsed, 1000);
            });
          })();
        </script>
        """,
        height=0,
    )


def render_footer_visibility_script(hidden: bool) -> None:
    """Hide or restore the already-mounted footer in the browser document."""
    class_action = "add" if hidden else "remove"
    sequence_key = "_hhs_footer_visibility_sequence"
    sequence = st.session_state.setdefault(sequence_key, 0)
    if not isinstance(sequence, int):
        sequence = 0
    sequence += 1
    st.session_state[sequence_key] = sequence
    retry_script = (
        """
            if (!hidden) {
              [0, 50, 150, 300, 600].forEach((delay) => {
                window.setTimeout(apply_visibility, delay);
              });
              window.requestAnimationFrame(apply_visibility);
            }
        """
        if not hidden
        else ""
    )
    components.html(
        f"""
        <script>
          (() => {{
            const doc = window.parent.document;
            const sequence = {sequence};
            const hidden = {str(hidden).lower()};
            const apply_visibility = () => {{
              const current_sequence = Number(doc.documentElement.dataset.hhsFooterVisibilitySequence || "0");
              if (sequence < current_sequence) {{
                return;
              }}
              doc.documentElement.dataset.hhsFooterVisibilitySequence = String(sequence);
              doc.documentElement.classList.{class_action}("hhs-footer-hidden");
              doc.querySelectorAll(".hhs-app-footer").forEach((footer) => {{
                footer.style.visibility = "";
                footer.style.opacity = "";
                footer.style.pointerEvents = "";
              }});
            }};
            apply_visibility();
            {retry_script}
          }})();
        </script>
        """,
        height=0,
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
) -> None:
    """Show or hide the reusable full-page command overlay."""
    placeholder_key = "_hhs_overlay_placeholder"
    if active:
        if close_dialogs:
            close_all_dialogs()
        save_ui_state()
        placeholder = st.empty()
        st.session_state[placeholder_key] = placeholder
        with placeholder.container():
            render_preloader(message, transient=transient)
        time.sleep(0.1)
        return

    placeholder = st.session_state.pop(placeholder_key, None)
    if placeholder is not None:
        placeholder.empty()
    render_footer_visibility_script(hidden=False)


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


def folder_picker_label(directory: str) -> str:
    """Return the display label for a folder picker option."""
    path = Path(directory)
    return path.name or str(path)


def request_folder_picker(
    target_key: str,
    fallback_value: str = "",
) -> None:
    """Open the folder picker for a Streamlit input key."""
    current_value = str(st.session_state.get(target_key, "") or fallback_value)
    start_directory = folder_picker_start_directory(current_value)
    st.session_state["_hhs_folder_picker_open"] = True
    st.session_state["_hhs_folder_picker_target_key"] = target_key
    st.session_state["_hhs_folder_picker_current_dir"] = start_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = start_directory
    st.session_state.setdefault("_hhs_folder_picker_include_dot_folders", False)
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def close_folder_picker() -> None:
    """Close the folder picker dialog and clear transient selection state."""
    st.session_state["_hhs_folder_picker_open"] = False
    st.session_state.pop("_hhs_folder_picker_target_key", None)
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def set_folder_picker_current_directory(directory: str) -> None:
    """Set the folder picker current directory."""
    selected_directory = folder_picker_start_directory(directory)
    st.session_state["_hhs_folder_picker_current_dir"] = selected_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = selected_directory
    include_dot_folders = bool(
        st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
    )
    child_directories = folder_picker_child_directories(
        selected_directory, include_dot_folders
    )
    if child_directories:
        st.session_state["_hhs_folder_picker_selected_dir"] = child_directories[0]
    else:
        st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def apply_folder_picker_typed_directory() -> None:
    """Apply the manually typed folder picker directory."""
    set_folder_picker_current_directory(
        str(st.session_state.get("_hhs_folder_picker_current_dir_input", ""))
    )


def open_folder_picker_parent() -> None:
    """Move the folder picker to the parent directory."""
    current_directory = Path(
        folder_picker_start_directory(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
    )
    set_folder_picker_current_directory(str(current_directory.parent))


def open_folder_picker_selected_directory() -> None:
    """Move the folder picker into the selected child directory."""
    selected_directory = str(
        st.session_state.get("_hhs_folder_picker_selected_dir", "")
    )
    if selected_directory:
        set_folder_picker_current_directory(selected_directory)


def apply_folder_picker_selection() -> None:
    """Assign the selected folder to the target Streamlit input key."""
    target_key = str(st.session_state.get("_hhs_folder_picker_target_key", ""))
    if target_key:
        st.session_state[target_key] = folder_picker_start_directory(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
    close_folder_picker()


def render_folder_picker_dialog() -> bool:
    """Render the visual folder picker dialog when requested."""
    if not st.session_state.get("_hhs_folder_picker_open"):
        return False

    def render_body() -> None:
        """Render the visual folder picker controls."""
        current_directory = folder_picker_start_directory(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
        st.text_input(
            "Folder",
            key="_hhs_folder_picker_current_dir_input",
            on_change=apply_folder_picker_typed_directory,
        )
        include_dot_folders = bool(
            st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
        )
        child_directories = folder_picker_child_directories(
            current_directory, include_dot_folders
        )
        selected_directory = st.session_state.get("_hhs_folder_picker_selected_dir")
        if selected_directory not in child_directories:
            st.session_state.pop("_hhs_folder_picker_selected_dir", None)
        if child_directories:
            st.selectbox(
                "Folders",
                child_directories,
                key="_hhs_folder_picker_selected_dir",
                format_func=folder_picker_label,
            )
        else:
            st.caption("No child folders.")
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
                on_click=apply_folder_picker_selection,
                width="stretch",
            )
            st.button(
                "ﰸ",
                key="folder_picker_cancel_button",
                help="Cancel",
                on_click=close_folder_picker,
                width="stretch",
            )

    return pop_dialog(
        title="Select folder",
        body=render_body,
        buttons=(),
        close_callback=close_folder_picker,
    )


def homesetup_version() -> str:
    """Return the cached HomeSetup product version from the shell environment."""
    refresh_cache = not bool(st.session_state.get("footer_hhs_version_cache_loaded"))
    result = run_hhs_envs("^HHS_VERSION$", refresh_cache=refresh_cache)
    st.session_state["footer_hhs_version_cache_loaded"] = True
    if result.returncode == 0:
        for row in parse_hhs_envs(result.stdout):
            if row["Name"] == "HHS_VERSION" and row["Value"]:
                return row["Value"]
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
        os.environ.get("HHS_OLLAMA_HISTORY_FILE", homesetup_config_dir() / ".ollama_history")
    ).expanduser()


def ollama_prompt_file() -> Path:
    """Return the configured HomeSetup Ollama prompt file path."""
    return Path(
        os.environ.get("HHS_OLLAMA_PROMPT_FILE", homesetup_config_dir() / "hhs-ask-ollama.md")
    ).expanduser()


def monitor_default_disk_directory() -> str:
    """Return the default directory for the disk monitor."""
    return str(homesetup_home())


def normalized_monitor_disk_top_n(value: object) -> int:
    """Return a valid monitor disk Top N value."""
    try:
        top_n = int(value)
    except (TypeError, ValueError):
        return 10
    if top_n < 1 or top_n > 100:
        return 10
    return top_n


def handle_monitor_disk_top_n_change() -> None:
    """Persist the pending monitor disk Top N widget value."""
    st.session_state["monitor_disk_top_n_input"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n_input")
    )
    save_ui_state()


def apply_monitor_disk_controls() -> None:
    """Apply pending disk monitor controls before the next command refresh."""
    directory = str(st.session_state.get("monitor_disk_directory", "")).strip()
    st.session_state["monitor_disk_directory_applied"] = (
        directory or monitor_default_disk_directory()
    )
    st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n_input")
    )
    cache_delete_tag("monitor_disk")
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


def apply_monitor_process_filter() -> None:
    """Apply the pending process monitor filter before the next command refresh."""
    st.session_state["monitor_process_filter_applied"] = str(
        st.session_state.get("monitor_process_filter", "")
    ).strip()
    cache_delete_tag("monitor_process")
    save_ui_state()


def applied_monitor_process_filter() -> str:
    """Return the process filter currently applied to the monitor command."""
    return str(
        st.session_state.get(
            "monitor_process_filter_applied",
            st.session_state.get("monitor_process_filter", ""),
        )
    ).strip()


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
    persisted_theme = validated_theme_name(
        load_ui_state().get(hhs_ui.THEME_SELECTED_KEY, "")
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
    del status_queue[:-FLOATING_STATUS_QUEUE_LIMIT]
    st.session_state[FLOATING_STATUS_QUEUE_KEY] = status_queue


def normalize_floating_status_kind(kind: str) -> str:
    """Return a supported floating status kind from a user-facing alias."""
    kind_aliases = {"success": "info", "warning": "warn"}
    clean_kind = kind_aliases.get(kind, kind)
    if clean_kind not in {"info", "warn", "error"}:
        clean_kind = "info"
    return clean_kind


def floating_status_queue() -> list[dict[str, object]]:
    """Return the floating status queue, migrating legacy single-message state."""
    queue = st.session_state.get(FLOATING_STATUS_QUEUE_KEY)
    if not isinstance(queue, list):
        queue = []
    legacy_status = st.session_state.pop(FLOATING_STATUS_LEGACY_KEY, None)
    if isinstance(legacy_status, dict):
        queue.append(legacy_status)
    normalized_queue = [item for item in queue if isinstance(item, dict)]
    st.session_state[FLOATING_STATUS_QUEUE_KEY] = normalized_queue
    return normalized_queue


def pop_floating_status() -> dict[str, object] | None:
    """Remove and return the oldest queued floating status message."""
    queue = floating_status_queue()
    if not queue:
        return None
    status = queue.pop(0)
    st.session_state[FLOATING_STATUS_QUEUE_KEY] = queue
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
            st.session_state[FLOATING_STATUS_QUEUE_KEY] = queue
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
    if shell_name:
        shell_status_markup = (
            f'<a class="hhs-footer-shell-status" href="{shell_version_url}" '
            f'target="_self" title="Show bash version" aria-label="Show bash version">'
            f'<span class="hhs-footer-glyph"></span>'
            f'<span class="hhs-footer-shell-name">{shell_name}</span></a>'
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
    status_group_markup = (
        f'<span class="hhs-footer-status-group">'
        f"{remote_status_markup}{shell_status_markup}"
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


def query_param_requested(name: str) -> bool:
    """Return whether a Streamlit query parameter was requested."""
    value = st.query_params.get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).lower() in {"1", "true", "yes"}


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
    title = str(
        st.session_state.get("footer_shell_version_dialog_title", "")
    ).strip()
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


def handle_footer_actions() -> None:
    """Run footer actions requested through Streamlit query parameters."""
    if query_param_requested(hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM)
        result = run_shell_version()
        output = strip_ansi(result.stdout or result.stderr or "").strip()
        st.session_state["footer_shell_version_dialog_title"] = "Shell version"
        st.session_state["footer_shell_version_output"] = (
            output or "bash --version returned no output."
        )

    if query_param_requested(hhs_ui.FOOTER_RUN_UPDATER_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_RUN_UPDATER_QUERY_PARAM)
        result = run_hhs_updater_update()
        output = strip_ansi(result.stdout or result.stderr or "").strip()
        if result.returncode != 0:
            message = output or "Unable to update HomeSetup."
            push_floating_status(message, "error")
            st.error(message)
        else:
            st.session_state["updater_last_check_epoch"] = time.time()
            st.session_state["updater_last_check_output"] = (
                output or "HomeSetup update command completed."
            )
            st.session_state["updater_update_available"] = False
            cache_delete_tag("env")
            st.session_state["footer_hhs_version_cache_loaded"] = False
            save_ui_state()
            push_floating_status("HomeSetup update command completed.", "info")

    if query_param_requested(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM):
        remove_query_param(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM)
        result = run_open_working_directory()
        if result.returncode != 0:
            message = result.stderr or "Unable to open working directory."
            push_floating_status(message, "error")
            st.error(message)
        else:
            push_floating_status("Opened working directory.", "info")


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
    if home_view != "Docker":
        st.write("")
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
    result = run_hhs_sysinfo()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to load system information.")
        return
    st.markdown(format_hhs_sysinfo_markdown(result.stdout))


def render_home_docker_panel() -> None:
    """Render Docker container and image listings on the Home view."""
    if not docker_agent_is_running():
        render_docker_agent_required_view()
        return
    with st.expander("All Containers", expanded=True):
        render_docker_container_table(run_docker_ps())
    with st.expander("Available Images", expanded=True):
        render_docker_image_table(run_docker_images())


def render_docker_agent_required_view() -> None:
    """Render an empty Docker panel when the Docker daemon is unavailable."""
    st.markdown(
        """
        <section class="hhs-remote-connect-required">
          <h2>Docker agent is not running</h2>
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


def selected_item_editing_key(table_key: str | None, selected_index: int) -> str:
    """Return the session key for a selected table row edit mode."""
    safe_key = table_key or "hhs_table"
    return f"{safe_key}_selected_editing_{selected_index}"


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
    snapshots = st.session_state.setdefault(TABLE_SELECTION_SNAPSHOT_KEY, {})
    if not isinstance(snapshots, dict):
        snapshots = {}
        st.session_state[TABLE_SELECTION_SNAPSHOT_KEY] = snapshots
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
        dataframe_args["on_select"] = "rerun"
        dataframe_args["selection_mode"] = "single-row"

    selection = st.dataframe(rendered_data, **dataframe_args)
    if checkbox:
        remember_table_selection(key, selection)
    if not checkbox:
        return None, None

    selected_rows = selection.selection.rows if selection else []
    if not selected_rows or selected_rows[0] >= len(rows):
        if empty_hint:
            st.caption(empty_hint)
        return None, None

    selected_index = selected_rows[0]
    selected_row = rows[selected_index]
    visible_selected_actions = selected_table_actions(
        selected_action_buttons or [], selected_row, selected_index, reset_selection
    )
    if action_hint:
        st.caption(action_hint)
    if selected_label is not None:
        label = selected_label(selected_row, selected_index)
        selected_item_label, selected_item_value = selected_label_parts(label)
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
            edit_args=table_edit_args(selected_edit_args, selected_row, selected_index),
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
        weights = action_column_weights or [1.0] * len(visible_actions)
        columns = st.columns(weights)
        for column, action in zip(columns, visible_actions):
            label = str(action["label"])
            key_prefix = str(action.get("key_prefix", label.lower().replace(" ", "_")))
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
        [*columns, 0.18], vertical_alignment="bottom", gap="small"
    )
    with filter_col:
        selected_filter = st.radio(
            "Filters",
            options,
            horizontal=True,
            index=index,
            key=key,
            on_change=handle_monitor_disk_top_n_change,
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
    with st.form(f"{key_prefix}_add_form", border=False):
        if value_folder_picker:
            name_col, value_col, _spacer_col, folder_col = st.columns(
                [1.25, 4.05, 0.012, 0.15], vertical_alignment="center"
            )
        else:
            name_col, value_col = st.columns([1.25, 4.2], vertical_alignment="center")
            folder_col = None
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
        if folder_col is not None:
            with folder_col:
                st.form_submit_button(
                    "",
                    key=f"{key_prefix}_folder_picker_button",
                    help="Select folder",
                    on_click=request_folder_picker,
                    args=(f"{key_prefix}_add_value", value_placeholder),
                    width="stretch",
                )
        st.form_submit_button(
            "Add",
            key=f"{key_prefix}_add_submit",
            on_click=on_submit,
        )


def render_value_add_controls(
    key_prefix: str,
    value_label: str,
    value_placeholder: str,
    on_submit: Callable[[], None],
    value_folder_picker: bool = False,
) -> None:
    """Render an Enter-submitted Value control for a config listing."""
    with st.form(f"{key_prefix}_add_form", border=False):
        if value_folder_picker:
            value_col, folder_col = st.columns([1, 0.035], vertical_alignment="center")
        else:
            value_col = st.container()
            folder_col = None
        with value_col:
            st.text_input(
                value_label,
                key=f"{key_prefix}_add_value",
                placeholder=value_placeholder,
            )
        if folder_col is not None:
            with folder_col:
                st.form_submit_button(
                    "",
                    key=f"{key_prefix}_folder_picker_button",
                    help="Select folder",
                    on_click=request_folder_picker,
                    args=(f"{key_prefix}_add_value", value_placeholder),
                    width="stretch",
                )
        st.form_submit_button(
            "Add",
            key=f"{key_prefix}_add_submit",
            on_click=on_submit,
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

    result = run_hhs_tools()
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to load tool checks.")
        return
    rows = parse_hhs_tools(result.stdout)
    if not rows:
        st.caption("No tool checks found.")
        return
    tools_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.LIST_FILTERS,
            "home_tools_filter",
            "home_tools_other_filter",
            hhs_ui.TWO_OPTION_FILTER_COLUMNS,
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
    result = run_hhs_shopt()
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to load shell options.")
        return
    rows = parse_hhs_shopt(result.stdout)
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
    title, document = document_details(
        document_key
    )
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
    """Render the line-oriented xterm.js terminal document view."""
    title = terminal_document_title()
    st.markdown(
        f"""
        <section class="hhs-view-heading">
          <h2> {html.escape(title)}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    initialize_terminal_session_state()
    terminal_event = render_terminal_component(
        transcript=str(st.session_state[hhs_ui.TERMINAL_TRANSCRIPT_KEY]),
        prompt=terminal_prompt(str(st.session_state[hhs_ui.TERMINAL_CWD_KEY])),
        history=list(st.session_state[hhs_ui.TERMINAL_COMMAND_HISTORY_KEY]),
        reset_counter=terminal_reset_counter(),
        height=0,
    )
    handle_terminal_event(terminal_event)


def terminal_document_title() -> str:
    """Return the terminal document title for local or SSH-connected sessions."""
    if str(st.session_state.get("ssh_connection_status", "")).strip() == "connected":
        return "Remote Terminal"
    return "Terminal"


def hhs_terminal_component(**kwargs: object) -> object:
    """Render the HomeSetup terminal custom component and return its value."""
    component = components.declare_component(
        "hhs_terminal", path=str(hhs_ui.TERMINAL_COMPONENT_DIR)
    )
    return component(**kwargs)


def render_terminal_component(
    transcript: str, prompt: str, history: list[str], reset_counter: int, height: int
) -> dict[str, object] | None:
    """Render the xterm.js terminal component and return submitted command events."""
    value = hhs_terminal_component(
        transcript=transcript,
        prompt=prompt,
        history=history,
        resetCounter=reset_counter,
        height=height,
        borderColor=selected_theme_custom_property("hhs-theme-heading-border-color"),
        key="hhs_terminal_component",
        default=None,
    )
    return value if isinstance(value, dict) else None


def initialize_terminal_session_state() -> None:
    """Initialize terminal transcript, working directory, and command history."""
    restored_transcript = load_terminal_transcript()
    st.session_state.setdefault(hhs_ui.TERMINAL_TRANSCRIPT_KEY, restored_transcript)
    st.session_state.setdefault(hhs_ui.TERMINAL_CWD_KEY, footer_working_directory())
    st.session_state.setdefault(hhs_ui.TERMINAL_COMMAND_HISTORY_KEY, [])
    st.session_state.setdefault(hhs_ui.TERMINAL_LAST_EVENT_ID_KEY, "")
    st.session_state.setdefault(hhs_ui.TERMINAL_RESET_COUNTER_KEY, 0)
    if not bool(st.session_state.get(hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY, False)):
        push_floating_status(terminal_ready_status_message(restored_transcript), "info")
        st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = True


def terminal_reset_counter() -> int:
    """Return the terminal reset counter as a valid integer."""
    reset_counter = st.session_state.setdefault(hhs_ui.TERMINAL_RESET_COUNTER_KEY, 0)
    if isinstance(reset_counter, int):
        return reset_counter
    st.session_state[hhs_ui.TERMINAL_RESET_COUNTER_KEY] = 0
    return 0


def terminal_ready_status_message(restored_transcript: str) -> str:
    """Return the terminal ready status message for a fresh or restored session."""
    if restored_transcript:
        return "HomeSetup terminal ready. Session restored."
    return "HomeSetup terminal ready."


def terminal_prompt(cwd: str) -> str:
    """Return the visible terminal prompt for the current working directory."""
    home = str(Path.home())
    display_cwd = "~" if cwd == home else cwd.replace(f"{home}/", "~/", 1)
    return f"{display_cwd} $ "


def terminal_command_tokens(command: str) -> list[str]:
    """Return shell-like tokens for a standalone terminal command."""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def terminal_command_is_standalone(command: str) -> bool:
    """Return whether a command can be safely pre-applied without changing semantics."""
    return not bool(re.search(r"(?:&&|\|\||[;&|<>`])", command))


def terminal_directory_target_is_static(target: str) -> bool:
    """Return whether a directory target can be resolved without shell evaluation."""
    return not bool(re.search(r"[$*?\[\]{}()!]", target))


def resolve_terminal_directory_target(target: str, cwd: str) -> str | None:
    """Resolve a static directory target against the current terminal cwd."""
    clean_target = target.strip()
    if not clean_target:
        return str(Path.home()) if not connected_ssh_host() else None
    if clean_target == "~" or clean_target.startswith("~/"):
        if connected_ssh_host():
            return None
        clean_target = str(Path.home()) + clean_target[1:]
    if not terminal_directory_target_is_static(clean_target):
        return None
    if os.path.isabs(clean_target):
        return os.path.normpath(clean_target)
    return os.path.normpath(os.path.join(cwd, clean_target))


def local_terminal_directory_is_valid(path: str) -> bool:
    """Return whether a local predicted terminal directory exists."""
    return connected_ssh_host() or os.path.isdir(path)


def terminal_directory_stack() -> list[str]:
    """Return the terminal directory stack used to predict pushd/popd effects."""
    stack = st.session_state.setdefault(TERMINAL_DIR_STACK_KEY, [])
    if not isinstance(stack, list):
        stack = []
        st.session_state[TERMINAL_DIR_STACK_KEY] = stack
    return [str(path) for path in stack]


def set_terminal_directory_stack(stack: list[str]) -> None:
    """Persist the terminal directory stack."""
    st.session_state[TERMINAL_DIR_STACK_KEY] = stack


def update_terminal_working_directory(cwd: str) -> None:
    """Update terminal and footer working directory state."""
    clean_cwd = cwd.strip()
    if not clean_cwd:
        return
    st.session_state[hhs_ui.TERMINAL_CWD_KEY] = clean_cwd
    if connected_ssh_host():
        st.session_state[FOOTER_REMOTE_WORKING_DIR_KEY] = clean_cwd
    else:
        st.session_state[FOOTER_LOCAL_WORKING_DIR_KEY] = clean_cwd


def predicted_terminal_directory(command: str, cwd: str) -> str | None:
    """Return a pre-send cwd prediction for standalone directory mutations."""
    if not terminal_command_is_standalone(command):
        return None
    tokens = terminal_command_tokens(command)
    if not tokens:
        return None
    operation = tokens[0]
    if operation == "dirs" and tokens[1:] == ["-c"]:
        set_terminal_directory_stack([])
        return cwd
    if operation == "cd":
        target = tokens[1] if len(tokens) > 1 else ""
        if target == "-":
            previous_cwd = str(st.session_state.get(TERMINAL_PREVIOUS_CWD_KEY, ""))
            if not previous_cwd:
                return None
            target_cwd = previous_cwd
        else:
            target_cwd = resolve_terminal_directory_target(target, cwd)
        if target_cwd and local_terminal_directory_is_valid(target_cwd):
            st.session_state[TERMINAL_PREVIOUS_CWD_KEY] = cwd
            return target_cwd
        return None
    if operation == "pushd":
        stack = terminal_directory_stack()
        if len(tokens) > 1 and re.fullmatch(r"[+-]\d+", tokens[1]):
            return None
        if len(tokens) == 1:
            if not stack:
                return None
            target_cwd = stack[0]
            set_terminal_directory_stack([cwd, *stack[1:]])
            st.session_state[TERMINAL_PREVIOUS_CWD_KEY] = cwd
            return target_cwd
        target_cwd = resolve_terminal_directory_target(tokens[1], cwd)
        if target_cwd and local_terminal_directory_is_valid(target_cwd):
            set_terminal_directory_stack([cwd, *stack])
            st.session_state[TERMINAL_PREVIOUS_CWD_KEY] = cwd
            return target_cwd
        return None
    if operation == "popd":
        if len(tokens) > 1:
            return None
        stack = terminal_directory_stack()
        if not stack:
            return None
        target_cwd = stack[0]
        set_terminal_directory_stack(stack[1:])
        st.session_state[TERMINAL_PREVIOUS_CWD_KEY] = cwd
        return target_cwd
    return None


def handle_terminal_event(event: dict[str, object] | None) -> None:
    """Execute a submitted terminal command when the component emits a new event."""
    if not event:
        return
    event_id = str(event.get("eventId", ""))
    command = str(event.get("command", ""))
    if not event_id or event_id == st.session_state[hhs_ui.TERMINAL_LAST_EVENT_ID_KEY]:
        return
    st.session_state[hhs_ui.TERMINAL_LAST_EVENT_ID_KEY] = event_id
    execute_terminal_command(command)
    st.rerun()


def sendToTerminal(command: str) -> None:
    """Send a command to the Terminal panel and execute it."""
    initialize_terminal_session_state()
    execute_terminal_command(command)


def execute_terminal_command(command: str) -> None:
    """Execute a terminal command and append its output to the transcript."""
    clean_command = command.strip()
    if clean_command in {"clear", "cls", "reset"}:
        clear_terminal_transcript()
        return
    if not clean_command:
        cwd = str(st.session_state[hhs_ui.TERMINAL_CWD_KEY])
        append_terminal_transcript(f"{terminal_prompt(cwd)}\n")
        return

    history = st.session_state.setdefault(hhs_ui.TERMINAL_COMMAND_HISTORY_KEY, [])
    if isinstance(history, list):
        history.append(command)
    cwd = str(st.session_state[hhs_ui.TERMINAL_CWD_KEY])
    predicted_cwd = predicted_terminal_directory(command, cwd)
    if predicted_cwd:
        update_terminal_working_directory(predicted_cwd)
    prompt = terminal_prompt(cwd)
    result = run_terminal_command(command, cwd)
    stdout, next_cwd = parse_terminal_command_stdout(result.stdout, cwd)
    output = format_terminal_command_output(result, stdout)
    update_terminal_working_directory(next_cwd)
    append_terminal_transcript(f"{prompt}{command}\n{output}")


def append_terminal_transcript(value: str) -> None:
    """Append text to the terminal transcript."""
    transcript = str(st.session_state.get(hhs_ui.TERMINAL_TRANSCRIPT_KEY, ""))
    st.session_state[hhs_ui.TERMINAL_TRANSCRIPT_KEY] = truncate_terminal_transcript(
        transcript + value
    )
    save_terminal_transcript(str(st.session_state[hhs_ui.TERMINAL_TRANSCRIPT_KEY]))


def truncate_terminal_transcript(value: str) -> str:
    """Return a transcript constrained to the terminal buffer size."""
    if len(value) <= hhs_ui.TERMINAL_TRANSCRIPT_MAX_CHARS:
        return value
    return value[-hhs_ui.TERMINAL_TRANSCRIPT_MAX_CHARS :]


def load_terminal_transcript() -> str:
    """Load the persisted terminal transcript buffer."""
    try:
        return truncate_terminal_transcript(
            hhs_ui.TERMINAL_LOG_FILE.read_text(encoding="utf-8")
        )
    except OSError:
        return ""


def save_terminal_transcript(value: str) -> None:
    """Persist the terminal transcript buffer."""
    try:
        hhs_ui.TERMINAL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        hhs_ui.TERMINAL_LOG_FILE.write_text(
            truncate_terminal_transcript(value), encoding="utf-8"
        )
    except OSError:
        return


def clear_terminal_transcript() -> None:
    """Clear the terminal transcript session state and persisted buffer."""
    st.session_state[hhs_ui.TERMINAL_TRANSCRIPT_KEY] = ""
    st.session_state[hhs_ui.TERMINAL_RESET_COUNTER_KEY] = terminal_reset_counter() + 1
    try:
        hhs_ui.TERMINAL_LOG_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    push_floating_status("Session was reset", "info")


def build_terminal_command(command: str, cwd: str) -> str:
    """Build a Bash command that runs a line-oriented terminal command."""
    return "\n".join(
        (
            'export HHS_HOME="${HHS_HOME}";',
            'export HHS_DIR="${HHS_DIR}";',
            'export TERM="${TERM:-xterm-256color}";',
            'export PS1="${PS1:-\\u@\\h:\\w\\$ }";',
            "shopt -s expand_aliases;",
            "shopt -s checkwinsize 2>/dev/null || true;",
            'if [[ -s "${HOME}/.hhsrc" ]]; then',
            'source "${HOME}/.hhsrc" >/dev/null 2>&1 || true;',
            'elif [[ -n "${HHS_HOME:-}" && -s "${HHS_HOME}/dotfiles/bash/bash_commons.bash" ]]; then',
            'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash" >/dev/null 2>&1 || true;',
            'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash" >/dev/null 2>&1 || true;',
            'source "${HHS_HOME}/dotfiles/bash/bash_env.bash" >/dev/null 2>&1 || true;',
            'source "${HHS_HOME}/dotfiles/bash/bash_functions.bash" >/dev/null 2>&1 || true;',
            'source "${HHS_HOME}/dotfiles/bash/bash_aliases.bash" >/dev/null 2>&1 || true;',
            "fi;",
            f"cd {shlex.quote(cwd)} 2>/dev/null || cd \"${{HOME}}\";",
            "__hhs_terminal_status=0;",
            f"{{ {command}; }} || __hhs_terminal_status=$?;",
            'printf "\\n__HHS_TERMINAL_CWD__%s\\n" "$PWD";',
            'exit "${__hhs_terminal_status}";',
        )
    )


def run_terminal_command(
    command: str, cwd: str
) -> subprocess.CompletedProcess[str]:
    """Run a terminal command through the existing HomeSetup command runner."""
    return run_bash_command(
        build_terminal_command(command, cwd),
        "Running terminal command...",
        ttl_seconds=0,
        use_cache=False,
        timeout_seconds=120,
        cache_tag="terminal",
    )


def parse_terminal_command_stdout(stdout: str, fallback_cwd: str) -> tuple[str, str]:
    """Return terminal stdout with the cwd marker removed."""
    next_cwd = fallback_cwd
    output_lines: list[str] = []
    for line in stdout.splitlines():
        if line.startswith("__HHS_TERMINAL_CWD__"):
            next_cwd = line.removeprefix("__HHS_TERMINAL_CWD__").strip() or fallback_cwd
            continue
        if terminal_output_line_is_noise(line):
            continue
        output_lines.append(line)
    output = "\n".join(output_lines)
    if stdout.endswith("\n") and output:
        output += "\n"
    return output, next_cwd


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
    if re.fullmatch(r"(?:Shared )?Connection to .+ closed\.", clean_line, re.IGNORECASE):
        return True
    if re.fullmatch(r"Shared connection to .+ closed\.", clean_line, re.IGNORECASE):
        return True
    return False


def filter_terminal_output_noise(value: str) -> str:
    """Return terminal output without SSH/HomeSetup wrapper chatter lines."""
    lines = [
        line
        for line in value.splitlines()
        if not terminal_output_line_is_noise(line)
    ]
    output = "\n".join(lines)
    if value.endswith("\n") and output:
        output += "\n"
    return output


def format_terminal_command_output(
    result: subprocess.CompletedProcess[str], stdout: str
) -> str:
    """Return command output formatted for the terminal transcript."""
    output = stdout
    if result.stderr:
        output += filter_terminal_output_noise(
            strip_ssh_shared_connection_notice(result.stderr)
        )
    if result.returncode != 0:
        output += f"\n[exit {result.returncode}]\n"
    if output and not output.endswith("\n"):
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
    """Return whether the persisted updater check is missing or older than seven days."""
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
    return current_time - last_check_epoch >= UPDATER_CHECK_INTERVAL_SECONDS


def store_updater_check_result(result: subprocess.CompletedProcess[str]) -> None:
    """Persist the latest updater check output and update-availability flag."""
    output = strip_ansi(f"{result.stdout or ''}\n{result.stderr or ''}").strip()
    if not output:
        output = "No HomeSetup updater output."
    if result.returncode == 0:
        st.session_state["updater_last_check_epoch"] = time.time()
        st.session_state["updater_last_check_output"] = output
        st.session_state["updater_update_available"] = updater_output_has_updates(
            output
        )
        save_ui_state()
        return
    push_floating_status(output or "Unable to check HomeSetup updates.", "warn")


def execute_due_updater_check() -> None:
    """Run the updater check once when the persisted check state is stale."""
    if bool(st.session_state.get("updater_check_attempted", False)):
        return
    if not updater_check_due():
        return
    st.session_state["updater_check_attempted"] = True
    store_updater_check_result(run_hhs_updater_check())


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


def colorize_log_output(value: str) -> str:
    """Return log output highlighted with __hhs_tailor-compatible CSS classes."""
    clean_value = strip_ansi(value)
    ranges = log_tailor_highlight_ranges(clean_value)
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


def clean_hhs_ask_output(output: str) -> str:
    """Return user-facing ask output without terminal control decoration."""
    final_output = output
    for marker in ("\x1b[H\x1b[2J\x1b[3J", "\033[H\033[2J\033[3J"):
        if marker in final_output:
            final_output = final_output.rsplit(marker, 1)[-1]
    clean_output = strip_ansi(final_output)
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
    for row in parse_ollama_model_rows(output):
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
            for row in parse_ollama_model_rows(model_output, ollama_model)
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
    sample_counts = st.session_state.setdefault("ai_model_performance_sample_counts", {})
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
    if (
        model_sample_count == hhs_ui.AI_PERFORMANCE_MIN_SAMPLES
        or (
            model_sample_count > hhs_ui.AI_PERFORMANCE_MIN_SAMPLES
            and model_sample_count % hhs_ui.AI_PERFORMANCE_RECALC_INTERVAL == 0
        )
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
        index for index, header in enumerate(headers) if header not in omitted_column_names
    ]
    return (
        [headers[index] for index in kept_indexes],
        [[row[index] if index < len(row) else "" for index in kept_indexes] for row in rows],
    )


def docker_cli_table_rows(
    output: str, omitted_columns: tuple[str, ...] = ()
) -> list[dict[str, str]]:
    """Return Docker CLI table output as row dictionaries."""
    headers, rows = parse_fixed_width_cli_table(docker_cli_table_output(output))
    headers, rows = filter_markdown_table_columns(headers, rows, omitted_columns)
    return [
        {header: row[index] if index < len(row) else "" for index, header in enumerate(headers)}
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
        RUN_SHELL_ENV_KEY: RUN_SHELL,
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
    try:
        return hhs_ui.UI_SSH_CONNECTION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def register_ssh_connection(host: str) -> None:
    """Persist the UI-managed SSH connection host for later cleanup."""
    hhs_ui.UI_SSH_CONNECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    hhs_ui.UI_SSH_CONNECTION_FILE.write_text(f"{host.strip()}\n", encoding="utf-8")


def clear_registered_ssh_connection() -> None:
    """Remove the UI-managed SSH connection cleanup marker."""
    try:
        hhs_ui.UI_SSH_CONNECTION_FILE.unlink()
    except FileNotFoundError:
        return
    except OSError:
        return


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
    """Restore a registered SSH connection when a new Streamlit session starts."""
    if st.session_state.get("ssh_connection_restore_checked"):
        return
    st.session_state["ssh_connection_restore_checked"] = True
    host = registered_ssh_connection_host()
    if not host:
        return
    if not ssh_connection_is_alive(host):
        clear_disconnected_ssh_host(host)
        return
    st.session_state["ssh_connection_status"] = "connected"
    st.session_state["ssh_connection_host"] = host
    st.session_state["ssh_host_selected"] = host
    st.session_state["ssh_host_selector"] = host
    st.session_state["ssh_connection_error"] = ""
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
    st.session_state["ssh_connection_status"] = ""
    st.session_state["ssh_connection_host"] = ""
    st.session_state["ssh_connection_error"] = ""
    st.session_state["ssh_connect_pending"] = ""
    st.session_state["ssh_disconnect_pending"] = ""
    st.session_state["ssh_host_selected"] = local_hostname()
    st.session_state["ssh_host_selector"] = local_hostname()
    st.session_state.pop(FOOTER_REMOTE_WORKING_DIR_KEY, None)
    clear_registered_ssh_connection()
    cache_clear()
    save_ui_state()


def clear_host_scoped_session_state() -> None:
    """Clear UI state that belongs to the previously selected execution host."""
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
    reset_counter = terminal_reset_counter() + 1

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
    st.session_state[hhs_ui.TERMINAL_TRANSCRIPT_KEY] = ""
    st.session_state[hhs_ui.TERMINAL_CWD_KEY] = "."
    st.session_state[hhs_ui.TERMINAL_COMMAND_HISTORY_KEY] = []
    st.session_state[hhs_ui.TERMINAL_LAST_EVENT_ID_KEY] = ""
    st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = False
    st.session_state[hhs_ui.TERMINAL_RESET_COUNTER_KEY] = reset_counter
    try:
        hhs_ui.TERMINAL_LOG_FILE.unlink(missing_ok=True)
    except OSError:
        pass
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


def execute_pending_ssh_connection() -> None:
    """Open a pending SSH ControlMaster connection from the normal render flow."""
    host = str(st.session_state.get("ssh_connect_pending", "")).strip()
    if not host:
        return
    was_terminal_active = terminal_document_view_is_active()
    st.session_state["ssh_connect_pending"] = ""
    result = run_bash_command(
        build_ssh_connect_command(host),
        f"Connecting to SSH host {host}...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=15,
        cache_tag="ssh",
    )
    if result.returncode == 0:
        clear_host_scoped_session_state()
        st.session_state["ssh_connection_status"] = "connected"
        st.session_state["ssh_connection_host"] = host
        st.session_state["ssh_host_selected"] = host
        st.session_state["ssh_host_selector"] = host
        st.session_state["ssh_connection_error"] = ""
        st.session_state["ssh_connection_dialog_title"] = ""
        update_remote_footer_working_directory()
        restore_terminal_document_view(was_terminal_active)
        push_floating_status(
            f"Connected to remote  {ssh_connection_display(host)}",
            "info",
        )
        register_ssh_connection(host)
        save_ui_state()
    else:
        st.session_state["ssh_connection_status"] = "failed"
        st.session_state["ssh_connection_host"] = ""
        st.session_state["ssh_connection_error"] = strip_ansi(
            result.stderr or result.stdout or f"Unable to connect to SSH host {host}."
        )
        st.session_state["ssh_connection_dialog_title"] = f"Failed to connect to {host}"
        push_floating_status(f"Failed to connect to remote: {host}", "error")


def execute_pending_ssh_disconnection() -> None:
    """Close a pending SSH ControlMaster connection from the normal render flow."""
    host = str(st.session_state.get("ssh_disconnect_pending", "")).strip()
    if not host:
        return
    st.session_state["ssh_disconnect_pending"] = ""
    run_bash_command(
        build_ssh_disconnect_command(host),
        f"Disconnecting from SSH host {host}...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=10,
        cache_tag="ssh",
    )
    st.session_state["ssh_connection_status"] = ""
    st.session_state["ssh_connection_host"] = ""
    st.session_state["ssh_connection_error"] = ""
    st.session_state["ssh_connection_dialog_title"] = ""
    st.session_state["ssh_host_selected"] = local_hostname()
    st.session_state["ssh_host_selector"] = local_hostname()
    st.session_state.pop(FOOTER_REMOTE_WORKING_DIR_KEY, None)
    clear_registered_ssh_connection()
    cache_clear()
    save_ui_state()


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
    show_overlay: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a Bash command with tagged command-result caching and a preloader."""
    remote_host = command_remote_host(force_local=force_local)
    command_to_run = effective_bash_command(command, force_local=force_local)
    selection_only_rerun = table_selection_rerun_in_progress()
    show_command_overlay = show_overlay and not selection_only_rerun
    effective_timeout = timeout_seconds
    if effective_timeout is None and command_to_run != command:
        effective_timeout = 60
    cache_key = command_cache_key(command_to_run, cache_tag)
    snapshot_value = command_result_snapshot_get(cache_key) if selection_only_rerun else None
    if snapshot_value is not None:
        return completed_process_from_cache(command_to_run, snapshot_value)

    cached_value = cache_get(cache_key) if use_cache else None
    if use_cache and cached_value is not None:
        command_result_snapshot_set(cache_key, cached_value)
        result = completed_process_from_cache(command_to_run, cached_value)
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result

    if remote_host and not ssh_connection_is_alive(remote_host):
        result = completed_disconnected_ssh_process(command_to_run, remote_host)
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result

    if show_command_overlay:
        set_overlay(True, loader_message, close_dialogs=close_dialogs)
    try:
        result = subprocess.run(
            [RUN_SHELL, "-lc", command_to_run],
            capture_output=True,
            check=False,
            env=command_env(),
            text=True,
            timeout=effective_timeout,
        )
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
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result
    finally:
        if show_command_overlay:
            set_overlay(False)


def load_ui_cache() -> dict[str, dict[str, object]]:
    """Load the UI cache file and lazily prune expired entries."""
    global UI_CACHE_MEMORY, UI_CACHE_MEMORY_MTIME
    cache_mtime = ui_cache_mtime()
    if UI_CACHE_MEMORY_MTIME == cache_mtime:
        pruned_cache = prune_ui_cache_entries(UI_CACHE_MEMORY)
        if pruned_cache != UI_CACHE_MEMORY:
            save_ui_cache(pruned_cache)
        return pruned_cache
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
        if isinstance(key, str)
        and (key.startswith("command_hash:") or key.startswith("command_tag:"))
        and isinstance(value, dict)
    }
    pruned_cache = prune_ui_cache_entries(cache)
    if pruned_cache != cache or len(cache) != len(data):
        save_ui_cache(pruned_cache)
    else:
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


def prune_ui_cache_entries(
    cache: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Return cache entries whose TTL has not expired."""
    now = time.time()
    return {
        key: entry
        for key, entry in cache.items()
        if isinstance(entry.get("expires_at"), int | float)
        and float(entry["expires_at"]) > now
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
    snapshots = st.session_state.setdefault(COMMAND_RESULT_SNAPSHOT_KEY, {})
    if not isinstance(snapshots, dict):
        snapshots = {}
        st.session_state[COMMAND_RESULT_SNAPSHOT_KEY] = snapshots
    return snapshots


def command_result_snapshot_get(key: str) -> dict[str, object] | None:
    """Return the last in-session command result for a command cache key."""
    value = command_result_snapshots().get(key)
    return value if isinstance(value, dict) else None


def command_result_snapshot_set(key: str, value: dict[str, object]) -> None:
    """Store an in-session command result for fast selection-only reruns."""
    snapshots = command_result_snapshots()
    snapshots[key] = value
    while len(snapshots) > COMMAND_RESULT_SNAPSHOT_LIMIT:
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
    st.session_state[COMMAND_RESULT_SNAPSHOT_KEY] = {}


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
    save_ui_cache({})
    command_result_snapshot_clear()


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
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; return "${exit_code}"; }; '
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


def run_open_working_directory() -> subprocess.CompletedProcess[str]:
    """Open the current working directory in the operating system file explorer."""
    return run_bash_command(
        build_open_directory_command(os.getcwd()),
        "Opening working directory...",
        ttl_seconds=0,
        use_cache=False,
        cache_tag="system",
    )


def run_shell_version() -> subprocess.CompletedProcess[str]:
    """Run the local Bash version command used by the footer shell status."""
    return run_bash_command(
        shell_version_command(),
        "Checking shell version...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=10,
        cache_tag="system",
    )


def run_footer_working_directory() -> subprocess.CompletedProcess[str]:
    """Run the active host shell command used by the footer working-directory status."""
    return run_bash_command(
        build_footer_working_directory_command(),
        "Loading current working dir",
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
    """Capture the connected SSH host working directory for footer rendering."""
    result = run_footer_working_directory()
    output = parse_footer_working_directory_output(result.stdout or "")
    if output:
        st.session_state[FOOTER_REMOTE_WORKING_DIR_KEY] = output
    else:
        st.session_state.pop(FOOTER_REMOTE_WORKING_DIR_KEY, None)


def footer_working_directory() -> str:
    """Return the footer working directory from state or the local process cwd."""
    if str(st.session_state.get("ssh_connection_status", "")).strip() == "connected":
        remote_cwd = str(st.session_state.get(FOOTER_REMOTE_WORKING_DIR_KEY, "")).strip()
        if remote_cwd:
            return remote_cwd
    else:
        local_cwd = str(st.session_state.get(FOOTER_LOCAL_WORKING_DIR_KEY, "")).strip()
        if local_cwd:
            return local_cwd
    return os.getcwd()


def run_hhs_updater_check() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup updater check command locally."""
    return run_bash_command(
        build_hhs_updater_command("check"),
        "Checking HomeSetup updates...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=45,
        cache_tag="updater",
    )


def run_hhs_updater_update() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup updater update command locally."""
    return run_bash_command(
        build_hhs_updater_command("update"),
        "Updating HomeSetup...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=600,
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
        "\\shopt | awk '{print $1\" = \"$2}' >\"${HHS_SHOPTS_FILE}\"; "
        'fi; '
    )


def build_hhs_shopt_load_saved_command() -> str:
    """Build a Bash command that applies saved shell options to this process."""
    return (
        'if [[ -s "${HHS_SHOPTS_FILE}" ]]; then '
        'while IFS= read -r line; do '
        'if [[ "${line}" =~ ^([a-zA-Z0-9_]+)[[:space:]]*='
        '[[:space:]]*([Oo][Nn]|[Oo][Ff][Ff])$ ]]; then '
        'option="${BASH_REMATCH[1]}"; state="${BASH_REMATCH[2]}"; '
        'if [[ "${state}" =~ ^[Oo][Nn]$ ]]; then '
        'shopt -s "${option}" 2>/dev/null || true; '
        'else '
        'shopt -u "${option}" 2>/dev/null || true; '
        'fi; '
        'fi; '
        'done < "${HHS_SHOPTS_FILE}"; '
        'fi; '
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
    return "docker info >/dev/null 2>&1"


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
        if expanded_directory == str(hhs_home)
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
    return (
        'if [[ "$(uname -s)" == "Darwin" ]]; then '
        f"top -l 2 -s 1 -o {darwin_sort} -n {safe_top_n} 2>/dev/null || "
        f"ps -axo pid,user,%cpu,%mem,comm {ps_sort} 2>/dev/null | head -n {safe_top_n + 1}; "
        "else "
        f"top -b -n 1 -o {linux_sort} -w 512 2>/dev/null || "
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


def build_hhs_ask_prompt_command() -> str:
    """Build the Bash command used to show the main Ollama ask prompt."""
    return build_hhs_ask_execute_command(["-p"])


def build_hhs_ask_prompt_file_command() -> str:
    """Build the Bash command used to read the editable Ollama ask prompt file."""
    return build_hhs_ask_plugin_command(
        '[[ -r "${HHS_OLLAMA_PROMPT_FILE}" ]] || { '
        'echo "Ollama prompt file not found: ${HHS_OLLAMA_PROMPT_FILE}" >&2; '
        "exit 2; "
        "}; "
        'cat "${HHS_OLLAMA_PROMPT_FILE}"'
    )


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
        'function quit() { local exit_code=${1:-0}; shift; [[ $# -gt 0 ]] && echo -e "$*"; return "${exit_code}"; }; '
        'function __hhs() { if [[ "$1" == "services" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f'__hhs services execute "{safe_operation}" "{safe_service_name}"'
    )


def run_hhs_envs(
    prefix_filter: str | None, refresh_cache: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_envs HomeSetup function and return the completed process."""
    command = build_hhs_envs_command(prefix_filter)
    if refresh_cache:
        cache_delete_command(command, "env")
    return run_bash_command(
        command,
        "Loading environment variables...",
        cache_tag="env",
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


def run_hhs_sysinfo() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_sysinfo HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_sysinfo_command(),
        "Loading system information...",
        ttl_seconds=hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        cache_tag="system",
    )


def run_hhs_tools() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_tools HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_tools_command(),
        "Loading tool checks...",
        ttl_seconds=hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        cache_tag="tools",
    )


def run_hhs_shopt() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_shopt HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_shopt_command(),
        "Loading shell options...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="shopt",
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


def run_docker_ps() -> subprocess.CompletedProcess[str]:
    """Run docker ps and return the completed process."""
    return run_bash_command(
        build_docker_ps_command(),
        "Loading Docker containers...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        timeout_seconds=10,
        cache_tag="docker",
    )


def run_docker_images() -> subprocess.CompletedProcess[str]:
    """Run docker images and return the completed process."""
    return run_bash_command(
        build_docker_images_command(),
        "Loading Docker images...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        timeout_seconds=10,
        cache_tag="docker",
    )


def docker_agent_is_running() -> bool:
    """Return whether the Docker daemon responds on the selected host."""
    result = run_bash_command(
        build_docker_agent_check_command(),
        "Checking Docker agent...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        timeout_seconds=5,
        cache_tag="docker",
    )
    return result.returncode == 0


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


def run_hhs_tool_action(
    operation: str, tool_name: str
) -> subprocess.CompletedProcess[str]:
    """Run an hspm install or uninstall action for a Home tool."""
    return run_bash_command(
        build_hhs_hspm_command(operation, tool_name),
        f"Running hspm {operation} for {tool_name}...",
        use_cache=False,
        cache_tag="tools",
    )


def run_tool_tldr(tool_name: str) -> subprocess.CompletedProcess[str]:
    """Run tldr for the selected Home tool."""
    return run_bash_command(
        build_tool_tldr_command(tool_name),
        f"Loading TLDR for {tool_name}...",
        use_cache=False,
        cache_tag="tools",
    )


def run_hhs_history() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_history HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_history_command(),
        "Loading command history...",
        cache_tag="history",
    )


def run_hhs_history_dirs() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_dirs HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_history_dirs_command(),
        "Loading directory history...",
        cache_tag="history",
    )


def run_hhs_history_stats(top_n: int = 10) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_hist_stats HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_history_stats_command(top_n),
        "Loading history stats...",
        cache_tag="history",
    )


def run_hhs_disk_usage(
    directory: str, top_n: int = 10
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_du HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_disk_usage_command(directory, top_n),
        "Loading disk usage...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="monitor_disk",
    )


def run_process_monitor(
    metric: str, top_n: int = 10
) -> subprocess.CompletedProcess[str]:
    """Run the process monitor command and return the completed process."""
    return run_bash_command(
        build_process_monitor_command(metric, top_n),
        f"Loading {metric.lower()} usage...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="monitor_process",
    )


def run_hhs_process_list(process_filter: str) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup process list command and return the completed process."""
    return run_bash_command(
        build_hhs_process_list_command(process_filter),
        "Loading processes...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="monitor_process",
    )


def run_hhs_process_kill(process_name: str) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup process kill command and return the completed process."""
    return run_bash_command(
        build_hhs_process_kill_command(process_name),
        "Killing process...",
        use_cache=False,
        cache_tag="monitor_process",
    )


def run_ssh_tunnels(host: str) -> subprocess.CompletedProcess[str]:
    """Run the local SSH tunnel listing command and return the completed process."""
    return run_bash_command(
        build_ssh_tunnels_command(host),
        "Loading SSH tunnels...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        force_local=True,
        cache_tag="ssh",
    )


def run_hhs_logs(
    log_file: str, tail_lines: int = 200, log_level: str = "ALL_LEVELS"
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs logs command and return the completed process."""
    return run_bash_command(
        build_hhs_logs_command(log_file, tail_lines, log_level),
        "Loading logs...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="monitor_logs",
    )


def run_hhs_ask(message: str) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_command(message),
        "Asking Ollama...",
        timeout_seconds=hhs_ask_timeout_seconds(),
        use_cache=False,
        cache_tag="ai",
    )


def run_hhs_ask_context() -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask context command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_context_command(),
        "Loading Ollama context...",
        cache_tag="ai",
    )


def run_hhs_ask_prompt() -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask prompt command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_prompt_command(),
        "Loading Ollama prompt...",
        cache_tag="ai",
    )


def run_hhs_ask_prompt_file() -> subprocess.CompletedProcess[str]:
    """Read the editable Ollama prompt file and return the completed process."""
    return run_bash_command(
        build_hhs_ask_prompt_file_command(),
        "Loading Ollama prompt file...",
        use_cache=False,
        cache_tag="ai",
    )


def run_hhs_save_ask_prompt_file(prompt_text: str) -> subprocess.CompletedProcess[str]:
    """Save the editable Ollama prompt file and return the completed process."""
    return run_bash_command(
        build_hhs_save_ask_prompt_file_command(prompt_text),
        "Saving Ollama prompt file...",
        use_cache=False,
        cache_tag="ai",
    )


def run_hhs_revert_ask_prompt_file() -> subprocess.CompletedProcess[str]:
    """Revert the editable Ollama prompt file and return the completed process."""
    return run_bash_command(
        build_hhs_revert_ask_prompt_file_command(),
        "Reverting Ollama prompt file...",
        use_cache=False,
        cache_tag="ai",
    )


def run_hhs_ask_reset(close_dialogs: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask reset command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_reset_command(),
        "Resetting Ollama context...",
        close_dialogs=close_dialogs,
        use_cache=False,
        cache_tag="ai",
    )


def run_hhs_ask_ingest(file_path: str) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask ingest command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_ingest_command(file_path),
        "Ingesting Ollama context...",
        use_cache=False,
        cache_tag="ai",
    )


def run_hhs_ask_models() -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask model listing command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_models_command(),
        "Loading Ollama model...",
        ttl_seconds=hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        cache_tag="ai_models",
    )


def run_hhs_ask_select_model(
    model_name: str,
    loader_message: str = "Selecting Ollama model...",
    close_dialogs: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask model selection command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_select_model_command(model_name),
        loader_message,
        close_dialogs=close_dialogs,
        use_cache=False,
        cache_tag="ai_models",
    )


def run_ollama_delete_model(
    model_name: str, close_dialogs: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the Ollama model deletion command and return the completed process."""
    return run_bash_command(
        build_ollama_delete_model_command(model_name),
        "Deleting model...",
        close_dialogs=close_dialogs,
        use_cache=False,
        cache_tag="ai_models",
    )


def run_hhs_paths() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_paths HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_paths_command(),
        "Loading PATH entries...",
        cache_tag="path",
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


def run_hhs_dirs() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_load_dir HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_dirs_command(),
        "Loading saved directories...",
        cache_tag="dirs",
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


def run_hhs_commands() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_command HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_commands_command(),
        "Loading saved commands...",
        cache_tag="cmds",
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


def run_hhs_aliases() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_aliases HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_aliases_command(),
        "Loading custom aliases...",
        cache_tag="aliases",
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


def run_hhs_services() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup services list command and return the completed process."""
    return run_bash_command(
        build_hhs_services_command(),
        "Loading services...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="services",
    )


def run_hhs_services_quietly() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup services list command through the shared command runner."""
    return run_bash_command(
        build_hhs_services_command(),
        "Loading services...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="services",
    )


def run_hhs_service_action(
    operation: str, service_name: str
) -> subprocess.CompletedProcess[str]:
    """Run a HomeSetup service action command and return the completed process."""
    return run_bash_command(
        build_hhs_services_command(operation, service_name),
        f"{operation.capitalize()}ing service...",
        use_cache=False,
        cache_tag="services",
    )


def env_filter_pattern(env_filter: str, other_filter: str = "") -> str | None:
    """Return the __hhs_envs filter pattern for the selected UI filter."""
    if env_filter == "HHS":
        return "^HHS_"
    if env_filter == "Other":
        clean_filter = other_filter.strip()
        return clean_filter or None
    return None


def refresh_env_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the current environment listing command after a mutation."""
    env_filter = str(st.session_state.get("env_filter", "All"))
    other_filter = str(st.session_state.get("env_other_filter", ""))
    return run_hhs_envs(env_filter_pattern(env_filter, other_filter))


def refresh_path_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the PATH listing command after a mutation."""
    return run_hhs_paths()


def refresh_dir_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the saved directory listing command after a mutation."""
    return run_hhs_dirs()


def refresh_cmd_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the saved command listing command after a mutation."""
    return run_hhs_commands()


def refresh_alias_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the custom alias listing command after a mutation."""
    return run_hhs_aliases()


def refresh_home_tools_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the Home tools listing command after a mutation."""
    return run_hhs_tools()


def refresh_home_shopts_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the Home shell options listing command after a mutation."""
    return run_hhs_shopt()


def refresh_service_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the services listing command after a mutation."""
    return run_hhs_services()


def refresh_process_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the current process listing command after a mutation."""
    process_filter = str(st.session_state.get("monitor_process_filter", ""))
    return run_hhs_process_list(process_filter)


def refresh_ai_model_listing() -> subprocess.CompletedProcess[str]:
    """Reissue the AI model listing command after a mutation."""
    return run_hhs_ask_models()


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
    if service_filter == "Started":
        return [row for row in rows if service_is_up(row)]
    if service_filter == "Stopped":
        return [row for row in rows if service_is_down(row)]
    if service_filter == "Other":
        return [row for row in rows if row_matches_text_filter(row, text_filter)]
    return rows


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


def remote_port_is_reachable(host: str, port: int | None) -> bool:
    """Return whether a remote TCP host and port accepts connections."""
    if port is None:
        return False
    result = run_bash_command(
        build_port_reachability_command(host, port),
        "Checking SSH tunnel status...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        timeout_seconds=3,
        cache_tag="ssh",
    )
    return result.returncode == 0


def ssh_tunnel_is_reachable(row: dict[str, str]) -> bool:
    """Return whether an SSH tunnel row currently accepts connections."""
    host, port = split_bind_address(row.get("Bind", ""))
    if row.get("Type", "").lower() == "remote":
        return remote_port_is_reachable(host, port)
    return local_port_is_reachable(host, port)


def annotate_ssh_tunnel_statuses(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return SSH tunnel rows with a reachable/not reachable status value."""
    annotated_rows: list[dict[str, str]] = []
    for row in rows:
        annotated_row = dict(row)
        annotated_row["Status"] = (
            "Reachable" if ssh_tunnel_is_reachable(row) else "Not reachable"
        )
        annotated_rows.append(annotated_row)
    return annotated_rows


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


def ssh_tunnel_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for SSH tunnel status values."""
    value_text = str(value).strip().lower()
    base_style = "font-weight: 800;"
    if value_text == "reachable":
        return f"{base_style} color: #50fa7b;"
    if value_text == "not reachable":
        return f"{base_style} color: #ff5555;"
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
                "Status": "Active",
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
        st.session_state[hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.DOCKER_CONTAINER_TABLE_KEY}_{reset_counter}"


def reset_docker_container_table_selection() -> None:
    """Reset the Docker container dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.DOCKER_CONTAINER_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


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
    cache_delete_tag("env")
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
    cache_delete_tag("env")
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
    reset_env_table_selection()
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
    cache_delete_tag("path")
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
    cache_delete_tag("path")
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
    reset_path_table_selection()
    save_ui_state()


def apply_selected_dir_value(name: str, value: str) -> bool:
    """Persist a saved directory value."""
    result = run_hhs_dir_action("add", name, value)
    cache_delete_tag("dirs")
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
    cache_delete_tag("dirs")
    refresh_dir_listing()
    push_config_action_status(
        result,
        f'Saved directory removed: "{name}"',
        f"Unable to remove saved directory: {name}",
    )
    reset_dir_table_selection()
    save_ui_state()


def apply_selected_cmd_value(name: str, value: str) -> bool:
    """Persist a saved command value."""
    result = run_hhs_command_action("add", name, value)
    cache_delete_tag("cmds")
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
    cache_delete_tag("cmds")
    refresh_cmd_listing()
    push_config_action_status(
        result,
        f'Saved command removed: "{name}"',
        f"Unable to remove saved command: {name}",
    )
    reset_cmd_table_selection()
    save_ui_state()


def apply_selected_alias_value(name: str, value: str) -> bool:
    """Persist a custom alias value."""
    result = run_hhs_alias_action("add", name, value)
    cache_delete_tag("aliases")
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
    cache_delete_tag("aliases")
    refresh_alias_listing()
    push_config_action_status(
        result,
        f'Alias removed: "{name}"',
        f"Unable to remove alias: {name}",
    )
    reset_alias_table_selection()
    save_ui_state()


def apply_home_shopt_action(operation: str, option_name: str) -> None:
    """Set or unset a shell option from the Home SHOPTS table."""
    result = run_hhs_shopt_action(operation, option_name)
    cache_delete_tag("shopt")
    refresh_home_shopts_listing()
    action_label = "set" if operation == "set" else "unset"
    push_config_action_status(
        result,
        f'Shell option {option_name} {action_label}.',
        f"Unable to {action_label} shell option: {option_name}",
    )
    reset_home_shopts_table_selection()
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


def ollama_service_is_up() -> bool:
    """Return whether the Ollama service is currently reported as up."""
    result = run_hhs_services_quietly()
    if result.returncode != 0:
        return False
    return any(
        row.get("Name", "").strip().lower() == "ollama" and service_is_up(row)
        for row in parse_hhs_services(result.stdout)
    )


def main_views() -> tuple[str, ...]:
    """Return the visible main view names for the current service state."""
    views = hhs_ui.VIEWS
    if connected_ssh_host():
        views = (*views, hhs_ui.SSH_VIEW)
    if ollama_service_is_up():
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
    if not operation or not tool_name:
        return

    result = run_hhs_tool_action(operation, tool_name)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    cache_delete_tag("tools")
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
    """Run a service action and reset the service selection."""
    result = run_hhs_service_action(operation, service_name)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    cache_delete_tag("services")
    refresh_service_listing()
    st.session_state["service_action_message"] = status_message
    st.session_state["service_action_succeeded"] = result.returncode == 0
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
    reset_service_table_selection()


def apply_selected_process_kill(process_name: str) -> None:
    """Kill the selected process name and store the action result."""
    result = run_hhs_process_kill(process_name)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    cache_delete_tag("monitor_process")
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
    action_message = st.session_state.pop("service_action_message", "")
    action_succeeded = st.session_state.pop("service_action_succeeded", None)
    if action_message:
        if action_succeeded:
            st.success(clean_command_status_message(action_message))
        else:
            st.error(clean_command_status_message(action_message))

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

    result = run_hhs_envs(env_filter_pattern(env_filter, other_filter))
    rows = parse_hhs_envs(result.stdout) if result.returncode == 0 else []
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
    result = run_hhs_paths()
    rows = parse_hhs_paths(result.stdout) if result.returncode == 0 else []
    render_path_rows(
        filter_path_rows(rows, path_filter, other_filter)
    )


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
    result = run_hhs_dirs()
    rows = parse_hhs_dirs(result.stdout) if result.returncode == 0 else []
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
    result = run_hhs_commands()
    rows = parse_hhs_commands(result.stdout) if result.returncode == 0 else []
    render_cmd_rows(
        filter_rows_by_text(rows, cmds_filter, other_filter),
    )


def render_aliases_table() -> None:
    """Render custom aliases using __hhs_aliases."""

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
    result = run_hhs_aliases()
    rows = parse_hhs_aliases(result.stdout) if result.returncode == 0 else []
    render_alias_rows(
        filter_rows_by_text(rows, alias_filter, other_filter),
    )


def render_services_table() -> None:
    """Render HomeSetup services using __hhs_services status output."""
    service_filter, other_filter = render_table_controls_panel(
        lambda: render_table_filter_controls(
            hhs_ui.SERVICE_FILTERS,
            "service_filter",
            "service_other_filter",
            hhs_ui.FOUR_OPTION_FILTER_COLUMNS,
        )
    )
    result = run_hhs_services()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list services.")
        return
    render_service_rows(
        filter_service_rows(
            parse_hhs_services(result.stdout), service_filter, other_filter
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
    result = run_hhs_history()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list command history.")
        return
    render_read_only_rows(
        filter_rows_by_text(
            parse_hhs_history(result.stdout), history_commands_filter, other_filter
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
    result = run_hhs_history_dirs()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list directory history.")
        return
    rows = filter_rows_by_text(
        parse_hhs_history_dirs(result.stdout),
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
    result = run_hhs_history_stats(int(top_n))
    if result.returncode != 0:
        st.error(result.stderr or result.stdout or "Unable to list history stats.")
        return
    rows = sorted(
        parse_hhs_history_stats(result.stdout),
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
            on_change=save_ui_state,
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
    result = run_hhs_disk_usage(selected_directory, applied_top_n)
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load disk usage."
            )
        )
        return
    rows = sorted(
        parse_hhs_disk_usage(result.stdout),
        key=lambda row: float(row["Bytes"]),
        reverse=True,
    )
    for row in rows:
        row["Label"] = relative_disk_usage_path(str(row["Path"]), selected_directory)
    if not rows:
        st.caption("No disk usage entries found.")
        return
    st.markdown(f"##### Top {applied_top_n} disk usage at `{selected_directory}`")
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
    st.button("Refresh", key=f"monitor_{metric.lower()}_refresh_button")
    result = run_process_monitor(metric)
    if result.returncode != 0:
        st.error(
            strip_ansi(
                result.stderr
                or result.stdout
                or f"Unable to load {metric.lower()} usage."
            )
        )
        return
    rows = sorted(
        parse_process_monitor(result.stdout, metric),
        key=lambda row: float(row["Value"]),
        reverse=True,
    )[:10]
    if not rows:
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
    st.markdown(f"##### Top 10 {title} processes")
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
    action_message = st.session_state.pop("monitor_process_action_message", "")
    action_succeeded = st.session_state.pop("monitor_process_action_succeeded", None)
    if action_message:
        if action_succeeded:
            st.success(clean_command_status_message(action_message))
        else:
            st.error(clean_command_status_message(action_message))

    def render_process_controls() -> str:
        """Render process table controls and return the filter text."""
        label_col, input_col, action_col = st.columns(
            [0.55, 3.0, 0.45], vertical_alignment="center"
        )
        with label_col:
            st.markdown(
                '<span class="hhs-inline-form-label">Filters</span>',
                unsafe_allow_html=True,
            )
        with input_col:
            st.text_input(
                "Filters",
                key="monitor_process_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type process filter",
            )
        with action_col:
            st.button(
                "",
                key="monitor_process_filter_apply_button",
                help="Apply",
                on_click=apply_monitor_process_filter,
                width="stretch",
            )
        return applied_monitor_process_filter()

    process_filter = render_table_controls_panel(render_process_controls)
    result = run_hhs_process_list(process_filter)
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load processes."
            )
        )
        return
    rows = parse_hhs_process_list(result.stdout)
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
    label_col, input_col, level_label_col, level_col, tail_col, clear_col = st.columns(
        [0.55, 2.65, 0.62, 0.82, 0.45, 0.16], vertical_alignment="center"
    )
    with label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Log file</span>',
            unsafe_allow_html=True,
        )
    with input_col:
        selected_log = st.selectbox(
            "Log file",
            options=log_files,
            key="monitor_log_file",
            label_visibility="collapsed",
            on_change=save_ui_state,
        )
    with level_label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Log level</span>',
            unsafe_allow_html=True,
        )
    with level_col:
        selected_level = st.selectbox(
            "Log level",
            options=hhs_ui.LOG_LEVELS,
            key="monitor_log_level",
            format_func=monitor_log_level_label,
            label_visibility="collapsed",
            on_change=save_ui_state,
        )
    with tail_col:
        tail_enabled = st.checkbox(
            "Tail",
            key="monitor_logs_tail",
            on_change=save_ui_state,
        )
    with clear_col:
        st.button(
            "",
            key="monitor_log_clear_button",
            help="Clear selected log file",
            on_click=clear_monitor_log_file,
            width="stretch",
        )
    st.markdown(
        f'<div class="hhs-log-file-title"><code>{html.escape(selected_log)}</code></div>',
        unsafe_allow_html=True,
    )
    if tail_enabled:
        render_monitor_logs_tail(selected_log, selected_level)
    else:
        render_monitor_logs_once(selected_log, selected_level)


@st.fragment(run_every="5s")
def render_monitor_logs_tail(selected_log: str, selected_level: str) -> None:
    """Render a tail-like log pane that refreshes only while LOGS is active."""
    render_monitor_logs_once(selected_log, selected_level)


def render_monitor_logs_once(selected_log: str, selected_level: str) -> None:
    """Render the selected log once without automatic refresh."""
    result = run_hhs_logs(selected_log, 200, selected_level)
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load logs."
            )
        )
        return
    render_terminal_output(
        colorize_log_output(result.stdout),
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
    st.write("")
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
    st.write("")
    render_services_table()


def monitor_view_label(monitor_view: str) -> str:
    """Return the display label for a Monitor view key."""
    return hhs_ui.MONITOR_VIEW_LABELS.get(monitor_view, monitor_view)


def render_ssh_view() -> None:
    """Render the SSH tunnel and port-forward view."""
    host = connected_ssh_host()
    st.markdown(
        f"""
        <section class="hhs-view-heading">
          <h2> SSH</h2>
          <p>Connected to remote  {html.escape(ssh_connection_display(host))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    result = run_ssh_tunnels(host)
    if result.returncode != 0:
        st.error(result.stderr or "Unable to load SSH tunnels.")
        return
    rows = annotate_ssh_tunnel_statuses(parse_ssh_tunnels(result.stdout, host))
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
    st.write("")
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
    st.write("")
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
    model_result = run_hhs_ask_models()
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
            ai_chat_meta_html(username, ollama_model, context_size, model_result.stdout),
            unsafe_allow_html=True,
        )
    with clear_col:
        st.button(
            " Clear",
            key="ai_clear_chat_button",
            help="Clear chat and context",
            on_click=request_ai_chat_clear_confirmation,
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
    if prompt := st.chat_input("Ask Ollama through HomeSetup"):
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
        with st.chat_message(
            "Ollama",
            avatar=(
                str(hhs_ui.APP_AI_OLLAMA_AVATAR_FILE)
                if hhs_ui.APP_AI_OLLAMA_AVATAR_FILE.is_file()
                else None
            ),
        ):
            ask_started_at = time.perf_counter()
            result = run_hhs_ask(prompt)
            request_duration = time.perf_counter() - ask_started_at
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
                render_ai_chat_message(
                    "assistant", answer, username, ollama_model, context_size
                )
            else:
                answer = clean_hhs_ask_output(result.stdout) or strip_ansi(
                    result.stdout
                )
                render_ai_chat_message(
                    "assistant", answer, username, ollama_model, context_size
                )
            st.session_state["ai_chat_messages"].append(
                {"role": "assistant", "content": answer}
            )
            save_ui_state()


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
        refresh_ai_prompt_file()

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
            type=AI_CONTEXT_UPLOAD_TYPES,
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

    model_result = run_hhs_ask_models()
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
    rows = parse_ollama_model_rows(model_result.stdout, current_model)
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
    if st.session_state.get("ai_model_select_execute_pending"):
        execute_pending_ai_model_selection()
    if st.session_state.get("ai_model_delete_execute_pending"):
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
    st.write("")
    if ai_view == "CHAT":
        render_ai_chat_panel()
    elif ai_view == "CONTEXT":
        render_ai_context_panel()
    elif ai_view == "SETTINGS":
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
    st.session_state.setdefault("footer_hhs_version_cache_loaded", False)
    st.session_state.setdefault("footer_shell_version_dialog_title", "")
    st.session_state.setdefault("footer_shell_version_output", "")
    render_styles()
    handle_footer_actions()
    render_footer_shell_version_dialog()
    execute_due_updater_check()
    if st.session_state.get("theme_reload_pending"):
        render_theme_reload_overlay()
    st.session_state.setdefault("active_view", "Home")
    if st.session_state["active_view"] not in (
        *hhs_ui.VIEWS,
        hhs_ui.SSH_VIEW,
        hhs_ui.AI_VIEW,
    ):
        st.session_state["active_view"] = "Home"
    st.session_state.setdefault("ai_chat_messages", [])
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
    st.session_state.setdefault("ssh_disconnect_pending", "")
    st.session_state.setdefault("ssh_connection_status", "")
    st.session_state.setdefault("ssh_connection_host", "")
    st.session_state.setdefault("ssh_connection_error", "")
    st.session_state.setdefault("ssh_connection_dialog_title", "")
    restore_registered_ssh_connection_on_session_start()
    synchronize_selected_ssh_host_with_connection()
    if selected_host_is_local():
        st.session_state["ssh_connection_status"] = ""
        st.session_state["ssh_connection_host"] = ""
        st.session_state["ssh_connection_error"] = ""
        st.session_state["ssh_connect_pending"] = ""
        st.session_state["ssh_disconnect_pending"] = ""
    execute_pending_ssh_disconnection()
    execute_pending_ssh_connection()
    if render_ssh_connection_dialog():
        return
    st.session_state.setdefault("home_view", "System")
    if st.session_state["home_view"] not in hhs_ui.HOME_VIEWS:
        st.session_state["home_view"] = "System"
    st.session_state.setdefault("home_tools_filter", "All")
    if st.session_state["home_tools_filter"] not in hhs_ui.LIST_FILTERS:
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
    st.session_state.setdefault("monitor_process_filter", "")
    st.session_state.setdefault(
        "monitor_process_filter_applied",
        st.session_state["monitor_process_filter"],
    )
    st.session_state.setdefault(
        "monitor_disk_directory", monitor_default_disk_directory()
    )
    if not str(st.session_state["monitor_disk_directory"]).strip():
        st.session_state["monitor_disk_directory"] = monitor_default_disk_directory()
    st.session_state.setdefault(
        "monitor_disk_directory_applied",
        st.session_state["monitor_disk_directory"],
    )
    st.session_state.setdefault("monitor_disk_top_n", 10)
    st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n")
    )
    st.session_state.setdefault("monitor_log_file", "")
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
    render_sidebar()
    render_main_view()
    render_folder_picker_dialog()
    render_footer()
    render_floating_status()


if __name__ == "__main__":
    main()
