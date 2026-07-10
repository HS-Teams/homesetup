#!/usr/bin/env python3
"""Search UI and runtime helpers for the HomeSetup Streamlit app."""

from __future__ import annotations

import hashlib
import html
import json
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import urllib.parse
from collections.abc import Callable
from pathlib import Path

import streamlit as st

import hhs_ui
import hhs_ui.constants as hhs_ui_constants
from hhs_ui.cache_runtime import (
    background_command_metadata,
    cache_background_command_result,
    cache_delete_tag,
    cache_get,
    cache_set,
    command_result_snapshot_get,
    command_result_snapshot_set,
    completed_process_from_cache,
    parse_rows_cached,
    safe_cache_tag,
)
from hhs_ui.command_catalog import (
    clean_command_status_message,
    log_filter_highlight_ranges,
    open_file,
    row_matches_text_filter,
    sanitize_remote_command_result,
    strip_ansi,
)
from hhs_ui.command_runtime import (
    background_job_is_running,
    background_job_result,
    background_job_state,
    render_background_job_status,
    run_bash_command,
    start_background_bash_command,
    stop_background_job,
)
from hhs_ui.path_picker import render_folder_picker_dialog, request_path_picker
from hhs_ui.search_core import (
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
from hhs_ui.ssh_runtime import (
    command_remote_host,
    connected_ssh_host,
    effective_bash_command,
    handle_remote_command_result,
)
from hhs_ui.status_ui import push_floating_status
from hhs_ui.table_ui import (
    clean_table_text_filter_value,
    clear_table_other_filter,
    display_path_value,
    normalize_table_text_filter_state,
)
from hhs_ui.ui_definitions import SEARCH_COMMAND_JOB, SEARCH_OPEN_JOB
from hhs_ui.ui_state import save_ui_state


def _unconfigured_dependency(name: str) -> Callable[..., object]:
    """Return a placeholder callback for dependencies configured by streamlit_ui."""

    def dependency(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"search UI dependency is not configured: {name}")

    return dependency


render_script_html = _unconfigured_dependency("render_script_html")
ui_disposable_files_dir = _unconfigured_dependency("ui_disposable_files_dir")
start_background_action_job = _unconfigured_dependency("start_background_action_job")
build_scp_to_local_command = _unconfigured_dependency("build_scp_to_local_command")
ssh_explorer_mtime_text = _unconfigured_dependency("ssh_explorer_mtime_text")
ssh_explorer_size_text = _unconfigured_dependency("ssh_explorer_size_text")
footer_working_directory = _unconfigured_dependency("footer_working_directory")


def configure_search_ui(
    *,
    render_script_html: Callable[..., None],
    ui_disposable_files_dir: Callable[[], Path],
    start_background_action_job: Callable[..., bool],
    build_scp_to_local_command: Callable[[str, str, str], str],
    ssh_explorer_mtime_text: Callable[[str], str],
    ssh_explorer_size_text: Callable[[str, str], str],
    footer_working_directory: Callable[[], str],
) -> None:
    """Configure callbacks required by Search helpers."""
    globals().update(
        {
            "render_script_html": render_script_html,
            "ui_disposable_files_dir": ui_disposable_files_dir,
            "start_background_action_job": start_background_action_job,
            "build_scp_to_local_command": build_scp_to_local_command,
            "ssh_explorer_mtime_text": ssh_explorer_mtime_text,
            "ssh_explorer_size_text": ssh_explorer_size_text,
            "footer_working_directory": footer_working_directory,
        }
    )


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
    open_command = open_file(str(local_path))
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
        open_file(path),
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
