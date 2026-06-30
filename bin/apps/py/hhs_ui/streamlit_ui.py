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

import hashlib
import html
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
import time
from base64 import b64encode
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit import config as st_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hhs_ui


def load_app_css() -> str:
    """Load the HomeSetup Streamlit UI stylesheet."""
    return hhs_ui.APP_CSS_FILE.read_text(encoding="utf-8")


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
    theme_properties = css_custom_properties(
        theme_css_file(theme_name).read_text(encoding="utf-8")
    )
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
    return theme_css_file(selected_theme).read_text(encoding="utf-8")


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
    font_data = b64encode(hhs_ui.APP_FONT_FILE.read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{font_data}"


def load_app_image_data_uri(image_file: Path, mime_type: str) -> str:
    """Load a HomeSetup UI image as a browser-embeddable data URI."""
    image_data = b64encode(image_file.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{image_data}"


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
    st.markdown(
        f'<div class="hhs-sidebar-clock">{html.escape(format_datetime(datetime.now()))}</div>',
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


def close_document_view() -> None:
    """Close the document view and restore the previous main view."""
    previous_view = st.session_state.get(hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY, "Home")
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = False
    if previous_view in hhs_ui.VIEWS:
        st.session_state["active_view"] = previous_view


def clear_ai_chat_history() -> None:
    """Reset the backend ask history and clear the current AI chat history."""
    run_hhs_ask_reset(close_dialogs=True)
    cache_clear()
    st.session_state["ai_chat_messages"] = []
    st.session_state["ai_clear_chat_pending"] = False
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


def show_ai_chat_context() -> None:
    """Append the current backend ask context as a HomeSetup chat message."""
    result = run_hhs_ask_context()
    output = result.stdout if result.returncode == 0 else result.stderr or result.stdout
    message = (
        strip_ansi(output or "No Ollama context available.").strip()
        or "No Ollama context available."
    )
    st.session_state["ai_chat_messages"].append({"role": "system", "content": message})
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
        if result.returncode != 0:
            st.session_state["ai_model_select_error"] = strip_ansi(
                result.stderr or result.stdout or "Unable to select model."
            )
        else:
            st.session_state["ai_model_select_error"] = ""
            cache_clear()
            reset_ai_model_table_selection()
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
        if result.returncode != 0:
            st.session_state["ai_model_delete_error"] = strip_ansi(
                result.stderr or result.stdout or "Unable to delete model."
            )
        else:
            st.session_state["ai_model_delete_error"] = ""
            cache_clear()
            if model_status == "Active":
                fallback_model = first_downloaded_ollama_model(
                    run_hhs_ask_models().stdout, excluded_model=model_name
                )
                if fallback_model:
                    fallback_result = run_hhs_ask_select_model(
                        fallback_model, close_dialogs=True
                    )
                    if fallback_result.returncode != 0:
                        st.session_state["ai_model_delete_error"] = strip_ansi(
                            fallback_result.stderr
                            or fallback_result.stdout
                            or "Unable to select fallback model."
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
        st.markdown(
            f'<div class="hhs-sidebar-title">HomeSetup - UI v{html.escape(hhs_ui.VERSION)}</div>',
            unsafe_allow_html=True,
        )
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
            st.markdown('<div class="hhs-vspacer"></div>', unsafe_allow_html=True)
            if connected_host:
                st.button(
                    "Disconnect",
                    key="ssh_disconnect_button",
                    on_click=request_ssh_host_disconnection,
                    width="stretch",
                )
            else:
                st.button(
                    "Connect",
                    key="ssh_connect_button",
                    on_click=request_ssh_host_connect,
                    width="stretch",
                )
            st.markdown(
                '<div class="hhs-vspacer"></div><hr class="hhs-sidebar-separator" /><div class="hhs-vspacer"></div>',
                unsafe_allow_html=True,
            )
        st.write("")
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
        st.write("")
        st.markdown("**Documents**")
        if st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY):
            st.button(
                "BACK",
                key="document_back_button",
                on_click=close_document_view,
                width="stretch",
            )
        else:
            st.button(
                "README",
                key="readme_open_button",
                on_click=open_document_view,
                args=("README",),
                width="stretch",
            )
            st.button(
                "HANDBOOK",
                key="handbook_open_button",
                on_click=open_document_view,
                args=("HANDBOOK",),
                width="stretch",
            )


def render_preloader(message: str = "Loading...", transient: bool = True) -> None:
    """Render a full-page overlay preloader."""
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


def homesetup_version() -> str:
    """Return the HomeSetup product version from the shell environment."""
    return os.environ.get("HHS_VERSION", "unknown")


def homesetup_home() -> Path:
    """Return the HomeSetup repository root used by this UI."""
    return Path(os.environ.get("HHS_HOME", hhs_ui.APP_DIR.parents[3])).expanduser()


def monitor_default_disk_directory() -> str:
    """Return the default directory for the disk monitor."""
    return str(homesetup_home())


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


def render_footer() -> None:
    """Render the HomeSetup UI footer."""
    version = homesetup_version()
    working_dir = html.escape(os.getcwd())
    repository_url = html.escape(os.environ.get("HHS_GITHUB_URL", "#"), quote=True)
    working_dir_url = f"?{hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM}=1"
    connected_host = html.escape(
        str(st.session_state.get("ssh_connection_host", "")).strip()
    )
    remote_status_markup = ""
    if (
        str(st.session_state.get("ssh_connection_status", "")).strip() == "connected"
        and connected_host
    ):
        remote_status_markup = (
            f'<span class="hhs-footer-remote-status">'
            f"Connected to remote: {connected_host}</span>"
        )
    logo_data_uri = load_app_image_data_uri(
        hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"
    )
    st.markdown(
        f"""
        <footer class="hhs-app-footer">
          <a class="hhs-footer-logo-link" href="{repository_url}" target="_blank" rel="noopener noreferrer" aria-label="HomeSetup repository">
            <img class="hhs-footer-logo" src="{logo_data_uri}" alt="" aria-hidden="true">
          </a>
          <a class="hhs-footer-link" href="{repository_url}" target="_blank" rel="noopener noreferrer">HomeSetup - v{version}</a>
          <span class="hhs-footer-spacer"></span>
          <span class="hhs-footer-glyph"></span>
          <span class="hhs-footer-spacer"></span>
          <a class="hhs-footer-link" href="{working_dir_url}" target="_self">Working dir: {working_dir}</a>
          {remote_status_markup}
        </footer>
        """,
        unsafe_allow_html=True,
    )


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


def handle_footer_actions() -> None:
    """Run footer actions requested through Streamlit query parameters."""
    if not query_param_requested(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM):
        return
    remove_query_param(hhs_ui.FOOTER_OPEN_WORKING_DIR_QUERY_PARAM)
    result = run_open_working_directory()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to open working directory.")


def render_home_view() -> None:
    """Render the Home informational view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2>Informational</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    home_view = st.segmented_control(
        "Home view",
        options=hhs_ui.HOME_VIEWS,
        default=st.session_state["home_view"],
        key="home_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    st.write("")
    if home_view == "System":
        render_home_system_panel()
    elif home_view == "Tools":
        render_home_tools_panel()


def render_home_system_panel() -> None:
    """Render system information on the Home view."""
    result = run_hhs_sysinfo()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to load system information.")
        return
    st.markdown(format_hhs_sysinfo_markdown(result.stdout))


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


def render_selected_item(label: str, value: str) -> None:
    """Render a selected item label/value pair using theme-controlled styles."""
    st.markdown(
        (
            '<div class="hhs-selected-item">'
            f'<span class="hhs-selected-item-label">{html.escape(label)}</span>'
            " "
            f'<span class="hhs-selected-item-value">{html.escape(value)}</span>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_selected_item_text(text: str) -> None:
    """Render selected item text split on the first label/value separator."""
    label, separator, value = text.partition(":")
    if not separator:
        render_selected_item(text, "")
        return
    render_selected_item(f"{label}:", value.strip())


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
    selected_label_html: bool = False,
    action_buttons: list[dict[str, object]] | None = None,
    action_column_weights: list[float] | None = None,
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
    if not checkbox:
        return None, None

    selected_rows = selection.selection.rows if selection else []
    if not selected_rows or selected_rows[0] >= len(rows):
        if empty_hint:
            st.caption(empty_hint)
        return None, None

    selected_index = selected_rows[0]
    selected_row = rows[selected_index]
    if action_hint:
        st.caption(action_hint)
    if selected_label is not None:
        label = selected_label(selected_row, selected_index)
        if selected_label_html:
            st.markdown(label, unsafe_allow_html=True)
        else:
            render_selected_item_text(label)

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
    filter_col, other_filter_col = st.columns(
        hhs_ui.TWO_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        tools_filter = st.radio(
            "Filters",
            hhs_ui.LIST_FILTERS,
            horizontal=True,
            index=0,
            key="home_tools_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if tools_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="home_tools_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
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


def render_document_view() -> None:
    """Render the selected HomeSetup document."""
    title, document = document_details(
        str(st.session_state.get(hhs_ui.DOCUMENT_SELECTED_KEY, "README"))
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


def strip_ansi(value: str) -> str:
    """Remove terminal ANSI color escapes from command output."""
    return hhs_ui.ESCAPED_ANSI_ESCAPE_PATTERN.sub(
        "", hhs_ui.ANSI_ESCAPE_PATTERN.sub("", value)
    )


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


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Return a Markdown table for the provided headers and rows."""
    if not headers or not rows:
        return ""
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(row[: len(headers)]) + " |" for row in rows]
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


def command_env() -> dict[str, str]:
    """Return the environment used by HomeSetup command subprocesses."""
    return {
        **os.environ,
        "COLUMNS": hhs_ui.COMMAND_COLUMNS,
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
    clear_registered_ssh_connection()
    cache_clear()
    save_ui_state()


def ssh_shared_connection_closed(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether a failed SSH command reports a closed shared connection."""
    if result.returncode == 0:
        return False
    output = strip_ansi(f"{result.stdout or ''}\n{result.stderr or ''}").lower()
    return "shared connection to " in output and " closed" in output


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
        ["bash", "-lc", command],
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
    st.session_state["ssh_connect_pending"] = ""
    result = run_bash_command(
        build_ssh_connect_command(host),
        f"Connecting to SSH host {host}...",
        ttl_seconds=0,
        use_cache=False,
        force_local=True,
        timeout_seconds=15,
    )
    if result.returncode == 0:
        st.session_state["ssh_connection_status"] = "connected"
        st.session_state["ssh_connection_host"] = host
        st.session_state["ssh_host_selected"] = host
        st.session_state["ssh_host_selector"] = host
        st.session_state["ssh_connection_error"] = ""
        st.session_state["ssh_connection_dialog_title"] = ""
        register_ssh_connection(host)
        save_ui_state()
    else:
        st.session_state["ssh_connection_status"] = "failed"
        st.session_state["ssh_connection_host"] = ""
        st.session_state["ssh_connection_error"] = strip_ansi(
            result.stderr or result.stdout or f"Unable to connect to SSH host {host}."
        )
        st.session_state["ssh_connection_dialog_title"] = f"Failed to connect to {host}"


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
    )
    st.session_state["ssh_connection_status"] = ""
    st.session_state["ssh_connection_host"] = ""
    st.session_state["ssh_connection_error"] = ""
    st.session_state["ssh_connection_dialog_title"] = ""
    st.session_state["ssh_host_selected"] = local_hostname()
    st.session_state["ssh_host_selector"] = local_hostname()
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
) -> subprocess.CompletedProcess[str]:
    """Run a Bash command with hash-keyed command-result caching and a preloader."""
    remote_host = command_remote_host(force_local=force_local)
    command_to_run = effective_bash_command(command, force_local=force_local)
    effective_timeout = timeout_seconds
    if effective_timeout is None and command_to_run != command:
        effective_timeout = 60
    cache_key = command_cache_key(command_to_run)
    cached_value = cache_get(cache_key) if use_cache else None
    if use_cache and cached_value is not None:
        result = completed_process_from_cache(command_to_run, cached_value)
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result

    if remote_host and not ssh_connection_is_alive(remote_host):
        result = completed_disconnected_ssh_process(command_to_run, remote_host)
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result

    set_overlay(True, loader_message, close_dialogs=close_dialogs)
    try:
        result = subprocess.run(
            ["bash", "-lc", command_to_run],
            capture_output=True,
            check=False,
            env=command_env(),
            text=True,
            timeout=effective_timeout,
        )
        disconnected = handle_remote_command_result(remote_host, result)
        if use_cache and not ssh_shared_connection_closed(result):
            cache_set(
                cache_key, cache_value_from_completed_process(result), ttl_seconds
            )
        if disconnected:
            st.rerun()
        return result
    except subprocess.TimeoutExpired as error:
        result = subprocess.CompletedProcess(
            ["bash", "-lc", command_to_run],
            124,
            error.stdout or "",
            error.stderr or f"Command timed out after {effective_timeout} seconds.",
        )
        if handle_remote_command_result(remote_host, result):
            st.rerun()
        return result
    finally:
        set_overlay(False)


def load_ui_cache() -> dict[str, dict[str, object]]:
    """Load the UI cache file and lazily prune expired entries."""
    if not hhs_ui.UI_CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(hhs_ui.UI_CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    cache = {
        key: value
        for key, value in data.items()
        if isinstance(key, str)
        and key.startswith("command_hash:")
        and isinstance(value, dict)
    }
    pruned_cache = prune_ui_cache_entries(cache)
    if pruned_cache != cache or len(cache) != len(data):
        save_ui_cache(pruned_cache)
    return pruned_cache


def save_ui_cache(cache: dict[str, dict[str, object]]) -> None:
    """Persist the UI cache file."""
    try:
        hhs_ui.UI_CACHE_FILE.write_text(
            json.dumps(cache, indent=2) + "\n", encoding="utf-8"
        )
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


def cache_clear() -> None:
    """Delete all UI cache entries."""
    save_ui_cache({})


def completed_process_from_cache(
    command: str, cached_value: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    """Build a CompletedProcess from a cached command result."""
    return subprocess.CompletedProcess(
        ["bash", "-lc", command],
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


def command_cache_key(command: str) -> str:
    """Return a stable cache key based on the full command string."""
    return f"command_hash:{hashlib.sha256(command.encode('utf-8')).hexdigest()}"


def build_hhs_envs_command(prefix_filter: str | None) -> str:
    """Build the Bash command used to run the __hhs_envs HomeSetup function."""
    filter_arg = f' "{prefix_filter}"' if prefix_filter else ""
    return (
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_envs{filter_arg}"
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


def run_open_working_directory() -> subprocess.CompletedProcess[str]:
    """Open the current working directory in the operating system file explorer."""
    return run_bash_command(
        build_open_directory_command(os.getcwd()),
        "Opening working directory...",
        ttl_seconds=0,
        use_cache=False,
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


def build_hhs_logs_command(log_file: str, tail_lines: int = 200) -> str:
    """Build the Bash command used to run the __hhs logs command."""
    safe_log_file = Path(log_file).name
    safe_tail_lines = max(1, min(int(tail_lines), 5000))
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
        f"__hhs logs -n {safe_tail_lines} {shlex.quote(safe_log_file)}"
    )


def build_hhs_ask_execute_command(arguments: list[str]) -> str:
    """Build the Bash command used to run the __hhs ask execute command."""
    safe_arguments = " ".join(shlex.quote(argument) for argument in arguments)
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
        'function __hhs() { if [[ "$1" == "ask" && "$2" == "execute" ]]; then shift 2; execute "$@"; else return 127; fi; }; '
        f"__hhs ask execute {safe_arguments}"
    )


def build_hhs_ask_command(message: str) -> str:
    """Build the Bash command used to run the __hhs ask command."""
    return build_hhs_ask_execute_command(["-k", message])


def build_hhs_ask_context_command() -> str:
    """Build the Bash command used to show the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-c"])


def build_hhs_ask_reset_command() -> str:
    """Build the Bash command used to reset the current Ollama ask context."""
    return build_hhs_ask_execute_command(["-r"])


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


def build_hhs_dirs_command() -> str:
    """Build the Bash command used to run the __hhs_load_dir HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-dirs.bash"; '
        "__hhs_load_dir -l"
    )


def build_hhs_commands_command() -> str:
    """Build the Bash command used to run the __hhs_command HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-command.bash"; '
        "__hhs_command -l"
    )


def build_hhs_aliases_command() -> str:
    """Build the Bash command used to run the __hhs_aliases HomeSetup function."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-aliases.bash"; '
        "__hhs_aliases -l"
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


def run_hhs_envs(prefix_filter: str | None) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_envs HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_envs_command(prefix_filter),
        "Loading environment variables...",
    )


def run_hhs_sysinfo() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_sysinfo HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_sysinfo_command(),
        "Loading system information...",
        ttl_seconds=hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
    )


def run_hhs_tools() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_tools HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_tools_command(),
        "Loading tool checks...",
        ttl_seconds=hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
    )


def run_hhs_tool_action(
    operation: str, tool_name: str
) -> subprocess.CompletedProcess[str]:
    """Run an hspm install or uninstall action for a Home tool."""
    return run_bash_command(
        build_hhs_hspm_command(operation, tool_name),
        f"Running hspm {operation} for {tool_name}...",
        use_cache=False,
    )


def run_tool_tldr(tool_name: str) -> subprocess.CompletedProcess[str]:
    """Run tldr for the selected Home tool."""
    return run_bash_command(
        build_tool_tldr_command(tool_name),
        f"Loading TLDR for {tool_name}...",
        use_cache=False,
    )


def run_hhs_history() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_history HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_history_command(),
        "Loading command history...",
    )


def run_hhs_history_dirs() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_dirs HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_history_dirs_command(),
        "Loading directory history...",
    )


def run_hhs_history_stats(top_n: int = 10) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_hist_stats HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_history_stats_command(top_n),
        "Loading history stats...",
    )


def run_hhs_disk_usage(
    directory: str, top_n: int = 10
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs_du HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_disk_usage_command(directory, top_n),
        "Loading disk usage...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
    )


def run_process_monitor(
    metric: str, top_n: int = 10
) -> subprocess.CompletedProcess[str]:
    """Run the process monitor command and return the completed process."""
    return run_bash_command(
        build_process_monitor_command(metric, top_n),
        f"Loading {metric.lower()} usage...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
    )


def run_hhs_process_list(process_filter: str) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup process list command and return the completed process."""
    return run_bash_command(
        build_hhs_process_list_command(process_filter),
        "Loading processes...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
    )


def run_hhs_process_kill(process_name: str) -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup process kill command and return the completed process."""
    return run_bash_command(
        build_hhs_process_kill_command(process_name),
        "Killing process...",
    )


def run_hhs_logs(
    log_file: str, tail_lines: int = 200
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs logs command and return the completed process."""
    return run_bash_command(
        build_hhs_logs_command(log_file, tail_lines),
        "Loading logs...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
    )


def run_hhs_ask(message: str) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_command(message),
        "Asking Ollama...",
        timeout_seconds=hhs_ask_timeout_seconds(),
    )


def run_hhs_ask_context() -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask context command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_context_command(),
        "Loading Ollama context...",
    )


def run_hhs_ask_reset(close_dialogs: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask reset command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_reset_command(),
        "Resetting Ollama context...",
        close_dialogs=close_dialogs,
    )


def run_hhs_ask_models() -> subprocess.CompletedProcess[str]:
    """Run the __hhs ask model listing command and return the completed process."""
    return run_bash_command(
        build_hhs_ask_models_command(),
        "Loading Ollama model...",
        ttl_seconds=hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
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
    )


def run_ollama_delete_model(
    model_name: str, close_dialogs: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the Ollama model deletion command and return the completed process."""
    return run_bash_command(
        build_ollama_delete_model_command(model_name),
        "Deleting model...",
        close_dialogs=close_dialogs,
    )


def run_hhs_paths() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_paths HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_paths_command(),
        "Loading PATH entries...",
    )


def run_hhs_dirs() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_load_dir HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_dirs_command(),
        "Loading saved directories...",
    )


def run_hhs_commands() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_command HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_commands_command(),
        "Loading saved commands...",
    )


def run_hhs_aliases() -> subprocess.CompletedProcess[str]:
    """Run the __hhs_aliases HomeSetup function and return the completed process."""
    return run_bash_command(
        build_hhs_aliases_command(),
        "Loading custom aliases...",
    )


def run_hhs_services() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup services list command and return the completed process."""
    return run_bash_command(
        build_hhs_services_command(),
        "Loading services...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
    )


def run_hhs_services_quietly() -> subprocess.CompletedProcess[str]:
    """Run the HomeSetup services list command through the shared command runner."""
    return run_bash_command(
        build_hhs_services_command(),
        "Loading services...",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
    )


def run_hhs_service_action(
    operation: str, service_name: str
) -> subprocess.CompletedProcess[str]:
    """Run a HomeSetup service action command and return the completed process."""
    return run_bash_command(
        build_hhs_services_command(operation, service_name),
        f"{operation.capitalize()}ing service...",
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
    if tools_filter == "Other":
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


def cmd_table_key() -> str:
    """Return the Streamlit command dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.CMD_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.CMD_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.CMD_TABLE_KEY}_{reset_counter}"


def alias_table_key() -> str:
    """Return the Streamlit alias dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(hhs_ui.ALIAS_TABLE_RESET_COUNTER_KEY, 0)
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.ALIAS_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"{hhs_ui.ALIAS_TABLE_KEY}_{reset_counter}"


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


def apply_selected_env_value(name: str, value: str) -> None:
    """Export a selected environment value and store it for table rerenders."""
    os.environ[name] = value
    env_value_overrides()[name] = value
    save_ui_state()


def apply_selected_path_value(old_path: str, new_path: str) -> None:
    """Export an edited PATH entry and store it for table rerenders."""
    path_values = path_entries()
    updated_values = [new_path if entry == old_path else entry for entry in path_values]
    if new_path not in updated_values:
        updated_values.append(new_path)
    os.environ["PATH"] = ":".join(updated_values)
    path_value_overrides()[old_path] = new_path
    save_ui_state()


def apply_selected_env_editor_value(name: str, editor_key: str) -> None:
    """Export the current selected environment editor value."""
    apply_selected_env_value(name, str(st.session_state.get(editor_key, "")))
    reset_env_table_selection()


def apply_selected_path_editor_value(old_path: str, editor_key: str) -> None:
    """Export the current selected PATH editor value."""
    apply_selected_path_value(old_path, str(st.session_state.get(editor_key, "")))
    reset_path_table_selection()


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
    """Render selectable read-only environment variable rows."""
    rows = apply_env_value_overrides(rows)
    _, selected_row = render_table(
        rows,
        key=env_table_key(),
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
    )
    if selected_row is None:
        return

    editor_key = env_value_editor_key(selected_row["Name"])
    st.session_state.setdefault(editor_key, selected_row["Value"])
    render_selected_item("Selected:", selected_row["Name"])
    st.text_area(
        "Selected value",
        height=hhs_ui.ENV_VALUE_EDITOR_HEIGHT,
        key=editor_key,
        label_visibility="collapsed",
        max_chars=int(hhs_ui.COMMAND_COLUMNS),
        on_change=apply_selected_env_editor_value,
        args=(selected_row["Name"], editor_key),
    )
    scroll_to_env_value_editor(editor_key)


def render_path_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable PATH rows."""
    rows = apply_path_value_overrides(rows)
    selected_index, selected_row = render_table(
        rows,
        key=path_table_key(),
        height=hhs_ui.PATH_TABLE_HEIGHT,
        width=hhs_ui.PATH_TABLE_WIDTH,
    )
    if selected_index is None or selected_row is None:
        return

    editor_key = path_value_editor_key(selected_index)
    st.session_state.setdefault(editor_key, selected_row["Value"])
    render_selected_item("Selected:", selected_row["Name"])
    st.text_area(
        "Selected PATH value",
        height=hhs_ui.PATH_VALUE_EDITOR_HEIGHT,
        key=editor_key,
        label_visibility="collapsed",
        max_chars=int(hhs_ui.COMMAND_COLUMNS),
        on_change=apply_selected_path_editor_value,
        args=(selected_row["Value"], editor_key),
    )
    scroll_to_env_value_editor(editor_key)


def render_read_only_rows(
    rows: list[dict[str, str]],
    table_key: str,
    value_key_prefix: str,
    selected_label: str,
    empty_caption: str = "Select a row to interact",
) -> None:
    """Render selectable read-only configuration rows."""
    selected_index, selected_row = render_table(
        rows,
        key=table_key,
        empty_hint=empty_caption,
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
    )
    if selected_index is None or selected_row is None:
        return

    editor_key = f"{value_key_prefix}_{selected_index}"
    st.session_state[editor_key] = selected_row["Value"]
    selected_name = (
        selected_row.get("Name")
        or selected_row.get("Index")
        or selected_row.get("Value", "")
    )
    render_selected_item("Selected:", selected_name)
    st.text_area(
        selected_label,
        disabled=True,
        height=hhs_ui.ENV_VALUE_EDITOR_HEIGHT,
        key=editor_key,
        label_visibility="collapsed",
        max_chars=int(hhs_ui.COMMAND_COLUMNS),
    )
    scroll_to_env_value_editor(editor_key)


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
    return (*hhs_ui.VIEWS, hhs_ui.AI_VIEW) if ollama_service_is_up() else hhs_ui.VIEWS


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
    cache_clear()
    close_home_tool_tldr_dialog()
    st.session_state["home_tool_action_operation"] = operation
    st.session_state["home_tool_action_name"] = tool_name
    st.session_state["home_tool_action_message"] = result.stdout or result.stderr or ""
    st.session_state["home_tool_action_succeeded"] = result.returncode == 0


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
    cache_clear()
    st.session_state["service_action_message"] = result.stdout or result.stderr or ""
    st.session_state["service_action_succeeded"] = result.returncode == 0
    reset_service_table_selection()


def apply_selected_process_kill(process_name: str) -> None:
    """Kill the selected process name and store the action result."""
    result = run_hhs_process_kill(process_name)
    cache_clear()
    st.session_state["monitor_process_action_message"] = (
        result.stdout or result.stderr or ""
    )
    st.session_state["monitor_process_action_succeeded"] = result.returncode == 0


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
            st.success(strip_ansi(action_message))
        else:
            st.error(strip_ansi(action_message))

    _, selected_row = render_table(
        rows,
        key=service_table_key(),
        action_hint="",
        table_data=styled_service_rows(rows),
        height=hhs_ui.ENV_TABLE_HEIGHT,
        width=hhs_ui.ENV_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Name']}",
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
    filter_col, other_filter_col = st.columns(
        hhs_ui.THREE_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        env_filter = st.radio(
            "Filters",
            hhs_ui.ENV_FILTERS,
            horizontal=True,
            index=1,
            key="env_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if env_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="env_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
            )
    result = run_hhs_envs(env_filter_pattern(env_filter, other_filter))
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list environment variables.")
        return
    render_env_rows(parse_hhs_envs(result.stdout))


def render_paths_table() -> None:
    """Render PATH entries using __hhs_paths."""
    filter_col, other_filter_col = st.columns(
        hhs_ui.PATH_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        path_filter = st.radio(
            "Filters",
            hhs_ui.PATH_FILTERS,
            horizontal=True,
            index=0,
            key="path_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if path_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="path_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
            )
    result = run_hhs_paths()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list PATH entries.")
        return
    render_path_rows(
        filter_path_rows(parse_hhs_paths(result.stdout), path_filter, other_filter)
    )


def render_dirs_table() -> None:
    """Render saved directories using __hhs_load_dir."""
    filter_col, other_filter_col = st.columns(
        hhs_ui.TWO_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        dirs_filter = st.radio(
            "Filters",
            hhs_ui.LIST_FILTERS,
            horizontal=True,
            index=0,
            key="dirs_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if dirs_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="dirs_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
            )
    result = run_hhs_dirs()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list saved directories.")
        return
    render_read_only_rows(
        filter_rows_by_text(parse_hhs_dirs(result.stdout), dirs_filter, other_filter),
        dir_table_key(),
        hhs_ui.DIR_VALUE_EDITOR_KEY_PREFIX,
        "Selected DIR value",
    )


def render_cmds_table() -> None:
    """Render saved commands using __hhs_command."""
    filter_col, other_filter_col = st.columns(
        hhs_ui.TWO_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        cmds_filter = st.radio(
            "Filters",
            hhs_ui.LIST_FILTERS,
            horizontal=True,
            index=0,
            key="cmds_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if cmds_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="cmds_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
            )
    result = run_hhs_commands()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list saved commands.")
        return
    render_read_only_rows(
        filter_rows_by_text(
            parse_hhs_commands(result.stdout), cmds_filter, other_filter
        ),
        cmd_table_key(),
        hhs_ui.CMD_VALUE_EDITOR_KEY_PREFIX,
        "Selected COMMAND value",
    )


def render_aliases_table() -> None:
    """Render custom aliases using __hhs_aliases."""
    filter_col, other_filter_col = st.columns(
        hhs_ui.TWO_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        alias_filter = st.radio(
            "Filters",
            hhs_ui.LIST_FILTERS,
            horizontal=True,
            index=0,
            key="alias_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if alias_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="alias_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
            )
    result = run_hhs_aliases()
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list custom aliases.")
        return
    render_read_only_rows(
        filter_rows_by_text(
            parse_hhs_aliases(result.stdout), alias_filter, other_filter
        ),
        alias_table_key(),
        hhs_ui.ALIAS_VALUE_EDITOR_KEY_PREFIX,
        "Selected ALIAS value",
    )


def render_services_table() -> None:
    """Render HomeSetup services using __hhs_services status output."""
    filter_col, other_filter_col = st.columns(
        hhs_ui.FOUR_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        service_filter = st.radio(
            "Filters",
            hhs_ui.SERVICE_FILTERS,
            horizontal=True,
            index=0,
            key="service_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if service_filter == "Other":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="service_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
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
    filter_col, other_filter_col = st.columns(
        hhs_ui.TWO_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        history_commands_filter = st.radio(
            "Filters",
            hhs_ui.HISTORY_FILTERS,
            horizontal=True,
            index=0,
            key="history_commands_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if history_commands_filter == "Others":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="history_commands_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
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
        hhs_ui.HISTORY_COMMAND_VALUE_EDITOR_KEY_PREFIX,
        "Selected COMMANDS value",
    )


def render_history_directories_table() -> None:
    """Render directory history using __hhs_dirs."""
    filter_col, other_filter_col = st.columns(
        hhs_ui.TWO_OPTION_FILTER_COLUMNS, vertical_alignment="bottom"
    )
    with filter_col:
        history_directories_filter = st.radio(
            "Filters",
            hhs_ui.HISTORY_FILTERS,
            horizontal=True,
            index=0,
            key="history_directories_filter",
            on_change=save_ui_state,
        )
    other_filter = ""
    if history_directories_filter == "Others":
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key="history_directories_other_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Type filter text",
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
        hhs_ui.HISTORY_DIRECTORY_VALUE_EDITOR_KEY_PREFIX,
        "Selected DIRECTORIES value",
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
    dir_label_col, dir_input_col, top_label_col, top_input_col, spacer_col = st.columns(
        [0.85, 3.25, 0.55, 0.95, 0.15],
        vertical_alignment="center",
    )
    with dir_label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Directory</span>',
            unsafe_allow_html=True,
        )
    with dir_input_col:
        directory = st.text_input(
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
        top_n = st.number_input(
            "Top N",
            min_value=1,
            max_value=100,
            step=1,
            key="monitor_disk_top_n",
            label_visibility="collapsed",
            on_change=save_ui_state,
        )
    selected_directory = directory.strip() or monitor_default_disk_directory()
    result = run_hhs_disk_usage(selected_directory, int(top_n))
    if result.returncode != 0:
        st.error(
            strip_ansi(result.stderr or result.stdout or "Unable to load disk usage.")
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
    st.markdown(f"##### Top {int(top_n)} disk usage at `{selected_directory}`")
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
            st.success(strip_ansi(action_message))
        else:
            st.error(strip_ansi(action_message))

    label_col, input_col = st.columns([0.55, 3.45], vertical_alignment="center")
    with label_col:
        st.markdown(
            '<span class="hhs-inline-form-label">Filters</span>', unsafe_allow_html=True
        )
    with input_col:
        process_filter = st.text_input(
            "Filters",
            key="monitor_process_filter",
            label_visibility="collapsed",
            on_change=save_ui_state,
            placeholder="Type process filter",
        )
    result = run_hhs_process_list(process_filter)
    if result.returncode != 0:
        st.error(
            strip_ansi(result.stderr or result.stdout or "Unable to load processes.")
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
    label_col, input_col, tail_col = st.columns(
        [0.55, 3.0, 0.45], vertical_alignment="center"
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
    with tail_col:
        tail_enabled = st.checkbox(
            "Tail",
            key="monitor_logs_tail",
            on_change=save_ui_state,
        )
    st.markdown(
        f'<div class="hhs-log-file-title"><code>{html.escape(selected_log)}</code></div>',
        unsafe_allow_html=True,
    )
    if tail_enabled:
        render_monitor_logs_tail(selected_log)
    else:
        render_monitor_logs_once(selected_log)


@st.fragment(run_every="5s")
def render_monitor_logs_tail(selected_log: str) -> None:
    """Render a tail-like log pane that refreshes only while LOGS is active."""
    render_monitor_logs_once(selected_log)


def render_monitor_logs_once(selected_log: str) -> None:
    """Render the selected log once without automatic refresh."""
    result = run_hhs_logs(selected_log, 200)
    if result.returncode != 0:
        st.error(strip_ansi(result.stderr or result.stdout or "Unable to load logs."))
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
          <h2>Configurations</h2>
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
          <h2>Services</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    render_services_table()


def render_history_view() -> None:
    """Render the command and directory history view."""
    st.markdown(
        """
        <section class="hhs-view-heading">
          <h2>History</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    history_view = st.segmented_control(
        "History view",
        options=hhs_ui.HISTORY_VIEWS,
        default=st.session_state["history_view"],
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
          <h2>Monitor</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    monitor_view = st.segmented_control(
        "Monitor view",
        options=hhs_ui.MONITOR_VIEWS,
        default=st.session_state["monitor_view"],
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
    meta_col, context_col, clear_col = st.columns(
        [3.0, 0.55, 0.55], vertical_alignment="center"
    )
    with meta_col:
        st.markdown(
            f"""
            <div class="hhs-ai-chat-meta">
              <span>User: <strong class="hhs-ai-chat-user">{html.escape(username)}</strong></span>
              <span>Model: <strong class="hhs-ai-chat-model">{html.escape(ollama_model)}[{html.escape(context_size)}]</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with context_col:
        st.button(
            "Context",
            key="ai_show_context_button",
            help="Show current Ollama context",
            on_click=show_ai_chat_context,
            width="stretch",
        )
    with clear_col:
        st.button(
            "Clear",
            key="ai_clear_chat_button",
            help="Clear chat history",
            on_click=request_ai_chat_clear_confirmation,
            disabled=not st.session_state["ai_chat_messages"],
            width="stretch",
        )
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
            result = run_hhs_ask(prompt)
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
        selected_label=lambda row, _index: (
            f'<div class="hhs-ai-selected-model">Selected: <strong>{html.escape(row["Name"])}</strong></div>'
        ),
        selected_label_html=True,
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
            {
                "label": "Delete Model",
                "key_prefix": "ai_delete_model_button",
                "on_click": request_ai_model_deletion,
                "visible": lambda row, _index: str(row.get("Status", ""))
                in ("Active", "Downloaded"),
                "args": lambda row, _index: (row["Name"], str(row.get("Status", ""))),
            },
        ],
        action_column_weights=[1, 1, 2],
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
          <h2>Ask Ollama HomeSetup AI</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    ai_view = st.segmented_control(
        "AI view",
        options=hhs_ui.AI_VIEWS,
        default=st.session_state["ai_view"],
        key="ai_view",
        label_visibility="collapsed",
        on_change=save_ui_state,
        width="stretch",
    )
    st.write("")
    if ai_view == "CHAT":
        render_ai_chat_panel()
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
        format_func=str.upper,
        on_change=save_ui_state,
    )
    if active_view == "Home":
        render_home_view()
    elif active_view == "Configs":
        render_configs_view()
    elif active_view == "Services":
        render_service_view()
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
        layout="wide",
    )
    restore_ui_state()
    restore_persisted_theme_selection()
    render_styles()
    handle_footer_actions()
    if st.session_state.get("theme_reload_pending"):
        render_theme_reload_overlay()
    st.session_state.setdefault("active_view", "Home")
    if st.session_state["active_view"] not in (*hhs_ui.VIEWS, hhs_ui.AI_VIEW):
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
        "monitor_disk_directory", monitor_default_disk_directory()
    )
    if not str(st.session_state["monitor_disk_directory"]).strip():
        st.session_state["monitor_disk_directory"] = monitor_default_disk_directory()
    st.session_state.setdefault("monitor_disk_top_n", 10)
    if not isinstance(st.session_state["monitor_disk_top_n"], int):
        st.session_state["monitor_disk_top_n"] = 10
    st.session_state.setdefault("monitor_log_file", "")
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
    render_footer()


if __name__ == "__main__":
    main()
