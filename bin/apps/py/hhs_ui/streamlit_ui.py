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
import posixpath
import subprocess
import sys
import time
import urllib.parse
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.command_catalog import (
    normalized_monitor_top_n,
    normalized_history_stats_top_n,
    normalized_monitor_disk_top_n,
    normalized_monitor_log_tail_lines,
    strip_ansi,
    clean_command_status_message,
    service_action_status_message,
    updater_output_has_updates,
    format_hhs_sysinfo_markdown,
    docker_cli_table_rows,
    docker_container_is_up,
    build_hhs_envs_command,
    build_hhs_env_action_command,
    build_hhs_sysinfo_command,
    build_hhs_updater_command,
    build_hhs_tools_command,
    build_hhs_shopt_command,
    build_hhs_shopt_action_command,
    build_docker_ps_command,
    build_docker_images_command,
    build_docker_agent_check_command,
    build_docker_container_action_command,
    build_docker_image_delete_command,
    build_hhs_hspm_command,
    build_tool_tldr_command,
    build_hhs_history_command,
    build_hhs_history_dirs_command,
    build_hhs_process_kill_command,
    build_hhs_paths_command,
    build_hhs_path_action_command,
    build_hhs_dirs_command,
    build_hhs_dir_action_command,
    build_hhs_commands_command,
    build_hhs_command_action_command,
    build_hhs_aliases_command,
    build_hhs_alias_action_command,
    build_hhs_services_command,
    row_matches_text_filter,
    filter_env_rows,
    filter_shopt_rows,
    filter_path_rows,
    filter_rows_by_text,
    filter_process_rows,
    parse_hhs_envs,
    parse_hhs_tools,
    parse_hhs_shopt,
    parse_hhs_dirs,
    parse_hhs_commands,
    parse_hhs_aliases,
    parse_hhs_services,
    parse_hhs_history,
    parse_hhs_history_dirs,
    parse_process_monitor,
    path_entries,
    parse_hhs_paths,
    env_value_editor_key,
    dir_value_editor_key,
    cmd_value_editor_key,
    alias_value_editor_key,
)
from hhs_ui.core.process_resources import install_footer_status_log_handler
from hhs_ui.core.paths import (
    homesetup_home,
)
from hhs_ui.features.search_core import (
    normalized_search_type,
)
from hhs_ui.execution import cache_runtime, command_runtime
from hhs_ui.features import (
    ai_ui,
    hhs_app_ui,
    monitor_ui,
    search_ui,
    ssh_explorer_ui,
    ssh_runtime,
)
from hhs_ui.widgets import (
    dialog_ui,
    dom_scripts,
    feedback_ui,
    footer_ui,
    path_picker as path_picker_ui,
    status_ui,
    terminal_ui,
)
from hhs_ui.features.ai_ui import (
    clear_ai_chat_history,
    execute_pending_ai_context_action,
    execute_pending_ai_prompt_action,
    render_ai_view,
    reset_ai_model_table_selection,
    ui_disposable_files_dir,
)
from hhs_ui.execution.cache_runtime import (
    cache_background_command_result,
    cache_delete_tag,
    cache_get,
    cache_set,
    cached_background_command_result,
    cache_value_from_completed_process,
    command_cache_key,
    command_result_snapshot_get,
    command_result_snapshot_set,
    completed_process_from_cache,
    complete_cached_background_command,
    parse_rows_cached,
    render_cached_command_result,
    safe_cache_tag,
    start_cached_background_command,
    sync_ui_cache_file,
)
from hhs_ui.widgets.dialog_ui import execute_pending_dialog_callback, pop_dialog
from hhs_ui.widgets.dom_scripts import render_combobox_vt100_shortcuts_script
from hhs_ui.widgets.feedback_ui import (
    clear_preloader,
    render_command_loader,
    render_command_preloader_events,
    render_terminal_output,
    render_theme_reload_overlay,
)
from hhs_ui.widgets.footer_ui import (
    footer_working_directory,
    handle_footer_actions,
    render_footer_client_error_bridge_script,
    render_footer_shell_version_dialog,
    render_footer_status_fragment,
    update_remote_footer_working_directory,
)
from hhs_ui.features.hhs_app_ui import (
    clear_firebase_aliases_cache,
    execute_pending_hhs_firebase_action,
    execute_pending_hhs_settings_action,
    execute_pending_hhs_setup_action,
    execute_pending_hhs_starship_action,
    render_hhs_view,
)
from hhs_ui.features.monitor_runtime import (
    monitor_default_disk_directory,
    monitor_process_top_n_state_key,
    selected_monitor_log_level,
    synchronize_monitor_disk_directory_with_host,
)
from hhs_ui.features.monitor_ui import (
    render_history_stats_chart,
    render_monitor_disk_chart,
    render_monitor_logs_panel,
    render_process_monitor_chart,
    render_monitor_processes_panel,
)
from hhs_ui.features.search_ui import (
    execute_pending_search_open_action,
    expand_path_with_environment,
    initialize_search_directory_home_default,
    normalize_search_directories,
    open_search_result_path,
    remote_environment_values,
    render_search_view,
    reset_search_directory_to_home,
)
from hhs_ui.features.ssh_explorer_ui import (
    build_scp_to_local_command,
    execute_pending_ssh_explorer_action,
    execute_pending_ssh_explorer_delete,
    open_remote_explorer_path,
    render_ssh_view,
    ssh_explorer_mtime_text,
    ssh_explorer_size_text,
)
from hhs_ui.execution.command_runtime import (
    background_job_is_running,
    background_job_result,
    background_job_state_key,
    render_background_job_polling_fragment,
    render_background_job_status,
    render_background_job_status_if_blocking,
    run_bash_command,
    start_background_bash_command,
    stop_background_job,
    stop_background_jobs_with_state_prefix,
)
from hhs_ui.widgets.path_picker import (
    apply_pending_folder_picker_selection,
    render_folder_picker_dialog,
    request_folder_picker,
    stop_path_picker_listing_jobs,
)
from hhs_ui.features.ssh_runtime import (
    clear_registered_ssh_connection,
    command_remote_host,
    command_timeout_seconds,
    connected_ssh_host,
    dismiss_streamlit_dialog,
    effective_bash_command,
    effective_command_timeout_seconds,
    execute_pending_ssh_connection,
    execute_pending_ssh_disconnection,
    handle_remote_command_result,
    host_selector_options,
    render_ssh_connection_dialog,
    request_ssh_host_connect,
    request_ssh_host_disconnection,
    restore_registered_ssh_connection_on_session_start,
    selected_host_is_local,
    selected_ssh_host,
    selected_ssh_host_is_connected,
    select_ssh_host_from_widget,
    ssh_connection_is_alive,
    synchronize_selected_ssh_host_with_connection,
)
from hhs_ui.widgets.terminal_ui import (
    clear_ttyd_exit_request,
    render_browser_cleanup_script,
    render_terminal_document_view,
    render_ttyd_terminal_frame_hide_script,
    stop_ttyd_session,
)
from hhs_ui.widgets.status_ui import (
    push_floating_status,
)
from hhs_ui.widgets.table_ui import (
    clean_table_text_filter_value,
    cmd_column_config,
    config_filter_columns,
    config_filter_display_label,
    config_filter_return_value,
    home_shopt_is_off,
    home_shopt_is_on,
    home_tool_is_aliased,
    home_tool_is_installed,
    home_tool_is_not_found,
    history_command_column_config,
    history_command_table_data,
    history_directory_column_config,
    history_directory_table_data,
    normalize_persisted_table_text_filter_states,
    normalized_table_filter_selection,
    path_column_config,
    render_read_only_rows,
    render_table,
    render_table_controls_panel,
    render_table_filter_controls,
    styled_path_rows,
    styled_service_rows,
    styled_shopt_rows,
    styled_tool_rows,
    table_filter_mapping,
)
from hhs_ui.features.ssh_core import (
    local_hostname,
    ssh_config_hostname,
)
from hhs_ui.core.theme_assets import (
    available_theme_options,
    configure_app_font_theme,
    default_theme_name,
    format_datetime,
    load_app_image_data_uri,
    render_styles,
    validated_theme_name,
)
from hhs_ui.core.ui_state import (
    load_ui_state,
    persisted_theme_name,
    restore_persisted_theme_selection,
    restore_ui_state,
    save_ui_state,
    unlink_legacy_ui_state_files,
)
from hhs_ui.core.ui_definitions import (
    ALIAS_LIST_JOB,
    CONFIG_ACTION_JOB,
    DOCKER_ACTION_JOB,
    HHS_HSPM_CATALOG_CACHE_TAG,
    HOME_TOOL_ACTION_JOB,
    HOME_TOOL_TLDR_JOB,
    MONITOR_PROCESS_ACTION_JOB,
    SEARCH_OPEN_JOB,
    SERVICE_ACTION_JOB,
    SERVICE_LIST_JOB,
    UPDATER_CHECK_JOB,
    UPDATER_UPDATE_JOB,
)


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
    unlink_legacy_ui_state_files()


def request_theme_reload() -> None:
    """Persist the selected theme and schedule the theme loading overlay."""
    selected_theme = validated_theme_name(
        st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    )
    if selected_theme:
        persist_theme_selection(selected_theme)
        st.session_state["theme_reload_pending"] = True
        st.session_state["theme_reload_name"] = selected_theme


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


def render_sidebar_title_separator_alignment_script() -> None:
    """Align the sidebar title separator with the rendered sidebar controls."""
    render_script_html("""
        <script>
        (() => {
          const parentWindow = window.parent || window;
          const doc = parentWindow.document;
          const syncSeparator = () => {
            const title = doc.querySelector(".hhs-sidebar-title");
            const controls = [
              ...doc.querySelectorAll(
                '.st-key-ssh_host_selector [data-testid="stSelectbox"], ' +
                'div[class*="st-key-ssh_host_connected_display_"] [data-testid="stSelectbox"], ' +
                '.st-key-theme_selected [data-testid="stSelectbox"]'
              ),
            ];
            const control = controls.find((candidate) => {
              const rect = candidate.getBoundingClientRect();
              return rect.width > 0 && rect.height > 0;
            });
            if (!title || !control) {
              return;
            }
            const titleRect = title.getBoundingClientRect();
            const controlRect = control.getBoundingClientRect();
            const separatorLeft = Math.max(0, controlRect.left - titleRect.left);
            doc.documentElement.style.setProperty(
              "--hhs-sidebar-title-separator-left",
              `${separatorLeft}px`
            );
            doc.documentElement.style.setProperty(
              "--hhs-sidebar-title-separator-width",
              `${controlRect.width}px`
            );
          };
          syncSeparator();
          parentWindow.requestAnimationFrame(syncSeparator);
          parentWindow.setTimeout(syncSeparator, 100);
          parentWindow.setTimeout(syncSeparator, 500);
          if (parentWindow.__hhsSidebarTitleSeparatorSync !== true) {
            parentWindow.__hhsSidebarTitleSeparatorSync = true;
            parentWindow.addEventListener("resize", syncSeparator);
          }
        })();
        </script>
        """)


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


def deactivate_terminal_document_view() -> None:
    """Stop ttyd resources when the Terminal session must reset."""
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


def render_script_html(
    body: str,
    *,
    height: int | None = None,
    width: int | str | None = None,
) -> None:
    """Render trusted in-app JavaScript without deprecated component HTML."""
    del height, width
    st.html(
        f'<span class="hhs-script-only" aria-hidden="true"></span>{body}',
        unsafe_allow_javascript=True,
    )


def render_persisted_expander_state_script(
    marker_selector: str, storage_key: str, default_expanded: bool = True
) -> None:
    """Persist one Streamlit expander open state in browser storage."""
    render_script_html(
        f"""
        <script>
          (() => {{
            const parentWindow = window.parent || window;
            const doc = parentWindow.document;
            const markerSelector = {json.dumps(marker_selector)};
            const storageKey = {json.dumps(storage_key)};
            const defaultExpanded = {json.dumps(default_expanded)};
            const readExpanded = () => {{
              try {{
                const stored = parentWindow.localStorage.getItem(storageKey);
                return stored === null ? defaultExpanded : stored === "true";
              }} catch (_error) {{
                return defaultExpanded;
              }}
            }};
            const writeExpanded = (expanded) => {{
              try {{
                parentWindow.localStorage.setItem(storageKey, expanded ? "true" : "false");
              }} catch (_error) {{}}
            }};
            const bindExpander = (attempt = 0) => {{
              const marker = doc.querySelector(markerSelector);
              const expander = marker?.closest("details");
              if (!expander) {{
                if (attempt < 12) {{
                  parentWindow.setTimeout(() => bindExpander(attempt + 1), 80);
                }}
                return;
              }}
              const expanded = readExpanded();
              if (expander.open !== expanded) {{
                expander.open = expanded;
              }}
              if (expander.dataset.hhsPersistedExpanderStateKey === storageKey) {{
                return;
              }}
              expander.dataset.hhsPersistedExpanderStateKey = storageKey;
              expander.addEventListener("toggle", () => {{
                writeExpanded(expander.open);
              }});
            }};
            bindExpander();
          }})();
        </script>
        """,
        height=0,
        width=0,
    )


def close_document_view(reset_terminal: bool = False) -> None:
    """Close the document view and restore the previous main view."""
    previous_view = st.session_state.get(hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY, "Home")
    if reset_terminal and terminal_document_view_is_active():
        deactivate_terminal_document_view()
    st.session_state[hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = False
    if previous_view in hhs_ui.VIEWS:
        st.session_state["active_view"] = previous_view
    save_ui_state()


def render_terminal_back_button_cleanup_script() -> None:
    """Attach browser-side ttyd iframe hiding to the document Back button."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            const detachTerminalFrameSync = () => {
              if (parentWindow.__hhsTtydFrameSyncCleanup) {
                parentWindow.__hhsTtydFrameSyncCleanup();
                parentWindow.__hhsTtydFrameSyncCleanup = null;
              }
              if (parentWindow.__hhsTtydExitBackHandler) {
                parentWindow.removeEventListener("message", parentWindow.__hhsTtydExitBackHandler);
                parentWindow.__hhsTtydExitBackHandler = null;
              }
            };
            const hideFrame = () => {
              detachTerminalFrameSync();
              const frame = doc.getElementById("hhs-persistent-ttyd-frame");
              if (frame) {
                frame.style.display = "none";
              }
            };
            const removeFrame = () => {
              detachTerminalFrameSync();
              const frame = doc.getElementById("hhs-persistent-ttyd-frame");
              if (frame) {
                frame.remove();
              }
            };
            const triggerBack = () => {
              removeFrame();
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
            button.addEventListener("click", hideFrame, { capture: true });
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
        help="Open the interactive terminal.",
        on_click=open_document_view,
        args=("TERMINAL",),
        width="stretch",
    )


def terminal_document_view_is_active() -> bool:
    """Return whether the Terminal document view is currently active."""
    return bool(st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY)) and (
        st.session_state.get(hhs_ui.DOCUMENT_SELECTED_KEY) == "TERMINAL"
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
                help="Shows the active connected host.",
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
                help="Choose the local machine or an SSH host.",
                on_change=select_ssh_host_from_widget,
                width="stretch",
            )
        if connected_host or not selected_host_is_local():
            if connected_host:
                st.button(
                    "ﮤ Disconnect",
                    key="ssh_disconnect_button",
                    help="Disconnect from the current SSH host.",
                    on_click=request_ssh_host_disconnection,
                    width="stretch",
                )
            else:
                st.button(
                    "ﮣ Connect",
                    key="ssh_connect_button",
                    help="Connect to the selected SSH host.",
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
            help="Choose the HomeSetup color theme.",
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
        render_sidebar_title_separator_alignment_script()
        st.markdown(
            '<hr class="hhs-sidebar-separator" />',
            unsafe_allow_html=True,
        )
        if st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY):
            st.button(
                "BACK",
                key="document_back_button",
                help="Return to the previous HomeSetup view.",
                on_click=close_document_view,
                width="stretch",
            )
            if terminal_document_view_is_active():
                render_terminal_back_button_cleanup_script()
        else:
            render_ttyd_terminal_frame_hide_script()
            st.button(
                " README",
                key="readme_open_button",
                help="Open the HomeSetup README.",
                on_click=open_document_view,
                args=("README",),
                width="stretch",
            )
            st.button(
                " HANDBOOK",
                key="handbook_open_button",
                help="Open the HomeSetup handbook.",
                on_click=open_document_view,
                args=("HANDBOOK",),
                width="stretch",
            )
            render_sidebar_terminal_button()


def render_home_view() -> None:
    """Render the Home informational view."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> System</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    home_view = render_view_segmented_control(
        "Home view",
        hhs_ui.HOME_VIEWS,
        "home_view",
        "System",
        format_func=home_view_label,
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


def view_segmented_control_widget_key(state_key: str) -> str:
    """Return the temporary widget key for a persisted sub-view state key."""
    return f"{state_key}_widget"


def active_view_widget_key() -> str:
    """Return the temporary widget key for the top-level navigation control."""
    return view_segmented_control_widget_key("active_view")


def fallback_main_view(visible_views: tuple[str, ...]) -> str:
    """Return the non-persistent fallback main view for a temporarily hidden tab."""
    if "Home" in visible_views:
        return "Home"
    return visible_views[0] if visible_views else "Home"


def save_active_view_state(
    widget_key: str,
    visible_views: tuple[str, ...],
) -> None:
    """Copy a user-selected main tab into persisted UI state."""
    value = st.session_state.get(widget_key)
    if value in visible_views:
        st.session_state["active_view"] = value
    save_ui_state()


def normalized_active_view_value(visible_views: tuple[str, ...]) -> str:
    """Return the active main view without persisting transient visibility fallbacks."""
    current_value = st.session_state.get("active_view")
    if current_value in visible_views:
        return str(current_value)
    persisted_value = load_ui_state().get("active_view")
    if persisted_value in visible_views:
        st.session_state["active_view"] = persisted_value
        return str(persisted_value)
    return fallback_main_view(visible_views)


def render_active_view_control(visible_views: tuple[str, ...]) -> str:
    """Render the top-level navigation tabs while preserving durable tab state."""
    selected_value = normalized_active_view_value(visible_views)
    widget_key = active_view_widget_key()
    widget_value = st.session_state.get(widget_key)
    if widget_value in visible_views and widget_value != selected_value:
        st.session_state[widget_key] = selected_value
    elif widget_value not in visible_views:
        st.session_state[widget_key] = selected_value
    active_view = st.radio(
        "View",
        visible_views,
        horizontal=True,
        index=None,
        key=widget_key,
        label_visibility="collapsed",
        help="Choose the HomeSetup section to display.",
        format_func=main_view_label,
        on_change=save_active_view_state,
        args=(widget_key, visible_views),
    )
    if active_view not in visible_views:
        return selected_value
    return str(active_view)


def save_view_segmented_control_state(
    state_key: str,
    widget_key: str,
    options: tuple[str, ...],
) -> None:
    """Copy a temporary segmented-control widget value into persisted UI state."""
    value = st.session_state.get(widget_key)
    if value in options:
        st.session_state[state_key] = value
    save_ui_state()


def normalized_view_segmented_control_value(
    state_key: str,
    options: tuple[str, ...],
    default: str,
) -> str:
    """Return a valid persisted sub-view segmented-control value."""
    value = st.session_state.get(state_key, default)
    if value in options:
        return str(value)
    return default


def render_view_segmented_control(
    label: str,
    options: tuple[str, ...],
    state_key: str,
    default: str,
    format_func: Callable[[str], str],
) -> str:
    """Render a persisted sub-view segmented control with a stable selected state."""
    selected_value = normalized_view_segmented_control_value(
        state_key, options, default
    )
    st.session_state[state_key] = selected_value
    widget_key = view_segmented_control_widget_key(state_key)
    widget_value = st.session_state.get(widget_key)
    if widget_value in options and widget_value != selected_value:
        st.session_state[widget_key] = selected_value
        widget_value = selected_value
    elif widget_value not in options:
        st.session_state.pop(widget_key, None)
    default_value = selected_value if widget_value not in options else None
    view_value = st.segmented_control(
        label,
        options=options,
        default=default_value,
        required=True,
        format_func=format_func,
        key=widget_key,
        label_visibility="collapsed",
        help=f"Choose the {label.lower()} to display.",
        on_change=save_view_segmented_control_state,
        args=(state_key, widget_key, options),
        width="stretch",
    )
    if view_value not in options:
        view_value = selected_value
    st.session_state[state_key] = view_value
    return view_value


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
    execute_pending_docker_action()
    render_background_job_status(DOCKER_ACTION_JOB)
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


CONFIG_FILE_DEFINITIONS = {
    "ENV": ("HHS_ENV_FILE", ".env"),
    "PATH": ("HHS_PATHS_FILE", ".path"),
    "DIR": ("HHS_SAVED_DIRS_FILE", ".saved_dirs"),
    "CMD": ("HHS_CMD_FILE", ".cmd_file"),
    "ALIAS": ("HHS_ALIASES_FILE", ".aliases"),
}
CONFIG_FILE_PAGE_LABELS = {
    "ENV": "Environment",
    "PATH": "Paths",
    "DIR": "Saved Dirs",
    "CMD": "Saved Cmds",
    "ALIAS": "Aliases",
}


def default_config_file_path(file_name: str) -> str:
    """Return a default HomeSetup config file path for the active host."""
    if connected_ssh_host():
        values = remote_environment_values(["HHS_DIR", "HOME"])
        hhs_dir = values.get("HHS_DIR", "").strip()
        if not hhs_dir:
            home_dir = values.get("HOME", "").strip() or "~"
            hhs_dir = posixpath.join(home_dir, ".config/hhs")
        return posixpath.normpath(posixpath.join(hhs_dir, file_name))
    return str((hhs_ui.HHS_DIR / file_name).expanduser())


def config_file_path(config_view: str) -> str:
    """Return the backing custom config file path for one Configs page."""
    env_name, file_name = CONFIG_FILE_DEFINITIONS.get(
        config_view,
        CONFIG_FILE_DEFINITIONS["ENV"],
    )
    if connected_ssh_host():
        values = remote_environment_values([env_name, "HHS_DIR", "HOME"])
        raw_path = values.get(env_name, "").strip()
        if raw_path:
            return expand_path_with_environment(raw_path, values)
        return default_config_file_path(file_name)

    raw_path = os.environ.get(env_name, "").strip()
    if raw_path:
        return os.path.expandvars(os.path.expanduser(raw_path))
    return default_config_file_path(file_name)


def hhs_setup_file_path() -> str:
    """Return the effective HomeSetup setup file path for the active host."""
    env_name = "HHS_SETUP_FILE"
    file_name = ".homesetup.toml"
    if connected_ssh_host():
        values = remote_environment_values([env_name, "HHS_DIR", "HOME"])
        raw_path = values.get(env_name, "").strip()
        if raw_path:
            return expand_path_with_environment(raw_path, values)
        return default_config_file_path(file_name)

    raw_path = os.environ.get(env_name, "").strip()
    if raw_path:
        return os.path.expandvars(os.path.expanduser(raw_path))
    return default_config_file_path(file_name)


def file_uri_for_path(path_value: str) -> str:
    """Return a file URI for a POSIX-style absolute path."""
    clean_path = posixpath.normpath(path_value.strip())
    return f"file://{urllib.parse.quote(clean_path, safe='/')}"


def search_open_href(path_or_uri: str) -> str:
    """Return a Search-style open link for a path or file URI."""
    query = urllib.parse.urlencode({hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM: path_or_uri})
    return f"?{query}"


def openable_file_label(file_path: str) -> str:
    """Return the filename shown inside an openable file pill."""
    clean_file_path = file_path.strip()
    return posixpath.basename(clean_file_path.rstrip("/")) or clean_file_path


def render_openable_file_pill(label: str, file_path: str) -> None:
    """Render a clickable filename pill that opens the full file path."""
    clean_file_path = file_path.strip()
    if not clean_file_path:
        return
    file_uri = file_uri_for_path(clean_file_path)
    href = html.escape(search_open_href(file_uri), quote=True)
    safe_file_uri = html.escape(file_uri, quote=True)
    safe_label = html.escape(label.strip())
    safe_file_label = html.escape(openable_file_label(clean_file_path))
    st.markdown(
        (
            '<div class="hhs-config-file-pill-row">'
            f'<span class="hhs-config-file-pill-label">{safe_label}</span>'
            f'<a class="hhs-config-file-pill" href="{href}" '
            'target="_self" '
            f'title="{safe_file_uri}" '
            f'data-hhs-open-path="{safe_file_uri}">'
            f'<span aria-hidden="true"></span>{safe_file_label}</a>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_config_file_pill(config_view: str) -> None:
    """Render a clickable pill for the custom config file used by a Configs page."""
    file_path = config_file_path(config_view)
    if not file_path:
        return
    page_label = CONFIG_FILE_PAGE_LABELS.get(config_view, "Environment")
    render_openable_file_pill(
        f"Custom {page_label} file:",
        file_path,
    )


def render_filters_and_controls(
    name_label: str | None = "Name",
    value_label: str | None = "Value",
    has_plus_btn: bool = True,
    has_file_picker_btn: bool = False,
    filters: dict[str, str | None] | None = None,
    *,
    key_prefix: str,
    filter_key: str,
    other_filter_key: str,
    name_placeholder: str | None = None,
    value_placeholder: str | None = None,
    on_submit: Callable[[], None] | None = None,
    default_filter: str | None = None,
) -> tuple[str, str]:
    """Render a Config Filters & Controls expander and return filter selections."""
    filter_map = filters or {"All": None, "Containing": None}
    filter_labels = tuple(filter_map)
    default_label = config_filter_display_label(
        filter_map,
        default_filter,
        filter_labels[0],
    )
    st.session_state[filter_key] = config_filter_display_label(
        filter_map,
        st.session_state.get(filter_key, default_label),
        default_label,
    )
    with st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True):
        render_config_add_controls(
            key_prefix,
            name_label,
            value_label,
            name_placeholder or name_label or "",
            value_placeholder or value_label or "",
            on_submit=on_submit,
            has_plus_btn=has_plus_btn,
            has_file_picker_btn=has_file_picker_btn,
        )
        selected_label, other_filter = render_table_filter_controls(
            filter_labels,
            filter_key,
            other_filter_key,
            config_filter_columns(filter_map),
            index=filter_labels.index(default_label),
            other_options=(filter_labels[-1],),
        )
    return config_filter_return_value(filter_map, selected_label), other_filter


def config_add_columns(weights: list[float]) -> list:
    """Return Config add-row columns with the standard horizontal gap."""
    return st.columns(
        weights,
        gap="small",
        vertical_alignment="bottom",
    )


def render_config_add_controls(
    key_prefix: str,
    name_label: str | None,
    value_label: str | None,
    name_placeholder: str,
    value_placeholder: str,
    *,
    on_submit: Callable[[], None] | None = None,
    has_plus_btn: bool = True,
    has_file_picker_btn: bool = False,
) -> None:
    """Render the Config add-row inputs and action buttons."""
    if value_label is None:
        return

    action_weights = []
    if has_plus_btn:
        action_weights.append(0.2 if name_label else 0.035)
    if has_file_picker_btn:
        action_weights.append(0.19 if name_label else 0.035)

    if name_label is None:
        columns = config_add_columns([1, *action_weights])
        value_col = columns[0]
        action_cols = columns[1:]
        name_col = None
    else:
        value_weight = 4.05 if has_file_picker_btn else 4.2
        columns = config_add_columns([1.375, value_weight, *action_weights])
        name_col = columns[0]
        value_col = columns[1]
        action_cols = columns[2:]

    if name_col is not None and name_label is not None:
        with name_col:
            st.text_input(
                name_label,
                key=f"{key_prefix}_add_name",
                placeholder=name_placeholder,
                help=f"Enter the {name_label.lower()}.",
            )
    value_input_args: dict[str, object] = {
        "key": f"{key_prefix}_add_value",
        "placeholder": value_placeholder,
    }
    if on_submit is not None:
        value_input_args["on_change"] = on_submit
    with value_col:
        st.text_input(
            value_label,
            help=f"Enter the {value_label.lower()}.",
            **value_input_args,
        )

    action_index = 0
    if has_plus_btn:
        with action_cols[action_index]:
            st.button(
                "",
                key=f"{key_prefix}_add_submit",
                help="Add",
                on_click=on_submit,
                width="stretch",
            )
        action_index += 1
    if has_file_picker_btn:
        with action_cols[action_index]:
            st.button(
                "",
                key=f"{key_prefix}_folder_picker_button",
                help="Select folder",
                on_click=request_folder_picker,
                args=(f"{key_prefix}_add_value", value_placeholder),
                width="stretch",
            )


def render_home_tools_panel() -> None:
    """Render HomeSetup development tool checks on the Home view."""
    execute_pending_home_tool_action()
    execute_pending_home_tool_tldr()
    home_tool_action_dialog_opened = render_home_tool_action_dialog()
    if not home_tool_action_dialog_opened:
        render_home_tool_tldr_dialog()
    render_background_job_status(HOME_TOOL_ACTION_JOB)
    render_background_job_status(HOME_TOOL_TLDR_JOB)

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
    execute_pending_config_action()
    render_background_job_status(CONFIG_ACTION_JOB)
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


def updater_check_context() -> str:
    """Return the active updater check context for local or SSH execution."""
    host = connected_ssh_host()
    return f"ssh:{host}" if host else "local"


def restore_local_updater_status() -> None:
    """Restore the footer update icon state from the latest local check."""
    output = str(st.session_state.get("updater_last_check_output", ""))
    st.session_state["updater_update_available"] = updater_output_has_updates(output)
    st.session_state["updater_check_context"] = "local"


def reset_updater_remote_check_state() -> None:
    """Clear updater context state so the active SSH host is checked fresh."""
    st.session_state["updater_check_started_context"] = ""
    st.session_state["updater_remote_checked_context"] = ""
    st.session_state["updater_check_context"] = ""
    st.session_state["updater_update_available"] = False


def start_updater_check(
    context: str, force_local: bool, show_preloader_event: bool = True
) -> None:
    """Start a HomeSetup updater check for the given execution context."""
    started = start_background_bash_command(
        UPDATER_CHECK_JOB,
        build_hhs_updater_command("check"),
        "Checking HomeSetup updates",
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        force_local=force_local,
        metadata={"updater_context": context},
        show_preloader_event=show_preloader_event,
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
        st.session_state["updater_last_check_output"] = output
        save_ui_state()
    else:
        st.session_state["updater_remote_checked_context"] = context
    if result.returncode == 0:
        return
    push_floating_status(output or "Unable to check HomeSetup updates.", "warn")


def execute_due_updater_check() -> None:
    """Start or complete one updater check for the active execution context."""
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
    st.session_state["updater_check_attempted"] = True
    start_updater_check("local", force_local=True)


def execute_mount_updater_check() -> None:
    """Start one local updater check for each Streamlit browser session mount."""
    if bool(st.session_state.get("updater_mount_check_attempted", False)):
        return
    st.session_state["updater_mount_check_attempted"] = True
    st.session_state["updater_check_attempted"] = True
    if background_job_is_running(UPDATER_CHECK_JOB):
        return
    start_updater_check("local", force_local=True, show_preloader_event=False)


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


def start_hhs_services_list_refresh(completion_rerun: bool = True) -> bool:
    """Start a background refresh for the services list."""
    command, _command_to_run, _remote_host, _cache_key = hhs_services_command_context()
    started = start_cached_background_command(
        SERVICE_LIST_JOB,
        command,
        "Loading services",
        "services",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        completion_rerun=completion_rerun,
    )
    if started:
        st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_REFRESHED_AT_KEY] = (
            time.time()
        )
    return started


def complete_hhs_services_list_refresh() -> subprocess.CompletedProcess[str] | None:
    """Complete a background services-list refresh and cache successful output."""
    completed = background_job_result(SERVICE_LIST_JOB)
    if completed is None:
        return None
    result, metadata = completed
    if str(metadata.get("remote_host", "")).strip() != command_remote_host():
        return None
    if result.returncode == 0:
        cache_background_command_result(metadata, result)
        st.session_state["service_list_error"] = ""
    else:
        st.session_state["service_list_error"] = strip_ansi(
            result.stderr or result.stdout or "Unable to list services."
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
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_CONTEXT_KEY] = (
        ai_service_availability_context()
    )
    start_hhs_services_list_refresh()


def update_ollama_service_availability_refresh() -> None:
    """Complete or poll the services refresh that drives AI tab visibility."""
    previous_availability = ollama_service_is_available()
    result = complete_hhs_services_list_refresh()
    if result is not None and ollama_service_is_available() != previous_availability:
        st.rerun()
    if background_job_is_running(SERVICE_LIST_JOB):
        return
    if ollama_service_availability_refresh_due():
        start_hhs_services_list_refresh(completion_rerun=False)


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
    if tools_filter in ("Other", "Containing"):
        return [row for row in rows if row_matches_text_filter(row, other_filter)]
    return rows


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
    if service_filter in ("Other", "Containing"):
        return [row for row in rows if row_matches_text_filter(row, text_filter)]
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
    reset_counter = st.session_state.setdefault(
        hhs_ui.HOME_TOOLS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui.HOME_TOOLS_TABLE_RESET_COUNTER_KEY] = reset_counter
    return f"home_tools_table_{reset_counter}"


def reset_home_tools_table_selection() -> None:
    """Reset the Home Tools dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui.HOME_TOOLS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui.HOME_TOOLS_TABLE_RESET_COUNTER_KEY] = reset_counter + 1


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


def hhs_settings_table_key() -> str:
    """Return the HHS Settings dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui_constants.HHS_SETTINGS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui_constants.HHS_SETTINGS_TABLE_RESET_COUNTER_KEY] = (
            reset_counter
        )
    return f"{hhs_ui_constants.HHS_SETTINGS_TABLE_KEY}_{reset_counter}"


def reset_hhs_settings_table_selection() -> None:
    """Reset the HHS Settings dataframe selection for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui_constants.HHS_SETTINGS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui_constants.HHS_SETTINGS_TABLE_RESET_COUNTER_KEY] = (
        reset_counter + 1
    )


def hhs_hspm_catalog_table_key() -> str:
    """Return the HSPM catalog data editor key for the current generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui_constants.HHS_HSPM_CATALOG_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[hhs_ui_constants.HHS_HSPM_CATALOG_TABLE_RESET_COUNTER_KEY] = (
            reset_counter
        )
    return f"hhs_hspm_catalog_table_{reset_counter}"


def reset_hhs_hspm_catalog_table_selection() -> None:
    """Reset the HSPM catalog table marks for the next rerun."""
    reset_counter = st.session_state.setdefault(
        hhs_ui_constants.HHS_HSPM_CATALOG_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
    st.session_state[hhs_ui_constants.HHS_HSPM_CATALOG_TABLE_RESET_COUNTER_KEY] = (
        reset_counter + 1
    )


def refresh_hhs_hspm_catalog_listing() -> None:
    """Refresh cached HSPM catalog data and clear marked rows."""
    cache_delete_tag(HHS_HSPM_CATALOG_CACHE_TAG)
    reset_hhs_hspm_catalog_table_selection()


def refresh_home_tools_listing() -> None:
    """Refresh cached Home tool listings and reset the tool selection."""
    cache_delete_tag("tools")
    reset_home_tools_table_selection()


def refresh_home_shopts_listing() -> None:
    """Refresh the cached Home SHOPTS listing after a shell option change."""
    cache_delete_tag("shopt")
    reset_home_shopts_table_selection()


def stop_config_listing_background_jobs(cache_tag: str) -> None:
    """Stop stale background listing jobs for one Config cache tag."""
    stop_background_jobs_with_state_prefix(
        background_job_state_key(f"cached_{safe_cache_tag(cache_tag)}_")
    )
    if cache_tag == "aliases":
        stop_background_job(ALIAS_LIST_JOB)


def refresh_config_listing_cache(
    cache_tag: str,
    command: str,
    loader_message: str,
    reset_selection: Callable[[], None],
) -> None:
    """Invalidate one Config listing so the background renderer reloads it."""
    del command, loader_message
    stop_config_listing_background_jobs(cache_tag)
    cache_delete_tag(cache_tag)
    reset_selection()


def refresh_env_listing() -> None:
    """Refresh cached environment listings and reset the environment selection."""
    refresh_config_listing_cache(
        "env",
        build_hhs_envs_command(None),
        "Loading environment variables...",
        reset_env_table_selection,
    )


def refresh_path_listing() -> None:
    """Refresh cached PATH listings and reset the PATH selection."""
    refresh_config_listing_cache(
        "path",
        build_hhs_paths_command(),
        "Loading PATH entries...",
        reset_path_table_selection,
    )


def refresh_dir_listing() -> None:
    """Refresh cached saved directory listings and reset the directory selection."""
    refresh_config_listing_cache(
        "dirs",
        build_hhs_dirs_command(),
        "Loading saved directories...",
        reset_dir_table_selection,
    )


def refresh_cmd_listing() -> None:
    """Refresh cached saved command listings and reset the command selection."""
    refresh_config_listing_cache(
        "cmds",
        build_hhs_commands_command(),
        "Loading saved commands...",
        reset_cmd_table_selection,
    )


def refresh_alias_listing() -> None:
    """Refresh cached alias listings and reset the alias selection."""
    refresh_config_listing_cache(
        "aliases",
        build_hhs_aliases_command(),
        "Loading custom aliases...",
        reset_alias_table_selection,
    )


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


def apply_selected_env_value(
    name: str,
    value: str,
    clear_form_key_prefix: str = "",
    clear_form_include_name: bool = True,
) -> bool:
    """Persist a selected environment value and store it for table rerenders."""
    return queue_config_action(
        build_hhs_env_action_command("add", name, value),
        "Updating environment variables",
        {
            "domain": "env",
            "operation": "add",
            "name": name,
            "value": value,
            "started_message": f'Updating environment variable: "{name}"',
            "success_fallback": f'Environment variable saved: "{name}"',
            "error_fallback": f"Unable to save environment variable: {name}",
            "clear_form_key_prefix": clear_form_key_prefix,
            "clear_form_include_name": clear_form_include_name,
        },
    )


def apply_env_delete(name: str) -> None:
    """Delete a custom environment value and reset the table selection."""
    queue_config_action(
        build_hhs_env_action_command("del", name),
        "Updating environment variables",
        {
            "domain": "env",
            "operation": "del",
            "name": name,
            "started_message": f'Removing environment variable: "{name}"',
            "success_fallback": f'Environment variable removed: "{name}"',
            "error_fallback": f"Unable to delete environment variable: {name}",
        },
    )


def apply_env_add_form_value() -> None:
    """Persist the current custom environment form value."""
    name = str(st.session_state.get("env_add_name", "")).strip()
    value = str(st.session_state.get("env_add_value", ""))
    if not name:
        return
    apply_selected_env_value(name, value, clear_form_key_prefix="env")


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


def start_background_action_job(
    job_name: str,
    command: str,
    description: str,
    timeout_seconds: int,
    metadata: dict[str, object],
    busy_message: str,
    force_local: bool = False,
    show_preloader_event: bool = True,
) -> bool:
    """Start one user-triggered action command as an EventBus-backed background job."""
    started = start_background_bash_command(
        job_name,
        command,
        description,
        timeout_seconds,
        force_local=force_local,
        metadata=metadata,
        show_preloader_event=show_preloader_event,
    )
    if not started:
        push_floating_status(busy_message, "warn")
    return started


def queue_config_action(
    command: str,
    description: str,
    metadata: dict[str, object],
) -> bool:
    """Queue a Config or shell-option mutation for background execution."""
    pending = {
        **metadata,
        "command": command,
        "description": description,
    }
    st.session_state["config_action_execute_pending"] = pending
    save_ui_state()
    return True


def start_pending_config_action() -> None:
    """Start a queued Config mutation background job, when present."""
    pending = st.session_state.pop("config_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        CONFIG_ACTION_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another configuration action is already running.",
    )
    if started:
        started_message = str(pending.get("started_message", "")).strip()
        if started_message:
            push_floating_status(started_message, "info")
    else:
        st.session_state["config_action_execute_pending"] = pending


def apply_successful_config_action_side_effects(
    metadata: dict[str, object],
) -> None:
    """Apply local state and cache updates for a successful Config mutation."""
    domain = str(metadata.get("domain", "")).strip()
    operation = str(metadata.get("operation", "")).strip()
    name = str(metadata.get("name", "")).strip()
    value = str(metadata.get("value", ""))
    old_value = str(metadata.get("old_value", "")).strip()
    if domain == "env":
        if operation == "del":
            os.environ.pop(name, None)
            env_value_overrides().pop(name, None)
        else:
            os.environ[name] = value
            env_value_overrides()[name] = value
        refresh_env_listing()
    elif domain == "path":
        if operation == "del":
            path_values = [entry for entry in path_entries() if entry != value]
        else:
            path_values = [entry for entry in path_entries() if entry != old_value]
            if value not in path_values:
                path_values.insert(0, value)
        os.environ["PATH"] = ":".join(path_values)
        refresh_path_listing()
    elif domain == "dir":
        refresh_dir_listing()
    elif domain == "cmd":
        refresh_cmd_listing()
    elif domain == "alias":
        refresh_alias_listing()
    elif domain == "shopt":
        refresh_home_shopts_listing()
    form_prefix = str(metadata.get("clear_form_key_prefix", "")).strip()
    if form_prefix:
        clear_add_form_fields(
            form_prefix,
            include_name=bool(metadata.get("clear_form_include_name", True)),
        )


def complete_config_action_job() -> None:
    """Complete a background Config mutation and publish its user status."""
    completed = background_job_result(CONFIG_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    if result.returncode == 0:
        apply_successful_config_action_side_effects(metadata)
    push_config_action_status(
        result,
        str(metadata.get("success_fallback", "Configuration updated.")),
        str(metadata.get("error_fallback", "Configuration update failed.")),
    )
    save_ui_state()


def execute_pending_config_action() -> None:
    """Start or complete the current Config mutation background job."""
    start_pending_config_action()
    complete_config_action_job()


def apply_selected_path_value(
    old_path: str,
    new_path: str,
    clear_form_key_prefix: str = "",
    clear_form_include_name: bool = True,
) -> bool:
    """Persist a PATH entry and refresh the table listing."""
    return queue_config_action(
        build_hhs_path_action_command("edit", new_path, old_path),
        "Updating PATH entries",
        {
            "domain": "path",
            "operation": "edit",
            "name": new_path,
            "value": new_path,
            "old_value": old_path,
            "started_message": f'Updating PATH entry: "{new_path}"',
            "success_fallback": f'PATH entry saved: "{new_path}"',
            "error_fallback": f"Unable to save PATH entry: {new_path}",
            "clear_form_key_prefix": clear_form_key_prefix,
            "clear_form_include_name": clear_form_include_name,
        },
    )


def apply_path_delete(path_value: str) -> None:
    """Delete a PATH entry and reset the table selection."""
    queue_config_action(
        build_hhs_path_action_command("del", path_value),
        "Updating PATH entries",
        {
            "domain": "path",
            "operation": "del",
            "name": path_value,
            "value": path_value,
            "started_message": f'Removing PATH entry: "{path_value}"',
            "success_fallback": f'PATH entry removed: "{path_value}"',
            "error_fallback": f"Unable to remove PATH entry: {path_value}",
        },
    )


def apply_selected_dir_value(
    name: str,
    value: str,
    clear_form_key_prefix: str = "",
    clear_form_include_name: bool = True,
) -> bool:
    """Persist a saved directory value."""
    return queue_config_action(
        build_hhs_dir_action_command("add", name, value),
        "Updating saved directories",
        {
            "domain": "dir",
            "operation": "add",
            "name": name,
            "value": value,
            "started_message": f'Updating saved directory: "{name}"',
            "success_fallback": f'Saved directory saved: "{name}"',
            "error_fallback": f"Unable to save directory: {name}",
            "clear_form_key_prefix": clear_form_key_prefix,
            "clear_form_include_name": clear_form_include_name,
        },
    )


def apply_dir_delete(name: str) -> None:
    """Delete a saved directory and reset the table selection."""
    queue_config_action(
        build_hhs_dir_action_command("del", name),
        "Updating saved directories",
        {
            "domain": "dir",
            "operation": "del",
            "name": name,
            "started_message": f'Removing saved directory: "{name}"',
            "success_fallback": f'Saved directory removed: "{name}"',
            "error_fallback": f"Unable to remove saved directory: {name}",
        },
    )


def apply_selected_cmd_value(
    name: str,
    value: str,
    clear_form_key_prefix: str = "",
    clear_form_include_name: bool = True,
) -> bool:
    """Persist a saved command value."""
    return queue_config_action(
        build_hhs_command_action_command("add", name, value),
        "Updating saved commands",
        {
            "domain": "cmd",
            "operation": "add",
            "name": name,
            "value": value,
            "started_message": f'Updating saved command: "{name}"',
            "success_fallback": f'Saved command saved: "{name}"',
            "error_fallback": f"Unable to save command: {name}",
            "clear_form_key_prefix": clear_form_key_prefix,
            "clear_form_include_name": clear_form_include_name,
        },
    )


def apply_cmd_delete(name: str) -> None:
    """Delete a saved command and reset the table selection."""
    queue_config_action(
        build_hhs_command_action_command("del", name),
        "Updating saved commands",
        {
            "domain": "cmd",
            "operation": "del",
            "name": name,
            "started_message": f'Removing saved command: "{name}"',
            "success_fallback": f'Saved command removed: "{name}"',
            "error_fallback": f"Unable to remove saved command: {name}",
        },
    )


def apply_selected_alias_value(
    name: str,
    value: str,
    clear_form_key_prefix: str = "",
    clear_form_include_name: bool = True,
) -> bool:
    """Persist a custom alias value."""
    return queue_config_action(
        build_hhs_alias_action_command("add", name, value),
        "Updating custom aliases",
        {
            "domain": "alias",
            "operation": "add",
            "name": name,
            "value": value,
            "started_message": f'Updating alias: "{name}"',
            "success_fallback": f'Alias saved: "{name}"',
            "error_fallback": f"Unable to save alias: {name}",
            "clear_form_key_prefix": clear_form_key_prefix,
            "clear_form_include_name": clear_form_include_name,
        },
    )


def apply_alias_delete(name: str) -> None:
    """Delete a custom alias and reset the table selection."""
    queue_config_action(
        build_hhs_alias_action_command("del", name),
        "Updating custom aliases",
        {
            "domain": "alias",
            "operation": "del",
            "name": name,
            "started_message": f'Removing alias: "{name}"',
            "success_fallback": f'Alias removed: "{name}"',
            "error_fallback": f"Unable to remove alias: {name}",
        },
    )


def apply_home_shopt_action(operation: str, option_name: str) -> None:
    """Set or unset a shell option from the Home SHOPTS table."""
    action_label = "set" if operation == "set" else "unset"
    queue_config_action(
        build_hhs_shopt_action_command(operation, option_name),
        "Updating shell option",
        {
            "domain": "shopt",
            "operation": operation,
            "name": option_name,
            "started_message": f"Updating shell option: {option_name}",
            "success_fallback": f"Shell option {option_name} {action_label}.",
            "error_fallback": f"Unable to {action_label} shell option: {option_name}",
        },
    )


def queue_docker_action(
    command: str,
    description: str,
    timeout_seconds: int,
    metadata: dict[str, object],
) -> None:
    """Queue a Docker mutation for background execution."""
    st.session_state["docker_action_execute_pending"] = {
        **metadata,
        "command": command,
        "description": description,
        "timeout_seconds": timeout_seconds,
    }
    save_ui_state()


def start_pending_docker_action() -> None:
    """Start a queued Docker mutation background job, when present."""
    pending = st.session_state.pop("docker_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    timeout_seconds = int(
        pending.get("timeout_seconds", hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS)
    )
    if not command or not description:
        return
    started = start_background_action_job(
        DOCKER_ACTION_JOB,
        command,
        description,
        timeout_seconds,
        pending,
        "Another Docker action is already running.",
    )
    if started:
        started_message = str(pending.get("started_message", "")).strip()
        if started_message:
            push_floating_status(started_message, "info")
    else:
        st.session_state["docker_action_execute_pending"] = pending


def complete_docker_action_job() -> None:
    """Complete a Docker mutation background job and refresh Docker listings."""
    completed = background_job_result(DOCKER_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    cache_delete_tag("docker")
    if str(metadata.get("action_type", "")).strip() == "image":
        reset_docker_image_table_selection()
    else:
        reset_docker_container_table_selection()
    push_config_action_status(
        result,
        str(metadata.get("success_fallback", "Docker action completed.")),
        str(metadata.get("error_fallback", "Docker action failed.")),
    )
    save_ui_state()


def execute_pending_docker_action() -> None:
    """Start or complete the current Docker mutation background job."""
    start_pending_docker_action()
    complete_docker_action_job()


def apply_docker_container_action(operation: str, container_id: str) -> None:
    """Run a Docker container action from the selected container table row."""
    clean_container_id = container_id.strip()
    if not clean_container_id:
        return
    queue_docker_action(
        build_docker_container_action_command(operation, clean_container_id),
        f"Running docker {operation}",
        20,
        {
            "action_type": "container",
            "operation": operation,
            "container_id": clean_container_id,
            "started_message": f"Docker container {operation} started: {clean_container_id}",
            "success_fallback": (
                f"Docker container {operation} completed: {clean_container_id}"
            ),
            "error_fallback": f"Docker container {operation} failed: {clean_container_id}",
        },
    )


def apply_docker_image_action(image_id: str) -> None:
    """Delete a Docker image from the selected image table row."""
    clean_image_id = image_id.strip()
    if not clean_image_id:
        return
    queue_docker_action(
        build_docker_image_delete_command(clean_image_id),
        "Deleting Docker image",
        30,
        {
            "action_type": "image",
            "image_id": clean_image_id,
            "started_message": f"Docker image deletion started: {clean_image_id}",
            "success_fallback": f"Docker image deleted: {clean_image_id}",
            "error_fallback": f"Docker image deletion failed: {clean_image_id}",
        },
    )


def apply_selected_env_editor_value(name: str, editor_key: str) -> None:
    """Export the current selected environment editor value."""
    apply_selected_env_value(name, str(st.session_state.get(editor_key, "")))


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
    apply_selected_path_value(
        value,
        value,
        clear_form_key_prefix="path",
        clear_form_include_name=False,
    )


def apply_dir_add_form_value() -> None:
    """Persist the current saved directory add form value."""
    name = str(st.session_state.get("dir_add_name", "")).strip()
    value = str(st.session_state.get("dir_add_value", "")).strip()
    if not name or not value:
        return
    apply_selected_dir_value(name, value, clear_form_key_prefix="dir")


def apply_cmd_add_form_value() -> None:
    """Persist the current saved command add form value."""
    name = str(st.session_state.get("cmd_add_name", "")).strip()
    value = str(st.session_state.get("cmd_add_value", ""))
    if not name:
        return
    apply_selected_cmd_value(name, value, clear_form_key_prefix="cmd")


def apply_alias_add_form_value() -> None:
    """Persist the current alias add form value."""
    name = str(st.session_state.get("alias_add_name", "")).strip()
    value = str(st.session_state.get("alias_add_value", ""))
    if not name:
        return
    apply_selected_alias_value(name, value, clear_form_key_prefix="alias")


def render_env_rows(rows: list[dict[str, str]]) -> None:
    """Render selectable editable environment variable rows."""
    rows = apply_env_value_overrides(rows)
    render_table(
        rows,
        key=env_table_key(),
        translate_paths=False,
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
    """Render selectable read-only PATH rows."""
    render_table(
        rows,
        key=path_table_key(),
        headers=["Type", "Origin", "Path Value"],
        table_data=styled_path_rows(rows),
        column_config=path_column_config(),
        height=hhs_ui.PATH_TABLE_HEIGHT,
        width=hhs_ui.PATH_TABLE_WIDTH,
        selected_label=lambda row, _index: f"Selected: {row['Path Value']}",
        reset_selection=reset_path_table_selection,
        selected_action_buttons=[
            {
                "label": "Delete",
                "glyph": "",
                "key_prefix": "path_delete_button",
                "on_click": apply_path_delete,
                "args": lambda row, _index: (row["Path Value"],),
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
        folder_picker_callback=request_folder_picker,
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
        column_config=cmd_column_config(),
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


def ai_service_availability_context() -> str:
    """Return the active execution-host key for Ollama availability state."""
    remote_host = command_remote_host()
    return f"ssh:{remote_host}" if remote_host else "local"


def ai_service_availability_context_matches_active_host() -> bool:
    """Return whether stored Ollama availability belongs to the active host."""
    stored_context = str(
        st.session_state.get(
            hhs_ui_constants.AI_SERVICE_AVAILABILITY_CONTEXT_KEY,
            "",
        )
    ).strip()
    return stored_context == ai_service_availability_context()


def remember_ollama_service_availability(
    result: subprocess.CompletedProcess[str] | None,
) -> bool:
    """Store Ollama service availability when a successful services result exists."""
    if result is None or result.returncode != 0:
        return ollama_service_is_available()
    available = ollama_service_is_available_from_output(result.stdout)
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_CONTEXT_KEY] = (
        ai_service_availability_context()
    )
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY] = available
    return available


def ollama_service_availability_refresh_due() -> bool:
    """Return whether AI tab visibility should recheck Ollama service status."""
    if not ai_service_availability_context_matches_active_host():
        return True
    try:
        refreshed_at = float(
            st.session_state.get(
                hhs_ui_constants.AI_SERVICE_AVAILABILITY_REFRESHED_AT_KEY,
                0.0,
            )
            or 0.0
        )
    except (TypeError, ValueError):
        refreshed_at = 0.0
    elapsed = time.time() - refreshed_at if refreshed_at else float("inf")
    return elapsed >= hhs_ui_constants.AI_SERVICE_AVAILABILITY_REFRESH_INTERVAL_SECONDS


def ollama_service_is_available() -> bool:
    """Return the last known Ollama service availability without starting commands."""
    return ai_service_availability_context_matches_active_host() and bool(
        st.session_state.get(hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY, False)
    )


def initialize_ollama_service_availability() -> None:
    """Seed and refresh AI tab visibility from service availability data."""
    if (
        st.session_state.get(hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY)
        and ai_service_availability_context_matches_active_host()
    ):
        return
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY] = True
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_CONTEXT_KEY] = (
        ai_service_availability_context()
    )
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY] = False
    _result, fresh_cache = cached_hhs_services_result()
    if not fresh_cache and not background_job_is_running(SERVICE_LIST_JOB):
        start_hhs_services_list_refresh()


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
            force_local=False,
            metadata={"operation": operation, "tool_name": tool_name},
            show_preloader_event=True,
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
    clean_tool_name = tool_name.strip()
    if not clean_tool_name:
        return
    st.session_state["home_tool_tldr_execute_pending"] = {
        "tool_name": clean_tool_name,
    }
    save_ui_state()


def execute_pending_home_tool_tldr() -> None:
    """Start or complete the selected Home tool TLDR background job."""
    pending = st.session_state.pop("home_tool_tldr_execute_pending", None) or {}
    if isinstance(pending, dict):
        tool_name = str(pending.get("tool_name", "")).strip()
        if tool_name:
            started = start_background_action_job(
                HOME_TOOL_TLDR_JOB,
                build_tool_tldr_command(tool_name),
                f"Loading TLDR for {tool_name}",
                hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
                {"tool_name": tool_name},
                "Another TLDR load is already running.",
            )
            if started:
                push_floating_status(f"Loading TLDR: {tool_name}", "info")
            else:
                st.session_state["home_tool_tldr_execute_pending"] = pending

    completed = background_job_result(HOME_TOOL_TLDR_JOB)
    if completed is None:
        return
    result, metadata = completed
    tool_name = str(metadata.get("tool_name", "")).strip()
    st.session_state["home_tool_tldr_name"] = tool_name
    st.session_state["home_tool_tldr_output"] = result.stdout or result.stderr or ""
    st.session_state["home_tool_tldr_succeeded"] = result.returncode == 0
    if result.returncode == 0:
        push_floating_status(f"Loaded TLDR: {tool_name}", "info")
    else:
        push_floating_status(f"Unable to load TLDR: {tool_name}", "error")
    save_ui_state()


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
            show_preloader_event=True,
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


def queue_monitor_process_action(command: str, metadata: dict[str, object]) -> None:
    """Queue a monitor process mutation for background execution."""
    st.session_state["monitor_process_action_execute_pending"] = {
        **metadata,
        "command": command,
    }
    save_ui_state()


def start_pending_monitor_process_action() -> None:
    """Start a queued monitor process mutation background job, when present."""
    pending = st.session_state.pop("monitor_process_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    if not command:
        return
    process_name = str(pending.get("process_name", "")).strip()
    started = start_background_action_job(
        MONITOR_PROCESS_ACTION_JOB,
        command,
        "Killing process",
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another process action is already running.",
    )
    if started:
        push_floating_status(f"Killing process: {process_name}", "info")
    else:
        st.session_state["monitor_process_action_execute_pending"] = pending


def complete_monitor_process_action_job() -> None:
    """Complete a monitor process mutation and refresh the process listing."""
    completed = background_job_result(MONITOR_PROCESS_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    process_name = str(metadata.get("process_name", "")).strip()
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
    save_ui_state()


def execute_pending_monitor_process_action() -> None:
    """Start or complete the current monitor process action background job."""
    start_pending_monitor_process_action()
    complete_monitor_process_action_job()


def complete_background_action_jobs() -> None:
    """Start or complete background jobs created by user action buttons."""
    execute_pending_home_tool_action()
    execute_pending_home_tool_tldr()
    execute_pending_config_action()
    execute_pending_hhs_setup_action()
    execute_pending_hhs_settings_action()
    execute_pending_hhs_starship_action()
    execute_pending_hhs_firebase_action()
    execute_pending_docker_action()
    execute_pending_service_action()
    execute_pending_monitor_process_action()
    execute_pending_ssh_explorer_action()
    execute_pending_ssh_explorer_delete()
    execute_pending_search_open_action()
    execute_pending_ai_context_action()
    execute_pending_ai_prompt_action()


def apply_selected_process_kill(process_name: str) -> None:
    """Kill the selected process name and store the action result."""
    clean_process_name = process_name.strip()
    if not clean_process_name:
        return
    queue_monitor_process_action(
        build_hhs_process_kill_command(clean_process_name),
        {"process_name": clean_process_name},
    )


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


@st.fragment()
def render_envs_table() -> None:
    """Render environment variables using __hhs_envs."""
    execute_pending_config_action()
    render_background_job_status(CONFIG_ACTION_JOB)
    env_filter, other_filter = render_filters_and_controls(
        "Name",
        "Value",
        filters=table_filter_mapping(hhs_ui.ENV_FILTERS),
        key_prefix="env",
        filter_key="env_filter",
        other_filter_key="env_other_filter",
        name_placeholder="Custom Variable",
        value_placeholder="Optional value",
        on_submit=apply_env_add_form_value,
        default_filter="HHS",
    )
    render_config_file_pill("ENV")

    result = render_cached_command_result(
        build_hhs_envs_command(None),
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
    render_env_rows(filter_env_rows(rows, env_filter, other_filter))


@st.fragment()
def render_paths_table() -> None:
    """Render PATH entries using __hhs_paths."""
    execute_pending_config_action()
    render_background_job_status(CONFIG_ACTION_JOB)
    path_filter, other_filter = render_filters_and_controls(
        None,
        "Path",
        has_file_picker_btn=True,
        filters=table_filter_mapping(hhs_ui.PATH_FILTERS),
        key_prefix="path",
        filter_key="path_filter",
        other_filter_key="path_other_filter",
        value_placeholder="Custom path",
        on_submit=apply_path_add_form_value,
    )
    render_folder_picker_dialog("path")
    render_config_file_pill("PATH")
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


@st.fragment()
def render_dirs_table() -> None:
    """Render saved directories using __hhs_load_dir."""
    execute_pending_config_action()
    render_background_job_status(CONFIG_ACTION_JOB)
    dirs_filter, other_filter = render_filters_and_controls(
        "Name",
        "Path",
        has_file_picker_btn=True,
        filters=table_filter_mapping(hhs_ui.LIST_FILTERS),
        key_prefix="dir",
        filter_key="dirs_filter",
        other_filter_key="dirs_other_filter",
        name_placeholder="Directory alias",
        value_placeholder="Directory path",
        on_submit=apply_dir_add_form_value,
    )
    render_folder_picker_dialog("dir")
    render_config_file_pill("DIR")
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


@st.fragment()
def render_cmds_table() -> None:
    """Render saved commands using __hhs_command."""
    execute_pending_config_action()
    render_background_job_status(CONFIG_ACTION_JOB)
    cmds_filter, other_filter = render_filters_and_controls(
        "Name",
        "Command",
        filters=table_filter_mapping(hhs_ui.LIST_FILTERS),
        key_prefix="cmd",
        filter_key="cmds_filter",
        other_filter_key="cmds_other_filter",
        name_placeholder="Command alias",
        value_placeholder="Command value",
        on_submit=apply_cmd_add_form_value,
    )
    render_config_file_pill("CMD")
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


@st.fragment()
def render_aliases_table() -> None:
    """Render custom aliases using __hhs_aliases."""
    execute_pending_config_action()
    render_background_job_status(CONFIG_ACTION_JOB)
    complete_aliases_list_refresh()
    alias_filter, other_filter = render_filters_and_controls(
        "Name",
        "Expression",
        filters=table_filter_mapping(hhs_ui.LIST_FILTERS),
        key_prefix="alias",
        filter_key="alias_filter",
        other_filter_key="alias_other_filter",
        name_placeholder="Alias",
        value_placeholder="Alias expression",
        on_submit=apply_alias_add_form_value,
    )
    render_config_file_pill("ALIAS")
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
    render_background_job_status_if_blocking(SERVICE_LIST_JOB, result is not None)
    if service_list_running and not fresh_cache and result is None:
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
    result = run_bash_command(
        build_hhs_history_command(),
        "Loading command history",
        ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        cache_tag="history",
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        show_overlay=False,
    )
    if result.returncode != 0:
        st.error(result.stderr or "Unable to list command history.")
        return
    rows = filter_rows_by_text(
        parse_rows_cached("history", result.stdout, parse_hhs_history),
        history_commands_filter,
        other_filter,
    )
    render_read_only_rows(
        rows,
        history_command_table_key(),
        headers=["Value"],
        hide_index=False,
        table_data=history_command_table_data(rows),
        column_config=history_command_column_config(rows),
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
        headers=["Value"],
        hide_index=False,
        table_data=history_directory_table_data(rows),
        column_config=history_directory_column_config(),
        selected_value=lambda row, _index: row.get("Value", ""),
    )


def config_view_label(config_view: str) -> str:
    """Return the display label for a configuration view key."""
    return hhs_ui.CONFIG_VIEW_LABELS.get(config_view, config_view)


def render_configs_view() -> None:
    """Render the draft configurations view."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> Dotfiles Configurations</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_background_job_status(SEARCH_OPEN_JOB)
    config_view = render_view_segmented_control(
        "Configuration view",
        hhs_ui.CONFIG_VIEWS,
        "config_view",
        "ENV",
        format_func=config_view_label,
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
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> System Services</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_services_table()


def monitor_view_label(monitor_view: str) -> str:
    """Return the display label for a Monitor view key."""
    return hhs_ui.MONITOR_VIEW_LABELS.get(monitor_view, monitor_view)


def history_view_label(history_view: str) -> str:
    """Return the display label for a History view key."""
    return hhs_ui.HISTORY_VIEW_LABELS.get(history_view, history_view)


def render_history_view() -> None:
    """Render the command and directory history view."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> History</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    history_view = render_view_segmented_control(
        "History view",
        hhs_ui.HISTORY_VIEWS,
        "history_view",
        "COMMANDS",
        format_func=history_view_label,
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
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> Activity Monitor</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    monitor_view = render_view_segmented_control(
        "Monitor view",
        hhs_ui.MONITOR_VIEWS,
        "monitor_view",
        "DISK",
        format_func=monitor_view_label,
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
        render_ttyd_terminal_frame_hide_script()
    if selected_remote_host_requires_connection():
        render_remote_connection_required_view()
        return
    if st.session_state.get(hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY):
        render_document_view()
        return
    visible_views = main_views()
    active_view = render_active_view_control(visible_views)
    if active_view == "Home":
        render_home_view()
    elif active_view == "Configs":
        render_configs_view()
    elif active_view == "HHS":
        render_hhs_view()
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


def configure_dialog_runtime_dependencies() -> None:
    """Wire reusable dialog helpers to Streamlit UI runtime callbacks."""
    dialog_ui.configure_dialog_runtime(
        render_script_html=render_script_html,
        dismiss_streamlit_dialog=dismiss_streamlit_dialog,
    )


def configure_dom_script_dependencies() -> None:
    """Wire browser DOM script helpers to Streamlit UI callbacks."""
    dom_scripts.configure_dom_scripts(render_script_html=render_script_html)


def configure_feedback_runtime_dependencies() -> None:
    """Wire shared feedback helpers to Streamlit UI runtime callbacks."""
    feedback_ui.configure_feedback_runtime(
        render_script_html=render_script_html,
        command_timeout_seconds=command_timeout_seconds,
        save_ui_state=save_ui_state,
    )


def configure_status_runtime_dependencies() -> None:
    """Wire floating status helpers to Streamlit UI runtime callbacks."""
    status_ui.configure_status_runtime(render_script_html=render_script_html)


def configure_ai_ui_dependencies() -> None:
    """Wire AI UI helpers to Streamlit UI callbacks."""
    ai_ui.configure_ai_ui(
        render_script_html=render_script_html,
        render_view_segmented_control=render_view_segmented_control,
        start_background_action_job=start_background_action_job,
    )


def configure_hhs_app_ui_dependencies() -> None:
    """Wire HomeSetup application views to shared Streamlit UI callbacks."""
    hhs_app_ui.configure_hhs_app_ui(
        render_script_html=render_script_html,
        render_openable_file_pill=render_openable_file_pill,
        render_view_segmented_control=render_view_segmented_control,
        start_background_action_job=start_background_action_job,
        hhs_setup_file_path=hhs_setup_file_path,
        hhs_settings_table_key=hhs_settings_table_key,
        reset_hhs_settings_table_selection=reset_hhs_settings_table_selection,
        hhs_hspm_catalog_table_key=hhs_hspm_catalog_table_key,
        refresh_hhs_hspm_catalog_listing=refresh_hhs_hspm_catalog_listing,
    )


def configure_monitor_ui_dependencies() -> None:
    """Wire History and Monitor views to shared Streamlit UI callbacks."""
    monitor_ui.configure_monitor_ui(
        apply_selected_process_kill=apply_selected_process_kill,
        execute_pending_monitor_process_action=execute_pending_monitor_process_action,
        filter_process_rows=filter_process_rows,
        process_monitor_chart_rows=process_monitor_chart_rows,
        render_openable_file_pill=render_openable_file_pill,
        render_persisted_expander_state_script=render_persisted_expander_state_script,
    )


def configure_cache_runtime_dependencies() -> None:
    """Wire UI cache helpers to Streamlit UI runtime callbacks."""
    cache_runtime.configure_cache_runtime(
        effective_bash_command=effective_bash_command,
        command_remote_host=command_remote_host,
        stop_path_picker_listing_jobs=stop_path_picker_listing_jobs,
        push_floating_status=push_floating_status,
        clear_firebase_aliases_cache=clear_firebase_aliases_cache,
        handle_remote_command_result=handle_remote_command_result,
    )


def configure_ssh_runtime_dependencies() -> None:
    """Wire SSH runtime helpers to Streamlit UI callbacks."""
    ssh_runtime.configure_ssh_runtime(
        terminal_document_view_is_active=terminal_document_view_is_active,
        restore_terminal_document_view=restore_terminal_document_view,
        reset_updater_remote_check_state=reset_updater_remote_check_state,
        update_remote_footer_working_directory=update_remote_footer_working_directory,
        reset_search_directory_to_home=reset_search_directory_to_home,
        schedule_ollama_service_availability_refresh=(
            schedule_ollama_service_availability_refresh
        ),
    )


def configure_command_runtime_dependencies() -> None:
    """Wire command execution helpers to Streamlit UI runtime callbacks."""
    command_runtime.configure_command_runtime(
        command_remote_host=command_remote_host,
        effective_bash_command=effective_bash_command,
        effective_command_timeout_seconds=effective_command_timeout_seconds,
        command_timeout_seconds=command_timeout_seconds,
        command_cache_key=command_cache_key,
        command_result_snapshot_get=command_result_snapshot_get,
        command_result_snapshot_set=command_result_snapshot_set,
        completed_process_from_cache=completed_process_from_cache,
        cache_value_from_completed_process=cache_value_from_completed_process,
        cache_get=cache_get,
        cache_set=cache_set,
        handle_remote_command_result=handle_remote_command_result,
        ssh_connection_is_alive=ssh_connection_is_alive,
        ui_disposable_files_dir=ui_disposable_files_dir,
        update_ollama_service_availability_refresh=update_ollama_service_availability_refresh,
    )


def configure_terminal_runtime_dependencies() -> None:
    """Wire terminal runtime helpers to Streamlit UI callbacks."""
    terminal_ui.configure_terminal_runtime(
        render_script_html=render_script_html,
        render_command_preloader_events=render_command_preloader_events,
        footer_working_directory=footer_working_directory,
        connected_ssh_host=connected_ssh_host,
        selected_host_is_local=selected_host_is_local,
        clear_registered_ssh_connection=clear_registered_ssh_connection,
        terminal_document_view_is_active=terminal_document_view_is_active,
        close_document_view=close_document_view,
        deactivate_terminal_document_view=deactivate_terminal_document_view,
        push_floating_status=push_floating_status,
    )


def configure_path_picker_dependencies() -> None:
    """Wire path-picker helpers to Streamlit UI runtime callbacks."""
    path_picker_ui.configure_path_picker(
        connected_ssh_host=connected_ssh_host,
        background_job_state_key=background_job_state_key,
        stop_background_jobs_with_state_prefix=stop_background_jobs_with_state_prefix,
        background_job_result=background_job_result,
        background_job_is_running=background_job_is_running,
        start_background_bash_command=start_background_bash_command,
        push_floating_status=push_floating_status,
        render_background_job_status=render_background_job_status,
        clear_preloader=clear_preloader,
    )


def configure_ssh_explorer_ui_dependencies() -> None:
    """Wire SSH explorer UI helpers to Streamlit UI callbacks."""
    ssh_explorer_ui.configure_ssh_explorer_ui(
        start_background_action_job=start_background_action_job,
        render_view_segmented_control=render_view_segmented_control,
    )


def configure_footer_ui_dependencies() -> None:
    """Wire footer helpers to Streamlit UI callbacks."""
    footer_ui.configure_footer_ui(
        render_script_html=render_script_html,
        execute_due_updater_check=execute_due_updater_check,
        terminal_document_view_is_active=terminal_document_view_is_active,
        updater_check_context=updater_check_context,
        clear_ai_chat_history=clear_ai_chat_history,
        open_remote_explorer_path=open_remote_explorer_path,
        open_search_result_path=open_search_result_path,
    )


def configure_search_ui_dependencies() -> None:
    """Wire Search helpers to Streamlit UI callbacks."""
    search_ui.configure_search_ui(
        render_script_html=render_script_html,
        ui_disposable_files_dir=ui_disposable_files_dir,
        start_background_action_job=start_background_action_job,
        build_scp_to_local_command=build_scp_to_local_command,
        ssh_explorer_mtime_text=ssh_explorer_mtime_text,
        ssh_explorer_size_text=ssh_explorer_size_text,
        footer_working_directory=footer_working_directory,
    )


def main() -> None:
    """Configure and render the HomeSetup Streamlit UI."""
    install_footer_status_log_handler()
    configure_dialog_runtime_dependencies()
    configure_dom_script_dependencies()
    configure_feedback_runtime_dependencies()
    configure_status_runtime_dependencies()
    configure_ai_ui_dependencies()
    configure_hhs_app_ui_dependencies()
    configure_monitor_ui_dependencies()
    configure_cache_runtime_dependencies()
    configure_ssh_runtime_dependencies()
    configure_command_runtime_dependencies()
    configure_terminal_runtime_dependencies()
    configure_path_picker_dependencies()
    configure_ssh_explorer_ui_dependencies()
    configure_footer_ui_dependencies()
    configure_search_ui_dependencies()
    selected_theme = persisted_theme_name()
    configure_app_font_theme(selected_theme)
    st.set_page_config(
        page_title=f"HomeSetup - UI v{hhs_ui.VERSION}",
        page_icon=str(hhs_ui.APP_FAVICON_FILE),
        layout="wide",
    )
    restore_ui_state()
    if not st.session_state.get(hhs_ui_constants.UI_CACHE_FILE_SYNCED_SESSION_KEY):
        sync_ui_cache_file()
        st.session_state[hhs_ui_constants.UI_CACHE_FILE_SYNCED_SESSION_KEY] = True
    restore_persisted_theme_selection()
    st.session_state.setdefault("updater_last_check_output", "")
    st.session_state.setdefault("updater_update_available", False)
    st.session_state.setdefault("updater_check_context", "local")
    st.session_state.setdefault("updater_check_started_context", "")
    st.session_state.setdefault("updater_remote_checked_context", "")
    execute_mount_updater_check()
    st.session_state.setdefault("footer_hhs_version_cache_loaded", False)
    st.session_state.setdefault("footer_shell_version_dialog_title", "")
    st.session_state.setdefault("footer_shell_version_output", "")
    render_styles()
    if st.session_state.get("theme_reload_pending"):
        render_theme_reload_overlay()
    st.session_state.setdefault("active_view", "Home")
    st.session_state.setdefault("ai_chat_messages", [])
    st.session_state.setdefault(hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY, False)
    st.session_state.setdefault(
        hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY,
        False,
    )
    st.session_state.setdefault(
        hhs_ui_constants.AI_SERVICE_AVAILABILITY_CONTEXT_KEY,
        "",
    )
    st.session_state.setdefault(
        hhs_ui_constants.AI_SERVICE_AVAILABILITY_REFRESHED_AT_KEY,
        0.0,
    )
    if not isinstance(st.session_state["ai_chat_messages"], list):
        st.session_state["ai_chat_messages"] = []
    st.session_state.setdefault("ai_clear_chat_pending", False)
    st.session_state.setdefault("ai_clear_chat_execute_pending", False)
    st.session_state.setdefault("ai_context_action_execute_pending", None)
    st.session_state.setdefault("ai_prompt_action_execute_pending", None)
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
    render_background_job_polling_fragment()
    if execute_pending_ssh_disconnection():
        return
    if execute_pending_ssh_connection():
        return
    if render_ssh_connection_dialog():
        return
    initialize_ollama_service_availability()
    update_ollama_service_availability_refresh()
    handle_footer_actions()
    render_background_job_status(UPDATER_UPDATE_JOB)
    render_footer_shell_version_dialog()
    st.session_state.setdefault("home_view", "System")
    if st.session_state["home_view"] not in hhs_ui.HOME_VIEWS:
        st.session_state["home_view"] = "System"
    st.session_state.setdefault("hhs_view", "SETUP")
    if st.session_state["hhs_view"] not in hhs_ui.HHS_VIEWS:
        st.session_state["hhs_view"] = "SETUP"
    st.session_state.setdefault("home_tools_filter", "All")
    if st.session_state["home_tools_filter"] == "Not Found":
        st.session_state["home_tools_filter"] = "Not Installed"
    st.session_state["home_tools_filter"] = normalized_table_filter_selection(
        st.session_state["home_tools_filter"], hhs_ui.HOME_TOOLS_FILTERS
    )
    st.session_state.setdefault("home_tools_other_filter", "")
    st.session_state.setdefault(hhs_ui.HOME_TOOLS_TABLE_RESET_COUNTER_KEY, 0)
    st.session_state.setdefault("home_shopts_filter", "All")
    st.session_state["home_shopts_filter"] = normalized_table_filter_selection(
        st.session_state["home_shopts_filter"], hhs_ui.SHOPTS_FILTERS
    )
    st.session_state.setdefault("home_shopts_other_filter", "")
    st.session_state.setdefault(hhs_ui.HOME_SHOPTS_TABLE_RESET_COUNTER_KEY, 0)
    st.session_state.setdefault("home_tool_action_execute_pending", None)
    st.session_state.setdefault("home_tool_tldr_execute_pending", None)
    st.session_state.setdefault("config_action_execute_pending", None)
    st.session_state.setdefault("hhs_setup_action_execute_pending", None)
    st.session_state.setdefault("hhs_settings_action_execute_pending", None)
    st.session_state.setdefault("hhs_starship_action_execute_pending", None)
    st.session_state.setdefault("docker_action_execute_pending", None)
    st.session_state.setdefault("config_view", "ENV")
    if st.session_state["config_view"] not in hhs_ui.CONFIG_VIEWS:
        st.session_state["config_view"] = "ENV"
    st.session_state.setdefault("env_filter", "All")
    st.session_state["env_filter"] = normalized_table_filter_selection(
        st.session_state["env_filter"], hhs_ui.ENV_FILTERS
    )
    st.session_state.setdefault("env_other_filter", "")
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
    initialize_search_directory_home_default()
    st.session_state.setdefault("search_directories", [])
    st.session_state["search_directories"] = normalize_search_directories(
        st.session_state.get("search_directories", []),
        str(st.session_state.get("search_path", "")),
    )
    st.session_state.setdefault("search_query", None)
    st.session_state.setdefault("search_ignore_case", False)
    st.session_state.setdefault("search_words", False)
    st.session_state.setdefault("search_binary", False)
    st.session_state.setdefault("search_replace", False)
    st.session_state.setdefault("search_replacement", "")
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
    st.session_state.setdefault("search_result_replace", False)
    st.session_state.setdefault("search_result_replacement", "")
    st.session_state.setdefault("search_open_execute_pending", None)
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
    st.session_state["ssh_tunnel_filter"] = normalized_table_filter_selection(
        st.session_state["ssh_tunnel_filter"], hhs_ui.SSH_TUNNEL_FILTERS
    )
    st.session_state.setdefault("ssh_tunnel_other_filter", "")
    st.session_state.setdefault("monitor_process_filter", "All")
    st.session_state.setdefault("monitor_process_other_filter", "")
    st.session_state["monitor_process_other_filter"] = clean_table_text_filter_value(
        st.session_state.get("monitor_process_other_filter")
    )
    monitor_process_filter_value = st.session_state.get("monitor_process_filter")
    monitor_process_filter = (
        ""
        if monitor_process_filter_value is None
        else str(monitor_process_filter_value).strip()
    )
    if not monitor_process_filter:
        st.session_state["monitor_process_filter"] = "All"
        st.session_state["monitor_process_other_filter"] = ""
    elif monitor_process_filter == "None":
        st.session_state["monitor_process_filter"] = "All"
        st.session_state["monitor_process_other_filter"] = ""
    elif monitor_process_filter in ("Other", "Others"):
        st.session_state["monitor_process_filter"] = "Containing"
    elif monitor_process_filter not in hhs_ui.PROCESS_FILTERS:
        st.session_state["monitor_process_other_filter"] = monitor_process_filter
        st.session_state["monitor_process_filter"] = "Containing"
    else:
        st.session_state["monitor_process_filter"] = monitor_process_filter
    st.session_state.setdefault("monitor_process_action_execute_pending", None)
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
    st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(
        st.session_state.get("monitor_disk_top_n")
    )
    for metric in ("CPU", "MEM"):
        top_n_key = monitor_process_top_n_state_key(metric)
        st.session_state[top_n_key] = normalized_monitor_top_n(
            st.session_state.get(top_n_key)
        )
    st.session_state.setdefault("monitor_log_file", "")
    st.session_state.setdefault("monitor_log_filter", "All")
    st.session_state["monitor_log_filter"] = normalized_table_filter_selection(
        st.session_state["monitor_log_filter"], hhs_ui.LOG_FILTERS
    )
    st.session_state.setdefault("monitor_log_other_filter", "")
    st.session_state.setdefault("monitor_log_level", "ALL_LEVELS")
    st.session_state["monitor_log_level"] = selected_monitor_log_level()
    st.session_state["monitor_log_tail_lines"] = normalized_monitor_log_tail_lines(
        st.session_state.get("monitor_log_tail_lines")
    )
    st.session_state.setdefault("monitor_logs_tail", True)
    st.session_state.setdefault("alias_filter", "All")
    st.session_state["alias_filter"] = normalized_table_filter_selection(
        st.session_state["alias_filter"], hhs_ui.LIST_FILTERS
    )
    st.session_state.setdefault("path_filter", "All")
    st.session_state["path_filter"] = normalized_table_filter_selection(
        st.session_state["path_filter"], hhs_ui.PATH_FILTERS
    )
    st.session_state.setdefault("dirs_filter", "All")
    st.session_state["dirs_filter"] = normalized_table_filter_selection(
        st.session_state["dirs_filter"], hhs_ui.LIST_FILTERS
    )
    st.session_state.setdefault("cmds_filter", "All")
    st.session_state["cmds_filter"] = normalized_table_filter_selection(
        st.session_state["cmds_filter"], hhs_ui.LIST_FILTERS
    )
    st.session_state.setdefault("service_filter", "All")
    if st.session_state["service_filter"] == "Started":
        st.session_state["service_filter"] = "Up"
    elif st.session_state["service_filter"] == "Stopped":
        st.session_state["service_filter"] = "Down"
    st.session_state["service_filter"] = normalized_table_filter_selection(
        st.session_state["service_filter"], hhs_ui.SERVICE_FILTERS
    )
    st.session_state.setdefault("ssh_explorer_action_execute_pending", None)
    st.session_state.setdefault("ssh_explorer_delete_execute_pending", None)
    for history_filter_key in (
        "history_commands_filter",
        "history_directories_filter",
    ):
        st.session_state.setdefault(history_filter_key, "All")
        st.session_state[history_filter_key] = normalized_table_filter_selection(
            st.session_state[history_filter_key], hhs_ui.HISTORY_FILTERS
        )
    normalize_persisted_table_text_filter_states(
        *(
            key
            for key in hhs_ui_constants.PERSISTED_UI_KEYS
            if isinstance(key, str) and key.endswith("_other_filter")
        )
    )
    st.session_state["history_stats_top_n"] = normalized_history_stats_top_n(
        st.session_state.get("history_stats_top_n")
    )
    if not st.session_state.get(hhs_ui_constants.UI_STATE_FILE_SYNCED_SESSION_KEY):
        save_ui_state()
        st.session_state[hhs_ui_constants.UI_STATE_FILE_SYNCED_SESSION_KEY] = True
    complete_background_action_jobs()
    execute_pending_dialog_callback()
    apply_pending_folder_picker_selection()
    render_sidebar()
    render_main_view()
    render_combobox_vt100_shortcuts_script()
    render_footer_status_fragment()
    render_footer_client_error_bridge_script()
    install_footer_status_log_handler()
    render_folder_picker_dialog()
    render_command_preloader_events()
    render_browser_cleanup_script()


if __name__ == "__main__":
    main()
