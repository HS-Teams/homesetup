#!/usr/bin/env python3
"""Reusable Streamlit path-picker helpers for HomeSetup."""

from __future__ import annotations

import hashlib
import html
import os
import posixpath
import shlex
import textwrap
from collections.abc import Callable
from pathlib import Path

import streamlit as st

import hhs_ui
import hhs_ui.constants as hhs_ui_constants
from hhs_ui.command_catalog import clean_command_status_message, strip_ansi
from hhs_ui.ui_definitions import (
    PATH_PICKER_LISTING_JOB_PREFIX,
    PATH_PICKER_LISTING_LOADER_MESSAGE,
)


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"path picker dependency is not configured: {name}")

    return dependency


connected_ssh_host = _unconfigured_dependency("connected_ssh_host")
background_job_state_key = _unconfigured_dependency("background_job_state_key")
stop_background_jobs_with_state_prefix = _unconfigured_dependency(
    "stop_background_jobs_with_state_prefix"
)
background_job_result = _unconfigured_dependency("background_job_result")
background_job_is_running = _unconfigured_dependency("background_job_is_running")
start_background_bash_command = _unconfigured_dependency("start_background_bash_command")
push_floating_status = _unconfigured_dependency("push_floating_status")
render_background_job_status = _unconfigured_dependency("render_background_job_status")
clear_preloader = _unconfigured_dependency("clear_preloader")


def configure_path_picker(
    *,
    connected_ssh_host: Callable[[], str],
    background_job_state_key: Callable[[str], str],
    stop_background_jobs_with_state_prefix: Callable[[str], None],
    background_job_result: Callable[[str], object],
    background_job_is_running: Callable[[str], bool],
    start_background_bash_command: Callable[..., object],
    push_floating_status: Callable[[str, str], None],
    render_background_job_status: Callable[..., None],
    clear_preloader: Callable[[], None],
) -> None:
    """Configure callbacks required by the reusable picker module."""
    globals().update(
        {
            "connected_ssh_host": connected_ssh_host,
            "background_job_state_key": background_job_state_key,
            "stop_background_jobs_with_state_prefix": stop_background_jobs_with_state_prefix,
            "background_job_result": background_job_result,
            "background_job_is_running": background_job_is_running,
            "start_background_bash_command": start_background_bash_command,
            "push_floating_status": push_floating_status,
            "render_background_job_status": render_background_job_status,
            "clear_preloader": clear_preloader,
        }
    )


def folder_picker_start_directory(value: str = "") -> str:
    """Return the best existing directory to open in the folder picker."""
    raw_value = str(value or "").strip() or str(Path.home())
    expanded_value = os.path.expandvars(os.path.expanduser(raw_value))
    candidate = Path(expanded_value)
    if candidate.is_file():
        candidate = candidate.parent
    if not candidate.is_dir():
        candidate = Path.home()
    return str(candidate.resolve())


def path_picker_uses_remote() -> bool:
    """Return whether the reusable path picker should browse the SSH host."""
    return bool(connected_ssh_host())


def remote_path_picker_default_directory() -> str:
    """Return the default remote directory for the reusable path picker."""
    return "$HOME"


def path_picker_mode() -> str:
    """Return the active path picker mode."""
    mode = str(st.session_state.get("_hhs_folder_picker_mode", "folder")).strip()
    return "file" if mode == "file" else "folder"


def normalize_remote_path_picker_path(
    path_value: str, base_path: str | None = None
) -> str:
    """Return a normalized remote picker path without local filesystem access."""
    raw_path = str(path_value or "").strip()
    if not raw_path:
        return remote_path_picker_default_directory()
    if (
        raw_path in {"~", "$HOME", "${HOME}"}
        or raw_path.startswith("~/")
        or raw_path.startswith("$HOME/")
        or raw_path.startswith("${HOME}/")
    ):
        return posixpath.normpath(raw_path)
    if raw_path.startswith("/"):
        return posixpath.normpath(raw_path)
    normalized_base = str(base_path or remote_path_picker_default_directory()).strip()
    if normalized_base.startswith("/"):
        return posixpath.normpath(posixpath.join(normalized_base, raw_path))
    if normalized_base == "~" or normalized_base.startswith("~/"):
        base_tail = "" if normalized_base == "~" else normalized_base[2:]
        joined_tail = posixpath.normpath(posixpath.join(base_tail, raw_path))
        return "~" if joined_tail == "." else f"~/{joined_tail}"
    for home_token in ("$HOME", "${HOME}"):
        if normalized_base == home_token or normalized_base.startswith(
            f"{home_token}/"
        ):
            base_tail = (
                ""
                if normalized_base == home_token
                else normalized_base[len(home_token) + 1 :]
            )
            joined_tail = posixpath.normpath(posixpath.join(base_tail, raw_path))
            return home_token if joined_tail == "." else f"{home_token}/{joined_tail}"
    return posixpath.normpath(raw_path)


def remote_path_picker_parent_path(path_value: str) -> str:
    """Return the parent directory for a remote picker path."""
    clean_path = normalize_remote_path_picker_path(path_value).rstrip("/")
    if clean_path in {"", ".", "~", "$HOME", "${HOME}", "/"}:
        return clean_path or "."
    if clean_path.startswith("~/"):
        tail = clean_path[2:]
        parent_tail = posixpath.dirname(tail)
        return "~" if not parent_tail else f"~/{parent_tail}"
    for home_token in ("$HOME", "${HOME}"):
        home_prefix = f"{home_token}/"
        if clean_path.startswith(home_prefix):
            tail = clean_path[len(home_prefix) :]
            parent_tail = posixpath.dirname(tail)
            return home_token if not parent_tail else f"{home_token}/{parent_tail}"
    parent_path = posixpath.dirname(clean_path)
    if clean_path.startswith("/") and not parent_path:
        return "/"
    return parent_path or "."


def path_picker_start_path(value: str = "", mode: str = "folder") -> str:
    """Return the best existing path to seed a folder or file picker."""
    if path_picker_uses_remote():
        return normalize_remote_path_picker_path(value)
    raw_value = str(value or "").strip() or str(Path.home())
    expanded_value = os.path.expandvars(os.path.expanduser(raw_value))
    candidate = Path(expanded_value)
    if mode == "file" and candidate.is_file():
        return str(candidate.resolve())
    return folder_picker_start_directory(expanded_value)


def path_picker_current_directory(value: str = "", mode: str = "folder") -> str:
    """Return the browsing directory for a folder or file picker value."""
    if path_picker_uses_remote():
        normalized_path = normalize_remote_path_picker_path(value)
        if mode == "file":
            return remote_path_picker_parent_path(normalized_path)
        return normalized_path
    selected_path = Path(path_picker_start_path(value, mode))
    if mode == "file" and selected_path.is_file():
        return str(selected_path.parent.resolve())
    return folder_picker_start_directory(str(selected_path))


def build_remote_path_picker_listing_command(
    directory: str, mode: str = "folder", include_dot_folders: bool = False
) -> str:
    """Build a remote shell command that lists path picker entries."""
    picker_mode = "file" if mode == "file" else "folder"
    include_hidden = "1" if include_dot_folders else "0"
    safe_path = shlex.quote(directory.strip() or remote_path_picker_default_directory())
    return textwrap.dedent(f"""
        raw_target={safe_path}
        picker_mode={shlex.quote(picker_mode)}
        include_hidden={include_hidden}
        case "${{raw_target}}" in
          "~"|"\$HOME"|"\${{HOME}}") target=${{HOME:-.}} ;;
          "~/"*) target="${{HOME:-.}}/${{raw_target#*/}}" ;;
          "\$HOME/"*) target="${{HOME:-.}}/${{raw_target#\$HOME/}}" ;;
          "\${{HOME}}/"*) target="${{HOME:-.}}/${{raw_target#\$\{{HOME\}}/}}" ;;
          *) target="${{raw_target}}" ;;
        esac
        if [ "${{picker_mode}}" = "file" ] && [ -f "${{target}}" ]; then
          target=$(dirname "${{target}}")
        fi
        if [ ! -d "${{target}}" ]; then
          target=${{HOME:-.}}
        fi
        if [ ! -d "${{target}}" ]; then
          target=.
        fi
        abs_dir=$(cd "${{target}}" && pwd -P) || {{
          printf '__HHS_PICKER_CWD__\\t%s\\n' .
          exit 0
        }}
        printf '__HHS_PICKER_CWD__\\t%s\\n' "${{abs_dir}}"
        for entry in "${{abs_dir}}"/* "${{abs_dir}}"/.[!.]* "${{abs_dir}}"/..?*; do
          [ -e "${{entry}}" ] || continue
          name=${{entry##*/}}
          case "${{name}}" in "."|"..") continue ;; esac
          if [ "${{include_hidden}}" != "1" ]; then
            case "${{name}}" in .*) continue ;; esac
          fi
          if [ -d "${{entry}}" ]; then
            kind=Dir
          elif [ -f "${{entry}}" ]; then
            kind=File
          else
            continue
          fi
          if [ "${{picker_mode}}" = "folder" ] && [ "${{kind}}" != "Dir" ]; then
            continue
          fi
          printf '__HHS_PICKER_ENTRY__\\t%s\\t%s\\n' "${{kind}}" "${{entry}}"
        done
        """).strip()


def parse_remote_path_picker_listing(output: str) -> tuple[str, list[tuple[str, str]]]:
    """Parse remote path picker command output into current dir and entries."""
    current_directory = ""
    entries: list[tuple[str, str]] = []
    for line in strip_ansi(output).splitlines():
        if line.startswith("__HHS_PICKER_CWD__\t"):
            current_directory = line.split("\t", 1)[1].strip()
            continue
        if not line.startswith("__HHS_PICKER_ENTRY__\t"):
            continue
        parts = line.split("\t", 2)
        if len(parts) == 3 and parts[1] in {"Dir", "File"} and parts[2].strip():
            entries.append((parts[1], parts[2].strip()))
    entries.sort(
        key=lambda item: (item[0] != "Dir", posixpath.basename(item[1]).lower())
    )
    return current_directory, entries


def clear_folder_picker_listing_cache() -> None:
    """Clear the dialog-local remote path picker listing cache."""
    st.session_state.pop("_hhs_folder_picker_listing_cache", None)


def path_picker_listing_job_name(
    directory: str, mode: str = "folder", include_dot_folders: bool = False
) -> str:
    """Return the background job name for one remote path picker listing."""
    cache_key = remote_path_picker_listing_cache_key(
        directory, mode, include_dot_folders
    )
    digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:16]
    return f"{PATH_PICKER_LISTING_JOB_PREFIX}_{digest}"


def path_picker_listing_job_state_prefix() -> str:
    """Return the Streamlit state prefix for all remote path picker listing jobs."""
    return background_job_state_key(PATH_PICKER_LISTING_JOB_PREFIX)


def stop_path_picker_listing_jobs() -> None:
    """Stop any in-flight remote path picker listing jobs."""
    stop_background_jobs_with_state_prefix(path_picker_listing_job_state_prefix())
    st.session_state.pop("_hhs_folder_picker_listing_loading_job", None)
    st.session_state.pop("_hhs_folder_picker_pending_dir", None)


def folder_picker_pending_directory() -> str:
    """Return the remote directory currently being loaded without promoting it."""
    return str(st.session_state.get("_hhs_folder_picker_pending_dir", "")).strip()


def folder_picker_visible_child_paths() -> list[str]:
    """Return the last child paths rendered by the picker."""
    raw_paths = st.session_state.get("_hhs_folder_picker_visible_child_paths", [])
    if not isinstance(raw_paths, list):
        return []
    return [str(path) for path in raw_paths if str(path).strip()]


def remember_folder_picker_visible_child_paths(child_paths: list[str]) -> None:
    """Remember the child paths currently visible in the picker."""
    st.session_state["_hhs_folder_picker_visible_child_paths"] = list(child_paths)


def queue_folder_picker_directory_load(directory: str) -> None:
    """Queue a remote picker directory load without changing the visible listing."""
    selected_directory = (
        normalize_remote_path_picker_path(directory)
        if path_picker_uses_remote()
        else folder_picker_start_directory(directory)
    )
    if not selected_directory:
        return
    if not path_picker_uses_remote():
        set_folder_picker_current_directory(selected_directory)
        return
    stop_path_picker_listing_jobs()
    st.session_state["_hhs_folder_picker_pending_dir"] = selected_directory


def folder_picker_listing_cache() -> dict[str, dict[str, object]]:
    """Return the dialog-local remote path picker listing cache."""
    cache = st.session_state.get("_hhs_folder_picker_listing_cache")
    if not isinstance(cache, dict):
        cache = {}
        st.session_state["_hhs_folder_picker_listing_cache"] = cache
    return cache


def remote_path_picker_listing_cache_key(
    directory: str, mode: str = "folder", include_dot_folders: bool = False
) -> str:
    """Return the cache key for one remote path picker directory listing."""
    host = connected_ssh_host()
    picker_mode = "file" if mode == "file" else "folder"
    include_hidden = "1" if include_dot_folders else "0"
    normalized_directory = normalize_remote_path_picker_path(directory)
    return "\0".join((host, picker_mode, include_hidden, normalized_directory))


def cached_remote_path_picker_listing(
    directory: str, mode: str = "folder", include_dot_folders: bool = False
) -> tuple[str, list[tuple[str, str]]] | None:
    """Return a cached remote path picker listing, when available."""
    cache_key = remote_path_picker_listing_cache_key(
        directory, mode, include_dot_folders
    )
    listing = folder_picker_listing_cache().get(cache_key)
    if not isinstance(listing, dict):
        return None
    current_directory = str(listing.get("current_directory", "")).strip()
    raw_entries = listing.get("entries", [])
    if not current_directory or not isinstance(raw_entries, list):
        return None
    entries: list[tuple[str, str]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, (list, tuple)) or len(raw_entry) != 2:
            return None
        kind = str(raw_entry[0])
        path = str(raw_entry[1]).strip()
        if kind not in {"Dir", "File"} or not path:
            return None
        entries.append((kind, path))
    return current_directory, entries


def remember_remote_path_picker_listing(
    requested_directory: str,
    current_directory: str,
    entries: list[tuple[str, str]],
    mode: str = "folder",
    include_dot_folders: bool = False,
) -> None:
    """Cache one remote path picker listing for this open dialog."""
    clean_current_directory = (
        current_directory.strip()
        or normalize_remote_path_picker_path(requested_directory)
    )
    listing = {
        "current_directory": clean_current_directory,
        "entries": list(entries),
    }
    cache = folder_picker_listing_cache()
    for directory in {requested_directory, clean_current_directory}:
        cache[
            remote_path_picker_listing_cache_key(directory, mode, include_dot_folders)
        ] = listing


def apply_remote_path_picker_listing(
    current_directory: str, entries: list[tuple[str, str]]
) -> list[str]:
    """Apply one remote path picker listing to session state and return paths."""
    if current_directory:
        st.session_state["_hhs_folder_picker_current_dir"] = current_directory
        if path_picker_mode() == "folder":
            st.session_state["_hhs_folder_picker_current_dir_input"] = current_directory
    st.session_state["_hhs_folder_picker_path_kinds"] = {
        path: kind for kind, path in entries
    }
    return [path for _kind, path in entries]


def complete_remote_path_picker_listing_job(
    job_name: str,
    directory: str,
    mode: str = "folder",
    include_dot_folders: bool = False,
) -> list[str] | None:
    """Complete one remote path picker listing job, caching successful output."""
    completed = background_job_result(job_name)
    if completed is None:
        return None
    result, metadata = completed
    requested_directory = str(metadata.get("directory", "") or directory)
    picker_mode = (
        "file" if str(metadata.get("mode", "") or mode) == "file" else "folder"
    )
    include_hidden = bool(metadata.get("include_dot_folders", include_dot_folders))
    if st.session_state.get("_hhs_folder_picker_listing_loading_job") == job_name:
        st.session_state.pop("_hhs_folder_picker_listing_loading_job", None)
    if result.returncode != 0:
        push_floating_status(
            clean_command_status_message(result.stderr or result.stdout),
            "error",
        )
        current_directory = normalize_remote_path_picker_path(requested_directory)
        remember_remote_path_picker_listing(
            requested_directory, current_directory, [], picker_mode, include_hidden
        )
        apply_remote_path_picker_listing(current_directory, [])
        return []
    current_directory, entries = parse_remote_path_picker_listing(result.stdout)
    remember_remote_path_picker_listing(
        requested_directory, current_directory, entries, picker_mode, include_hidden
    )
    return apply_remote_path_picker_listing(current_directory, entries)


def remote_path_picker_child_paths(
    directory: str, mode: str = "folder", include_dot_folders: bool = False
) -> list[str]:
    """Return remote child paths for the reusable path picker."""
    if not connected_ssh_host():
        return []
    cached_listing = cached_remote_path_picker_listing(
        directory, mode, include_dot_folders
    )
    if cached_listing is not None:
        st.session_state.pop("_hhs_folder_picker_listing_loading_job", None)
        return apply_remote_path_picker_listing(*cached_listing)
    job_name = path_picker_listing_job_name(directory, mode, include_dot_folders)
    completed_paths = complete_remote_path_picker_listing_job(
        job_name, directory, mode, include_dot_folders
    )
    if completed_paths is not None:
        return completed_paths
    st.session_state["_hhs_folder_picker_listing_loading_job"] = job_name
    if background_job_is_running(job_name):
        return []
    start_background_bash_command(
        job_name,
        build_remote_path_picker_listing_command(directory, mode, include_dot_folders),
        PATH_PICKER_LISTING_LOADER_MESSAGE,
        timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
        metadata={
            "directory": directory,
            "mode": "file" if mode == "file" else "folder",
            "include_dot_folders": bool(include_dot_folders),
        },
        show_preloader_event=True,
    )
    return []


def load_pending_remote_path_picker_directory(
    mode: str = "folder", include_dot_folders: bool = False
) -> bool:
    """Start or complete a pending remote directory load for the picker."""
    pending_directory = folder_picker_pending_directory()
    if not pending_directory:
        return False
    cached_listing = cached_remote_path_picker_listing(
        pending_directory, mode, include_dot_folders
    )
    if cached_listing is not None:
        st.session_state.pop("_hhs_folder_picker_pending_dir", None)
        st.session_state.pop("_hhs_folder_picker_listing_loading_job", None)
        child_paths = apply_remote_path_picker_listing(*cached_listing)
        remember_folder_picker_visible_child_paths(child_paths)
        sync_folder_picker_child_selection(child_paths)
        return True
    job_name = path_picker_listing_job_name(
        pending_directory, mode, include_dot_folders
    )
    completed_paths = complete_remote_path_picker_listing_job(
        job_name, pending_directory, mode, include_dot_folders
    )
    if completed_paths is not None:
        st.session_state.pop("_hhs_folder_picker_pending_dir", None)
        remember_folder_picker_visible_child_paths(completed_paths)
        sync_folder_picker_child_selection(completed_paths)
        return True
    st.session_state["_hhs_folder_picker_listing_loading_job"] = job_name
    if not background_job_is_running(job_name):
        start_background_bash_command(
            job_name,
            build_remote_path_picker_listing_command(
                pending_directory, mode, include_dot_folders
            ),
            PATH_PICKER_LISTING_LOADER_MESSAGE,
            timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS,
            metadata={
                "directory": pending_directory,
                "mode": "file" if mode == "file" else "folder",
                "include_dot_folders": bool(include_dot_folders),
            },
            show_preloader_event=True,
        )
    return False


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
    if path_picker_uses_remote():
        return remote_path_picker_child_paths(directory, mode, include_dot_folders)
    st.session_state.pop("_hhs_folder_picker_listing_loading_job", None)
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
    if path_picker_uses_remote():
        return posixpath.basename(str(directory).rstrip("/")) or str(directory)
    path = Path(directory)
    return path.name or str(path)


def path_picker_label(path_value: str) -> str:
    """Return the display label for a folder or file picker option."""
    if path_picker_uses_remote():
        return posixpath.basename(str(path_value).rstrip("/")) or str(path_value)
    path = Path(path_value)
    return path.name or str(path)


def folder_picker_owner_context_for_target(target_key: str) -> str:
    """Return the fragment owner that should render a picker target key."""
    target = str(target_key or "")
    if target == "search_path" or target.startswith("search_"):
        return "search"
    if target.startswith("path_add_"):
        return "path"
    if target.startswith("dir_") or target.startswith(
        f"{hhs_ui.DIR_VALUE_EDITOR_KEY_PREFIX}_"
    ):
        return "dir"
    return ""


def folder_picker_owner_context() -> str:
    """Return the current picker owner context, if any."""
    return str(st.session_state.get("_hhs_folder_picker_owner_context", "") or "")


def folder_picker_owner_matches(owner_context: str) -> bool:
    """Return whether a picker render location owns the open picker."""
    active_owner = folder_picker_owner_context()
    if owner_context:
        return active_owner == owner_context
    return not active_owner


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
    st.session_state["_hhs_folder_picker_owner_context"] = (
        folder_picker_owner_context_for_target(target_key)
    )
    st.session_state["_hhs_folder_picker_current_dir"] = start_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = start_path
    st.session_state.setdefault("_hhs_folder_picker_include_dot_folders", False)
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)
    st.session_state.pop("_hhs_folder_picker_path_kinds", None)
    st.session_state.pop("_hhs_folder_picker_visible_child_paths", None)
    stop_path_picker_listing_jobs()
    clear_folder_picker_listing_cache()
    prune_folder_picker_child_selection_widget_keys()


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
    st.session_state.pop("_hhs_folder_picker_owner_context", None)
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)
    st.session_state.pop("_hhs_folder_picker_path_kinds", None)
    st.session_state.pop("_hhs_folder_picker_visible_child_paths", None)
    stop_path_picker_listing_jobs()
    clear_folder_picker_listing_cache()
    prune_folder_picker_child_selection_widget_keys()


def selected_folder_picker_path() -> str:
    """Return the selected path from the path picker current input."""
    typed_path = str(
        st.session_state.get("_hhs_folder_picker_current_dir_input", "")
    ).strip()
    mode = path_picker_mode()
    if path_picker_uses_remote():
        if typed_path:
            return normalize_remote_path_picker_path(typed_path)
        return normalize_remote_path_picker_path(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
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


def sync_folder_picker_child_selection(child_paths: list[str]) -> None:
    """Keep the selected path picker child valid for the loaded child list."""
    current_selection = str(st.session_state.get("_hhs_folder_picker_selected_dir", ""))
    if child_paths:
        if current_selection not in child_paths:
            st.session_state["_hhs_folder_picker_selected_dir"] = child_paths[0]
        return
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)


def folder_picker_child_selection_widget_key(
    directory: str, mode: str, include_dot_folders: bool
) -> str:
    """Return a directory-scoped widget key for the path picker child combo."""
    key_material = "\0".join((str(directory), str(mode), str(include_dot_folders)))
    digest = hashlib.sha1(key_material.encode("utf-8")).hexdigest()[:16]
    return f"_hhs_folder_picker_selected_dir_widget_{digest}"


def prune_folder_picker_child_selection_widget_keys(active_key: str = "") -> None:
    """Remove stale directory-scoped path picker child combo widget state."""
    key_prefix = "_hhs_folder_picker_selected_dir_widget_"
    for key in list(st.session_state.keys()):
        if str(key).startswith(key_prefix) and key != active_key:
            st.session_state.pop(key, None)


def folder_picker_browsing_directory() -> str:
    """Return the path picker directory that should be listed now."""
    current_value = str(
        st.session_state.get("_hhs_folder_picker_current_dir_input", "")
    ).strip()
    if not current_value:
        current_value = str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
    return path_picker_current_directory(current_value, path_picker_mode())


def refresh_folder_picker_current_children() -> None:
    """Queue a child-list refresh for the current path picker directory."""
    current_directory = folder_picker_browsing_directory()
    if path_picker_uses_remote():
        queue_folder_picker_directory_load(current_directory)
        return
    st.session_state["_hhs_folder_picker_current_dir"] = current_directory
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)
    st.session_state.pop("_hhs_folder_picker_path_kinds", None)
    prune_folder_picker_child_selection_widget_keys()


def prepare_path_picker_dialog_listing(mode: str) -> None:
    """Load the current remote picker listing before mounting the dialog."""
    if not path_picker_uses_remote():
        return
    include_dot_folders = bool(
        st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
    )
    if folder_picker_pending_directory():
        load_pending_remote_path_picker_directory(mode, include_dot_folders)
        return
    current_directory = folder_picker_browsing_directory()
    child_paths = path_picker_child_paths(current_directory, mode, include_dot_folders)
    remember_folder_picker_visible_child_paths(child_paths)
    sync_folder_picker_child_selection(child_paths)


def set_folder_picker_current_directory(
    directory: str, load_children: bool = False
) -> None:
    """Set the folder picker current directory."""
    selected_directory = (
        normalize_remote_path_picker_path(directory)
        if path_picker_uses_remote()
        else folder_picker_start_directory(directory)
    )
    st.session_state["_hhs_folder_picker_current_dir"] = selected_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = selected_directory
    if not load_children:
        st.session_state.pop("_hhs_folder_picker_selected_dir", None)
        st.session_state.pop("_hhs_folder_picker_path_kinds", None)
        prune_folder_picker_child_selection_widget_keys()
        return
    include_dot_folders = bool(
        st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
    )
    child_directories = path_picker_child_paths(
        selected_directory, path_picker_mode(), include_dot_folders
    )
    sync_folder_picker_child_selection(child_directories)


def apply_folder_picker_typed_directory() -> None:
    """Apply the manually typed path picker value."""
    typed_path = str(st.session_state.get("_hhs_folder_picker_current_dir_input", ""))
    mode = path_picker_mode()
    if mode == "folder":
        if path_picker_uses_remote():
            queue_folder_picker_directory_load(typed_path)
            return
        set_folder_picker_current_directory(typed_path)
        return
    if path_picker_uses_remote():
        selected_path = normalize_remote_path_picker_path(typed_path)
        current_directory = path_picker_current_directory(selected_path, mode)
        st.session_state["_hhs_folder_picker_current_dir"] = current_directory
        st.session_state["_hhs_folder_picker_current_dir_input"] = selected_path
        st.session_state.pop("_hhs_folder_picker_selected_dir", None)
        st.session_state.pop("_hhs_folder_picker_path_kinds", None)
        prune_folder_picker_child_selection_widget_keys()
        return
    selected_path = path_picker_start_path(typed_path, mode)
    current_directory = path_picker_current_directory(selected_path, mode)
    st.session_state["_hhs_folder_picker_current_dir"] = current_directory
    st.session_state["_hhs_folder_picker_current_dir_input"] = selected_path
    st.session_state.pop("_hhs_folder_picker_selected_dir", None)
    st.session_state.pop("_hhs_folder_picker_path_kinds", None)
    prune_folder_picker_child_selection_widget_keys()


def open_folder_picker_parent() -> None:
    """Move the folder picker to the parent directory."""
    if path_picker_uses_remote():
        current_directory = normalize_remote_path_picker_path(
            str(st.session_state.get("_hhs_folder_picker_current_dir", ""))
        )
        queue_folder_picker_directory_load(
            remote_path_picker_parent_path(current_directory)
        )
        return
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
    if path_picker_uses_remote():
        path_kinds = st.session_state.get("_hhs_folder_picker_path_kinds", {})
        selected_kind = (
            path_kinds.get(selected_path) if isinstance(path_kinds, dict) else ""
        )
        if path_picker_mode() == "file" and selected_kind == "File":
            st.session_state["_hhs_folder_picker_current_dir_input"] = selected_path
            return
        queue_folder_picker_directory_load(selected_path)
        return
    selected_entry = Path(selected_path)
    if path_picker_mode() == "file" and selected_entry.is_file():
        st.session_state["_hhs_folder_picker_current_dir_input"] = str(
            selected_entry.resolve()
        )
        return
    set_folder_picker_current_directory(selected_path)


def open_folder_picker_selected_child(selected_widget_key: str) -> None:
    """Open the selected child folder when the folder list changes."""
    if path_picker_mode() != "folder":
        return
    selected_path = str(st.session_state.get(selected_widget_key, "")).strip()
    if not selected_path:
        return
    st.session_state["_hhs_folder_picker_selected_dir"] = selected_path
    open_folder_picker_selected_directory()


def apply_folder_picker_selection() -> None:
    """Assign the selected folder to the target Streamlit input key."""
    target_key = str(st.session_state.get("_hhs_folder_picker_target_key", ""))
    if target_key:
        selected_path = selected_folder_picker_path()
        st.session_state[target_key] = selected_path
        queue_folder_picker_selection(target_key, selected_path)
    close_folder_picker()


def apply_folder_picker_selection_and_dismiss() -> None:
    """Assign the selected folder and close the folder picker overlay."""
    apply_folder_picker_selection()


def cancel_folder_picker_and_dismiss() -> None:
    """Close the folder picker overlay without changing the target input."""
    close_folder_picker()


def render_path_picker_dialog(owner_context: str = "") -> bool:
    """Render the reusable path picker as a styled page overlay."""
    if not st.session_state.get("_hhs_folder_picker_open"):
        return False
    if not folder_picker_owner_matches(owner_context):
        return False

    mode = path_picker_mode()
    selected_label = "Selected file" if mode == "file" else "Selected folder"
    option_label = "Files" if mode == "file" else "Folders"
    empty_caption = "No files or folders." if mode == "file" else "No child folders."
    prepare_path_picker_dialog_listing(mode)
    title = "Select file" if mode == "file" else "Select folder"

    with st.container(key="hhs_path_picker_overlay"):
        with st.container(key="hhs_path_picker_panel"):
            title_col, close_col = st.columns([1.0, 0.08], vertical_alignment="center")
            with title_col:
                st.markdown(
                    f'<h2 class="hhs-path-picker-title">{html.escape(title)}</h2>',
                    unsafe_allow_html=True,
                )
            with close_col:
                st.button(
                    "×",
                    key="folder_picker_header_close_button",
                    help="Close",
                    on_click=close_folder_picker,
                    width="content",
                )
            render_path_picker_body(
                mode,
                selected_label,
                option_label,
                empty_caption,
            )
    clear_preloader()
    return True


def render_path_picker_body(
    mode: str,
    selected_label: str,
    option_label: str,
    empty_caption: str,
) -> None:
    """Render the path picker controls inside the styled overlay."""
    current_directory = folder_picker_browsing_directory()
    st.session_state["_hhs_folder_picker_current_dir"] = current_directory
    include_dot_folders = bool(
        st.session_state.get("_hhs_folder_picker_include_dot_folders", False)
    )
    loading_job_name = str(
        st.session_state.get("_hhs_folder_picker_listing_loading_job", "")
    )
    loading_children = bool(
        loading_job_name and background_job_is_running(loading_job_name)
    )
    if loading_children and folder_picker_pending_directory():
        child_directories = folder_picker_visible_child_paths()
    else:
        child_directories = path_picker_child_paths(
            current_directory, mode, include_dot_folders
        )
        remember_folder_picker_visible_child_paths(child_directories)
    sync_folder_picker_child_selection(child_directories)
    if loading_children:
        render_path_picker_listing_loader(loading_job_name)
    st.text_input(
        selected_label,
        key="_hhs_folder_picker_current_dir_input",
        disabled=loading_children,
        on_change=apply_folder_picker_typed_directory,
    )
    selected_widget_key = folder_picker_child_selection_widget_key(
        current_directory, mode, include_dot_folders
    )
    prune_folder_picker_child_selection_widget_keys(selected_widget_key)
    selected_directory = str(
        st.session_state.get("_hhs_folder_picker_selected_dir", "")
    )
    if child_directories:
        if selected_directory not in child_directories:
            selected_directory = child_directories[0]
        if st.session_state.get(selected_widget_key) not in child_directories:
            st.session_state[selected_widget_key] = selected_directory
    else:
        st.session_state.pop("_hhs_folder_picker_selected_dir", None)
        st.session_state.pop(selected_widget_key, None)
    selectbox_kwargs: dict[str, object] = {
        "key": selected_widget_key,
        "format_func": path_picker_label,
        "placeholder": (
            PATH_PICKER_LISTING_LOADER_MESSAGE if loading_children else empty_caption
        ),
        "disabled": loading_children or not bool(child_directories),
    }
    if mode == "folder":
        selectbox_kwargs["on_change"] = open_folder_picker_selected_child
        selectbox_kwargs["args"] = (selected_widget_key,)
    if not child_directories:
        selectbox_kwargs["index"] = None
    selected_directory = st.selectbox(
        option_label,
        child_directories,
        **selectbox_kwargs,
    )
    if selected_directory:
        st.session_state["_hhs_folder_picker_selected_dir"] = selected_directory
    st.checkbox(
        "Include .dot-folders",
        key="_hhs_folder_picker_include_dot_folders",
        value=False,
        disabled=loading_children,
        on_change=refresh_folder_picker_current_children,
    )
    with st.container(key="folder_picker_action_grid"):
        (
            _left_spacer,
            parent_column,
            open_column,
            select_column,
            cancel_column,
            _right_spacer,
        ) = st.columns(
            [1.0, 0.12, 0.12, 0.12, 0.12, 1.0],
            gap="small",
            vertical_alignment="center",
        )
        with parent_column:
            st.button(
                "",
                key="folder_picker_parent_button",
                help="Parent",
                disabled=loading_children,
                on_click=open_folder_picker_parent,
                width="content",
            )
        with open_column:
            st.button(
                "",
                key="folder_picker_open_button",
                help="Open",
                disabled=loading_children or not bool(child_directories),
                on_click=open_folder_picker_selected_directory,
                width="content",
            )
        with select_column:
            st.button(
                "﬌",
                key="folder_picker_select_button",
                help="Select",
                disabled=loading_children,
                on_click=apply_folder_picker_selection_and_dismiss,
                width="content",
            )
        with cancel_column:
            st.button(
                "ﰸ",
                key="folder_picker_cancel_button",
                help="Cancel",
                on_click=cancel_folder_picker_and_dismiss,
                width="content",
            )


def render_path_picker_listing_loader(job_name: str) -> None:
    """Render an in-dialog loader while a remote path picker listing runs."""
    render_background_job_status(job_name, PATH_PICKER_LISTING_LOADER_MESSAGE)


def render_folder_picker_dialog(owner_context: str = "") -> bool:
    """Render the reusable path picker dialog when requested."""
    return render_path_picker_dialog(owner_context)


