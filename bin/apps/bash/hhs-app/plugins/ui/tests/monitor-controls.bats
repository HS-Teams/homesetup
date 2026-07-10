#!/usr/bin/env bats

#  Script: monitor-controls.bats
# Purpose: HomeSetup Streamlit UI monitor control tests.
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

@test "when rendering History and Monitor controls then Top N state should be normalized" {
  assert_file_contains "${constants_file}" 'HISTORY_VIEWS = ("COMMANDS", "DIRECTORIES", "STATS")'
  assert_file_contains_many "${ui_file}" \
'def history_view_label' 'format_func=history_view_label'
  assert_file_contains "${constants_file}" 'MONITOR_VIEWS = ("DISK", "MEM", "CPU", "PROCESSES", "LOGS")'
  assert_file_contains_many "${ui_file}" \
'def monitor_view_label' 'format_func=monitor_view_label'
  assert_file_contains_many "${command_catalog_file}" \
'def normalized_monitor_disk_top_n' \
    'def normalized_history_stats_top_n'
  assert_file_contains_many "${constants_file}" \
'DEFAULT_TOP_N = 10' 'MIN_TOP_N = 1' 'MAX_TOP_N = 100' \
    '"monitor_cpu_top_n"' '"monitor_mem_top_n"'
  assert_file_contains "${command_catalog_file}" 'def normalized_monitor_top_n'
  assert_file_contains "${ui_file}" \
'st.session_state\["history_stats_top_n"\] = normalized_history_stats_top_n'
  assert_file_contains_many "${table_ui_file}" \
    '"min_value": hhs_ui_constants.MIN_TOP_N' '"max_value": hhs_ui_constants.MAX_TOP_N'

  run python3 - <<'PY'
import ast
import types
from pathlib import Path

source = (
    Path("bin/apps/py/hhs_ui/command_catalog.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/monitor_runtime.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
)
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
namespace = {
    "hhs_ui_constants": types.SimpleNamespace(
        DEFAULT_TOP_N=10,
        MIN_TOP_N=1,
        MAX_TOP_N=100,
    )
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "normalized_top_n",
            "normalized_monitor_top_n",
            "normalized_history_stats_top_n",
            "normalized_monitor_disk_top_n",
            "monitor_process_top_n_state_key",
            "monitor_process_top_n_input_key",
        )
    ),
    namespace,
)

assert namespace["normalized_top_n"](None) == 10
assert namespace["normalized_top_n"](True) == 10
assert namespace["normalized_top_n"](False) == 10
assert namespace["normalized_top_n"]("0") == 10
assert namespace["normalized_top_n"]("101") == 10
assert namespace["normalized_top_n"]("25") == 25
assert namespace["normalized_monitor_top_n"](None) == 10
assert namespace["normalized_monitor_top_n"](True) == 10
assert namespace["normalized_monitor_top_n"]("0") == 10
assert namespace["normalized_monitor_top_n"]("101") == 10
assert namespace["normalized_monitor_top_n"]("25") == 25
assert namespace["normalized_history_stats_top_n"](None) == 10
assert namespace["normalized_history_stats_top_n"](True) == 10
assert namespace["normalized_history_stats_top_n"]("25") == 25
assert namespace["normalized_monitor_disk_top_n"]("12") == 12
assert namespace["monitor_process_top_n_state_key"]("CPU") == "monitor_cpu_top_n"
assert namespace["monitor_process_top_n_state_key"]("MEM") == "monitor_mem_top_n"
assert namespace["monitor_process_top_n_input_key"]("CPU") == "monitor_cpu_top_n_input"
assert namespace["monitor_process_top_n_input_key"]("MEM") == "monitor_mem_top_n_input"
PY
  assert_success
}

@test "when rendering Monitor disk and process controls then remote host context should be preserved" {
  assert_file_contains_many "${monitor_runtime_file}" \
'def monitor_disk_directory_for_host' 'def synchronize_monitor_disk_directory_with_host' \
    'def monitor_process_top_n_state_key' 'def handle_monitor_process_top_n_change' \
    'def monitor_metric_command' 'normalized_monitor_process_top_n(metric)'
  assert_file_contains_many "${ui_file}" \
    '"ssh_files"' 'key="monitor_disk_top_n_input"' \
    'on_change=handle_monitor_disk_top_n_change' 'on_change=handle_monitor_process_top_n_change' \
    'on_click=apply_monitor_process_controls' 'for metric in ("CPU", "MEM"):' \
    'process_monitor_chart_rows(result.stdout, metric, applied_top_n)' \
    'Top {applied_top_n} {title} processes' 'def process_monitor_chart_rows' \
    'top -b -n 2 -d 1 -o {linux_sort} -w 512' 'No CPU usage above 0.0% found.'
  assert_file_contains "${command_catalog_file}" 'return hhs_ui_constants.DEFAULT_TOP_N'

  run python3 - <<'PY'
import ast
import os
import re
import shlex
from pathlib import Path
from types import SimpleNamespace

source = (
    Path("bin/apps/py/hhs_ui/command_catalog.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/monitor_runtime.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
)
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
host = ""
namespace = {
    "hhs_ui": SimpleNamespace(
        ANSI_ESCAPE_PATTERN=re.compile(
            r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
        ),
        ESCAPED_ANSI_ESCAPE_PATTERN=re.compile(
            r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
        ),
    ),
    "hhs_ui_constants": SimpleNamespace(MIN_TOP_N=1, MAX_TOP_N=100),
    "os": os,
    "re": re,
    "shlex": shlex,
    "connected_ssh_host": lambda: host,
    "homesetup_home": lambda: Path("/Users/hjunior/HomeSetup"),
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "strip_ansi",
            "monitor_default_disk_directory",
            "monitor_disk_directory_is_hhs_home_token",
            "expand_monitor_disk_directory",
            "monitor_disk_directory_for_host",
            "parse_hhs_disk_usage_directory",
            "monitor_disk_display_directory",
            "relative_disk_usage_path",
            "build_hhs_disk_usage_command",
        )
    ),
    namespace,
)

assert namespace["monitor_default_disk_directory"]() == "/Users/hjunior/HomeSetup"
assert namespace["monitor_disk_directory_for_host"]("") == "/Users/hjunior/HomeSetup"
assert namespace["monitor_disk_directory_for_host"]("/Users/hjunior/HomeSetup") == "/Users/hjunior/HomeSetup"
assert namespace["monitor_disk_directory_for_host"]("${HHS_HOME}") == "/Users/hjunior/HomeSetup"

host = "remote-box"
assert namespace["monitor_default_disk_directory"]() == "${HHS_HOME}"
assert namespace["monitor_disk_directory_for_host"]("") == "${HHS_HOME}"
assert namespace["monitor_disk_directory_for_host"]("/Users/hjunior/HomeSetup") == "${HHS_HOME}"
assert namespace["monitor_disk_directory_for_host"]("/root/HomeSetup") == "/root/HomeSetup"
command = namespace["build_hhs_disk_usage_command"]("${HHS_HOME}", 10)
assert '__hhs_du "${HHS_HOME}" 10' in command
output = 'Top 10 disk usage at: "/root/HomeSetup"\n1: /root/HomeSetup/bin..... 12M |'
display_directory = namespace["monitor_disk_display_directory"]("${HHS_HOME}", output)
assert display_directory == "/root/HomeSetup"
assert namespace["relative_disk_usage_path"]("/root/HomeSetup/bin", display_directory) == "bin"
assert namespace["relative_disk_usage_path"]("/root/HomeSetup", display_directory) == "."
PY
  assert_success
}

@test "when rendering monitor process charts then Top N should apply after parsing command output" {
  run python3 - <<'PY'
import ast
import re
from pathlib import Path
from types import SimpleNamespace

source = (
    Path("bin/apps/py/hhs_ui/command_catalog.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/monitor_runtime.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/table_ui.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
)
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
namespace = {
    "hhs_ui": SimpleNamespace(
        ANSI_ESCAPE_PATTERN=re.compile(
            r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
        ),
        ESCAPED_ANSI_ESCAPE_PATTERN=re.compile(
            r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
        ),
        TOP_PROCESS_SORT_KEYS={
            "CPU": {"darwin": "cpu", "linux": "%CPU", "field": "CPU"},
            "MEM": {"darwin": "mem", "linux": "%MEM", "field": "MEM"},
        },
    ),
    "parse_rows_cached": lambda _name, output, parser: parser(output),
    "re": re,
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "strip_ansi",
            "human_size_to_bytes",
            "metric_value",
            "parse_process_monitor",
            "process_monitor_chart_rows",
        )
    ),
    namespace,
)

output = """
PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
1 root 20 0 1 1 1 S 0.0 0.1 0:01 systemd
2 root 20 0 1 1 1 S 0.0 0.0 0:00 kthreadd
PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
88 root 20 0 1 1 1 R 14.5 0.2 0:02 python
1 root 20 0 1 1 1 S 0.0 0.1 0:01 systemd
"""
cpu_rows = namespace["process_monitor_chart_rows"](output, "CPU")
assert [row["Command"] for row in cpu_rows] == ["python"], cpu_rows
assert cpu_rows[0]["Value"] == 14.5

limited_output = """
PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
88 root 20 0 1 1 1 R 14.5 0.2 0:02 python
99 root 20 0 1 1 1 R 7.0 0.8 0:01 node
"""
limited_cpu_rows = namespace["process_monitor_chart_rows"](limited_output, "CPU", 1)
assert [row["Command"] for row in limited_cpu_rows] == ["python"], limited_cpu_rows
limited_mem_rows = namespace["process_monitor_chart_rows"](limited_output, "MEM", 1)
assert [row["Command"] for row in limited_mem_rows] == ["node"], limited_mem_rows

zero_rows = namespace["process_monitor_chart_rows"](
    """
PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
1 root 20 0 1 1 1 S 0.0 0.1 0:01 systemd
""",
    "CPU",
)
assert zero_rows == [], zero_rows

mem_rows = namespace["process_monitor_chart_rows"](
    """
PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
1 root 20 0 1 1 1 S 0.0 0.1 0:01 systemd
""",
    "MEM",
)
assert [row["Command"] for row in mem_rows] == ["systemd"], mem_rows
PY
  assert_success
}

@test "when initializing Top N controls then defaults should be ten" {
  assert_file_contains_many "${constants_file}" \
'DEFAULT_TOP_N = 10' 'MIN_TOP_N = 1' 'MAX_TOP_N = 100'
  run python3 - <<'PY'
import ast
import types
from pathlib import Path

source = (
    Path("bin/apps/py/hhs_ui/command_catalog.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/monitor_runtime.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/table_ui.py").read_text()
    + "\n"
    + Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
)
tree = ast.parse(source)
source_lines = source.splitlines()
functions = {
    node.name: "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
namespace = {
    "hhs_ui_constants": types.SimpleNamespace(
        DEFAULT_TOP_N=10,
        MIN_TOP_N=1,
        MAX_TOP_N=100,
    )
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "normalized_top_n",
            "normalized_monitor_top_n",
            "normalized_history_stats_top_n",
            "normalized_monitor_disk_top_n",
        )
    ),
    namespace,
)

assert namespace["normalized_top_n"](None) == 10
assert namespace["normalized_top_n"](True) == 10
assert namespace["normalized_top_n"](False) == 10
assert namespace["normalized_top_n"]("0") == 10
assert namespace["normalized_top_n"]("101") == 10
assert namespace["normalized_top_n"]("25") == 25
assert namespace["normalized_monitor_top_n"](None) == 10
assert namespace["normalized_monitor_top_n"](True) == 10
assert namespace["normalized_monitor_disk_top_n"](False) == 10
assert namespace["normalized_history_stats_top_n"](True) == 10
assert namespace["normalized_history_stats_top_n"]("25") == 25

main_body = source.split("def main()", 1)[1].split('if __name__ == "__main__"', 1)[0]
assert 'st.session_state["monitor_disk_top_n"] = normalized_monitor_disk_top_n(' in main_body
assert 'st.session_state[top_n_key] = normalized_monitor_top_n(' in main_body
assert 'st.session_state["history_stats_top_n"] = normalized_history_stats_top_n(' in main_body

history_body = source.split("def render_history_stats_chart()", 1)[1].split("\ndef ", 1)[0]
assert history_body.index(
    'st.session_state["history_stats_top_n"] = normalized_history_stats_top_n('
) < history_body.index("render_chart_controls(")
assert '"history_stats_controls"' in history_body
assert 'top_n_key="history_stats_top_n"' in history_body
assert 'refresh_key="history_stats_refresh_button"' in history_body
assert 'refresh_on_click=refresh_history_stats_chart' in history_body
chart_top_n_body = source.split("def render_chart_top_n_input", 1)[1].split("\ndef ", 1)[0]
assert '"min_value"' in chart_top_n_body
assert "hhs_ui_constants.MIN_TOP_N" in chart_top_n_body
assert '"max_value"' in chart_top_n_body
assert "hhs_ui_constants.MAX_TOP_N" in chart_top_n_body
assert "width" in chart_top_n_body
assert "150" in chart_top_n_body
assert source.count("render_chart_controls(") >= 3
assert source.count("plot_chart(") >= 3
for function_name in (
    "build_hhs_history_stats_command",
    "build_hhs_disk_usage_command",
    "build_process_monitor_command",
):
    function_body = functions[function_name]
    assert "hhs_ui_constants.MIN_TOP_N" in function_body
    assert "hhs_ui_constants.MAX_TOP_N" in function_body
PY
  assert_success
}
