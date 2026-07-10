#!/usr/bin/env python3
"""Monitor state and command runtime helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import os
import re
import shlex
import subprocess

import streamlit as st

import hhs_ui
import hhs_ui.constants as hhs_ui_constants
from hhs_ui.cache_runtime import (
    cache_delete_command,
    cache_delete_tag,
    cached_background_command_result,
    complete_cached_background_command,
    start_cached_background_command,
)
from hhs_ui.command_catalog import (
    build_hhs_history_stats_command,
    build_hhs_process_list_command,
    build_process_monitor_command,
    normalized_history_stats_top_n,
    normalized_monitor_disk_top_n,
    normalized_monitor_log_tail_lines,
    normalized_monitor_top_n,
    strip_ansi,
)
from hhs_ui.paths import hhs_log_file_path, hhs_log_files, homesetup_home
from hhs_ui.ssh_runtime import command_remote_host, connected_ssh_host
from hhs_ui.status_ui import push_floating_status
from hhs_ui.ui_definitions import (
    MONITOR_CPU_JOB,
    MONITOR_MEM_JOB,
    MONITOR_PROCESS_LIST_JOB,
)
from hhs_ui.ui_state import save_ui_state


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
