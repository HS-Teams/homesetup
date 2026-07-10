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

import atexit
import hashlib
import html
import json
import logging
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
import textwrap
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import warnings
from base64 import b64encode
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hhs_ui
import hhs_ui.constants as hhs_ui_constants
from hhs_ui.command_catalog import (
    normalized_top_n,
    normalized_monitor_top_n,
    normalized_history_stats_top_n,
    normalized_monitor_disk_top_n,
    normalized_monitor_log_tail_lines,
    terminal_output_line_is_noise,
    filter_terminal_output_noise,
    strip_ansi,
    clean_command_status_message,
    service_action_success_message,
    clean_service_action_error,
    service_action_status_message,
    updater_output_has_updates,
    overlaps_existing_range,
    log_tailor_highlight_ranges,
    log_filter_highlight_ranges,
    colorize_log_output,
    filter_log_output,
    interpret_terminal_edit_sequences,
    clean_hhs_ask_output,
    current_username,
    parse_current_ollama_model,
    parse_ollama_model_rows,
    parse_downloaded_ollama_models,
    first_downloaded_ollama_model,
    ollama_model_status,
    ollama_model_context_size,
    parse_context_window_kib,
    file_size_bytes,
    percent_of_context,
    ai_context_usage_percentages,
    ai_context_used_percent,
    ai_context_used_color,
    html_tooltip_chip,
    ai_context_used_tooltip_html,
    ai_context_used_meta_html,
    format_ai_request_duration,
    format_ai_chat_prefix,
    wrap_ai_code_line,
    normalize_ai_code_blocks,
    prepare_ai_chat_content,
    human_size_to_bytes,
    metric_value,
    escape_markdown_table_cell,
    markdown_table,
    normalize_markdown_table_row,
    format_hhs_sysinfo_markdown,
    parse_fixed_width_cli_table,
    docker_cli_table_output,
    filter_markdown_table_columns,
    docker_cli_table_rows,
    docker_container_is_up,
    ssh_shared_connection_closed,
    strip_ssh_shared_connection_notice,
    remote_command_startup_line_is_noise,
    homesetup_motd_template,
    skip_shell_expansion,
    motd_literal_template_text,
    motd_template_fragment_groups,
    homesetup_motd_fragment_groups,
    remote_command_motd_line_is_boundary,
    strip_remote_command_motd_block,
    strip_remote_command_startup_chatter,
    sanitize_remote_command_result,
    ssh_output_is_only_shared_close,
    completed_disconnected_ssh_process,
    build_hhs_env_environment_command,
    build_hhs_envs_command,
    build_homesetup_version_command,
    build_hhs_env_action_command,
    build_hhs_sysinfo_command,
    build_open_directory_command,
    build_footer_working_directory_command,
    build_hhs_updater_command,
    build_hhs_setup_plugin_command,
    build_hhs_setup_settings_command,
    build_hhs_setup_apply_command,
    build_hhs_setup_restore_command,
    build_hhs_starship_info_command,
    build_hhs_firebase_info_command,
    build_hhs_firebase_plugin_command,
    build_hhs_firebase_alias_action_command,
    build_hhs_starship_plugin_command,
    build_hhs_settings_plugin_prefix,
    build_hhs_settings_plugin_command,
    build_hhs_settings_list_command,
    build_hhs_settings_add_command,
    build_hhs_settings_delete_command,
    build_hhs_settings_delete_many_command,
    build_hhs_settings_truncate_command,
    build_hhs_starship_preset_command,
    build_hhs_save_starship_config_command,
    build_hhs_save_firebase_config_command,
    build_ssh_tunnels_command,
    build_hhs_tools_command,
    build_hhs_shopt_setup_command,
    build_hhs_shopt_load_saved_command,
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
    build_hhs_history_stats_command,
    build_process_monitor_command,
    build_hhs_process_list_command,
    build_hhs_process_kill_command,
    build_hhs_logs_command,
    build_hhs_ask_execute_command,
    build_hhs_ask_plugin_command,
    build_hhs_ask_command,
    terminal_context_source_label,
    terminal_context_markdown_fence,
    build_terminal_ai_context_prompt,
    build_hhs_ask_context_command,
    build_hhs_ask_prompt_file_command,
    build_hhs_ask_prompt_command,
    build_hhs_save_ask_prompt_file_command,
    build_hhs_revert_ask_prompt_file_command,
    build_hhs_ask_reset_command,
    build_hhs_ask_ingest_command,
    build_hhs_ask_models_command,
    build_hhs_ask_select_model_command,
    build_ollama_delete_model_command,
    build_hhs_path_environment_command,
    build_hhs_paths_raw_entries_command,
    build_hhs_paths_command,
    build_hhs_path_action_command,
    build_hhs_dirs_command,
    build_hhs_dir_action_command,
    build_hhs_commands_command,
    build_hhs_command_action_command,
    build_hhs_aliases_command,
    build_hhs_alias_action_command,
    build_hhs_services_command,
    env_filter_pattern,
    row_matches_text_filter,
    filter_env_rows,
    filter_shopt_rows,
    path_row_matches_filter,
    filter_path_rows,
    filter_rows_by_text,
    filter_process_rows,
    parse_hhs_envs,
    parse_hhs_tools,
    shopt_status_value,
    shopt_description,
    parse_hhs_shopt,
    parse_hhs_dirs,
    parse_hhs_commands,
    parse_hhs_aliases,
    parse_hhs_setup_settings,
    hhs_settings_ini_file,
    load_hhs_settings_defaults,
    hhs_setting_variable_name,
    setman_table_cells,
    hhs_settings_row_setting,
    hhs_settings_csv_row,
    parse_hhs_settings_list,
    parse_hhs_config_environment,
    parse_hhs_starship_info,
    parse_hhs_properties,
    hhs_firebase_config_aliases,
    parse_hhs_firebase_info,
    normalize_hhs_firebase_value,
    render_hhs_firebase_config_content,
    parse_hhs_services,
    split_ssh_command,
    ssh_command_executable_name,
    ssh_forward_spec_parts,
    ssh_config_forward_parts,
    ssh_process_host,
    ssh_tunnel_row,
    append_ssh_forward_row,
    parse_ssh_config_tunnels,
    parse_ssh_tunnel_process,
    merge_ssh_tunnel_rows,
    parse_ssh_tunnels,
    normalized_bind_host,
    split_bind_address,
    split_host_port,
    default_port_kinds,
    ssh_tunnel_kind_port,
    ssh_tunnel_kind,
    local_port_is_reachable,
    build_port_reachability_command,
    ssh_tunnel_link,
    display_ssh_tunnel_rows,
    filter_ssh_tunnel_rows,
    ssh_tunnel_status_cell_style,
    parse_legacy_hhs_history_line,
    parse_hhs_history,
    parse_hhs_history_dirs,
    parse_hhs_history_stats,
    parse_hhs_disk_usage,
    parse_process_monitor,
    parse_hhs_process_list,
    path_sources,
    path_types,
    path_statuses,
    path_entries,
    parse_hhs_paths,
    env_widget_key_fragment,
    env_value_editor_key,
    dir_value_editor_key,
    cmd_value_editor_key,
    alias_value_editor_key,
)
from hhs_ui.process_resources import (
    install_footer_status_log_handler,
    process_resource_registry,
    process_resource_state,
)
from hhs_ui.paths import (
    hhs_log_dir,
    hhs_log_file_info,
    hhs_log_file_path,
    hhs_log_files,
    homesetup_config_dir,
    homesetup_home,
    ollama_history_file,
    ollama_prompt_file,
)
from hhs_ui.runtime import RUN_SHELL, shell_version_command
from hhs_ui.search_core import (
    build_hhs_open_search_result_command,
    build_hhs_search_command,
    normalized_search_option_values,
    normalized_search_type,
    path_from_file_uri,
    search_full_path,
    search_output_line_is_status,
    search_relative_path,
    search_result_download_name,
    search_type_label,
)
from hhs_ui import path_picker as path_picker_ui
from hhs_ui.path_picker import (
    apply_pending_folder_picker_selection,
    render_folder_picker_dialog,
    request_folder_picker,
    request_path_picker,
    stop_path_picker_listing_jobs,
)
from hhs_ui.table_ui import (
    clean_table_text_filter_value,
    clear_table_other_filter,
    cmd_column_config,
    config_filter_columns,
    config_filter_display_label,
    config_filter_return_value,
    display_path_value,
    display_table_rows,
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
    normalize_table_text_filter_state,
    normalized_table_filter_selection,
    path_column_config,
    plot_chart,
    render_chart_controls,
    render_markdown_table,
    render_read_only_rows,
    render_standard_number_spinner,
    render_table,
    render_table_controls_panel,
    render_table_filter_controls,
    render_view_subtitle,
    resolve_css_custom_property,
    styled_path_rows,
    styled_service_rows,
    styled_shopt_rows,
    styled_tool_rows,
    table_filter_mapping,
    table_height,
    table_selection_rerun_in_progress,
)
from hhs_ui.ssh_core import (
    build_ssh_check_command,
    build_ssh_connect_command,
    build_ssh_disconnect_command,
    build_ssh_wrapped_command,
    local_hostname,
    ssh_config_file,
    ssh_config_hostname,
    ssh_config_hosts,
    ssh_config_option,
    ssh_config_option_args,
    ssh_connection_display,
    ssh_control_path,
)
from hhs_ui.theme_assets import (
    available_theme_options,
    configure_app_font_theme,
    default_theme_name,
    format_datetime,
    load_app_image_data_uri,
    load_text_file,
    render_styles,
    theme_custom_properties,
    validated_theme_name,
)
from hhs_ui.ui_state import (
    is_persistable_ui_value,
    is_persisted_ui_key,
    load_ui_state,
    persisted_theme_name,
    restore_persisted_theme_selection,
    restore_ui_state,
    save_ui_state,
    ui_state_files,
    unlink_legacy_ui_state_files,
)
from hhs_ui.ui_definitions import (
    AI_ASK_JOB,
    AI_CONTEXT_ACTION_JOB,
    AI_MODEL_DELETE_JOB,
    AI_MODEL_SELECT_JOB,
    AI_PROMPT_ACTION_JOB,
    ALIAS_LIST_JOB,
    BACKGROUND_JOB_STATE_KEY_PREFIX,
    CACHE_CLEAR_BACKGROUND_JOBS,
    COMMAND_PRELOADER_BUS,
    COMMAND_PRELOADER_EVENT_BUS_REGISTRY_KEY,
    COMMAND_PRELOADER_EVENT_QUEUE_KEY,
    COMMAND_PRELOADER_FINISH_EVENT,
    COMMAND_PRELOADER_START_EVENT,
    COMMAND_PRELOADER_SUBSCRIBER_MARKER,
    CONFIG_ACTION_JOB,
    DOCKER_ACTION_JOB,
    FIREBASE_CONFIG_CONTENT_OUTPUT_MARKER,
    FIREBASE_CONFIG_END_OUTPUT_MARKER,
    FIREBASE_CONFIG_FILE_OUTPUT_MARKER,
    FOOTER_VERSION_CACHE_TAG,
    FOOTER_VERSION_JOB,
    FOOTER_VERSION_OUTPUT_MARKER,
    FOOTER_WORKING_DIR_JOB,
    HHS_CONFIG_ENV_OUTPUT_MARKER,
    HHS_FIREBASE_ACTION_JOB,
    HHS_FIREBASE_FIELDS,
    HHS_PATHS_RAW_ENTRY_MARKER,
    HHS_SETTINGS_ACTION_JOB,
    HHS_SETUP_ACTION_JOB,
    HHS_SETUP_SETTINGS,
    HHS_STARSHIP_ACTION_JOB,
    HOME_TOOL_ACTION_JOB,
    HOME_TOOL_TLDR_JOB,
    HOST_SWITCH_BACKGROUND_JOBS,
    HOST_SWITCH_CACHE_TAGS,
    HOST_SWITCH_STATE_KEYS,
    HOST_SWITCH_VIEW_STATE_KEY,
    MONITOR_CPU_JOB,
    MONITOR_MEM_JOB,
    MONITOR_PROCESS_ACTION_JOB,
    MONITOR_PROCESS_LIST_JOB,
    SEARCH_COMMAND_JOB,
    SEARCH_OPEN_JOB,
    SERVICE_ACTION_JOB,
    SERVICE_LIST_JOB,
    SHOPT_DESCRIPTIONS,
    SSH_CONNECT_JOB,
    SSH_DISCONNECT_JOB,
    SSH_EXPLORER_ACTION_JOB,
    SSH_EXPLORER_DELETE_JOB,
    SSH_FILE_TRANSFER_JOB,
    STARSHIP_CACHE_OUTPUT_MARKER,
    STARSHIP_CONFIG_CONTENT_OUTPUT_MARKER,
    STARSHIP_CONFIG_OUTPUT_MARKER,
    STARSHIP_END_OUTPUT_MARKER,
    STARSHIP_HHS_DIR_OUTPUT_MARKER,
    STARSHIP_PRESETS_OUTPUT_MARKER,
    TERMINAL_AI_DEFAULT_PROMPT,
    UPDATER_CHECK_JOB,
    UPDATER_UPDATE_JOB,
)


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


UI_CACHE_MEMORY: dict[str, dict[str, object]] = {}
UI_CACHE_MEMORY_MTIME: float | None = None


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


def clear_ttyd_exit_request() -> None:
    """Drop any pending ttyd exit request for the current browser session."""
    token = str(
        st.session_state.get(hhs_ui_constants.TTYD_CLEANUP_TOKEN_KEY, "")
    ).strip()
    entry = TTYD_CLEANUP_REGISTRY.get(token)
    if isinstance(entry, dict):
        entry.pop("exit_requested", None)


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


def reconnect_view_state_keys() -> tuple[str, ...]:
    """Return UI navigation keys that must survive SSH host switches."""
    return (
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


def reconnect_view_state_snapshot() -> dict[str, object]:
    """Return persisted view state that should survive SSH host switches."""
    persisted_state = load_ui_state()
    snapshot = {}
    for key in reconnect_view_state_keys():
        if key in st.session_state:
            value = st.session_state.get(key)
        else:
            value = persisted_state.get(key)
        if is_persistable_ui_value(value):
            snapshot[key] = value
    return snapshot


def remember_host_switch_view_state() -> dict[str, object]:
    """Store the current UI navigation state before an SSH host switch."""
    snapshot = reconnect_view_state_snapshot()
    st.session_state[HOST_SWITCH_VIEW_STATE_KEY] = snapshot
    return {
        key: value for key, value in snapshot.items() if is_persistable_ui_value(value)
    }


def consume_host_switch_view_state() -> dict[str, object]:
    """Return and clear the stored SSH host-switch navigation state."""
    snapshot = st.session_state.pop(HOST_SWITCH_VIEW_STATE_KEY, None)
    if not isinstance(snapshot, dict):
        return reconnect_view_state_snapshot()
    return {
        key: value
        for key, value in snapshot.items()
        if isinstance(key, str) and is_persistable_ui_value(value)
    }


def restore_reconnect_view_state(snapshot: dict[str, object]) -> None:
    """Restore persisted view state after an automatic SSH reconnect reset."""
    for key, value in snapshot.items():
        st.session_state[key] = value


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
    """Queue a backend ask reset and current AI chat-history clear."""
    queue_ai_context_action(
        "clear_chat",
        build_hhs_ask_reset_command(),
        "Resetting Ollama context",
        {
            "success_fallback": "AI chat history cleared.",
            "error_fallback": "Unable to clear AI chat history.",
        },
    )


def clear_ai_context_history() -> None:
    """Queue a backend ask reset and current context display clear."""
    queue_ai_context_action(
        "clear_context",
        build_hhs_ask_reset_command(),
        "Resetting Ollama context",
        {
            "success_fallback": "AI context history cleared.",
            "error_fallback": "Unable to clear AI context history.",
        },
    )


def confirm_ai_chat_clear() -> None:
    """Schedule the AI chat history reset after closing dialogs."""
    st.session_state["ai_clear_chat_execute_pending"] = True
    st.session_state["ai_clear_chat_pending"] = False
    save_ui_state()


def execute_pending_ai_chat_clear() -> None:
    """Queue a pending AI chat reset after dialogs are closed."""
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
    """Queue a backend ask context refresh for the Context tab."""
    queue_ai_context_action(
        "refresh",
        build_hhs_ask_context_command(),
        "Loading Ollama context",
        {
            "success_fallback": "AI context refreshed.",
            "error_fallback": "Unable to load Ollama context.",
        },
    )


def refresh_ai_prompt_file() -> None:
    """Invalidate the editable backend ask prompt file so it reloads in background."""
    cache_delete_tag("ai")
    st.session_state["ai_prompt_loaded"] = False
    save_ui_state()


def save_ai_prompt_file() -> None:
    """Queue saving the editable backend ask prompt file from the Prompt panel."""
    prompt_text = str(st.session_state.get("ai_prompt_editor", ""))
    queue_ai_prompt_action(
        "save",
        build_hhs_save_ask_prompt_file_command(prompt_text),
        "Saving Ollama prompt file",
        {
            "success_fallback": "Ollama prompt saved.",
            "error_fallback": "Unable to save Ollama prompt.",
        },
    )


def revert_ai_prompt_file() -> None:
    """Queue restoring the editable backend ask prompt file from source."""
    queue_ai_prompt_action(
        "revert",
        build_hhs_revert_ask_prompt_file_command(),
        "Reverting Ollama prompt file",
        {
            "success_fallback": "Ollama prompt reverted.",
            "error_fallback": "Unable to revert Ollama prompt.",
        },
    )


def queue_ai_context_action(
    action: str,
    command: str,
    description: str,
    metadata: dict[str, object] | None = None,
) -> None:
    """Queue an AI context mutation or refresh for background execution."""
    st.session_state["ai_context_action_execute_pending"] = {
        **(metadata or {}),
        "action": action,
        "command": command,
        "description": description,
    }
    save_ui_state()


def queue_ai_prompt_action(
    action: str,
    command: str,
    description: str,
    metadata: dict[str, object] | None = None,
) -> None:
    """Queue an AI prompt-file mutation for background execution."""
    st.session_state["ai_prompt_action_execute_pending"] = {
        **(metadata or {}),
        "action": action,
        "command": command,
        "description": description,
    }
    save_ui_state()


def start_pending_ai_context_action() -> None:
    """Start a queued AI context action background job, when present."""
    pending = st.session_state.pop("ai_context_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        AI_CONTEXT_ACTION_JOB,
        command,
        description,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        pending,
        "Another AI context action is already running.",
    )
    if not started:
        st.session_state["ai_context_action_execute_pending"] = pending


def complete_ai_context_action_job() -> None:
    """Complete an AI context action and update context state."""
    completed = background_job_result(AI_CONTEXT_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    action = str(metadata.get("action", "")).strip()
    output = result.stdout if result.returncode == 0 else result.stderr or result.stdout
    clean_output = strip_ansi(output or "").strip()
    upload_path = str(metadata.get("upload_path", "")).strip()
    if upload_path:
        try:
            Path(upload_path).unlink(missing_ok=True)
        except OSError:
            pass
    if result.returncode != 0:
        st.session_state["ai_context_error"] = clean_output or str(
            metadata.get("error_fallback", "Unable to update AI context.")
        )
        if action in {"refresh", "ingest", "refresh_after_ingest"}:
            st.session_state["ai_context_output"] = ""
        push_floating_status(st.session_state["ai_context_error"], "error")
        save_ui_state()
        return
    if action == "refresh":
        st.session_state["ai_context_output"] = (
            clean_output or "No Ollama context available."
        )
        st.session_state["ai_context_error"] = ""
        push_floating_status(
            str(metadata.get("success_fallback", "AI context refreshed.")), "info"
        )
    elif action == "refresh_after_ingest":
        st.session_state["ai_context_output"] = (
            clean_output or "No Ollama context available."
        )
        st.session_state["ai_context_error"] = ""
        push_floating_status(
            str(metadata.get("success_fallback", "Ingested AI context.")), "info"
        )
    elif action == "ingest":
        queue_ai_context_action(
            "refresh_after_ingest",
            build_hhs_ask_context_command(),
            "Loading Ollama context",
            {
                "success_fallback": str(
                    metadata.get("success_fallback", "Ingested AI context.")
                ),
                "error_fallback": "Unable to load Ollama context.",
            },
        )
        start_pending_ai_context_action()
    elif action in {"clear_chat", "clear_context"}:
        cache_delete_tag("ai")
        st.session_state["ai_context_output"] = ""
        st.session_state["ai_context_error"] = ""
        if action == "clear_chat":
            st.session_state["ai_chat_messages"] = []
            st.session_state["ai_clear_chat_pending"] = False
            st.session_state["ai_clear_chat_execute_pending"] = False
        push_floating_status(
            clean_output
            or str(metadata.get("success_fallback", "AI context cleared.")),
            "info",
        )
    save_ui_state()


def execute_pending_ai_context_action() -> None:
    """Start or complete the current AI context action background job."""
    start_pending_ai_context_action()
    complete_ai_context_action_job()


def start_pending_ai_prompt_action() -> None:
    """Start a queued AI prompt-file action background job, when present."""
    pending = st.session_state.pop("ai_prompt_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        AI_PROMPT_ACTION_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another AI prompt action is already running.",
    )
    if not started:
        st.session_state["ai_prompt_action_execute_pending"] = pending


def complete_ai_prompt_action_job() -> None:
    """Complete an AI prompt-file action and update prompt editor state."""
    completed = background_job_result(AI_PROMPT_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    action = str(metadata.get("action", "")).strip()
    output = strip_ansi(result.stdout or result.stderr or "")
    if result.returncode == 0:
        cache_delete_tag("ai")
        if action == "revert":
            st.session_state["ai_prompt_editor"] = output
        st.session_state["ai_prompt_error"] = ""
        st.session_state["ai_prompt_loaded"] = True
        push_floating_status(
            output.strip()
            or str(metadata.get("success_fallback", "Ollama prompt updated.")),
            "info",
        )
    else:
        st.session_state["ai_prompt_error"] = output.strip() or str(
            metadata.get("error_fallback", "Unable to update Ollama prompt.")
        )
        push_floating_status(st.session_state["ai_prompt_error"], "error")
    save_ui_state()


def execute_pending_ai_prompt_action() -> None:
    """Start or complete the current AI prompt-file action background job."""
    start_pending_ai_prompt_action()
    complete_ai_prompt_action_job()


def uploaded_context_suffix(file_name: str) -> str:
    """Return a safe suffix for an uploaded AI context file."""
    suffix = Path(file_name).suffix.lower()
    if suffix.lstrip(".") in hhs_ui_constants.AI_CONTEXT_UPLOAD_TYPES:
        return suffix
    return ".txt"


def ui_disposable_files_dir() -> Path:
    """Return the cache directory used for disposable HomeSetup UI files."""
    hhs_ui.HHS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return hhs_ui.HHS_CACHE_DIR


def ai_context_upload_path(file_name: str) -> Path:
    """Return the deterministic cache path for an uploaded AI context file."""
    return (
        ui_disposable_files_dir()
        / f"hhs-ai-context-upload{uploaded_context_suffix(file_name)}"
    )


def ingest_ai_context_upload(uploaded_file: object) -> None:
    """Ingest an uploaded text file into the backend ask context."""
    if uploaded_file is None:
        st.session_state["ai_context_error"] = "Choose a text file to ingest."
        save_ui_state()
        return

    file_name = str(getattr(uploaded_file, "name", "context.txt"))
    tmp_file_path = ai_context_upload_path(file_name)

    try:
        tmp_file_path.write_bytes(uploaded_file.getvalue())
    except OSError:
        st.session_state["ai_context_error"] = "Unable to store uploaded context."
        save_ui_state()
        return
    queue_ai_context_action(
        "ingest",
        build_hhs_ask_ingest_command(str(tmp_file_path)),
        "Ingesting Ollama context",
        {
            "upload_path": str(tmp_file_path),
            "success_fallback": f"Ingested context: {file_name}",
            "error_fallback": "Unable to ingest context.",
        },
    )


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
            show_preloader_event=True,
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
            show_preloader_event=True,
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
        show_preloader_event=True,
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
        show_preloader_event=True,
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
        render_sidebar_title_separator_alignment_script()
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
            render_ttyd_terminal_frame_hide_script()
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
    safe_theme_name = theme_name.strip() or hhs_ui.APP_THEME_CSS_FILE.stem
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


def close_all_dialogs() -> None:
    """Close every Streamlit dialog or inline confirmation controlled by this UI."""
    st.session_state.pop("_hhs_dialog_pending_callback", None)
    st.session_state.pop("_hhs_dialog_button_dismissal", None)
    st.session_state.pop("_hhs_dialog_dismiss_requested", None)
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


def render_pending_streamlit_dialog_dismiss() -> None:
    """Render a queued browser-side dialog dismiss script during normal dialog flow."""
    if not st.session_state.pop("_hhs_dialog_dismiss_requested", False):
        return
    render_script_html("""
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
        """)


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
        render_pending_streamlit_dialog_dismiss()
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


def render_combobox_vt100_shortcuts_script() -> None:
    """Attach readline-style keyboard shortcuts to editable combobox inputs."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (parentWindow.__hhsComboboxVt100Cleanup) {
              parentWindow.__hhsComboboxVt100Cleanup();
            }
            const isEditableComboboxInput = (node) => {
              if (!node || typeof node.closest !== "function") {
                return false;
              }
              const tagName = String(node.tagName || "").toLowerCase();
              if (tagName !== "input" && tagName !== "textarea") {
                return false;
              }
              if (node.disabled || node.readOnly) {
                return false;
              }
              return Boolean(
                node.closest('[data-baseweb="select"]') ||
                node.closest('[role="combobox"]') ||
                String(node.getAttribute("role") || "").toLowerCase() === "combobox"
              );
            };
            const setNativeValue = (node, value) => {
              const prototype = Object.getPrototypeOf(node);
              const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
              if (descriptor && descriptor.set) {
                descriptor.set.call(node, value);
                return;
              }
              node.value = value;
            };
            const dispatchInputEvent = (node, inputType, data = null) => {
              let inputEvent = null;
              try {
                inputEvent = new InputEvent("input", {
                  bubbles: true,
                  inputType,
                  data,
                });
              } catch (error) {
                inputEvent = new Event("input", { bubbles: true });
              }
              node.dispatchEvent(inputEvent);
            };
            const normalizedText = (value) =>
              String(value || "").replace(/\s+/g, " ").trim();
            const isVisibleNode = (node) => {
              if (!node || typeof node.getClientRects !== "function") {
                return false;
              }
              if (node.getClientRects().length === 0) {
                return false;
              }
              const style = parentWindow.getComputedStyle(node);
              return style.display !== "none" && style.visibility !== "hidden";
            };
            const isSearchTermsComboboxInput = (node) =>
              isEditableComboboxInput(node) &&
              Boolean(node.closest(".st-key-search_query"));
            const dispatchMouseEvent = (node, eventName) => {
              node.dispatchEvent(
                new MouseEvent(eventName, {
                  bubbles: true,
                  cancelable: true,
                  view: parentWindow,
                })
              );
            };
            const activateComboboxOption = (option) => {
              for (const eventName of ["mousedown", "mouseup", "click"]) {
                dispatchMouseEvent(option, eventName);
              }
            };
            const selectPendingSearchTermAddOption = (node) => {
              if (!isSearchTermsComboboxInput(node)) {
                return false;
              }
              const value = normalizedText(node.value);
              if (!value) {
                return false;
              }
              const lowerValue = value.toLowerCase();
              const optionSelectors = [
                '[role="option"]',
                '[data-baseweb="menu"] li',
                '[data-baseweb="popover"] li',
              ];
              const addOption = Array.from(
                doc.querySelectorAll(optionSelectors.join(","))
              ).find((option) => {
                if (!isVisibleNode(option)) {
                  return false;
                }
                const text = normalizedText(option.textContent);
                const lowerText = text.toLowerCase();
                return lowerText.startsWith("add:") && lowerText.includes(lowerValue);
              });
              if (!addOption) {
                return false;
              }
              activateComboboxOption(addOption);
              return true;
            };
            const selectionState = (node) => {
              const value = String(node.value || "");
              const fallback = value.length;
              const rawStart = Number.isInteger(node.selectionStart)
                ? node.selectionStart
                : fallback;
              const rawEnd = Number.isInteger(node.selectionEnd)
                ? node.selectionEnd
                : rawStart;
              const start = Math.max(0, Math.min(rawStart, value.length));
              const end = Math.max(start, Math.min(rawEnd, value.length));
              return { value, start, end };
            };
            const setCaret = (
              node,
              position,
              length = String(node.value || "").length
            ) => {
              if (typeof node.setSelectionRange !== "function") {
                return;
              }
              const cursor = Math.max(0, Math.min(position, length));
              node.setSelectionRange(cursor, cursor);
            };
            const replaceRange = (node, start, end, replacement, inputType) => {
              const state = selectionState(node);
              const boundedStart = Math.max(0, Math.min(start, state.value.length));
              const boundedEnd = Math.max(boundedStart, Math.min(end, state.value.length));
              const nextValue =
                state.value.slice(0, boundedStart) +
                replacement +
                state.value.slice(boundedEnd);
              setNativeValue(node, nextValue);
              setCaret(node, boundedStart + replacement.length, nextValue.length);
              dispatchInputEvent(node, inputType, replacement || null);
            };
            const previousWordStart = (value, start) => {
              let index = Math.max(0, Math.min(start, value.length));
              while (index > 0 && /\s/.test(value.charAt(index - 1))) {
                index -= 1;
              }
              while (index > 0 && !/\s/.test(value.charAt(index - 1))) {
                index -= 1;
              }
              return index;
            };
            const onKeydown = (event) => {
              const node = event.target;
              if (
                event.key === "Enter" &&
                !event.ctrlKey &&
                !event.metaKey &&
                !event.altKey &&
                selectPendingSearchTermAddOption(node)
              ) {
                event.preventDefault();
                event.stopPropagation();
                if (typeof event.stopImmediatePropagation === "function") {
                  event.stopImmediatePropagation();
                }
                return;
              }
              if (!(event.ctrlKey || event.metaKey) || event.altKey) {
                return;
              }
              if (!isEditableComboboxInput(node)) {
                return;
              }
              const key = String(event.key || "").toLowerCase();
              const state = selectionState(node);
              const hasSelection = state.start !== state.end;
              let handled = true;
              switch (key) {
                case "a":
                  setCaret(node, 0, state.value.length);
                  break;
                case "e":
                  setCaret(node, state.value.length, state.value.length);
                  break;
                case "b":
                  setCaret(node, Math.max(0, state.start - 1), state.value.length);
                  break;
                case "f":
                  setCaret(
                    node,
                    Math.min(state.value.length, state.end + 1),
                    state.value.length
                  );
                  break;
                case "d":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentForward");
                  } else if (state.start < state.value.length) {
                    replaceRange(node, state.start, state.start + 1, "", "deleteContentForward");
                  }
                  break;
                case "h":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentBackward");
                  } else if (state.start > 0) {
                    replaceRange(node, state.start - 1, state.start, "", "deleteContentBackward");
                  }
                  break;
                case "k":
                  if (state.start < state.value.length) {
                    replaceRange(node, state.start, state.value.length, "", "deleteContentForward");
                  }
                  break;
                case "u":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentBackward");
                  } else if (state.start > 0) {
                    replaceRange(node, 0, state.start, "", "deleteContentBackward");
                  }
                  break;
                case "w":
                  if (hasSelection) {
                    replaceRange(node, state.start, state.end, "", "deleteContentBackward");
                  } else if (state.start > 0) {
                    replaceRange(
                      node,
                      previousWordStart(state.value, state.start),
                      state.start,
                      "",
                      "deleteWordBackward"
                    );
                  }
                  break;
                default:
                  handled = false;
              }
              if (!handled) {
                return;
              }
              event.preventDefault();
              event.stopPropagation();
              if (typeof event.stopImmediatePropagation === "function") {
                event.stopImmediatePropagation();
              }
            };
            doc.addEventListener("keydown", onKeydown, true);
            parentWindow.__hhsComboboxVt100Cleanup = () => {
              doc.removeEventListener("keydown", onKeydown, true);
            };
          })();
        </script>
        """,
        height=0,
        width=0,
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


def normalize_monitor_log_tail_lines_state() -> int:
    """Normalize and migrate the persisted monitor log bottom-line count."""
    raw_tail_lines = st.session_state.get("monitor_log_tail_lines")
    tail_lines = normalized_monitor_log_tail_lines(raw_tail_lines)
    migrated = bool(
        st.session_state.get("monitor_log_tail_lines_default_migrated", False)
    )
    if (
        raw_tail_lines is not None
        and not migrated
        and tail_lines == hhs_ui_constants.LEGACY_DEFAULT_LOG_TAIL_LINES
    ):
        tail_lines = hhs_ui_constants.DEFAULT_LOG_TAIL_LINES
    st.session_state["monitor_log_tail_lines"] = tail_lines
    st.session_state["monitor_log_tail_lines_default_migrated"] = True
    return tail_lines


def monitor_process_top_n_state_key(metric: str) -> str:
    """Return the session key for the applied process monitor Top N value."""
    return f"monitor_{metric.lower()}_top_n"


def monitor_process_top_n_input_key(metric: str) -> str:
    """Return the session key for the pending process monitor Top N value."""
    return f"monitor_{metric.lower()}_top_n_input"


def monitor_default_disk_directory() -> str:
    """Return the default directory for the disk monitor."""
    if connected_ssh_host():
        return "${HHS_HOME}"
    return str(homesetup_home())


def monitor_disk_directory_is_hhs_home_token(directory: object) -> bool:
    """Return whether a disk monitor directory references HomeSetup home."""
    return str(directory or "").strip() in {"${HHS_HOME}", "$HHS_HOME"}


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


def handle_monitor_log_tail_lines_change() -> None:
    """Persist the pending monitor log bottom-line count."""
    normalize_monitor_log_tail_lines_state()
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


def refresh_history_stats_chart() -> None:
    """Clear cached history stats so the next chart run reloads command data."""
    top_n = normalized_history_stats_top_n(st.session_state.get("history_stats_top_n"))
    cache_delete_command(build_hhs_history_stats_command(top_n), "history")
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


def render_footer_client_error_bridge_script() -> None:
    """Mirror client-side Streamlit errors and alerts into the footer status UI."""
    render_script_html("""
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            if (!doc?.body || parentWindow.__hhsFooterErrorBridgeInstalled) {
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

            const showStatus = (message, kind = "error") => {
              const cleanMessage = normalize(message);
              if (!cleanMessage || !remember(cleanMessage)) {
                return;
              }
              doc.getElementById("hhs-client-floating-status")?.remove();
              const status = doc.createElement("div");
              status.id = "hhs-client-floating-status";
              status.className = `hhs-floating-status hhs-floating-status-kind-${kind} hhs-floating-status--stable`;
              status.style.setProperty("--hhs-floating-status-timeout", "8s");

              const glyph = doc.createElement("span");
              glyph.className = "hhs-floating-status-glyph";
              glyph.textContent = kind === "error" ? "" : "";

              const text = doc.createElement("span");
              text.className = "hhs-floating-status-message";
              text.textContent = cleanMessage;

              const dismiss = doc.createElement("button");
              dismiss.className = "hhs-floating-status-dismiss";
              dismiss.type = "button";
              dismiss.setAttribute("aria-label", "Dispose footer status");
              dismiss.title = "Dispose footer status";
              dismiss.textContent = "x";
              dismiss.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                status.classList.add("hhs-floating-status--disposing");
                parentWindow.clearTimeout(parentWindow.__hhsFooterErrorBridgeTimer);
                parentWindow.setTimeout(() => status.remove(), 240);
              });

              status.append(glyph, text, dismiss);
              doc.body.append(status);
              parentWindow.clearTimeout(parentWindow.__hhsFooterErrorBridgeTimer);
              parentWindow.__hhsFooterErrorBridgeTimer = parentWindow.setTimeout(() => {
                status.remove();
              }, 9000);
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
        """)


def footer_cache_clear_menu_markup() -> str:
    """Return the native HTML footer cleanup menu without form semantics."""
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
          <span class="hhs-footer-glyph-button">♻</span>
        </summary>
        <div class="hhs-footer-cache-clear-panel" data-clear-param="{clear_param}">
          <label>
            <input type="checkbox" data-param="{app_cache_param}">
            <span>Clear application cache</span>
          </label>
          <label>
            <input type="checkbox" data-param="{app_states_param}">
            <span>Clear application states</span>
          </label>
          <label>
            <input type="checkbox" data-param="{ai_history_param}">
            <span>Clear AI history</span>
          </label>
          <button type="button">OK</button>
        </div>
      </details>
    """.strip()


def render_footer_cache_clear_menu_script() -> None:
    """Submit footer cleanup choices without creating a browser form."""
    render_script_html(
        """
        <script>
          (() => {
            const doc = window.parent.document;
            const panel = doc.querySelector(".hhs-footer-cache-clear-panel");
            if (!panel || panel.dataset.clickHandlerInstalled === "true") {
              return;
            }
            panel.dataset.clickHandlerInstalled = "true";
            const menu = panel.closest(".hhs-footer-cache-clear-menu");
            const closeMenu = () => {
              if (menu) {
                menu.removeAttribute("open");
              }
            };
            const outsidePointerHandler = (event) => {
              if (!menu || !menu.open || menu.contains(event.target)) {
                return;
              }
              closeMenu();
            };
            const outsideFocusHandler = () => {
              window.setTimeout(() => {
                const activeElement = doc.activeElement;
                if (!menu || !menu.open || !activeElement || menu.contains(activeElement)) {
                  return;
                }
                closeMenu();
              }, 0);
            };
            if (window.parent.__hhsFooterCacheClearOutsideHandler) {
              doc.removeEventListener(
                "pointerdown",
                window.parent.__hhsFooterCacheClearOutsideHandler,
                true
              );
              doc.removeEventListener(
                "focusin",
                window.parent.__hhsFooterCacheClearOutsideHandler,
                true
              );
            }
            if (window.parent.__hhsFooterCacheClearOutsideFocusHandler) {
              window.parent.removeEventListener(
                "blur",
                window.parent.__hhsFooterCacheClearOutsideFocusHandler,
                true
              );
            }
            window.parent.__hhsFooterCacheClearOutsideHandler = outsidePointerHandler;
            window.parent.__hhsFooterCacheClearOutsideFocusHandler = outsideFocusHandler;
            doc.addEventListener("pointerdown", outsidePointerHandler, true);
            doc.addEventListener("focusin", outsidePointerHandler, true);
            window.parent.addEventListener("blur", outsideFocusHandler, true);
            menu?.addEventListener("toggle", () => {
              if (menu.open) {
                doc.querySelectorAll(".hhs-footer-terminal-ai-menu[open]").forEach((otherMenu) => {
                  otherMenu.removeAttribute("open");
                });
              }
            });
            panel.querySelector("button")?.addEventListener("click", () => {
              const checkedOptions = Array.from(
                panel.querySelectorAll('input[type="checkbox"][data-param]:checked')
              );
              if (!checkedOptions.length) {
                closeMenu();
                return;
              }
              const params = new URLSearchParams(window.parent.location.search);
              params.set(panel.dataset.clearParam, "1");
              checkedOptions.forEach((option) => {
                params.set(option.dataset.param, "1");
              });
              window.parent.location.search = params.toString();
            });
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
            title="Open Terminal to ask AI about terminal output"
            aria-disabled="true">
        <span class="hhs-footer-terminal-ai-trigger hhs-footer-terminal-ai-trigger--disabled"
              aria-label="Ask AI about terminal disabled">
          <span class="hhs-footer-glyph-button"></span>
        </span>
      </span>
    """.strip()
    return f"""
      <details class="hhs-footer-terminal-ai-menu">
        <summary class="hhs-footer-terminal-ai-trigger"
                 title="Ask AI about terminal"
                 aria-label="Ask AI about terminal">
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
              readonly
            >
          </label>
          <button type="button">OK</button>
        </div>
      </details>
    """.strip()


def render_footer_terminal_ai_menu_script() -> None:
    """Submit terminal context prompt choices directly into the ttyd terminal."""
    render_script_html(
        f"""
        <script>
          (() => {{
            const doc = window.parent.document;
            const panel = doc.querySelector(".hhs-footer-terminal-ai-panel");
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
              requestTerminalContext(true);
            }}, {{ capture: true }});
            if (menu) {{
              menu.addEventListener("toggle", () => {{
                if (menu.open) {{
                  ignoreTerminalContextUntil = 0;
                  doc.querySelectorAll(".hhs-footer-cache-clear-menu[open]").forEach((otherMenu) => {{
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


def open_working_directory_endpoint_url() -> str:
    """Return the local browser-to-UI endpoint URL for opening the working directory."""
    update_browser_cleanup_registration()
    token = browser_cleanup_token()
    port = ensure_ttyd_cleanup_server()
    return f"http://{hhs_ui.TTYD_HOST}:{port}/open-working-directory?token={token}"


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
            f'target="_self" title="Show bash version" aria-label="Show bash version">'
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
    shell_controls_markup = ""
    if shell_status_markup:
        shell_controls_markup = (
            f'<span class="hhs-footer-shell-group">'
            f"{shell_status_markup}{cache_clear_markup}{terminal_ai_markup}</span>"
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
          <a class="hhs-footer-link hhs-footer-working-dir-link"
             href="{working_dir_url}"
             target="_self"{working_dir_attrs}>Working dir: <span class="hhs-footer-working-dir-value">{working_dir}</span></a>
          {status_group_markup}
        </footer>
        """)
    if not connected_to_ssh:
        render_footer_working_directory_open_script()
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
    for name in (
        hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM,
        hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM,
    ):
        remove_query_param(name)


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


def file_uri_for_path(path_value: str) -> str:
    """Return a file URI for a POSIX-style absolute path."""
    clean_path = posixpath.normpath(path_value.strip())
    return f"file://{urllib.parse.quote(clean_path, safe='/')}"


def search_open_href(path_or_uri: str) -> str:
    """Return a Search-style open link for a path or file URI."""
    query = urllib.parse.urlencode({hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM: path_or_uri})
    return f"?{query}"


def render_openable_config_path(display_path: str, file_path: str) -> None:
    """Render a subtitle path link that opens a file through __hhs_open."""
    clean_display_path = display_path.strip()
    clean_file_path = file_path.strip()
    if not clean_display_path or not clean_file_path:
        return
    file_uri = file_uri_for_path(clean_file_path)
    href = html.escape(search_open_href(file_uri), quote=True)
    safe_file_uri = html.escape(file_uri, quote=True)
    safe_display_path = html.escape(clean_display_path)
    st.markdown(
        (
            '<h3 class="hhs-view-subtitle">'
            f'<a class="hhs-view-subtitle-link" href="{href}" '
            'target="_self" '
            f'title="{safe_file_uri}" '
            f'data-hhs-open-path="{safe_file_uri}">'
            f"<code>{safe_display_path}</code></a>"
            "</h3>"
        ),
        unsafe_allow_html=True,
    )


def render_config_file_pill(config_view: str) -> None:
    """Render a clickable pill for the custom config file used by a Configs page."""
    file_path = config_file_path(config_view)
    if not file_path:
        return
    file_name = posixpath.basename(file_path.rstrip("/")) or file_path
    file_uri = file_uri_for_path(file_path)
    href = html.escape(search_open_href(file_uri), quote=True)
    safe_file_uri = html.escape(file_uri, quote=True)
    page_label = CONFIG_FILE_PAGE_LABELS.get(config_view, "Environment")
    st.markdown(
        (
            '<div class="hhs-config-file-pill-row">'
            f'<span class="hhs-config-file-pill-label">Custom {html.escape(page_label)} file:</span>'
            f'<a class="hhs-config-file-pill" href="{href}" '
            'target="_self" '
            f'title="{safe_file_uri}" '
            f'data-hhs-open-path="{safe_file_uri}">'
            f'<span aria-hidden="true"></span>{html.escape(file_name)}</a>'
            "</div>"
        ),
        unsafe_allow_html=True,
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
            )
    value_input_args: dict[str, object] = {
        "key": f"{key_prefix}_add_value",
        "placeholder": value_placeholder,
    }
    if on_submit is not None:
        value_input_args["on_change"] = on_submit
    with value_col:
        st.text_input(value_label, **value_input_args)

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


def render_named_value_add_controls(
    key_prefix: str,
    name_label: str,
    value_label: str,
    name_placeholder: str,
    value_placeholder: str,
    on_submit: Callable[[], None],
    value_folder_picker: bool = False,
) -> None:
    """Render Name and Value add controls for a config listing."""
    render_config_add_controls(
        key_prefix,
        name_label,
        value_label,
        name_placeholder,
        value_placeholder,
        on_submit=on_submit,
        has_plus_btn=True,
        has_file_picker_btn=value_folder_picker,
    )


def render_value_add_controls(
    key_prefix: str,
    value_label: str,
    value_placeholder: str,
    on_submit: Callable[[], None],
    value_folder_picker: bool = False,
) -> None:
    """Render a Value add control for a config listing."""
    render_config_add_controls(
        key_prefix,
        None,
        value_label,
        "",
        value_placeholder,
        on_submit=on_submit,
        has_plus_btn=True,
        has_file_picker_btn=value_folder_picker,
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
    render_command_preloader_events()
    show_terminal_ready_status()


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


def ttyd_background_image_file() -> Path:
    """Return the image file used as the ttyd terminal background."""
    return hhs_ui.APP_TERMINAL_BACKGROUND_FILE


def ttyd_background_image_data_url() -> str:
    """Return a PNG data URL for the ttyd terminal background image."""
    background_file = ttyd_background_image_file()
    if not background_file.is_file():
        return ""
    encoded_image = b64encode(background_file.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def ttyd_index_signature(binary: str, event_url: str = "") -> str:
    """Return a stable cache signature for the ttyd index and terminal font."""
    font_file = ttyd_font_file()
    background_file = ttyd_background_image_file()
    parts = ["hhs-ttyd-font-index-v23-terminal-scroll-v1", binary, event_url]
    for path in (Path(binary), font_file, background_file):
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
    family = html.escape(ttyd_font_family(), quote=True)
    font_face = ""
    if font_file.is_file():
        encoded_font = b64encode(font_file.read_bytes()).decode("ascii")
        mime_type = ttyd_font_mime_type(font_file)
        font_format = ttyd_font_format(font_file)
        font_face = (
            "@font-face{"
            f'font-family:"{family}";'
            f'src:url("data:{mime_type};base64,{encoded_font}") format("{font_format}");'
            "font-weight:normal;"
            "font-style:normal;"
            "font-display:block;"
            "}"
        )
    background_image = html.escape(ttyd_background_image_data_url(), quote=True)
    background_layer = (
        "background-image:linear-gradient(rgba(0,0,0,0.90),rgba(0,0,0,0.90)),"
        f'url("{background_image}")!important;'
        "background-position:center center!important;"
        "background-size:cover!important;"
        "background-repeat:no-repeat!important;"
    )
    if not background_image:
        background_layer = ""
    return (
        "<style>"
        f"{font_face}"
        "html,body,#terminal,.terminal,.xterm,.xterm-screen,.xterm-rows{"
        f'font-family:"{family}",monospace!important;'
        "}"
        "html,body{"
        "background:#000000!important;"
        "min-height:100%!important;"
        "}"
        "body::before{"
        'content:"";'
        "position:fixed!important;"
        "inset:0!important;"
        "pointer-events:none!important;"
        "z-index:0!important;"
        f"{background_layer}"
        "}"
        "#terminal,.terminal,.xterm{"
        "background:transparent!important;"
        "position:relative!important;"
        "z-index:1!important;"
        "}"
        ".xterm .xterm-screen,.xterm .xterm-rows,.xterm .xterm-screen canvas{"
        "background:transparent!important;"
        "}"
        "#terminal,.terminal,.xterm{"
        "box-sizing:border-box!important;"
        "padding:0!important;"
        "}"
        ".xterm .xterm-viewport{"
        "background:transparent!important;"
        "overflow-y:scroll!important;"
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
        f"const maxContentLength={int(hhs_ui.AI_TERMINAL_CONTEXT_MAX_CHARS)};"
        "const prefix='HHS_TTYD_EVENT|';"
        "const transparentBackground='rgba(0,0,0,0)';"
        "const selectionSnapshotAgeMs=300000;"
        "let lastSelectedContent='';"
        "let lastSelectedAt=0;"
        "let lastMiddlePasteAt=0;"
        "let transparentBackgroundTimer=null;"
        "let transparentBackgroundAttempts=0;"
        "const decode=(value)=>{try{return decodeURIComponent(escape(atob(value)));}catch(_error){return '';}};"
        "const cleanContent=(value)=>String(value||'').replace(/\\r\\n?/g,'\\n').trim();"
        "const limitContent=(value)=>{const content=cleanContent(value);"
        "if(content.length<=maxContentLength){return {content,truncated:false};}"
        "return {content:content.slice(content.length-maxContentLength),truncated:true};};"
        "const applyTransparentTerminalBackground=()=>{"
        "const term=window.term;"
        "if(!term||!term.options){return false;}"
        "const theme=(term.options.theme&&typeof term.options.theme==='object')?term.options.theme:{};"
        "if(theme.background!==transparentBackground){"
        "term.options.theme={...theme,background:transparentBackground};"
        "}"
        "if(typeof term.refresh==='function'){"
        "try{term.refresh(0,Math.max(0,Number(term.rows||1)-1));}catch(_error){}"
        "}"
        "return true;"
        "};"
        "const scheduleTransparentTerminalBackground=()=>{"
        "if(transparentBackgroundTimer){return;}"
        "transparentBackgroundAttempts=0;"
        "transparentBackgroundTimer=window.setInterval(()=>{"
        "transparentBackgroundAttempts+=1;"
        "applyTransparentTerminalBackground();"
        "if(transparentBackgroundAttempts>=20){"
        "window.clearInterval(transparentBackgroundTimer);"
        "transparentBackgroundTimer=null;"
        "}"
        "},250);"
        "};"
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
        "const replyToRequester=(requestEvent,event)=>{"
        "try{if(requestEvent&&requestEvent.source&&requestEvent.source!==window.parent){"
        "requestEvent.source.postMessage({type:'hhs-ttyd-event',event},'*');}}catch(_error){}"
        "};"
        "const visibleBuffer=()=>{"
        "const term=window.term;"
        "const buffer=term&&term.buffer&&term.buffer.active;"
        "if(!term||!buffer||typeof buffer.getLine!=='function'){return '';}"
        "const rows=Number(term.rows||24);"
        "const length=Number(buffer.length||0);"
        "const viewportY=Number(buffer.viewportY||Math.max(0,(buffer.baseY||0)-rows+1));"
        "const start=Math.max(0,Math.min(length,viewportY));"
        "const end=Math.max(start,Math.min(length,start+rows));"
        "const lines=[];"
        "for(let index=start;index<end;index+=1){"
        "const line=buffer.getLine(index);"
        "if(line&&typeof line.translateToString==='function'){lines.push(line.translateToString(true));}"
        "}"
        "return lines.join('\\n');"
        "};"
        "const selectionContent=()=>{"
        "const term=window.term;"
        "return term&&typeof term.getSelection==='function'?cleanContent(term.getSelection()):'';"
        "};"
        "const cacheSelection=(value)=>{"
        "const selected=cleanContent(value);"
        "if(selected){lastSelectedContent=selected;lastSelectedAt=Date.now();}"
        "return selected;"
        "};"
        "const rememberSelection=()=>{"
        "cacheSelection(selectionContent());"
        "};"
        "const recentSelection=()=>{"
        "const current=cacheSelection(selectionContent());"
        "if(current){return current;}"
        "if(lastSelectedContent&&Date.now()-lastSelectedAt<=selectionSnapshotAgeMs){return lastSelectedContent;}"
        "return '';"
        "};"
        "const terminalContext=()=>{"
        "const selected=recentSelection();"
        "if(selected){const limited=limitContent(selected);return {...limited,mode:'selection'};}"
        "const limited=limitContent(visibleBuffer());"
        "return {...limited,mode:limited.content?'visible':'empty'};"
        "};"
        "const sendTerminalInput=(text)=>{"
        "const term=window.term;"
        "if(term&&typeof term.focus==='function'){term.focus();}"
        "const coreService=term&&term._core&&term._core.coreService;"
        "if(coreService&&typeof coreService.triggerDataEvent==='function'){"
        "coreService.triggerDataEvent(String(text||''),true);return true;}"
        "if(term&&typeof term.paste==='function'){term.paste(String(text||''));return true;}"
        "const textarea=window.document&&window.document.querySelector('.xterm-helper-textarea');"
        "if(textarea){textarea.focus();textarea.value+=String(text||'');"
        "textarea.dispatchEvent(new InputEvent('input',{inputType:'insertText',data:String(text||''),bubbles:true}));"
        "return true;}"
        "return false;"
        "};"
        "const pasteSelectedTerminalText=()=>{"
        "const selected=selectionContent();"
        "if(!selected){return false;}"
        "lastSelectedContent=selected;"
        "lastSelectedAt=Date.now();"
        "try{if(navigator.clipboard&&navigator.clipboard.writeText){"
        "navigator.clipboard.writeText(selected).catch(()=>{});}}catch(_error){}"
        "return sendTerminalInput(selected);"
        "};"
        "const middleClickPasteHandler=(event)=>{"
        "if(Number(event.button)!==1){return;}"
        "event.preventDefault();"
        "event.stopPropagation();"
        "if(event.type!=='mousedown'){return;}"
        "const now=Date.now();"
        "if(now-lastMiddlePasteAt<250){return;}"
        "if(pasteSelectedTerminalText()){lastMiddlePasteAt=now;}"
        "};"
        "const submitTerminalCommand=(command)=>{"
        "const cleanCommand=String(command||'').trim();"
        "if(!cleanCommand){return false;}"
        "if(!sendTerminalInput('\\x03')){return false;}"
        "window.setTimeout(()=>{sendTerminalInput(`${cleanCommand}\\r`);},90);"
        "return true;"
        "};"
        "window.addEventListener('message',(messageEvent)=>{"
        "const data=messageEvent.data||{};"
        "if(data.type==='hhs-ttyd-command-submit'){submitTerminalCommand(data.command);return;}"
        "if(data.type!=='hhs-ttyd-context-request'){return;}"
        "const requestId=String(data.requestId||'').replace(/[^A-Za-z0-9_.:-]/g,'').slice(0,80);"
        "const context=terminalContext();"
        "const event={type:'terminal-context',command:'ask-ai',status:context.content?0:1,cwd:'',"
        "time:Date.now(),requestId,mode:context.mode,content:context.content,truncated:context.truncated};"
        "publish(event);"
        "replyToRequester(messageEvent,event);"
        "});"
        "const install=()=>{"
        "const term=window.term;"
        "if(!term){return false;}"
        "applyTransparentTerminalBackground();"
        "scheduleTransparentTerminalBackground();"
        "if(!term.parser||window.__hhsTtydBridgeInstalled){return !!window.__hhsTtydBridgeInstalled;}"
        "window.__hhsTtydBridgeInstalled=true;"
        "term.parser.registerOscHandler(777,(data)=>{const event=parse(String(data||''));if(event){publish(event);return true;}return false;});"
        "const scheduleRememberSelection=()=>{window.setTimeout(rememberSelection,0);};"
        "window.addEventListener('mouseup',scheduleRememberSelection,true);"
        "window.addEventListener('mousedown',middleClickPasteHandler,true);"
        "window.addEventListener('auxclick',middleClickPasteHandler,true);"
        "window.addEventListener('keyup',scheduleRememberSelection,true);"
        "window.addEventListener('touchend',scheduleRememberSelection,true);"
        "if(typeof term.onSelectionChange==='function'){"
        "window.__hhsTtydSelectionChangeDisposable=term.onSelectionChange(scheduleRememberSelection);}"
        "if(window.document){window.document.addEventListener('selectionchange',scheduleRememberSelection,true);}"
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
    render_script_html(
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
              const inset = 10;
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
    """Remove the browser-persistent ttyd iframe after a Terminal session reset."""
    render_script_html(
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


def render_ttyd_terminal_frame_hide_script() -> None:
    """Hide the browser-persistent ttyd iframe while preserving its session."""
    render_script_html(
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
              frame.style.display = "none";
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
    event = {
        "type": event_type,
        "command": command or "unknown",
        "status": status,
        "cwd": cwd,
        "time": event_time,
    }
    if event_type == "terminal-context":
        content = str(value.get("content", "")).replace("\r\n", "\n")
        content = content.replace("\r", "\n").strip()
        truncated = bool(value.get("truncated", False))
        max_chars = int(hhs_ui.AI_TERMINAL_CONTEXT_MAX_CHARS)
        if len(content) > max_chars:
            content = content[-max_chars:]
            truncated = True
        event["content"] = content
        event["mode"] = re.sub(r"[^A-Za-z0-9_-]+", "", str(value.get("mode", "")))[:32]
        event["requestId"] = re.sub(
            r"[^A-Za-z0-9_.:-]+", "", str(value.get("requestId", ""))
        )[:80]
        event["truncated"] = truncated
    return event


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
            close_document_view(reset_terminal=True)
            st.rerun()
        else:
            deactivate_terminal_document_view()
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
            encoding="utf-8",
            errors="replace",
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
        request_path = urllib.parse.urlparse(self.path).path
        if request_path == "/ttyd-event":
            self.handle_ttyd_event_request()
            return
        if request_path == "/open-working-directory":
            self.handle_open_working_directory_request()
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

    def handle_open_working_directory_request(self) -> None:
        """Open the registered local working directory without a Streamlit rerun."""
        parsed_url = urllib.parse.urlparse(self.path)
        token = urllib.parse.parse_qs(parsed_url.query).get("token", [""])[0]
        entry = TTYD_CLEANUP_REGISTRY.get(token, {})
        if not token or entry.get("ssh_host"):
            self.send_response(409)
            self.end_headers()
            return
        directory = (
            str(entry.get("cwd") or entry.get("working_dir") or os.getcwd()).strip()
            or os.getcwd()
        )
        result = run_cleanup_bash_command(build_open_directory_command(directory), 10)
        self.send_response(204 if result.returncode == 0 else 500)
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
            "working_dir": footer_working_directory(),
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
    ttyd_event_request_url = (
        f"http://{hhs_ui.TTYD_HOST}:{port}/ttyd-event?token={token}"
    )
    render_script_html(
        f"""
        <script>
          (() => {{
            const cleanupUrl = {cleanup_url!r};
            const ttydEventUrl = {ttyd_event_request_url!r};
            const parentWindow = window.parent;
            parentWindow.__hhsTtydEventUrl = ttydEventUrl;
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
            if (parentWindow.__hhsTtydTerminalContextCacheHandler) {{
              parentWindow.removeEventListener(
                "message",
                parentWindow.__hhsTtydTerminalContextCacheHandler
              );
            }}
            parentWindow.__hhsTtydTerminalContextCacheHandler = (event) => {{
              const data = event.data || {{}};
              if (
                data.type === "hhs-ttyd-event" &&
                data.event &&
                data.event.type === "terminal-context"
              ) {{
                parentWindow.__hhsTtydTerminalContextEvent = data.event;
              }}
            }};
            parentWindow.addEventListener(
              "message",
              parentWindow.__hhsTtydTerminalContextCacheHandler
            );
            if (!parentWindow.__hhsTtydEventListenerInstalled) {{
              parentWindow.__hhsTtydEventListenerInstalled = true;
              parentWindow.addEventListener("message", (event) => {{
                const data = event.data || {{}};
                if (data.type !== "hhs-ttyd-event" || !data.event) {{
                  return;
                }}
                if (data.event.type === "terminal-context") {{
                  parentWindow.__hhsTtydTerminalContextEvent = data.event;
                  try {{
                    fetch(parentWindow.__hhsTtydEventUrl || ttydEventUrl, {{
                      method: "POST",
                      headers: {{"Content-Type": "application/json"}},
                      body: JSON.stringify(data.event),
                      keepalive: true,
                    }}).catch(() => {{}});
                  }} catch (_error) {{}}
                  return;
                }}
                if (data.event.type !== "cwd") {{
                  return;
                }}
                const cwd = String(data.event.cwd || "").trim();
                if (!cwd) {{
                  return;
                }}
                const link = parentWindow.document.querySelector(".hhs-footer-working-dir-link");
                const node = parentWindow.document.querySelector(".hhs-footer-working-dir-value");
                if (node) {{
                  node.textContent = cwd;
                }}
                if (link) {{
                  link.dataset.hhsWorkingDir = cwd;
                  link.title = `Working dir: ${{cwd}}`;
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
    """Initialize ttyd terminal working directory state."""
    st.session_state.setdefault(hhs_ui.TERMINAL_CWD_KEY, footer_working_directory())


def show_terminal_ready_status() -> None:
    """Queue the terminal ready status once the ttyd terminal is rendered."""
    if not bool(st.session_state.get(hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY, False)):
        push_floating_status("HomeSetup terminal is ready.", "info")
        st.session_state[hhs_ui.TERMINAL_READY_STATUS_SHOWN_KEY] = True


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


def render_ai_chat_message(
    role: str, content: str, username: str, ollama_model: str, context_size: str
) -> None:
    """Render an AI chat message with a colored prefix and Markdown content."""
    separator = "\n" if role in ("assistant", "system") else " "
    st.markdown(
        f"{format_ai_chat_prefix(role, username, ollama_model, context_size)}{separator}{prepare_ai_chat_content(role, content)}",
        unsafe_allow_html=True,
    )


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
            remember_host_switch_view_state()
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
    reset_search_directory_to_home()
    schedule_ollama_service_availability_refresh()
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
    queue_search_directory_home_reset()
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
    remember_host_switch_view_state()
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
    remember_host_switch_view_state()
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
    reconnect_state = consume_host_switch_view_state()
    was_terminal_active = terminal_document_view_is_active()
    render_ttyd_terminal_frame_cleanup_script()
    stop_ttyd_session()
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
        show_preloader_event=True,
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
    if not reconnect_state:
        reconnect_state = consume_host_switch_view_state()
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
        reset_search_directory_to_home()
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
    disconnect_view_state = consume_host_switch_view_state()
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
    reset_search_directory_to_home()
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
    render_ttyd_terminal_frame_cleanup_script()
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
        show_preloader_event=True,
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
    """Queue dismissal of the currently mounted Streamlit dialog."""
    st.session_state["_hhs_dialog_dismiss_requested"] = True


def render_ssh_connection_dialog() -> bool:
    """Render the SSH connection result dialog when a connection attempt completes."""
    title = str(st.session_state.get("ssh_connection_dialog_title", "")).strip()
    if not title:
        return False
    set_overlay(False)
    render_command_preloader_events()
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
        encoding="utf-8",
        errors="replace",
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
    return f"{BACKGROUND_JOB_STATE_KEY_PREFIX}{safe_background_job_name(job_name)}"


def safe_background_job_name(job_name: str) -> str:
    """Return a filesystem-safe background command job name."""
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", job_name.strip())
    return safe_name or "job"


def background_job_output_path(job_name: str, stream_name: str) -> Path:
    """Return the deterministic cache path for one background job output stream."""
    safe_stream_name = re.sub(r"[^A-Za-z0-9_-]+", "_", stream_name.strip())
    return (
        ui_disposable_files_dir()
        / f"{safe_background_job_name(job_name)}-{safe_stream_name or 'output'}.log"
    )


def background_job_state(job_name: str) -> dict[str, object] | None:
    """Return the stored background job state for a named job."""
    value = st.session_state.get(background_job_state_key(job_name))
    return value if isinstance(value, dict) else None


def background_job_session_items() -> list[tuple[str, dict[str, object]]]:
    """Return all stored background job states for this Streamlit session."""
    jobs: list[tuple[str, dict[str, object]]] = []
    for state_key in list(st.session_state):
        if not str(state_key).startswith(BACKGROUND_JOB_STATE_KEY_PREFIX):
            continue
        value = st.session_state.get(state_key)
        if isinstance(value, dict):
            jobs.append((str(state_key), value))
    return jobs


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
    finish_background_job_preloader(job, "cancelled")
    process = background_job_process(job)
    if process is not None:
        stop_process(process)
    st.session_state.pop(job_key, None)
    cleanup_background_job_files(job)


def stop_background_job_by_preloader_token(preloader_token: str) -> bool:
    """Stop the background job that owns a command-preloader token."""
    clean_token = preloader_token.strip()
    if not clean_token:
        return False
    for state_key, job in background_job_session_items():
        if str(job.get("preloader_token", "")).strip() != clean_token:
            continue
        finish_background_job_preloader(job, "cancelled")
        process = background_job_process(job)
        if process is not None:
            stop_process(process)
        st.session_state.pop(state_key, None)
        cleanup_background_job_files(job)
        return True
    return False


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
        finish_background_job_preloader(job, "cancelled")
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


def background_job_preloader_token(job_name: str) -> str:
    """Return a unique command preloader token for one background job."""
    return f"{job_name}:{secrets.token_hex(8)}"


def finish_background_job_preloader(
    job: dict[str, object], status: str = "success"
) -> None:
    """Emit the finish event for one background job command preloader."""
    preloader_token = str(job.get("preloader_token", "")).strip()
    if not preloader_token or bool(job.get("preloader_finished")):
        return
    emit_command_preloader_finish(preloader_token, status)
    job["preloader_finished"] = True


def dismiss_background_job_preloader(
    job_name: str, job: dict[str, object], status: str = "error"
) -> None:
    """Dismiss one background job preloader without consuming its command result."""
    finish_background_job_preloader(job, status)
    st.session_state[background_job_state_key(job_name)] = job
    render_command_preloader_events()


def start_background_bash_command(
    job_name: str,
    command: str,
    description: str,
    timeout_seconds: int,
    force_local: bool = False,
    metadata: dict[str, object] | None = None,
    show_preloader_event: bool = False,
    preloader_token: str | None = None,
) -> bool:
    """Start a Bash command in the background and store its process state."""
    if background_job_is_running(job_name):
        return False

    stdout_path = str(background_job_output_path(job_name, "stdout"))
    stderr_path = str(background_job_output_path(job_name, "stderr"))

    remote_host = command_remote_host(force_local=force_local)
    effective_timeout = effective_command_timeout_seconds(
        timeout_seconds, force_local=force_local
    )
    command_to_run = effective_bash_command(command, force_local=force_local)
    command_preloader_token = ""
    if show_preloader_event:
        command_preloader_token = (
            preloader_token.strip()
            if preloader_token and preloader_token.strip()
            else background_job_preloader_token(job_name)
        )
        emit_command_preloader_start(
            command_preloader_token,
            description,
            int(effective_timeout),
        )
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
        "preloader_token": command_preloader_token,
    }
    return True


def read_background_job_file(job: dict[str, object], key: str) -> str:
    """Return the captured output text for one background job output file."""
    raw_path = str(job.get(key, ""))
    if not raw_path:
        return ""
    file_path = Path(raw_path)
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def cleanup_background_job_files(job: dict[str, object]) -> None:
    """Remove disposable output files owned by a background command job."""
    for key in ("stdout_path", "stderr_path"):
        raw_path = str(job.get(key, ""))
        if not raw_path:
            continue
        file_path = Path(raw_path)
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            continue


def background_job_completion_needs_app_rerun(
    state_key: str, job: dict[str, object]
) -> bool:
    """Return whether one completed background job should trigger one app rerun."""
    process = background_job_process(job)
    if process is None:
        return False
    if process.poll() is None and background_job_has_timed_out(job):
        stop_process(process)
    if process.poll() is None or bool(job.get("completion_rerun_queued")):
        return False
    metadata = job.get("metadata")
    if isinstance(metadata, dict) and metadata.get("completion_rerun") is False:
        job["completion_rerun_queued"] = True
        st.session_state[state_key] = job
        return False
    job["completion_rerun_queued"] = True
    st.session_state[state_key] = job
    return True


def background_jobs_completion_needs_app_rerun() -> bool:
    """Return whether any completed background job should trigger one app rerun."""
    return any(
        background_job_completion_needs_app_rerun(state_key, job)
        for state_key, job in background_job_session_items()
    )


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
    finish_background_job_preloader(
        job,
        "success" if result.returncode == 0 else "error",
    )
    st.session_state.pop(job_key, None)
    cleanup_background_job_files(job)
    metadata = job.get("metadata")
    return result, metadata if isinstance(metadata, dict) else {}


def render_background_job_status(job_name: str, message: str = "") -> None:
    """Render a compact status line for a background command."""
    job = background_job_state(job_name)
    if job:
        process = background_job_process(job)
        if (
            process is not None
            and process.poll() is None
            and background_job_has_timed_out(job)
        ):
            stop_process(process)
            dismiss_background_job_preloader(job_name, job, "error")
            return
        if process is not None and process.poll() is not None:
            dismiss_background_job_preloader(
                job_name,
                job,
                "success" if int(process.returncode or 0) == 0 else "error",
            )
            return
        if background_job_is_running(job_name):
            description = (
                message.strip() or str(job.get("description", "Command")).strip()
            )
            try:
                started_at = float(job.get("started_at", 0.0) or 0.0)
            except (TypeError, ValueError):
                started_at = 0.0
            render_command_loader(
                description or "Command running...",
                started_at or None,
                int(background_job_timeout_seconds(job) or command_timeout_seconds()),
                str(job.get("preloader_token", "")),
            )
    render_command_preloader_events()


def render_background_job_status_if_blocking(
    job_name: str, has_visible_content: bool, message: str = ""
) -> None:
    """Render a background job loader only when the page is waiting for content."""
    if has_visible_content:
        return
    render_background_job_status(job_name, message)


@st.fragment(run_every="2s")
def render_background_job_polling_fragment() -> None:
    """Poll all background jobs from one always-mounted fragment."""
    update_ollama_service_availability_refresh()
    if background_jobs_completion_needs_app_rerun():
        st.rerun()


def load_ui_cache() -> dict[str, dict[str, object]]:
    """Load the UI cache file and prune expired entries without writing on reads."""
    global UI_CACHE_MEMORY, UI_CACHE_MEMORY_MTIME
    cache_mtime = ui_cache_mtime()
    if UI_CACHE_MEMORY_MTIME == cache_mtime:
        UI_CACHE_MEMORY = prune_ui_cache_entries(UI_CACHE_MEMORY)
        return dict(UI_CACHE_MEMORY)
    cache_file = ui_cache_source_file()
    if cache_file is None:
        UI_CACHE_MEMORY = {}
        UI_CACHE_MEMORY_MTIME = 0.0
        return {}
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
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


def ui_cache_files() -> tuple[Path, ...]:
    """Return current and legacy UI cache file paths."""
    return (hhs_ui.UI_CACHE_FILE, *legacy_ui_cache_files())


def legacy_ui_cache_files() -> tuple[Path, ...]:
    """Return legacy hidden UI cache file paths."""
    return (hhs_ui.HHS_CACHE_DIR / ".streamlit-ui-cache",)


def unlink_legacy_ui_cache_files() -> None:
    """Remove legacy hidden UI cache files after writing the visible cache file."""
    for cache_file in legacy_ui_cache_files():
        try:
            cache_file.unlink(missing_ok=True)
        except OSError:
            continue


def ui_cache_source_file() -> Path | None:
    """Return the first existing current or legacy UI cache file path."""
    for cache_file in ui_cache_files():
        if cache_file.exists():
            return cache_file
    return None


def ui_cache_mtime() -> float:
    """Return the UI cache file modification time used for memory cache coherency."""
    cache_file = ui_cache_source_file()
    if cache_file is None:
        return 0.0
    try:
        return cache_file.stat().st_mtime
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
        unlink_legacy_ui_cache_files()
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
    clear_firebase_aliases_cache()
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
    stop_path_picker_listing_jobs()
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
    stop_path_picker_listing_jobs()
    for cache_tag in HOST_SWITCH_CACHE_TAGS:
        cache_delete_tag(cache_tag)
    clear_render_caches()
    for state_key in HOST_SWITCH_STATE_KEYS:
        st.session_state.pop(state_key, None)
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABLE_KEY] = False
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_LOADED_KEY] = False
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_CONTEXT_KEY] = ""
    st.session_state[hhs_ui_constants.AI_SERVICE_AVAILABILITY_REFRESHED_AT_KEY] = 0.0
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
    completion_rerun: bool = True,
) -> bool:
    """Start a background command that will be written to command-result cache."""
    metadata = {
        **background_command_metadata(command, cache_tag, force_local=force_local),
        "ttl_seconds": ttl_seconds,
        "completion_rerun": completion_rerun,
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
    render_background_job_status_if_blocking(job_name, result is not None)
    if command_running and not fresh_cache and result is None:
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


def monitor_metric_job_name(metric: str) -> str:
    """Return the background job name for a process metric chart."""
    return MONITOR_MEM_JOB if metric == "MEM" else MONITOR_CPU_JOB


def monitor_metric_command(metric: str) -> str:
    """Return the command used to load one process monitor metric."""
    return build_process_monitor_command(
        metric, normalized_monitor_process_top_n(metric)
    )


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


def build_hhs_disk_usage_command(directory: str, top_n: int = 10) -> str:
    """Build the Bash command used to run the __hhs_du HomeSetup function."""
    hhs_home = homesetup_home()
    safe_top_n = max(
        hhs_ui_constants.MIN_TOP_N,
        min(int(top_n), hhs_ui_constants.MAX_TOP_N),
    )
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


def run_ssh_tunnels(host: str) -> subprocess.CompletedProcess[str]:
    """Run the SSH tunnel listing command and return the completed process."""
    return run_bash_command(
        build_ssh_tunnels_command(host),
        "Loading SSH tunnels...",
        cache_tag="ssh",
    )


def run_open_working_directory(directory: str) -> subprocess.CompletedProcess[str]:
    """Open a working directory in the operating system file explorer."""
    return run_bash_command(
        build_open_directory_command(directory),
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


def run_hhs_logs(
    log_file: str,
    tail_lines: int = hhs_ui_constants.DEFAULT_LOG_TAIL_LINES,
    log_level: str = "ALL_LEVELS",
) -> subprocess.CompletedProcess[str]:
    """Run the __hhs logs command and return the completed process."""
    return run_bash_command(
        build_hhs_logs_command(log_file, tail_lines, log_level),
        "Loading logs...",
        cache_tag="monitor_logs",
    )


def submit_ai_chat_prompt(
    prompt: str,
    ollama_model: str = "",
    context_size: str = "",
) -> bool:
    """Submit a prompt through the same background Ask AI job used by chat."""
    clean_prompt = prompt.strip()
    if not clean_prompt:
        push_floating_status("Ask AI prompt is empty.", "warn")
        return False
    if background_job_is_running(AI_ASK_JOB):
        push_floating_status("Ollama is still generating a response.", "warn")
        return False
    st.session_state.setdefault("ai_chat_messages", [])
    if not isinstance(st.session_state["ai_chat_messages"], list):
        st.session_state["ai_chat_messages"] = []
    st.session_state["ai_chat_messages"].append(
        {"role": "user", "content": clean_prompt}
    )
    save_ui_state()
    ask_started_at = time.perf_counter()
    started = start_background_bash_command(
        AI_ASK_JOB,
        build_hhs_ask_command(clean_prompt),
        "Asking AI...",
        timeout_seconds=hhs_ask_timeout_seconds(),
        metadata={
            "prompt": clean_prompt,
            "ollama_model": ollama_model,
            "context_size": context_size,
            "started_at": ask_started_at,
        },
        show_preloader_event=True,
    )
    if not started:
        push_floating_status("Ollama is still generating a response.", "warn")
        return False
    return True


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


def styled_ssh_tunnel_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return SSH tunnel rows with styled Status cells."""
    dataframe = pd.DataFrame(display_table_rows(display_ssh_tunnel_rows(rows)))
    styler = dataframe.style
    if "Status" in dataframe:
        styler = styler.map(ssh_tunnel_status_cell_style, subset=["Status"])
    return styler


def render_ssh_tunnel_status_loader(job_names: tuple[str, ...]) -> None:
    """Render one polling loader while SSH tunnel status jobs are running."""
    if not any(background_job_is_running(job_name) for job_name in job_names):
        return
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


def hhs_settings_table_key() -> str:
    """Return the HHS Settings dataframe key for the current selection generation."""
    reset_counter = st.session_state.setdefault(
        hhs_ui_constants.HHS_SETTINGS_TABLE_RESET_COUNTER_KEY, 0
    )
    if not isinstance(reset_counter, int):
        reset_counter = 0
        st.session_state[
            hhs_ui_constants.HHS_SETTINGS_TABLE_RESET_COUNTER_KEY
        ] = reset_counter
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
) -> bool:
    """Start one user-triggered action command as an EventBus-backed background job."""
    started = start_background_bash_command(
        job_name,
        command,
        description,
        timeout_seconds,
        force_local=force_local,
        metadata=metadata,
        show_preloader_event=True,
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


def queue_hhs_setup_action(
    command: str,
    description: str,
    metadata: dict[str, object],
) -> bool:
    """Queue a HomeSetup setup plug-in mutation for background execution."""
    st.session_state["hhs_setup_action_execute_pending"] = {
        **metadata,
        "command": command,
        "description": description,
    }
    save_ui_state()
    return True


def start_pending_hhs_setup_action() -> None:
    """Start a queued HomeSetup setup action background job, when present."""
    pending = st.session_state.pop("hhs_setup_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        HHS_SETUP_ACTION_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another setup action is already running.",
    )
    if not started:
        st.session_state["hhs_setup_action_execute_pending"] = pending


def complete_hhs_setup_action_job() -> None:
    """Complete a HomeSetup setup action and refresh setup settings."""
    completed = background_job_result(HHS_SETUP_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    if result.returncode == 0:
        cache_delete_tag("hhs_setup")
        st.session_state.pop("_hhs_setup_loaded_token", None)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        fallback = str(metadata.get("success_fallback", "Setup updated."))
        push_floating_status(status_message or fallback, "info")
    else:
        fallback = str(metadata.get("error_fallback", "Setup update failed."))
        push_floating_status(status_message or fallback, "error")
    save_ui_state()


def execute_pending_hhs_setup_action() -> None:
    """Start or complete the current HomeSetup setup action."""
    start_pending_hhs_setup_action()
    complete_hhs_setup_action_job()


def queue_hhs_settings_action(
    command: str,
    description: str,
    metadata: dict[str, object],
) -> bool:
    """Queue a HomeSetup Settings plug-in mutation for background execution."""
    st.session_state["hhs_settings_action_execute_pending"] = {
        **metadata,
        "command": command,
        "description": description,
    }
    save_ui_state()
    return True


def start_pending_hhs_settings_action() -> None:
    """Start a queued HomeSetup Settings action background job, when present."""
    pending = st.session_state.pop("hhs_settings_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        HHS_SETTINGS_ACTION_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another Settings action is already running.",
    )
    if not started:
        st.session_state["hhs_settings_action_execute_pending"] = pending


def complete_hhs_settings_action_job() -> None:
    """Complete a HomeSetup Settings action and refresh Settings data."""
    completed = background_job_result(HHS_SETTINGS_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    if result.returncode == 0:
        cache_delete_tag("hhs_settings")
        reset_hhs_settings_table_selection()
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        fallback = str(metadata.get("success_fallback", "Settings updated."))
        push_floating_status(status_message or fallback, "info")
    else:
        fallback = str(metadata.get("error_fallback", "Settings update failed."))
        push_floating_status(status_message or fallback, "error")
    save_ui_state()


def execute_pending_hhs_settings_action() -> None:
    """Start or complete the current HomeSetup Settings action."""
    start_pending_hhs_settings_action()
    complete_hhs_settings_action_job()


def queue_hhs_starship_action(
    command: str,
    description: str,
    metadata: dict[str, object],
) -> bool:
    """Queue a HomeSetup Starship plug-in mutation for background execution."""
    st.session_state["hhs_starship_action_execute_pending"] = {
        **metadata,
        "command": command,
        "description": description,
    }
    save_ui_state()
    return True


def start_pending_hhs_starship_action() -> None:
    """Start a queued HomeSetup Starship action background job, when present."""
    pending = st.session_state.pop("hhs_starship_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        HHS_STARSHIP_ACTION_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another Starship action is already running.",
    )
    if not started:
        st.session_state["hhs_starship_action_execute_pending"] = pending


def complete_hhs_starship_action_job() -> None:
    """Complete a HomeSetup Starship action and refresh Starship info."""
    completed = background_job_result(HHS_STARSHIP_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    if result.returncode == 0:
        cache_delete_tag("hhs_starship")
        if metadata.get("operation") == "preset":
            preset = str(metadata.get("preset", "")).strip()
            if preset:
                st.session_state[
                    hhs_ui_constants.HHS_STARSHIP_CURRENT_PRESET_KEY
                ] = preset
        if metadata.get("operation") == "save_config":
            st.session_state["hhs_starship_config_editing"] = False
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        fallback = str(metadata.get("success_fallback", "Starship updated."))
        push_floating_status(status_message or fallback, "info")
    else:
        fallback = str(metadata.get("error_fallback", "Starship update failed."))
        push_floating_status(status_message or fallback, "error")
    save_ui_state()


def execute_pending_hhs_starship_action() -> None:
    """Start or complete the current HomeSetup Starship action."""
    start_pending_hhs_starship_action()
    complete_hhs_starship_action_job()


def queue_hhs_firebase_action(
    command: str,
    description: str,
    metadata: dict[str, object],
) -> bool:
    """Queue a HomeSetup Firebase config mutation for background execution."""
    st.session_state["hhs_firebase_action_execute_pending"] = {
        **metadata,
        "command": command,
        "description": description,
    }
    save_ui_state()
    return True


def start_pending_hhs_firebase_action() -> None:
    """Start a queued HomeSetup Firebase action background job, when present."""
    pending = st.session_state.pop("hhs_firebase_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        HHS_FIREBASE_ACTION_JOB,
        command,
        description,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        pending,
        "Another Firebase action is already running.",
    )
    if not started:
        st.session_state["hhs_firebase_action_execute_pending"] = pending


def complete_hhs_firebase_action_job() -> None:
    """Complete a HomeSetup Firebase action and refresh config data."""
    completed = background_job_result(HHS_FIREBASE_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    if result.returncode == 0:
        cache_delete_tag("hhs_firebase")
        clear_firebase_aliases_cache()
        st.session_state.pop("_hhs_firebase_loaded_token", None)
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        fallback = str(metadata.get("success_fallback", "Firebase updated."))
        push_floating_status(status_message or fallback, "info")
    else:
        fallback = str(metadata.get("error_fallback", "Firebase update failed."))
        push_floating_status(status_message or fallback, "error")
    save_ui_state()


def execute_pending_hhs_firebase_action() -> None:
    """Start or complete the current HomeSetup Firebase action."""
    start_pending_hhs_firebase_action()
    complete_hhs_firebase_action_job()


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


def scroll_to_env_value_editor(editor_key: str) -> None:
    """Scroll the browser viewport to the selected environment value editor."""
    selector = f'div[class*="st-key-{editor_key}"] textarea'
    render_script_html(
        f"""
        <script>
          (() => {{
            const editor_selector = {selector!r};
            const scroll_to_editor = () => {{
              const target = window.parent.document.querySelector(editor_selector);
              if (target) {{
                target.scrollIntoView({{ behavior: "smooth", block: "center" }});
                target.focus({{ preventScroll: true }});
              }}
            }};
            window.setTimeout(scroll_to_editor, 75);
          }})();
        </script>
        """,
        height=hhs_ui.ENV_VALUE_EDITOR_SCROLL_HELPER_HEIGHT,
    )


def scroll_to_ai_model_actions(anchor_id: str) -> None:
    """Scroll the browser viewport to the selected AI model action buttons."""
    render_script_html(
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

def render_history_stats_chart() -> None:
    """Render command history stats using __hhs_hist_stats."""
    st.session_state["history_stats_top_n"] = normalized_history_stats_top_n(
        st.session_state.get("history_stats_top_n")
    )
    render_chart_controls(
        "history_stats_controls",
        top_n_key="history_stats_top_n",
        top_n_on_change=save_ui_state,
        refresh_key="history_stats_refresh_button",
        refresh_on_click=refresh_history_stats_chart,
    )
    top_n = normalized_history_stats_top_n(st.session_state.get("history_stats_top_n"))
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
    plot_chart(
        rows,
        "HBars",
        f"Top {int(top_n)} most used commands",
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
    render_chart_controls(
        "monitor_disk_controls",
        top_n_key="monitor_disk_top_n_input",
        top_n_on_change=handle_monitor_disk_top_n_change,
        has_input=True,
        input_key="monitor_disk_directory",
        input_label="Directory:",
        input_on_change=save_ui_state,
        refresh_key="monitor_disk_apply_button",
        refresh_on_click=apply_monitor_disk_controls,
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
    display_directory = monitor_disk_display_directory(
        selected_directory, result.stdout
    )
    for row in rows:
        row["Label"] = relative_disk_usage_path(str(row["Path"]), display_directory)
    if not rows:
        st.caption("No disk usage entries found.")
        return
    plot_chart(
        rows,
        "HBars",
        (
            f"Top {applied_top_n} disk usage at "
            f"<code>{html.escape(display_directory)}</code>"
        ),
        has_input=True,
        input_label="Directory:",
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
        title_is_html=True,
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
    refresh_clicked = render_chart_controls(
        f"monitor_{metric.lower()}_controls",
        top_n_key=top_n_input_key,
        top_n_on_change=handle_monitor_process_top_n_change,
        top_n_args=(metric,),
        refresh_key=f"monitor_{metric.lower()}_refresh_button",
        refresh_on_click=apply_monitor_process_controls,
        refresh_args=(metric,),
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
    plot_chart(
        rows,
        "HBars",
        f"Top {applied_top_n} {title} processes",
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
    execute_pending_monitor_process_action()
    render_background_job_status(MONITOR_PROCESS_ACTION_JOB)
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
    if result is None and not fresh_cache:
        result = complete_monitor_process_list_refresh()
    if (
        result is None
        and not fresh_cache
        and not background_job_is_running(MONITOR_PROCESS_LIST_JOB)
    ):
        start_monitor_process_list_refresh()
    process_list_running = background_job_is_running(MONITOR_PROCESS_LIST_JOB)
    render_background_job_status(MONITOR_PROCESS_LIST_JOB)
    if result is None:
        result = complete_monitor_process_list_refresh()
        process_list_running = background_job_is_running(MONITOR_PROCESS_LIST_JOB)
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
    normalize_monitor_log_tail_lines_state()

    def render_tail_lines_spinner() -> int:
        """Render the monitor log bottom-line spinner and return its value."""
        selected_tail_lines = render_standard_number_spinner(
            "Bot N:",
            min_value=hhs_ui_constants.MIN_LOG_TAIL_LINES,
            max_value=hhs_ui_constants.MAX_LOG_TAIL_LINES,
            step=hhs_ui_constants.LOG_TAIL_LINES_STEP,
            key="monitor_log_tail_lines",
            label_visibility="collapsed",
            on_change=handle_monitor_log_tail_lines_change,
            width=150,
        )
        return normalized_monitor_log_tail_lines(selected_tail_lines)

    def render_log_controls() -> tuple[str, str, int, bool, str, str]:
        """Render log controls and return the selected log viewing options."""
        with st.container(key="monitor_log_controls"):
            (
                label_col,
                input_col,
                level_label_col,
                level_col,
                tail_lines_label_col,
                tail_lines_col,
                tail_col,
                clear_col,
            ) = st.columns(
                [0.32, 1.0, 0.36, 0.85, 0.46, 0.34, 0.16, 0.16],
                vertical_alignment="center",
            )
            with label_col:
                st.markdown(
                    '<span class="hhs-inline-form-label">File:</span>',
                    unsafe_allow_html=True,
                )
            with input_col:
                selected_log_value = st.selectbox(
                    "File:",
                    options=log_files,
                    key="monitor_log_file",
                    label_visibility="collapsed",
                    on_change=save_ui_state,
                )
            with level_label_col:
                st.markdown(
                    '<span class="hhs-inline-form-label">Level:</span>',
                    unsafe_allow_html=True,
                )
            with level_col:
                selected_level_value = st.selectbox(
                    "Level:",
                    options=hhs_ui.LOG_LEVELS,
                    key="monitor_log_level",
                    format_func=monitor_log_level_label,
                    label_visibility="collapsed",
                    on_change=save_ui_state,
                )
            with tail_lines_label_col:
                st.markdown(
                    '<span class="hhs-inline-form-label">Bot N:</span>',
                    unsafe_allow_html=True,
                )
            with tail_lines_col:
                selected_tail_lines_value = render_tail_lines_spinner()
            with tail_col:
                tail_enabled_value = bool(
                    st.session_state.get("monitor_logs_tail", True)
                )
                tail_button_state = "selected" if tail_enabled_value else "idle"
                st.button(
                    "",
                    key=f"monitor_logs_tail_button_{tail_button_state}",
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
                    "",
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
                placeholder="Type log filter text",
            )
        return (
            str(selected_log_value),
            str(selected_level_value),
            normalized_monitor_log_tail_lines(selected_tail_lines_value),
            bool(tail_enabled_value),
            str(selected_filter_value),
            str(text_filter_value),
        )

    (
        selected_log,
        selected_level,
        tail_lines,
        tail_enabled,
        log_filter,
        log_text_filter,
    ) = render_table_controls_panel(render_log_controls)
    render_persisted_expander_state_script(
        ".st-key-monitor_log_controls",
        "hhs.monitor.logs.controls.expanded",
    )
    log_file_path, log_environment = hhs_log_file_info(selected_log)
    log_display_path = display_path_value(log_file_path, log_environment)
    render_openable_config_path(log_display_path, log_file_path)
    if tail_enabled:
        render_monitor_logs_tail(
            selected_log, selected_level, tail_lines, log_filter, log_text_filter
        )
    else:
        render_monitor_logs_once(
            selected_log, selected_level, tail_lines, log_filter, log_text_filter
        )


@st.fragment(run_every="5s")
def render_monitor_logs_tail(
    selected_log: str,
    selected_level: str,
    tail_lines: int,
    log_filter: str,
    log_text_filter: str,
) -> None:
    """Render a tail-like log pane that refreshes only while LOGS is active."""
    if not bool(st.session_state.get("monitor_logs_tail", True)):
        return
    render_monitor_logs_once(
        selected_log, selected_level, tail_lines, log_filter, log_text_filter
    )


def render_monitor_logs_once(
    selected_log: str,
    selected_level: str,
    tail_lines: int,
    log_filter: str = "All",
    log_text_filter: str = "",
) -> None:
    """Render the selected log once without automatic refresh."""
    if False:
        run_hhs_logs(selected_log, tail_lines, selected_level)
    result = render_cached_command_result(
        build_hhs_logs_command(selected_log, tail_lines, selected_level),
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


def hhs_view_label(hhs_view: str) -> str:
    """Return the display label for a HomeSetup application view key."""
    return hhs_ui.HHS_VIEW_LABELS.get(hhs_view, hhs_view)


def hhs_setup_setting_key(setting_name: str) -> str:
    """Return the Session State key for a setup setting checkbox."""
    return f"hhs_setup_setting_{setting_name}"


def normalized_hhs_setup_settings(settings: dict[str, bool]) -> dict[str, bool]:
    """Return setup settings with every known option present."""
    return {name: bool(settings.get(name, False)) for name in HHS_SETUP_SETTINGS}


def hhs_setup_settings_token(settings: dict[str, bool]) -> str:
    """Return a stable token for the loaded setup settings."""
    normalized_settings = normalized_hhs_setup_settings(settings)
    return json.dumps(
        [normalized_settings[name] for name in HHS_SETUP_SETTINGS],
        separators=(",", ":"),
    )


def sync_hhs_setup_form_state(settings: dict[str, bool]) -> None:
    """Initialize setup checkbox state when the loaded settings change."""
    normalized_settings = normalized_hhs_setup_settings(settings)
    token = hhs_setup_settings_token(normalized_settings)
    if st.session_state.get("_hhs_setup_loaded_token") == token:
        return
    st.session_state["_hhs_setup_loaded_token"] = token
    st.session_state["_hhs_setup_original_settings"] = normalized_settings
    for setting_name, enabled in normalized_settings.items():
        st.session_state[hhs_setup_setting_key(setting_name)] = enabled


def apply_pending_hhs_setup_form_revert() -> None:
    """Apply a queued setup form revert before rendering checkbox widgets."""
    if not st.session_state.pop("_hhs_setup_revert_pending", False):
        return
    original_settings = st.session_state.get("_hhs_setup_original_settings", {})
    if not isinstance(original_settings, dict):
        return
    for setting_name in HHS_SETUP_SETTINGS:
        st.session_state[hhs_setup_setting_key(setting_name)] = bool(
            original_settings.get(setting_name, False)
        )


def selected_hhs_setup_settings() -> dict[str, bool]:
    """Return setup settings selected in the form."""
    return {
        setting_name: bool(st.session_state.get(hhs_setup_setting_key(setting_name)))
        for setting_name in HHS_SETUP_SETTINGS
    }


def request_hhs_setup_apply() -> None:
    """Queue applying the selected setup settings."""
    queue_hhs_setup_action(
        build_hhs_setup_apply_command(selected_hhs_setup_settings()),
        "Applying HomeSetup settings",
        {
            "operation": "apply",
            "success_fallback": "HomeSetup settings applied.",
            "error_fallback": "Unable to apply HomeSetup settings.",
        },
    )


def request_hhs_setup_revert() -> None:
    """Queue reverting the setup form to the loaded settings."""
    st.session_state["_hhs_setup_revert_pending"] = True
    save_ui_state()


def request_hhs_setup_restore() -> None:
    """Queue restoring HomeSetup setup defaults."""
    queue_hhs_setup_action(
        build_hhs_setup_restore_command(),
        "Restoring HomeSetup settings",
        {
            "operation": "restore",
            "success_fallback": "HomeSetup settings restored.",
            "error_fallback": "Unable to restore HomeSetup settings.",
        },
    )


def render_hhs_setup_title() -> None:
    """Render the HomeSetup setup page title."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> Initialization Setup</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )

def render_hhs_setup_settings_table(action_running: bool) -> None:
    """Render the setup settings table."""
    settings = selected_hhs_setup_settings()
    render_markdown_table(
        "Mark the preferred startup settings",
        list(HHS_SETUP_SETTINGS),
        list(HHS_SETUP_SETTINGS),
        [settings[name] for name in HHS_SETUP_SETTINGS],
        "hhs_setup_settings",
        [hhs_setup_setting_key(name) for name in HHS_SETUP_SETTINGS],
        disabled=action_running,
    )


def render_hhs_setup_panel() -> None:
    """Render the HomeSetup setup settings panel."""
    execute_pending_hhs_setup_action()
    render_background_job_status(HHS_SETUP_ACTION_JOB)
    render_hhs_setup_title()
    result = render_cached_command_result(
        build_hhs_setup_settings_command(),
        "Loading setup settings",
        "hhs_setup",
        hhs_ui.UI_CACHE_DEFAULT_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load setup settings.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load setup settings."
            )
        )
        return

    sync_hhs_setup_form_state(parse_hhs_setup_settings(result.stdout))
    apply_pending_hhs_setup_form_revert()
    action_running = background_job_is_running(HHS_SETUP_ACTION_JOB)
    render_hhs_setup_settings_table(action_running)
    (
        left_column,
        ok_column,
        revert_column,
        restore_column,
        right_column,
    ) = st.columns(
        [1.0, 0.42, 0.42, 0.48, 1.0],
        gap="small",
        vertical_alignment="center",
    )
    with left_column:
        st.empty()
    with ok_column:
        ok_clicked = st.button(
            " Apply",
            key="hhs_setup_apply_button",
            help="Apply",
            disabled=action_running,
            width="stretch",
        )
    with revert_column:
        revert_clicked = st.button(
            " Cancel",
            key="hhs_setup_cancel_button",
            help="Cancel",
            disabled=action_running,
            width="stretch",
        )
    with restore_column:
        restore_clicked = st.button(
            " Restore",
            key="hhs_setup_restore_button",
            help="Restore",
            disabled=action_running,
            width="stretch",
        )
    with right_column:
        st.empty()

    if ok_clicked:
        request_hhs_setup_apply()
        st.rerun()
    elif revert_clicked:
        request_hhs_setup_revert()
        st.rerun()
    elif restore_clicked:
        request_hhs_setup_restore()
        st.rerun()


def request_hhs_settings_add() -> None:
    """Queue adding or updating a system setting override."""
    setting = str(st.session_state.get("hhs_settings_add_name", "")).strip()
    value = str(st.session_state.get("hhs_settings_add_value", ""))
    if not setting:
        push_floating_status("Select or type a setting before adding it.", "warn")
        return
    queue_hhs_settings_action(
        build_hhs_settings_add_command(setting, value),
        f"Saving setting: {setting}",
        {
            "operation": "set",
            "setting": setting,
            "success_fallback": f"Setting saved: {setting}",
            "error_fallback": f"Unable to save setting: {setting}",
        },
    )


def request_hhs_settings_delete(settings: str | list[str] | tuple[str, ...]) -> None:
    """Queue deleting selected system setting overrides."""
    if isinstance(settings, str):
        raw_settings = [settings]
    else:
        raw_settings = list(settings)
    clean_settings = list(
        dict.fromkeys(setting.strip() for setting in raw_settings if setting.strip())
    )
    if not clean_settings:
        push_floating_status("Select settings to delete.", "warn")
        return
    if len(clean_settings) == 1:
        setting_label = clean_settings[0]
        command = build_hhs_settings_delete_command(setting_label)
        description = f"Deleting setting: {setting_label}"
        success_fallback = f"Setting deleted: {setting_label}"
        error_fallback = f"Unable to delete setting: {setting_label}"
    else:
        setting_label = f"{len(clean_settings)} settings"
        command = build_hhs_settings_delete_many_command(clean_settings)
        description = f"Deleting settings: {len(clean_settings)} selected"
        success_fallback = f"Settings deleted: {len(clean_settings)} selected"
        error_fallback = f"Unable to delete settings: {len(clean_settings)} selected"
    queue_hhs_settings_action(
        command,
        description,
        {
            "operation": "delete",
            "setting": setting_label,
            "settings": clean_settings,
            "success_fallback": success_fallback,
            "error_fallback": error_fallback,
        },
    )


def request_hhs_settings_truncate() -> None:
    """Queue deleting all system setting overrides."""
    queue_hhs_settings_action(
        build_hhs_settings_truncate_command(),
        "Truncating system settings",
        {
            "operation": "truncate",
            "success_fallback": "System settings truncated.",
            "error_fallback": "Unable to truncate system settings.",
        },
    )


def render_hhs_settings_controls(action_running: bool) -> None:
    """Render the HHS Settings add/update controls."""
    setting_defaults = load_hhs_settings_defaults()
    setting_options = list(setting_defaults)
    if setting_options:
        selected_setting = str(st.session_state.get("hhs_settings_add_name", ""))
        if selected_setting and selected_setting not in setting_options:
            setting_options = [selected_setting, *setting_options]
    selected_setting = str(st.session_state.get("hhs_settings_add_name", "")).strip()
    if not selected_setting and setting_options:
        selected_setting = setting_options[0]
    previous_setting = str(
        st.session_state.get("_hhs_settings_add_previous_name", "")
    ).strip()
    if selected_setting != previous_setting:
        st.session_state["hhs_settings_add_value"] = setting_defaults.get(
            selected_setting,
            "",
        )
        st.session_state["_hhs_settings_add_previous_name"] = selected_setting
    st.session_state["hhs_settings_add_variable"] = (
        hhs_setting_variable_name(selected_setting) if selected_setting else ""
    )
    with st.container(key="hhs_settings_controls"):
        with st.expander("Override", expanded=True):
            setting_col, variable_col, value_col, add_col = st.columns(
                [1, 1, 1, 0.22],
                gap="small",
                vertical_alignment="bottom",
            )
            with setting_col:
                st.selectbox(
                    "Setting",
                    setting_options,
                    index=0 if setting_options else None,
                    key="hhs_settings_add_name",
                    placeholder="setting.name",
                    accept_new_options=True,
                    disabled=action_running,
                )
            with variable_col:
                st.text_input(
                    "Variable",
                    key="hhs_settings_add_variable",
                    disabled=True,
                )
            with value_col:
                st.text_input(
                    "Value",
                    key="hhs_settings_add_value",
                    placeholder="value",
                    disabled=action_running,
                )
            with add_col:
                st.button(
                    "",
                    key="hhs_settings_add_button",
                    help="Override",
                    on_click=request_hhs_settings_add,
                    disabled=action_running,
                    width="stretch",
                )


def render_hhs_settings_table(
    rows: list[dict[str, str]],
    action_running: bool,
) -> list[str]:
    """Render overridden system settings with the setup table component style."""
    settings = [row.get("Setting", "") for row in rows]
    selected_values = render_markdown_table(
        "System Overrides",
        settings,
        settings,
        [False for _row in rows],
        hhs_settings_table_key(),
        disabled=action_running,
        variable_values=[row.get("Variable", "") for row in rows],
        extra_columns={"Value": [row.get("Value", "") for row in rows]},
    )
    return [
        setting
        for setting, selected in zip(settings, selected_values, strict=True)
        if selected and setting
    ]


def render_hhs_settings_actions(
    selected_settings: list[str],
    rows: list[dict[str, str]],
    action_running: bool,
) -> None:
    """Render centered HHS Settings mutation buttons."""
    with st.container(key="hhs_settings_action_buttons"):
        left, delete_col, truncate_col, right = st.columns(
            [1, 0.18, 0.18, 1],
            gap="small",
            vertical_alignment="center",
        )
        del left, right
        with delete_col:
            st.button(
                " Delete",
                key="hhs_settings_delete_button",
                help="Delete",
                on_click=request_hhs_settings_delete,
                args=(selected_settings,),
                disabled=action_running or not selected_settings,
                width="stretch",
            )
        with truncate_col:
            st.button(
                " Truncate",
                key="hhs_settings_truncate_button",
                help="Truncate",
                on_click=request_hhs_settings_truncate,
                disabled=action_running or not rows,
                width="stretch",
            )


def render_hhs_settings_title() -> None:
    """Render the HomeSetup Settings page title."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> Settings</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_hhs_settings_panel() -> None:
    """Render the HomeSetup Settings manager panel."""
    execute_pending_hhs_settings_action()
    render_background_job_status(HHS_SETTINGS_ACTION_JOB)
    render_hhs_settings_title()
    result = render_cached_command_result(
        build_hhs_settings_list_command(),
        "Loading overridden system settings",
        "hhs_settings",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load overridden system settings.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load overridden system settings."
            )
        )
        return

    action_running = background_job_is_running(HHS_SETTINGS_ACTION_JOB)
    render_hhs_settings_controls(action_running)
    rows = parse_hhs_settings_list(result.stdout)
    selected_settings = render_hhs_settings_table(rows, action_running)
    render_hhs_settings_actions(selected_settings, rows, action_running)


def request_hhs_starship_preset_apply() -> None:
    """Queue applying the selected Starship preset."""
    preset = str(st.session_state.get("hhs_starship_preset", "")).strip()
    if not preset:
        push_floating_status("Select a Starship preset before applying.", "warn")
        return
    queue_hhs_starship_action(
        build_hhs_starship_preset_command(preset),
        "Applying Starship preset",
        {
            "operation": "preset",
            "preset": preset,
            "success_fallback": f"Starship preset applied: {preset}",
            "error_fallback": f"Unable to apply Starship preset: {preset}",
        },
    )


def toggle_hhs_starship_config_editing() -> None:
    """Toggle inline editing for the rendered Starship config file."""
    st.session_state["hhs_starship_config_editing"] = not bool(
        st.session_state.get("hhs_starship_config_editing")
    )


def request_hhs_starship_config_save() -> None:
    """Queue saving the editable Starship config file."""
    config_content = str(st.session_state.get("hhs_starship_config_editor", ""))
    queue_hhs_starship_action(
        build_hhs_save_starship_config_command(config_content),
        "Saving Starship config",
        {
            "operation": "save_config",
            "success_fallback": "Starship config saved.",
            "error_fallback": "Unable to save Starship config.",
        },
    )


def render_hhs_starship_title() -> None:
    """Render the HomeSetup Starship page title."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> Starship</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def normalize_hhs_starship_preset_state(presets: list[str]) -> None:
    """Keep the selected Starship preset inside the available preset list."""
    selected_preset = str(st.session_state.get("hhs_starship_preset", "")).strip()
    if selected_preset in presets:
        return

    current_preset = str(
        st.session_state.get(hhs_ui_constants.HHS_STARSHIP_CURRENT_PRESET_KEY, "")
    ).strip()
    if current_preset in presets:
        st.session_state["hhs_starship_preset"] = current_preset
    elif presets:
        st.session_state["hhs_starship_preset"] = presets[0]
    else:
        st.session_state["hhs_starship_preset"] = ""


def render_hhs_starship_controls(
    starship_info: dict[str, object], action_running: bool
) -> None:
    """Render Starship paths, preset selector, and apply action."""
    cache_path = str(starship_info.get("cache", "")).strip()
    config_path = str(starship_info.get("config", "")).strip()
    presets = [
        str(preset).strip()
        for preset in starship_info.get("presets", [])
        if str(preset).strip()
    ]
    normalize_hhs_starship_preset_state(presets)
    preset_options = presets or [""]
    editing = bool(st.session_state.get("hhs_starship_config_editing"))
    edit_button_key = (
        "hhs_starship_edit_config_button_selected"
        if editing
        else "hhs_starship_edit_config_button"
    )
    with st.container(key="hhs_starship_controls"):
        with st.expander("Configurations", expanded=True):
            cache_col, config_col, preset_col, apply_col, edit_col = st.columns(
                [1.2, 1.6, 1.1, 0.22, 0.22],
                gap="small",
                vertical_alignment="bottom",
            )
            with cache_col:
                st.text_input(
                    "Cache",
                    value=cache_path,
                    disabled=True,
                )
            with config_col:
                st.text_input(
                    "Config",
                    value=config_path,
                    disabled=True,
                )
            with preset_col:
                st.selectbox(
                    "Preset",
                    preset_options,
                    key="hhs_starship_preset",
                    disabled=action_running or not presets,
                )
            with apply_col:
                st.button(
                    "",
                    key="hhs_starship_apply_preset_button",
                    help="Apply Starship preset",
                    on_click=request_hhs_starship_preset_apply,
                    disabled=action_running or not presets,
                    width="stretch",
                )
            with edit_col:
                st.button(
                    "",
                    key=edit_button_key,
                    help="Toggle Starship config editing",
                    on_click=toggle_hhs_starship_config_editing,
                    disabled=action_running or not config_path,
                    width="stretch",
                )


def sync_hhs_starship_config_editor_state(config_content: str) -> None:
    """Keep the read-only Starship editor synchronized with loaded file content."""
    content_token = hashlib.sha256(config_content.encode("utf-8")).hexdigest()
    if "hhs_starship_config_editor" not in st.session_state:
        st.session_state["hhs_starship_config_editor"] = config_content
    if st.session_state.get("hhs_starship_config_editing"):
        return
    if st.session_state.get("hhs_starship_config_content_token") == content_token:
        return
    st.session_state["hhs_starship_config_editor"] = config_content
    st.session_state["hhs_starship_config_content_token"] = content_token


def render_hhs_starship_config_editor(
    starship_info: dict[str, object], action_running: bool
) -> None:
    """Render the current Starship config file contents."""
    config_path = str(starship_info.get("config", "")).strip()
    config_content = str(starship_info.get("content", ""))
    editing = bool(st.session_state.get("hhs_starship_config_editing"))
    sync_hhs_starship_config_editor_state(config_content)

    with st.container(key="hhs_starship_config_editor_panel"):
        st.text_area(
            "Starship config",
            key="hhs_starship_config_editor",
            height=360,
            disabled=not editing or action_running,
            label_visibility="collapsed",
        )
        if editing:
            st.button(
                "",
                key="hhs_starship_save_config_button",
                help="Save Starship config",
                on_click=request_hhs_starship_config_save,
                disabled=action_running or not config_path,
            )


def render_hhs_starship_panel() -> None:
    """Render the HomeSetup Starship integration panel."""
    execute_pending_hhs_starship_action()
    render_background_job_status(HHS_STARSHIP_ACTION_JOB)
    render_hhs_starship_title()
    result = render_cached_command_result(
        build_hhs_starship_info_command(),
        "Loading Starship configuration",
        "hhs_starship",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load Starship configuration.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load Starship configuration."
            )
        )
        return

    starship_info = parse_hhs_starship_info(result.stdout)
    action_running = background_job_is_running(HHS_STARSHIP_ACTION_JOB)
    render_hhs_starship_controls(starship_info, action_running)
    render_hhs_starship_config_editor(starship_info, action_running)


def hhs_firebase_info_token(firebase_info: dict[str, object]) -> str:
    """Return a stable token for the loaded Firebase config file."""
    return json.dumps(
        {
            "config_file": str(firebase_info.get("config_file", "")),
            "content": str(firebase_info.get("content", "")),
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def hhs_firebase_info_values(firebase_info: dict[str, object]) -> dict[str, str]:
    """Return normalized Firebase field values from loaded info."""
    raw_values = firebase_info.get("values", {})
    values = raw_values if isinstance(raw_values, dict) else {}
    return {
        property_name: normalize_hhs_firebase_value(values.get(property_name, ""))
        for _label, property_name, _fallback, _state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    }


def hhs_firebase_form_state_needs_reload(values: dict[str, str]) -> bool:
    """Return whether Firebase form widgets need to be repopulated."""
    state_keys = [
        state_key
        for _label, _property_name, _fallback, state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    ]
    original_values = st.session_state.get("_hhs_firebase_original_values")
    if not isinstance(original_values, dict):
        return True
    if any(state_key not in st.session_state for state_key in state_keys):
        return True
    loaded_has_value = any(
        values.get(property_name, "")
        for _label, property_name, _fallback, _state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    )
    if not loaded_has_value or st.session_state.get("_hhs_firebase_form_dirty"):
        return False
    current_values = [
        normalize_hhs_firebase_value(st.session_state.get(state_key, ""))
        for _label, _property_name, _fallback, state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    ]
    return not any(current_values)


def sync_hhs_firebase_form_state(firebase_info: dict[str, object]) -> None:
    """Initialize Firebase form state when the loaded config changes."""
    token = hhs_firebase_info_token(firebase_info)
    values = hhs_firebase_info_values(firebase_info)
    token_matches = st.session_state.get("_hhs_firebase_loaded_token") == token
    if token_matches and not hhs_firebase_form_state_needs_reload(values):
        return
    st.session_state["_hhs_firebase_loaded_token"] = token
    st.session_state["_hhs_firebase_original_content"] = str(
        firebase_info.get("content", "")
    )
    st.session_state["_hhs_firebase_original_values"] = values
    st.session_state["_hhs_firebase_form_dirty"] = False
    for _label, property_name, _fallback, state_key, _placeholder in HHS_FIREBASE_FIELDS:
        st.session_state[state_key] = values.get(property_name, "")


def apply_pending_hhs_firebase_form_revert() -> None:
    """Apply a queued Firebase form revert before rendering inputs."""
    if not st.session_state.pop("_hhs_firebase_revert_pending", False):
        return
    restore_hhs_firebase_original_values()


def restore_hhs_firebase_original_values() -> bool:
    """Restore Firebase form session values from the loaded config file."""
    original_values = st.session_state.get("_hhs_firebase_original_values", {})
    if not isinstance(original_values, dict):
        return False
    for _label, property_name, _fallback, state_key, _placeholder in HHS_FIREBASE_FIELDS:
        st.session_state[state_key] = normalize_hhs_firebase_value(
            original_values.get(property_name, "")
        )
    st.session_state["_hhs_firebase_form_dirty"] = False
    return True


def selected_hhs_firebase_values() -> dict[str, str]:
    """Return Firebase property values selected in the form."""
    return {
        property_name: normalize_hhs_firebase_value(st.session_state.get(state_key, ""))
        for _label, property_name, _fallback, state_key, _placeholder in (
            HHS_FIREBASE_FIELDS
        )
    }


def apply_hhs_firebase_component_values(values: object) -> None:
    """Copy Firebase component values into Streamlit session state."""
    value_map = values if isinstance(values, dict) else {}
    for _label, property_name, _fallback, state_key, _placeholder in (
        HHS_FIREBASE_FIELDS
    ):
        st.session_state[state_key] = normalize_hhs_firebase_value(
            value_map.get(property_name, st.session_state.get(state_key, ""))
        )
    st.session_state["_hhs_firebase_form_dirty"] = True


def request_hhs_firebase_save() -> None:
    """Queue saving Firebase configuration values."""
    original_content = str(st.session_state.get("_hhs_firebase_original_content", ""))
    config_content = render_hhs_firebase_config_content(
        original_content,
        selected_hhs_firebase_values(),
    )
    queue_hhs_firebase_action(
        build_hhs_save_firebase_config_command(config_content),
        "Saving Firebase configuration",
        {
            "operation": "save_config",
            "success_fallback": "Firebase configuration saved.",
            "error_fallback": "Unable to save Firebase configuration.",
        },
    )


def request_hhs_firebase_revert() -> None:
    """Queue reverting the Firebase form to the loaded config values."""
    st.session_state["_hhs_firebase_revert_pending"] = True
    save_ui_state()


def request_hhs_firebase_alias_action(operation: str, selected_alias: str) -> None:
    """Queue uploading or downloading the selected Firebase alias."""
    clean_operation = operation.strip().lower()
    clean_alias = selected_alias.strip()
    if clean_operation not in {"upload", "download"}:
        push_floating_status("Unsupported Firebase alias action.", "error")
        return
    if not clean_alias:
        push_floating_status("Select a Firebase alias before continuing.", "warn")
        return
    operation_label = clean_operation.title()
    queue_hhs_firebase_action(
        build_hhs_firebase_alias_action_command(clean_operation, clean_alias),
        f"{operation_label} Firebase alias: {clean_alias}",
        {
            "operation": clean_operation,
            "alias": clean_alias,
            "success_fallback": f"Firebase alias {clean_operation} completed: {clean_alias}",
            "error_fallback": f"Unable to {clean_operation} Firebase alias: {clean_alias}",
        },
    )


def render_hhs_firebase_title() -> None:
    """Render the HomeSetup Firebase page title."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> Firebase</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def hhs_firebase_config_file() -> Path:
    """Return the HomeSetup Firebase configuration file path."""
    return Path(
        os.environ.get(
            "HHS_FIREBASE_CONFIG_FILE",
            homesetup_config_dir() / "firebase.properties",
        )
    ).expanduser()


def hhs_firebase_creds_file(project_id: str) -> Path:
    """Return the Firebase service account credentials file path."""
    creds_template = os.environ.get(
        "HHS_FIREBASE_CREDS_FILE",
        str(Path.home() / "firebase-credentials.json"),
    )
    return Path(creds_template.format(project_id=project_id)).expanduser()


def hhs_firebase_configuration() -> object:
    """Return the hspylib Firebase configuration."""
    from datasource.firebase.firebase_configuration import FirebaseConfiguration

    return FirebaseConfiguration.of_file(str(hhs_firebase_config_file()))


def firebase_authenticate(project_id: str, uid: str) -> None:
    """Authenticate the configured Firebase user using hspylib."""
    from firebase.core.firebase_auth import FirebaseAuth

    FirebaseAuth.authenticate(project_id, uid)


def firebase_rest_auth_headers(project_id: str) -> list[dict[str, str]]:
    """Return OAuth headers for Firebase Realtime Database REST requests."""
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(
        str(hhs_firebase_creds_file(project_id)),
        scopes=[
            "https://www.googleapis.com/auth/firebase.database",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
    )
    credentials.refresh(Request())
    return [{"Authorization": f"Bearer {credentials.token}"}]


def firebase_root_json_url(firebase_config: object) -> str:
    """Return the Firebase Realtime Database root JSON URL."""
    database = str(getattr(firebase_config, "database", "") or "").strip("/")
    base_url = str(getattr(firebase_config, "base_url", "") or "").rstrip("/")
    if database and base_url.endswith(f"/{database}"):
        root_url = base_url[: -(len(database) + 1)]
    else:
        scheme = str(getattr(firebase_config, "scheme", "") or "https")
        hostname = str(getattr(firebase_config, "hostname", "") or "")
        port = str(getattr(firebase_config, "port", "") or "")
        root_url = f"{scheme}://{hostname}" + (f":{port}" if port else "")
    return f"{root_url.rstrip('/')}/.json"


def firebase_root_json_response(firebase_config: object) -> object:
    """Request the Firebase Realtime Database root JSON payload."""
    from hspylib.modules.fetch.fetch import get
    from urllib3.exceptions import InsecureRequestWarning

    project_id = str(getattr(firebase_config, "project_id", "") or "")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        return get(
            firebase_root_json_url(firebase_config),
            headers=firebase_rest_auth_headers(project_id),
            timeout=10,
        )


def firebase_response_is_success(response: object) -> bool:
    """Return whether a Firebase REST response succeeded."""
    status_code = getattr(response, "status_code", None)
    if hasattr(status_code, "is_2xx"):
        return bool(status_code.is_2xx())
    try:
        return 200 <= int(status_code) < 300
    except (TypeError, ValueError):
        return False


def firebase_response_json(response: object) -> dict[str, object]:
    """Return a Firebase REST response body as a dictionary."""
    body = str(getattr(response, "body", "") or "").strip()
    if not body or body == "null" or not firebase_response_is_success(response):
        return {}
    alias_data = json.loads(body)
    return alias_data if isinstance(alias_data, dict) else {}


def fetch_firebase_aliases_uncached() -> dict[str, object]:
    """Return Firebase alias data from the live Realtime Database root."""
    firebase_config = hhs_firebase_configuration()
    firebase_authenticate(
        str(getattr(firebase_config, "project_id", "") or ""),
        str(getattr(firebase_config, "uid", "") or ""),
    )
    response = firebase_root_json_response(firebase_config)
    if not firebase_response_is_success(response):
        raise RuntimeError(f"Unable to fetch Firebase aliases: {response!r}")
    return firebase_response_json(response)


@lru_cache(maxsize=1)
def fetch_firebase_aliases_cached() -> dict[str, object]:
    """Return cached Firebase aliases from the live Realtime Database root."""
    return fetch_firebase_aliases_uncached()


def clear_firebase_aliases_cache() -> None:
    """Clear cached Firebase aliases."""
    fetch_firebase_aliases_cached.cache_clear()


def firebase_aliases_cache_is_warm() -> bool:
    """Return whether Firebase aliases are already cached."""
    return fetch_firebase_aliases_cached.cache_info().currsize > 0


def fetch_firebase_aliases() -> dict[str, object]:
    """Return cached Firebase alias data from the live Realtime Database root."""
    try:
        return fetch_firebase_aliases_cached()
    except Exception as err:
        clear_firebase_aliases_cache()
        logging.warning("Unable to fetch Firebase aliases: %s", err)
        return {}


def fetch_firebase_aliases_with_preloader() -> dict[str, object]:
    """Return Firebase aliases while rendering a transient loading message."""
    if firebase_aliases_cache_is_warm():
        return fetch_firebase_aliases()
    loader_placeholder = st.empty()
    with loader_placeholder.container():
        render_command_loader("Fetching Firebase aliases")
    try:
        return fetch_firebase_aliases()
    finally:
        loader_placeholder.empty()


def firebase_alias_table_rows(alias_data: dict[str, object]) -> list[dict[str, str]]:
    """Return Firebase alias rows from the fetched alias payload."""
    rows: list[dict[str, str]] = []
    for database_name, groups in alias_data.items():
        if not isinstance(groups, dict):
            continue
        for group_name, aliases in groups.items():
            if not isinstance(aliases, dict):
                continue
            for alias_name, alias_value in aliases.items():
                count = len(alias_value) if isinstance(alias_value, list) else 0
                rows.append(
                    {
                        "Database": str(database_name),
                        "Group": str(group_name),
                        "Alias": str(alias_name),
                        "Count": str(count),
                    }
                )
    return rows


def render_hhs_firebase_aliases_table(action_running: bool) -> str:
    """Render the Firebase aliases table and return the selected alias."""
    alias_rows = firebase_alias_table_rows(fetch_firebase_aliases_with_preloader())
    alias_keys = [
        f"{row['Database']}:{row['Group']}:{row['Alias']}" for row in alias_rows
    ]
    selected_values = render_markdown_table(
        "Firebase Aliases",
        [row["Database"] for row in alias_rows],
        alias_keys,
        [False] * len(alias_rows),
        "hhs_firebase_aliases",
        disabled=action_running,
        variable_values=[row["Group"] for row in alias_rows],
        item_column_label="Database",
        variable_column_label="Group",
        extra_columns={
            "Alias": [row["Alias"] for row in alias_rows],
            "Count": [row["Count"] for row in alias_rows],
        },
        multi_selection=False,
        show_value_column=False,
        column_text_colors={
            "Group": "var(--hhs-secondary)",
            "Alias": "var(--hhs-theme-primary-color)",
        },
    )
    selected_aliases = [
        row["Alias"]
        for row, selected in zip(alias_rows, selected_values, strict=True)
        if selected
    ]
    return selected_aliases[0] if selected_aliases else ""


def render_hhs_firebase_aliases_actions(
    selected_alias: str,
    action_running: bool,
) -> None:
    """Render centered Firebase alias transfer buttons."""
    clean_alias = selected_alias.strip()
    action_disabled = action_running or not clean_alias
    with st.container(key="hhs_firebase_aliases_action_buttons"):
        left, upload_col, download_col, right = st.columns(
            [1, 0.28, 0.28, 1],
            gap="small",
            vertical_alignment="center",
        )
        del left, right
        with upload_col:
            st.button(
                " Upload",
                key="hhs_firebase_alias_upload_button",
                help="Upload",
                on_click=request_hhs_firebase_alias_action,
                args=("upload", clean_alias),
                disabled=action_disabled,
                width="stretch",
            )
        with download_col:
            st.button(
                " Download",
                key="hhs_firebase_alias_download_button",
                help="Download",
                on_click=request_hhs_firebase_alias_action,
                args=("download", clean_alias),
                disabled=action_disabled,
                width="stretch",
            )


@lru_cache(maxsize=1)
def firebase_config_component() -> Callable[..., dict[str, object] | None]:
    """Return the registered Firebase configuration Streamlit component."""
    return components.declare_component(
        "hhs_firebase_config_form",
        path=str(hhs_ui.FIREBASE_CONFIG_COMPONENT_DIR),
    )


def firebase_config_component_theme() -> dict[str, str]:
    """Return CSS tokens for the Firebase configuration component iframe."""
    theme_name = st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    properties = theme_custom_properties(theme_name)
    return {
        "background": resolve_css_custom_property(
            properties, "hhs-background", "#282a36"
        ),
        "field": resolve_css_custom_property(
            properties, "hhs-theme-secondary-background-color", "#44475a"
        ),
        "text": resolve_css_custom_property(
            properties, "hhs-theme-text-color", "#f8f8f2"
        ),
        "muted": resolve_css_custom_property(
            properties, "hhs-theme-input-placeholder-color", "#686e7a"
        ),
        "border": resolve_css_custom_property(
            properties, "hhs-theme-dataframe-border-color", "#6272a4"
        ),
        "primary": resolve_css_custom_property(
            properties, "hhs-theme-primary-color", "#bd93f9"
        ),
        "buttonWidth": resolve_css_custom_property(
            properties, "hhs-theme-hhs-action-button-width", "140px"
        ),
    }


def hhs_firebase_component_fields() -> list[dict[str, str]]:
    """Return Firebase component field definitions and current values."""
    return [
        {
            "label": label,
            "name": property_name,
            "placeholder": placeholder,
            "value": normalize_hhs_firebase_value(
                st.session_state.get(state_key, "")
            ),
        }
        for label, property_name, _fallback, state_key, placeholder in (
            HHS_FIREBASE_FIELDS
        )
    ]


def render_hhs_firebase_config_component(
    action_running: bool,
) -> dict[str, object] | None:
    """Render the Firebase configuration component and return its event."""
    component = firebase_config_component()
    return component(
        disabled=action_running,
        fields=hhs_firebase_component_fields(),
        theme=firebase_config_component_theme(),
        token=str(st.session_state.get("_hhs_firebase_loaded_token", "default")),
        key="hhs_firebase_config_component",
        default=None,
    )


def handle_hhs_firebase_config_component_event(event: object) -> bool:
    """Handle one Firebase configuration component action event."""
    if not isinstance(event, dict):
        return False
    event_id = normalize_hhs_firebase_value(event.get("eventId", ""))
    if not event_id:
        return False
    if st.session_state.get("_hhs_firebase_config_component_event_id") == event_id:
        return False
    st.session_state["_hhs_firebase_config_component_event_id"] = event_id

    action = normalize_hhs_firebase_value(event.get("action", ""))
    if action == "save":
        apply_hhs_firebase_component_values(event.get("values", {}))
        request_hhs_firebase_save()
        return True
    if action == "restore":
        restore_hhs_firebase_original_values()
        save_ui_state()
        return True
    return False


def render_hhs_firebase_configurations(action_running: bool) -> None:
    """Render Firebase configuration fields and action buttons."""
    with st.container(key="hhs_firebase_configurations"):
        with st.expander("Configurations", expanded=True):
            event = render_hhs_firebase_config_component(action_running)
        selected_alias = render_hhs_firebase_aliases_table(action_running)
        render_hhs_firebase_aliases_actions(selected_alias, action_running)
    if handle_hhs_firebase_config_component_event(event):
        st.rerun()


def render_hhs_firebase_panel() -> None:
    """Render the HomeSetup Firebase configuration panel."""
    execute_pending_hhs_firebase_action()
    render_background_job_status(HHS_FIREBASE_ACTION_JOB)
    render_hhs_firebase_title()
    result = render_cached_command_result(
        build_hhs_firebase_info_command(),
        "Loading Firebase configuration",
        "hhs_firebase",
        hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS,
        hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS,
        "Unable to load Firebase configuration.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load Firebase configuration."
            )
        )
        return

    firebase_info = parse_hhs_firebase_info(result.stdout)
    sync_hhs_firebase_form_state(firebase_info)
    apply_pending_hhs_firebase_form_revert()
    action_running = background_job_is_running(HHS_FIREBASE_ACTION_JOB)
    render_hhs_firebase_configurations(action_running)


def render_hhs_placeholder_panel(hhs_view: str) -> None:
    """Render a title-only placeholder HHS sub-page."""
    st.markdown(
        f"""
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2>{html.escape(hhs_view)}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_hhs_view() -> None:
    """Render the HomeSetup application view."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> HomeSetup Application</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    hhs_view = render_view_segmented_control(
        "HHS view",
        hhs_ui.HHS_VIEWS,
        "hhs_view",
        "SETUP",
        format_func=hhs_view_label,
    )
    if hhs_view == "SETUP":
        render_hhs_setup_panel()
    elif hhs_view == "STARSHIP":
        render_hhs_starship_panel()
    elif hhs_view == "SETTINGS":
        render_hhs_settings_panel()
    elif hhs_view == "Firebase":
        render_hhs_firebase_panel()
    else:
        render_hhs_placeholder_panel(hhs_view)


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


def normalize_remote_explorer_path(
    path_value: str, base_path: str | None = None
) -> str:
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
    return textwrap.dedent(f"""
        raw_target={safe_path}
        case "${{raw_target}}" in
          "~") target=${{HOME:-.}} ;;
          "~/"*) target="${{HOME:-.}}/${{raw_target#*/}}" ;;
          *) target="${{raw_target}}" ;;
        esac
        [ -n "${{target}}" ] || target=.
        """).strip()


def build_remote_explorer_listing_command(remote_path: str) -> str:
    """Build a portable remote shell command that lists one directory."""
    return textwrap.dedent(f"""
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
        """).strip()


def build_remote_explorer_create_folder_command(remote_path: str) -> str:
    """Build a remote shell command that creates the requested folder path."""
    return textwrap.dedent(f"""
        {remote_explorer_target_assignment(remote_path)}
        mkdir -p "${{target}}" || exit 1
        abs_dir=$(cd "${{target}}" && pwd -P) || exit 1
        printf '__HHS_CREATED_DIR__\\t%s\\n' "${{abs_dir}}"
        """).strip()


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
    """Queue creation of the requested remote explorer folder path."""
    clean_remote_path = remote_path.strip() or ssh_explorer_remote_default_path()
    st.session_state["ssh_explorer_action_execute_pending"] = {
        "action": "create_remote_folder",
        "remote_path": clean_remote_path,
    }
    save_ui_state()


def start_pending_ssh_explorer_action() -> None:
    """Start a queued SSH explorer action background job, when present."""
    pending = st.session_state.pop("ssh_explorer_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    action = str(pending.get("action", "")).strip()
    if action != "create_remote_folder":
        return
    remote_path = str(pending.get("remote_path", "")).strip()
    if not remote_path:
        return
    started = start_background_action_job(
        SSH_EXPLORER_ACTION_JOB,
        build_remote_explorer_create_folder_command(remote_path),
        "Creating remote folder",
        hhs_ui.UI_COMMAND_REMOTE_TIMEOUT_SECONDS,
        pending,
        "Another SSH explorer action is already running.",
    )
    if started:
        push_floating_status("Creating remote folder.", "info")
    else:
        st.session_state["ssh_explorer_action_execute_pending"] = pending


def complete_ssh_explorer_action_job() -> None:
    """Complete an SSH explorer action and refresh file listings."""
    completed = background_job_result(SSH_EXPLORER_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    remote_path = str(metadata.get("remote_path", "")).strip()
    if result.returncode != 0:
        push_floating_status(
            strip_ansi(result.stderr or result.stdout or "Unable to create folder."),
            "error",
        )
        save_ui_state()
        return
    created_dir = parse_remote_explorer_created_dir(result.stdout)
    created_path = created_dir or remote_path
    created_name = posixpath.basename(created_path) or created_path
    open_remote_explorer_path(created_path)
    push_floating_status(f"Folder created on remote {created_name}", "info")
    save_ui_state()


def execute_pending_ssh_explorer_action() -> None:
    """Start or complete the current SSH explorer action background job."""
    start_pending_ssh_explorer_action()
    complete_ssh_explorer_action_job()


def create_ssh_explorer_folder(panel: str, local_path: str, remote_path: str) -> None:
    """Create a new folder in the active SSH explorer panel."""
    if panel == "remote":
        create_remote_explorer_folder(remote_path)
    else:
        create_local_explorer_folder(local_path)

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
        "placeholder": resolve_css_custom_property(
            properties, "hhs-theme-input-placeholder-color", "#686e7a"
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
    return textwrap.dedent(f"""
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
        """).strip()


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
        show_preloader_event=True,
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
        ssh_explorer_delete_name(panel, path) for path in paths if str(path).strip()
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
    """Queue the pending SSH explorer delete request."""
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
    st.session_state["ssh_explorer_delete_execute_pending"] = {
        "panel": panel,
        "paths": clean_paths,
        "force_local": panel == "local",
    }
    save_ui_state()


def start_pending_ssh_explorer_delete() -> None:
    """Start a queued SSH explorer delete background job, when present."""
    pending = st.session_state.pop("ssh_explorer_delete_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    paths_value = pending.get("paths", [])
    paths = paths_value if isinstance(paths_value, list) else []
    clean_paths = [str(path) for path in paths if str(path).strip()]
    if not clean_paths:
        return
    pending["paths"] = clean_paths
    started = start_background_action_job(
        SSH_EXPLORER_DELETE_JOB,
        build_recoverable_delete_command(clean_paths),
        "Deleting selected file(s)/folder(s)",
        hhs_ui.UI_COMMAND_REMOTE_TIMEOUT_SECONDS,
        pending,
        "Another SSH explorer delete action is already running.",
        force_local=bool(pending.get("force_local", False)),
    )
    if started:
        push_floating_status("Deleting selected file(s)/folder(s).", "info")
    else:
        st.session_state["ssh_explorer_delete_execute_pending"] = pending


def complete_ssh_explorer_delete_job() -> None:
    """Complete an SSH explorer delete job and refresh file listings."""
    completed = background_job_result(SSH_EXPLORER_DELETE_JOB)
    if completed is None:
        return
    result, _metadata = completed
    if result.returncode != 0:
        push_floating_status(
            strip_ansi(result.stderr or result.stdout or "Unable to delete selection."),
            "error",
        )
        save_ui_state()
        return
    cache_delete_tag("ssh_files")
    push_floating_status("Deleted selected file(s)/folder(s).", "info")
    save_ui_state()


def execute_pending_ssh_explorer_delete() -> None:
    """Start or complete the current SSH explorer delete background job."""
    start_pending_ssh_explorer_delete()
    complete_ssh_explorer_delete_job()


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
    execute_pending_ssh_explorer_action()
    execute_pending_ssh_explorer_delete()
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
    if background_job_is_running(SSH_EXPLORER_ACTION_JOB):
        render_background_job_status(SSH_EXPLORER_ACTION_JOB)
    if background_job_is_running(SSH_EXPLORER_DELETE_JOB):
        render_background_job_status(SSH_EXPLORER_DELETE_JOB)

    transfer_running = (
        background_job_is_running(SSH_FILE_TRANSFER_JOB)
        or background_job_is_running(SSH_EXPLORER_ACTION_JOB)
        or background_job_is_running(SSH_EXPLORER_DELETE_JOB)
    )
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
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> Remote Connection</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    ssh_view = render_view_segmented_control(
        "SSH view",
        hhs_ui.SSH_VIEWS,
        "ssh_view",
        "TUNNELS",
        format_func=ssh_view_label,
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


def search_command_cache_key(
    search_type: str,
    query: str,
    search_path: str,
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
    replace: bool = False,
    replacement: object = "",
) -> str:
    """Return the tagged MD5 command cache key for one Search execution."""
    option_values = normalized_search_option_values(
        search_type, ignore_case, words, binary, replace, replacement
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


def cached_search_command_result(
    command: str, cache_key: str
) -> subprocess.CompletedProcess[str] | None:
    """Return a cached Search command result by explicit Search cache key."""
    command_to_run = effective_bash_command(command)
    remote_host = command_remote_host()
    cached_value = cache_get(cache_key)
    if cached_value is None:
        cached_value = command_result_snapshot_get(cache_key)
    if cached_value is None:
        return None
    command_result_snapshot_set(cache_key, cached_value)
    result = sanitize_remote_command_result(
        remote_host,
        completed_process_from_cache(command_to_run, cached_value),
    )
    if handle_remote_command_result(remote_host, result):
        st.rerun()
    return result


def search_command_background_metadata(
    command: str, cache_key: str
) -> dict[str, object]:
    """Return background metadata for one Search command execution."""
    return {
        **background_command_metadata(command, "search"),
        "cache_key": cache_key,
        "ttl_seconds": hhs_ui.UI_CACHE_NORMAL_TTL_SECONDS,
    }


def search_background_job_matches(cache_key: str) -> bool:
    """Return whether the active Search background job is for the cache key."""
    job = background_job_state(SEARCH_COMMAND_JOB)
    if not job:
        return False
    metadata = job.get("metadata")
    return (
        isinstance(metadata, dict) and str(metadata.get("cache_key", "")) == cache_key
    )


def complete_search_command_result(
    cache_key: str,
) -> subprocess.CompletedProcess[str] | None:
    """Complete the active Search background job and cache its result."""
    completed = background_job_result(SEARCH_COMMAND_JOB)
    if completed is None:
        return None
    result, metadata = completed
    if str(metadata.get("cache_key", "")) != cache_key:
        return None
    if result.returncode == 0:
        cache_background_command_result(metadata, result)
    return result


def start_search_command(command: str, cache_key: str, loader_message: str) -> bool:
    """Start the Search command in the background with a command preloader event."""
    if background_job_state(SEARCH_COMMAND_JOB) and not search_background_job_matches(
        cache_key
    ):
        stop_background_job(SEARCH_COMMAND_JOB)
    return start_background_bash_command(
        SEARCH_COMMAND_JOB,
        command,
        loader_message,
        hhs_ui_constants.UI_COMMAND_SEARCH_TIMEOUT_SECONDS,
        metadata=search_command_background_metadata(command, cache_key),
        show_preloader_event=True,
    )


def create_search_result_download_dir() -> Path:
    """Create the stable local cache directory for downloaded remote Search results."""
    download_dir = ui_disposable_files_dir() / "hhs-search-open.dir"
    shutil.rmtree(download_dir, ignore_errors=True)
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def search_result_download_path(remote_path: str, download_dir: Path) -> Path:
    """Return the expected local path for one downloaded remote Search result."""
    return download_dir / search_result_download_name(remote_path)


def build_download_remote_search_result_command(
    remote_path: str, download_dir: Path, host: str
) -> str:
    """Build a local scp command that downloads one remote Search result."""
    return build_scp_to_local_command(remote_path, str(download_dir), host)


def build_open_remote_search_result_command(
    remote_path: str, local_path: Path, download_dir: Path, host: str
) -> str:
    """Build a local command that downloads and opens one remote Search result."""
    download_command = build_download_remote_search_result_command(
        remote_path, download_dir, host
    )
    open_command = build_hhs_open_search_result_command(str(local_path))
    return f"{download_command} && {open_command}"


def queue_search_open_action(
    command: str, description: str, metadata: dict[str, object]
) -> None:
    """Queue a Search result open action for background execution."""
    st.session_state["search_open_execute_pending"] = {
        **metadata,
        "command": command,
        "description": description,
    }
    save_ui_state()


def start_pending_search_open_action() -> None:
    """Start a queued Search result open background job, when present."""
    pending = st.session_state.pop("search_open_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        SEARCH_OPEN_JOB,
        command,
        description,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        pending,
        "Another Search open action is already running.",
        force_local=True,
    )
    if not started:
        st.session_state["search_open_execute_pending"] = pending


def complete_search_open_action_job() -> None:
    """Complete a Search result open action and publish its status."""
    completed = background_job_result(SEARCH_OPEN_JOB)
    if completed is None:
        return
    result, metadata = completed
    path = str(metadata.get("path", "")).strip()
    action = str(metadata.get("action", "open")).strip()
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        if action == "remote_open":
            fallback = f"Opened downloaded result {path}."
        else:
            fallback = f"Opened {path}."
        push_floating_status(status_message or fallback, "info")
    else:
        if action == "remote_open":
            fallback = f"Unable to download or open remote result {path}."
        else:
            fallback = f"Unable to open {path}."
        push_floating_status(status_message or fallback, "error")
    save_ui_state()


def execute_pending_search_open_action() -> None:
    """Start or complete the current Search result open background job."""
    start_pending_search_open_action()
    complete_search_open_action_job()


def open_local_search_result_path(path: str) -> None:
    """Queue opening one local Search result path through HomeSetup."""
    queue_search_open_action(
        build_hhs_open_search_result_command(path),
        f"Opening {path}",
        {"action": "local_open", "path": path},
    )


def open_remote_search_result_path(path: str, host: str) -> None:
    """Queue downloading one remote Search result and opening it locally."""
    download_dir = create_search_result_download_dir()
    local_path = search_result_download_path(path, download_dir)
    queue_search_open_action(
        build_open_remote_search_result_command(path, local_path, download_dir, host),
        f"Opening remote result {path}",
        {
            "action": "remote_open",
            "path": path,
            "local_path": str(local_path),
            "host": host,
        },
    )


def open_search_result_path(path: str) -> None:
    """Open one Search result path through the HomeSetup generic opener."""
    clean_path = path_from_file_uri(path)
    if not clean_path:
        return
    host = connected_ssh_host()
    if host:
        open_remote_search_result_path(clean_path, host)
        return
    open_local_search_result_path(clean_path)


def parse_hhs_search_results(
    output: str, search_type: str, search_path: str
) -> list[dict[str, str]]:
    """Parse HomeSetup search command output into table rows."""
    rows: list[dict[str, str]] = []
    result_type = "Folder" if search_type == "Folders" else search_type.rstrip("s")
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if not clean_line or search_output_line_is_status(clean_line):
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
                if search_output_line_is_status(parts[1]):
                    continue
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


def search_result_index_width(total_count: int) -> str:
    """Return the CSS width for the Search result index column."""
    safe_total = max(1, int(total_count or 1))
    return f"{len(str(safe_total))}ch"


def search_result_index_header(total_count: int) -> str:
    """Return the empty Search result index table header."""
    width = html.escape(search_result_index_width(total_count), quote=True)
    return f'<th class="hhs-search-result-index" style="width: {width};"></th>'


def search_result_index_cell(index: int) -> str:
    """Return one Search result index table cell."""
    return f'<td class="hhs-search-result-index">{index}</td>'


def render_search_string_results(
    rows: list[dict[str, str]],
    query: str,
    text_filter: str = "",
    total_count: int = 0,
) -> None:
    """Render string Search results with highlighted matching text."""
    if not rows:
        st.caption("No search results.")
        return
    line_filter = query or text_filter
    table_index_header = search_result_index_header(total_count or len(rows))
    table_rows = []
    for index, row in enumerate(rows, start=1):
        table_rows.append(
            "<tr>"
            f"{search_result_index_cell(index)}"
            f"<td>{search_result_path_link(row)}</td>"
            f"<td>{html.escape(row.get('Line', ''))}</td>"
            f"<td>{colorize_search_result_line(row.get('Match', ''), line_filter)}</td>"
            "</tr>"
        )
    st.markdown(
        '<div class="hhs-search-results hhs-search-string-results">'
        "<table>"
        f"<thead><tr>{table_index_header}<th>Path</th><th>Line</th><th>Match</th></tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_search_path_results(
    rows: list[dict[str, str]], search_type: str, total_count: int = 0
) -> None:
    """Render file and folder Search results with clickable paths."""
    if not rows:
        st.caption("No search results.")
        return
    headers = search_result_headers(search_type)
    table_index_header = search_result_index_header(total_count or len(rows))
    header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    table_rows = []
    for index, row in enumerate(rows, start=1):
        row_cells = [
            search_result_index_cell(index),
            f"<td>{search_result_path_link(row)}</td>",
        ]
        if "Size" in headers:
            row_cells.append(f"<td>{html.escape(row.get('Size', ''))}</td>")
        row_cells.append(f"<td>{html.escape(row.get('Modified', ''))}</td>")
        table_rows.append(f"<tr>{''.join(row_cells)}</tr>")
    st.markdown(
        '<div class="hhs-search-results hhs-search-string-results">'
        "<table>"
        f"<thead><tr>{table_index_header}{header_html}</tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )


def search_replace_status_message(replaced_count: int) -> str:
    """Return the user-facing Search replace completion status."""
    entry_label = "entry" if replaced_count == 1 else "entries"
    return f"{replaced_count} {entry_label} replaced"


def push_search_replace_status(cache_key: str, replaced_count: int) -> None:
    """Queue one Search replace status message for a completed replace command."""
    if st.session_state.get("_search_replace_status_cache_key") == cache_key:
        return
    st.session_state["_search_replace_status_cache_key"] = cache_key
    push_floating_status(search_replace_status_message(replaced_count), "info")


def increase_search_visible_count() -> None:
    """Increase the number of visible Search results by one page."""
    visible_count = int(
        st.session_state.get("search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE)
    )
    st.session_state["search_visible_count"] = (
        visible_count + hhs_ui_constants.SEARCH_PAGE_SIZE
    )


def visible_search_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return the Search rows currently visible for incremental rendering."""
    visible_count = int(
        st.session_state.get("search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE)
    )
    if visible_count < hhs_ui_constants.SEARCH_PAGE_SIZE:
        visible_count = hhs_ui_constants.SEARCH_PAGE_SIZE
    st.session_state["search_visible_count"] = visible_count
    return rows[:visible_count]


def render_search_load_more(total_count: int) -> None:
    """Render the Search load-more control when hidden rows remain."""
    visible_count = int(
        st.session_state.get("search_visible_count", hhs_ui_constants.SEARCH_PAGE_SIZE)
    )
    if visible_count >= total_count:
        render_search_auto_load_more_cleanup()
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


def render_search_auto_load_more_cleanup() -> None:
    """Detach browser-side Search auto loading when no hidden rows remain."""
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            if (parentWindow.__hhsSearchAutoLoadCleanup) {
              parentWindow.__hhsSearchAutoLoadCleanup();
            }
            delete parentWindow.__hhsSearchAutoLoadCleanup;
            delete parentWindow.__hhsSearchAutoLoadController;
          })();
        </script>
        """,
        height=0,
    )


def render_search_auto_load_more(displayed_count: int, total_count: int) -> None:
    """Attach browser-side auto loading for Search results at page bottom."""
    render_token = json.dumps(f"{displayed_count}:{total_count}")
    render_script_html(
        """
        <script>
          (() => {
            const parentWindow = window.parent;
            const doc = parentWindow.document;
            const renderToken = __HHS_SEARCH_AUTO_LOAD_TOKEN__;
            const tokenParts = String(renderToken).split(":");
            const displayedCount = Number.parseInt(tokenParts[0] || "0", 10) || 0;
            const totalCount = Number.parseInt(tokenParts[1] || "0", 10) || 0;
            const activeController = parentWindow.__hhsSearchAutoLoadController;
            if (
              activeController
              && activeController.totalCount === totalCount
              && activeController.displayedCount > displayedCount
            ) {
              return;
            }
            if (parentWindow.__hhsSearchAutoLoadCleanup) {
              parentWindow.__hhsSearchAutoLoadCleanup();
            }
            const buttonSelector = ".st-key-search_load_more_button button";
            const loadingMarkup = `
              <span class="hhs-search-load-more-preloader">
                <span class="hhs-search-load-more-preloader-spinner" aria-hidden="true"></span>
                <span class="hhs-search-load-more-preloader-label">Loading more results...</span>
              </span>
            `;
            let requested = false;
            let userReachedBottom = false;
            const componentFrame = window.frameElement;
            const loadMoreContainer = doc.querySelector(".st-key-search_load_more");
            const sentinel = loadMoreContainer || componentFrame;
            const bottomThreshold = 12;
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
            const nearBottom = () => {
              const target = doc.querySelector(buttonSelector) || sentinel;
              if (!target || typeof target.getBoundingClientRect !== "function") {
                return false;
              }
              const rect = target.getBoundingClientRect();
              const viewportHeight =
                parentWindow.innerHeight || doc.documentElement.clientHeight || 0;
              return rect.top <= viewportHeight - bottomThreshold && rect.bottom >= bottomThreshold;
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
              if (!force && !userReachedBottom) {
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
              userReachedBottom = nearBottom();
              if (!userReachedBottom) {
                return;
              }
              parentWindow.requestAnimationFrame(loadMore);
            };
            const onResize = () => {
              parentWindow.requestAnimationFrame(loadMore);
            };
            let observer = null;
            bindButton();
            if (sentinel && parentWindow.IntersectionObserver) {
              observer = new parentWindow.IntersectionObserver(
                (entries) => {
                  if (userReachedBottom && entries.some((entry) => entry.isIntersecting)) {
                    loadMore(true);
                  }
                },
                { root: null, rootMargin: "0px", threshold: 0.25 }
              );
              observer.observe(sentinel);
            }
            scrollTargets.forEach((target) => {
              target.addEventListener("scroll", onScroll, { passive: true });
            });
            parentWindow.addEventListener("resize", onResize, { passive: true });
            const cleanup = () => {
              if (observer) {
                observer.disconnect();
              }
              scrollTargets.forEach((target) => {
                target.removeEventListener("scroll", onScroll);
              });
              parentWindow.removeEventListener("resize", onResize);
            };
            parentWindow.__hhsSearchAutoLoadCleanup = cleanup;
            parentWindow.__hhsSearchAutoLoadController = {
              cleanup,
              displayedCount,
              totalCount,
            };
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


def path_variable_names(path_value: str) -> list[str]:
    """Return shell variable names referenced by a path-like value."""
    names = set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", path_value))
    names.update(re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", path_value))
    return sorted(names)


def expand_path_with_environment(
    path_value: str, environment_values: dict[str, str]
) -> str:
    """Expand tilde and shell variables in a path-like value."""
    expanded_path = path_value.strip()
    home_directory = environment_values.get("HOME", "")
    if expanded_path == "~":
        expanded_path = home_directory or expanded_path
    elif expanded_path.startswith("~/") and home_directory:
        expanded_path = f"{home_directory}/{expanded_path[2:]}"

    def replace_variable(match: re.Match[str]) -> str:
        """Return the environment value for one matched variable token."""
        name = match.group(1) or match.group(2)
        return environment_values.get(name, match.group(0))

    expanded_path = re.sub(
        r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)",
        replace_variable,
        expanded_path,
    )
    if expanded_path.startswith("/"):
        return posixpath.normpath(expanded_path)
    return expanded_path


def build_remote_environment_values_command(variable_names: list[str]) -> str:
    """Build a shell command that prints selected remote environment values."""
    safe_names = [
        name for name in variable_names if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
    ]
    commands = ['printf "__HHS_UI_ENV__\\n"']
    for name in safe_names:
        commands.append(f'printf "%s\\t%s\\n" {shlex.quote(name)} "${{{name}-}}"')
    return "; ".join(commands)


def parse_remote_environment_values(output: str) -> dict[str, str]:
    """Parse marked remote environment output into name/value pairs."""
    clean_output = strip_ansi(output or "").replace("\r", "")
    marker = "__HHS_UI_ENV__"
    marker_index = clean_output.rfind(marker)
    if marker_index < 0:
        return {}
    values: dict[str, str] = {}
    for line in clean_output[marker_index + len(marker) :].splitlines():
        if "\t" not in line:
            continue
        name, value = line.split("\t", 1)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            values[name] = value
    return values


def remote_environment_values(variable_names: list[str]) -> dict[str, str]:
    """Return selected environment values from the connected SSH host."""
    host = connected_ssh_host()
    if not host:
        return {}
    safe_names = sorted(
        {
            name
            for name in variable_names
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
        }
    )
    if not safe_names:
        return {}
    cache_key = f"_hhs_remote_environment_values:{host}:{','.join(safe_names)}"
    cached_values = st.session_state.get(cache_key)
    if isinstance(cached_values, dict):
        return {str(name): str(value) for name, value in cached_values.items()}
    result = run_bash_command(
        build_remote_environment_values_command(safe_names),
        "Resolving remote environment...",
        timeout_seconds=10,
        cache_tag="system",
    )
    values = parse_remote_environment_values(
        result.stdout if result.returncode == 0 else ""
    )
    st.session_state[cache_key] = values
    return values


def expand_path_for_active_host(path_value: str) -> str:
    """Expand path variables against the active local or SSH host."""
    clean_path = path_value.strip()
    if not connected_ssh_host():
        expanded_path = os.path.expandvars(os.path.expanduser(clean_path))
        return (
            posixpath.normpath(expanded_path)
            if expanded_path.startswith("/")
            else expanded_path
        )
    variable_names = path_variable_names(clean_path)
    if clean_path == "~" or clean_path.startswith("~/") or "HOME" in variable_names:
        variable_names.append("HOME")
    environment_values = remote_environment_values(variable_names)
    return expand_path_with_environment(clean_path, environment_values)


def default_search_directory() -> str:
    """Return the expanded default directory for Search controls."""
    if connected_ssh_host():
        expanded_home = expand_path_for_active_host("$HOME")
        if "$" not in expanded_home and expanded_home:
            return expanded_home
        return footer_working_directory() or "."
    return str(Path.home().resolve())


def search_host_context() -> str:
    """Return the active execution host context key for Search state."""
    host = connected_ssh_host()
    return f"ssh:{host}" if host else "local"


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
    clean_path = clean_recent_search_value(search_path)
    clean_path = (
        expand_path_for_active_host(clean_path)
        if clean_path
        else default_search_directory()
    )
    st.session_state["search_path"] = clean_path
    st.session_state["_hhs_search_home_context"] = search_host_context()
    st.session_state["search_directories"] = normalize_search_directories(
        st.session_state.get("search_directories", []),
        clean_path,
    )
    return clean_path


def reset_search_directory_to_home(clear_results: bool = True) -> str:
    """Reset the Search directory state to the active host home directory."""
    search_path = remember_search_directory(default_search_directory())
    st.session_state["_hhs_search_home_context"] = search_host_context()
    if clear_results:
        st.session_state["search_result_path"] = search_path
        st.session_state["search_result_query"] = ""
        st.session_state["search_visible_count"] = hhs_ui_constants.SEARCH_PAGE_SIZE
    return search_path


def queue_search_directory_home_reset(clear_results: bool = True) -> None:
    """Queue a Search directory reset for the next pre-widget render phase."""
    st.session_state["_hhs_search_directory_home_reset_pending"] = True
    st.session_state["_hhs_search_directory_home_reset_clear_results"] = bool(
        clear_results
    )


def apply_pending_search_directory_home_reset() -> None:
    """Apply a queued Search directory reset before Search widgets render."""
    if not st.session_state.pop("_hhs_search_directory_home_reset_pending", False):
        st.session_state.pop("_hhs_search_directory_home_reset_clear_results", None)
        return
    clear_results = bool(
        st.session_state.pop(
            "_hhs_search_directory_home_reset_clear_results",
            True,
        )
    )
    reset_search_directory_to_home(clear_results=clear_results)


def initialize_search_directory_home_default() -> None:
    """Ensure Search starts at home for the current host context."""
    current_context = search_host_context()
    search_path = clean_recent_search_value(st.session_state.get("search_path", ""))
    if search_path:
        st.session_state["search_path"] = search_path
        st.session_state["_hhs_search_home_context"] = current_context
        return
    reset_search_directory_to_home()


def search_directory_options() -> list[str]:
    """Return Search directory select options including the current value."""
    remember_search_directory(st.session_state.get("search_path", ""))
    return list(st.session_state.get("search_directories", []))


def apply_search_directory_change() -> None:
    """Persist Search directory changes without submitting a Search."""
    search_path = remember_search_directory(st.session_state.get("search_path", ""))
    st.session_state["search_result_path"] = search_path
    st.session_state["search_result_query"] = ""
    st.session_state["search_visible_count"] = hhs_ui_constants.SEARCH_PAGE_SIZE
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
    """Return Search term select options without selecting a value by default."""
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
    if state_key == "search_replace" and st.session_state[state_key]:
        st.session_state["search_words"] = False
    elif state_key == "search_words" and st.session_state[state_key]:
        st.session_state["search_replace"] = False
    save_ui_state()


def apply_search_type_change() -> None:
    """Normalize Search kind changes and clear incompatible Search options."""
    search_type = normalized_search_type(st.session_state.get("search_type"))
    st.session_state["search_type"] = search_type
    if search_type != "Strings":
        st.session_state["search_replace"] = False
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


def submit_search_query(replace_requested: bool = False) -> None:
    """Persist the Search form values that should be executed."""
    query = clean_search_term_value(st.session_state.get("search_query", ""))
    search_path = clean_recent_search_value(st.session_state.get("search_path", ""))
    if not search_path:
        search_path = default_search_directory()
    search_path = remember_search_directory(search_path)
    if not query:
        st.session_state["search_result_query"] = ""
        push_floating_status("Enter a search query before searching.", "warn")
        save_ui_state()
        return
    query = remember_search_term(query)
    search_type = normalized_search_type(st.session_state.get("search_type"))
    replace = bool(replace_requested) and search_type == "Strings" and bool(
        st.session_state.get("search_replace", False)
    )
    replacement = str(st.session_state.get("search_replacement", "")) if replace else ""
    if replace and replacement == "":
        push_floating_status("Enter replacement text before replacing.", "warn")
        save_ui_state()
        return
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
    st.session_state["search_result_replace"] = replace
    st.session_state["search_result_replacement"] = replacement
    st.session_state["search_visible_count"] = hhs_ui_constants.SEARCH_PAGE_SIZE
    if replace:
        st.session_state["_search_replace_status_cache_key"] = ""
    cache_delete_tag("search")
    save_ui_state()


def render_search_controls() -> None:
    """Render the Search controls in one compact row."""
    with st.container(key="search_controls"):
        kind_column, path_column, picker_column, term_column, search_column = (
            st.columns([1.15, 3.0, 0.22, 3.0, 0.22], vertical_alignment="bottom")
        )
        with kind_column:
            st.selectbox(
                "Kind",
                options=hhs_ui_constants.SEARCH_TYPES,
                key="search_type",
                format_func=search_type_label,
                on_change=apply_search_type_change,
            )
        with path_column:
            st.selectbox(
                "Search directory",
                options=search_directory_options(),
                key="search_path",
                accept_new_options=True,
                on_change=apply_search_directory_change,
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
        with search_column:
            st.button(
                "",
                key="search_submit_button",
                help="Search",
                on_click=submit_search_query,
                width="stretch",
            )


def search_replace_enabled() -> bool:
    """Return whether the Search replace row should be visible."""
    return normalized_search_type(
        st.session_state.get("search_type")
    ) == "Strings" and bool(st.session_state.get("search_replace", False))


def render_search_replace_controls() -> None:
    """Render the Search replacement input row when replace mode is enabled."""
    if not search_replace_enabled():
        return
    with st.container(key="search_replace_controls"):
        label_column, replacement_column, replace_column = st.columns(
            [1.15, 6.22, 0.22],
            vertical_alignment="center",
        )
        with label_column:
            st.markdown(
                '<span class="hhs-search-replace-label">Replace by:</span>',
                unsafe_allow_html=True,
            )
        with replacement_column:
            st.text_input(
                "Replacement",
                key="search_replacement",
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder="Replacement string",
                width="stretch",
            )
        with replace_column:
            st.button(
                "",
                key="search_replace_submit_button",
                help="Search and Replace",
                on_click=submit_search_query,
                args=(True,),
                width="stretch",
            )


def selected_search_result_filter() -> str:
    """Return the active Search result table filter from Session State."""
    selected_filter = str(st.session_state.get("search_filter", "All") or "All")
    if selected_filter not in hhs_ui.SEARCH_FILTERS:
        return "All"
    return selected_filter


def selected_search_result_text_filter() -> str:
    """Return the active Search result text filter from Session State."""
    if selected_search_result_filter() != "Containing":
        return ""
    return clean_table_text_filter_value(
        st.session_state.get("search_other_filter", "")
    )


def render_search_filters() -> None:
    """Render Search result filters and store selections in Session State."""
    with st.container(key="search_filter_controls"):
        strings_selected = (
            normalized_search_type(st.session_state.get("search_type")) == "Strings"
        )
        if strings_selected:
            (
                filter_column,
                other_filter_column,
                replace_column,
                ignore_case_column,
                words_column,
                binary_column,
                clear_column,
            ) = st.columns(
                [1.15, 3.0, 0.22, 0.22, 0.22, 0.22, 0.22],
                vertical_alignment="center",
            )
        else:
            (
                filter_column,
                other_filter_column,
                ignore_case_column,
                words_column,
                binary_column,
                clear_column,
            ) = st.columns(
                [1.15, 3.0, 0.22, 0.22, 0.22, 0.22],
                vertical_alignment="center",
            )
        with filter_column:
            selected_filter = st.radio(
                "Table filter",
                hhs_ui.SEARCH_FILTERS,
                horizontal=True,
                index=None,
                key="search_filter",
                label_visibility="collapsed",
                on_change=save_ui_state,
            )
        other_filter = ""
        if selected_filter == "Containing":
            normalize_table_text_filter_state("search_other_filter")
            with other_filter_column:
                other_filter = st.text_input(
                    "Filters",
                    key="search_other_filter",
                    label_visibility="collapsed",
                    on_change=save_ui_state,
                    placeholder="Type result filter text",
                    width="stretch",
                )
        if strings_selected:
            with replace_column:
                render_search_option_toggle(
                    "search_replace",
                    "﯒",
                    "Show replacement controls",
                )
        with ignore_case_column:
            render_search_option_toggle("search_ignore_case", "Aa", "Ignore case (-i)")
        with words_column:
            render_search_option_toggle(
                "search_words",
                "",
                "Match words (-w)",
                disabled=bool(st.session_state.get("search_replace", False)),
            )
        with binary_column:
            render_search_option_toggle(
                "search_binary", "", "Search binary files (-b)"
            )
        with clear_column:
            st.button(
                "",
                key="search_other_filter_clear",
                help="Clear filter text",
                on_click=clear_table_other_filter,
                args=("search_other_filter",),
                disabled=not bool(clean_table_text_filter_value(other_filter)),
                width="stretch",
            )


def render_search_results() -> None:
    """Render the Search results table for the submitted query."""
    search_filter = selected_search_result_filter()
    text_filter = selected_search_result_text_filter()
    search_type = normalized_search_type(st.session_state.get("search_result_type"))
    search_path = str(st.session_state.get("search_result_path", "")).strip()
    query = str(st.session_state.get("search_result_query", "")).strip()
    if not query:
        return
    ignore_case = bool(st.session_state.get("search_result_ignore_case", False))
    words = bool(st.session_state.get("search_result_words", False))
    binary = bool(st.session_state.get("search_result_binary", False))
    replace = bool(st.session_state.get("search_result_replace", False))
    replacement = str(st.session_state.get("search_result_replacement", ""))
    command = build_hhs_search_command(
        search_type,
        query,
        search_path,
        ignore_case,
        words,
        binary,
        replace,
        replacement,
    )
    cache_key = search_command_cache_key(
        search_type,
        query,
        search_path,
        ignore_case,
        words,
        binary,
        replace,
        replacement,
    )
    loader_message = search_loader_message(query, search_path)
    result = complete_search_command_result(cache_key)
    if result is None:
        result = cached_search_command_result(command, cache_key)
    if result is None:
        if not background_job_is_running(
            SEARCH_COMMAND_JOB
        ) or not search_background_job_matches(cache_key):
            start_search_command(command, cache_key, loader_message)
        render_background_job_status(SEARCH_COMMAND_JOB, loader_message)
        return
    if result.returncode != 0:
        message = clean_command_status_message(result.stderr or result.stdout)
        push_floating_status(message or "Search command failed.", "error")
        return
    with st.container(key="search_results"):
        rows = parse_rows_cached(
            "search",
            f"{search_type}\n{search_path}\n{result.stdout}",
            lambda output: parse_hhs_search_results(
                output.split("\n", 2)[2], search_type, search_path
            ),
        )
        replaced_count = len(rows)
        if replace:
            push_search_replace_status(cache_key, replaced_count)
        rows = filter_search_rows(rows, search_filter, text_filter)
        visible_rows = visible_search_rows(rows)
        total_count = len(rows)
        if search_type == "Strings":
            render_search_string_results(visible_rows, query, text_filter, total_count)
            render_search_load_more(total_count)
            return
        render_search_path_results(visible_rows, search_type, total_count)
        render_search_load_more(total_count)


@st.fragment()
def render_search_panel() -> None:
    """Render Search controls and results with Session State communication."""
    render_background_job_status(SEARCH_OPEN_JOB)
    with st.expander("Search Parameters", expanded=True):
        render_search_controls()
        render_search_replace_controls()
        render_search_filters()
    render_folder_picker_dialog("search")
    render_search_results()


def render_search_view() -> None:
    """Render the HomeSetup Search view."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> Global Search</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_search_panel()


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
    execute_pending_ai_context_action()
    render_background_job_status(AI_CONTEXT_ACTION_JOB)
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
        render_view_subtitle("There is no chat history")
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
        if not submit_ai_chat_prompt(prompt, ollama_model, context_size):
            return
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
    execute_pending_ai_prompt_action()
    render_background_job_status(AI_PROMPT_ACTION_JOB)
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
    execute_pending_ai_context_action()
    render_background_job_status(AI_CONTEXT_ACTION_JOB)
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
        render_view_subtitle("AI context is clear")
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
    render_view_subtitle("Available Models")
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
        <section class="hhs-view-heading hhs-view-heading--with-tabs">
          <h2> Ask Ollama HomeSetup AI</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )
    ai_view = render_view_segmented_control(
        "AI view",
        hhs_ui.AI_VIEWS,
        "ai_view",
        "CHAT",
        format_func=ai_view_label,
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


def main() -> None:
    """Configure and render the HomeSetup Streamlit UI."""
    install_footer_status_log_handler()
    configure_path_picker_dependencies()
    selected_theme = persisted_theme_name()
    configure_app_font_theme(selected_theme)
    st.set_page_config(
        page_title=f"HomeSetup - UI v{hhs_ui.VERSION}",
        page_icon=str(hhs_ui.APP_FAVICON_FILE),
        layout="wide",
    )
    restore_ui_state()
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
    apply_pending_search_directory_home_reset()
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
    st.session_state.setdefault("home_tools_table_reset_counter", 0)
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
