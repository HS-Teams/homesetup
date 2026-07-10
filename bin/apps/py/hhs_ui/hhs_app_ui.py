#!/usr/bin/env python3
"""HomeSetup application configuration views and action helpers."""

from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import shutil
import sys
import warnings
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import hhs_ui
import hhs_ui.constants as hhs_ui_constants
from hhs_ui.cache_runtime import (
    cache_delete_tag,
    parse_rows_cached,
    render_cached_command_result,
)
from hhs_ui.command_catalog import (
    build_hhs_firebase_alias_action_command,
    build_hhs_firebase_info_command,
    build_hhs_hspm_command,
    build_hhs_save_firebase_config_command,
    build_hhs_save_starship_config_command,
    build_hhs_settings_add_command,
    build_hhs_settings_delete_command,
    build_hhs_settings_delete_many_command,
    build_hhs_settings_list_command,
    build_hhs_settings_truncate_command,
    build_hhs_setup_apply_command,
    build_hhs_setup_restore_command,
    build_hhs_setup_settings_command,
    build_hhs_starship_info_command,
    build_hhs_starship_preset_command,
    clean_command_status_message,
    hhs_setting_variable_name,
    load_hhs_settings_defaults,
    normalize_hhs_firebase_value,
    parse_hhs_firebase_info,
    parse_hhs_settings_list,
    parse_hhs_setup_settings,
    parse_hhs_starship_info,
    render_hhs_firebase_config_content,
    strip_ansi,
)
from hhs_ui.command_runtime import (
    background_job_is_running,
    background_job_result,
    background_job_state,
    render_background_job_status,
)
from hhs_ui.feedback_ui import render_command_loader
from hhs_ui.paths import homesetup_config_dir, homesetup_home
from hhs_ui.search_ui import expand_path_with_environment
from hhs_ui.ssh_runtime import connected_ssh_host
from hhs_ui.status_ui import push_floating_status
from hhs_ui.table_ui import (
    render_markdown_table,
    render_table,
    resolve_css_custom_property,
)
from hhs_ui.theme_assets import theme_custom_properties
from hhs_ui.ui_definitions import (
    HHS_FIREBASE_ACTION_JOB,
    HHS_FIREBASE_FIELDS,
    HHS_HSPM_ACTION_JOB,
    HHS_SETTINGS_ACTION_JOB,
    HHS_SETUP_ACTION_JOB,
    HHS_SETUP_SETTINGS,
    HHS_STARSHIP_ACTION_JOB,
)
from hhs_ui.ui_state import save_ui_state


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"HHS application UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
render_openable_file_pill = _unconfigured_dependency("render_openable_file_pill")
render_view_segmented_control = _unconfigured_dependency(
    "render_view_segmented_control"
)
start_background_action_job = _unconfigured_dependency("start_background_action_job")
hhs_setup_file_path = _unconfigured_dependency("hhs_setup_file_path")
hhs_settings_table_key = _unconfigured_dependency("hhs_settings_table_key")
reset_hhs_settings_table_selection = _unconfigured_dependency(
    "reset_hhs_settings_table_selection"
)
hhs_hspm_catalog_table_key = _unconfigured_dependency("hhs_hspm_catalog_table_key")
refresh_hhs_hspm_catalog_listing = _unconfigured_dependency(
    "refresh_hhs_hspm_catalog_listing"
)


def configure_hhs_app_ui(
    *,
    render_script_html: Callable[..., None],
    render_openable_file_pill: Callable[[str, str], None],
    render_view_segmented_control: Callable[..., str],
    start_background_action_job: Callable[..., bool],
    hhs_setup_file_path: Callable[[], str],
    hhs_settings_table_key: Callable[[], str],
    reset_hhs_settings_table_selection: Callable[[], None],
    hhs_hspm_catalog_table_key: Callable[[], str],
    refresh_hhs_hspm_catalog_listing: Callable[[], None],
) -> None:
    """Configure callbacks supplied by the root Streamlit UI module."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "render_openable_file_pill": render_openable_file_pill,
            "render_view_segmented_control": render_view_segmented_control,
            "start_background_action_job": start_background_action_job,
            "hhs_setup_file_path": hhs_setup_file_path,
            "hhs_settings_table_key": hhs_settings_table_key,
            "reset_hhs_settings_table_selection": reset_hhs_settings_table_selection,
            "hhs_hspm_catalog_table_key": hhs_hspm_catalog_table_key,
            "refresh_hhs_hspm_catalog_listing": refresh_hhs_hspm_catalog_listing,
        }
    )


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
                st.session_state[hhs_ui_constants.HHS_STARSHIP_CURRENT_PRESET_KEY] = (
                    preset
                )
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


def hhs_hspm_action_noun(operation: str) -> str:
    """Return the display noun for an HSPM action."""
    return {
        "install": "Installation",
        "uninstall": "Uninstallation",
        "recover": "Recovery",
    }.get(operation, "Operation")


def hhs_hspm_package_summary(package_names: list[str]) -> str:
    """Return a compact package summary for action status messages."""
    clean_names = [name for name in package_names if name]
    if len(clean_names) <= 3:
        return ", ".join(clean_names)
    shown_names = ", ".join(clean_names[:3])
    return f"{shown_names}, +{len(clean_names) - 3} more"


def queue_hhs_hspm_catalog_action(operation: str, package_names: list[str]) -> bool:
    """Queue an HSPM catalog install or uninstall action."""
    clean_operation = operation if operation in {"install", "uninstall"} else ""
    clean_package_names = list(dict.fromkeys(name.strip() for name in package_names))
    clean_package_names = [name for name in clean_package_names if name]
    if not clean_operation or not clean_package_names:
        push_floating_status("Mark at least one package first.", "warn")
        return False
    package_summary = hhs_hspm_package_summary(clean_package_names)
    st.session_state["hhs_hspm_action_execute_pending"] = {
        "operation": clean_operation,
        "package_names": clean_package_names,
        "command": build_hhs_hspm_command(clean_operation, clean_package_names),
        "description": f"{hhs_hspm_action_noun(clean_operation)} of {package_summary}",
    }
    save_ui_state()
    return True


def queue_hhs_hspm_recovery_action(action: str) -> bool:
    """Queue a predefined HSPM recovery action."""
    recovery_actions = {
        "packages": ("-i", "Recovering packages"),
        "tools": ("-t", "Loading recovery tools"),
        "edit": ("-e", "Opening the recovery file"),
    }
    recovery_action = recovery_actions.get(action)
    if recovery_action is None:
        return False
    option, description = recovery_action
    st.session_state["hhs_hspm_action_execute_pending"] = {
        "operation": "recover",
        "command": build_hhs_hspm_command("recover", option),
        "description": description,
        "success_fallback": f"{description} completed.",
        "error_fallback": f"{description} failed.",
    }
    save_ui_state()
    return True


def start_pending_hhs_hspm_action() -> None:
    """Start a queued HSPM action background job, when present."""
    pending = st.session_state.pop("hhs_hspm_action_execute_pending", None) or {}
    if not isinstance(pending, dict):
        return
    command = str(pending.get("command", "")).strip()
    description = str(pending.get("description", "")).strip()
    if not command or not description:
        return
    started = start_background_action_job(
        HHS_HSPM_ACTION_JOB,
        command,
        description,
        hhs_ui_constants.UI_COMMAND_LONG_ACTION_TIMEOUT_SECONDS,
        pending,
        "Another HSPM action is already running.",
        show_preloader_event=False,
    )
    if not started:
        st.session_state["hhs_hspm_action_execute_pending"] = pending


def complete_hhs_hspm_action_job() -> None:
    """Complete an HSPM action and refresh its cached data."""
    completed = background_job_result(HHS_HSPM_ACTION_JOB)
    if completed is None:
        return
    result, metadata = completed
    package_names = [
        str(package_name).strip()
        for package_name in metadata.get("package_names", [])
        if str(package_name).strip()
    ]
    operation = str(metadata.get("operation", "")).strip()
    package_summary = hhs_hspm_package_summary(package_names)
    if result.returncode == 0:
        if operation == "recover":
            cache_delete_tag("hhs_hspm_recovery")
        else:
            refresh_hhs_hspm_catalog_listing()
    status_message = clean_command_status_message(result.stdout or result.stderr or "")
    if result.returncode == 0:
        fallback = str(metadata.get("success_fallback", "")).strip()
        if not fallback:
            fallback = f"{hhs_hspm_action_noun(operation)} completed: {package_summary}"
        push_floating_status(status_message or fallback, "info")
    else:
        fallback = str(metadata.get("error_fallback", "")).strip()
        if not fallback:
            fallback = f"{hhs_hspm_action_noun(operation)} failed: {package_summary}"
        push_floating_status(status_message or fallback, "error")
    save_ui_state()


def execute_pending_hhs_hspm_action() -> None:
    """Start or complete the current HSPM catalog action."""
    start_pending_hhs_hspm_action()
    complete_hhs_hspm_action_job()


def hhs_view_label(hhs_view: str) -> str:
    """Return the display label for a HomeSetup application view key."""
    return hhs_ui.HHS_VIEW_LABELS.get(hhs_view, hhs_view)


def hhs_hspm_os_name() -> str:
    """Return the OS name used by the HSPM catalog title."""
    raw_os_name = os.environ.get("HHS_MY_OS", "").strip()
    if not raw_os_name:
        try:
            raw_os_name = os.uname().sysname
        except AttributeError:
            raw_os_name = sys.platform
    return {
        "darwin": "Darwin",
        "linux": "Linux",
    }.get(raw_os_name.lower(), raw_os_name)


def hhs_hspm_os_glyph(os_name: str) -> str:
    """Return the display glyph for an HSPM OS name."""
    return {
        "Darwin": "",
        "Linux": "",
    }.get(os_name, "")


def hhs_hspm_catalog_title() -> str:
    """Return the HSPM catalog slide title with an OS glyph when known."""
    os_name = hhs_hspm_os_name()
    glyph = hhs_hspm_os_glyph(os_name)
    if not os_name:
        return "Catalog"
    if glyph:
        return f"{glyph} Catalog ({os_name})"
    return f"Catalog ({os_name})"


def hhs_hspm_package_manager_name() -> str:
    """Return the package manager name used by the HSPM recovery title."""
    package_manager = os.environ.get("HHS_MY_OS_PACKMAN", "").strip()
    if package_manager:
        return package_manager
    for package_manager in ("brew", "apt-get", "apt", "yum", "dnf", "apk"):
        if shutil.which(package_manager):
            return package_manager
    return ""


def hhs_hspm_recovery_title() -> str:
    """Return the HSPM recovery slide title with OS glyph and package manager."""
    glyph = hhs_hspm_os_glyph(hhs_hspm_os_name())
    package_manager = hhs_hspm_package_manager_name()
    title_prefix = f"{glyph} " if glyph else ""
    if package_manager:
        return f"{title_prefix}Recovery ({package_manager})"
    return f"{title_prefix}Recovery"


def hhs_hspm_recipe_file_path(package_name: str) -> Path | None:
    """Return the local recipe path for a package on the selected OS."""
    clean_package_name = package_name.strip()
    if (
        connected_ssh_host()
        or not clean_package_name
        or clean_package_name in {".", ".."}
        or Path(clean_package_name).name != clean_package_name
    ):
        return None
    recipe_path = (
        homesetup_home()
        / "bin/apps/bash/hhs-app/plugins/hspm/recipes"
        / hhs_hspm_os_name()
        / f"{clean_package_name}.recipe"
    )
    return recipe_path if recipe_path.is_file() else None


def slider_pane_theme() -> dict[str, str]:
    """Return CSS color tokens for reusable slider pane components."""
    theme_name = st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    properties = theme_custom_properties(theme_name)
    return {
        "background": resolve_css_custom_property(
            properties, "hhs-background", "#19181f"
        ),
        "field": resolve_css_custom_property(
            properties, "hhs-theme-secondary-background-color", "#221f2b"
        ),
        "text": resolve_css_custom_property(
            properties, "hhs-theme-text-color", "#fcfcfa"
        ),
        "border": resolve_css_custom_property(
            properties, "hhs-theme-dataframe-border-color", "#6c5f91"
        ),
        "primary": resolve_css_custom_property(
            properties, "hhs-theme-primary-color", "#bd93f9"
        ),
        "accent": resolve_css_custom_property(
            properties, "hhs-theme-link-color", "#8be9fd"
        ),
        "success": resolve_css_custom_property(properties, "hhs-success", "#50fa7b"),
        "danger": resolve_css_custom_property(properties, "hhs-danger", "#ff5555"),
        "muted": resolve_css_custom_property(
            properties, "hhs-theme-text-muted-color", "#a7a4b5"
        ),
    }


def slider_pane_state_key(key: str, suffix: str) -> str:
    """Return a stable Session State key for a slider pane value."""
    return f"{key}_{suffix}"


def slider_pane_active_index(key: str, page_count: int) -> int:
    """Return the active slider page index."""
    active_key = slider_pane_state_key(key, "active_index")
    try:
        active_index = int(st.session_state.get(active_key, 0))
    except (TypeError, ValueError):
        active_index = 0
    if active_index < 0 or active_index >= page_count:
        active_index = 0
        st.session_state[active_key] = active_index
    return active_index


def set_slider_pane_active_index(key: str, page_count: int, next_index: int) -> None:
    """Set the active slider page and remember transition direction."""
    if page_count <= 0:
        return
    active_key = slider_pane_state_key(key, "active_index")
    direction_key = slider_pane_state_key(key, "direction")
    current_index = slider_pane_active_index(key, page_count)
    normalized_index = next_index % page_count
    if normalized_index == current_index:
        return
    if normalized_index > current_index or (
        current_index == page_count - 1 and normalized_index == 0
    ):
        st.session_state[direction_key] = "right"
    else:
        st.session_state[direction_key] = "left"
    st.session_state[active_key] = normalized_index
    save_ui_state()


def move_slider_pane(key: str, page_count: int, step: int) -> None:
    """Move the slider page by one relative step."""
    set_slider_pane_active_index(
        key,
        page_count,
        slider_pane_active_index(key, page_count) + step,
    )


def slider_pane_css_class_key(key: str) -> str:
    """Return the Streamlit key class suffix for a slider pane element."""
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", key).strip("-") or "slider"


def render_slider_pane_styles(
    key: str,
    active_bullet_key: str,
    slide_key: str,
    direction: str,
    viewport_border: bool,
    navigation_offset: int,
    vertical_offset: int,
) -> None:
    """Render key-scoped CSS for a native Streamlit slider pane."""
    theme = slider_pane_theme()
    font_family = html.escape(hhs_ui_constants.APP_FONT_FAMILY)
    safe_key = slider_pane_css_class_key(key)
    active_bullet_class = slider_pane_css_class_key(active_bullet_key)
    slide_class = slider_pane_css_class_key(slide_key)
    animation_name = (
        "hhs-slider-slide-from-left"
        if direction == "left"
        else "hhs-slider-slide-from-right"
    )
    st.markdown(
        f"""
        <style>
          @keyframes hhs-slider-slide-from-left {{
            from {{ opacity: 0.55; transform: translateX(-1.75rem); }}
            to {{ opacity: 1; transform: translateX(0); }}
          }}

          @keyframes hhs-slider-slide-from-right {{
            from {{ opacity: 0.55; transform: translateX(1.75rem); }}
            to {{ opacity: 1; transform: translateX(0); }}
          }}

          .st-key-{safe_key} {{
            --hhs-slider-background: {html.escape(theme["background"])};
            --hhs-slider-field: {html.escape(theme["field"])};
            --hhs-slider-text: {html.escape(theme["text"])};
            --hhs-slider-border: {html.escape(theme["border"])};
            --hhs-slider-primary: {html.escape(theme["primary"])};
            --hhs-slider-muted: {html.escape(theme["muted"])};
            color: var(--hhs-slider-text);
            font-family: "{font_family}", monospace;
            font-size: 0.5rem;
            margin-top: {vertical_offset}px;
          }}

          .st-key-{safe_key},
          .st-key-{safe_key} * {{
            box-sizing: border-box;
            font-family: inherit;
          }}

          .st-key-{safe_key} [data-testid="stVerticalBlock"] {{
            gap: 1rem;
          }}

          .st-key-{safe_key}_viewport {{
            background: {"var(--hhs-slider-field)" if viewport_border else "transparent"};
            border: {"1px solid var(--hhs-slider-border)" if viewport_border else "0"};
            border-radius: {"6px" if viewport_border else "0"};
            overflow: hidden;
          }}

          .st-key-{safe_key}_slide_area {{
            height: 100%;
            min-height: 100%;
            overflow: visible;
            padding: 0;
            transform: none;
          }}

          .st-key-{safe_key}_slide_area [data-testid="stVerticalBlock"] {{
            gap: 1rem;
          }}

          .st-key-{safe_key}_catalog_table_layout {{
            margin-top: 0;
          }}

          .st-key-{slide_class} {{
            animation: {animation_name} 280ms cubic-bezier(0.22, 1, 0.36, 1);
            min-height: 100%;
            min-width: 0;
          }}

          .st-key-{safe_key} [data-testid="stDataEditor"],
          .st-key-{safe_key} [data-testid="stDataEditor"] * {{
            font-size: 0.5rem !important;
          }}

          .st-key-{safe_key} [data-testid="stDataEditor"] [role="columnheader"],
          .st-key-{safe_key} [data-testid="stDataEditor"] [role="gridcell"] {{
            font-size: 0.5rem !important;
          }}

          .st-key-{safe_key} button {{
            font-size: 0.5rem !important;
          }}

          .st-key-{safe_key} h3.hhs-slider-slide-title {{
            color: var(--hhs-slider-text);
            font-size: 0.9rem !important;
            font-weight: 800;
            line-height: 1.2;
            margin: 0 0 1rem;
            text-align: center;
          }}

          .st-key-{safe_key}_arrow_previous button,
          .st-key-{safe_key}_arrow_next button {{
            align-items: center;
            display: inline-flex;
            font-size: 0.5rem;
            font-weight: 800;
            height: 4rem !important;
            justify-content: center;
            line-height: 1;
            min-width: 2rem !important;
            padding: 0 !important;
            transform: translateY({navigation_offset}px);
            width: 2rem !important;
          }}

          .st-key-{safe_key}_bullets {{
            min-height: 1rem;
          }}

          .st-key-{safe_key}_bullets [data-testid="stHorizontalBlock"] {{
            align-items: center;
            justify-content: center;
          }}

          .st-key-{safe_key}_bullets [data-testid="stColumn"] {{
            align-items: center;
            display: flex;
            justify-content: center;
          }}

          .st-key-{safe_key}_bullets button {{
            background: var(--hhs-slider-muted) !important;
            border: 1px solid var(--hhs-slider-border) !important;
            border-radius: 999px !important;
            color: transparent !important;
            font-size: 0 !important;
            height: 0.6rem !important;
            min-height: 0.6rem !important;
            min-width: 0.6rem !important;
            padding: 0 !important;
            width: 0.6rem !important;
          }}

          .st-key-{active_bullet_class} button {{
            background: var(--hhs-slider-primary) !important;
            border-color: var(--hhs-slider-primary) !important;
            box-shadow: 0 0 0 2px
              color-mix(in srgb, var(--hhs-slider-primary) 30%, transparent);
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_slider_pane(
    key: str,
    pages: list[tuple[str, Callable[[], None]]],
    height: int = 470,
    viewport_border: bool = True,
    show_bullets: bool = True,
    navigation_offset: int = 0,
    vertical_offset: int = 0,
) -> None:
    """Render a reusable native Streamlit slider pane."""
    safe_key = re.sub(r"[^a-zA-Z0-9_-]+", "-", key).strip("-") or "slider"
    clean_pages = pages or [("", st.empty)]
    page_count = len(clean_pages)
    active_index = slider_pane_active_index(safe_key, page_count)
    direction = str(
        st.session_state.get(slider_pane_state_key(safe_key, "direction"), "right")
    )
    active_bullet_key = f"{safe_key}_bullet_{active_index}"
    slide_key = f"{safe_key}_slide_{active_index}_{direction}"
    height_px = max(int(height), 240)
    viewport_height = max(height_px - (32 if show_bullets else 0), 196)
    render_slider_pane_styles(
        safe_key,
        active_bullet_key,
        slide_key,
        direction,
        viewport_border,
        navigation_offset,
        vertical_offset,
    )
    with st.container(key=safe_key, height=height_px, border=False):
        with st.container(
            key=f"{safe_key}_viewport",
            height=viewport_height,
            border=viewport_border,
            horizontal=True,
            vertical_alignment="center",
            gap="small",
        ):
            with st.container(
                key=f"{safe_key}_arrow_previous",
                width=32,
            ):
                st.button(
                    "",
                    key=f"{safe_key}_previous_button",
                    help="Slide left",
                    on_click=move_slider_pane,
                    args=(safe_key, page_count, -1),
                    width=32,
                )
            with st.container(
                key=f"{safe_key}_slide_area",
                width="stretch",
                height="stretch",
            ):
                with st.container(key=slide_key):
                    clean_pages[active_index][1]()
            with st.container(
                key=f"{safe_key}_arrow_next",
                width=32,
            ):
                st.button(
                    "",
                    key=f"{safe_key}_next_button",
                    help="Slide right",
                    on_click=move_slider_pane,
                    args=(safe_key, page_count, 1),
                    width=32,
                )
        if show_bullets:
            render_slider_pane_bullets(
                safe_key,
                [page_title for page_title, _render_page in clean_pages],
            )


def render_slider_pane_bullets(key: str, page_titles: list[str]) -> None:
    """Render slider pagination bullets for the supplied page titles."""
    safe_key = slider_pane_css_class_key(key)
    page_count = len(page_titles)
    if page_count < 2:
        return
    with st.container(key=f"{safe_key}_bullets"):
        bullet_columns = st.columns(
            [1.0, *([0.025] * page_count), 1.0],
            gap="small",
            vertical_alignment="center",
        )
        for page_index, page_title in enumerate(page_titles):
            bullet_key = f"{safe_key}_bullet_{page_index}"
            with bullet_columns[page_index + 1]:
                with st.container(key=bullet_key):
                    st.button(
                        "•",
                        key=f"{bullet_key}_button",
                        help=f"Show {page_title}",
                        on_click=set_slider_pane_active_index,
                        args=(safe_key, page_count, page_index),
                        width=24,
                    )


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

    render_openable_file_pill("Current setup file:", hhs_setup_file_path())
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
                "ﮊ Truncate",
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
                result.stderr
                or result.stdout
                or "Unable to load overridden system settings."
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
            cache_col, preset_col, apply_col, edit_col = st.columns(
                [1.4, 1.1, 0.22, 0.22],
                gap="small",
                vertical_alignment="bottom",
            )
            with cache_col:
                st.text_input(
                    "Cache",
                    value=cache_path,
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
                result.stderr
                or result.stdout
                or "Unable to load Starship configuration."
            )
        )
        return

    starship_info = parse_hhs_starship_info(result.stdout)
    action_running = background_job_is_running(HHS_STARSHIP_ACTION_JOB)
    render_hhs_starship_controls(starship_info, action_running)
    render_openable_file_pill(
        "Current Starship file:",
        str(starship_info.get("config", "")).strip(),
    )
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
    for (
        _label,
        property_name,
        _fallback,
        state_key,
        _placeholder,
    ) in HHS_FIREBASE_FIELDS:
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
    for (
        _label,
        property_name,
        _fallback,
        state_key,
        _placeholder,
    ) in HHS_FIREBASE_FIELDS:
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
    for (
        _label,
        property_name,
        _fallback,
        state_key,
        _placeholder,
    ) in HHS_FIREBASE_FIELDS:
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


def hhs_firebase_creds_file_path(firebase_info: dict[str, object]) -> str:
    """Return the effective Firebase credentials file path for display."""
    raw_environment = firebase_info.get("environment", {})
    environment = (
        {str(name): str(value) for name, value in raw_environment.items()}
        if isinstance(raw_environment, dict)
        else {}
    )
    raw_path = environment.get("HHS_FIREBASE_CREDS_FILE", "").strip()
    if not raw_path:
        raw_path = "~/firebase-credentials.json"
    project_id = hhs_firebase_info_values(firebase_info).get("PROJECT_ID", "").strip()
    try:
        raw_path = raw_path.format(project_id=project_id)
    except (IndexError, KeyError, ValueError):
        pass
    return expand_path_with_environment(raw_path, environment)


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


def style_hhs_firebase_alias_row(row: pd.Series) -> list[str]:
    """Return dataframe row styles for Firebase alias metadata."""
    return [
        (
            "color: var(--hhs-secondary); font-weight: 800;"
            if column == "Group"
            else (
                "color: var(--hhs-theme-primary-color); font-weight: 800;"
                if column == "Alias"
                else ""
            )
        )
        for column in row.index
    ]


def render_hhs_firebase_aliases_table(action_running: bool) -> str:
    """Render the Firebase aliases table and return the selected alias."""
    alias_rows = firebase_alias_table_rows(fetch_firebase_aliases_with_preloader())
    with st.container(key="hhs_firebase_aliases_table_panel"):
        st.markdown(
            '<div class="hhs-table-caption">Firebase Aliases</div>',
            unsafe_allow_html=True,
        )
        _selected_index, selected_row = render_table(
            alias_rows,
            key="hhs_firebase_aliases_table",
            empty_hint="Select a Firebase alias.",
            headers=["Database", "Group", "Alias", "Count"],
            checkbox=not action_running,
            height=hhs_ui.ENV_TABLE_HEIGHT,
            row_style=style_hhs_firebase_alias_row,
        )
    return str(selected_row.get("Alias", "")) if selected_row else ""


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
            "value": normalize_hhs_firebase_value(st.session_state.get(state_key, "")),
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


def render_hhs_firebase_configurations(
    firebase_info: dict[str, object], action_running: bool
) -> None:
    """Render Firebase configuration fields and action buttons."""
    config_file = str(firebase_info.get("config_file", "")).strip()
    with st.container(key="hhs_firebase_configurations"):
        render_openable_file_pill("Current Firebase file:", config_file)
        with st.expander("Configurations", expanded=True):
            event = render_hhs_firebase_config_component(action_running)
        render_openable_file_pill(
            "Firebase credentials file:",
            hhs_firebase_creds_file_path(firebase_info),
        )
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
                result.stderr
                or result.stdout
                or "Unable to load Firebase configuration."
            )
        )
        return

    firebase_info = parse_hhs_firebase_info(result.stdout)
    sync_hhs_firebase_form_state(firebase_info)
    apply_pending_hhs_firebase_form_revert()
    action_running = background_job_is_running(HHS_FIREBASE_ACTION_JOB)
    render_hhs_firebase_configurations(firebase_info, action_running)


def render_hhs_hspm_title() -> None:
    """Render the HomeSetup package manager page title."""
    st.markdown(
        """
        <section class="hhs-view-heading hhs-view-heading--direct-content">
          <h2> Package Manager</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_hhs_hspm_slide_title(title: str) -> None:
    """Render a centered HSPM slider page title."""
    st.markdown(
        f'<h3 class="hhs-slider-slide-title">{html.escape(title)}</h3>',
        unsafe_allow_html=True,
    )


def parse_hhs_hspm_catalog(output: str) -> list[dict[str, str]]:
    """Parse HSPM list output into catalog table rows."""
    rows: list[dict[str, str]] = []
    for line in strip_ansi(output).splitlines():
        clean_line = line.strip()
        if "=>" not in clean_line:
            continue
        match = re.match(
            r"^\d+\s+(?P<recipe>[+-])\s+(?P<command>\S+)\s*\.{2,}\s*=>\s*(?P<description>.*)$",
            clean_line,
        )
        if match is None:
            match = re.match(
                r"^\d+\s+(?P<recipe>[+-])\s+(?P<command>\S+)\s+=>\s*(?P<description>.*)$",
                clean_line,
            )
        if match is None:
            continue
        rows.append(
            {
                "Command": match.group("command"),
                "Description": match.group("description").strip(),
                "CustomRecipe": match.group("recipe"),
            }
        )
    return rows


def hhs_hspm_catalog_table_data(
    rows: list[dict[str, str]],
) -> pd.io.formats.style.Styler:
    """Return styled HSPM catalog rows with the editable Mark column."""
    dataframe = pd.DataFrame(
        {
            "Mark": pd.Series([False] * len(rows), dtype="bool"),
            "Command": pd.Series(
                [row.get("Command", "") for row in rows],
                dtype="string",
            ),
            "Description": pd.Series(
                [row.get("Description", "") for row in rows],
                dtype="string",
            ),
        }
    )
    custom_commands = {
        row.get("Command", "") for row in rows if row.get("CustomRecipe") == "+"
    }
    accent_color = slider_pane_theme()["accent"]
    return dataframe.style.map(
        lambda value: (
            "font-size: 0.5rem; "
            + (
                f"color: {accent_color}; font-weight: 800;"
                if str(value) in custom_commands
                else ""
            )
        ),
        subset=["Command", "Description"],
    )


def selected_hhs_hspm_catalog_packages(edited_data: pd.DataFrame) -> list[str]:
    """Return package names marked in the HSPM catalog table."""
    if "Mark" not in edited_data or "Command" not in edited_data:
        return []
    selected_rows = edited_data[edited_data["Mark"].astype(bool)]
    return [
        str(command).strip()
        for command in selected_rows["Command"].tolist()
        if str(command).strip()
    ]


def parse_hhs_hspm_recovery(output: str) -> list[dict[str, str]]:
    """Parse HSPM recovery output into package status table rows."""
    rows: list[dict[str, str]] = []
    status_pattern = re.compile(
        r"^\s*\d+\s*-\s*(?P<command>\S+).*?\s+(?P<status>NOT INSTALLED|INSTALLED)\s*$"
    )
    normalized_output = strip_ansi(output)
    for line in normalized_output.splitlines():
        match = status_pattern.match(line)
        if match is None:
            continue
        rows.append(
            {
                "Command": match.group("command"),
                "Status": match.group("status"),
            }
        )
    return rows


def hhs_hspm_recovery_table_data(
    rows: list[dict[str, str]],
) -> pd.io.formats.style.Styler:
    """Return recovery rows with theme-aware status colors."""
    dataframe = pd.DataFrame(
        {
            "Command": pd.Series(
                [row.get("Command", "") for row in rows],
                dtype="string",
            ),
            "Status": pd.Series(
                [row.get("Status", "") for row in rows],
                dtype="string",
            ),
        }
    )
    theme = slider_pane_theme()
    return dataframe.style.map(
        lambda value: (
            f"color: {theme['success']}; font-weight: 800;"
            if str(value) == "INSTALLED"
            else (
                f"color: {theme['danger']}; font-weight: 800;"
                if str(value) == "NOT INSTALLED"
                else ""
            )
        ),
        subset=["Status"],
    )


def render_hhs_hspm_catalog_action_buttons(
    selected_package_names: list[str],
    action_running: bool,
) -> None:
    """Render centered HSPM catalog action buttons."""
    disabled = action_running or not selected_package_names
    with st.container(
        key="hhs_hspm_catalog_actions",
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center",
    ):
        install_clicked = st.button(
            "Install",
            key="hhs_hspm_catalog_install_button",
            disabled=disabled,
            width=180,
        )
        uninstall_clicked = st.button(
            "Uninstall",
            key="hhs_hspm_catalog_uninstall_button",
            disabled=disabled,
            width=180,
        )
    if install_clicked:
        if queue_hhs_hspm_catalog_action("install", selected_package_names):
            st.rerun()
    elif uninstall_clicked:
        if queue_hhs_hspm_catalog_action("uninstall", selected_package_names):
            st.rerun()


def render_hhs_hspm_recovery_action_buttons(action_running: bool) -> None:
    """Render the predefined HSPM recovery action buttons."""
    with st.container(
        key="hhs_hspm_recovery_actions",
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center",
    ):
        packages_clicked = st.button(
            " Install Pkgs.",
            key="hhs_hspm_recovery_packages_button",
            disabled=action_running,
            width=180,
        )
        tools_clicked = st.button(
            " Install Tools",
            key="hhs_hspm_recovery_tools_button",
            disabled=action_running,
            width=180,
        )
        edit_clicked = st.button(
            " Edit",
            key="hhs_hspm_recovery_edit_button",
            disabled=action_running,
            width=180,
        )
    for action, clicked in (
        ("packages", packages_clicked),
        ("tools", tools_clicked),
        ("edit", edit_clicked),
    ):
        if clicked and queue_hhs_hspm_recovery_action(action):
            st.rerun()


def render_hhs_hspm_catalog_slide() -> None:
    """Render the HSPM catalog slider page."""
    render_hhs_hspm_slide_title(hhs_hspm_catalog_title())
    result = render_cached_command_result(
        build_hhs_hspm_command("list"),
        "Loading HSPM catalog",
        "hhs_hspm_catalog",
        hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to load HSPM catalog.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr or result.stdout or "Unable to load HSPM catalog."
            )
        )
        return
    rows = parse_rows_cached("hhs_hspm_catalog", result.stdout, parse_hhs_hspm_catalog)
    if not rows:
        st.caption("No HSPM packages found.")
        return
    action_running = background_job_is_running(HHS_HSPM_ACTION_JOB)
    with st.container(key="hhs_hspm_slider_catalog_table_layout"):
        if action_running:
            action_job = background_job_state(HHS_HSPM_ACTION_JOB) or {}
            metadata = action_job.get("metadata", {})
            metadata = metadata if isinstance(metadata, dict) else {}
            operation = str(metadata.get("operation", "operation")).strip()
            package_names = [
                str(package_name).strip()
                for package_name in metadata.get("package_names", [])
                if str(package_name).strip()
            ]
            action_message = (
                f"{hhs_hspm_action_noun(operation)} in progress: "
                f"{hhs_hspm_package_summary(package_names)}"
            )
            action_status = st.status(
                action_message,
                state="running",
                expanded=False,
            )
            action_status.write("The Catalog is locked until the operation completes.")
        edited_data = st.data_editor(
            hhs_hspm_catalog_table_data(rows),
            key=hhs_hspm_catalog_table_key(),
            hide_index=True,
            column_order=["Mark", "Command", "Description"],
            height=304,
            disabled=["Command", "Description"] if not action_running else True,
            column_config={
                "Mark": st.column_config.CheckboxColumn(
                    "Mark",
                    disabled=action_running,
                    width=80,
                ),
                "Command": st.column_config.TextColumn(
                    "Command",
                    disabled=True,
                ),
                "Description": st.column_config.TextColumn(
                    "Description",
                    disabled=True,
                ),
            },
            width="stretch",
        )
    render_slider_pane_bullets("hhs_hspm_slider", ["Catalog", "Recovery"])
    render_hhs_hspm_catalog_action_buttons(
        selected_hhs_hspm_catalog_packages(edited_data),
        action_running,
    )


def render_hhs_hspm_recovery_slide() -> None:
    """Render the HSPM package recovery slider page."""
    render_hhs_hspm_slide_title(hhs_hspm_recovery_title())
    result = render_cached_command_result(
        build_hhs_hspm_command("recover"),
        "Loading HSPM recovery packages",
        "hhs_hspm_recovery",
        hhs_ui.UI_CACHE_LOW_CHANGE_TTL_SECONDS,
        hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        "Unable to load HSPM recovery packages.",
    )
    if result is None:
        return
    if result.returncode != 0:
        st.error(
            clean_command_status_message(
                result.stderr
                or result.stdout
                or "Unable to load HSPM recovery packages."
            )
        )
        return
    rows = parse_rows_cached(
        "hhs_hspm_recovery",
        result.stdout,
        parse_hhs_hspm_recovery,
    )
    action_running = background_job_is_running(HHS_HSPM_ACTION_JOB)
    with st.container(key="hhs_hspm_slider_recovery_table_layout"):
        st.data_editor(
            hhs_hspm_recovery_table_data(rows),
            key="hhs_hspm_recovery_table",
            hide_index=True,
            column_order=["Command", "Status"],
            height=304,
            disabled=True,
            column_config={
                "Command": st.column_config.TextColumn("Command", disabled=True),
                "Status": st.column_config.TextColumn("Status", disabled=True),
            },
            width="stretch",
        )
    render_slider_pane_bullets("hhs_hspm_slider", ["Catalog", "Recovery"])
    render_hhs_hspm_recovery_action_buttons(action_running)


def render_hhs_hspm_panel() -> None:
    """Render the HomeSetup package manager panel."""
    with st.container(key="hhs_hspm_panel", border=False):
        execute_pending_hhs_hspm_action()
        render_hhs_hspm_title()
        render_slider_pane(
            "hhs_hspm_slider",
            [
                ("Catalog", render_hhs_hspm_catalog_slide),
                ("Recovery", render_hhs_hspm_recovery_slide),
            ],
            height=450,
            viewport_border=False,
            show_bullets=False,
            navigation_offset=-30,
            vertical_offset=-16,
        )


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
    elif hhs_view == "HSPM":
        render_hhs_hspm_panel()
    elif hhs_view == "Firebase":
        render_hhs_firebase_panel()
    else:
        render_hhs_placeholder_panel(hhs_view)
