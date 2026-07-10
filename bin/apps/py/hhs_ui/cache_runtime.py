#!/usr/bin/env python3
"""UI cache and cached command helpers for HomeSetup Streamlit."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import streamlit as st

import hhs_ui
import hhs_ui.constants as hhs_ui_constants
from hhs_ui.command_catalog import (
    colorize_log_output,
    filter_log_output,
    sanitize_remote_command_result,
    ssh_shared_connection_closed,
    strip_ansi,
)
from hhs_ui.command_runtime import (
    background_job_is_running,
    background_job_result,
    background_job_state_key,
    render_background_job_status_if_blocking,
    start_background_bash_command,
    stop_background_jobs,
    stop_background_jobs_with_state_prefix,
)
from hhs_ui.feedback_ui import render_command_loader
from hhs_ui.runtime import RUN_SHELL
from hhs_ui.ui_definitions import (
    CACHE_CLEAR_BACKGROUND_JOBS,
    HOST_SWITCH_BACKGROUND_JOBS,
    HOST_SWITCH_CACHE_TAGS,
    HOST_SWITCH_STATE_KEYS,
)


UI_CACHE_MEMORY: dict[str, dict[str, object]] = {}
UI_CACHE_MEMORY_MTIME: float | None = None


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"cache runtime dependency is not configured: {name}")

    return dependency


effective_bash_command = _unconfigured_dependency("effective_bash_command")
command_remote_host = _unconfigured_dependency("command_remote_host")
stop_path_picker_listing_jobs = _unconfigured_dependency("stop_path_picker_listing_jobs")
push_floating_status = _unconfigured_dependency("push_floating_status")
clear_firebase_aliases_cache = _unconfigured_dependency("clear_firebase_aliases_cache")


def configure_cache_runtime(
    *,
    effective_bash_command: Callable[..., str],
    command_remote_host: Callable[..., str],
    stop_path_picker_listing_jobs: Callable[[], None],
    push_floating_status: Callable[[str, str], None],
    clear_firebase_aliases_cache: Callable[[], None],
) -> None:
    """Configure callbacks required by cache runtime helpers."""
    globals().update(
        {
            "effective_bash_command": effective_bash_command,
            "command_remote_host": command_remote_host,
            "stop_path_picker_listing_jobs": stop_path_picker_listing_jobs,
            "push_floating_status": push_floating_status,
            "clear_firebase_aliases_cache": clear_firebase_aliases_cache,
        }
    )


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
