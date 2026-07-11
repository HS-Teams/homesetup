#!/usr/bin/env bats

#  Script: core.bats
# Purpose: HomeSetup Streamlit UI plugin tests.
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

@test "when organizing HomeSetup UI modules then responsibilities should be grouped by package" {
  run python3 - "${HHS_REPO_DIR}/bin/apps/py/hhs_ui" <<'PY'
import sys
from pathlib import Path

package_dir = Path(sys.argv[1])
expected_groups = {
    "core": {
        "constants.py",
        "paths.py",
        "process_resources.py",
        "runtime.py",
        "theme_assets.py",
        "ui_definitions.py",
        "ui_state.py",
    },
    "execution": {"cache_runtime.py", "command_catalog.py", "command_runtime.py"},
    "features": {
        "ai_ui.py",
        "hhs_app_ui.py",
        "monitor_runtime.py",
        "monitor_ui.py",
        "search_core.py",
        "search_ui.py",
        "ssh_core.py",
        "ssh_explorer_ui.py",
        "ssh_runtime.py",
    },
    "widgets": {
        "dialog_ui.py",
        "dom_scripts.py",
        "feedback_ui.py",
        "footer_ui.py",
        "path_picker.py",
        "status_ui.py",
        "table_ui.py",
        "terminal_ui.py",
    },
}

assert {path.name for path in package_dir.glob("*.py")} == {
    "__init__.py",
    "startup_theme.py",
    "streamlit_ui.py",
}
for group, expected_modules in expected_groups.items():
    group_dir = package_dir / group
    assert group_dir.is_dir(), group_dir
    assert {path.name for path in group_dir.glob("*.py")} == {
        "__init__.py",
        *expected_modules,
    }
PY
  assert_success
}

@test "when launching HomeSetup UI then plugin should use the configured Streamlit UI port" {
  assert_file_contains "${HHS_REPO_DIR}/dotfiles/bash/hhsrc.bash" 'HHS_STREAMLIT_UI_PORT:-18501'

  assert_file_contains "${ui_plugin_file}" 'HHS_STREAMLIT_UI_PORT:-18501'

  run grep -q -- '--server.port "${HHS_STREAMLIT_UI_PORT}"' "${ui_plugin_file}"
  assert_success

  run grep -q -- '--server.address 127.0.0.1' "${ui_plugin_file}"
  assert_success

  run grep -q -- '--browser.serverAddress localhost' "${ui_plugin_file}"
  assert_success

  run grep -q -- '--browser.serverPort "${HHS_STREAMLIT_UI_PORT}"' "${ui_plugin_file}"
  assert_success

  assert_file_contains_many "${ui_plugin_file}" \
'STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"' 'STREAMLIT_SERVER_ADDRESS="127.0.0.1"' \
    'STREAMLIT_BROWSER_SERVER_ADDRESS="localhost"' 'STREAMLIT_BROWSER_SERVER_PORT="${HHS_STREAMLIT_UI_PORT}"' \
    'HHS_STREAMLIT_UI_OWNER="${owner_token}"'
  run grep -q -- '--browser.gatherUsageStats false' "${ui_plugin_file}"
  assert_success

  assert_file_contains_many "${HHS_REPO_DIR}/gradle/streamlit.gradle" \
"'--browser.gatherUsageStats'," "'--browser.serverAddress'," "'--browser.serverPort',"
  run grep -A1 "'--browser.gatherUsageStats'," "${HHS_REPO_DIR}/gradle/streamlit.gradle"
  assert_line --partial "'false'"

  assert_file_contains "${HHS_REPO_DIR}/gradle/streamlit.gradle" "STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false'"

  assert_file_contains_many "${ui_plugin_file}" \
'PYTHONPATH="${HHS_HOME}/bin/apps/py:${PYTHONPATH:-}"' \
    'usage: ${APP_NAME} execute ${PLUGIN_NAME} \[command\] \[options\]' \
    '${APP_NAME} execute ${PLUGIN_NAME} restart' 'case "${1:-open}" in' 'restart_ui "$@"' 'ui_port_pids' \
    'HHS_STREAMLIT_UI_RUNTIME_DIR=' 'HHS_CACHE_DIR:-${HHS_DIR}/cache' 'HHS_STREAMLIT_UI_PID_FILE:=' \
    'HHS_STREAMLIT_UI_RUNTIME_DIR}/.streamlit-ui.pid' 'HHS_STREAMLIT_UI_PROCESS_FILE:=' \
    'HHS_STREAMLIT_UI_RUNTIME_DIR}/.streamlit-ui.processes' 'record_ui_process "${pid}" "${owner_token}"'
  assert_file_not_contains_many "${ui_plugin_file}" \
'defunct' "ui_process_tree""_pids"
  assert_file_contains_many "${ui_plugin_file}" \
'is_hhs_ui_pid "${pid}"' 'is_owned_ui_pid "${pid}"' 'is_python_or_streamlit_pid "${pid}"'
  assert_file_not_contains "${ui_plugin_file}" 'def is_python_or_streamlit_pid'

  assert_file_contains_many "${ui_plugin_file}" \
'^function is_python_or_streamlit_pid()' '^function is_hhs_ui_pid()' '^function is_hhs_ui_running()' \
    '^function validate_safe_streamlit_args()' \
    'validate_safe_streamlit_args "$@"' '^function streamlit_theme_args()' 'startup_theme.py' \
    '"${theme_args\[@\]}"'
  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/startup_theme.py"
  assert_success

  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/startup_theme.py" 'def streamlit_theme_args'

  assert_file_contains "${HHS_REPO_DIR}/gradle/streamlit.gradle" 'streamlitStartupThemeArgs()'

  assert_file_not_contains_many "${ui_plugin_file}" \
"launch""ctl" "hhs-ui-""codex" "stop_legacy_ui_""respawner"
  run python3 - "${ui_plugin_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("function start_ui()", 1)[1].split("\n# @purpose:", 1)[0]
command = body.split('nohup python3 -m streamlit run "${STREAMLIT_UI}"', 1)[1].split('pid=$!', 1)[0]
arg_index = command.rindex('"$@"')
assert command.index("--server.address 127.0.0.1") < arg_index
assert command.index('--browser.serverAddress localhost') < arg_index
assert command.index('--server.headless true') < arg_index
assert command.index('--browser.gatherUsageStats false') < arg_index
assert command.index('"${theme_args[@]}"') < arg_index
launch_body = source.split("function launch_ui()", 1)[1].split("\n# @purpose:", 1)[0]
assert "validate_ui_runtime" in launch_body
assert "if is_ui_running; then" in launch_body
PY
  assert_success

  assert_file_contains_many "${ui_plugin_file}" \
'known_pids="$(ui_known_pids)"' '\[\[ "$1" == "execute" \]\] && shift'
}

@test "when starting HomeSetup UI then persisted theme is passed to Streamlit startup" {
  run bash --noprofile --norc -c '
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    mkdir -p "${HHS_DIR}/cache" "${HHS_LOG_DIR}"
    printf "%s\n" "{\"theme_selected\":\"homesetup\"}" > "${HHS_DIR}/cache/streamlit-ui-state.json"
    source "${3}"
    streamlit_theme_args
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial '--theme.base'
  assert_output --partial '--theme.primaryColor'
  assert_output --partial '#2563eb'
  assert_output --partial '--theme.backgroundColor'
  assert_output --partial '#0f172a'
  assert_output --partial '--theme.showWidgetBorder'
  assert_output --partial 'true'
  refute_output --partial '#282a36'

  run bash --noprofile --norc -c '
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/fallback-hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/fallback-log"
    mkdir -p "${HHS_DIR}/cache" "${HHS_LOG_DIR}"
    printf "%s\n" "{\"theme_selected\":\"missing-theme\"}" > "${HHS_DIR}/cache/streamlit-ui-state.json"
    source "${3}"
    streamlit_theme_args
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial '--theme.backgroundColor'
  assert_output --partial '#282a36'
}

@test "when executing UI plugin commands then lifecycle subcommands route explicitly" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { printf "open:%s\n" "$1"; }
    source "${3}"
    function is_ui_running() { [[ "${UI_RUNNING:-0}" == "1" ]]; }
    function start_ui() { printf "start:%s\n" "$*"; }
    function stop_ui() { printf "stop\n"; }
    function status_ui() { printf "status\n"; }
    function launch_ui() { printf "launch:%s\n" "$*"; }
    execute
    execute execute restart --flag
    execute start --flag
    execute status
    execute stop
    execute restart --flag
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_line --index 0 'launch:'
  assert_line --index 1 'stop'
  assert_line --index 2 'launch:--flag'
  assert_line --index 3 'start:--flag'
  assert_line --index 4 'status'
  assert_line --index 5 'stop'
  assert_line --index 6 'stop'
  assert_line --index 7 'launch:--flag'
}

@test "when starting an already running UI then browser is opened without restart" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { printf "open:%s\n" "$1"; }
    source "${3}"
    function is_ui_running() { return 0; }
    function is_managed_ui_running() { return 0; }
    start_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'HomeSetup UI is already running'
  assert_output --partial 'HomeSetup UI is running at http://localhost:28501'
}

@test "when HomeSetup UI is recognizable but unowned then it is opened without adoption" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() { exit "${1:-0}"; }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { printf "open:%s\n" "$1"; }
    source "${3}"
    function validate_ui_runtime() { return 0; }
    function is_ui_running() { return 0; }
    function is_managed_ui_running() { return 1; }
    function is_hhs_ui_running() { return 0; }
    function ui_hhs_port_pid() { printf "45678\n"; }
    start_ui
    launch_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'HomeSetup UI is already running on port 28501 [PID=45678] outside UI plugin ownership.'
  assert_output --partial 'Opening it without adopting it.'
  assert_line --index 1 'HomeSetup UI is running at http://localhost:28501'
  assert_line --index 3 'HomeSetup UI is running at http://localhost:28501'
}

@test "when HomeSetup UI is recognizable but unowned then stop and restart leave it running" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { exit "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      exit "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { return 0; }
    function kill() {
      [[ "$1" == "-0" ]] && return 0
      printf "kill:%s\n" "$*"
    }
    source "${3}"
    function is_ui_running() { return 0; }
    function is_managed_ui_running() { return 1; }
    function is_hhs_ui_running() { return 0; }
    function ui_hhs_port_pid() { printf "45678\n"; }
    function ui_known_pids() { return 0; }
    stop_ui
    restart_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_failure
  assert_output --partial 'outside UI plugin ownership. Leaving it running.'
  assert_output --partial 'outside UI plugin ownership. Cannot restart it safely.'
  refute_output --partial 'kill:'
}

@test "when starting UI with an unmanaged listener then plugin should leave it alone" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { printf "open:%s\n" "$1"; }
    function kill() {
      [[ "$1" == "-0" ]] && return 0
      printf "kill:%s\n" "$*" >&2
      return 0
    }
    printf "%s\n" "12345 old-token" > "${HHS_CACHE_DIR}/.streamlit-ui.processes"
    source "${3}"
    function is_ui_running() { return 0; }
    function ui_port_pids() { printf "99999\n"; }
    function ui_pid_command_name() { printf "Python\n"; }
    function ui_pid_args() {
      printf "python3 -m streamlit run /tmp/other.py --server.port 28501 --server.address 127.0.0.1\n"
    }
    start_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_failure
  assert_output --partial 'Port 28501 is in use by another Streamlit application [PID=99999, process=Python].'
  assert_output --partial 'Cannot start HomeSetup UI.'
  refute_output --partial 'kill:'
  refute_output --partial 'open:'
}

@test "when starting UI then protected Streamlit network options cannot be overridden" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { return 0; }
    source "${3}"
    function is_ui_running() { return 1; }
    start_ui --server.address 0.0.0.0
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_failure
  assert_output --partial 'Protected Streamlit option is managed by HomeSetup UI and cannot be overridden: --server.address'

  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { return 0; }
    source "${3}"
    function is_ui_running() { return 1; }
    start_ui --server.enableCORS=false
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_failure
  assert_output --partial 'Protected Streamlit option is managed by HomeSetup UI and cannot be overridden: --server.enableCORS'

  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { return 0; }
    source "${3}"
    function is_ui_running() { return 1; }
    start_ui --server.enableXsrfProtection=false
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_failure
  assert_output --partial 'Protected Streamlit option is managed by HomeSetup UI and cannot be overridden: --server.enableXsrfProtection'
}

@test "when validating owned UI process then PID must be Python or Streamlit" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { return 0; }
    function kill() {
      [[ "$1" == "-0" ]] && return 0
      return 1
    }
    printf "%s\n" "12345 token-a" > "${HHS_CACHE_DIR}/.streamlit-ui.pid"
    source "${3}"
    function ui_pid_args() {
      printf "python3 -m streamlit run %s --server.port %s --server.address 127.0.0.1\n" "${STREAMLIT_UI}" "${HHS_STREAMLIT_UI_PORT}"
    }
    function ui_pid_env() { printf "HHS_STREAMLIT_UI_OWNER=token-a\n"; }
    function ui_pid_command_name() { printf "node\n"; }
    is_owned_ui_pid 12345 && printf "bad-owned\n" || printf "bad-rejected\n"
    function ui_pid_command_name() { printf "Python\n"; }
    is_owned_ui_pid 12345 && printf "mac-python-owned\n" || printf "mac-python-rejected\n"
    function ui_pid_command_name() { printf "python3\n"; }
    is_owned_ui_pid 12345 && printf "python-owned\n" || printf "python-rejected\n"
    function ui_pid_command_name() { printf "streamlit\n"; }
    is_owned_ui_pid 12345 && printf "streamlit-owned\n" || printf "streamlit-rejected\n"
    rm -f "${HHS_CACHE_DIR}/.streamlit-ui.pid"
    function ui_pid_command_name() { printf "Python\n"; }
    function ui_pid_env() { printf "HHS_STREAMLIT_UI_OWNER=hhs-ui.123.456.789\n"; }
    is_owned_ui_pid 12345 && printf "env-owned\n" || printf "env-rejected\n"
    function ui_pid_env() { return 0; }
    is_hhs_ui_pid 12345 && printf "hhs-recognized\n" || printf "hhs-unrecognized\n"
    is_owned_ui_pid 12345 && printf "untracked-owned\n" || printf "untracked-rejected\n"
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_line --index 0 'bad-rejected'
  assert_line --index 1 'mac-python-owned'
  assert_line --index 2 'python-owned'
  assert_line --index 3 'streamlit-owned'
  assert_line --index 4 'env-owned'
  assert_line --index 5 'hhs-recognized'
  assert_line --index 6 'untracked-rejected'
}

@test "when restarting UI then launch path opens the browser after stop" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { return 0; }
    function __hhs_open() { printf "open:%s\n" "$1"; }
    source "${3}"
    function is_ui_running() { return 1; }
    function stop_ui() { printf "stop\n"; }
    function launch_ui() { printf "launch:%s\n" "$*"; open_ui; }
    restart_ui --flag
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_line --index 0 'stop'
  assert_line --index 1 'launch:--flag'
  assert_output --partial 'HomeSetup UI is running at http://localhost:28501'
}

@test "when stopping UI then recorded plugin process IDs are killed" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_CACHE_DIR="${HHS_DIR}/cache"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { [[ "$1" == "lsof" ]] && return 1; return 0; }
    function __hhs_open() { return 0; }
    killed=""
    function kill() {
      if [[ "$1" == "-0" ]]; then
        [[ " ${killed} " != *" $2 "* ]]
        return
      fi
      printf "kill:%s\n" "$1"
      killed="${killed} $1"
      return 0
    }
    printf "%s\n" "12345 token-a" > "${HHS_CACHE_DIR}/.streamlit-ui.pid"
    printf "%s\n" "12345 token-a" "23456 token-b" > "${HHS_CACHE_DIR}/.streamlit-ui.processes"
    printf "%s\n" "34567 token-c" > "${HHS_DIR}/.streamlit-ui.pid"
    printf "%s\n" "34567 token-c" > "${HHS_DIR}/.streamlit-ui.processes"
    source "${3}"
    function is_ui_running() { return 1; }
    function ui_pids() { return 0; }
    function ui_port_pids() { printf "99999\n"; }
    function is_owned_ui_pid() {
      [[ "$1" =~ ^(12345|23456)$ ]] && [[ " ${killed} " != *" $1 "* ]]
    }
    stop_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'Stopping HomeSetup UI process 12345'
  assert_output --partial 'Stopping HomeSetup UI process 23456'
  assert_output --partial 'kill:12345'
  assert_output --partial 'kill:23456'
  refute_output --partial 'kill:99999'
  [[ ! -e "${BATS_TEST_TMPDIR}/hhs/cache/.streamlit-ui.pid" ]]
  [[ ! -e "${BATS_TEST_TMPDIR}/hhs/cache/.streamlit-ui.processes" ]]
  [[ ! -e "${BATS_TEST_TMPDIR}/hhs/.streamlit-ui.pid" ]]
  [[ ! -e "${BATS_TEST_TMPDIR}/hhs/.streamlit-ui.processes" ]]
}

@test "when stopping UI then an owned port listener is recovered from its environment token" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { [[ "$1" == "lsof" ]] && return 1; return 0; }
    function __hhs_open() { return 0; }
    killed=""
    function kill() {
      if [[ "$1" == "-0" ]]; then
        [[ " ${killed} " != *" $2 "* ]]
        return
      fi
      printf "kill:%s\n" "$1"
      killed="${killed} $1"
      return 0
    }
    source "${3}"
    function is_ui_running() { return 0; }
    function ui_port_pids() { printf "34567\n"; }
    function ui_pid_command_name() { printf "Python\n"; }
    function ui_pid_args() {
      printf "Python -m streamlit run %s --server.port %s --server.address 127.0.0.1\n" \
        "${STREAMLIT_UI}" \
        "${HHS_STREAMLIT_UI_PORT}"
    }
    function ui_pid_env() {
      printf "HHS_STREAMLIT_UI_OWNER=hhs-ui.345.67.89\n"
    }
    stop_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'Stopping HomeSetup UI process 34567'
  assert_output --partial 'kill:34567'
  assert_output --partial 'HomeSetup UI stopped.'
}

@test "when stopping UI with only an unmanaged listener then plugin should not kill it" {
  run bash --noprofile --norc -c '
    export APP_NAME="hhs"
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_LOG_DIR="${2}/log"
    export HHS_STREAMLIT_UI_PORT="28501"
    export BLUE=""
    export GREEN=""
    export NC=""
    export YELLOW=""
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_is_venv() { return 0; }
    function __hhs_has() { [[ "$1" == "lsof" ]] && return 1; return 0; }
    function __hhs_open() { return 0; }
    function kill() {
      [[ "$1" == "-0" ]] && return 0
      printf "kill:%s\n" "$*" >&2
      return 0
    }
    source "${3}"
    function is_ui_running() { return 0; }
    function ui_pids() { printf "88888\n"; }
    function ui_port_pids() { printf "99999\n"; }
    function ui_pid_command_name() { printf "node\n"; }
    function ui_pid_args() { printf "node server.js\n"; }
    stop_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'Port 28501 is in use by another process [PID=99999, process=node]. Leaving it running.'
  refute_output --partial 'kill:'
}


# TC - 6
