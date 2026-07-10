#!/usr/bin/env bats

#  Script: config-tables.bats
# Purpose: HomeSetup Streamlit UI config and history table tests.
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

@test "when listing saved dirs then hhs load dir should not fall through to alias loading" {
  run bash --noprofile --norc -c '
    export HHS_DIR="${1}/hhs"
    export HHS_SAVED_DIRS_FILE="${HHS_DIR}/.saved_dirs"
    export HHS_HIGHLIGHT_COLOR=""
    export WHITE=""
    export GREEN=""
    export YELLOW=""
    export NC=""
    mkdir -p "${HHS_DIR}" "${1}/project"
    printf "PROJECT=%s/project\n" "${1}" > "${HHS_SAVED_DIRS_FILE}"
    function __hhs_errcho() {
      printf "%s\n" "$*" >&2
    }
    source "${2}/bin/hhs-functions/bash/hhs-dirs.bash"
    __hhs_load_dir -l
  ' -- "${BATS_TEST_TMPDIR}" "${HHS_REPO_DIR}"
  assert_success
  assert_output --partial 'PROJECT'
  refute_output --partial 'Alias "" not found'
}
@test "when listing directory history with no recorded dirs then hhs dirs should print an explicit message" {
  run bash --noprofile --norc -c '
    export HHS_DIR="${1}/hhs"
    export HHS_DIRS_FILE="${HHS_DIR}/.dirs"
    mkdir -p "${HHS_DIR}"
    : > "${HHS_DIRS_FILE}"
    function dirs() {
      return 0
    }
    source "${2}/bin/hhs-functions/bash/hhs-dirs.bash"
    __hhs_dirs -l
  ' -- "${BATS_TEST_TMPDIR}" "${HHS_REPO_DIR}"
  assert_success
  assert_output --partial 'No directories recorded yet'
}
@test "when rendering directory history then Streamlit should handle successful empty output" {
  assert_file_contains_many "${ui_file}" \
'message = strip_ansi(result.stdout).strip() or "No directories recorded yet"' 'st.info(message)'
}
@test "when parsing saved dirs then escaped ANSI sequences should be stripped" {
  run python3 - <<'PY'
import re

ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Za-z0-9])"
)
ESCAPED_ANSI_ESCAPE_PATTERN = re.compile(
    r"(?:\\033|\\x1b|\\e)(?:\[[0-?]*[ -/]*[@-~]|\][^\\]*(?:\\a|\\033\\|\\x1b\\)|[()][A-Za-z0-9])"
)
DIR_LINE_PATTERN = re.compile(r"^(.+?)\.{2,}\s+(?:|=>)\s+'?(.*?)'?$")

def strip_ansi(value):
    return ESCAPED_ANSI_ESCAPE_PATTERN.sub("", ANSI_ESCAPE_PATTERN.sub("", value))

def parse_hhs_dirs(output):
    rows = []
    for line in strip_ansi(output).splitlines():
        match = DIR_LINE_PATTERN.match(line.strip())
        if match:
            rows.append({"Name": match.group(1).strip(), "Value": match.group(2).strip()})
    return rows

rows = parse_hhs_dirs(r"\033[0;36mAKS\033[0;97m......................................  '/tmp/aks'")
assert rows == [{"Name": "AKS", "Value": "/tmp/aks"}], rows
PY
  assert_success
}
@test "when building ENV rows then the command should load HomeSetup shell environment" {
  run python3 - "${command_catalog_file}" "${BATS_TEST_TMPDIR}" "${HHS_REPO_DIR}" <<'PY'
import os
import shlex
import subprocess
import sys
from pathlib import Path

ui_source = Path(sys.argv[1]).read_text(encoding="utf-8")
command_source = Path("bin/apps/py/hhs_ui/command_catalog.py").read_text(encoding="utf-8")
source = command_source + "\n" + ui_source
tmp_dir = Path(sys.argv[2])
repo_dir = Path(sys.argv[3])
start = source.index("def build_hhs_env_environment_command()")
end = source.index("def build_hhs_env_action_command(")
namespace = {"shlex": shlex}
exec("from __future__ import annotations\n" + source[start:end], namespace)

hhs_dir = tmp_dir / "hhs-env-command"
home_dir = tmp_dir / "home"
custom_bin = hhs_dir / "custom-bin"
hhs_dir.mkdir(parents=True, exist_ok=True)
home_dir.mkdir(parents=True, exist_ok=True)
custom_bin.mkdir(parents=True, exist_ok=True)
(hhs_dir / ".env").write_text(
    'export HHS_UI_TEST_ENV="from-env-file"\n',
    encoding="utf-8",
)
(hhs_dir / ".path").write_text(f"{custom_bin}\n", encoding="utf-8")
(hhs_dir / ".homesetup.toml").write_text(
    "hhs_python_venv_enabled = false\n",
    encoding="utf-8",
)

command = namespace["build_hhs_envs_command"]("^HHS_UI_TEST_ENV$|^PATH$")
assert 'source "${HHS_HOME}/dotfiles/bash/bash_env.bash";' in command
assert '[[ -s "${HHS_ENV_FILE}" ]] && source "${HHS_ENV_FILE}";' in command
assert 'HHS_PATHS_FILE' in command

result = subprocess.run(
    ["bash", "--noprofile", "--norc", "-c", command],
    env={
        "HOME": str(home_dir),
        "HHS_HOME": str(repo_dir),
        "HHS_DIR": str(hhs_dir),
        "PATH": "/usr/bin:/bin",
        "TERM": "xterm-256color",
        "COLUMNS": "260",
    },
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=30,
    check=False,
)
assert result.returncode == 0, result.stderr or result.stdout
assert "HHS_UI_TEST_ENV" in result.stdout, result.stdout
assert "from-env-file" in result.stdout, result.stdout
assert str(custom_bin) in result.stdout, result.stdout
PY
  assert_success
}
@test "when parsing command-backed config rows then non-PATH parsers should not read process environment" {
  run python3 - "${command_catalog_file}" <<'PY'
import ast
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(source)
parser_names = {
    "parse_hhs_envs",
    "parse_hhs_dirs",
    "parse_hhs_commands",
    "parse_hhs_aliases",
}
parsers = {
    node.name: node
    for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name in parser_names
}
assert set(parsers) == parser_names, parsers
for name, node in parsers.items():
    body = ast.unparse(node)
    assert "os.environ" not in body, (name, body)
    assert "getenv" not in body, (name, body)
PY
  assert_success
}
@test "when parsing PATH rows then command output should provide path values" {
  run python3 - "${command_catalog_file}" <<'PY'
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

ui_source = Path(sys.argv[1]).read_text(encoding="utf-8")
command_source = Path("bin/apps/py/hhs_ui/command_catalog.py").read_text(encoding="utf-8")
source = command_source + "\n" + ui_source
start = source.index("def path_sources(")
end = source.index("def env_widget_key_fragment(")
namespace = {
    "HHS_PATHS_RAW_ENTRY_MARKER": "__HHS_UI_PATH_ENTRY__",
    "hhs_ui": SimpleNamespace(
        PATH_SOURCE_PATTERN=re.compile(r"(?:|=>)\s+(.*)$"),
        PATH_TYPE_PATTERN=re.compile(r"^(\S+)\s+"),
    ),
    "os": os,
    "strip_ansi": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

os.environ["PATH"] = "/wrong/streamlit/path:/another/wrong/path"
output = "\n".join(
    (
        " /truncated/custom................................  Custom path",
        " /truncated/shell.................................  Shell export",
        "__HHS_UI_PATH_ENTRY__\t/actual/custom/path",
        "__HHS_UI_PATH_ENTRY__\t/actual/shell/path",
    )
)
rows = namespace["parse_hhs_paths"](output)
assert [row["Path Value"] for row in rows] == [
    "/actual/custom/path",
    "/actual/shell/path",
], rows
assert [row["Origin"] for row in rows] == ["Custom path", "Shell export"], rows
assert list(rows[0]) == ["Type", "Origin", "Path Value", "_Path Status"], rows
assert namespace["path_entries"]("") == ["/wrong/streamlit/path", "/another/wrong/path"]
PY
  assert_success
}
@test "when rendering table rows then path values are visually abbreviated with env vars" {
  run python3 - "${ui_file}" <<'PY'
import os
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def env_path_aliases(")
end = source.index("def render_table(")
namespace = {"os": os, "re": re}
exec("from __future__ import annotations\n" + source[start:end], namespace)

os.environ.clear()
os.environ.update(
    {
        "HOME": "/Users/hjunior",
        "HHS_HOME": "/Users/hjunior/HomeSetup",
        "HHS_DIR": "/Users/hjunior/.config/hhs",
        "PATH": "/bin:/usr/bin",
        "PLAIN": "not-a-path",
    }
)

rows = [
    {"Name": "Repo", "Value": "/Users/hjunior/HomeSetup/bin"},
    {"Name": "Config", "Value": "/Users/hjunior/.config/hhs/log/app.log"},
    {"Name": "Other", "Value": "/opt/tool"},
    {
        "Name": "List",
        "Value": "/Users/hjunior/HomeSetup/bin:/Users/hjunior/.config/hhs/bin",
    },
]

display_rows = namespace["display_table_rows"](rows)
assert display_rows[0]["Value"] == "${HHS_HOME}/bin", display_rows
assert display_rows[1]["Value"] == "${HHS_DIR}/log/app.log", display_rows
assert display_rows[2]["Value"] == "/opt/tool", display_rows
assert display_rows[3]["Value"] == "${HHS_HOME}/bin:${HHS_DIR}/bin", display_rows
assert rows[0]["Value"] == "/Users/hjunior/HomeSetup/bin", rows
PY
  assert_success
}
@test "when rendering history tables then compact columns are headless" {
  run python3 - "${ui_file}" <<'PY'
import sys
import re
from pathlib import Path
from types import SimpleNamespace

ui_source = Path(sys.argv[1]).read_text(encoding="utf-8")
command_source = Path("bin/apps/py/hhs_ui/command_catalog.py").read_text(encoding="utf-8")
source = command_source + "\n" + ui_source
start = source.index("def history_command_display_index(")
end = source.index("def table_selection_key_prefixes()")
parse_start = source.index("def parse_legacy_hhs_history_line(")
parse_end = source.index("def parse_hhs_history_dirs(")

class ColumnConfig:
    """Stub Streamlit column config used by the pure helper test."""

    def TextColumn(self, label, width=None, disabled=False):
        """Return the requested text column label and width."""
        return {"disabled": disabled, "label": label, "width": width}


class FakeIndex(list):
    """Stub dataframe index with a mutable name."""

    name = None


class FakeDataFrame:
    """Stub pandas DataFrame behavior used by history command table helpers."""

    def __init__(self, rows, columns):
        """Store row dictionaries and ordered column labels."""
        self.rows = [dict(row) for row in rows]
        self.columns = list(columns)
        self.index = FakeIndex()

    def __setitem__(self, column, values):
        """Assign one column across all stub rows."""
        for row, value in zip(self.rows, values):
            row[column] = value
        if column not in self.columns:
            self.columns.append(column)

    def set_index(self, column):
        """Move one column into the stub index and return this dataframe."""
        self.index = FakeIndex([row[column] for row in self.rows])
        self.columns = [name for name in self.columns if name != column]
        return self


namespace = {
    "hhs_ui_constants": SimpleNamespace(
        CMD_INDEX_COLUMN_WIDTH=80,
        HISTORY_DIRECTORY_TYPE_COLUMN_WIDTH=27,
        HISTORY_INDEX_COLUMN_DIGIT_WIDTH=9,
        HISTORY_INDEX_COLUMN_MIN_WIDTH=36,
        HISTORY_INDEX_COLUMN_PADDING=24,
    ),
    "display_table_rows": lambda rows: rows,
    "pd": SimpleNamespace(DataFrame=FakeDataFrame),
    "st": SimpleNamespace(column_config=ColumnConfig()),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

rows = [
    {"Index": "49", "Value": "ls"},
    {"Index": "1200", "Value": "git status"},
]
config = namespace["history_command_column_config"](rows)
table_data = namespace["history_command_table_data"](rows)
assert namespace["history_command_display_index"]("1200") == "!1200"
assert namespace["history_command_display_index"]("") == ""
assert namespace["history_index_column_width"](rows) == 69
assert namespace["history_index_column_width"]([]) == 36
assert config["_index"] == {"disabled": True, "label": "", "width": 69}, config
assert config["Value"] == {"disabled": True, "label": "Value", "width": None}, config
assert list(table_data.index) == ["!49", "!1200"], table_data
assert table_data.index.name == "", table_data
assert list(table_data.columns) == ["Value"], table_data

directory_rows = [
    {"Type": "", "Value": "/tmp"},
    {"Type": "", "Value": "/tmp/link"},
]
directory_config = namespace["history_directory_column_config"]()
directory_table_data = namespace["history_directory_table_data"](directory_rows)
assert directory_config["_index"] == {"disabled": True, "label": "", "width": 27}, directory_config
assert directory_config["Value"] == {
    "disabled": True,
    "label": "Value",
    "width": None,
}, directory_config
assert list(directory_table_data.index) == ["", ""], directory_table_data
assert directory_table_data.index.name == "", directory_table_data
assert list(directory_table_data.columns) == ["Value"], directory_table_data

cmd_config = namespace["cmd_column_config"]()
assert cmd_config == {
    "Index": {"disabled": True, "label": "Index", "width": 80}
}, cmd_config

parse_namespace = {
    "hhs_ui": SimpleNamespace(
        HISTORY_COMMAND_LINE_PATTERN=re.compile(
            r"^(\d+)\.{2,}\s+(?:|➜|→|=>)\s+(.*)$"
        ),
    ),
    "re": re,
    "strip_ansi": lambda value: value,
}
exec("from __future__ import annotations\n" + source[parse_start:parse_end], parse_namespace)
parsed_rows = parse_namespace["parse_hhs_history"](
    """
    49.....................................  ls
    1200...................................  git status
    """
)
parsed_table_data = namespace["history_command_table_data"](parsed_rows)
assert parsed_rows == [
    {"Index": "49", "Value": "ls"},
    {"Index": "1200", "Value": "git status"},
], parsed_rows
assert list(parsed_table_data.index) == ["!49", "!1200"], parsed_table_data

history_body = source.split("def render_history_commands_table()", 1)[1].split("\ndef ", 1)[0]
assert 'headers=["Value"]' in history_body
assert "hide_index=False" in history_body
assert "table_data=history_command_table_data(rows)" in history_body
assert "column_config=history_command_column_config(rows)" in history_body
assert "history_command_display_index(row.get(\"Index\", \"\"))" in source
assert 'parse_rows_cached("history", result.stdout, parse_hhs_history)' in history_body
assert "run_bash_command(" in history_body
assert "ttl_seconds=hhs_ui.UI_CACHE_REALTIME_TTL_SECONDS" in history_body

history_directories_body = source.split("def render_history_directories_table()", 1)[1].split("\ndef ", 1)[0]
assert 'headers=["Value"]' in history_directories_body
assert "hide_index=False" in history_directories_body
assert "table_data=history_directory_table_data(rows)" in history_directories_body
assert "column_config=history_directory_column_config()" in history_directories_body

path_body = source.split("def render_path_rows(", 1)[1].split("\ndef ", 1)[0]
assert "column_config=path_column_config()" in path_body
assert "path_column_config" in source

cmd_body = source.split("def render_cmd_rows(", 1)[1].split("\ndef ", 1)[0]
assert "column_config=cmd_column_config()" in cmd_body

history_command_body = source.split("def build_hhs_history_command()", 1)[1].split("\ndef ", 1)[0]
assert "HISTFILE" in history_command_body
assert "__hhs_history" in history_command_body
PY
  assert_success
}
