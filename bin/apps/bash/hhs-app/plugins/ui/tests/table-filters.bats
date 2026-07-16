#!/usr/bin/env bats

#  Script: table-filters.bats
# Purpose: HomeSetup Streamlit UI table filter tests.
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

@test "when using table filters then shared filter controls should persist filter keys" {
  run python3 - "${table_ui_file}" <<'PY'
import ast
import sys
from pathlib import Path

tree = ast.parse(Path(sys.argv[1]).read_text(encoding="utf-8"))
functions = {
    node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
}
filter_controls = functions["render_table_filter_controls"]
radio_index_resolver = functions["table_filter_radio_index"]
normalizer = functions["normalized_table_filter_selection"]
text_filter_cleaner = functions["clean_table_text_filter_value"]
text_filter_state_normalizer = functions["normalize_table_text_filter_state"]
persisted_text_filter_normalizer = functions["normalize_persisted_table_text_filter_states"]

radio_calls = [
    call
    for call in ast.walk(filter_controls)
    if isinstance(call, ast.Call)
    and isinstance(call.func, ast.Attribute)
    and call.func.attr == "radio"
]
assert len(radio_calls) == 1
keywords = {keyword.arg: keyword.value for keyword in radio_calls[0].keywords}
on_change = keywords["on_change"]
assert isinstance(on_change, ast.Name)
assert on_change.id == "save_ui_state"
radio_index = keywords["index"]
assert isinstance(radio_index, ast.Name)
assert radio_index.id == "radio_index"
assert "handle_monitor_disk_top_n_change" not in ast.unparse(filter_controls)
assert "Containing" in ast.unparse(filter_controls)
assert "Containing" in ast.unparse(normalizer)
assert 'normalize_table_text_filter_state(other_key)' in ast.unparse(filter_controls)
assert 'clean_table_text_filter_value(other_filter)' in ast.unparse(filter_controls)
assert 'table_filter_radio_index(options, key, index)' in ast.unparse(filter_controls)
assert 'st.session_state.pop(key, None)' in ast.unparse(radio_index_resolver)
assert 'return max(0, min(index, len(options) - 1))' in ast.unparse(
    radio_index_resolver
)
assert "clean_value == 'None'" in ast.unparse(persisted_text_filter_normalizer)
assert any(
    isinstance(node, ast.Constant) and node.value == ""
    for node in ast.walk(text_filter_cleaner)
)
assert 'st.session_state[other_key] = clean_value' in ast.unparse(text_filter_state_normalizer)
PY
  assert_success

  run python3 - "${table_ui_file}" <<'PY'
from pathlib import Path
import sys


class Column:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class StreamlitStub:
    def __init__(self, session_state):
        self.session_state = session_state
        self.radio_indexes = []

    def columns(self, *_args, **_kwargs):
        return Column(), Column(), Column()

    def radio(self, _label, options, *, index, key, **_kwargs):
        self.radio_indexes.append(index)
        if key not in self.session_state:
            self.session_state[key] = options[index] if index is not None else None
        return self.session_state[key]


source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def table_filter_radio_index(")
end = source.index("def normalized_table_filter_selection(")
namespace = {
    "clean_table_text_filter_value": lambda value: "" if value is None else str(value),
    "save_ui_state": lambda: None,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)
render_controls = namespace["render_table_filter_controls"]
options = ("All", "Downloaded", "Active", "Other")

for invalid_state in ({}, {"ai_model_filter": None}, {"ai_model_filter": "Invalid"}):
    st = StreamlitStub(invalid_state)
    namespace["st"] = st
    selected_filter, other_filter = render_controls(
        options,
        "ai_model_filter",
        "ai_model_other_filter",
        [1.75, 2.25],
    )
    assert selected_filter == "All"
    assert other_filter == ""
    assert st.session_state["ai_model_filter"] == "All"
    assert st.radio_indexes == [0]

valid_state = {"ai_model_filter": "Active"}
st = StreamlitStub(valid_state)
namespace["st"] = st
selected_filter, _ = render_controls(
    options,
    "ai_model_filter",
    "ai_model_other_filter",
    [1.75, 2.25],
)
assert selected_filter == "Active"
assert st.radio_indexes == [None]
PY
  assert_success

  run python3 - "${table_ui_file}" <<'PY'
from pathlib import Path
from types import SimpleNamespace
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def clear_table_other_filter(")
end = source.index("def render_view_subtitle(")
session_state = {"monitor_process_other_filter": None}
namespace = {
    "hhs_ui": SimpleNamespace(
        FOUR_OPTION_FILTER_COLUMNS=[1.75, 2.25],
        PATH_FILTER_COLUMNS=[2.25, 1.75],
        THREE_OPTION_FILTER_COLUMNS=[1.1, 2.9],
        TWO_OPTION_FILTER_COLUMNS=[0.75, 3.25],
    ),
    "save_ui_state": lambda: None,
    "st": SimpleNamespace(session_state=session_state),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)
sample_filters = {
    "All": None,
    "On": "Up",
    "Off": "Down",
    "Other": "Containing",
}
assert namespace["clean_table_text_filter_value"](None) == ""
assert namespace["table_filter_mapping"](("All", "Containing")) == {
    "All": None,
    "Containing": None,
}
assert namespace["config_filter_columns"](sample_filters) == [1.75, 2.25]
assert namespace["config_filter_display_label"](
    sample_filters,
    "Containing",
    "All",
) == "Other"
assert namespace["config_filter_return_value"](sample_filters, "Other") == "Containing"
assert namespace["normalized_table_filter_selection"](None, ("All", "Containing")) == "All"
assert namespace["normalized_table_filter_selection"]("None", ("All", "Containing")) == "All"
assert namespace["normalized_table_filter_selection"]("Other", ("All", "Containing")) == "Containing"
assert namespace["normalize_table_text_filter_state"]("monitor_process_other_filter") == ""
assert session_state["monitor_process_other_filter"] == ""
session_state["monitor_process_other_filter"] = 123
assert namespace["normalize_table_text_filter_state"]("monitor_process_other_filter") == "123"
assert session_state["monitor_process_other_filter"] == "123"
session_state["env_other_filter"] = "None"
namespace["normalize_persisted_table_text_filter_states"]("env_other_filter", "path_other_filter")
assert session_state["env_other_filter"] == ""
assert session_state["path_other_filter"] == ""
PY
  assert_success
}
@test "when filtering table rows then status and text filters should reduce rows" {
  run python3 - "${command_catalog_file}" "${ui_file}" <<'PY'
import re
import sys
from pathlib import Path

command_source = Path(sys.argv[1]).read_text(encoding="utf-8")
ui_source = Path(sys.argv[2]).read_text(encoding="utf-8")
start = command_source.index("def row_matches_text_filter(")
end = command_source.index("def parse_hhs_envs(")
namespace = {
    "re": re,
    "home_tool_is_installed": lambda row: (
        "installed" in row.get("Status", "").lower()
        and "not installed" not in row.get("Status", "").lower()
    ),
    "home_tool_is_not_found": lambda row: (
        "not found" in row.get("Status", "").lower()
        or "not installed" in row.get("Status", "").lower()
    ),
    "home_tool_is_aliased": lambda row: (
        "aliased" in row.get("Status", "").lower()
    ),
    "service_is_up": lambda row: "up" in row.get("Value", "").lower(),
    "service_is_down": lambda row: "down" in row.get("Value", "").lower(),
}
exec("from __future__ import annotations\n" + command_source[start:end], namespace)
tool_start = ui_source.index("def filter_tool_rows(")
tool_end = ui_source.index("def process_monitor_chart_rows(")
exec("from __future__ import annotations\n" + ui_source[tool_start:tool_end], namespace)

rows = [
    {"Name": "ollama", "Value": "Up"},
    {"Name": "postgres", "Value": "Down"},
    {"Name": "custom", "Value": "Other"},
]
assert namespace["filter_rows_by_text"](rows, "All", "post") == rows
assert namespace["filter_rows_by_text"](rows, "Other", "post") == [rows[1]]
assert namespace["filter_rows_by_text"](rows, "Others", "post") == [rows[1]]
assert namespace["filter_rows_by_text"](rows, "Containing", "post") == [rows[1]]
assert namespace["filter_service_rows"](rows, "Up", "") == [rows[0]]
assert namespace["filter_service_rows"](rows, "Down", "") == [rows[1]]
assert namespace["filter_service_rows"](rows, "Other", "custom") == [rows[2]]
assert namespace["filter_service_rows"](rows, "Containing", "custom") == [rows[2]]

shopt_rows = [
    {"Name": "cdspell", "State": "ON"},
    {"Name": "histappend", "State": "OFF"},
]
assert namespace["filter_shopt_rows"](shopt_rows, "ON", "") == [shopt_rows[0]]
assert namespace["filter_shopt_rows"](shopt_rows, "OFF", "") == [shopt_rows[1]]
assert namespace["filter_shopt_rows"](shopt_rows, "Containing", "spell") == [shopt_rows[0]]

path_rows = [
    {"Origin": "Shell", "Path Value": "/bin"},
    {"Origin": "Custom", "Path Value": "/opt/tool"},
]
assert namespace["filter_path_rows"](path_rows, "Shell", "") == [path_rows[0]]
assert namespace["filter_path_rows"](path_rows, "Custom", "") == [path_rows[1]]
assert namespace["filter_path_rows"](path_rows, "Containing", "tool") == [path_rows[1]]

tool_rows = [
    {"Tool": "git", "Status": "Installed"},
    {"Tool": "ollama", "Status": "Not Found"},
    {"Tool": "node", "Status": "Not Installed"},
    {"Tool": "gw", "Status": "Aliased"},
]
assert namespace["filter_tool_rows"](tool_rows, "All", "") == tool_rows
assert namespace["filter_tool_rows"](tool_rows, "Installed", "") == [tool_rows[0]]
assert namespace["filter_tool_rows"](tool_rows, "Not Installed", "") == tool_rows[1:3]
assert namespace["filter_tool_rows"](tool_rows, "Aliased", "") == [tool_rows[3]]
assert namespace["filter_tool_rows"](tool_rows, "Other", "node") == [tool_rows[2]]
assert namespace["filter_tool_rows"](tool_rows, "Containing", "node") == [tool_rows[2]]
PY
  assert_success
}
