#!/usr/bin/env bats

#  Script: search.bats
# Purpose: HomeSetup Streamlit UI search and footer tests.
# Created: Jun 25, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

repo_dir="${BATS_TEST_DIRNAME}"
while [[ ! -f "${repo_dir}/install.bash" ]]; do
  repo_dir="${repo_dir}/.."
done
export HHS_REPO_DIR="$(cd "${repo_dir}" && pwd)"
export HHS_HOME="${HHS_REPO_DIR}"

load "${HHS_REPO_DIR}/tests/test_helper"
load_bats_libs
load "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/tests/hhs-ui-test-helpers.bash"

@test "when building Search commands then query type should choose the matching hhs helper" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import hashlib
import html
import os
import posixpath
import re
import shlex
import subprocess
import types
import urllib.parse

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
search_core_source = Path("bin/apps/py/hhs_ui/search_core.py").read_text(encoding="utf-8")
search_core_start = search_core_source.index("def search_type_label(")
start = source.index("def search_command_cache_key(")
end = source.index("def render_ai_models_result(")

def fragment(*args, **kwargs):
    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        return args[0]

    def decorator(func):
        return func

    return decorator

namespace = {
    "posixpath": posixpath,
    "re": re,
    "shlex": shlex,
    "urllib": types.SimpleNamespace(parse=urllib.parse),
    "hhs_ui": types.SimpleNamespace(
        SEARCH_OPEN_RESULT_QUERY_PARAM="hhs_open_search_result",
        SEARCH_FILTERS=("All", "Containing"),
    ),
    "hhs_ui_constants": types.SimpleNamespace(
        SEARCH_TYPES=("Files", "Folders", "Strings"),
        SEARCH_DIRECTORY_HISTORY_LIMIT=3,
        SEARCH_TERM_HISTORY_CACHE_KEY="search_terms:history",
        SEARCH_TERM_HISTORY_LIMIT=3,
        SEARCH_TERM_HISTORY_TTL_SECONDS=900,
        SEARCH_PAGE_SIZE=20,
        UI_CACHE_NORMAL_TTL_SECONDS=300,
        UI_COMMAND_SEARCH_TIMEOUT_SECONDS=300,
        UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS=30,
        SEARCH_TYPE_LABELS={
            "Files": "Files",
            "Folders": "Folders",
            "Strings": "Strings",
        },
    ),
    "st": types.SimpleNamespace(session_state={}, fragment=fragment),
    "Path": Path,
    "os": os,
    "html": html,
    "hashlib": hashlib,
    "safe_cache_tag": lambda value: value,
    "display_path_value": lambda value: value,
    "footer_working_directory": lambda: "/work/current",
    "connected_ssh_host": lambda: namespace.get("connected_host", ""),
    "build_scp_to_local_command": lambda remote_path, local_dir, host: (
        f"scp-download {host} {remote_path} {local_dir}"
    ),
    "run_bash_command": lambda command, *args, **kwargs: remote_commands.append(
        (command, kwargs)
    )
    or subprocess.CompletedProcess(
        ["remote-env"],
        0,
        "__HHS_UI_ENV__\nHOME\t/remote/home\nHHS_HOME\t/opt/hhs\n",
        "",
    ),
    "push_floating_status": lambda message, level: statuses.append((message, level)),
    "clean_command_status_message": lambda value: str(value).strip(),
    "cache_delete_tag": lambda tag: deleted_cache_tags.append(tag),
    "save_ui_state": lambda: None,
    "strip_ansi": lambda value: value,
    "ssh_explorer_mtime_text": lambda value: f"mtime:{value}",
    "ssh_explorer_size_text": lambda value, kind: (
        "2.0 KB" if value == "2048" and kind == "File" else f"{kind}:{value}"
    ),
    "row_matches_text_filter": lambda row, value: value.lower() in " ".join(
        str(item).lower() for item in row.values()
    ),
    "log_filter_highlight_ranges": lambda value, text_filter: [
        (match.start(), match.end(), "filter-match")
        for match in re.finditer(re.escape(text_filter), value, flags=re.IGNORECASE)
    ]
    if text_filter
    else [],
}
term_cache = {}
cache_writes = []
statuses = []
deleted_cache_tags = []
remote_commands = []

def cache_get(key):
    return term_cache.get(key)

def cache_set(key, value, ttl_seconds):
    cache_writes.append((key, value, ttl_seconds))
    term_cache[key] = value

namespace["cache_get"] = cache_get
namespace["cache_set"] = cache_set
exec(
    "from __future__ import annotations\n"
    + search_core_source[search_core_start:]
    + "\n"
    + source[start:end],
    namespace,
)

controls_body = source.split("def render_search_controls", 1)[1].split("\ndef ", 1)[0]
assert (
    '"Search directory",\n'
    '                options=search_directory_options(),\n'
    '                key="search_path",\n'
    '                accept_new_options=True,\n'
    '                on_change=apply_search_directory_change,\n'
    '                width="stretch",'
) in controls_body
submit_body = source.split("def submit_search_query", 1)[1].split("\ndef ", 1)[0]
type_change_body = source.split("def apply_search_type_change", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["search_replace"] = False' in type_change_body
assert 'save_ui_state()' in type_change_body
assert 'st.session_state["search_type"] =' not in submit_body
assert 'st.session_state["search_result_type"] = search_type' in submit_body
assert "query = remember_search_term(query)" in submit_body
assert "search_path = remember_search_directory(search_path)" in submit_body
assert submit_body.index("search_path = remember_search_directory(search_path)") < (
    submit_body.index('if not query:')
)
render_results_body = source.split("def render_search_results", 1)[1].split("\ndef ", 1)[0]
assert "run_bash_command(" not in render_results_body
assert "st.error(" not in render_results_body
assert 'push_floating_status(message or "Search command failed.", "error")' in render_results_body
assert "start_search_command(command, cache_key, loader_message)" in render_results_body
assert "render_background_job_status(SEARCH_COMMAND_JOB, loader_message)" in render_results_body
assert "complete_search_command_result(cache_key)" in render_results_body
assert "cached_search_command_result(command, cache_key)" in render_results_body
assert 'SEARCH_COMMAND_JOB = "search_command"' in source
assert 'SEARCH_OPEN_JOB = "search_open"' in source
assert "SEARCH_OPEN_JOB" in source.split("HOST_SWITCH_BACKGROUND_JOBS = (", 1)[1].split(")", 1)[0]
assert "SEARCH_OPEN_JOB" in source.split("CACHE_CLEAR_BACKGROUND_JOBS = (", 1)[1].split(")", 1)[0]
start_search_body = source.split("def start_search_command", 1)[1].split("\ndef ", 1)[0]
assert "hhs_ui_constants.UI_COMMAND_SEARCH_TIMEOUT_SECONDS" in start_search_body
assert "show_preloader_event=True" in start_search_body
open_local_body = source.split("def open_local_search_result_path", 1)[1].split("\ndef ", 1)[0]
open_remote_body = source.split("def open_remote_search_result_path", 1)[1].split("\ndef ", 1)[0]
start_open_body = source.split("def start_pending_search_open_action", 1)[1].split("\ndef ", 1)[0]
complete_open_body = source.split("def complete_search_open_action_job", 1)[1].split("\ndef ", 1)[0]
global_actions_body = source.split("def complete_background_action_jobs", 1)[1].split("\ndef ", 1)[0]
render_panel_body = source.split("def render_search_panel", 1)[1].split("\ndef ", 1)[0]
main_body = source.split("def main", 1)[1].split("\n\nif __name__", 1)[0]
assert "queue_search_open_action(" in open_local_body
assert "run_bash_command(" not in open_local_body
assert "queue_search_open_action(" in open_remote_body
assert "run_bash_command(" not in open_remote_body
assert "build_open_remote_search_result_command(" in open_remote_body
assert "start_background_action_job(" in start_open_body
assert "SEARCH_OPEN_JOB" in start_open_body
assert "force_local=True" in start_open_body
assert "background_job_result(SEARCH_OPEN_JOB)" in complete_open_body
assert "execute_pending_search_open_action()" in global_actions_body
assert "render_background_job_status(SEARCH_OPEN_JOB)" in render_panel_body
assert 'st.session_state.setdefault("search_open_execute_pending", None)' in main_body
assert namespace["normalized_search_type"]("Folders") == "Folders"
assert namespace["normalized_search_type"]("Unknown") == "Files"
namespace["st"].session_state["search_type"] = "Files"
namespace["st"].session_state["search_replace"] = True
namespace["apply_search_type_change"]()
assert namespace["st"].session_state["search_type"] == "Files"
assert namespace["st"].session_state["search_replace"] is False
namespace["st"].session_state["search_type"] = "Strings"
namespace["st"].session_state["search_replace"] = True
namespace["apply_search_type_change"]()
assert namespace["st"].session_state["search_replace"] is True
assert namespace["search_glob_from_query"]("report") == "*report*"
assert namespace["search_glob_from_query"]("*.md") == "*.md"
local_home = str(Path.home().resolve())
assert namespace["default_search_directory"]() == local_home
namespace["st"].session_state["search_path"] = "/persisted/path"
namespace["st"].session_state["search_directories"] = ["/persisted/path", "/tmp"]
namespace["st"].session_state["_hhs_search_home_context"] = "ssh:old-box"
namespace["initialize_search_directory_home_default"]()
assert namespace["st"].session_state["search_path"] == "/persisted/path"
assert namespace["st"].session_state.get("search_result_path", "") == ""
assert namespace["st"].session_state.get("search_result_query", "") == ""
assert namespace["st"].session_state["_hhs_search_home_context"] == "local"
namespace["st"].session_state["search_path"] = "$HOME/projects"
assert namespace["remember_search_directory"]("$HOME/projects") == f"{local_home}/projects"
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_result_query"] = "homeselect"
namespace["initialize_search_directory_home_default"]()
assert namespace["st"].session_state["search_path"] == "/srv/homeselect"
namespace["connected_host"] = "remote-box"
namespace["reset_search_directory_to_home"]()
assert namespace["st"].session_state["search_path"] == "/remote/home"
assert namespace["st"].session_state["search_result_query"] == ""
assert namespace["st"].session_state["_hhs_search_home_context"] == "ssh:remote-box"
assert any("__HHS_UI_ENV__" in command for command, _kwargs in remote_commands)
assert namespace["remember_search_directory"]("$HHS_HOME/projects") == "/opt/hhs/projects"
assert namespace["normalize_search_directories"](
    ["/tmp", " /var ", "/tmp", "", "/opt"],
    "/home",
) == ["/home", "/tmp", "/var"]
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_directories"] = ["/tmp", "/var"]
assert namespace["search_directory_options"]() == ["/srv/homeselect", "/tmp", "/var"]
assert namespace["st"].session_state["search_path"] == "/srv/homeselect"
namespace["st"].session_state["search_query"] = None
namespace["st"].session_state["search_path"] = "$HHS_HOME/selected"
namespace["st"].session_state["search_result_query"] = "*.mp4"
namespace["st"].session_state["search_result_path"] = "/old/search/root"
statuses_before = list(statuses)
namespace["apply_search_directory_change"]()
assert namespace["st"].session_state["search_path"] == "/opt/hhs/selected"
assert namespace["st"].session_state["search_result_path"] == "/opt/hhs/selected"
assert namespace["st"].session_state["search_result_query"] == ""
assert namespace["st"].session_state["search_directories"] == [
    "/opt/hhs/selected",
    "/srv/homeselect",
    "/tmp",
]
assert statuses == statuses_before
namespace["st"].session_state["search_query"] = None
namespace["st"].session_state["search_path"] = ""
namespace["submit_search_query"]()
assert namespace["st"].session_state["search_directories"] == [
    "/remote/home",
    "/opt/hhs/selected",
    "/srv/homeselect",
]
assert namespace["st"].session_state["search_result_query"] == ""
assert statuses[-1] == ("Enter a search query before searching.", "warn")
namespace["st"].session_state["search_query"] = "homeselect"
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_type"] = "Files"
namespace["submit_search_query"]()
assert namespace["st"].session_state["search_result_query"] == "homeselect"
assert namespace["st"].session_state["search_result_path"] == "/srv/homeselect"
assert deleted_cache_tags[-1] == "search"
namespace["st"].session_state["search_query"] = "needle"
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_type"] = "Strings"
namespace["st"].session_state["search_replace"] = True
namespace["st"].session_state["search_replacement"] = "replacement value"
namespace["submit_search_query"]()
assert namespace["st"].session_state["search_result_query"] == "needle"
assert namespace["st"].session_state["search_result_replace"] is False
assert namespace["st"].session_state["search_result_replacement"] == ""
normal_result_command = namespace["build_hhs_search_command"](
    namespace["st"].session_state["search_result_type"],
    namespace["st"].session_state["search_result_query"],
    namespace["st"].session_state["search_result_path"],
    namespace["st"].session_state["search_result_ignore_case"],
    namespace["st"].session_state["search_result_words"],
    namespace["st"].session_state["search_result_binary"],
    namespace["st"].session_state["search_result_replace"],
    namespace["st"].session_state["search_result_replacement"],
)
assert " -r " not in normal_result_command
namespace["submit_search_query"](True)
assert namespace["st"].session_state["search_result_query"] == "needle"
assert namespace["st"].session_state["search_result_replace"] is True
assert namespace["st"].session_state["search_result_replacement"] == "replacement value"
replace_result_command = namespace["build_hhs_search_command"](
    namespace["st"].session_state["search_result_type"],
    namespace["st"].session_state["search_result_query"],
    namespace["st"].session_state["search_result_path"],
    namespace["st"].session_state["search_result_ignore_case"],
    namespace["st"].session_state["search_result_words"],
    namespace["st"].session_state["search_result_binary"],
    namespace["st"].session_state["search_result_replace"],
    namespace["st"].session_state["search_result_replacement"],
)
assert " -r 'replacement value' needle '*'" in replace_result_command
namespace["st"].session_state["search_replacement"] = ""
statuses.clear()
namespace["submit_search_query"](True)
assert statuses[-1] == ("Enter replacement text before replacing.", "warn")
assert namespace["normalize_search_terms"](
    ["admin", " saridon ", "admin", "", "root"],
    "needle",
) == ["needle", "admin", "saridon"]
assert namespace["clean_search_term_value"](None) == ""
assert namespace["clean_search_term_value"]("None") == ""
assert namespace["normalize_search_terms"](["None", None, "admin"], None) == ["admin"]
namespace["st"].session_state["search_query"] = None
term_cache["search_terms:history"] = {"terms": ["saridon", "admin"]}
assert namespace["search_term_options"]() == ["saridon", "admin"]
assert namespace["st"].session_state["search_query"] is None
term_cache.clear()
cache_writes.clear()
namespace["st"].session_state["search_query"] = "admin"
assert namespace["search_term_options"]() == ["admin"]
assert namespace["remember_search_term"](" saridon ") == "saridon"
assert term_cache["search_terms:history"]["terms"] == ["saridon"]
assert cache_writes[-1] == (
    "search_terms:history",
    {"terms": ["saridon"]},
    900,
)
assert namespace["remember_search_term"](" admin ") == "admin"
assert term_cache["search_terms:history"]["terms"] == ["admin", "saridon"]
assert namespace["remember_search_term"]("saridon") == "saridon"
assert term_cache["search_terms:history"]["terms"] == ["saridon", "admin"]
namespace["st"].session_state["search_query"] = "None"
term_cache["search_terms:history"] = {"terms": ["None", "admin", None]}
assert namespace["search_term_options"]() == ["admin"]
assert namespace["st"].session_state["search_query"] is None
assert namespace["remember_search_term"](None) == ""
assert namespace["st"].session_state["search_query"] is None
assert namespace["normalized_search_option_values"]("Files", True, True, True) == (
    False,
    False,
    False,
    False,
    "",
)
assert namespace["normalized_search_option_values"]("Strings", True, False, True) == (
    True,
    False,
    True,
    False,
    "",
)
assert namespace["normalized_search_option_values"](
    "Strings", True, True, True, True, "replacement value"
) == (
    True,
    False,
    True,
    True,
    "replacement value",
)
assert namespace["search_string_option_flags"](True, True, True) == ["-i", "-w", "-b"]
assert namespace["search_string_option_flags"](
    True, False, True, True, "replacement value"
) == ["-i", "-b", "-r", "replacement value"]
files_command = namespace["build_hhs_search_command"](
    "Files", "report", "/tmp/search root"
)
folders_command = namespace["build_hhs_search_command"](
    "Folders", "docs", "/tmp/search root"
)
strings_command = namespace["build_hhs_search_command"](
    "Strings", "needle value", "/tmp/search root"
)
strings_options_command = namespace["build_hhs_search_command"](
    "Strings", "needle value", "/tmp/search root", True, True, True
)
strings_replace_command = namespace["build_hhs_search_command"](
    "Strings",
    "needle value",
    "/tmp/search root",
    True,
    True,
    True,
    True,
    "replacement value",
)
home_files_command = namespace["build_hhs_search_command"]("Files", "report", "$HOME")
home_child_command = namespace["build_hhs_search_command"](
    "Files", "report", "$HOME/Project Files"
)
for command in (files_command, folders_command, strings_command):
    assert 'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash";' in command
    assert 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-text.bash";' in command
    assert 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-search.bash";' in command
    assert "function __hhs_highlight() { cat -; };" in command
assert "__hhs_search_file '/tmp/search root' '*report*'" in files_command
assert "__HHS_SEARCH_RESULT__" in files_command
assert "stat -c %s" in files_command
assert '""|Searching\\ for*) ;;' in files_command
assert "__hhs_search_dir '/tmp/search root' '*docs*'" in folders_command
assert "__HHS_SEARCH_RESULT__" in folders_command
assert strings_command.endswith("__hhs_search_string '/tmp/search root' 'needle value' '*'")
assert strings_options_command.endswith(
    "__hhs_search_string '/tmp/search root' -i -w -b 'needle value' '*'"
)
assert strings_replace_command.endswith(
    "__hhs_search_string '/tmp/search root' -i -b -r 'replacement value' 'needle value' '*'"
)
assert namespace["search_replace_status_message"](0) == "0 entries replaced"
assert namespace["search_replace_status_message"](1) == "1 entry replaced"
assert namespace["search_replace_status_message"](2) == "2 entries replaced"
statuses.clear()
namespace["st"].session_state.pop("_search_replace_status_cache_key", None)
namespace["push_search_replace_status"]("replace-cache", 2)
assert statuses == [("2 entries replaced", "info")]
namespace["push_search_replace_status"]("replace-cache", 3)
assert statuses == [("2 entries replaced", "info")]
assert '__hhs_search_file "${HOME:-.}"' in home_files_command
assert '__hhs_search_file "${HOME:-.}"/' in home_child_command
assert "'Project Files'" in home_child_command
assert "__HHS_SEARCH_RESULT__" not in strings_command
assert namespace["search_command_cache_key"]("Files", "*.mp4", "/tmp/search root") == (
    "command_tag:search:"
    + hashlib.md5(
        "Files\n*.mp4\n/tmp/search root\nFalse\nFalse\nFalse".encode("utf-8")
        + b"\nFalse\n"
    ).hexdigest()
)
assert namespace["search_command_cache_key"](
    "Strings", "needle", "/tmp/search root", True, True, True
) == (
    "command_tag:search:"
    + hashlib.md5(
        "Strings\nneedle\n/tmp/search root\nTrue\nTrue\nTrue\nFalse\n".encode("utf-8")
    ).hexdigest()
)
assert namespace["search_command_cache_key"](
    "Strings",
    "needle",
    "/tmp/search root",
    True,
    True,
    True,
    True,
    "replacement value",
) == (
    "command_tag:search:"
    + hashlib.md5(
        "Strings\nneedle\n/tmp/search root\nTrue\nFalse\nTrue\nTrue\nreplacement value".encode(
            "utf-8"
        )
    ).hexdigest()
)
namespace["st"].session_state.update(
    {
        "search_result_type": "Files",
        "search_result_path": "/tmp/search root",
        "search_result_query": "needle",
        "search_result_ignore_case": False,
        "search_result_words": False,
        "search_result_binary": False,
        "search_filter": "All",
    }
)
namespace["complete_search_command_result"] = lambda _cache_key: subprocess.CompletedProcess(
    ["search"],
    124,
    "",
    "Command timed out after 120 seconds.",
)
namespace["cached_search_command_result"] = lambda *_args: None
statuses.clear()
namespace["render_search_results"]()
assert statuses == [("Command timed out after 120 seconds.", "error")]
open_command = namespace["build_hhs_open_search_result_command"](
    "/tmp/search root/report.txt"
)
assert 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash";' in open_command
assert "__hhs_open '/tmp/search root/report.txt'" in open_command
assert (
    namespace["search_result_download_name"]("/tmp/search root/report.txt")
    == "report.txt"
)
assert namespace["search_result_download_name"]("/") == "search-result"
assert (
    str(
        namespace["search_result_download_path"](
            "/remote/report.txt",
            Path("/tmp/hhs-open"),
        )
    )
    == "/tmp/hhs-open/report.txt"
)

namespace["create_search_result_download_dir"] = lambda: Path(
    "/tmp/hhs-search-open.dir"
)
namespace["st"].session_state.pop("search_open_execute_pending", None)
statuses.clear()
namespace["connected_host"] = ""
namespace["open_search_result_path"]("/tmp/search root/report.txt")
local_open_pending = namespace["st"].session_state["search_open_execute_pending"]
assert local_open_pending["action"] == "local_open"
assert local_open_pending["path"] == "/tmp/search root/report.txt"
assert local_open_pending["description"] == "Opening /tmp/search root/report.txt"
assert local_open_pending["command"].endswith("__hhs_open '/tmp/search root/report.txt'")
assert statuses == []

namespace["st"].session_state.pop("search_open_execute_pending", None)
statuses.clear()
namespace["connected_host"] = "remote-box"
namespace["open_search_result_path"]("/remote/report.txt")
remote_open_pending = namespace["st"].session_state["search_open_execute_pending"]
assert remote_open_pending["action"] == "remote_open"
assert remote_open_pending["path"] == "/remote/report.txt"
assert remote_open_pending["host"] == "remote-box"
assert remote_open_pending["local_path"] == "/tmp/hhs-search-open.dir/report.txt"
assert remote_open_pending["description"] == "Opening remote result /remote/report.txt"
assert remote_open_pending["command"] == (
    "scp-download remote-box /remote/report.txt /tmp/hhs-search-open.dir"
    " && "
    'export HHS_DIR="${HHS_DIR}"; '
    'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
    'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
    "__hhs_open /tmp/hhs-search-open.dir/report.txt"
)
assert statuses == []
assert namespace["search_relative_path"](
    "/tmp/search root/docs/report.txt", "/tmp/search root"
) == "docs/report.txt"
assert namespace["search_relative_path"](
    "/tmp/other/report.txt", "/tmp/search root"
) == "/tmp/other/report.txt"
string_rows = namespace["parse_hhs_search_results"](
    'Searching for "regex" matching: "target" in "."\n'
    "/tmp/search root/report.txt:12:Alpha target line\n",
    "Strings",
    "/tmp/search root",
)
assert string_rows == [
    {
        "Type": "String",
        "Path": "report.txt",
        "FullPath": "/tmp/search root/report.txt",
        "Modified": "",
        "Size": "",
        "Line": "12",
        "LineNumber": "",
        "Match": "Alpha target line",
    }
]
assert namespace["parse_hhs_search_results"](
    "Searching for %primary_color%homeselect%primary_color% "
    "in %secondary_color%${HHS_HOME}%secondary_color%\n",
    "Files",
    "/tmp/search root",
) == []
assert namespace["parse_hhs_search_results"](
    '__HHS_SEARCH_RESULT__\tSearching for files matching: "*homeselect*" '
    'in "${HHS_HOME}"\t0\t\n',
    "Files",
    "/tmp/search root",
) == []
file_rows = namespace["parse_hhs_search_results"](
    "Searching for files matching: [movie] in .\n"
    "__HHS_SEARCH_RESULT__\t/tmp/search root/movie.mp4\t1710000000\t2048\n",
    "Files",
    "/tmp/search root",
)
assert file_rows == [
    {
        "Type": "File",
        "Path": "movie.mp4",
        "FullPath": "/tmp/search root/movie.mp4",
        "Modified": "mtime:1710000000",
        "Size": "2.0 KB",
        "Line": "",
        "LineNumber": "",
        "Match": "",
    }
]
folder_rows = namespace["parse_hhs_search_results"](
    "Searching for folders matching: [docs] in .\n"
    "__HHS_SEARCH_RESULT__\t/tmp/search root/docs\t1710000000\t\n",
    "Folders",
    "/tmp/search root",
)
assert folder_rows == [
    {
        "Type": "Folder",
        "Path": "docs",
        "FullPath": "/tmp/search root/docs",
        "Modified": "mtime:1710000000",
        "Size": "",
        "Line": "",
        "LineNumber": "",
        "Match": "",
    }
]
assert namespace["search_result_headers"]("Files") == ["Path", "Size", "Modified"]
assert namespace["search_result_headers"]("Folders") == ["Path", "Modified"]
assert namespace["search_result_headers"]("Strings") == ["Path", "Line", "Match"]
assert namespace["search_result_index_width"](0) == "1ch"
assert namespace["search_result_index_width"](9) == "1ch"
assert namespace["search_result_index_width"](100) == "3ch"
assert namespace["search_result_index_header"](100) == (
    '<th class="hhs-search-result-index" style="width: 3ch;"></th>'
)
assert namespace["search_result_index_cell"](12) == (
    '<td class="hhs-search-result-index">12</td>'
)
link = namespace["search_result_path_link"](string_rows[0])
assert 'class="hhs-search-result-path-link"' in link
assert "hhs_open_search_result=%2Ftmp%2Fsearch+root%2Freport.txt" in link
assert 'title="/tmp/search root/report.txt"' in link
assert 'data-hhs-open-path="/tmp/search root/report.txt"' in link
assert ">report.txt</a>" in link
rows = [{"Path": str(index)} for index in range(45)]
assert len(namespace["visible_search_rows"](rows)) == 20
namespace["increase_search_visible_count"]()
assert len(namespace["visible_search_rows"](rows)) == 40
assert namespace["search_loader_message"]("*.md", "/tmp/search root") == (
    "Searching for %primary_color%*.md%primary_color% "
    "in %secondary_color%/tmp/search root%secondary_color%"
)
assert namespace["filter_search_rows"](string_rows, "All", "missing") == string_rows
assert namespace["filter_search_rows"](string_rows, "Containing", "target") == string_rows
assert namespace["filter_search_rows"](string_rows, "Containing", "missing") == []
highlighted_line = namespace["colorize_search_result_line"](
    "Alpha target line", "target"
)
assert '<span class="hhs-log-filter-match">target</span>' in highlighted_line
PY
  assert_success
}

@test "when parsing footer working directory then startup banners should be ignored" {
  run python3 - "${ui_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def parse_footer_working_directory_output(")
end = source.index("def footer_working_directory(")
namespace = {
    "strip_ansi": lambda value: re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value),
}
exec(source[start:end], namespace)

noisy_output = (
    "[bash] HomeSetup is starting...\r\n"
    "[Linux-ubuntu/bash] Welcome root to HomeSetup v1.9.18\r\n"
    "__HHS_UI_PWD__/root\r\n"
)
assert namespace["parse_footer_working_directory_output"](noisy_output) == "/root"
assert namespace["parse_footer_working_directory_output"]("banner only") == ""
PY
  assert_success
}

@test "when rendering footer working directory then local cwd should not issue pwd" {
  run python3 - "${ui_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def footer_working_directory(")
end = source.index("def run_hhs_updater_check(")
session_state = {}
namespace = {
    "hhs_ui_constants": SimpleNamespace(
        FOOTER_LOCAL_WORKING_DIR_KEY="_hhs_footer_local_working_dir",
        FOOTER_REMOTE_WORKING_DIR_KEY="_hhs_footer_remote_working_dir",
    ),
    "sync_ttyd_event_state": lambda: None,
    "st": SimpleNamespace(session_state=session_state),
    "os": SimpleNamespace(getcwd=lambda: "/local/cwd"),
}
exec(source[start:end], namespace)

assert namespace["footer_working_directory"]() == "/local/cwd"
session_state["_hhs_footer_local_working_dir"] = "/terminal/local"
assert namespace["footer_working_directory"]() == "/terminal/local"
session_state["ssh_connection_status"] = "connected"
assert namespace["footer_working_directory"]() == "/local/cwd"
session_state["_hhs_footer_remote_working_dir"] = "/remote/cwd"
assert namespace["footer_working_directory"]() == "/remote/cwd"
PY
  assert_success
}

@test "when checking updates then updater should refresh installed version from .VERSION" {
  local updater_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/updater/updater.bash"

  assert_file_contains_many "${updater_file}" \
'refresh_hhs_version' "https://raw.githubusercontent.com/HS-Teams/homesetup/master/.VERSION"
  assert_file_not_contains "${updater_file}" "https://github.com/HS-Teams/homesetup/blob/master/.VERSION"

  assert_file_contains_many "${updater_file}" \
'HHS_VERSION="$(grep -m 1 . "${version_file}")"' 'export HHS_VERSION' 'cmd="$1"' 'refresh_hhs_version'
  assert_file_contains_many "${ui_file}" \
'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")";' \
    'build_homesetup_version_command()' 'FOOTER_VERSION_CACHE_TAG = "footer_version"' \
    'st.session_state.setdefault("footer_hhs_version_cache_loaded", False)'
}

@test "when parsing Docker command output then tables should preserve columns" {
  run python3 - "${command_catalog_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def escape_markdown_table_cell(")
end = source.index("def ssh_shared_connection_closed(")
namespace = {"re": re, "strip_ansi": lambda value: value}
exec(source[start:end], namespace)

sample = (
    "CONTAINER ID   IMAGE                          COMMAND                  CREATED      STATUS       PORTS                    NAMES\n"
    "f9eae755ef6e   yorevs/homeselect:ui-0.0.7.6   \"/docker-entrypoint\"   2 days ago   Up 2 days    127.0.0.1:8888->80/tcp   homeselect-webapp\n"
)

rows = namespace["docker_cli_table_rows"](sample)
assert rows == [
    {
        "CONTAINER ID": "f9eae755ef6e",
        "IMAGE": "yorevs/homeselect:ui-0.0.7.6",
        "COMMAND": "\"/docker-entrypoint\"",
        "CREATED": "2 days ago",
        "STATUS": "Up 2 days",
        "PORTS": "127.0.0.1:8888->80/tcp",
        "NAMES": "homeselect-webapp",
    }
]
containers_rows = namespace["docker_cli_table_rows"](
    sample, omitted_columns=("COMMAND", "PORTS")
)
assert containers_rows == [
    {
        "CONTAINER ID": "f9eae755ef6e",
        "IMAGE": "yorevs/homeselect:ui-0.0.7.6",
        "CREATED": "2 days ago",
        "STATUS": "Up 2 days",
        "NAMES": "homeselect-webapp",
    }
]
assert namespace["docker_container_is_up"](containers_rows[0]) is True
assert namespace["docker_container_is_up"]({"STATUS": "Exited (0) 2 hours ago"}) is False
remote_output = (
    "[bash] HomeSetup is starting...\n"
    "[Linux-ubuntu/bash] Welcome root to HomeSetup v1.9.18\n"
    + sample
)
remote_rows = namespace["docker_cli_table_rows"](
    remote_output, omitted_columns=("COMMAND", "PORTS")
)
assert remote_rows[0]["NAMES"] == "homeselect-webapp"
image_sample = (
    "REPOSITORY            TAG          IMAGE ID       CREATED       SIZE\n"
    "yorevs/homeselect     api-0.0.7.6  a1b2c3d4e5f6   2 days ago    314MB\n"
)
image_rows = namespace["docker_cli_table_rows"](
    "[bash] HomeSetup is starting...\n"
    "[Linux-ubuntu/bash] Welcome root to HomeSetup v1.9.18\n"
    + image_sample
)
assert image_rows == [
    {
        "REPOSITORY": "yorevs/homeselect",
        "TAG": "api-0.0.7.6",
        "IMAGE ID": "a1b2c3d4e5f6",
        "CREATED": "2 days ago",
        "SIZE": "314MB",
    }
]
formatted_image_sample = (
    "REPOSITORY\tTAG\tIMAGE ID\tSIZE\tCREATED AT\n"
    "yorevs/homeselect\tui-0.0.7.6\tf6b43e69bb9b\t203MB\t2026-06-19 00:21:26 -0300 -03\n"
)
formatted_image_rows = namespace["docker_cli_table_rows"](
    "[bash] HomeSetup is starting...\n" + formatted_image_sample
)
assert formatted_image_rows == [
    {
        "REPOSITORY": "yorevs/homeselect",
        "TAG": "ui-0.0.7.6",
        "IMAGE ID": "f6b43e69bb9b",
        "SIZE": "203MB",
        "CREATED AT": "2026-06-19 00:21:26 -0300 -03",
    }
]
assert namespace["docker_cli_table_rows"]("") == []
PY
  assert_success
}

# TC - 19

@test "when rendering UI then deprecated table approaches should stay removed" {
  run python3 - "${HHS_REPO_DIR}/bin/apps/py" <<'PY'
import ast
from pathlib import Path
import sys

matches = []
for path in Path(sys.argv[1]).rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "TextColumn":
            continue
        disabled = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "disabled"),
            None,
        )
        if not isinstance(disabled, ast.Constant) or disabled.value is not True:
            matches.append(f"{path}:{node.lineno}: TextColumn missing disabled=True")
if matches:
    raise SystemExit("deprecated or editable table source found: " + ", ".join(matches))
PY
  assert_success

  assert_file_not_contains_many "${ui_file}" \
'st.table(' 'use_container_width' 'st.form(' 'st.form_submit_button(' 'render_env_table_html'
  assert_file_not_contains_many "${css_file}" \
'hhs-env-table-scroll' '<style>'
}

# TC - 20

@test "when rendering keyed widgets then session state should not also be passed as defaults" {
  assert_file_not_contains_many "${ui_file}" \
'default=st.session_state' 'value=st.session_state' 'index=.*session_state'
  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
body = source.split("def render_table_filter_controls", 1)[1].split("\ndef ", 1)[0]
assert "st.session_state[key] = options[safe_index]" in body
assert "index=None" in body
assert "index=index" not in body
search_filter_body = source.split("def render_search_filters", 1)[1].split("\ndef ", 1)[0]
assert "key=\"search_filter\"" in search_filter_body
assert "index=None" in search_filter_body
main_view_body = source.split("def render_main_view", 1)[1].split("\ndef ", 1)[0]
active_control_body = source.split("def render_active_view_control", 1)[1].split("\ndef ", 1)[0]
assert "render_active_view_control(visible_views)" in main_view_body
assert "key=widget_key" in active_control_body
assert "index=None" in active_control_body
assert "on_change=save_active_view_state" in active_control_body
PY
  assert_success
}
