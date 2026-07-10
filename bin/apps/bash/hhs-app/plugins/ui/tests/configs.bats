#!/usr/bin/env bats

#  Script: configs.bats
# Purpose: HomeSetup Streamlit UI configuration tests.
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

@test "when rendering configs then current command-backed tables and filters should be wired" {
  assert_file_contains_many "${ui_file}" \
'__hhs_envs' '__hhs_paths' '__hhs_load_dir -l' '__hhs_command -l' '__hhs_aliases' 'def render_env_rows' \
    'def build_hhs_env_action_command' 'def run_hhs_env_action' 'def build_hhs_path_action_command' \
    'def run_hhs_path_action' 'def build_hhs_dir_action_command' 'def run_hhs_dir_action' \
    'def build_hhs_command_action_command' 'def run_hhs_command_action' 'def build_hhs_alias_action_command' \
    'def run_hhs_alias_action' 'def build_hhs_shopt_command' 'def build_hhs_shopt_setup_command' \
    '\[\[ ! -s "${HHS_SHOPTS_FILE}" \]\]' 'awk.*print \$1.*=.*\$2' 'def build_hhs_shopt_load_saved_command' \
    'def build_hhs_shopt_action_command' 'def run_hhs_shopt' 'def run_hhs_shopt_action' 'def parse_hhs_shopt' \
    'SHOPT_DESCRIPTIONS = {' '"cdspell": "Corrects minor spelling errors in directory names used with cd."' \
    'def shopt_description' '"Description": shopt_description(match.group(3).strip())' \
    'headers=\["Status", "Option", "Description"\]'
  assert_file_contains "${constants_file}" 'SHOPT_LINE_PATTERN = re.compile'

  assert_file_contains_many "${command_catalog_file}" \
'def filter_shopt_rows' 'f"__hhs_shopt {action} {shlex.quote(option_name)}"' \
    'build_hhs_shopt_load_saved_command()' '__hhs_shopt -p' \
    'shopt -s "${option}" 2>/dev/null || true' 'shopt -u "${option}" 2>/dev/null || true' \
    '"Status": shopt_status_value(state)' 'f"__hhs_paths {action_args}"' \
    'def build_hhs_path_environment_command' 'def build_hhs_paths_raw_entries_command' \
    'HHS_PATHS_RAW_ENTRY_MARKER' 'action_args = f"-a {safe_path}"' \
    'action_args = f"-r {safe_path}"' 'f"__hhs_save_dir {action_args}"' \
    'f"__hhs_command {action_args}"' 'f"__hhs_aliases {action_args}"'
  assert_file_contains_many "${ui_file}" \
'def apply_home_shopt_action' 'def refresh_home_shopts_listing' \
    'action_buttons=\[' '"label": " Turn ON"' '"label": " Turn OFF"' \
    'action_column_weights=\[1, 1\]'
  run grep -q -- "-a {shlex.quote(f'{name}={value}')}" "${command_catalog_file}"
  assert_success

  assert_file_contains_many "${ui_file}" \
'safe_path = shlex.quote(path_value)' 'action_args = f"{shlex.quote(value)} {safe_name}"' \
    'action_args = f"-a {safe_name} {shlex.quote(value)}"' \
    'f"-r {safe_name}" if operation == "del" else f"{safe_name} {shlex.quote(value)}"' \
    'apply_selected_env_value(name, str(st.session_state.get(editor_key, "")))'
  run grep -q -- '--del {safe_name}' "${ui_file}"
  assert_success

  assert_file_contains "${ui_file}" 'apply_env_add_form_value'

  assert_file_not_contains_many "${ui_file}" \
'with st.form(f"{key_prefix}_add_form", border=False)' 'st.form_submit_button('
  assert_file_contains_many "${ui_file}" \
'key=f"{key_prefix}_add_submit"' '""' 'value_input_args\["on_change"\] = on_submit'
  assert_file_not_contains "${ui_file}" 'env_add_button'

  assert_file_contains_many "${ui_file}" \
'"Custom Variable"' 'def render_path_add_controls' 'def render_dir_add_controls' 'request_folder_picker'
  assert_file_contains_many "${path_picker_file}" \
    'def apply_folder_picker_selection' 'def open_folder_picker_selected_child' \
    'sync_folder_picker_child_selection(child_directories)' 'def folder_picker_child_selection_widget_key' \
    '_hhs_folder_picker_selected_dir_widget_' \
    'prune_folder_picker_child_selection_widget_keys(selected_widget_key)' '"key": selected_widget_key' \
    'else empty_caption' 'loading_children or not bool(child_directories)'
  assert_file_not_contains "${path_picker_file}" 'st.caption(empty_caption)'

  assert_file_contains_many "${path_picker_file}" \
'def folder_picker_browsing_directory' 'def queue_folder_picker_directory_load' \
    'def load_pending_remote_path_picker_directory' 'def folder_picker_visible_child_paths' \
    'PATH_PICKER_LISTING_JOB_PREFIX' 'def path_picker_listing_job_name' \
    'start_background_bash_command(' 'def render_path_picker_listing_loader' \
    'render_background_job_status(job_name, PATH_PICKER_LISTING_LOADER_MESSAGE)'
  assert_file_not_contains "${path_picker_file}" 'poll_background_job_completion(job_name)'

  assert_file_contains "${ui_file}" 'stop_path_picker_listing_jobs()'

  assert_file_not_contains "${ui_file}" 'rerun_after_folder_picker_navigation()'

  assert_file_contains_many "${path_picker_file}" \
'st.container(key="folder_picker_action_grid")' '_left_spacer,'
  assert_file_not_contains "${path_picker_file}" '_parent_open_gap,'

  assert_file_contains_many "${path_picker_file}" \
'\[1.0, 0.12, 0.12, 0.12, 0.12, 1.0\]' 'gap="small"' 'width="content"' '""' '""' '"﬌"' '"ﰸ"'
  assert_file_not_contains_many "${path_picker_file}" \
'" Parent"' '"label": "﬌ Select"' 'buttons=()'
  assert_file_contains_many "${path_picker_file}" \
'st.container(key="hhs_path_picker_overlay")' 'st.container(key="hhs_path_picker_panel")' \
    'def render_path_picker_body' 'def folder_picker_owner_context_for_target' \
    'def folder_picker_owner_matches'
  assert_file_contains_many "${ui_file}" \
    'render_folder_picker_dialog("path")' 'render_folder_picker_dialog("dir")' 'render_folder_picker_dialog("search")'
  assert_file_not_contains_many "${ui_file}" \
'rerun_streamlit_app' 'st.rerun(scope="app")'
  assert_file_contains "${path_picker_file}" 'key="folder_picker_header_close_button"'

  assert_file_contains_many "${css_file}" \
'.st-key-folder_picker_select_button button' '.st-key-folder_picker_header_close_button button' \
    '.st-key-hhs_path_picker_overlay' 'align-items: center !important' 'justify-content: center !important' \
    'min-height: 100dvh !important' 'width: auto !important' 'margin: auto !important' \
    '.st-key-hhs_path_picker_panel' 'left: 50% !important' 'position: fixed !important' 'top: 50% !important' \
    'transform: translate(-50%, -50%) !important'
  assert_file_not_contains_many "${css_file}" \
'.st-key-folder_picker_action_grid,' '.st-key-folder_picker_action_grid \[data-testid="stVerticalBlock"\]'
  assert_file_contains_many "${css_file}" \
'.st-key-folder_picker_action_grid \[data-testid="stHorizontalBlock"\]' \
    'gap: var(--hhs-element-std-gap) !important'
  assert_file_not_contains_many "${css_file}" \
'grid-auto-flow: column' 'grid-template-columns: repeat(4, 2rem)'
  assert_file_contains "${css_file}" 'var(--hhs-element-std-gap)'

  run python3 - "${css_file}" <<'PY'
from pathlib import Path
import sys

css = Path(sys.argv[1]).read_text(encoding="utf-8")
folder_grid = css[
    css.index(".st-key-folder_picker_action_grid"):
    css.index('div[class*="st-key-alias_selected_value_"]')
]
assert "nth-child(8)" not in folder_grid
PY
  assert_success

  assert_file_contains_many "${css_file}" \
'nth-child(5)' 'min-width: 2rem' 'justify-content: center'
  assert_file_contains_many "${path_picker_file}" \
'"Include .dot-folders"' '"Loading directories and files..."'
  run python3 - "${path_picker_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
remote_listing_body = source.split("def remote_path_picker_child_paths", 1)[1].split("\ndef ", 1)[0]
pending_listing_body = source.split("def load_pending_remote_path_picker_directory", 1)[1].split("\ndef ", 1)[0]
assert "show_preloader_event=True" in remote_listing_body
assert "show_preloader_event=True" in pending_listing_body
assert "PATH_PICKER_LISTING_LOADER_MESSAGE" in remote_listing_body
assert "PATH_PICKER_LISTING_LOADER_MESSAGE" in pending_listing_body
PY
  assert_success

  assert_file_not_contains_many "${path_picker_file}" \
'def render_path_picker_open_preloader_script' 'render_path_picker_open_preloader_script()' \
    '__hhsPathPickerOpenPreloaderCleanup' 'const overlayToken = `path-picker-' \
    '[class*="st-key-"][class*="_folder_picker_button"] button' '.st-key-folder_picker_open_button button' \
    '.st-key-folder_picker_parent_button button'
  assert_file_contains_many "${path_picker_file}" \
'_hhs_folder_picker_include_dot_folders' 'include_dot_folders or not path.name.startswith(".")'
  assert_file_not_contains "${path_picker_file}" '_hhs_folder_picker_on_select'

  assert_file_contains_many "${ui_file}" \
'key=f"{key_prefix}_folder_picker_button"' 'name_col = columns\[0\]' \
    'action_weights.append(0.19 if name_label else 0.035)' \
    'action_weights.append(0.2 if name_label else 0.035)' 'columns = config_add_columns([1, *action_weights])' \
    'columns = config_add_columns([1.375, value_weight, *action_weights])'
  assert_file_not_contains_many "${ui_file}" \
'value_group_col.columns(' '\[1, 0.012, 0.035\], vertical_alignment="center"'
  assert_file_contains "${ui_file}" 'value_weight = 4.05 if has_file_picker_btn else 4.2'

  assert_file_not_contains "${ui_file}" 'value_group_col = st.columns'

  assert_file_contains_many "${ui_file}" \
'args=(f"{key_prefix}_add_value", value_placeholder)' 'def render_cmd_add_controls' \
    'def render_alias_add_controls' 'def render_filters_and_controls'
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
component_body = source.split("def render_filters_and_controls(", 1)[1].split("\ndef ", 1)[0]
assert "with st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True):" in component_body
assert "render_config_add_controls(" in component_body
assert "render_table_filter_controls(" in component_body
assert "other_options=(filter_labels[-1],)" in component_body
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'env_filter, other_filter = render_filters_and_controls(' \
    'path_filter, other_filter = render_filters_and_controls(' \
    'dirs_filter, other_filter = render_filters_and_controls(' \
    'cmds_filter, other_filter = render_filters_and_controls(' \
    'alias_filter, other_filter = render_filters_and_controls(' 'render_table_filter_controls' \
    'status_message = clean_command_status_message('
  assert_file_not_contains_many "${ui_file}" \
'env_action_message' '""'
  assert_file_contains_many "${ui_file}" \
'on_click": apply_env_delete' '"glyph": ""' 'def render_path_rows' 'def render_dir_rows' \
    'def render_cmd_rows' 'def render_alias_rows' 'def render_dirs_table' 'def render_cmds_table' \
    'def render_aliases_table'
  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
table_functions = (
    "render_envs_table",
    "render_paths_table",
    "render_dirs_table",
    "render_cmds_table",
    "render_aliases_table",
)
for function_name in table_functions:
    decorator = source[: source.index(f"def {function_name}")].rstrip().splitlines()[-1]
    assert decorator == "@st.fragment()", function_name
    body = source.split(f"def {function_name}", 1)[1].split("\ndef ", 1)[0]
    assert "st.error(" not in body, function_name
    assert "if result.returncode != 0:" not in body, function_name
    assert "parse_rows_cached(" in body, function_name
    assert "if result.returncode == 0" in body, function_name
    assert "else []" in body, function_name
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'selected_editable=True' 'selected_edit_key=lambda row, _index: env_value_editor_key(row\["Name"\])' \
    'selected_edit_key=lambda _row, index: dir_value_editor_key(index)' 'selected_edit_folder_picker=True' \
    'selected_edit_key=lambda _row, index: cmd_value_editor_key(index)' \
    'selected_edit_key=lambda _row, index: alias_value_editor_key(index)'
  run python3 - "${ui_file}" "${constants_file}" "${table_ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
constants_source = Path(sys.argv[2]).read_text(encoding="utf-8")
table_source = Path(sys.argv[3]).read_text(encoding="utf-8")
path_body = source.split("def render_path_rows(", 1)[1].split("\ndef ", 1)[0]
assert '"""Render selectable read-only PATH rows."""' in path_body
assert "selected_label=lambda row, _index: f\"Selected: {row['Path Value']}\"" in path_body
assert "reset_selection=reset_path_table_selection" in path_body
assert "selected_action_buttons=[" in path_body
assert '"key_prefix": "path_delete_button"' in path_body
assert '"on_click": apply_path_delete' in path_body
assert "table_data=styled_path_rows(rows)" in path_body
assert "column_config=path_column_config()" in path_body
assert "rows = apply_path_value_overrides(rows)" not in path_body
assert "selected_editable=True" not in path_body
assert "path_value_editor_key" not in path_body
assert "selected_edit_on_change=apply_selected_path_editor_value" not in path_body
assert "selected_edit_folder_picker=True" not in path_body
assert "checkbox=False" not in path_body
assert "clear_path_table_edit_state()" not in path_body
assert "def clear_path_table_edit_state(" not in source
assert "def path_value_editor_key(" not in source
assert "def apply_selected_path_editor_value(" not in source
assert "def path_value_overrides(" not in source
assert "def apply_path_value_overrides(" not in source
assert "def export_path_value_overrides(" not in source
assert "def path_column_config(" in table_source
assert "path_value_overrides()" not in source

persisted_prefix_body = constants_source.split("PERSISTED_UI_KEY_PREFIXES = (", 1)[1].split(")", 1)[0]
persisted_keys_body = constants_source.split("PERSISTED_UI_KEYS = (", 1)[1].split(")", 1)[0]
assert '"path_selected_value_"' not in persisted_prefix_body
assert "PATH_VALUE_EDITOR_KEY_PREFIX" not in constants_source
assert '"path_value_overrides"' not in persisted_keys_body
assert "PATH_VALUE_OVERRIDES_KEY" not in constants_source
assert "PATH_TYPE_COLUMN_WIDTH" in constants_source
assert "PATH_ORIGIN_COLUMN_WIDTH" not in constants_source
assert "PATH_VALUE_COLUMN_WIDTH" not in constants_source
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'on_click": apply_dir_delete' 'on_click": apply_cmd_delete' 'on_click": apply_alias_delete' \
    'selected_value: Callable\[\[dict\[str, str\], int\], str\] | None = None' \
    'selected_value=lambda row, _index: row.get("Value", "")'
  run python3 - <<'PY'
import ast
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
tree = ast.parse(source)
functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

def function_body(function_name):
    function = functions[function_name]
    return "\n".join(source.splitlines()[function.lineno - 1:function.end_lineno])

required_direct_refresh_calls = (
    ("execute_pending_ai_model_selection", "refresh_ai_model_listing"),
    ("execute_pending_ai_model_deletion", "refresh_ai_model_listing"),
    ("apply_successful_config_action_side_effects", "refresh_env_listing"),
    ("apply_successful_config_action_side_effects", "refresh_path_listing"),
    ("apply_successful_config_action_side_effects", "refresh_dir_listing"),
    ("apply_successful_config_action_side_effects", "refresh_cmd_listing"),
    ("apply_successful_config_action_side_effects", "refresh_alias_listing"),
    ("apply_successful_config_action_side_effects", "refresh_home_shopts_listing"),
    ("execute_pending_home_tool_action", "refresh_home_tools_listing"),
    ("apply_selected_service_action", "refresh_service_listing"),
    ("complete_monitor_process_action_job", "refresh_process_listing"),
)
for function_name, refresh_name in required_direct_refresh_calls:
    function = functions[function_name]
    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == refresh_name
        for node in ast.walk(function)
    ):
        raise SystemExit(f"{function_name} should call {refresh_name}")

required_config_action_queues = {
    "apply_selected_env_value": "build_hhs_env_action_command",
    "apply_env_delete": "build_hhs_env_action_command",
    "apply_selected_path_value": "build_hhs_path_action_command",
    "apply_path_delete": "build_hhs_path_action_command",
    "apply_selected_dir_value": "build_hhs_dir_action_command",
    "apply_dir_delete": "build_hhs_dir_action_command",
    "apply_selected_cmd_value": "build_hhs_command_action_command",
    "apply_cmd_delete": "build_hhs_command_action_command",
    "apply_selected_alias_value": "build_hhs_alias_action_command",
    "apply_alias_delete": "build_hhs_alias_action_command",
    "apply_home_shopt_action": "build_hhs_shopt_action_command",
}
for function_name, command_builder_name in required_config_action_queues.items():
    body = function_body(function_name)
    if "queue_config_action(" not in body:
        raise SystemExit(f"{function_name} should queue config action")
    if command_builder_name not in body:
        raise SystemExit(f"{function_name} should use {command_builder_name}")
    if "_listing()" in body:
        raise SystemExit(f"{function_name} should not refresh synchronously")

process_kill_body = function_body("apply_selected_process_kill")
if "queue_monitor_process_action(" not in process_kill_body:
    raise SystemExit("apply_selected_process_kill should queue monitor action")

refresh_cache_body = function_body("refresh_config_listing_cache")
for expected_fragment in (
    "stop_config_listing_background_jobs(cache_tag)",
    "cache_delete_tag(cache_tag)",
    "reset_selection()",
):
    if expected_fragment not in refresh_cache_body:
        raise SystemExit(f"refresh_config_listing_cache should include {expected_fragment}")
for forbidden_fragment in (
    "use_cache=False",
    "show_overlay=False",
    "background_command_metadata(command, cache_tag)",
    "cache_background_command_result(metadata, result)",
    "run_bash_command(",
):
    if forbidden_fragment in refresh_cache_body:
        raise SystemExit(f"refresh_config_listing_cache should not include {forbidden_fragment}")

stop_jobs_body = function_body("stop_config_listing_background_jobs")
for expected_fragment in (
    'background_job_state_key(f"cached_{safe_cache_tag(cache_tag)}_")',
    "stop_background_jobs_with_state_prefix(",
    'if cache_tag == "aliases":',
    "stop_background_job(ALIAS_LIST_JOB)",
):
    if expected_fragment not in stop_jobs_body:
        raise SystemExit(f"stop_config_listing_background_jobs should include {expected_fragment}")

config_refresh_specs = {
    "refresh_env_listing": ("env", "build_hhs_envs_command(None)", "reset_env_table_selection"),
    "refresh_path_listing": ("path", "build_hhs_paths_command()", "reset_path_table_selection"),
    "refresh_dir_listing": ("dirs", "build_hhs_dirs_command()", "reset_dir_table_selection"),
    "refresh_cmd_listing": ("cmds", "build_hhs_commands_command()", "reset_cmd_table_selection"),
    "refresh_alias_listing": ("aliases", "build_hhs_aliases_command()", "reset_alias_table_selection"),
}
for function_name, (cache_tag, command_fragment, reset_name) in config_refresh_specs.items():
    body = function_body(function_name)
    for expected_fragment in (
        "refresh_config_listing_cache(",
        f'"{cache_tag}"',
        command_fragment,
        reset_name,
    ):
        if expected_fragment not in body:
            raise SystemExit(f"{function_name} should include {expected_fragment}")

render_envs_body = function_body("render_envs_table")
for expected_fragment in (
    "build_hhs_envs_command(None)",
    "filter_env_rows(rows, env_filter, other_filter)",
):
    if expected_fragment not in render_envs_body:
        raise SystemExit(f"render_envs_table should include {expected_fragment}")

side_effect_body = function_body("apply_successful_config_action_side_effects")
for expected_fragment in (
    "if result.returncode == 0:",
    "os.environ[name] = value",
    "os.environ.pop(name, None)",
    'os.environ["PATH"] =',
    "refresh_env_listing()",
    "refresh_path_listing()",
    "refresh_dir_listing()",
    "refresh_cmd_listing()",
    "refresh_alias_listing()",
    "refresh_home_shopts_listing()",
    "clear_add_form_fields(",
):
    source_to_check = function_body("complete_config_action_job")
    if expected_fragment not in source_to_check + "\n" + side_effect_body:
        raise SystemExit(f"config action completion should include {expected_fragment}")

required_add_form_metadata = {
    "apply_env_add_form_value": (
        "apply_selected_env_value(name, value, clear_form_key_prefix=\"env\")",
    ),
    "apply_path_add_form_value": (
        "clear_form_key_prefix=\"path\"",
        "clear_form_include_name=False",
    ),
    "apply_dir_add_form_value": (
        "apply_selected_dir_value(name, value, clear_form_key_prefix=\"dir\")",
    ),
    "apply_cmd_add_form_value": (
        "apply_selected_cmd_value(name, value, clear_form_key_prefix=\"cmd\")",
    ),
    "apply_alias_add_form_value": (
        "apply_selected_alias_value(name, value, clear_form_key_prefix=\"alias\")",
    ),
}
for function_name, expected_fragments in required_add_form_metadata.items():
    body = function_body(function_name)
    for expected_fragment in expected_fragments:
        if expected_fragment not in body:
            raise SystemExit(f"{function_name} should include {expected_fragment}")

required_delete_command_fragments = {
    "build_hhs_env_action_command": "--del {safe_name}",
    "build_hhs_path_action_command": "-r {safe_path}",
    "build_hhs_dir_action_command": "-r {safe_name}",
    "build_hhs_command_action_command": "-r {safe_name}",
    "build_hhs_alias_action_command": "-r {safe_name}",
}
for function_name, expected_fragment in required_delete_command_fragments.items():
    function = functions[function_name]
    lines = source.splitlines()[function.lineno - 1:function.end_lineno]
    if expected_fragment not in "\n".join(lines):
        raise SystemExit(f"{function_name} should use delete flag fragment: {expected_fragment}")

read_only = functions["render_read_only_rows"]
if any(
    isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute)
    and node.func.attr == "text_area"
    for node in ast.walk(read_only)
):
    raise SystemExit("read-only selected rows should not render disabled text areas")
PY
  assert_success
}

@test "when Config listing cache refreshes then it invalidates stale data" {
  run python3 - "${ui_file}" <<'PY'
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def stop_config_listing_background_jobs(")
end = source.index("def service_table_key(")
calls = []
run_returncode = 0

def safe_cache_tag(cache_tag):
    calls.append(("safe_cache_tag", cache_tag))
    return cache_tag

def background_job_state_key(job_name):
    calls.append(("background_job_state_key", job_name))
    return f"state:{job_name}"

def stop_background_jobs_with_state_prefix(state_key_prefix):
    calls.append(("stop_prefix", state_key_prefix))

def stop_background_job(job_name):
    calls.append(("stop_job", job_name))

def cache_delete_tag(cache_tag):
    calls.append(("delete", cache_tag))

def run_bash_command(command, loader_message, **kwargs):
    calls.append(("run", command, loader_message, kwargs))
    return subprocess.CompletedProcess(["bash"], run_returncode, f"fresh:{command}", "")

def background_command_metadata(command, cache_tag):
    calls.append(("metadata", command, cache_tag))
    return {"cache_key": f"{cache_tag}:key"}

def cache_background_command_result(metadata, result):
    calls.append(("cache", metadata, result.stdout))

def build_hhs_envs_command(_prefix_filter):
    return "LIST_ENV"

def build_hhs_paths_command():
    return "LIST_PATH"

def build_hhs_dirs_command():
    return "LIST_DIRS"

def build_hhs_commands_command():
    return "LIST_CMDS"

def build_hhs_aliases_command():
    return "LIST_ALIASES"

def reset_env_table_selection():
    calls.append(("reset", "env"))

def reset_path_table_selection():
    calls.append(("reset", "path"))

def reset_dir_table_selection():
    calls.append(("reset", "dirs"))

def reset_cmd_table_selection():
    calls.append(("reset", "cmds"))

def reset_alias_table_selection():
    calls.append(("reset", "aliases"))

namespace = {
    "ALIAS_LIST_JOB": "alias_list_job",
    "hhs_ui": SimpleNamespace(
        UI_COMMAND_DEFAULT_TIMEOUT_SECONDS=30,
        UI_CACHE_DEFAULT_TTL_SECONDS=300,
    ),
    "safe_cache_tag": safe_cache_tag,
    "background_job_state_key": background_job_state_key,
    "stop_background_jobs_with_state_prefix": stop_background_jobs_with_state_prefix,
    "stop_background_job": stop_background_job,
    "cache_delete_tag": cache_delete_tag,
    "run_bash_command": run_bash_command,
    "background_command_metadata": background_command_metadata,
    "cache_background_command_result": cache_background_command_result,
    "build_hhs_envs_command": build_hhs_envs_command,
    "build_hhs_paths_command": build_hhs_paths_command,
    "build_hhs_dirs_command": build_hhs_dirs_command,
    "build_hhs_commands_command": build_hhs_commands_command,
    "build_hhs_aliases_command": build_hhs_aliases_command,
    "reset_env_table_selection": reset_env_table_selection,
    "reset_path_table_selection": reset_path_table_selection,
    "reset_dir_table_selection": reset_dir_table_selection,
    "reset_cmd_table_selection": reset_cmd_table_selection,
    "reset_alias_table_selection": reset_alias_table_selection,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["refresh_path_listing"]()
assert calls == [
    ("safe_cache_tag", "path"),
    ("background_job_state_key", "cached_path_"),
    ("stop_prefix", "state:cached_path_"),
    ("delete", "path"),
    ("reset", "path"),
], calls

calls.clear()
namespace["refresh_alias_listing"]()
assert ("stop_job", "alias_list_job") in calls, calls
assert ("delete", "aliases") in calls, calls
assert not any(call[0] in {"run", "metadata", "cache"} for call in calls), calls
assert calls[-1] == ("reset", "aliases"), calls

calls.clear()
run_returncode = 1
namespace["refresh_dir_listing"]()
assert ("delete", "dirs") in calls, calls
assert not any(call[0] in {"run", "metadata", "cache"} for call in calls), calls
assert calls[-1] == ("reset", "dirs"), calls
PY
  assert_success
}
