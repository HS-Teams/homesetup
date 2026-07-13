#!/usr/bin/env python3
"""AI UI and background action helpers for the HomeSetup Streamlit app."""

from __future__ import annotations

import html
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.cache_runtime import (
    background_command_metadata,
    cache_background_command_result,
    cache_delete_tag,
    parse_rows_cached,
    render_cached_command_result,
)
from hhs_ui.execution.command_catalog import (
    ai_context_used_meta_html,
    build_hhs_ask_command,
    build_hhs_ask_context_command,
    build_hhs_ask_ingest_command,
    build_hhs_ask_models_command,
    build_hhs_ask_prompt_file_command,
    build_hhs_ask_reset_command,
    build_hhs_ask_select_model_command,
    build_hhs_revert_ask_prompt_file_command,
    build_hhs_save_ask_prompt_file_command,
    build_ollama_delete_model_command,
    clean_command_status_message,
    clean_hhs_ask_output,
    current_username,
    first_downloaded_ollama_model,
    format_ai_chat_prefix,
    format_ai_request_duration,
    html_tooltip_chip,
    ollama_model_context_size,
    parse_current_ollama_model,
    parse_ollama_model_rows,
    prepare_ai_chat_content,
    strip_ansi,
)
from hhs_ui.execution.command_runtime import (
    background_job_is_running,
    background_job_result,
    background_job_state,
    render_background_job_status,
    start_background_bash_command,
)
from hhs_ui.widgets.dialog_ui import pop_dialog
from hhs_ui.widgets.feedback_ui import render_terminal_output
from hhs_ui.features.ssh_runtime import connected_ssh_host
from hhs_ui.widgets.status_ui import push_floating_status
from hhs_ui.widgets.table_ui import render_table, render_view_subtitle
from hhs_ui.core.ui_definitions import (
    AI_ASK_JOB,
    AI_CONTEXT_ACTION_JOB,
    AI_MODEL_DELETE_JOB,
    AI_MODEL_SELECT_JOB,
    AI_PROMPT_ACTION_JOB,
)
from hhs_ui.core.ui_state import save_ui_state


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"AI UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
render_view_segmented_control = _unconfigured_dependency(
    "render_view_segmented_control"
)
start_background_action_job = _unconfigured_dependency("start_background_action_job")


def configure_ai_ui(
    *,
    render_script_html: Callable[..., None],
    render_view_segmented_control: Callable[..., str],
    start_background_action_job: Callable[..., bool],
) -> None:
    """Configure callbacks required by AI UI helpers."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "render_view_segmented_control": render_view_segmented_control,
            "start_background_action_job": start_background_action_job,
        }
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


def hhs_ask_timeout_seconds() -> int:
    """Return the timeout for an Ollama prompt based on the selected host."""
    return 180 if connected_ssh_host() else 90


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


def refresh_ai_model_listing() -> None:
    """Refresh cached AI model listings and reset the AI model selection."""
    cache_delete_tag("ai_models")
    cache_delete_tag("ai")
    reset_ai_model_table_selection()


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


def render_ai_chat_input_tooltip() -> None:
    """Attach native tooltips to the Streamlit chat input controls."""
    render_script_html(
        """
        <script>
        (() => {
            const documentRoot = window.parent.document;
            const chatInput = documentRoot.querySelector('[data-testid="stChatInput"]');
            if (!chatInput) {
                return;
            }

            const input = chatInput.querySelector("textarea, [contenteditable='true']");
            if (input) {
                input.title = "Ask Ollama through HomeSetup.";
            }

            const submitButton = chatInput.querySelector("button");
            if (submitButton) {
                submitButton.title = "Send message to Ollama.";
            }
        })();
        </script>
        """,
        height=0,
        width=0,
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

    prompt = st.chat_input("Ask Ollama through HomeSetup")
    render_ai_chat_input_tooltip()
    if prompt:
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
        help=(
            "Edit the runtime instruction template prepended to HomeSetup requests "
            "sent to Ollama. Saving changes affects subsequent AI conversations."
        ),
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
            help=(
                "Upload a supported text-based file whose complete contents will be "
                "appended to the HomeSetup context used by subsequent Ollama requests."
            ),
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
                "help": "Delete the selected Ollama model",
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
