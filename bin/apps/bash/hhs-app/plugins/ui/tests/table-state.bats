#!/usr/bin/env bats

#  Script: table-state.bats
# Purpose: HomeSetup Streamlit UI table state and cache tests.
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

@test "when selecting table rows then command overlays should be suppressed" {
  run python3 - "${table_ui_file}" "${ui_file}" "${cache_runtime_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

table_source = Path(sys.argv[1]).read_text(encoding="utf-8")
ui_source = Path(sys.argv[2]).read_text(encoding="utf-8")
cache_runtime_source = Path(sys.argv[3]).read_text(encoding="utf-8")
start = table_source.index("def table_selection_key_prefixes()")
end = table_source.index("def render_table(")
session_state = {
    "_hhs_table_selection_snapshots": {
        "env_vars_table_0": (),
        "docker_container_table_0": (1,),
    },
    "env_vars_table_0": {"selection": {"rows": [2]}},
    "docker_container_table_0": {"selection": {"rows": [1]}},
}
namespace = {
    "hhs_ui": SimpleNamespace(
        AI_MODEL_TABLE_KEY="ai_model_table",
        ALIAS_TABLE_KEY="alias_vars_table",
        CMD_TABLE_KEY="cmd_vars_table",
        DIR_TABLE_KEY="dir_vars_table",
        DOCKER_CONTAINER_TABLE_KEY="docker_container_table",
        DOCKER_IMAGE_TABLE_KEY="docker_image_table",
        ENV_TABLE_KEY="env_vars_table",
        HISTORY_COMMAND_TABLE_KEY="history_command_vars_table",
        HISTORY_DIRECTORY_TABLE_KEY="history_directory_vars_table",
        HOME_SHOPTS_TABLE_KEY="home_shopts_table",
        HOME_TOOLS_TABLE_KEY="home_tools_table",
        HHS_RESET_TABLE_KEY="hhs_reset_targets",
        PATH_TABLE_KEY="path_vars_table",
        PROCESS_TABLE_KEY="monitor_process_table",
        SERVICE_TABLE_KEY="service_vars_table",
        SSH_TUNNEL_TABLE_KEY="ssh_tunnel_table",
    ),
    "hhs_ui_constants": SimpleNamespace(
        TABLE_SELECTION_SNAPSHOT_KEY="_hhs_table_selection_snapshots",
    ),
    "st": SimpleNamespace(session_state=session_state),
}
exec("from __future__ import annotations\n" + table_source[start:end], namespace)

assert namespace["table_selection_widget_key"]("env_vars_table_0") is True
assert namespace["table_selection_widget_key"](
    "hhs_reset_targets_markdown_table_editor_v4_row_selection"
) is True
assert namespace["table_selection_widget_key"]("unrelated") is False
assert namespace["table_selection_rows"]({"selection": {"rows": [2]}}) == (2,)
assert namespace["table_selection_rerun_in_progress"]() is True
namespace["remember_table_selection"]("env_vars_table_0", {"selection": {"rows": [2]}})
assert namespace["table_selection_rerun_in_progress"]() is False

snapshot_start = cache_runtime_source.index("def command_result_snapshots()")
snapshot_end = cache_runtime_source.index("def cache_set(")
snapshot_namespace = {
    "st": SimpleNamespace(session_state={}),
    "hhs_ui_constants": SimpleNamespace(
        COMMAND_RESULT_SNAPSHOT_KEY="_hhs_command_result_snapshots",
        COMMAND_RESULT_SNAPSHOT_LIMIT=2,
    ),
    "safe_cache_tag": lambda value: value,
}
exec(
    "from __future__ import annotations\n"
    + cache_runtime_source[snapshot_start:snapshot_end],
    snapshot_namespace,
)
snapshot_namespace["command_result_snapshot_set"]("command_tag:docker:one", {"stdout": "one"})
snapshot_namespace["command_result_snapshot_set"]("command_tag:docker:two", {"stdout": "two"})
snapshot_namespace["command_result_snapshot_set"]("command_tag:docker:three", {"stdout": "three"})
assert snapshot_namespace["command_result_snapshot_get"]("command_tag:docker:one") is None
assert snapshot_namespace["command_result_snapshot_get"]("command_tag:docker:three")["stdout"] == "three"
snapshot_namespace["command_result_snapshot_delete_tag"]("docker")
assert snapshot_namespace["command_result_snapshot_get"]("command_tag:docker:three") is None
PY
  assert_success
}
@test "when rerendering command tables then parsed rows should be cached in session state" {
  run python3 - "${cache_runtime_file}" <<'PY'
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def command_result_snapshots()")
end = source.index("def cache_set(")
session_state = {}
namespace = {
    "hashlib": hashlib,
    "st": SimpleNamespace(session_state=session_state),
    "hhs_ui_constants": SimpleNamespace(
        COMMAND_RESULT_SNAPSHOT_KEY="_hhs_command_result_snapshots",
        COMMAND_RESULT_SNAPSHOT_LIMIT=2,
        PARSED_ROWS_CACHE_KEY="_hhs_parsed_rows_cache",
        PARSED_ROWS_CACHE_LIMIT=2,
        LOG_RENDER_CACHE_KEY="_hhs_log_render_cache",
        LOG_RENDER_CACHE_LIMIT=2,
    ),
    "filter_log_output": lambda output, _filter, text: output.replace(text, text.upper()),
    "colorize_log_output": lambda output, highlight: f"{highlight}:{output}",
    "safe_cache_tag": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

calls = []

def parser(output):
    calls.append(output)
    return [{"Name": output}]

first = namespace["parse_rows_cached"]("sample", "one", parser)
second = namespace["parse_rows_cached"]("sample", "one", parser)
assert first == [{"Name": "one"}]
assert second == [{"Name": "one"}]
assert calls == ["one"]

first[0]["Name"] = "mutated"
third = namespace["parse_rows_cached"]("sample", "one", parser)
assert third == [{"Name": "one"}]
fourth = namespace["parse_rows_cached"]("sample", "two", parser)
assert fourth == [{"Name": "two"}]
assert calls == ["one", "two"]

rendered = namespace["rendered_log_output_cached"]("hello needle", "Containing", "needle")
cached = namespace["rendered_log_output_cached"]("hello needle", "Containing", "needle")
assert rendered == "needle:hello NEEDLE"
assert cached == rendered
PY
  assert_success
}
@test "when reading UI cache then expired entries should not be written back during load" {
  assert_file_contains_many "${cache_runtime_file}" \
'key.startswith("search_terms:")' 'def ui_cache_preserved_on_clear_key' \
    'hhs_ui_constants.SEARCH_TERM_HISTORY_CACHE_KEY' 'if ui_cache_preserved_on_clear_key(key)'
  run python3 - "${cache_runtime_file}" <<'PY'
import ast
import sys
from pathlib import Path

tree = ast.parse(Path(sys.argv[1]).read_text(encoding="utf-8"))

for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "load_ui_cache":
        load_ui_cache = node
        break
else:
    raise AssertionError("load_ui_cache not found")

save_calls = [
    call
    for call in ast.walk(load_ui_cache)
    if isinstance(call, ast.Call)
    and isinstance(call.func, ast.Name)
    and call.func.id == "save_ui_cache"
]
assert save_calls == []
PY
  assert_success
}

@test "when synchronizing UI persistence then stale state and cache entries should be removed" {
  run python3 - "${ui_state_file}" "${cache_runtime_file}" "${constants_file}" <<'PY'
import ast
import json
import sys
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

def load_functions(source_path, names, namespace):
    tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__",
                names=[ast.alias(name="annotations")],
                level=0,
            ),
            *functions,
        ],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(source_path), "exec"), namespace)

constants_tree = ast.parse(Path(sys.argv[3]).read_text(encoding="utf-8"))
constants = {}
for node in constants_tree.body:
    if not (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        continue
    try:
        constants[node.targets[0].id] = ast.literal_eval(node.value)
    except (ValueError, TypeError):
        continue

with tempfile.TemporaryDirectory() as tmp_dir:
    cache_dir = Path(tmp_dir)
    state_file = cache_dir / "streamlit-ui-state.json"
    cache_file = cache_dir / "streamlit-ui-cache.json"
    persisted_keys = tuple(
        value.value
        for node in constants_tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "PERSISTED_UI_KEYS"
        for value in node.value.elts
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    )
    state_constants = SimpleNamespace(
        HHS_CACHE_DIR=cache_dir,
        UI_STATE_FILE=state_file,
        PERSISTED_UI_KEYS=persisted_keys,
        PERSISTED_UI_KEY_PREFIXES=constants["PERSISTED_UI_KEY_PREFIXES"],
        THEME_SELECTED_KEY="theme_selected",
    )
    state_namespace = {
        "json": json,
        "lru_cache": lru_cache,
        "Path": Path,
        "hhs_ui_constants": state_constants,
        "st": SimpleNamespace(session_state={"active_view": "Home"}),
        "validated_theme_name": lambda value: value if isinstance(value, str) else "",
    }
    load_functions(
        sys.argv[1],
        {
            "is_persisted_ui_key",
            "is_persistable_ui_value",
            "cached_ui_state_file",
            "read_ui_state_file",
            "load_ui_state",
            "ui_state_files",
            "legacy_ui_state_files",
            "unlink_legacy_ui_state_files",
            "ui_state_source_file",
            "ui_state_file_is_synchronized",
            "save_ui_state",
        },
        state_namespace,
    )

    state_file.write_text(
        json.dumps(
            {
                "active_view": "Home",
                "ai_clear_chat_execute_pending": True,
                "stale_state_key": "remove me",
            }
        ),
        encoding="utf-8",
    )
    state_namespace["save_ui_state"]()
    assert json.loads(state_file.read_text(encoding="utf-8")) == {
        "active_view": "Home"
    }

    now = time.time()
    cache_file.write_text(
        json.dumps(
            {
                "command_tag:active:abc": {
                    "expires_at": now + 60,
                    "value": {"stdout": "active"},
                },
                "command_tag:expired:def": {
                    "expires_at": now - 60,
                    "value": {"stdout": "expired"},
                },
                "command_hash:legacy": {
                    "expires_at": now + 60,
                    "value": {"stdout": "legacy"},
                },
                "unsupported": {"value": {}},
            }
        ),
        encoding="utf-8",
    )
    cache_hhs_ui = SimpleNamespace(
        HHS_CACHE_DIR=cache_dir,
        UI_CACHE_FILE=cache_file,
        UI_CACHE_SSH_CONNECTION_KEY="ui:ssh_connection",
    )
    cache_namespace = {
        "json": json,
        "Path": Path,
        "time": time,
        "hhs_ui": cache_hhs_ui,
        "UI_CACHE_MEMORY": {},
        "UI_CACHE_MEMORY_MTIME": None,
        "prune_ui_cache_entries": lambda cache: {
            key: entry
            for key, entry in cache.items()
            if key.startswith("ui:")
            or (
                isinstance(entry.get("expires_at"), (int, float))
                and float(entry["expires_at"]) > time.time()
            )
        },
    }
    load_functions(
        sys.argv[2],
        {
            "read_ui_cache_file",
            "load_ui_cache",
            "ui_cache_files",
            "legacy_ui_cache_files",
            "unlink_legacy_ui_cache_files",
            "ui_cache_source_file",
            "ui_cache_mtime",
            "save_ui_cache",
            "ui_cache_file_is_synchronized",
            "sync_ui_cache_file",
            "ui_cache_key_is_supported",
        },
        cache_namespace,
    )
    cache_namespace["sync_ui_cache_file"]()
    assert list(json.loads(cache_file.read_text(encoding="utf-8"))) == [
        "command_tag:active:abc"
    ]
PY
  assert_success
}

@test "when rendering main navigation then AI visibility should refresh before Services view" {
  run python3 - "${ui_file}" "${command_runtime_file}" <<'PY'
import ast
import sys
from pathlib import Path

trees = [
    ast.parse(Path(path).read_text(encoding="utf-8"))
    for path in sys.argv[1:]
]
functions = {
    node.name: node
    for tree in trees
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}

main_views = functions["main_views"]
ollama_available = functions["ollama_service_is_available"]
initialize_available = functions["initialize_ollama_service_availability"]
for function_node in (main_views, ollama_available):
    called_names = {
        call.func.id
        for call in ast.walk(function_node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    assert "start_hhs_services_list_refresh" not in called_names
    assert "complete_hhs_services_list_refresh" not in called_names
    assert "poll_background_job_completion" not in called_names

initialize_calls = {
    call.func.id
    for call in ast.walk(initialize_available)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "cached_hhs_services_result" in initialize_calls
assert "background_job_is_running" in initialize_calls
assert "start_hhs_services_list_refresh" in initialize_calls
assert "complete_hhs_services_list_refresh" not in initialize_calls
assert "poll_background_job_completion" not in initialize_calls

remember = functions["remember_ollama_service_availability"]
remember_calls = {
    call.func.id
    for call in ast.walk(remember)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
remember_source = ast.get_source_segment(Path(sys.argv[1]).read_text(encoding="utf-8"), remember)
assert "ollama_service_is_available_from_output" in remember_calls
assert "AI_SERVICE_AVAILABILITY_CONTEXT_KEY" in remember_source

refresh_due = functions["ollama_service_availability_refresh_due"]
refresh_due_calls = {
    call.func.id
    for call in ast.walk(refresh_due)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "ai_service_availability_context_matches_active_host" in refresh_due_calls
assert "time" not in refresh_due_calls
refresh_due_source = ast.get_source_segment(Path(sys.argv[1]).read_text(encoding="utf-8"), refresh_due)
assert "AI_SERVICE_AVAILABILITY_REFRESH_INTERVAL_SECONDS" in refresh_due_source

schedule = functions["schedule_ollama_service_availability_refresh"]
schedule_calls = {
    call.func.id
    for call in ast.walk(schedule)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "stop_background_job" in schedule_calls
assert "cache_delete_tag" in schedule_calls
assert "start_hhs_services_list_refresh" in schedule_calls
schedule_source = ast.get_source_segment(Path(sys.argv[1]).read_text(encoding="utf-8"), schedule)
assert "AI_SERVICE_AVAILABILITY_CONTEXT_KEY" in schedule_source

update = functions["update_ollama_service_availability_refresh"]
update_calls = {
    call.func.id
    for call in ast.walk(update)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "complete_ollama_service_availability_refresh" in update_calls
assert "background_job_is_running" in update_calls
assert "poll_background_job_completion" not in update_calls
assert "ollama_service_availability_refresh_due" in update_calls
assert "start_hhs_services_list_refresh" in update_calls

complete_refresh = functions["complete_ollama_service_availability_refresh"]
complete_refresh_calls = {
    call.func.id
    for call in ast.walk(complete_refresh)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "complete_hhs_services_list_refresh" in complete_refresh_calls
assert "ollama_service_is_available" in complete_refresh_calls

polling = functions["render_background_job_polling_fragment"]
polling_calls = {
    call.func.id
    for call in ast.walk(polling)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "background_jobs_require_completion_polling" in polling_calls
assert "background_jobs_completion_needs_app_rerun" in polling_calls
assert "complete_ollama_service_availability_refresh" in polling_calls
assert "update_ollama_service_availability_refresh" not in polling_calls

ollama_polling = functions["render_ollama_service_availability_polling_fragment"]
ollama_polling_calls = {
    call.func.id
    for call in ast.walk(ollama_polling)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "update_ollama_service_availability_refresh" in ollama_polling_calls

main = functions["main"]
main_calls = {
    call.func.id
    for call in ast.walk(main)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "initialize_ollama_service_availability" in main_calls
assert "render_ollama_service_availability_polling_fragment" in main_calls
assert "render_background_job_polling_fragment" in main_calls
assert "render_main_view" in main_calls
assert "_render_background_job_polling_fragment" not in Path(sys.argv[2]).read_text(
    encoding="utf-8"
)
main_source = ast.get_source_segment(
    Path(sys.argv[1]).read_text(encoding="utf-8"), main
)
assert main_source.index("render_background_job_polling_fragment()") < main_source.index(
    "execute_pending_ssh_connection()"
)

render_main_view = functions["render_main_view"]
render_main_view_calls = {
    call.func.id
    for call in ast.walk(render_main_view)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "main_views" in render_main_view_calls
PY
  assert_success

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import types
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def ai_service_availability_context(")
end = source.index("def initialize_ollama_service_availability(")
session_state = {}
state = {"remote_host": ""}
namespace = {
    "hhs_ui": types.SimpleNamespace(),
    "hhs_ui_constants": types.SimpleNamespace(
        AI_SERVICE_AVAILABLE_KEY="_available",
        AI_SERVICE_AVAILABILITY_CONTEXT_KEY="_context",
        AI_SERVICE_AVAILABILITY_REFRESHED_AT_KEY="_refreshed_at",
        AI_SERVICE_AVAILABILITY_REFRESH_INTERVAL_SECONDS=5.0,
    ),
    "st": types.SimpleNamespace(session_state=session_state),
    "time": types.SimpleNamespace(time=lambda: 100.0),
    "command_remote_host": lambda: state["remote_host"],
}
exec("from __future__ import annotations\n" + source[start:end], namespace)
refresh_due = namespace["ollama_service_availability_refresh_due"]
available = namespace["ollama_service_is_available"]
availability_context = namespace["ai_service_availability_context"]
assert availability_context() == "local"
session_state["_context"] = "local"
assert refresh_due() is True
session_state["_refreshed_at"] = 98.0
assert refresh_due() is False
session_state["_refreshed_at"] = 94.0
assert refresh_due() is True
session_state["_available"] = True
assert available() is True
assert refresh_due() is True
session_state["_refreshed_at"] = 98.0
assert refresh_due() is False
state["remote_host"] = "remote-dev"
assert availability_context() == "ssh:remote-dev"
assert available() is False
assert refresh_due() is True
session_state["_context"] = "ssh:remote-dev"
assert available() is True
assert refresh_due() is False
PY
  assert_success
}
@test "when a completion rerun is interrupted then polling retries without looping forever" {
  run python3 - "${command_runtime_file}" <<'PY'
from pathlib import Path
import sys
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def background_job_completion_needs_app_rerun(")
end = source.index("def background_job_result(", start)
clock = {"now": 100.0}
session_state = {}

class CompletedProcess:
    def poll(self):
        return 0

class RunningProcess:
    def poll(self):
        return None

namespace = {
    "st": SimpleNamespace(session_state=session_state),
    "time": SimpleNamespace(monotonic=lambda: clock["now"]),
    "hhs_ui_constants": SimpleNamespace(
        BACKGROUND_JOB_COMPLETION_RERUN_RETRY_SECONDS=4.0,
        BACKGROUND_JOB_COMPLETION_RERUN_MAX_ATTEMPTS=3,
    ),
    "background_job_process": lambda job: job.get("process"),
    "background_job_has_timed_out": lambda _job: False,
    "stop_process": lambda _process: None,
    "background_job_session_items": lambda: list(session_state.items()),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)
needs_rerun = namespace["background_job_completion_needs_app_rerun"]
requires_polling = namespace["background_jobs_require_completion_polling"]

state_key = "_hhs_background_job_model"
job = {
    "process": CompletedProcess(),
    "metadata": {},
    "completion_rerun_queued": True,
}
session_state[state_key] = job
assert requires_polling() is True
assert needs_rerun(state_key, job) is True
assert "completion_rerun_queued" not in job
assert job["completion_rerun_attempts"] == 1
assert needs_rerun(state_key, job) is False

clock["now"] = 104.1
assert needs_rerun(state_key, job) is True
clock["now"] = 108.2
assert needs_rerun(state_key, job) is True
clock["now"] = 112.3
assert needs_rerun(state_key, job) is False
assert requires_polling() is False

job["process"] = RunningProcess()
assert requires_polling() is True
job["metadata"] = {"completion_rerun": False}
assert requires_polling() is False
assert needs_rerun(state_key, job) is False
PY
  assert_success
}

@test "when browser sessions run the same job then output files stay isolated" {
  run python3 - "${command_runtime_file}" <<'PY'
from pathlib import Path
import re
import sys
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def safe_background_job_name(")
end = source.index("def background_job_state(", start)
tokens = iter(("a" * 16, "b" * 16))
streamlit = SimpleNamespace(session_state={})
namespace = {
    "Path": Path,
    "re": re,
    "secrets": SimpleNamespace(token_hex=lambda _size: next(tokens)),
    "st": streamlit,
    "ui_disposable_files_dir": lambda: Path("/tmp/hhs-ui-test"),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)
session_token = namespace["background_job_session_token"]
output_path = namespace["background_job_output_path"]

first_token = session_token()
assert first_token == "a" * 16
assert session_token() == first_token
first_path = output_path("cached models", "stdout", first_token)
assert first_path.name == f"{first_token}-cached_models-stdout.log"

streamlit.session_state = {}
second_token = session_token()
second_path = output_path("cached models", "stdout", second_token)
assert second_token == "b" * 16
assert second_path != first_path
PY
  assert_success
}

@test "when cached content is fresh then background refresh loaders should stay hidden" {
  run python3 - "${ui_file}" "${command_runtime_file}" "${cache_runtime_file}" <<'PY'
import ast
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
command_runtime_source = Path(sys.argv[2]).read_text(encoding="utf-8")
cache_runtime_source = Path(sys.argv[3]).read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {
    node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
}
command_runtime_tree = ast.parse(command_runtime_source)
command_runtime_functions = {
    node.name: node for node in command_runtime_tree.body if isinstance(node, ast.FunctionDef)
}
cache_runtime_tree = ast.parse(cache_runtime_source)
cache_runtime_functions = {
    node.name: node for node in cache_runtime_tree.body if isinstance(node, ast.FunctionDef)
}

helper = ast.get_source_segment(
    command_runtime_source, command_runtime_functions["render_background_job_status_if_blocking"]
)
assert "if has_visible_content:" in helper
assert "poll_background_job_completion(job_name)" not in helper
assert "render_background_job_status(job_name, message)" in helper

cached_renderer = ast.get_source_segment(
    cache_runtime_source, cache_runtime_functions["render_cached_command_result"]
)
assert "render_background_job_status_if_blocking(job_name, result is not None)" in cached_renderer
assert "command_running and not fresh_cache and result is None" in cached_renderer
assert "render_background_job_status(job_name)" not in cached_renderer

services_table = ast.get_source_segment(source, functions["render_services_table"])
assert "render_background_job_status(SERVICE_ACTION_JOB)" in services_table
assert (
    "render_background_job_status_if_blocking(SERVICE_LIST_JOB, result is not None)"
    in services_table
)
assert "service_list_running and not fresh_cache and result is None" in services_table
assert "render_background_job_status(SERVICE_LIST_JOB)" not in services_table
PY
  assert_success
}
