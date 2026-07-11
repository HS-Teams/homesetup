#!/usr/bin/env python3
"""SSH explorer and tunnel panels for the HomeSetup Streamlit app."""

from __future__ import annotations

import os
import posixpath
import shlex
import subprocess
import textwrap
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.cache_runtime import (
    cache_background_command_result,
    cache_delete_tag,
    cached_background_command_result,
    cached_command_job_name,
    render_cached_command_result,
    start_cached_background_command,
)
from hhs_ui.execution.command_catalog import (
    build_port_reachability_command,
    build_ssh_tunnels_command,
    display_ssh_tunnel_rows,
    filter_ssh_tunnel_rows,
    local_port_is_reachable,
    parse_ssh_tunnels,
    split_bind_address,
    ssh_tunnel_status_cell_style,
    strip_ansi,
)
from hhs_ui.execution.command_runtime import (
    background_job_is_running,
    background_job_result,
    background_job_state,
    render_background_job_status,
    run_bash_command,
    start_background_bash_command,
)
from hhs_ui.widgets.dialog_ui import pop_dialog
from hhs_ui.widgets.feedback_ui import render_command_loader
from hhs_ui.features.ssh_core import ssh_config_option, ssh_control_path
from hhs_ui.features.ssh_runtime import connected_ssh_host
from hhs_ui.widgets.status_ui import push_floating_status
from hhs_ui.widgets.table_ui import (
    display_table_rows,
    render_table,
    render_table_controls_panel,
    render_table_filter_controls,
    resolve_css_custom_property,
    table_height,
)
from hhs_ui.core.theme_assets import theme_custom_properties
from hhs_ui.core.ui_definitions import (
    SSH_EXPLORER_ACTION_JOB,
    SSH_EXPLORER_DELETE_JOB,
    SSH_FILE_TRANSFER_JOB,
)
from hhs_ui.core.ui_state import save_ui_state


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"SSH explorer UI dependency is not configured: {name}")

    return dependency


start_background_action_job = _unconfigured_dependency("start_background_action_job")
render_view_segmented_control = _unconfigured_dependency(
    "render_view_segmented_control"
)


def configure_ssh_explorer_ui(
    *,
    start_background_action_job: Callable[..., bool],
    render_view_segmented_control: Callable[..., str],
) -> None:
    """Configure callbacks required by SSH explorer helpers."""
    globals().update(
        {
            "start_background_action_job": start_background_action_job,
            "render_view_segmented_control": render_view_segmented_control,
        }
    )


def run_ssh_tunnels(host: str) -> subprocess.CompletedProcess[str]:
    """Run the SSH tunnel listing command and return the completed process."""
    return run_bash_command(
        build_ssh_tunnels_command(host),
        "Loading SSH tunnels...",
        cache_tag="ssh",
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
