#!/usr/bin/env bats

#  Script: table-actions.bats
# Purpose: HomeSetup Streamlit UI selected table action tests.
# Created: Jul 09, 2026
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

@test "when rendering selected table rows then shared action and edit controls should be wired" {
  assert_file_contains_many "${ui_file}" \
'checkbox=True' 'selected_label=lambda row, _index: f"Selected: {row.get('"'"'Tool'"'"', '"'"''"'"')}"' \
    'reset_selection=reset_env_table_selection' 'reset_selection=reset_path_table_selection' \
    'reset_selection=reset_dir_table_selection' 'reset_selection=reset_cmd_table_selection' \
    'reset_selection=reset_alias_table_selection' 'reset_selection=reset_ai_model_table_selection'
  assert_file_contains_many "${table_ui_file}" \
    'def render_selected_table_item' 'def table_component_key' 'table_empty_hint' \
    'table_selected_panel_' 'table_actions_' 'def scroll_to_table_selection_content' \
    'table_selected_bottom_' 'scroll_to_table_selection_content(anchor_key)' \
    'target.scrollIntoView' 'selected_editable: bool | Callable' '""' '"ﰸ"' \
    'help="Edit"' 'args=(editing_key, edit_key, edit_value)' \
    'gap="small"' 'st.text_input(' 'f"{value}:"' \
    'def render_selected_table_actions' 'selected_action_buttons: list' \
    'selected_actions=visible_selected_actions' 'help="Cancel edit"' \
    'def cancel_selected_item_edit' 'reset_selection: Callable\[\[\], None\] | None = None' \
    'args=(editing_key, edit_key, reset_selection)' 'def execute_selected_table_action' \
    'callback(\*callback_args)'

  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
functions = {
    node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
}
for function_name in (
    "apply_selected_env_editor_value",
    "apply_selected_dir_editor_value",
    "apply_selected_cmd_editor_value",
    "apply_selected_alias_editor_value",
):
    function = functions[function_name]
    reset_calls = [
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id.startswith("reset_")
    ]
    if reset_calls:
        raise SystemExit(f"{function_name} should keep table selection checked")
PY
  assert_success
}

@test "when styling selected table actions then action panels should use shared layout tokens" {
  assert_file_contains_many "${css_file}" \
'div\[class\*="_selected_editing_"\] button' 'div\[class\*="_table_empty_hint"\]' \
    'div\[class\*="_table_selected_panel_"\]' 'div\[class\*="_table_actions_"\]' \
    'margin-top: 0 !important' 'gap: var(--hhs-element-std-gap) !important' \
    'div\[class\*="st-key-env_delete_button_"\]\[class\*="_selected"\] button' \
    'div\[class\*="st-key-path_delete_button_"\]\[class\*="_selected"\] button'
  assert_file_not_contains "${css_file}" 'st-key-path_selected_value_'

  run grep -R -q 'st-key-path_selected_value_' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes"
  assert_failure

  assert_file_contains_many "${css_file}" \
'div\[class\*="st-key-dir_delete_button_"\]\[class\*="_selected"\] button' \
    'div\[class\*="st-key-cmd_delete_button_"\]\[class\*="_selected"\] button' \
    'div\[class\*="st-key-alias_delete_button_"\]\[class\*="_selected"\] button' \
    'div\[class\*="st-key-ai_delete_model_button_"\]\[class\*="_selected"\] button' \
    'width: 2rem'
}
