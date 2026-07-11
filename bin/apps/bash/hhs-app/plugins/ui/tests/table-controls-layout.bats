#!/usr/bin/env bats

#  Script: table-controls-layout.bats
# Purpose: HomeSetup Streamlit UI shared table control layout tests.
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

@test "when rendering table controls then shared filters should use exported layout constants" {
  assert_file_contains "${constants_file}" 'TABLE_CONTROLS_PANEL_TITLE = "Filters & Controls"'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'TABLE_CONTROLS_PANEL_TITLE'
  assert_file_contains_many "${table_ui_file}" \
'def render_table_controls_panel' 'st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True)' \
    'def render_table_filter_controls' 'def clear_table_other_filter' \
    'key=f"{other_key}_clear"' '""' 'on_click=clear_table_other_filter' \
  assert_file_contains "${ui_file}" 'def render_config_add_controls'
  assert_file_contains_many "${constants_file}" \
'TWO_OPTION_FILTER_COLUMNS = \[0.75, 3.25\]' \
    'THREE_OPTION_FILTER_COLUMNS = \[1.1, 2.9\]' \
    'FOUR_OPTION_FILTER_COLUMNS = \[1.75, 2.25\]' \
    'FIVE_OPTION_FILTER_COLUMNS = \[2.75, 1.25\]' \
    'PATH_FILTER_COLUMNS = \[2.25, 1.75\]'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" \
'FIVE_OPTION_FILTER_COLUMNS'
  assert_file_contains "${table_ui_file}" 'hhs_ui.THREE_OPTION_FILTER_COLUMNS'

  assert_file_contains_many "${constants_file}" \
'SERVICE_FILTERS = ("All", "Up", "Down", "Containing")' \
    'PATH_FILTERS = ("All", "Shell", "Private", "Custom", "Containing")'
}

@test "when styling table filters then default gaps should be one rem and wrapping should stay visible" {
  assert_file_contains_many "${css_file}" \
'\[data-testid="stExpander"\]' 'border-color: var(--hhs-theme-border-color)'

  run grep -q -- '--hhs-element-std-gap: 1rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-filter-control-gap' "${css_file}"
  assert_failure

  run grep -q -- '--hhs-inline-control-gap' "${css_file}"
  assert_failure

  assert_file_contains_many "${css_file}" \
'gap: var(--hhs-element-std-gap)' 'gap: var(--hhs-element-std-gap) !important' \
    'div\[data-testid="stHorizontalBlock"\]:has(.st-key-env_other_filter)' \
    'div\[data-testid="stHorizontalBlock"\]:has(.st-key-home_shopts_other_filter)' \
    'div\[data-testid="stHorizontalBlock"\]:has(.st-key-home_tools_filter)' \
    'div\[data-testid="stHorizontalBlock"\]:has(.st-key-ssh_tunnel_filter)' \
    'div\[data-testid="stHorizontalBlock"\]:has(.st-key-ssh_tunnel_other_filter)' \
    'div\[data-testid="stHorizontalBlock"\]:has(.st-key-ssh_tunnel_filter) > div\[data-testid="stColumn"\]:first-child'
  assert_file_not_contains "${css_file}" '.st-key-ssh_tunnel_filter \[role="radiogroup"\]'

  run python3 - "${css_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(
    r'^\[role="radiogroup"\]\[aria-label\$="filter"\]\s*\{(?P<body>[^}]*)\}',
    source,
    flags=re.MULTILINE,
)
assert match is not None
body = match.group("body")
assert "flex-wrap: wrap" in body
assert "overflow-x: visible" in body
assert "overflow-x: auto" not in body
PY
  assert_success

  assert_file_contains_many "${css_file}" \
'.st-key-home_shopts_other_filter input' 'div\[data-testid="stColumn"\]:first-child' \
    'div\[data-testid="stColumn"\]:last-child' 'flex: 0 0 auto !important' \
    'div\[data-testid="stColumn"\]:nth-child(2)' 'flex: 1 1 auto !important' \
    'flex: 0 0 2.1rem !important' 'align-self: center !important' \
    'div\[class\*="_other_filter_clear"\] button' 'height: 2rem' \
    'max-width: none' 'width: 100%'
}

@test "when rendering table filters then legacy ad hoc filter labels should stay removed" {
  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
old_labels = (
    "Tools filter",
    "Tools filter text",
    "Environment filter",
    "Environment filter text",
    "PATH filter",
    "PATH filter text",
    "DIR filter",
    "DIR filter text",
    "COMMAND filter",
    "COMMAND filter text",
    "ALIAS filter",
    "ALIAS filter text",
    "SERVICE filter",
    "SERVICE filter text",
    "COMMANDS filter",
    "COMMANDS filter text",
    "DIRECTORIES filter",
    "DIRECTORIES filter text",
    ">Filter</span>",
    'st.text_input("Filter"',
)
missing_defaults = (
    '"Filters"',
    '"Select a row to interact"',
)
violations = [label for label in old_labels if label in source]
violations.extend(default for default in missing_defaults if default not in source)
if violations:
    raise AssertionError("\n".join(violations))
PY
  assert_success
}
