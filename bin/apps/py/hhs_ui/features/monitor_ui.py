#!/usr/bin/env python3
"""History statistics and monitor view helpers for the HomeSetup Streamlit app."""

from __future__ import annotations

import html
import re
from collections.abc import Callable

import altair as alt
import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.cache_runtime import (
    parse_rows_cached,
    render_cached_command_result,
    rendered_log_output_cached,
)
from hhs_ui.execution.command_catalog import (
    build_hhs_history_stats_command,
    build_hhs_logs_command,
    clean_command_status_message,
    normalized_history_stats_top_n,
    normalized_monitor_disk_top_n,
    normalized_monitor_log_tail_lines,
    normalized_monitor_top_n,
    parse_hhs_disk_usage,
    parse_hhs_history_stats,
    parse_hhs_process_list,
    strip_ansi,
)
from hhs_ui.execution.command_runtime import background_job_is_running, render_background_job_status
from hhs_ui.widgets.feedback_ui import render_command_loader, render_terminal_output
from hhs_ui.features.monitor_runtime import (
    applied_monitor_disk_directory,
    apply_monitor_disk_controls,
    apply_monitor_process_controls,
    build_hhs_disk_usage_command,
    cached_monitor_metric_result,
    cached_monitor_process_list_result,
    clear_monitor_log_file,
    complete_monitor_metric_refresh,
    complete_monitor_process_list_refresh,
    handle_monitor_disk_top_n_change,
    handle_monitor_log_tail_lines_change,
    handle_monitor_process_top_n_change,
    monitor_disk_display_directory,
    monitor_log_level_label,
    monitor_metric_job_name,
    monitor_process_top_n_input_key,
    monitor_process_top_n_state_key,
    normalize_monitor_log_tail_lines_state,
    normalized_monitor_process_top_n,
    refresh_history_stats_chart,
    relative_disk_usage_path,
    selected_monitor_log_level,
    start_monitor_metric_refresh,
    start_monitor_process_list_refresh,
    toggle_monitor_logs_tail,
)
from hhs_ui.core.paths import hhs_log_dir, hhs_log_file_info, hhs_log_files
from hhs_ui.widgets.table_ui import (
    plot_chart,
    render_chart_controls,
    render_standard_number_spinner,
    render_table,
    render_table_controls_panel,
    render_table_filter_controls,
)
from hhs_ui.core.ui_definitions import MONITOR_PROCESS_ACTION_JOB, MONITOR_PROCESS_LIST_JOB
from hhs_ui.core.ui_state import save_ui_state


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"monitor UI dependency is not configured: {name}")

    return dependency


apply_selected_process_kill = _unconfigured_dependency("apply_selected_process_kill")
execute_pending_monitor_process_action = _unconfigured_dependency(
    "execute_pending_monitor_process_action"
)
filter_process_rows = _unconfigured_dependency("filter_process_rows")
process_monitor_chart_rows = _unconfigured_dependency("process_monitor_chart_rows")
render_openable_file_pill = _unconfigured_dependency("render_openable_file_pill")
render_persisted_expander_state_script = _unconfigured_dependency(
    "render_persisted_expander_state_script"
)


def configure_monitor_ui(
    *,
    apply_selected_process_kill: Callable[[str], None],
    execute_pending_monitor_process_action: Callable[[], None],
    filter_process_rows: Callable[..., list[dict[str, str]]],
    process_monitor_chart_rows: Callable[..., list[dict[str, float | str]]],
    render_openable_file_pill: Callable[[str, str], None],
    render_persisted_expander_state_script: Callable[[str, str], None],
) -> None:
    """Configure callbacks supplied by the root Streamlit UI module."""
    globals().update(
        {
            "apply_selected_process_kill": apply_selected_process_kill,
            "execute_pending_monitor_process_action": execute_pending_monitor_process_action,
            "filter_process_rows": filter_process_rows,
            "process_monitor_chart_rows": process_monitor_chart_rows,
            "render_openable_file_pill": render_openable_file_pill,
            "render_persisted_expander_state_script": render_persisted_expander_state_script,
        }
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
            help="Set how many recent log lines to display.",
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
                    help="Choose the log file to display.",
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
                    help="Filter entries by minimum log severity.",
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
    log_file_path = hhs_log_file_info(selected_log)[0]
    render_openable_file_pill("Selected log file:", log_file_path)
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
