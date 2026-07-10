#!/usr/bin/env bats

#  Script: path-picker.bats
# Purpose: HomeSetup Streamlit UI path picker tests.
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

@test "when connected over SSH then reusable path picker should list remote paths" {
  run python3 - "${ui_file}" <<'PY'
import hashlib
import os
import posixpath
import shlex
import subprocess
import sys
import textwrap
import types
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def folder_picker_start_directory(")
end = source.index("def homesetup_version(")
host = "remote-box"
statuses = []
commands = []
jobs = {}
stopped_prefixes = []
session_state = {
    "_hhs_folder_picker_mode": "file",
    "_hhs_folder_picker_current_dir": "/home/root",
    "_hhs_folder_picker_current_dir_input": "/home/root/readme.md",
}

def run_bash_command(command, *args, **kwargs):
    commands.append((command, kwargs))
    return path_picker_result(command)

def path_picker_result(command):
    if "raw_target=/home/root/app" in command:
        return subprocess.CompletedProcess(
            ["ssh"],
            0,
            "__HHS_PICKER_CWD__\t/home/root/app\n"
            "__HHS_PICKER_ENTRY__\tDir\t/home/root/app/logs\n"
            "__HHS_PICKER_ENTRY__\tDir\t/home/root/app/tmp\n",
            "",
        )
    output = (
        "__HHS_PICKER_CWD__\t/home/root\n"
        "__HHS_PICKER_ENTRY__\tDir\t/home/root/app\n"
    )
    if "picker_mode=file" in command:
        output += "__HHS_PICKER_ENTRY__\tFile\t/home/root/readme.md\n"
    return subprocess.CompletedProcess(
        ["ssh"],
        0,
        output,
        "",
    )

def background_job_state_key(job_name):
    return f"_hhs_background_job_{job_name}"

def start_background_bash_command(
    job_name,
    command,
    description,
    timeout_seconds,
    force_local=False,
    metadata=None,
    show_preloader_event=False,
):
    commands.append(
        (
            command,
            {
                "description": description,
                "timeout_seconds": timeout_seconds,
                "metadata": metadata or {},
                "show_preloader_event": show_preloader_event,
            },
        )
    )
    jobs[job_name] = (path_picker_result(command), metadata or {})
    return True

def background_job_result(job_name):
    return jobs.pop(job_name, None)

def background_job_is_running(job_name):
    return job_name in jobs

def stop_background_jobs_with_state_prefix(state_key_prefix):
    stopped_prefixes.append(state_key_prefix)
    jobs.clear()

namespace = {
    "Path": Path,
    "hashlib": hashlib,
    "os": os,
    "posixpath": posixpath,
    "shlex": shlex,
    "subprocess": subprocess,
    "textwrap": textwrap,
    "hhs_ui": types.SimpleNamespace(
        DIR_VALUE_EDITOR_KEY_PREFIX="dir_selected_value",
        UI_CACHE_REALTIME_TTL_SECONDS=1,
    ),
    "hhs_ui_constants": types.SimpleNamespace(
        FOOTER_REMOTE_WORKING_DIR_KEY="footer_remote_cwd",
        UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS=30,
    ),
    "PATH_PICKER_LISTING_JOB_PREFIX": "path_picker_listing",
    "PATH_PICKER_LISTING_LOADER_MESSAGE": "Loading directories and files...",
    "st": types.SimpleNamespace(session_state=session_state),
    "connected_ssh_host": lambda: host,
    "run_bash_command": run_bash_command,
    "background_job_state_key": background_job_state_key,
    "start_background_bash_command": start_background_bash_command,
    "background_job_result": background_job_result,
    "background_job_is_running": background_job_is_running,
    "stop_background_jobs_with_state_prefix": stop_background_jobs_with_state_prefix,
    "strip_ansi": lambda value: value,
    "push_floating_status": lambda message, level: statuses.append((message, level)),
    "clean_command_status_message": lambda value: str(value).strip(),
    "dismiss_streamlit_dialog": lambda: None,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

dialog_body = source.split("def render_path_picker_dialog", 1)[1].split("\ndef ", 1)[0]
assert "dialog_rendered = pop_dialog(" not in dialog_body
assert "folder_picker_owner_matches(owner_context)" in dialog_body
assert 'st.container(key="hhs_path_picker_overlay")' in dialog_body
assert 'st.container(key="hhs_path_picker_panel")' in dialog_body
assert 'key="folder_picker_header_close_button"' in dialog_body
assert "return True" in dialog_body
assert dialog_body.index("prepare_path_picker_dialog_listing(mode)") < dialog_body.index(
    'st.container(key="hhs_path_picker_overlay")'
)
render_body = source.split("def render_path_picker_body", 1)[1].split("\ndef ", 1)[0]
assert "current_directory = folder_picker_browsing_directory()" in render_body
assert "sync_folder_picker_child_selection(child_directories)" in render_body
assert render_body.index(
    "current_directory = folder_picker_browsing_directory()"
) < render_body.index("path_picker_child_paths(")
assert render_body.index("path_picker_child_paths(") < render_body.index(
    "st.text_input("
)
assert render_body.index(
    "sync_folder_picker_child_selection(child_directories)"
) < render_body.index("st.text_input(")
assert "st.caption(empty_caption)" not in render_body
assert "PATH_PICKER_LISTING_LOADER_MESSAGE" in render_body
assert "render_path_picker_listing_loader(loading_job_name)" in render_body
assert "disabled=loading_children" in render_body
assert "loading_children or not bool(child_directories)" in render_body
assert 'selectbox_kwargs["on_change"] = open_folder_picker_selected_child' in render_body
assert 'selectbox_kwargs["args"] = (selected_widget_key,)' in render_body
assert render_body.index("st.selectbox(") < render_body.index("st.checkbox(")
assert namespace["path_picker_uses_remote"]()
assert namespace["remote_path_picker_default_directory"]() == "$HOME"
assert namespace["folder_picker_owner_context_for_target"]("search_path") == "search"
assert namespace["folder_picker_owner_context_for_target"]("path_add_value") == "path"
assert namespace["folder_picker_owner_context_for_target"]("path_selected_value_0") == ""
assert namespace["folder_picker_owner_context_for_target"]("dir_add_value") == "dir"
assert namespace["folder_picker_owner_context_for_target"]("dir_selected_value_0") == "dir"
assert namespace["request_path_picker"]("search_path", "", "folder") is None
assert session_state["_hhs_folder_picker_owner_context"] == "search"
assert session_state["_hhs_folder_picker_current_dir"] == "$HOME"
assert session_state["_hhs_folder_picker_current_dir_input"] == "$HOME"
assert commands == []
children = namespace["path_picker_child_paths"]("$HOME", "folder", False)
assert children == []
assert len(commands) == 1
loading_job = session_state["_hhs_folder_picker_listing_loading_job"]
assert loading_job.startswith("path_picker_listing_")
assert "raw_target='$HOME'" in commands[0][0]
assert commands[0][1]["description"] == "Loading directories and files..."
assert commands[0][1]["timeout_seconds"] == 30
assert commands[0][1]["show_preloader_event"] is True
children = namespace["path_picker_child_paths"]("$HOME", "folder", False)
assert children == ["/home/root/app"]
namespace["remember_folder_picker_visible_child_paths"](children)
assert len(commands) == 1
assert "_hhs_folder_picker_listing_loading_job" not in session_state
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"
children = namespace["path_picker_child_paths"]("/home/root", "folder", False)
assert children == ["/home/root/app"]
assert len(commands) == 1

assert namespace["request_path_picker"]("search_path", "/srv", "folder") is None
assert session_state["_hhs_folder_picker_owner_context"] == "search"
assert session_state["_hhs_folder_picker_current_dir"] == "/srv"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/srv"

command_count = len(commands)
session_state["_hhs_folder_picker_mode"] = "folder"
session_state["_hhs_folder_picker_current_dir"] = "/home/root"
session_state["_hhs_folder_picker_current_dir_input"] = "/home/root"
session_state["_hhs_folder_picker_path_kinds"] = {"/home/root/app": "Dir"}
session_state["_hhs_folder_picker_selected_dir"] = "/home/root/app"
namespace["remember_folder_picker_visible_child_paths"](["/home/root/app"])
namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"
assert session_state["_hhs_folder_picker_pending_dir"] == "/home/root/app"
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app"
assert session_state["_hhs_folder_picker_path_kinds"] == {"/home/root/app": "Dir"}
assert len(commands) == command_count
assert namespace["load_pending_remote_path_picker_directory"]("folder", False) is False
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert namespace["folder_picker_visible_child_paths"]() == ["/home/root/app"]
assert len(commands) == command_count + 1
assert commands[-1][1]["show_preloader_event"] is True
assert namespace["load_pending_remote_path_picker_directory"]("folder", False) is True
assert "_hhs_folder_picker_pending_dir" not in session_state
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root/app"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/app"
children = namespace["folder_picker_visible_child_paths"]()
assert children == ["/home/root/app/logs", "/home/root/app/tmp"]
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
assert session_state["_hhs_folder_picker_path_kinds"]["/home/root/app/logs"] == "Dir"
assert len(commands) == command_count + 1
namespace["sync_folder_picker_child_selection"](
    ["/home/root/app/logs", "/home/root/app/tmp"]
)
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
namespace["sync_folder_picker_child_selection"](
    ["/home/root/app/logs", "/home/root/app/tmp"]
)
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
session_state["_hhs_folder_picker_selected_dir"] = "/home/root/app/tmp"
namespace["sync_folder_picker_child_selection"](
    ["/home/root/app/logs", "/home/root/app/tmp"]
)
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/tmp"
namespace["sync_folder_picker_child_selection"]([])
assert "_hhs_folder_picker_selected_dir" not in session_state

namespace["open_folder_picker_parent"]()
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root/app"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/app"
assert session_state["_hhs_folder_picker_pending_dir"] == "/home/root"
assert namespace["load_pending_remote_path_picker_directory"]("folder", False) is False
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root/app"
assert namespace["load_pending_remote_path_picker_directory"]("folder", False) is True
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"
assert len(commands) == command_count + 2
session_state["_hhs_folder_picker_selected_dir"] = "/home/root/app"
namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_pending_dir"] == "/home/root/app"
assert namespace["load_pending_remote_path_picker_directory"]("folder", False) is True
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root/app"
assert len(commands) == command_count + 2

session_state["_hhs_folder_picker_mode"] = "file"
session_state["_hhs_folder_picker_current_dir"] = "/home/root"
session_state["_hhs_folder_picker_current_dir_input"] = "/home/root/readme.md"
children = namespace["path_picker_child_paths"]("/home/root", "file", False)
assert children == []
children = namespace["path_picker_child_paths"]("/home/root", "file", False)
assert children == ["/home/root/app", "/home/root/readme.md"]
assert commands[-1][1]["timeout_seconds"] == 30
assert commands[-1][1]["show_preloader_event"] is True
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/readme.md"
assert session_state["_hhs_folder_picker_path_kinds"]["/home/root/readme.md"] == "File"

session_state["_hhs_folder_picker_selected_dir"] = "/home/root/readme.md"
namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/readme.md"
assert namespace["selected_folder_picker_path"]() == "/home/root/readme.md"
assert "raw_target=/home/root" in commands[-1][0]
assert statuses == []
namespace["close_folder_picker"]()
assert "_hhs_folder_picker_owner_context" not in session_state
assert stopped_prefixes
PY
  assert_success
}
@test "when local path picker opens a child folder then its children should be selected" {
  run python3 - "${ui_file}" "${BATS_TEST_TMPDIR}" <<'PY'
import hashlib
import os
import posixpath
import shlex
import subprocess
import sys
import textwrap
import types
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tmpdir = Path(sys.argv[2])
start = source.index("def folder_picker_start_directory(")
end = source.index("def homesetup_version(")
home = tmpdir / "home"
apps = home / "Applications"
alpha = apps / "alpha"
beta = apps / "Beta"
for directory in (alpha, beta):
    directory.mkdir(parents=True, exist_ok=True)
other_widget_key = "_hhs_folder_picker_selected_dir_widget_stale"
session_state = {
    "_hhs_folder_picker_mode": "folder",
    "_hhs_folder_picker_current_dir": str(home),
    "_hhs_folder_picker_current_dir_input": str(home),
    "_hhs_folder_picker_selected_dir": str(apps),
    other_widget_key: str(apps),
}

namespace = {
    "Path": Path,
    "hashlib": hashlib,
    "os": os,
    "posixpath": posixpath,
    "shlex": shlex,
    "subprocess": subprocess,
    "textwrap": textwrap,
    "hhs_ui": types.SimpleNamespace(
        DIR_VALUE_EDITOR_KEY_PREFIX="dir_selected_value",
    ),
    "st": types.SimpleNamespace(
        session_state=session_state,
    ),
    "connected_ssh_host": lambda: "",
    "dismiss_streamlit_dialog": lambda: None,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir"] == str(apps.resolve())
assert session_state["_hhs_folder_picker_current_dir_input"] == str(apps.resolve())
assert "_hhs_folder_picker_selected_dir" not in session_state
children = namespace["path_picker_child_paths"](str(apps.resolve()), "folder", False)
namespace["sync_folder_picker_child_selection"](children)
assert session_state["_hhs_folder_picker_selected_dir"] == str(alpha.resolve())

session_state["_hhs_folder_picker_current_dir"] = str(home)
session_state["_hhs_folder_picker_current_dir_input"] = str(apps)
assert namespace["folder_picker_browsing_directory"]() == str(apps.resolve())
children = namespace["path_picker_child_paths"](
    namespace["folder_picker_browsing_directory"](), "folder", False
)
assert children == [str(alpha.resolve()), str(beta.resolve())]

widget_key = namespace["folder_picker_child_selection_widget_key"](
    str(apps.resolve()), "folder", False
)
session_state[widget_key] = str(beta.resolve())
namespace["prune_folder_picker_child_selection_widget_keys"](widget_key)
assert session_state[widget_key] == str(beta.resolve())
assert other_widget_key not in session_state
assert widget_key.startswith("_hhs_folder_picker_selected_dir_widget_")

session_state["_hhs_folder_picker_mode"] = "folder"
session_state["_hhs_folder_picker_current_dir"] = str(home)
session_state["_hhs_folder_picker_current_dir_input"] = str(home)
session_state[widget_key] = str(beta.resolve())
namespace["open_folder_picker_selected_child"](widget_key)
assert session_state["_hhs_folder_picker_current_dir"] == str(beta.resolve())
assert session_state["_hhs_folder_picker_current_dir_input"] == str(beta.resolve())
assert "_hhs_folder_picker_selected_dir" not in session_state

session_state["_hhs_folder_picker_mode"] = "file"
session_state["_hhs_folder_picker_current_dir"] = str(home)
session_state["_hhs_folder_picker_current_dir_input"] = str(home)
session_state[widget_key] = str(alpha.resolve())
namespace["open_folder_picker_selected_child"](widget_key)
assert session_state["_hhs_folder_picker_current_dir"] == str(home)
assert session_state["_hhs_folder_picker_current_dir_input"] == str(home)
PY
  assert_success
}
