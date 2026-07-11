#!/usr/bin/env python3
"""Command execution and background job runtime helpers for HomeSetup."""

from __future__ import annotations

import os
import re
import secrets
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.command_catalog import (
    completed_disconnected_ssh_process,
    sanitize_remote_command_result,
    ssh_shared_connection_closed,
)
from hhs_ui.widgets.feedback_ui import (
    emit_command_preloader_finish,
    emit_command_preloader_start,
    render_command_loader,
    render_command_preloader_events,
    set_overlay,
)
from hhs_ui.core.runtime import RUN_SHELL
from hhs_ui.widgets.table_ui import table_selection_rerun_in_progress
from hhs_ui.widgets.terminal_ui import stop_process
from hhs_ui.core.ui_definitions import BACKGROUND_JOB_STATE_KEY_PREFIX


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"command runtime dependency is not configured: {name}")

    return dependency


command_remote_host = _unconfigured_dependency("command_remote_host")
effective_bash_command = _unconfigured_dependency("effective_bash_command")
effective_command_timeout_seconds = _unconfigured_dependency(
    "effective_command_timeout_seconds"
)
command_timeout_seconds = _unconfigured_dependency("command_timeout_seconds")
command_cache_key = _unconfigured_dependency("command_cache_key")
command_result_snapshot_get = _unconfigured_dependency("command_result_snapshot_get")
command_result_snapshot_set = _unconfigured_dependency("command_result_snapshot_set")
completed_process_from_cache = _unconfigured_dependency("completed_process_from_cache")
cache_value_from_completed_process = _unconfigured_dependency(
    "cache_value_from_completed_process"
)
cache_get = _unconfigured_dependency("cache_get")
cache_set = _unconfigured_dependency("cache_set")
handle_remote_command_result = _unconfigured_dependency("handle_remote_command_result")
ssh_connection_is_alive = _unconfigured_dependency("ssh_connection_is_alive")
ui_disposable_files_dir = _unconfigured_dependency("ui_disposable_files_dir")
update_ollama_service_availability_refresh = _unconfigured_dependency(
    "update_ollama_service_availability_refresh"
)


def configure_command_runtime(
    *,
    command_remote_host: Callable[..., str],
    effective_bash_command: Callable[..., str],
    effective_command_timeout_seconds: Callable[..., int],
    command_timeout_seconds: Callable[..., int],
    command_cache_key: Callable[..., str],
    command_result_snapshot_get: Callable[[str], dict[str, object] | None],
    command_result_snapshot_set: Callable[[str, dict[str, object]], None],
    completed_process_from_cache: Callable[
        [str, dict[str, object]], subprocess.CompletedProcess[str]
    ],
    cache_value_from_completed_process: Callable[
        [subprocess.CompletedProcess[str]], dict[str, object]
    ],
    cache_get: Callable[[str], dict[str, object] | None],
    cache_set: Callable[[str, dict[str, object], int | float | str], None],
    handle_remote_command_result: Callable[
        [str, subprocess.CompletedProcess[str]], bool
    ],
    ssh_connection_is_alive: Callable[[str], bool],
    ui_disposable_files_dir: Callable[[], Path],
    update_ollama_service_availability_refresh: Callable[[], None],
) -> None:
    """Configure callbacks required by command runtime helpers."""
    globals().update(
        {
            "command_remote_host": command_remote_host,
            "effective_bash_command": effective_bash_command,
            "effective_command_timeout_seconds": effective_command_timeout_seconds,
            "command_timeout_seconds": command_timeout_seconds,
            "command_cache_key": command_cache_key,
            "command_result_snapshot_get": command_result_snapshot_get,
            "command_result_snapshot_set": command_result_snapshot_set,
            "completed_process_from_cache": completed_process_from_cache,
            "cache_value_from_completed_process": cache_value_from_completed_process,
            "cache_get": cache_get,
            "cache_set": cache_set,
            "handle_remote_command_result": handle_remote_command_result,
            "ssh_connection_is_alive": ssh_connection_is_alive,
            "ui_disposable_files_dir": ui_disposable_files_dir,
            "update_ollama_service_availability_refresh": (
                update_ollama_service_availability_refresh
            ),
        }
    )


def command_env() -> dict[str, str]:
    """Return the environment used by HomeSetup command subprocesses."""
    return {
        **os.environ,
        "COLUMNS": hhs_ui.COMMAND_COLUMNS,
        hhs_ui_constants.RUN_SHELL_ENV_KEY: RUN_SHELL,
        "TERM": os.environ.get("TERM", "xterm-256color"),
    }


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
