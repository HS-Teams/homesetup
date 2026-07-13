#!/usr/bin/env bats

#  Script: monitor.bats
# Purpose: HomeSetup Streamlit UI monitor tests.
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

@test "when rendering monitor panes then process listing and process kill should be wired" {
  assert_file_contains_many "${constants_file}" \
'PROCESS_TABLE_KEY = "monitor_process_table"' 'PROCESS_LIST_LINE_PATTERN' \
    'PROCESS_FILTERS = ("All", "Active", "Inactive", "Ghost", "Containing")' \
    'PROCESS_FILTER_COLUMNS = \[2.65, 1.35\]' '"monitor_process_other_filter"'
  assert_file_contains_many "${ui_file}" \
'normalize_persisted_table_text_filter_states(' 'key.endswith("_other_filter")' \
    'hhs_ui_constants.PERSISTED_UI_KEYS'
  assert_file_not_contains "${ui_file}" 'UI_STATE_KEYS'

  assert_file_contains_many "${command_catalog_file}" \
'def build_hhs_process_list_command' 'def build_hhs_process_kill_command' '__hhs_process_list'
  run python3 - "${HHS_REPO_DIR}/bin/hhs-functions/bash/hhs-sys-utils.bash" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("function __hhs_process_list()", 1)[1].split("\n}", 1)[0]
assert 'read -r uid pid ppid cmd <<<"${next}"' in body
assert 'ps -p "${pid}"' not in body
assert "uid=$(awk" not in body
assert "pid=$(awk" not in body
assert "ppid=$(awk" not in body
assert "cmd=$(awk" not in body
PY
  assert_success

  assert_file_contains "${command_catalog_file}" '__hhs_process_kill -f'
  assert_file_contains_many "${table_ui_file}" \
    'def render_chart_controls' 'def plot_chart' 'Literal\["HBars", "VBars", "Pie"\]' \
    'with st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True):' \
    'top_n_label: str = "Top N:"'
  assert_file_contains_many "${monitor_ui_file}" \
    'def render_monitor_processes_panel' '"monitor_disk_controls"' 'f"monitor_{metric.lower()}_controls"' \
    '"history_stats_controls"' 'input_label="Directory:"' 'refresh_key="monitor_disk_apply_button"' \
    'refresh_key=f"monitor_{metric.lower()}_refresh_button"' 'refresh_key="history_stats_refresh_button"' \
    'refresh_on_click=refresh_history_stats_chart'
  assert_file_contains_many "${css_file}" \
'.st-key-history_stats_refresh_button button' '.st-key-monitor_disk_apply_button button' \
    '.st-key-monitor_mem_refresh_button button' '.st-key-monitor_cpu_refresh_button button' \
    '.st-key-monitor_disk_controls \[data-testid="stExpanderDetails"\] > \[data-testid="stVerticalBlock"\]' \
    '.st-key-history_stats_controls \[data-testid="stExpanderDetails"\]' \
    ':has(.st-key-history_stats_refresh_button)' ':has(.st-key-monitor_mem_refresh_button)' \
    'display: grid !important' ':has(.st-key-monitor_disk_apply_button)' \
    'grid-template-columns: max-content 150px minmax(0, 1fr) 2rem' \
    'grid-template-columns: max-content 150px max-content minmax(0, 1fr) 2rem' 'justify-self: end'
  run python3 - "${table_ui_file}" "${monitor_ui_file}" <<'PY'
from pathlib import Path
import sys

table_source = Path(sys.argv[1]).read_text(encoding="utf-8")
ui_source = Path(sys.argv[2]).read_text(encoding="utf-8")
chart_controls_body = table_source.split("def render_chart_controls", 1)[1].split(
    "\ndef ", 1
)[0]
disk_body = ui_source.split("def render_monitor_disk_chart", 1)[1].split("\ndef ", 1)[0]
process_chart_body = ui_source.split("def render_process_monitor_chart", 1)[1].split(
    "\ndef ", 1
)[0]
process_panel_body = ui_source.split("def render_monitor_processes_panel", 1)[1].split(
    "\ndef ", 1
)[0]
assert 'gap="small"' in chart_controls_body
assert (
    "top_label_col, top_input_col, _spacer_col, action_col = st.columns"
    in chart_controls_body
)
assert "[0.55, 0.75, 3.0, 0.45]" in chart_controls_body
assert "[0.55, 0.75, 0.85, 3.0, 0.45]" in chart_controls_body
assert "render_chart_top_n_input" in chart_controls_body
assert 'render_chart_control_label(top_n_label)' in chart_controls_body
assert 'render_chart_control_label(str(input_label))' in chart_controls_body
assert 'render_chart_refresh_button' in chart_controls_body
assert 'help": "Refresh chart data"' in table_source
assert "width" in table_source.split("def render_chart_top_n_input", 1)[1].split("\ndef ", 1)[0]
assert "150" in table_source.split("def render_chart_top_n_input", 1)[1].split("\ndef ", 1)[0]
assert "render_chart_controls(" in disk_body
assert "render_chart_controls(" in process_chart_body
assert "plot_chart(" in disk_body
assert "plot_chart(" in process_chart_body
assert 'st.altair_chart(chart, width="stretch", height=fallback_height)' in table_source
assert disk_body.index("top_n_key=") < disk_body.index("input_label=")
assert process_panel_body.count("complete_monitor_process_list_refresh()") >= 3
assert process_panel_body.index("result = complete_monitor_process_list_refresh()") < process_panel_body.index(
    "start_monitor_process_list_refresh()"
)
assert process_panel_body.index("render_background_job_status(MONITOR_PROCESS_LIST_JOB)") < process_panel_body.rindex(
    "result = complete_monitor_process_list_refresh()"
)
PY
  assert_success

  assert_file_contains_many "${monitor_ui_file}" \
'"monitor_process_filter"' '"monitor_process_other_filter"' 'hhs_ui.PROCESS_FILTERS' \
    'hhs_ui.PROCESS_FILTER_COLUMNS' 'filter_process_rows(' \
    'render_table_controls_panel(render_process_controls)'
  assert_file_contains "${command_catalog_file}" 'def filter_process_rows'
  assert_file_not_contains_many "${monitor_ui_file}" \
'monitor_process_filter_apply_button' 'apply_monitor_process_filter'
  assert_file_contains "${css_file}" '.st-key-monitor_process_other_filter'
}

@test "when filtering monitor processes then status and other filters should use parsed rows" {
  run python3 - "${command_catalog_file}" <<'PY'
import ast
import re
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
namespace = {
    "re": re,
    "hhs_ui": SimpleNamespace(
        ANSI_ESCAPE_PATTERN=re.compile(
            r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
        ),
        ESCAPED_ANSI_ESCAPE_PATTERN=re.compile(
            r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
        ),
        PROCESS_LIST_LINE_PATTERN=re.compile(
            r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(.+?)\s+(?:\S+\s+)?(active|inactive|ghost) process$",
            re.IGNORECASE,
        ),
    ),
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "strip_ansi",
            "row_matches_text_filter",
            "filter_process_rows",
            "parse_hhs_process_list",
        )
    ),
    namespace,
)
output = """
  501  1001     1 python                                  ✓ active process
  501  1002     1 stale-worker                            ✕ ghost process
  501  1003     1 stopped-worker                          ✕ inactive process
"""
rows = namespace["parse_hhs_process_list"](output)
assert [row["Status"] for row in rows] == ["Active", "Ghost", "Inactive"], rows
assert [row["PID"] for row in namespace["filter_process_rows"](rows, "Active")] == ["1001"]
assert [row["PID"] for row in namespace["filter_process_rows"](rows, "Ghost")] == ["1002"]
assert [row["PID"] for row in namespace["filter_process_rows"](rows, "Inactive")] == ["1003"]
assert [row["PID"] for row in namespace["filter_process_rows"](rows, "Other", "stale")] == ["1002"]
assert [row["PID"] for row in namespace["filter_process_rows"](rows, "Containing", "stale")] == ["1002"]
assert namespace["filter_process_rows"](rows, "All") == rows
PY
  assert_success
}

# TC - 17

@test "when rendering logs then VT100 colors and tail refresh should be handled in the LOGS panel" {
  assert_file_contains_many "${constants_file}" \
'LOG_TAILOR_RULES' 'LOG_LEVELS = (' 'DEFAULT_LOG_TAIL_LINES = 50' 'LEGACY_DEFAULT_LOG_TAIL_LINES = 10' \
    'MIN_LOG_TAIL_LINES = 5' 'MAX_LOG_TAIL_LINES = 5000' 'LOG_TAIL_LINES_STEP = 5' \
    'LOG_FILTERS = ("All", "Containing")'
  assert_hhs_ui_exports LOG_LEVELS LOG_FILTERS
  assert_file_contains_many "${constants_file}" \
'"monitor_log_filter"' '"monitor_log_other_filter"' '"monitor_log_level"' '"monitor_log_tail_lines"' \
    '"monitor_log_tail_lines_default_migrated"'
  assert_file_contains_many "${command_catalog_file}" \
'def colorize_log_output' 'def log_filter_highlight_ranges' 'def filter_log_output' \
    'def normalized_monitor_log_tail_lines'
  assert_file_contains_many "${monitor_runtime_file}" \
'def selected_monitor_log_level' 'def monitor_log_level_label' \
    'def normalize_monitor_log_tail_lines_state' 'def handle_monitor_log_tail_lines_change' \
    'def clear_monitor_log_file' 'def toggle_monitor_logs_tail'
  assert_file_contains_many "${monitor_ui_file}" \
    'def render_monitor_logs_panel' 'def render_log_controls' \
    'tail_lines,' 'render_log_controls' 'render_table_filter_controls(' \
    'hhs_ui.LOG_FILTERS'
  assert_file_not_contains "${monitor_ui_file}" 'other_options=("Containing",)'

  assert_file_contains "${table_ui_file}" \
'other_options: tuple\[str, ...\] = ("Other", "Others", "Containing")'
  assert_file_contains "${ui_file}" 'def render_persisted_expander_state_script'
  assert_file_contains_many "${monitor_ui_file}" \
    '"monitor_log_filter"' '"monitor_log_other_filter"' 'st.container(key="monitor_log_controls")' \
    'render_persisted_expander_state_script(' \
    '".st-key-monitor_log_controls"' '"hhs.monitor.logs.controls.expanded"' \
    '\[0.32, 1.0, 0.36, 0.85, 0.46, 0.34, 0.16, 0.16\]' 'File:'
  assert_file_contains_many "${ui_file}" \
    'parentWindow.localStorage.getItem(storageKey)' 'marker?.closest("details")' \
    'expander.addEventListener("toggle"'
  assert_file_not_contains "${monitor_ui_file}" 'Log file:'

  assert_file_contains "${monitor_ui_file}" 'Level:'

  assert_file_not_contains "${monitor_ui_file}" 'Log level:'

  assert_file_contains_many "${monitor_ui_file}" \
'Bot N:' 'render_standard_number_spinner(' 'key="monitor_log_tail_lines"' \
    'min_value=hhs_ui_constants.MIN_LOG_TAIL_LINES' 'max_value=hhs_ui_constants.MAX_LOG_TAIL_LINES' \
    'step=hhs_ui_constants.LOG_TAIL_LINES_STEP' 'width=150'
  assert_file_contains_many "${table_ui_file}" \
    'def render_standard_number_spinner' 'st.number_input(' \
    'render_standard_number_spinner("Top N"'
  assert_file_not_contains_many "${monitor_ui_file}" \
'monitor_log_tail_lines_decrement_button' 'monitor_log_tail_lines_increment_button'
  assert_file_contains_many "${monitor_ui_file}" \
'on_change=handle_monitor_log_tail_lines_change' \
    'tail_button_state = "selected" if tail_enabled_value else "idle"' \
    'key=f"monitor_logs_tail_button_{tail_button_state}"' '"",'
  assert_file_not_contains_many "${monitor_ui_file}" \
'""' 'tail_enabled_value = st.checkbox'
  assert_file_contains_many "${monitor_ui_file}" \
'on_click=toggle_monitor_logs_tail' 'key="monitor_log_clear_button"' '"",'
  assert_file_not_contains "${monitor_ui_file}" '""'

  assert_file_contains_many "${monitor_ui_file}" \
'key="monitor_log_level"' 'build_hhs_logs_command(selected_log, tail_lines, selected_level)'
  assert_file_not_contains "${monitor_ui_file}" \
'build_hhs_logs_command(selected_log, 200, selected_level)'
  assert_file_contains_many "${paths_file}" \
'def hhs_log_file_info(log_file: str)' '"HHS_LOG_DIR": str(hhs_log_dir())'
  assert_file_contains_many "${monitor_ui_file}" \
    'log_file_path = hhs_log_file_info(selected_log)\[0\]' \
    'render_openable_file_pill("Selected log file:", log_file_path)'
  run python3 - "${monitor_ui_file}" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
monitor_logs_body = source.split("def render_monitor_logs_panel", 1)[1].split("\ndef ", 1)[0]
assert 'render_openable_file_pill("Selected log file:", log_file_path)' in monitor_logs_body
assert "render_view_subtitle(" not in monitor_logs_body
assert monitor_logs_body.index("render_log_controls)") < monitor_logs_body.index(
    "log_file_path = hhs_log_file_info(selected_log)[0]"
)
PY
  assert_success

  run python3 - <<'PY'
import ast
import re
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/execution/command_catalog.py").read_text()
module = ast.parse(source)
selected = [
    node for node in module.body
    if isinstance(node, ast.FunctionDef)
    and node.name in {
        "strip_ansi",
        "overlaps_existing_range",
        "log_tailor_highlight_ranges",
        "log_filter_highlight_ranges",
        "colorize_log_output",
        "filter_log_output",
        "normalized_monitor_log_tail_lines",
    }
]
namespace = {
    "html": __import__("html"),
    "re": re,
    "hhs_ui_constants": type(
        "HhsUiConstants",
        (),
        {
            "DEFAULT_LOG_TAIL_LINES": 50,
            "MIN_LOG_TAIL_LINES": 5,
            "MAX_LOG_TAIL_LINES": 5000,
        },
    ),
    "hhs_ui": type(
        "HhsUi",
        (),
        {
            "ANSI_ESCAPE_PATTERN": re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"),
            "ESCAPED_ANSI_ESCAPE_PATTERN": re.compile(r"\\033\[[0-9;]*m"),
            "LOG_TAILOR_RULES": (),
        },
    ),
}
exec(compile(ast.Module(body=selected, type_ignores=[]), "<filter_log_output>", "exec"), namespace)
output = "INFO boot\nWARN skipped\nERROR failed\n"
assert namespace["filter_log_output"](output, "All", "warn") == output
assert namespace["filter_log_output"](output, "Containing", "warn") == "WARN skipped"
assert namespace["filter_log_output"](output, "Containing", "") == output
highlighted = namespace["colorize_log_output"]("WARN skipped", "warn")
assert '<span class="hhs-log-filter-match">WARN</span>' in highlighted
assert namespace["normalized_monitor_log_tail_lines"](None) == 50
assert namespace["normalized_monitor_log_tail_lines"]("4") == 5
assert namespace["normalized_monitor_log_tail_lines"]("25") == 25
assert namespace["normalized_monitor_log_tail_lines"]("6000") == 5000
PY
  assert_success

  assert_file_contains "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/functions/built-ins.bash" 'awk -v level="${level}" '\''toupper($3) == level'\'''

  assert_file_not_contains "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/functions/built-ins.bash" 'grep -i "${level}"'

  run bash --noprofile --norc -c '
    set -e
    tmp_dir="$(mktemp -d)"
    trap "rm -rf \"${tmp_dir}\"" EXIT
    mkdir -p "${tmp_dir}/log"
    cat > "${tmp_dir}/log/hhsrc.log" <<'"'"'LOGS'"'"'
07-02-26 00:13:01   INFO  Loading dotfile
07-02-26 00:13:02   WARN  Setting alias: "os-info" was skipped because it already exists !
07-02-26 00:13:03   ERROR  Failed to load test
LOGS
    export HHS_LOG_DIR="${tmp_dir}/log"
    export HHS_LOG_FILE="${tmp_dir}/log/hhsrc.log"
    export APP_NAME="hhs"
    NC= RED= GREEN= YELLOW= WHITE= BLUE= PURPLE= CYAN= VIOLET= POINTER_ICN=
    function quit() { return "${1:-0}"; }
    function list_contains() { [[ -n "${1}" && -n "${2}" && ${1} =~ (^|[[:space:]])${2}($|[[:space:]]) ]]; }
    function __hhs_errcho() { printf "%s\n" "$*" >&2; }
    source "${1}/bin/hhs-functions/bash/hhs-taylor.bash"
    source "${1}/bin/apps/bash/hhs-app/functions/built-ins.bash"
    output="$(logs hhsrc.log INFO)"
    [[ "${output}" == *"INFO  Loading dotfile"* ]]
    [[ "${output}" != *"os-info"* ]]
    [[ "${output}" != *"WARN  Setting alias"* ]]
  ' -- "${HHS_REPO_DIR}"
  assert_success

  assert_file_contains_many "${css_file}" \
'.st-key-monitor_log_clear_button button' '.st-key-monitor_logs_tail_button_idle button' \
    '.st-key-monitor_logs_tail_button_selected button' '.hhs-log-filter-match'
  run grep -q -- '--hhs-log-expander-collapsed-height: 3.4rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-open-height: 230px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-height: var(--hhs-log-expander-collapsed-height)' "${css_file}"
  assert_success

  run grep -Fq -- '[data-testid="stVerticalBlock"]:has(.hhs-log-output):has(details[open])' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-height: var(--hhs-log-expander-open-height)' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'background-color: #2563eb' 'color: #ffffff !important' \
    '.st-key-monitor_log_controls \[data-testid="stHorizontalBlock"\]' \
    'gap: var(--hhs-element-std-gap) !important' 'flex-wrap: nowrap !important' \
    '.st-key-monitor_log_controls [data-testid="stHorizontalBlock"]:has([class*="st-key-monitor_logs_tail_button_"])' \
    '> div\[data-testid="stColumn"\]:nth-child(1)' '> div\[data-testid="stColumn"\]:nth-child(3)' \
    '> div\[data-testid="stColumn"\]:nth-child(5)' 'min-width: max-content' 'flex: 1 1 0 !important' \
    '> div\[data-testid="stColumn"\]:nth-child(6)' 'flex: 0 0 150px !important' 'min-width: 150px'
  assert_file_not_contains_many "${css_file}" \
'monitor_log_tail_lines_decrement_button' 'monitor_log_tail_lines_increment_button'
  assert_file_contains_many "${css_file}" \
'> div\[data-testid="stColumn"\]:nth-child(7)' '> div\[data-testid="stColumn"\]:nth-child(8)' \
    'flex: 0 0 2rem !important'
  run grep -q -- '--hhs-log-chrome-height: 8.5rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-open-height: 230px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-height-reduction: 50px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-height: calc(100dvh - var(--hhs-log-chrome-height) - var(--hhs-footer-guard-height) - var(--hhs-log-expander-height) - var(--hhs-log-height-reduction))' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-max-height: calc(var(--hhs-ttyd-max-height, 760px) - var(--hhs-log-expander-height) - var(--hhs-log-height-reduction))' "${css_file}"
  assert_success

  assert_file_contains_many "${css_file}" \
'height: var(--hhs-log-height)' 'max-height: min(var(--hhs-log-height), var(--hhs-log-max-height))' \
    'min-height: 280px'
  assert_file_contains_many "${monitor_ui_file}" \
'@st.fragment(run_every="5s")' 'if not bool(st.session_state.get("monitor_logs_tail", True)):'
  assert_file_contains_many "${css_file}" \
'white-space: pre' '.hhs-view-subtitle' '\[data-testid="stMain"\] \[data-testid="stVegaLiteChart"\]' \
    'margin-top: var(--hhs-element-std-gap) !important' '\[data-testid="stVegaLiteChart"\] > div' \
    'div:has(\[data-testid="stVegaLiteChart"\])' 'padding-bottom: 0 !important' 'margin: 0 !important' \
    '.hhs-log-output' 'margin: 0;'
}

# TC - 18
