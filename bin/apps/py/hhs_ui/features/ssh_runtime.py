#!/usr/bin/env python3
"""SSH connection runtime helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.execution.cache_runtime import (
    cache_clear,
    cache_get,
    expire_host_scoped_command_state,
    load_ui_cache,
    save_ui_cache,
)
from hhs_ui.execution.command_catalog import (
    clean_command_status_message,
    ssh_shared_connection_closed,
    strip_ansi,
)
from hhs_ui.execution.command_runtime import (
    background_job_result,
    background_job_state,
    render_background_job_status,
    run_bash_command,
    start_background_bash_command,
)
from hhs_ui.widgets.dialog_ui import pop_dialog
from hhs_ui.widgets.feedback_ui import render_command_preloader_events, set_overlay
from hhs_ui.features.ssh_core import (
    build_ssh_check_command,
    build_ssh_connect_command,
    build_ssh_disconnect_command,
    build_ssh_wrapped_command,
    local_hostname,
    ssh_config_hosts,
    ssh_connection_display,
)
from hhs_ui.widgets.status_ui import push_floating_status
from hhs_ui.widgets.terminal_ui import (
    render_ttyd_terminal_frame_cleanup_script,
    stop_ttyd_session,
)
from hhs_ui.core.ui_definitions import (
    HOST_SWITCH_VIEW_STATE_KEY,
    SSH_CONNECT_JOB,
    SSH_DISCONNECT_JOB,
)
from hhs_ui.core.ui_state import is_persistable_ui_value, load_ui_state, save_ui_state


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"SSH runtime dependency is not configured: {name}")

    return dependency


terminal_document_view_is_active = _unconfigured_dependency(
    "terminal_document_view_is_active"
)
restore_terminal_document_view = _unconfigured_dependency(
    "restore_terminal_document_view"
)
reset_updater_remote_check_state = _unconfigured_dependency(
    "reset_updater_remote_check_state"
)
update_remote_footer_working_directory = _unconfigured_dependency(
    "update_remote_footer_working_directory"
)
reset_search_directory_to_home = _unconfigured_dependency(
    "reset_search_directory_to_home"
)
schedule_ollama_service_availability_refresh = _unconfigured_dependency(
    "schedule_ollama_service_availability_refresh"
)


def configure_ssh_runtime(
    *,
    terminal_document_view_is_active: Callable[[], bool],
    restore_terminal_document_view: Callable[[bool], None],
    reset_updater_remote_check_state: Callable[[], None],
    update_remote_footer_working_directory: Callable[[], None],
    reset_search_directory_to_home: Callable[[], None],
    schedule_ollama_service_availability_refresh: Callable[[], None],
) -> None:
    """Configure callbacks required by SSH runtime helpers."""
    globals().update(
        {
            "terminal_document_view_is_active": terminal_document_view_is_active,
            "restore_terminal_document_view": restore_terminal_document_view,
            "reset_updater_remote_check_state": reset_updater_remote_check_state,
            "update_remote_footer_working_directory": update_remote_footer_working_directory,
            "reset_search_directory_to_home": reset_search_directory_to_home,
            "schedule_ollama_service_availability_refresh": (
                schedule_ollama_service_availability_refresh
            ),
        }
    )


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
        "hhs_view",
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
        if reconnect_host and not selected_host_is_local(reconnect_host):
            schedule_ssh_reconnect(reconnect_host)
        else:
            clear_registered_ssh_connection()
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


def schedule_ssh_reconnect(host: str) -> None:
    """Schedule an on-demand reconnect without losing the active remote view."""
    clean_host = host.strip()
    if not clean_host or selected_host_is_local(clean_host):
        return
    remember_host_switch_view_state()
    stop_ttyd_session()
    expire_host_scoped_command_state()
    st.session_state["ssh_connection_status"] = "reconnecting"
    st.session_state["ssh_connection_host"] = clean_host
    st.session_state["ssh_connection_error"] = ""
    st.session_state["ssh_connect_pending"] = clean_host
    st.session_state["ssh_connect_pending_message"] = (
        f"Reconnecting to {ssh_connection_display(clean_host)}"
    )
    st.session_state["ssh_disconnect_pending"] = ""
    st.session_state["ssh_host_selected"] = clean_host
    st.session_state["ssh_host_selector"] = clean_host
    st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = clean_host
    st.session_state["ssh_reconnect_restore_view_state"] = True
    st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)
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
    if host and ssh_shared_connection_closed(result):
        schedule_ssh_reconnect(host)
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
        st.session_state["ssh_connection_dialog_title"] = ""
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
