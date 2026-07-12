#!/usr/bin/env bats

#  Script: config-layout.bats
# Purpose: HomeSetup Streamlit UI configuration layout tests.
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

@test "when rendering config navigation then view labels and imports should use explicit modules" {
  assert_file_contains "${constants_file}" 'CONFIG_VIEWS = ("ENV", "PATH", "DIR", "CMD", "ALIAS")'
  assert_file_contains "${ui_file}" 'format_func=config_view_label'
  assert_file_not_contains "${ui_file}" 'globals().get('

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  assert_file_not_contains "${ui_file}" 'from constants import \*'
  assert_file_contains "${ui_file}" '^import hhs_ui$'
}

@test "when rendering config add controls then shared bottom-aligned columns should be used" {
  assert_file_contains_many "${ui_file}" \
'action_weights.append(0.19 if name_label else 0.035)' 'def config_add_columns' \
    'vertical_alignment="bottom"'
  assert_file_contains_many "${css_file}" \
'div[data-testid="stHorizontalBlock"]:has(.st-key-alias_add_value)' \
    'div[data-testid="stHorizontalBlock"]:has(.st-key-cmd_add_value)' \
    'div[data-testid="stHorizontalBlock"]:has(.st-key-dir_add_value)' \
    'div[data-testid="stHorizontalBlock"]:has(.st-key-env_add_value)' \
    'div[data-testid="stHorizontalBlock"]:has(.st-key-path_add_value)' \
    'column-gap: var(--hhs-element-std-gap) !important' '.st-key-cmd_add_submit' \
    '.st-key-alias_add_submit' '.st-key-dir_add_submit' '.st-key-dir_folder_picker_button button'
  assert_file_not_contains "${css_file}" '.st-key-env_add_button'

  assert_file_contains_many "${css_file}" \
'color: var(--hhs-danger) !important' '\[data-testid="stTextInput"\]' \
    'grid-template-columns: max-content minmax(0, 1fr)' 'white-space: nowrap'
  assert_file_contains "${table_ui_file}" 'hhs-selected-item-line'
  assert_file_contains "${css_file}" 'display: inline-flex'
  assert_file_not_contains "${css_file}" 'margin-top: 1.55rem'

  run grep -q -- '--hhs-config-add-control-height' "${css_file}"
  assert_failure

  assert_file_contains "${css_file}" 'transform: translateY(-0.25rem)'
}
