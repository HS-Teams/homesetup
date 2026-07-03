#!/usr/bin/env bats

#  Script: hhs-ui.bats
# Purpose: HomeSetup Streamlit UI tests.
# Created: Jun 25, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

export HHS_REPO_DIR="${BATS_TEST_DIRNAME%/tests}"
export HHS_HOME="${HHS_REPO_DIR}"

load test_helper
load_bats_libs

setup() {
  cd "${HHS_REPO_DIR}"
  ui_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/streamlit_ui.py"
  constants_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/constants.py"
  css_file="${HHS_REPO_DIR}/bin/apps/py/hhs_ui/streamlit_ui.css"
  ask_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
  ask_prompt_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md"
  bash_env_file="${HHS_REPO_DIR}/dotfiles/bash/bash_env.bash"
  hhsrc_file="${HHS_REPO_DIR}/dotfiles/bash/hhsrc.bash"
  hspm_plugin_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/hspm.bash"
  ui_plugin_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/ui.bash"
}

# TC - 1
@test "when installing HomeSetup then Streamlit should be included as a Python package" {
  run grep -q "'streamlit'" "${HHS_REPO_DIR}/install.bash"
  assert_success

  run grep -q "'ttyd'" "${HHS_REPO_DIR}/install.bash"
  assert_success
}

# TC - 2
@test "when uninstalling HomeSetup then Streamlit should be included as a removable Python package" {
  run grep -q "'streamlit'" "${HHS_REPO_DIR}/uninstall.bash"
  assert_success

  run grep -q "REQUIRED_PACKAGES=(" "${HHS_REPO_DIR}/uninstall.bash"
  assert_success

  run grep -q "'ttyd'" "${HHS_REPO_DIR}/uninstall.bash"
  assert_success

  run grep -q "uninstall_required_packages" "${HHS_REPO_DIR}/uninstall.bash"
  assert_success
}

@test "when loading shell environment then ttyd should be a default developer tool" {
  run grep -q "'ttyd'" "${bash_env_file}"
  assert_success
}

# TC - 4
@test "when registering plugins then ui plugin should expose required hhs functions" {
  run grep -q '^function help()' "${ui_plugin_file}"
  assert_success

  run grep -q '^function version()' "${ui_plugin_file}"
  assert_success

  run grep -q '^function cleanup()' "${ui_plugin_file}"
  assert_success

  run grep -q '^function execute()' "${ui_plugin_file}"
  assert_success

  run grep -q 'reinstall <package...>' "${hspm_plugin_file}"
  assert_success

  run grep -q 'reinstall_recipe' "${hspm_plugin_file}"
  assert_success
}

# TC - 4
@test "when installing Ollama on Linux then hspm should use the current official installer URL" {
  ollama_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/ollama.recipe"
  ollama_darwin_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/ollama.recipe"

  run grep -q 'https://ollama.com/install.sh' "${ollama_recipe_file}"
  assert_success

  run grep -q 'OllamaInstall.sh' "${ollama_recipe_file}"
  assert_failure

  run grep -q 'systemctl stop ollama' "${ollama_recipe_file}"
  assert_success

  run grep -q "pkill -f 'ollama serve'" "${ollama_recipe_file}"
  assert_success

  run grep -q 'brew services stop ollama' "${ollama_darwin_recipe_file}"
  assert_success
}

# TC - 5
@test "when loading hspm recipes then Bash syntax should be valid" {
  run bash --noprofile --norc -c '
    for recipe in "$1"/bin/apps/bash/hhs-app/plugins/hspm/recipes/*/*.recipe; do
      bash -n "${recipe}" || exit 1
    done
  ' -- "${HHS_REPO_DIR}"
  assert_success
}

# TC - 6
@test "when reviewing hspm recipes then known stale recipe targets should be updated" {
  nvm_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/nvm.recipe"
  vue_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/vue.recipe"
  jenkins_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/jenkins.recipe"

  run grep -q 'https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.5/install.sh' "${nvm_recipe_file}"
  assert_success

  run grep -q 'creationix/nvm' "${nvm_recipe_file}"
  assert_failure

  run grep -q 'npm install -g @vue/cli' "${vue_recipe_file}"
  assert_success

  run grep -q 'openjdk-21-jre' "${jenkins_recipe_file}"
  assert_success

  run grep -q 'jenkins.io-2026.key' "${jenkins_recipe_file}"
  assert_success
}

# TC - 7
@test "when hspm install recipe fails then execute should return failure" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_LOG_DIR="${1}/log"
    export HHS_MY_OS="$(uname -s)"
    export HHS_MY_OS_RELEASE="test"
    export HHS_MY_OS_PACKMAN="test-packman"
    export HHS_DEV_TOOLS=""
    export HHS_HIGHLIGHT_COLOR=""
    export BLUE=""
    export GREEN=""
    export NC=""
    export ORANGE=""
    export RED=""
    export WHITE=""
    export YELLOW=""
    export OLDIFS="${IFS}"
    export PLUGINS_DIR="${1}/plugins"
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}" "${PLUGINS_DIR}/hspm/recipes/${HHS_MY_OS}"
    printf "%s\n" \
      "function _depends_() { return 0; }" \
      "function _install_() { return 22; }" \
      "function _uninstall_() { return 0; }" \
      "function _which_() { return 1; }" \
      > "${PLUGINS_DIR}/hspm/recipes/${HHS_MY_OS}/default.recipe"
    touch "${PLUGINS_DIR}/hspm/catalog.toml"
    function usage() { return "${1:-0}"; }
    function quit() {
      local exit_code="${1:-0}"
      shift || true
      [[ $# -gt 0 ]] && printf "%s\n" "$*"
      return "${exit_code}"
    }
    function __hhs_errcho() {
      shift
      printf "%s\n" "$*" >&2
    }
    source "${2}"
    execute install broken-package
  ' -- "${BATS_TEST_TMPDIR}" "${hspm_plugin_file}"
  assert_failure
  assert_output --partial 'Failed to install "broken-package"'
}

# TC - 4
@test "when loading Streamlit UI source then Python syntax should be valid" {
  run python3 -c 'import ast, pathlib; ast.parse(pathlib.Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())'
  assert_success

  run grep -q '^import os$' "${ui_file}"
  assert_success

  run grep -q '^from pathlib import Path$' "${ui_file}"
  assert_success

  run grep -q '^import sys$' "${ui_file}"
  assert_success

  run grep -q 'sys.path.insert(0, str(Path(__file__).resolve().parents\[1\]))' "${ui_file}"
  assert_success
}

# TC - 5
@test "when launching HomeSetup UI then plugin should use the configured Streamlit UI port" {
  run grep -q 'HHS_STREAMLIT_UI_PORT:-18501' "${HHS_REPO_DIR}/dotfiles/bash/hhsrc.bash"
  assert_success

  run grep -q 'HHS_STREAMLIT_UI_PORT:-18501' "${ui_plugin_file}"
  assert_success

  run grep -q -- '--server.port "${HHS_STREAMLIT_UI_PORT}"' "${ui_plugin_file}"
  assert_success

  run grep -q 'PYTHONPATH="${HHS_HOME}/bin/apps/py:${PYTHONPATH:-}"' "${ui_plugin_file}"
  assert_success

  run grep -q 'usage: ${APP_NAME} execute ${PLUGIN_NAME} \[command\] \[options\]' "${ui_plugin_file}"
  assert_success

  run grep -q '${APP_NAME} execute ${PLUGIN_NAME} restart' "${ui_plugin_file}"
  assert_success

  run grep -q 'case "${1:-open}" in' "${ui_plugin_file}"
  assert_success

  run grep -q 'restart_ui "$@"' "${ui_plugin_file}"
  assert_success

  run grep -q 'ui_port_pids' "${ui_plugin_file}"
  assert_success

  run grep -q '\[\[ "$1" == "execute" \]\] && shift' "${ui_plugin_file}"
  assert_success
}

@test "when executing UI plugin commands then lifecycle subcommands route explicitly" {
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
    function __hhs_open() { printf "open:%s\n" "$1"; }
    source "${3}"
    function is_ui_running() { return 0; }
    start_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'HomeSetup UI is already running'
  assert_output --partial 'HomeSetup UI is running at http://localhost:28501'
}

@test "when restarting UI then launch path opens the browser after stop" {
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
    function __hhs_open() { printf "open:%s\n" "$1"; }
    source "${3}"
    function stop_ui() { printf "stop\n"; }
    function launch_ui() { printf "launch:%s\n" "$*"; open_ui; }
    restart_ui --flag
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_line --index 0 'stop'
  assert_line --index 1 'launch:--flag'
  assert_output --partial 'HomeSetup UI is running at http://localhost:28501'
}

@test "when stopping UI then listener PID on configured port is included" {
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
      if [[ "$1" == "-0" ]]; then
        return 0
      fi
      printf "kill:%s\n" "$1"
      UI_RUNNING="0"
      return 0
    }
    source "${3}"
    function is_ui_running() { [[ "${UI_RUNNING:-1}" == "1" ]]; }
    function ui_pids() { return 0; }
    function ui_port_pids() { printf "12345\n"; }
    stop_ui
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}" "${ui_plugin_file}"
  assert_success
  assert_output --partial 'Stopping HomeSetup UI process 12345'
  assert_output --partial 'kill:12345'
}

# TC - 6
@test "when remote SSH command closes then Streamlit UI should clear stale connection state" {
  run grep -q 'def ssh_shared_connection_closed' "${ui_file}"
  assert_success

  run grep -q 'def strip_ssh_shared_connection_notice' "${ui_file}"
  assert_success

  run grep -q 'def clear_disconnected_ssh_host' "${ui_file}"
  assert_success

  run grep -q 'handle_remote_command_result(remote_host, result)' "${ui_file}"
  assert_success

  run grep -q 'sanitize_remote_command_result(' "${ui_file}"
  assert_success

  run grep -q 'if use_cache and not ssh_shared_connection_closed(result)' "${ui_file}"
  assert_success

  run grep -q 'if remote_host and not ssh_connection_is_alive(remote_host)' "${ui_file}"
  assert_success

  run grep -q 'completed_disconnected_ssh_process(command_to_run, remote_host)' "${ui_file}"
  assert_success

  run grep -q 'st.rerun()' "${ui_file}"
  assert_success

  run grep -q 'ConnectTimeout=5' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_host_selected"\] = local_hostname()' "${ui_file}"
  assert_success
}

@test "when remote commands print HomeSetup startup chatter then command output should be sanitized" {
  run python3 - "${ui_file}" <<'PY'
import re
import subprocess
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def remote_command_startup_line_is_noise(")
end = source.index("def ssh_output_is_only_shared_close(")
namespace = {
    "re": re,
    "subprocess": subprocess,
    "strip_ansi": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

noisy_stdout = (
    "[bash] HomeSetup is starting...\n"
    "\n"
    "[Linux-ubuntu/bash]   Welcome root to HomeSetup v1.9.19 \n"
    "\n"
    "GNU bash, version 5.2.21(1)-release\n"
)
noisy_stderr = "Shell option expand_aliases set to on\nreal error\n"
result = subprocess.CompletedProcess(["cmd"], 0, noisy_stdout, noisy_stderr)
remote = namespace["sanitize_remote_command_result"]("remote-host", result)
assert remote.stdout == "GNU bash, version 5.2.21(1)-release\n"
assert remote.stderr == "real error\n"

local = namespace["sanitize_remote_command_result"]("", result)
assert local.stdout == noisy_stdout
assert local.stderr == noisy_stderr

closed = subprocess.CompletedProcess(
    ["cmd"], 255, "", "Shared connection to 167.99.120.81 closed.\n"
)
sanitized_closed = namespace["sanitize_remote_command_result"]("remote-host", closed)
assert sanitized_closed.stderr == closed.stderr
PY
  assert_success
}

@test "when remote terminal command fails then SSH close trailer should not clear connection" {
  run python3 - "${ui_file}" <<'PY'
import subprocess
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def ssh_shared_connection_closed(")
end = source.index("def ssh_output_is_only_shared_close(")
namespace = {
    "strip_ansi": lambda value: value,
    "subprocess": subprocess,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

command_failure = subprocess.CompletedProcess(
    ["ssh"],
    2,
    "",
    "ls: unrecognized option '--long'\nShared connection to host closed.\n",
)
stale_connection = subprocess.CompletedProcess(
    ["ssh"],
    255,
    "",
    "Shared connection to host closed.\n",
)
assert not namespace["ssh_shared_connection_closed"](command_failure)
assert namespace["ssh_shared_connection_closed"](stale_connection)
assert (
    namespace["strip_ssh_shared_connection_notice"](command_failure.stderr)
    == "ls: unrecognized option '--long'\n"
)
PY
  assert_success
}

@test "when SSH connects from Terminal view then Terminal should be restored" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
start = source.index("def restore_terminal_document_view(")
end = source.index("def close_document_view(")
session_state = {}
activated = []
namespace = {
    "hhs_ui": SimpleNamespace(
        DOCUMENT_VIEW_ACTIVE_KEY="document_view_active",
        DOCUMENT_PREVIOUS_VIEW_KEY="document_previous_view",
        DOCUMENT_SELECTED_KEY="document_selected",
    ),
    "st": SimpleNamespace(session_state=session_state),
    "activate_terminal_document_view": lambda: activated.append(True),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["restore_terminal_document_view"](False)
assert session_state == {}
assert activated == []

namespace["restore_terminal_document_view"](True)
assert session_state["document_view_active"] is True
assert session_state["document_previous_view"] == "Home"
assert session_state["document_selected"] == "TERMINAL"
assert activated == [True]
PY
  assert_success
}

@test "when footer statuses are queued then display timing should start on render" {
  run python3 - "${ui_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

class Clock:
    def __init__(self):
        self.now = 100.0

    def time(self):
        return self.now

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def push_floating_status(")
end = source.index("def floating_status_glyph(")
clock = Clock()
session_state = {}
namespace = {
    "hhs_ui_constants": SimpleNamespace(
        FLOATING_STATUS_QUEUE_KEY="_hhs_floating_status_queue",
        FLOATING_STATUS_LEGACY_KEY="_hhs_floating_status",
        FLOATING_STATUS_QUEUE_LIMIT=20,
    ),
    "clean_command_status_message": lambda value: str(value).strip(),
    "st": SimpleNamespace(session_state=session_state),
    "time": clock,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["push_floating_status"]("First", "success", 5.0)
clock.now = 150.0
namespace["push_floating_status"]("Second", "warning", 5.0)
queue = session_state["_hhs_floating_status_queue"]
assert [item["message"] for item in queue] == ["First", "Second"]
assert "displayed_at" not in queue[0]

status = namespace["current_floating_status"]()
assert status["message"] == "First"
assert status["kind"] == "info"
assert status["displayed_at"] == 150.0

clock.now = 155.5
assert namespace["current_floating_status"]()["message"] == "First"
clock.now = 156.5
assert namespace["current_floating_status"]()["message"] == "Second"
assert session_state["_hhs_floating_status_queue"][0]["displayed_at"] == 156.5
assert namespace["pop_floating_status"]()["message"] == "Second"
assert namespace["pop_floating_status"]() is None
PY
  assert_success
}

# TC - 6
@test "when listing services then HomeSetup UI should be included as a managed service" {
  services_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/services/services.bash"

  run grep -q 'homesetup-ui:running' "${services_file}"
  assert_success

  run grep -q 'homesetup-ui:stopped' "${services_file}"
  assert_success
}

# TC - 7
@test "when styling HomeSetup UI then Dracula theme and Nerd Font should be configured" {
  run test -s "${css_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  run grep -q 'APP_CSS_FILE = APP_DIR / "streamlit_ui.css"' "${constants_file}"
  assert_success

  run grep -q 'APP_FONT_FAMILY = "Droid Sans Mono for Powerline Nerd Font Complete"' "${constants_file}"
  assert_success

  run grep -q -- '--hhs-ui-font-family: "Droid Sans Mono for Powerline Nerd Font Complete", monospace' "${css_file}"
  assert_success

  run grep -q -- '--hhs-theme-background-color: #282a36' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-background: var(--hhs-theme-background-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q 'def css_custom_properties' "${ui_file}"
  assert_success

  run grep -q 'def theme_config_options' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-sidebar-title"' "${ui_file}"
  assert_success

  run grep -q 'def render_sidebar_title' "${ui_file}"
  assert_success

  run grep -q 'render_sidebar_title()' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-sidebar-title-logo"' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-sidebar-clock-glyph"></span>' "${ui_file}"
  assert_success

  run grep -q '.hhs-sidebar-clock-glyph' "${css_file}"
  assert_success

  run grep -q 'flex: 0 0 24px' "${css_file}"
  assert_success

  run grep -q 'justify-content: center' "${css_file}"
  assert_success

  run grep -q 'width: 24px' "${css_file}"
  assert_success

  run grep -q 'margin-right: 0.45rem' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-theme-text-color)' "${css_file}"
  assert_success

  run grep -q 'position: fixed' "${css_file}"
  assert_success

  run grep -q 'top: 58px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-sidebar-inline-inset: 20px' "${css_file}"
  assert_success

  run grep -q 'padding: 0 2rem 0 var(--hhs-sidebar-inline-inset)' "${css_file}"
  assert_success

  run grep -q '.hhs-sidebar-title-logo' "${css_file}"
  assert_success

  run grep -q 'height: 24px' "${css_file}"
  assert_success

  run grep -q 'width: 24px' "${css_file}"
  assert_success

  run grep -q 'margin-right: 0.45rem' "${css_file}"
  assert_success

  run grep -q 'host_kind = "Local" if selected_host_is_local() else "SSH"' "${ui_file}"
  assert_success

  run grep -q 'Host ({host_kind})' "${ui_file}"
  assert_success

  run grep -q 'def select_ssh_host_from_widget' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_host_selector"' "${ui_file}"
  assert_success

  run grep -q 'on_change=select_ssh_host_from_widget' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_host_selected"' "${ui_file}"
  assert_failure

  run grep -q 'ssh_host_connected_display_' "${ui_file}"
  assert_success

  run grep -q 'disabled=True' "${ui_file}"
  assert_success

  run grep -Fq 'options = ["", local_hostname()]' "${ui_file}"
  assert_failure

  run grep -Fq 'options = [local_hostname()]' "${ui_file}"
  assert_success

  run grep -q 'if not selected_host:' "${ui_file}"
  assert_success

  run grep -q 'state_hosts = (' "${ui_file}"
  assert_success

  run grep -q 'registered_ssh_connection_host()' "${ui_file}"
  assert_success

  run grep -q 'def selected_remote_host_requires_connection' "${ui_file}"
  assert_success

  run grep -q 'def render_remote_connection_required_view' "${ui_file}"
  assert_success

  run grep -q 'Connect to the remote host to interact' "${ui_file}"
  assert_success

  run grep -q 'Remote host: {host} -&gt; {host_address}' "${ui_file}"
  assert_success

  run grep -q 'def parse_ssh_config_hostnames' "${ui_file}"
  assert_success

  run grep -q 'def ssh_config_hostname' "${ui_file}"
  assert_success

  run grep -q 'keyword == "hostname"' "${ui_file}"
  assert_success

  run grep -q '<hr />' "${ui_file}"
  assert_success

  run grep -q '.hhs-remote-connect-required h1' "${css_file}"
  assert_success

  run grep -q '.hhs-remote-connect-required hr' "${css_file}"
  assert_success

  run grep -q '.hhs-remote-connect-required h2' "${css_file}"
  assert_success

  run grep -q 'color: #dc2626' "${css_file}"
  assert_success

  run grep -q 'HHS_DIR = Path(os.environ.get("HHS_DIR", str(APP_DIR)))' "${constants_file}"
  assert_success

  run grep -q 'HHS_CACHE_DIR = Path(os.environ.get("HHS_CACHE_DIR", str(HHS_DIR / "cache")))' "${constants_file}"
  assert_success

  run grep -q 'UI_STATE_FILE = HHS_CACHE_DIR / ".streamlit-ui-state"' "${constants_file}"
  assert_success

  run grep -q 'UI_CACHE_FILE = HHS_CACHE_DIR / ".streamlit-ui-cache"' "${constants_file}"
  assert_success

  run grep -q 'UI_CACHE_SSH_CONNECTION_KEY = "ui:ssh_connection"' "${constants_file}"
  assert_success

  run grep -q 'UI_SSH_CONNECTION_FILE' "${constants_file}"
  assert_failure

  run grep -q 'UI_CACHE_REALTIME_TTL_SECONDS = 30' "${constants_file}"
  assert_success

  run grep -q 'UI_CACHE_NORMAL_TTL_SECONDS = 300' "${constants_file}"
  assert_success

  run grep -q 'UI_CACHE_LOW_CHANGE_TTL_SECONDS = 900' "${constants_file}"
  assert_success

  run grep -q 'UI_COMMAND_DEFAULT_TIMEOUT_SECONDS = 60' "${constants_file}"
  assert_success

  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
mutation_wrappers = {
    "run_hhs_process_kill",
    "run_hhs_ask_reset",
    "run_hhs_ask_select_model",
    "run_ollama_delete_model",
    "run_hhs_service_action",
}
seen = set()

for node in ast.walk(tree):
    if not isinstance(node, ast.FunctionDef) or node.name not in mutation_wrappers:
        continue
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Name) or call.func.id != "run_bash_command":
            continue
        use_cache = next((kw.value for kw in call.keywords if kw.arg == "use_cache"), None)
        if not isinstance(use_cache, ast.Constant) or use_cache.value is not False:
            raise SystemExit(f"{node.name} must pass use_cache=False")
        seen.add(node.name)

missing = mutation_wrappers - seen
if missing:
    raise SystemExit("missing mutation wrappers: " + ", ".join(sorted(missing)))
PY
  assert_success

  run grep -q '"ﮣ Connect"' "${ui_file}"
  assert_success

  run grep -q '"ﮤ Disconnect"' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_connect_button"' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_disconnect_button"' "${ui_file}"
  assert_success

  run grep -q 'class="hhs-vspacer"' "${ui_file}"
  assert_failure

  run grep -q 'class="hhs-sidebar-separator"' "${ui_file}"
  assert_success

  run grep -q '.st-key-ssh_connect_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-ssh_disconnect_button button' "${css_file}"
  assert_success

  run grep -q 'background: #16a34a' "${css_file}"
  assert_success

  run grep -q 'background: #dc2626' "${css_file}"
  assert_success

  run grep -q 'color: #ffffff' "${css_file}"
  assert_success

  run grep -q 'min-height: 2.55rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-markdown-table-header: var(--hhs-theme-text-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-markdown-table-value: var(--hhs-theme-primary-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-theme-text-color-accent:' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q 'color: var(--hhs-markdown-table-header)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-markdown-table-value)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-theme-text-color-accent)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-label: var(--hhs-theme-text-color)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-value: var(--hhs-success)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-selected-item-label)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-selected-item-value)' "${css_file}"
  assert_success

  run grep -q -- '--hhs-selected-item-label: var(--hhs-theme-text-color)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-selected-item-value: var(--hhs-success)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success

  run grep -q -- '--hhs-theme-primary-color: var(' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/pastel-powerline.css"
  assert_failure

  run grep -q -- '--hhs-theme-link-color: var(' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/pastel-powerline.css"
  assert_failure

  run grep -Eq -- '--hhs-theme-[^:]+: var\(' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/pastel-powerline.css"
  assert_failure

  run grep -Eq -- '--hhs-theme-[^:]+: var\(' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/jetpack.css"
  assert_failure

  run python3 - <<'PY'
import re
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
base_css = Path("bin/apps/py/hhs_ui/streamlit_ui.css").read_text()
dracula_css = Path("bin/apps/py/hhs_ui/themes/dracula.css").read_text()
homesetup_css = Path("bin/apps/py/hhs_ui/themes/homesetup.css").read_text()
jetpack_css = Path("bin/apps/py/hhs_ui/themes/jetpack.css").read_text()
pastel_powerline_css = Path("bin/apps/py/hhs_ui/themes/pastel-powerline.css").read_text()
tokyo_night_css = Path("bin/apps/py/hhs_ui/themes/tokyo-night.css").read_text()

assert 'class="hhs-footer-logo"' in ui_source
assert 'class="hhs-footer-logo-link"' in ui_source
assert 'hhs-footer-link' in ui_source
assert 'class="hhs-footer-shell-status"' in ui_source
assert 'class="hhs-footer-shell-name">{shell_name}</span>' in ui_source
assert 'href="{shell_version_url}"' in ui_source
assert 'target="_self" title="Show bash version" aria-label="Show bash version"' in ui_source
assert 'os.environ.get("HHS_MY_SHELL", "").strip().upper()' in ui_source
assert 'class="hhs-footer-remote-status"' in ui_source
footer_template = ui_source.split('<footer class="hhs-app-footer">', 1)[1].split('</footer>', 1)[0]
assert 'status_group_markup = (' in ui_source
assert 'f"{remote_status_markup}{shell_status_markup}"' in ui_source
assert "{status_group_markup}" in footer_template
assert "st.html(" in ui_source
assert 'class="hhs-footer-glyph"></span>' in ui_source
assert 'Connected to remote  {connected_host_display}' in ui_source
assert 'os.environ.get("HHS_GITHUB_URL", "#")' in ui_source
homesetup_version_body = ui_source.split("def homesetup_version", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state.get("footer_hhs_version_cache_loaded")' in homesetup_version_body
assert 'run_hhs_envs("^HHS_VERSION$", refresh_cache=refresh_cache)' in homesetup_version_body
assert 'st.session_state["footer_hhs_version_cache_loaded"] = True' in homesetup_version_body
assert 'parse_hhs_envs(result.stdout)' in homesetup_version_body
assert 'hhs_ui.VERSION' not in homesetup_version_body
constants_source = Path("bin/apps/py/hhs_ui/constants.py").read_text()
init_source = Path("bin/apps/py/hhs_ui/__init__.py").read_text()
assert 'FOOTER_OPEN_WORKING_DIR_QUERY_PARAM = "hhs_open_working_dir"' in constants_source
assert 'FOOTER_RUN_UPDATER_QUERY_PARAM = "hhs_run_updater_update"' in constants_source
assert 'FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM = "hhs_show_shell_version"' in constants_source
assert 'FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM' in init_source
assert '"updater_last_check_epoch"' in constants_source
assert '"updater_last_check_output"' in constants_source
assert '"updater_update_available"' in constants_source
assert 'class="hhs-footer-link hhs-footer-repository-link"' in ui_source
assert 'class="hhs-footer-link hhs-footer-working-dir-link"' in ui_source
assert 'class="hhs-footer-working-dir-value"' in ui_source
assert 'href="{working_dir_url}" target="_self">Working dir: <span class="hhs-footer-working-dir-value">' in ui_source
render_footer_body = ui_source.split("def render_footer()", 1)[1].split("\ndef ", 1)[0]
assert 'working_dir = html.escape(footer_working_directory())' in render_footer_body
assert 'os.getcwd()' not in render_footer_body
assert 'class="hhs-footer-version-group"' in ui_source
assert 'class="hhs-footer-spacer"' not in ui_source
assert 'class="hhs-footer-update-link"' in ui_source
assert 'href="{update_url}" target="_self"' in ui_source
assert '' in ui_source
assert 'def build_open_directory_command' in ui_source
assert 'def run_open_working_directory' in ui_source
assert 'def build_footer_working_directory_command' in ui_source
assert 'return r' in ui_source and '__HHS_UI_PWD__' in ui_source and '\\pwd' in ui_source
assert 'def run_footer_working_directory' in ui_source
run_footer_working_directory_body = ui_source.split("def run_footer_working_directory", 1)[1].split("\ndef ", 1)[0]
assert "ttl_seconds=0" in run_footer_working_directory_body
assert "use_cache=False" in run_footer_working_directory_body
assert "force_local=True" not in run_footer_working_directory_body
assert 'cache_tag="system"' in run_footer_working_directory_body
assert '"Loading remote working dir"' in run_footer_working_directory_body
assert "show_overlay=False" not in run_footer_working_directory_body
assert 'def parse_footer_working_directory_output' in ui_source
assert 'def update_remote_footer_working_directory' in ui_source
assert 'def footer_working_directory' in ui_source
footer_working_directory_body = ui_source.split("def footer_working_directory", 1)[1].split("\ndef ", 1)[0]
assert 'run_footer_working_directory()' not in footer_working_directory_body
assert 'hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY' in footer_working_directory_body
assert 'return os.getcwd()' in footer_working_directory_body
assert 'def run_shell_version' in ui_source
assert 'def shell_version_command' in ui_source
assert r"return r'${BASH:-bash} --version'" in ui_source
assert 'shell_version_command()' in ui_source
assert '"Checking shell version..."' in ui_source
run_shell_version_body = ui_source.split("def run_shell_version", 1)[1].split("\ndef ", 1)[0]
assert "force_local=True" not in run_shell_version_body
assert 'def shell_version_output_html' in ui_source
assert 'html.escape(output)' in ui_source
assert 're.sub(r"\\r\\n|\\n|\\r", "<br>", escaped_output)' in ui_source
assert 'def render_footer_shell_version_dialog' in ui_source
assert 'render_footer_shell_version_dialog()' in ui_source
assert 'shell_version_output_html(output or "No output.")' in ui_source
assert 'css_classes="hhs-shell-version-output"' in ui_source
assert 'content_is_html=True' in ui_source
assert 'footer_shell_version_dialog_title' in ui_source
assert 'footer_shell_version_output' in ui_source
assert 'hhs_ui.FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM' in ui_source
assert 'footer_shell_version_dialog_close_button' in ui_source
assert 'def build_hhs_updater_command' in ui_source
assert 'def run_hhs_updater_check' in ui_source
assert 'def run_hhs_updater_update' in ui_source
footer_actions_body = ui_source.split("def handle_footer_actions", 1)[1].split("\ndef ", 1)[0]
assert "clear_footer_shell_version_dialog()" in footer_actions_body
shell_result_index = footer_actions_body.index("result = run_shell_version()")
shell_output_index = footer_actions_body.index('st.session_state["footer_shell_version_output"]')
shell_title_index = footer_actions_body.index('st.session_state["footer_shell_version_dialog_title"] = "Shell version"')
assert shell_result_index < shell_output_index < shell_title_index
assert 'cache_delete_tag("env")' in footer_actions_body
assert 'st.session_state["footer_hhs_version_cache_loaded"] = False' in footer_actions_body
assert 'def cache_delete_command' in ui_source
assert 'cache_delete_command(command, "env")' in ui_source
assert 'def updater_output_has_updates' in ui_source
assert 'def updater_check_due' in ui_source
assert 'def store_updater_check_result' in ui_source
assert 'def execute_due_updater_check' in ui_source
assert 'execute_due_updater_check()' in ui_source
constants_source = Path("bin/apps/py/hhs_ui/constants.py").read_text()
assert "UPDATER_CHECK_INTERVAL_SECONDS = 24 * 60 * 60" in constants_source
store_updater_body = ui_source.split("def store_updater_check_result", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["updater_last_check_epoch"] = time.time()' in store_updater_body
assert 'st.session_state["updater_last_check_output"] = output' in store_updater_body
assert 'result.returncode == 0 and updater_output_has_updates(output)' in store_updater_body
assert 'save_ui_state()' in store_updater_body
assert '__hhs updater execute "{safe_operation}"' in ui_source
assert 'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")";' in ui_source
assert 'printf "y\\\\n" | ' in ui_source
assert 'def handle_footer_actions' in ui_source
assert 'def push_floating_status' in ui_source
assert 'def pop_floating_status' in ui_source
assert 'def current_floating_status' in ui_source
assert 'hhs_ui_constants.FLOATING_STATUS_QUEUE_KEY' in ui_source
assert 'def render_floating_status' in ui_source
assert 'render_floating_status()' in ui_source
assert 'class="hhs-floating-status ' in ui_source
assert 'open "$target"' in ui_source
assert 'xdg-open "$target"' in ui_source
assert 'gio open "$target"' in ui_source
assert 'sensible-browser "$target"' in ui_source
assert 'use_cache=False' in ui_source
assert 'hhs_ui.APP_AI_HOMESETUP_AVATAR_FILE, "image/png"' in ui_source
assert 'class="hhs-footer-glyph"></span>' in ui_source
base_block = re.search(r"\.hhs-footer-glyph\s*\{([^}]*)\}", base_css).group(1)
link_block = re.search(r"\.hhs-footer-link,[^{]+\{([^}]*)\}", base_css).group(1)
logo_link_block = re.search(r"\.hhs-footer-logo-link,[^{]+\{([^}]*)\}", base_css).group(1)
logo_block = re.search(r"\.hhs-footer-logo\s*\{([^}]*)\}", base_css).group(1)
shell_status_block = re.search(r"\.hhs-footer-shell-status,[^{]+\{([^}]*)\}", base_css).group(1)
shell_status_hover_block = re.search(r"\.hhs-footer-shell-status:hover,[^{]+\{([^}]*)\}", base_css).group(1)
shell_name_block = re.search(r"\.hhs-footer-shell-name\s*\{([^}]*)\}", base_css).group(1)
shell_name_hover_block = re.search(r"\.hhs-footer-shell-status:hover \.hhs-footer-shell-name,[^{]+\{([^}]*)\}", base_css).group(1)
remote_status_block = re.search(r"\.hhs-footer-remote-status\s*\{([^}]*)\}", base_css).group(1)
status_group_block = re.search(r"\.hhs-footer-status-group\s*\{([^}]*)\}", base_css).group(1)
block_container_block = re.search(r"\.block-container\s*\{([^}]*)\}", base_css).group(1)
main_block_gap_block = re.search(r"\[data-testid=\"stMainBlockContainer\"\] > \[data-testid=\"stVerticalBlock\"\],[^{]+\{([^}]*)\}", base_css).group(1)
active_view_block = re.search(r"\.st-key-active_view\s*\{([^}]*)\}", base_css).group(1)
sub_view_button_group_block = re.search(r"\.st-key-home_view \[data-baseweb=\"button-group\"\],[^{]+\{([^}]*)\}", base_css).group(1)
expander_block = re.search(r"\[data-testid=\"stExpander\"\]\s*\{([^}]*)\}", base_css).group(1)
docker_expander_block = re.search(r"\.st-key-home_docker_panel \[data-testid=\"stExpander\"\]\s*\{([^}]*)\}", base_css).group(1)
docker_expander_details_block = re.search(r"\.st-key-home_docker_panel \[data-testid=\"stExpanderDetails\"\] > \[data-testid=\"stVerticalBlock\"\]\s*\{([^}]*)\}", base_css).group(1)
hidden_streamlit_block = re.search(r"\[data-testid=\"stMain\"\] \[data-testid=\"stVerticalBlock\"\] > div:empty,[^{]+\{([^}]*)\}", base_css).group(1)
view_key_block = re.search(r"\.st-key-active_view,[^{]+\{([^}]*)\}", base_css).group(1)
active_view_tabs_block = re.search(r"\.st-key-active_view \[role=\"radiogroup\"\]\s*\{([^}]*)\}", base_css).group(1)
streamlit_chrome_block = re.search(r"\[data-testid=\"stHeader\"\],[^{]+\{([^}]*)\}", base_css).group(1)
theme_block = re.search(r"\.hhs-footer-glyph\s*\{([^}]*)\}", dracula_css).group(1)
assert "color: inherit" in link_block
assert "text-decoration: none !important" in link_block
assert "filter: brightness(1.2)" in base_css
assert "filter: none" in logo_link_block
assert "height:" in logo_block
assert "width:" in logo_block
assert ".hhs-footer-shell-status" in base_css
assert ".hhs-footer-remote-status" in base_css
assert ".hhs-footer-status-group" in base_css
assert ".hhs-footer-repository-link:hover" in base_css
assert ".hhs-footer-working-dir-link:hover" in base_css
assert ".hhs-footer-shell-status:hover" in base_css
assert ".hhs-footer-shell-name" in base_css
assert "text-decoration: none !important" in shell_name_block
assert "text-decoration: underline !important" in shell_name_hover_block
assert "text-decoration: underline" not in shell_status_hover_block
assert 'div[role="dialog"]:has(.hhs-shell-version-output)' in base_css
assert ".hhs-shell-version-output" in base_css
assert "max-height: 88dvh" in base_css
assert "max-width: 92vw" in base_css
assert "width: max-content" in base_css
assert '[data-testid="stHorizontalBlock"]:has(.st-key-footer_shell_version_dialog_close_button)' in base_css
assert "justify-content: center" in base_css
assert "margin-top: 1rem" in base_css
assert '[data-testid="stColumn"]:has(.st-key-footer_shell_version_dialog_close_button)' in base_css
assert "flex: 0 0 120px !important" in base_css
assert "width: 120px !important" in base_css
assert "max-height: calc(88dvh - 8rem)" in base_css
assert "max-width: calc(92vw - 4rem)" in base_css
assert ".hhs-footer-working-dir-value" in base_css
assert "color: var(--hhs-secondary)" in base_css
assert "text-decoration: underline !important" in base_css
assert ".hhs-footer-version-group" in base_css
assert "align-items: baseline" in base_css
assert ".hhs-footer-update-link" in base_css
assert "top: -0.42em" in base_css
assert ".hhs-floating-status" in base_css
assert "hhs-floating-status-hide" in base_css
assert ".hhs-floating-status-kind-info" in base_css
assert ".hhs-floating-status-kind-warn" in base_css
assert ".hhs-floating-status-kind-error" in base_css
assert "var(--hhs-theme-footer-status-info-color)" in base_css
assert "var(--hhs-theme-footer-status-warn-color)" in base_css
assert "var(--hhs-theme-footer-status-error-color)" in base_css
assert "font-size: var(--hhs-theme-footer-status-text-size)" in base_css
assert "--hhs-streamlit-toolbar-guard-width: 8rem" in base_css
assert "--hhs-ttyd-max-height: 760px" in base_css
assert "--hhs-view-gap: 0.95rem" in base_css
assert "--hhs-view-section-gap: 0.8rem" in base_css
assert "padding-top: 0 !important" in block_container_block
assert '[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]' in base_css
assert ".block-container > [data-testid=\"stVerticalBlock\"]" in base_css
assert "gap: 0 !important" in main_block_gap_block
assert "row-gap: 0 !important" in main_block_gap_block
assert "margin-bottom: var(--hhs-view-gap) !important" in active_view_block
assert "margin: 0 0 var(--hhs-view-gap) !important" in sub_view_button_group_block
assert "margin: var(--hhs-view-section-gap) 0" in expander_block
assert "margin: 0 0 var(--hhs-element-std-gap)" in docker_expander_block
assert "gap: 0 !important" in docker_expander_details_block
assert "row-gap: 0 !important" in docker_expander_details_block
assert "display: none !important" in hidden_streamlit_block
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has([data-testid="stDataFrame"])' in base_css
assert "margin-top: 0.35rem !important" in base_css
assert '[data-testid="stMain"] [data-testid="stMarkdownContainer"] h5' in base_css
assert "margin: var(--hhs-view-section-gap) 0 0.55rem !important" in base_css
assert '[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.hhs-inline-form-label)' in base_css
assert "margin-bottom: var(--hhs-view-section-gap)" in base_css
assert '.st-key-home_docker_panel [data-testid="stVerticalBlock"] > div:has([data-testid="stDataFrame"])' in base_css
assert '.st-key-home_docker_panel [data-testid="stElementContainer"][style*="height: 0px"]' in base_css
assert '.st-key-home_docker_panel [data-testid="stElementContainer"][style*="width:0px"]' in base_css
assert ".st-key-home_view" in base_css
assert ".st-key-config_view" in base_css
assert ".st-key-history_view" in base_css
assert ".st-key-monitor_view" in base_css
assert ".st-key-ai_view" in base_css
assert "margin-top: 0 !important" in view_key_block
assert "padding-top: 0 !important" in view_key_block
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-active_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-home_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ai_view)' in base_css
assert '.st-key-home_view [data-baseweb="button-group"]' in base_css
assert "padding-right: var(--hhs-streamlit-toolbar-guard-width)" in active_view_tabs_block
assert '[data-testid="stToolbar"]' in base_css
assert '[data-testid="stDecoration"]' in base_css
assert '[data-testid="stStatusWidget"]' in base_css
assert "#MainMenu" in base_css
assert "display: none !important" in streamlit_chrome_block
assert "height: 0 !important" in streamlit_chrome_block
assert "visibility: hidden !important" in streamlit_chrome_block
assert "border-top: 1px solid var(--hhs-floating-status-color)" in base_css
assert "border-bottom: 1px solid" in base_css
assert "border-top: 2px solid var(--hhs-comment)" in dracula_css
assert "justify-content: center" in base_css
assert "text-align: center" in base_css
assert "--hhs-footer-guard-height: 3.5rem" in base_css
assert "bottom: 3.25rem" in base_css
assert "font-size: 0.84rem" in base_css
assert "min-height: 3.25rem" in base_css
assert "height: 32px" in base_css
assert "background: rgba(15, 23, 42, 0.66)" in homesetup_css
assert "background: rgba(25, 24, 31, 0.82)" in jetpack_css
assert "background: rgba(20, 17, 31, 0.82)" in pastel_powerline_css
assert "left: 0" in base_css
assert "right: 0" in base_css
assert "min-height: 1.85em" in base_css
assert "padding: 0.32em 2rem 0.32em var(--hhs-sidebar-inline-inset)" in base_css
assert "--hhs-floating-status-timeout: 5s" in base_css
assert "animation-delay: var(--hhs-floating-status-timeout, 5s)" in base_css
assert "font-family: var(--hhs-ui-font-family)" in base_css
assert "var(--hhs-font-family)" not in base_css
main_body = ui_source.split("def main()", 1)[1].split('if __name__ == "__main__"', 1)[0]
assert main_body.index("render_footer()") < main_body.index("render_floating_status()")
assert "color: var(--hhs-warning)" in base_css
assert ".hhs-footer-spacer" not in base_css
assert "gap: 0.8rem" in base_css
assert "margin-left: auto" in status_group_block
assert "gap: 1.25rem" in status_group_block
assert "gap: 0.8rem" in shell_status_block
assert "gap: 0.8rem" in remote_status_block
assert "margin-left" not in shell_status_block
assert "margin-left" not in remote_status_block
assert "border-bottom" not in base_block
assert "border-bottom" not in theme_block
assert "color: var(--hhs-primary)" in theme_block
assert ".hhs-footer-remote-status" in dracula_css
assert "--hhs-theme-footer-status-info-color" in dracula_css
assert "--hhs-theme-footer-status-warn-color" in dracula_css
assert "--hhs-theme-footer-status-error-color" in dracula_css
assert "--hhs-theme-footer-status-text-size" in dracula_css
assert "--hhs-theme-footer-status-text-size: 1.176rem" in dracula_css
assert "--hhs-theme-footer-status-info-color" in homesetup_css
assert "--hhs-theme-footer-status-warn-color" in homesetup_css
assert "--hhs-theme-footer-status-error-color" in homesetup_css
assert "--hhs-theme-footer-status-text-size" in homesetup_css
assert "--hhs-theme-footer-status-text-size: 1.176rem" in homesetup_css
assert "--hhs-theme-footer-status-info-color" in tokyo_night_css
assert "--hhs-theme-footer-status-warn-color" in tokyo_night_css
assert "--hhs-theme-footer-status-error-color" in tokyo_night_css
assert "--hhs-theme-footer-status-text-size" in tokyo_night_css
assert "--hhs-theme-footer-status-text-size: 1.176rem" in tokyo_night_css
assert '.stButtonGroup [data-baseweb="button-group"] button[aria-checked="true"]' in dracula_css
assert "border-color: var(--hhs-primary)" in dracula_css
assert "--hhs-theme-heading-border-color: var(--hhs-theme-border-color)" in dracula_css
assert "--hhs-theme-heading-border-color: var(--hhs-theme-border-color)" in tokyo_night_css
PY
  assert_success

  run grep -q '<style>' "${css_file}"
  assert_failure
}

# TC - 8
@test "when selecting a UI theme then the selected theme should persist and restore" {
  run python3 - <<'PY'
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

app_dir = Path("bin/apps/py/hhs_ui").resolve()
sys.path.insert(0, str(app_dir))

streamlit = types.ModuleType("streamlit")
streamlit.session_state = {}
config_options = {}
streamlit.config = types.SimpleNamespace(
    set_option=lambda key, value: config_options.__setitem__(key, value)
)
streamlit.fragment = lambda **_kwargs: (lambda func: func)
sys.modules["streamlit"] = streamlit

components = types.ModuleType("streamlit.components")
components_v1 = types.ModuleType("streamlit.components.v1")
components.v1 = components_v1
sys.modules["streamlit.components"] = components
sys.modules["streamlit.components.v1"] = components_v1
sys.modules["altair"] = types.ModuleType("altair")
sys.modules["pandas"] = types.ModuleType("pandas")

spec = importlib.util.spec_from_file_location("streamlit_ui_under_test", app_dir / "streamlit_ui.py")
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "dracula.css").write_text("""
:root {
  --hhs-theme-base: dark;
  --hhs-theme-background-color: #282a36;
  --hhs-theme-primary-color: #bd93f9;
  --hhs-theme-text-color: #f8f8f2;
  --hhs-theme-code-background-color: #21222c;
  --hhs-theme-show-widget-border: true;
}
dracula-css
""", encoding="utf-8")
    (themes_dir / "homesetup.css").write_text("""
:root {
  --hhs-theme-base: dark;
  --hhs-theme-background-color: #07111f;
  --hhs-theme-primary-color: #3b82f6;
  --hhs-theme-text-color: #dbeafe;
  --hhs-theme-code-background-color: #0b1628;
  --hhs-theme-show-widget-border: true;
}
homesetup-css
""", encoding="utf-8")
    (themes_dir / "tokyo-night.css").write_text("""
:root {
  --hhs-theme-base: dark;
  --hhs-theme-background-color: #1a1b26;
  --hhs-theme-primary-color: #bb9af7;
  --hhs-theme-text-color: #c0caf5;
  --hhs-theme-code-background-color: #16161e;
  --hhs-theme-show-widget-border: true;
}
tokyo-night-css
""", encoding="utf-8")
    ui.hhs_ui.APP_THEME_CSS_FILE = themes_dir / "dracula.css"
    ui.hhs_ui.UI_STATE_FILE = tmp_path / "hhs-dir" / ".streamlit-ui-state"

    ui.persist_theme_selection("tokyo-night")
    assert json.loads(ui.hhs_ui.UI_STATE_FILE.read_text(encoding="utf-8"))["theme_selected"] == "tokyo-night"

    streamlit.session_state.clear()
    streamlit.session_state["active_view"] = "Home"
    streamlit.session_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] = True
    streamlit.session_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] = "TERMINAL"
    streamlit.session_state[ui.hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] = "Home"
    streamlit.session_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] = "homeserver"
    ui.save_ui_state()
    saved_state = json.loads(ui.hhs_ui.UI_STATE_FILE.read_text(encoding="utf-8"))
    assert saved_state["theme_selected"] == "tokyo-night"
    assert saved_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] is True
    assert saved_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] == "TERMINAL"
    assert saved_state[ui.hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] == "Home"
    assert saved_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] == "homeserver"

    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
    assert streamlit.session_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] is True
    assert streamlit.session_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] == "TERMINAL"
    assert streamlit.session_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] == "homeserver"
    assert "tokyo-night-css" in ui.load_app_theme_css()

    config_options.clear()
    ui.configure_app_font_theme(ui.persisted_theme_name())
    assert config_options["theme.backgroundColor"] == "#1a1b26"
    assert config_options["theme.showWidgetBorder"] is True

    theme_options = ui.theme_config_options("tokyo-night")
    assert theme_options["theme.backgroundColor"] == "#1a1b26"
    assert theme_options["theme.primaryColor"] == "#bb9af7"
    assert theme_options["theme.textColor"] == "#c0caf5"

    homesetup_options = ui.theme_config_options("homesetup")
    assert homesetup_options["theme.backgroundColor"] == "#07111f"
    assert homesetup_options["theme.codeBackgroundColor"] == "#0b1628"

    app_state_file = tmp_path / ".streamlit-ui-state"
    app_state_file.write_text('{"theme_selected": "dracula"}', encoding="utf-8")
    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
PY
  assert_success
}

# TC - 9
@test "when rendering the main UI then current navigation tabs should be registered" {
  run grep -q 'VIEWS = ("Home", "Configs", "Services", "Monitor", "History")' "${constants_file}"
  assert_success

  run grep -q 'AI_VIEW = "AI"' "${constants_file}"
  assert_success

  run grep -q 'SSH_VIEW = "SSH"' "${constants_file}"
  assert_success

  run grep -q 'SSH_RECONNECT_HOST_KEY = "ssh_reconnect_host"' "${constants_file}"
  assert_success

  run grep -q 'SSH_RECONNECT_HOST_KEY,' "${constants_file}"
  assert_success

  run grep -q 'def parse_ssh_config_ports' "${ui_file}"
  assert_success

  run grep -q 'def ssh_config_port' "${ui_file}"
  assert_success

  run grep -q 'def ssh_connection_display' "${ui_file}"
  assert_success

  run grep -q 'return f"{ssh_config_hostname(clean_host)}:{ssh_config_port(clean_host)}"' "${ui_file}"
  assert_success

  run grep -q 'import importlib' "${ui_file}"
  assert_success

  run grep -q 'import hhs_ui.constants as hhs_ui_constants' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui_constants = importlib.reload(hhs_ui_constants)' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui = importlib.reload(hhs_ui)' "${ui_file}"
  assert_success

  run grep -q '"Home": " System"' "${constants_file}"
  assert_success

  run grep -q '"Configs": " Configs"' "${constants_file}"
  assert_success

  run grep -q '"Services": " Services"' "${constants_file}"
  assert_success

  run grep -q '"Monitor": " Monitor"' "${constants_file}"
  assert_success

  run grep -q '"History": " History"' "${constants_file}"
  assert_success

  run grep -q 'SSH_VIEW: " SSH"' "${constants_file}"
  assert_success

  run grep -q 'AI_VIEW: " AI"' "${constants_file}"
  assert_success

  run grep -q '<h2> System</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> Dotfiles Configurations</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> System Services</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> Activity Monitor</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> History</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> SSH</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> Ask Ollama HomeSetup AI</h2>' "${ui_file}"
  assert_success

  run grep -q 'AI_VIEWS = ("CHAT", "CONTEXT", "SETTINGS")' "${constants_file}"
  assert_success

  run grep -q '"CHAT": " Chat"' "${constants_file}"
  assert_success

  run grep -q '"CONTEXT": " Context"' "${constants_file}"
  assert_success

  run grep -q '"SETTINGS": " Settings"' "${constants_file}"
  assert_success

  run grep -q 'def ai_view_label' "${ui_file}"
  assert_success

  run grep -q 'format_func=ai_view_label' "${ui_file}"
  assert_success

  run grep -q 'HOME_VIEWS = ("System", "Docker", "Tools", "SHOPTS")' "${constants_file}"
  assert_success

  run grep -q '"System": " Summary"' "${constants_file}"
  assert_success

  run grep -q '"Docker": " Docker"' "${constants_file}"
  assert_success

  run grep -q '"Tools": " Tools"' "${constants_file}"
  assert_success

  run grep -q '"SHOPTS": " Shell Options"' "${constants_file}"
  assert_success

  run grep -q 'def home_view_label' "${ui_file}"
  assert_success

  run grep -q 'format_func=home_view_label' "${ui_file}"
  assert_success

  run grep -q 'elif home_view == "Docker"' "${ui_file}"
  assert_success

  run grep -q 'render_home_docker_panel()' "${ui_file}"
  assert_success

  run grep -q 'def render_home_docker_panel' "${ui_file}"
  assert_success

  run grep -q 'with st.container(key="home_docker_panel")' "${ui_file}"
  assert_success

  run grep -q 'def render_docker_agent_required_view' "${ui_file}"
  assert_success

  run grep -q 'def docker_agent_is_running' "${ui_file}"
  assert_success

  run grep -q 'def build_docker_agent_check_command' "${ui_file}"
  assert_success

  run grep -q 'Docker agent is not running' "${ui_file}"
  assert_success

  run grep -q 'if not docker_agent_is_running()' "${ui_file}"
  assert_success

  run grep -q ' Docker Containers' "${ui_file}"
  assert_failure

  run grep -q 'def run_docker_ps' "${ui_file}"
  assert_success

  run grep -q 'def run_docker_images' "${ui_file}"
  assert_success

  run grep -q 'with st.expander("All Containers", expanded=True)' "${ui_file}"
  assert_success

  run grep -q 'with st.expander("Available Images", expanded=True)' "${ui_file}"
  assert_success

  run grep -q 'def render_docker_command_table' "${ui_file}"
  assert_success

  run grep -q 'render_docker_container_table(run_docker_ps())' "${ui_file}"
  assert_success

  run grep -q 'render_docker_image_table(run_docker_images())' "${ui_file}"
  assert_success

  run grep -q 'docker_container_table_key(),' "${ui_file}"
  assert_success

  run grep -q 'docker_image_table_key(),' "${ui_file}"
  assert_success

  run grep -q '"label": "Start"' "${ui_file}"
  assert_success

  run grep -q '"label": "Stop"' "${ui_file}"
  assert_success

  run grep -q '"label": "Remove"' "${ui_file}"
  assert_success

  run grep -q '"label": "Delete"' "${ui_file}"
  assert_success

  run grep -F -q '["CONTAINER ID", "IMAGE", "NAMES", "STATUS", "CREATED AT"]' "${ui_file}"
  assert_success

  run grep -F -q '["IMAGE ID", "REPOSITORY", "TAG", "SIZE", "CREATED AT"]' "${ui_file}"
  assert_success

  run grep -q 'def docker_container_is_up' "${ui_file}"
  assert_success

  run grep -q '"disabled": lambda row, _index: docker_container_is_up(row)' "${ui_file}"
  assert_success

  run grep -q '"disabled": lambda row, _index: not docker_container_is_up(row)' "${ui_file}"
  assert_success

  run grep -q 'build_docker_container_action_command' "${ui_file}"
  assert_success

  run grep -q 'build_docker_image_delete_command' "${ui_file}"
  assert_success

  run grep -q 'docker image rm -f' "${ui_file}"
  assert_success

  run grep -q 'docker ps -a --format' "${ui_file}"
  assert_success

  run grep -q 'docker images --format' "${ui_file}"
  assert_success

  run grep -F -q '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}' "${ui_file}"
  assert_success

  run grep -q 'return "docker info >/dev/null 2>&1"' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
for function_name in ("run_docker_ps", "run_docker_images"):
    body = source.split(f"def {function_name}", 1)[1].split("\ndef ", 1)[0]
    assert "use_cache=False" not in body, function_name
agent_body = source.split("def docker_agent_is_running", 1)[1].split("\ndef ", 1)[0]
assert "use_cache=False" not in agent_body
assert "timeout_seconds=2" in agent_body
assert "show_overlay=False" in agent_body
docker_body = source.split("def render_home_docker_panel", 1)[1].split("\ndef ", 1)[0]
required_index = docker_body.index("render_docker_agent_required_view()")
containers_index = docker_body.index('st.expander("All Containers"')
assert required_index < containers_index
PY
  assert_success

  run grep -q 'DOCKER_CONTAINER_TABLE_KEY = "docker_container_table"' "${constants_file}"
  assert_success

  run grep -q 'DOCKER_IMAGE_TABLE_KEY = "docker_image_table"' "${constants_file}"
  assert_success

  run grep -q 'hhs_ui.DOCKER_CONTAINER_TABLE_KEY' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.DOCKER_IMAGE_TABLE_KEY' "${ui_file}"
  assert_success

  run grep -q '"home_tools_filter"' "${constants_file}"
  assert_success

  run grep -q '"home_tools_other_filter"' "${constants_file}"
  assert_success

  run grep -q 'def filter_tool_rows' "${ui_file}"
  assert_success

  run grep -q '"home_tools_filter"' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.LIST_FILTERS' "${ui_file}"
  assert_success

  run grep -q '"home_tools_other_filter"' "${ui_file}"
  assert_success

  run grep -q 'SHOPTS_FILTERS = ("All", "ON", "OFF", "Other")' "${constants_file}"
  assert_success

  run grep -q 'SHOPTS_FILTERS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'SHOPT_LINE_PATTERN' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q '"home_shopts_filter"' "${constants_file}"
  assert_success

  run grep -q '"home_shopts_other_filter"' "${constants_file}"
  assert_success

  run grep -q 'def render_home_shopts_panel' "${ui_file}"
  assert_success

  run grep -q 'elif home_view == "SHOPTS"' "${ui_file}"
  assert_success

  run grep -q 'render_home_shopts_panel()' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.SHOPTS_FILTERS' "${ui_file}"
  assert_success

  run grep -q '"home_shopts_filter"' "${ui_file}"
  assert_success

  run grep -q '"home_shopts_other_filter"' "${ui_file}"
  assert_success

  run grep -q 'TABLE_CONTROLS_PANEL_TITLE = "Filters & Controls"' "${constants_file}"
  assert_success

  run grep -q 'TABLE_CONTROLS_PANEL_TITLE' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'def render_table_controls_panel' "${ui_file}"
  assert_success

  run grep -q 'st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True)' "${ui_file}"
  assert_success

  run grep -q 'def render_table_filter_controls' "${ui_file}"
  assert_success

  run grep -q 'def clear_table_other_filter' "${ui_file}"
  assert_success

  run grep -q 'key=f"{other_key}_clear"' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q 'on_click=clear_table_other_filter' "${ui_file}"
  assert_success

  run grep -q 'def render_env_add_controls' "${ui_file}"
  assert_success

  run grep -q '\[data-testid="stExpander"\]' "${css_file}"
  assert_success

  run grep -q 'border-color: var(--hhs-theme-border-color)' "${css_file}"
  assert_success

  run grep -q 'TWO_OPTION_FILTER_COLUMNS = \[0.75, 3.25\]' "${constants_file}"
  assert_success

  run grep -q 'THREE_OPTION_FILTER_COLUMNS = \[1.1, 2.9\]' "${constants_file}"
  assert_success

  run grep -q 'FOUR_OPTION_FILTER_COLUMNS = \[1.75, 2.25\]' "${constants_file}"
  assert_success

  run grep -q 'PATH_FILTER_COLUMNS = \[2.25, 1.75\]' "${constants_file}"
  assert_success

  run grep -q -- '--hhs-element-std-gap: 1rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-filter-control-gap' "${css_file}"
  assert_failure

  run grep -q -- '--hhs-inline-control-gap' "${css_file}"
  assert_failure

  run grep -q 'gap: var(--hhs-element-std-gap)' "${css_file}"
  assert_success

  run grep -q 'gap: var(--hhs-element-std-gap) !important' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stHorizontalBlock"\]:has(.st-key-env_other_filter)' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stHorizontalBlock"\]:has(.st-key-home_shopts_other_filter)' "${css_file}"
  assert_success

  run grep -q '.st-key-home_shopts_other_filter input' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stColumn"\]:first-child' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stColumn"\]:last-child' "${css_file}"
  assert_success

  run grep -q 'flex: 0 0 auto !important' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stColumn"\]:nth-child(2)' "${css_file}"
  assert_success

  run grep -q 'flex: 1 1 auto !important' "${css_file}"
  assert_success

  run grep -q 'flex: 0 0 2.1rem !important' "${css_file}"
  assert_success

  run grep -q 'align-self: center !important' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="_other_filter_clear"\] button' "${css_file}"
  assert_success

  run grep -q 'height: 2rem' "${css_file}"
  assert_success

  run grep -q 'max-width: none' "${css_file}"
  assert_success

  run grep -q 'width: 100%' "${css_file}"
  assert_success

  run grep -q 'hhs_ui.THREE_OPTION_FILTER_COLUMNS' "${ui_file}"
  assert_success

  run grep -q 'HOME_TOOLS_TABLE_KEY = "home_tools_table"' "${constants_file}"
  assert_success

  run grep -q 'HOME_TOOLS_TABLE_KEY' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'HOME_TOOLS_TABLE_RESET_COUNTER_KEY = "home_tools_table_reset_counter"' "${constants_file}"
  assert_success

  run grep -q 'HOME_TOOLS_TABLE_RESET_COUNTER_KEY' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'HOME_SHOPTS_TABLE_KEY = "home_shopts_table"' "${constants_file}"
  assert_success

  run grep -q 'HOME_SHOPTS_TABLE_RESET_COUNTER_KEY = "home_shopts_table_reset_counter"' "${constants_file}"
  assert_success

  run grep -q 'def home_tools_table_key' "${ui_file}"
  assert_success

  run grep -q 'def reset_home_tools_table_selection' "${ui_file}"
  assert_success

  run grep -q 'key=home_tools_table_key()' "${ui_file}"
  assert_success

  run grep -q 'reset_home_tools_table_selection()' "${ui_file}"
  assert_success

  run grep -q 'def home_shopts_table_key' "${ui_file}"
  assert_success

  run grep -q 'def reset_home_shopts_table_selection' "${ui_file}"
  assert_success

  run grep -q 'key=home_shopts_table_key()' "${ui_file}"
  assert_success

  run grep -q 'reset_home_shopts_table_selection()' "${ui_file}"
  assert_success

  run grep -q 'if connected_ssh_host():' "${ui_file}"
  assert_success

  run grep -q 'views = (\*views, hhs_ui.SSH_VIEW)' "${ui_file}"
  assert_success

  run grep -q 'elif active_view == hhs_ui.SSH_VIEW:' "${ui_file}"
  assert_success

  run grep -q 'render_ssh_view()' "${ui_file}"
  assert_success

  run grep -q 'SSH_TUNNEL_TABLE_KEY = "ssh_tunnel_table"' "${constants_file}"
  assert_success

  run grep -q 'def main_view_label' "${ui_file}"
  assert_success

  run grep -q 'format_func=main_view_label' "${ui_file}"
  assert_success

  run grep -q 'format_func=str.upper' "${ui_file}"
  assert_failure

  run grep -q 'checkbox=True' "${ui_file}"
  assert_success

  run grep -q 'selected_label=lambda row, _index: f"Selected: {row.get('"'"'Tool'"'"', '"'"''"'"')}"' "${ui_file}"
  assert_success

  run grep -q 'def render_selected_table_item' "${ui_file}"
  assert_success

  run grep -q 'def table_component_key' "${ui_file}"
  assert_success

  run grep -q 'table_empty_hint' "${ui_file}"
  assert_success

  run grep -q 'table_selected_panel_' "${ui_file}"
  assert_success

  run grep -q 'table_actions_' "${ui_file}"
  assert_success

  run grep -q 'selected_editable: bool | Callable' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q '"ﰸ"' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q 'help="Edit"' "${ui_file}"
  assert_success

  run grep -q 'args=(editing_key, edit_key, edit_value)' "${ui_file}"
  assert_success

  run grep -q 'gap="small"' "${ui_file}"
  assert_success

  run grep -q 'st.text_input(' "${ui_file}"
  assert_success

  run grep -q 'f"{value}:"' "${ui_file}"
  assert_success

  run grep -q 'def render_selected_table_actions' "${ui_file}"
  assert_success

  run grep -q 'selected_action_buttons: list' "${ui_file}"
  assert_success

  run grep -q 'selected_actions=visible_selected_actions' "${ui_file}"
  assert_success

  run grep -q 'help="Cancel edit"' "${ui_file}"
  assert_success

  run grep -q 'def cancel_selected_item_edit' "${ui_file}"
  assert_success

  run grep -q 'reset_selection: Callable\[\[\], None\] | None = None' "${ui_file}"
  assert_success

  run grep -q 'args=(editing_key, edit_key, reset_selection)' "${ui_file}"
  assert_success

  run grep -q 'def execute_selected_table_action' "${ui_file}"
  assert_success

  run grep -q 'callback(\*callback_args)' "${ui_file}"
  assert_success

  run grep -q 'reset_selection=reset_env_table_selection' "${ui_file}"
  assert_success

  run grep -q 'reset_selection=reset_path_table_selection' "${ui_file}"
  assert_success

  run grep -q 'reset_selection=reset_dir_table_selection' "${ui_file}"
  assert_success

  run grep -q 'reset_selection=reset_cmd_table_selection' "${ui_file}"
  assert_success

  run grep -q 'reset_selection=reset_alias_table_selection' "${ui_file}"
  assert_success

  run grep -q 'reset_selection=reset_ai_model_table_selection' "${ui_file}"
  assert_success

  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
for function_name in (
    "apply_selected_env_editor_value",
    "apply_selected_path_editor_value",
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

  run grep -q 'div\[class\*="_selected_editing_"\] button' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="_table_empty_hint"\]' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="_table_selected_panel_"\]' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="_table_actions_"\]' "${css_file}"
  assert_success

  run grep -q 'margin-top: var(--hhs-view-section-gap) !important' "${css_file}"
  assert_success

  run grep -q 'gap: var(--hhs-element-std-gap) !important' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="st-key-env_delete_button_"\]\[class\*="_selected"\] button' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="st-key-path_delete_button_"\]\[class\*="_selected"\] button' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="st-key-dir_delete_button_"\]\[class\*="_selected"\] button' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="st-key-cmd_delete_button_"\]\[class\*="_selected"\] button' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="st-key-alias_delete_button_"\]\[class\*="_selected"\] button' "${css_file}"
  assert_success

  run grep -q 'div\[class\*="st-key-ai_delete_model_button_"\]\[class\*="_selected"\] button' "${css_file}"
  assert_success

  run grep -q 'width: 2rem' "${css_file}"
  assert_success

  run grep -q '.st-key-env_add_submit' "${css_file}"
  assert_success

  run grep -q '.st-key-path_add_submit' "${css_file}"
  assert_success

  run grep -q '.st-key-path_folder_picker_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-dir_add_submit' "${css_file}"
  assert_success

  run grep -q '.st-key-dir_folder_picker_button button' "${css_file}"
  assert_success

  run grep -q 'margin-top: 1.55rem' "${css_file}"
  assert_success

  run grep -q '\[1.25, 4.05, 0.012, 0.15\], vertical_alignment="center"' "${ui_file}"
  assert_success

  run grep -q '.st-key-cmd_add_submit' "${css_file}"
  assert_success

  run grep -q '.st-key-alias_add_submit' "${css_file}"
  assert_success

  run grep -q 'display: none' "${css_file}"
  assert_success

  run grep -q '.st-key-env_add_button' "${css_file}"
  assert_failure

  run grep -q 'color: var(--hhs-danger) !important' "${css_file}"
  assert_success

  run grep -q '\[data-testid="stTextInput"\]' "${css_file}"
  assert_success

  run grep -q 'grid-template-columns: max-content minmax(0, 1fr)' "${css_file}"
  assert_success

  run grep -q 'white-space: nowrap' "${css_file}"
  assert_success

  run grep -q 'hhs-selected-item-line' "${ui_file}"
  assert_success

  run grep -q 'display: inline-flex' "${css_file}"
  assert_success

  run grep -q 'def build_hhs_hspm_command' "${ui_file}"
  assert_success

  run grep -q 'def home_tool_is_installed' "${ui_file}"
  assert_success

  run grep -q 'def home_tool_is_not_found' "${ui_file}"
  assert_success

  run grep -q '__hhs hspm execute' "${ui_file}"
  assert_success

  run grep -q '"install", "uninstall", "reinstall"' "${ui_file}"
  assert_success

  run grep -q 'def build_tool_tldr_command' "${ui_file}"
  assert_success

  run grep -q 'tldr {shlex.quote(tool_name.strip())}' "${ui_file}"
  assert_success

  run grep -q 'def apply_selected_tool_action' "${ui_file}"
  assert_success

  run grep -q 'home_tool_action_execute_pending' "${ui_file}"
  assert_success

  run grep -q 'def execute_pending_home_tool_action' "${ui_file}"
  assert_success

  run grep -q 'def render_home_tool_action_dialog' "${ui_file}"
  assert_success

  run grep -q 'def render_terminal_output' "${ui_file}"
  assert_success

  run grep -q 'hhs-home-tool-action-output' "${ui_file}"
  assert_success

  run grep -q '.hhs-home-tool-action-output' "${css_file}"
  assert_success

  run grep -q 'max-height: min(52dvh, 28rem)' "${css_file}"
  assert_success

  run grep -q 'max-width: min(82vw, 58rem)' "${css_file}"
  assert_success

  run grep -q 'def home_tool_action_noun' "${ui_file}"
  assert_success

  run grep -q '"Installation"' "${ui_file}"
  assert_success

  run grep -q 'title = f"{home_tool_action_noun(operation)} of {tool_name} {status}"' "${ui_file}"
  assert_success

  run grep -q 'def apply_selected_tool_tldr' "${ui_file}"
  assert_success

  run grep -q 'def render_home_tool_tldr_dialog' "${ui_file}"
  assert_success

  run grep -q 'label": "Install"' "${ui_file}"
  assert_success

  run grep -q 'label": "Uninstall"' "${ui_file}"
  assert_success

  run grep -q 'label": "Reinstall"' "${ui_file}"
  assert_success

  run grep -q 'label": "TLDR"' "${ui_file}"
  assert_success

  run grep -q 'empty_hint: str = "Select a row to interact"' "${ui_file}"
  assert_success

  run grep -q 'empty_caption: str = "Select a row to interact"' "${ui_file}"
  assert_success

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

  run grep -q 'CONFIG_VIEWS = ("ENV", "PATH", "DIR", "CMD", "ALIAS")' "${constants_file}"
  assert_success

  run grep -q '"ENV": " Environment"' "${constants_file}"
  assert_success

  run grep -q '"PATH": " Paths"' "${constants_file}"
  assert_success

  run grep -q '"DIR": " Saved Dirs"' "${constants_file}"
  assert_success

  run grep -q '"CMD": "ﮒ Saved Cmds"' "${constants_file}"
  assert_success

  run grep -q '"ALIAS": " Aliases"' "${constants_file}"
  assert_success

  run grep -q 'format_func=config_view_label' "${ui_file}"
  assert_success

  run grep -q 'globals().get(' "${ui_file}"
  assert_failure

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'from constants import \*' "${ui_file}"
  assert_failure

  run grep -q '^import hhs_ui$' "${ui_file}"
  assert_success

  run grep -q 'HISTORY_VIEWS = ("COMMANDS", "DIRECTORIES", "STATS")' "${constants_file}"
  assert_success

  run grep -q '"COMMANDS": " Commands"' "${constants_file}"
  assert_success

  run grep -q '"DIRECTORIES": " Directories"' "${constants_file}"
  assert_success

  run grep -q '"STATS": " Stats"' "${constants_file}"
  assert_success

  run grep -q 'def history_view_label' "${ui_file}"
  assert_success

  run grep -q 'format_func=history_view_label' "${ui_file}"
  assert_success

  run grep -q 'MONITOR_VIEWS = ("DISK", "MEM", "CPU", "PROCESSES", "LOGS")' "${constants_file}"
  assert_success

  run grep -q '"DISK": " Disks"' "${constants_file}"
  assert_success

  run grep -q '"CPU": " Cpu"' "${constants_file}"
  assert_success

  run grep -q '"MEM": " Memory"' "${constants_file}"
  assert_success

  run grep -q '"PROCESSES": " Processes"' "${constants_file}"
  assert_success

  run grep -q '"LOGS": " Logs"' "${constants_file}"
  assert_success

  run grep -q 'def monitor_view_label' "${ui_file}"
  assert_success

  run grep -q 'format_func=monitor_view_label' "${ui_file}"
  assert_success

  run grep -q 'def normalized_monitor_disk_top_n' "${ui_file}"
  assert_success

  run grep -q 'return 10' "${ui_file}"
  assert_success

  run grep -q 'key="monitor_disk_top_n_input"' "${ui_file}"
  assert_success

  run grep -q 'on_change=handle_monitor_disk_top_n_change' "${ui_file}"
  assert_success

  run grep -q 'SERVICE_FILTERS = ("All", "Up", "Down", "Other")' "${constants_file}"
  assert_success

  run grep -q 'PATH_FILTERS = ("All", "Shell", "Private", "Custom", "Other")' "${constants_file}"
  assert_success
}

# TC - 10
@test "when executing shell commands then every UI command path should use run_bash_command" {
  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
violations = []
parents = {}

for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
        parents[child] = node

def enclosing_function(node):
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.FunctionDef):
            return parent.name
        parent = parents.get(parent)
    return ""

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    func = node.func
    is_subprocess_run = (
        isinstance(func, ast.Attribute)
        and func.attr == "run"
        and isinstance(func.value, ast.Name)
        and func.value.id == "subprocess"
    )
    allowed_functions = {"resolve_run_shell", "run_bash_command", "run_cleanup_bash_command"}
    if is_subprocess_run and enclosing_function(node) not in allowed_functions:
        violations.append(f"line {node.lineno}")

if violations:
    raise SystemExit("subprocess.run outside command runners: " + ", ".join(violations))
PY
  assert_success

  run grep -q 'def run_bash_command(' "${ui_file}"
  assert_success

  run grep -q 'return run_bash_command(' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_services_quietly' "${ui_file}"
  assert_success

  run grep -q 'def parse_ssh_config_hosts' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_connect_command' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_disconnect_command' "${ui_file}"
  assert_success

  run grep -q 'UI_CACHE_SSH_CONNECTION_KEY' "${constants_file}"
  assert_success

  run grep -q 'UI_SSH_CONNECTION_FILE' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_failure

  run grep -q 'def restore_registered_ssh_connection_on_session_start' "${ui_file}"
  assert_success

  run grep -q 'restore_registered_ssh_connection_on_session_start()' "${ui_file}"
  assert_success

  run grep -q 'ssh_connection_restore_checked' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.SSH_RECONNECT_HOST_KEY' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_connect_pending"\] = reconnect_host' "${ui_file}"
  assert_success

  run grep -q 'f"Reconnecting to {ssh_connection_display(reconnect_host)}"' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_reconnect_restore_view_state"\] = True' "${ui_file}"
  assert_success

  run grep -q 'def reconnect_view_state_snapshot' "${ui_file}"
  assert_success

  run grep -q 'def restore_reconnect_view_state' "${ui_file}"
  assert_success

  run grep -q 'loader_message = str(' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_connect_pending_message"\] = ""' "${ui_file}"
  assert_success

  run grep -q 'Disconnecting stale SSH host' "${ui_file}"
  assert_failure

  run grep -q 'st.session_state\["ssh_connection_status"\] = "connected"' "${ui_file}"
  assert_success

  run grep -q 'def clear_host_scoped_session_state' "${ui_file}"
  assert_success

  run grep -q 'clear_host_scoped_session_state()' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\[hhs_ui.TERMINAL_CWD_KEY\] = "."' "${ui_file}"
  assert_success

  run grep -q 'key in hhs_ui.PERSISTED_UI_KEYS' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
body = source.split("def execute_pending_ssh_connection", 1)[1].split("\ndef ", 1)[0]
snapshot_index = body.index("was_terminal_active = terminal_document_view_is_active()")
reset_index = body.index("clear_host_scoped_session_state()")
status_index = body.index('st.session_state["ssh_connection_status"] = "connected"')
remote_cwd_index = body.index("update_remote_footer_working_directory()")
restore_index = body.index("restore_terminal_document_view(was_terminal_active)")
assert snapshot_index < reset_index
assert reset_index < status_index
assert status_index < remote_cwd_index < restore_index
assert "set_overlay(True" not in body
assert "set_overlay(False" not in body
assert "show_overlay=False" not in body
assert "cache_clear()" in source.split("def clear_host_scoped_session_state", 1)[1].split("\ndef ", 1)[0]
assert "cache_clear()" in source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state.pop("ssh_reconnect_restore_view_state", False)' in body
assert "reconnect_view_state_snapshot()" in body
assert "restore_reconnect_view_state(reconnect_state)" in body
restore_reconnect_index = body.index("restore_reconnect_view_state(reconnect_state)")
assert reset_index < restore_reconnect_index < status_index
disconnect_body = source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert "st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)" in disconnect_body
assert 'st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""' in disconnect_body
restore_body = source.split("def restore_registered_ssh_connection_on_session_start", 1)[1].split("\ndef ", 1)[0]
assert "registered_ssh_connection_host() or reconnect_host" in restore_body
assert "clear_disconnected_ssh_host(host)" not in restore_body
assert 'st.session_state["ssh_connect_pending"] = reconnect_host' in restore_body
assert 'st.session_state["ssh_connect_pending_message"] = (' in restore_body
assert 'st.session_state["ssh_reconnect_restore_view_state"] = True' in restore_body
PY
  assert_success

  run grep -q 'def register_ssh_connection' "${ui_file}"
  assert_success

  run grep -q 'def clear_registered_ssh_connection' "${ui_file}"
  assert_success

  run grep -q 'def legacy_ssh_connection_files' "${ui_file}"
  assert_success

  run grep -q 'def unlink_legacy_ssh_connection_files' "${ui_file}"
  assert_success

  run grep -Fq 'cache[hhs_ui.UI_CACHE_SSH_CONNECTION_KEY] = {"value": {"host": clean_host}}' "${ui_file}"
  assert_success

  run grep -q 'ui_cache_metadata_key(key)' "${ui_file}"
  assert_success

  run grep -q 'def request_ssh_host_connect' "${ui_file}"
  assert_success

  run grep -q 'on_change=request_ssh_host_connection' "${ui_file}"
  assert_failure

  run grep -q 'def selected_ssh_host_is_connected' "${ui_file}"
  assert_success

  run grep -q 'def connected_ssh_host' "${ui_file}"
  assert_success

  run grep -q 'def synchronize_selected_ssh_host_with_connection' "${ui_file}"
  assert_success

  run grep -q 'synchronize_selected_ssh_host_with_connection()' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_host_selected"\] = host' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_host_selector"\] = host' "${ui_file}"
  assert_success

  run grep -q 'ssh_connection_host' "${ui_file}"
  assert_success

  run grep -q 'def request_ssh_host_disconnection' "${ui_file}"
  assert_success

  run grep -q 'def execute_pending_ssh_disconnection' "${ui_file}"
  assert_success

  run grep -q -- '-O exit' "${ui_file}"
  assert_success

  run grep -q 'pgrep -f --' "${ui_file}"
  assert_success

  run grep -q 'kill -TERM' "${ui_file}"
  assert_success

  run grep -q 'kill -KILL' "${ui_file}"
  assert_success

  run grep -q 'rm -f {safe_control_path}' "${ui_file}"
  assert_success

  run grep -q 'def ssh_config_option' "${ui_file}"
  assert_success

  run grep -q -- '-F "${HOME}/.ssh/config"' "${ui_file}"
  assert_success

  run grep -q 'ControlMaster=yes' "${ui_file}"
  assert_success

  run grep -q 'ConnectionAttempts=1' "${ui_file}"
  assert_success

  run grep -q 'timeout_seconds=15' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_wrapped_command' "${ui_file}"
  assert_success

  run grep -q 'bash -ic' "${ui_file}"
  assert_success

  run grep -q '"ssh",' "${ui_file}"
  assert_success

  run grep -q '"-tt",' "${ui_file}"
  assert_success

  run grep -q 'safe_remote_shell = shlex.quote' "${ui_file}"
  assert_success

  run grep -Fq 'JOB_NAME="${JOB_NAME:-HomeSetup-UI}"' "${ui_file}"
  assert_failure

  run grep -Fq 'source "${HOME}/.bashrc"' "${ui_file}"
  assert_failure

  run grep -Fq '[[ ! -s "${HOME}/.hhsrc" ]]' "${ui_file}"
  assert_failure

  run grep -Fq '"HomeSetup" is not installed on the host.' "${ui_file}"
  assert_failure

  run grep -Fq 'def handle_missing_remote_homesetup' "${ui_file}"
  assert_failure

  run grep -Fq 'result.returncode != 86' "${ui_file}"
  assert_failure

  run grep -q 'def effective_bash_command' "${ui_file}"
  assert_success

  run grep -q 'def resolve_run_shell' "${ui_file}"
  assert_success

  run grep -q '\["brew", "--prefix", "bash"\]' "${ui_file}"
  assert_success

  run grep -q '\["/opt/homebrew/bin/brew", "--prefix", "bash"\]' "${ui_file}"
  assert_success

  run grep -q '\["/usr/local/bin/brew", "--prefix", "bash"\]' "${ui_file}"
  assert_success

  run grep -q 'Path(run_shell) / "bin" / "bash"' "${ui_file}"
  assert_success

  run grep -q 'Path("/opt/homebrew/opt/bash/bin/bash")' "${ui_file}"
  assert_success

  run grep -q 'Path("/usr/local/opt/bash/bin/bash")' "${ui_file}"
  assert_success

  run grep -q 'Path("/bin/bash")' "${ui_file}"
  assert_success

  run grep -q 'RUN_SHELL = resolve_run_shell()' "${ui_file}"
  assert_success

  run grep -q 'os.environ\[hhs_ui_constants.RUN_SHELL_ENV_KEY\] = RUN_SHELL' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui_constants.RUN_SHELL_ENV_KEY: RUN_SHELL' "${ui_file}"
  assert_success

  run grep -q '\[RUN_SHELL, "-lc", command_to_run\]' "${ui_file}"
  assert_success

  run grep -q '\["bash", "-lc"' "${ui_file}"
  assert_failure

  run grep -q 'source "{hhs_home}' "${ui_file}"
  assert_failure

  run grep -q 'export HHS_HOME="{hhs_home}' "${ui_file}"
  assert_failure

  run grep -q '/Users/hjunior/HomeSetup' "${ui_file}"
  assert_failure

  run grep -q 'export HHS_DIR="${HHS_DIR:-${HOME}/.config/hhs}"' "${ui_file}"
  assert_failure

  run grep -q 'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"' "${ui_file}"
  assert_success

  run grep -q 'or not selected_ssh_host_is_connected(host)' "${ui_file}"
  assert_success

  run grep -q 'force_local: bool = False' "${ui_file}"
  assert_success

  run grep -q 'def build_ssh_tunnels_command' "${ui_file}"
  assert_success

  run grep -q 'ssh {safe_config_option} -G {safe_host}' "${ui_file}"
  assert_success

  run grep -q 'def run_ssh_tunnels' "${ui_file}"
  assert_success

  run grep -q 'def parse_ssh_tunnels' "${ui_file}"
  assert_success

  run grep -q 'def parse_ssh_config_tunnels' "${ui_file}"
  assert_success

  run grep -q 'def annotate_ssh_tunnel_statuses' "${ui_file}"
  assert_success

  run grep -q 'def ssh_tunnel_status_cell_style' "${ui_file}"
  assert_success

  run grep -q 'def display_ssh_tunnel_rows' "${ui_file}"
  assert_success

  run grep -q 'headers = \["Local Port", "Remote Host:Port", "Kind", "Status", "Link"\]' "${ui_file}"
  assert_success

  run grep -q 'Path(os.environ.get("HHS_HOME", APP_DIR.parents\[4\]))' "${constants_file}"
  assert_success

  run grep -q '/ "assets/devel/ports-default.csv"' "${constants_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/assets/devel/ports-default.csv"
  assert_success

  run grep -q 'column_config: dict\[str, object\] | None = None' "${ui_file}"
  assert_success

  run grep -q 'st.column_config.LinkColumn' "${ui_file}"
  assert_success

  run grep -F -q 'display_text=r"http://(127\.0\.0\.1:\d+)"' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_view' "${ui_file}"
  assert_success

  run grep -q 'key=hhs_ui.SSH_TUNNEL_TABLE_KEY' "${ui_file}"
  assert_success

  run grep -q 'checkbox=False' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
import csv
import re
import shlex
import sys
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def split_ssh_command(")
end = source.index("def parse_hhs_history(")
namespace = {
    "csv": csv,
    "hhs_ui": SimpleNamespace(
        PORTS_DEFAULT_FILE=Path("assets/devel/ports-default.csv"),
    ),
    "lru_cache": lru_cache,
    "Path": Path,
    "re": re,
    "shlex": shlex,
    "ssh_config_file": lambda: Path.home() / ".ssh" / "config",
    "strip_ansi": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

rows = namespace["parse_ssh_tunnels"](
    """
    __HHS_SSH_CONFIG__
    host homeselect
    hostname 10.0.0.5
    localforward 15432 127.0.0.1:5432
    remoteforward 0.0.0.0:9000 127.0.0.1:9000
    dynamicforward 127.0.0.1:1080
    __HHS_SSH_PROCESSES__
    100 ssh -N -L 8080:localhost:80 user@example.com
    101 /usr/bin/ssh -N -R0.0.0.0:9000:127.0.0.1:9000 remote
    102 ssh -N -D 127.0.0.1:1080 remote
    103 ssh -MNf remote
    """,
    "homeselect",
)

assert rows == [
    {
        "Type": "Local",
        "Bind": "15432",
        "Destination": "127.0.0.1:5432",
        "SSH Host": "homeselect",
        "Source": "Config",
        "Status": "",
        "PID": "",
        "Command": str(Path.home() / ".ssh" / "config"),
    },
    {
        "Type": "Remote",
        "Bind": "0.0.0.0:9000",
        "Destination": "127.0.0.1:9000",
        "SSH Host": "homeselect",
        "Source": "Config",
        "Status": "",
        "PID": "",
        "Command": str(Path.home() / ".ssh" / "config"),
    },
    {
        "Type": "Dynamic",
        "Bind": "127.0.0.1:1080",
        "Destination": "SOCKS",
        "SSH Host": "homeselect",
        "Source": "Config",
        "Status": "",
        "PID": "",
        "Command": str(Path.home() / ".ssh" / "config"),
    },
    {
        "Type": "Local",
        "Bind": "8080",
        "Destination": "localhost:80",
        "SSH Host": "user@example.com",
        "Source": "Process",
        "Status": "",
        "PID": "100",
        "Command": "ssh -N -L 8080:localhost:80 user@example.com",
    },
    {
        "Type": "Remote",
        "Bind": "0.0.0.0:9000",
        "Destination": "127.0.0.1:9000",
        "SSH Host": "remote",
        "Source": "Process",
        "Status": "",
        "PID": "101",
        "Command": "/usr/bin/ssh -N -R0.0.0.0:9000:127.0.0.1:9000 remote",
    },
    {
        "Type": "Dynamic",
        "Bind": "127.0.0.1:1080",
        "Destination": "SOCKS",
        "SSH Host": "remote",
        "Source": "Process",
        "Status": "",
        "PID": "102",
        "Command": "ssh -N -D 127.0.0.1:1080 remote",
    },
], rows

assert namespace["split_bind_address"]("127.0.0.1:1080") == ("127.0.0.1", 1080)
assert namespace["split_bind_address"]("15432") == ("127.0.0.1", 15432)
assert namespace["ssh_tunnel_status_cell_style"]("Reachable").endswith("#50fa7b;")
assert namespace["ssh_tunnel_status_cell_style"]("Not reachable").endswith("#ff5555;")
display_rows = namespace["display_ssh_tunnel_rows"](
    [{"Bind": "15432", "Destination": "127.0.0.1:5432", "Status": "Reachable"}]
)
assert display_rows == [
    {
        "Local Port": "15432",
        "Remote Host:Port": "127.0.0.1:5432",
        "Kind": "PostgreSQL",
        "Status": "Reachable",
        "Link": "http://127.0.0.1:15432",
    }
], display_rows
assert namespace["ssh_tunnel_kind"]({"Type": "Local", "Destination": "localhost:80"}) == "HTTP"
assert namespace["ssh_tunnel_kind"]({"Type": "Dynamic", "Bind": "127.0.0.1:1080"}) == "SOCKS"
PY
  assert_success

  run grep -q 'timeout_seconds: int | None = None' "${ui_file}"
  assert_success

  run grep -q 'effective_timeout = hhs_ui.UI_COMMAND_DEFAULT_TIMEOUT_SECONDS' "${ui_file}"
  assert_success

  run grep -q 'except subprocess.TimeoutExpired' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'def clear_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'def dismiss_streamlit_dialog' "${ui_file}"
  assert_success

  run grep -Fq 'button[aria-label="Close"]' "${ui_file}"
  assert_success

  run grep -q 'close_button.click()' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'render_dialog()' "${ui_file}"
  assert_success

  run grep -q 'if render_ssh_connection_dialog()' "${ui_file}"
  assert_success

  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "render_ssh_connection_dialog":
        assert "st.stop()" not in ast.unparse(node)
        break
else:
    raise AssertionError("render_ssh_connection_dialog not found")
PY
  assert_success

  run grep -q 'return True' "${ui_file}"
  assert_success

  run grep -q 'dismiss_streamlit_dialog()' "${ui_file}"
  assert_success

  run grep -q 'set_overlay(False)' "${ui_file}"
  assert_success

  run grep -q 'f"Connected to remote  {ssh_connection_display(host)}"' "${ui_file}"
  assert_success

  run grep -q 'push_floating_status(f"Failed to connect to remote: {host}", "error")' "${ui_file}"
  assert_success

  run grep -q 'push_floating_status("Opened working directory.", "info")' "${ui_file}"
  assert_success

  run grep -q 'push_floating_status("AI chat history cleared.", "info")' "${ui_file}"
  assert_success

  run grep -q 'status_message or f"Selected AI model: {new_model}"' "${ui_file}"
  assert_success

  run grep -q 'status_message or f"Deleted AI model: {model_name}"' "${ui_file}"
  assert_success

  run grep -q 'push_floating_status(f"Loaded TLDR: {tool_name}", "info")' "${ui_file}"
  assert_success

  run grep -q 'status_message or f"Killed process: {process_name}"' "${ui_file}"
  assert_success

  run grep -q 'status_message or f"Service {operation} completed: {service_name}"' "${ui_file}"
  assert_success

  run grep -q 'kind_aliases = {"success": "info", "warning": "warn"}' "${ui_file}"
  assert_success

  run grep -q 'def clean_command_status_message' "${ui_file}"
  assert_success

  run grep -q 'clean_message = clean_command_status_message(str(message))' "${ui_file}"
  assert_success

  run grep -q 'clean_kind not in {"info", "warn", "error"}' "${ui_file}"
  assert_success

  run grep -q 'Successfully connected to {host}' "${ui_file}"
  assert_failure

  run grep -F -q 'st.session_state["ssh_connection_dialog_title"] = ""' "${ui_file}"
  assert_success

  run grep -q 'Failed to connect to {host}' "${ui_file}"
  assert_success

  run grep -q 'st.error(st.session_state.get("ssh_connection_error", "SSH failed."))' "${ui_file}"
  assert_failure
}

# TC - 11
@test "when showing command progress then command runner should paint overlay before subprocess" {
  run grep -q 'def set_overlay(' "${ui_file}"
  assert_success

  run grep -q 'def render_footer_visibility_script' "${ui_file}"
  assert_failure

  run grep -q 'render_footer_visibility_script(hidden=True)' "${ui_file}"
  assert_failure

  run grep -q 'render_footer_visibility_script(hidden=False)' "${ui_file}"
  assert_failure

  run grep -q 'hhs-footer-hidden' "${ui_file}"
  assert_failure

  run grep -q 'classList.add("hhs-main-hidden")' "${ui_file}"
  assert_failure

  run grep -q 'classList.remove("hhs-main-hidden")' "${ui_file}"
  assert_failure

  run grep -q '.hhs-main-hidden \[data-testid="stMain"\]' "${css_file}"
  assert_failure

  run grep -q '_hhs_footer_visibility_sequence' "${ui_file}"
  assert_failure

  run grep -q 'dataset.hhsFooterVisibilitySequence' "${ui_file}"
  assert_failure

  run grep -q '.hhs-footer-hidden .hhs-app-footer' "${css_file}"
  assert_failure

  run grep -q 'def close_all_dialogs()' "${ui_file}"
  assert_success

  run grep -q 'close_all_dialogs()' "${ui_file}"
  assert_success

  run grep -q 'set_overlay(True, loader_message, close_dialogs=close_dialogs)' "${ui_file}"
  assert_success

  run grep -q 'overlay.id = "hhs-command-overlay"' "${ui_file}"
  assert_success

  run grep -q 'doc.body.appendChild(overlay)' "${ui_file}"
  assert_success

  run grep -q 'def clear_preloader()' "${ui_file}"
  assert_success

  run grep -q 'clear_preloader()' "${ui_file}"
  assert_success

  run grep -q 'command_overlay_slot' "${ui_file}"
  assert_failure

  run grep -q 'placeholder_key = "_hhs_overlay_placeholder"' "${ui_file}"
  assert_failure

  run grep -q 'with placeholder.container()' "${ui_file}"
  assert_failure

  run grep -q 'st.container(key=f"command_overlay_slot_{sequence}")' "${ui_file}"
  assert_failure

  run grep -q 'sequence_key = "_hhs_overlay_slot_sequence"' "${ui_file}"
  assert_failure

  run grep -q 'hhs-tab-loader-label' "${ui_file}"
  assert_success

  run grep -q 'time.sleep(0.1)' "${ui_file}"
  assert_success

  run grep -q 'components.html(' "${ui_file}"
  assert_success

  run grep -q 'window.setInterval(render_elapsed, 1000)' "${ui_file}"
  assert_success

  run grep -q 'set_overlay(False)' "${ui_file}"
  assert_success

  run grep -q 'def run_bash_subprocess' "${ui_file}"
  assert_success

  run grep -q 'result = run_bash_subprocess(command_to_run, effective_timeout)' "${ui_file}"
  assert_success

  run grep -q 'subprocess.Popen(' "${ui_file}"
  assert_success

  run grep -q 'start_new_session=True' "${ui_file}"
  assert_success

  run grep -q 'stop_process(process)' "${ui_file}"
  assert_success

  run grep -q 'Command timed out after {timeout_seconds} seconds.' "${ui_file}"
  assert_success

  run grep -q 'hhs-tab-loader' "${css_file}"
  assert_success

  run grep -F -q 'div[class*="st-key-command_overlay_slot_"]' "${css_file}"
  assert_failure

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:empty' "${css_file}"
  assert_success

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has([data-testid="stMarkdownContainer"] style)' "${css_file}"
  assert_success

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has([data-testid="stAppIframeResizerAnchor"])' "${css_file}"
  assert_success

  run grep -q 'height: 0 !important' "${css_file}"
  assert_success

  run grep -q 'position: fixed' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-background)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success
}

# TC - 12
@test "when confirming actions then reusable pop_dialog component should be used" {
  run grep -q 'def pop_dialog(' "${ui_file}"
  assert_success

  run grep -q 'def render_folder_picker_dialog' "${ui_file}"
  assert_success

  run grep -q 'render_folder_picker_dialog()' "${ui_file}"
  assert_success

  run grep -q 'def queue_dialog_callback' "${ui_file}"
  assert_success

  run grep -q 'def execute_pending_dialog_callback' "${ui_file}"
  assert_success

  run grep -q 'def handle_dialog_button_click' "${ui_file}"
  assert_success

  run grep -q 'def handle_dialog_dismiss' "${ui_file}"
  assert_success

  run grep -q 'execute_pending_dialog_callback()' "${ui_file}"
  assert_success

  run grep -q '@st.dialog(title, dismissible=dismissible, on_dismiss=on_dismiss)' "${ui_file}"
  assert_success

  run grep -q 'handle_dialog_button_click(' "${ui_file}"
  assert_success

  run grep -q 'queue_dialog_callback(callback)' "${ui_file}"
  assert_success

  run grep -q '_hhs_dialog_button_dismissal' "${ui_file}"
  assert_success

  run grep -q 'handle_dialog_dismiss(dismiss_callback)' "${ui_file}"
  assert_success

  run grep -q 'dismiss_streamlit_dialog()' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_home_tool_action_dialog' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_home_tool_tldr_dialog' "${ui_file}"
  assert_success

  run grep -q 'close_callback=close_ssh_connection_dialog' "${ui_file}"
  assert_success

  run grep -q 'st.rerun(scope="app")' "${ui_file}"
  assert_failure

  run grep -q '" README"' "${ui_file}"
  assert_success

  run grep -q '" HANDBOOK"' "${ui_file}"
  assert_success

  run grep -q '" Terminal"' "${ui_file}"
  assert_success

  run grep -q 'args=("TERMINAL",)' "${ui_file}"
  assert_success

  run grep -q 'def terminal_document_view_is_active' "${ui_file}"
  assert_success

  run grep -q 'if terminal_document_view_is_active():' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
terminal_button_body = ui_source.split("def render_sidebar_terminal_button()", 1)[1].split("\ndef ", 1)[0]
assert "if terminal_document_view_is_active():" in terminal_button_body
assert "return" in terminal_button_body.split('st.button(', 1)[0]
sidebar_body = ui_source.split("def render_sidebar()", 1)[1].split("\ndef ", 1)[0]
terminal_index = sidebar_body.index("render_sidebar_terminal_button()")
theme_index = sidebar_body.index('st.markdown("**Theme**")')
separator_index = sidebar_body.index('hhs-sidebar-separator')
connect_index = sidebar_body.index('"ﮣ Connect"')
disconnect_index = sidebar_body.index('"ﮤ Disconnect"')
readme_index = sidebar_body.index('" README"')
handbook_index = sidebar_body.index('" HANDBOOK"')
assert connect_index < theme_index
assert disconnect_index < theme_index
assert theme_index < separator_index < readme_index < handbook_index < terminal_index
assert 'st.markdown("**Documents**")' not in sidebar_body
PY
  assert_success

  run grep -q 'def render_terminal_document_view' "${ui_file}"
  assert_success

  run grep -q 'document_key == "TERMINAL"' "${ui_file}"
  assert_success

  run grep -q '"document_view_active"' "${constants_file}"
  assert_success

  run grep -q '"document_selected"' "${constants_file}"
  assert_success

  run grep -q '"document_previous_view"' "${constants_file}"
  assert_success

  run grep -q 'def open_document_view' "${ui_file}"
  assert_success

  run grep -q 'def activate_terminal_document_view' "${ui_file}"
  assert_success

  run grep -q 'def deactivate_terminal_document_view' "${ui_file}"
  assert_success

  run grep -q 'def restore_terminal_document_view' "${ui_file}"
  assert_success

  run grep -q 'activate_terminal_document_view()' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\[hhs_ui.TERMINAL_CWD_KEY\] = footer_working_directory()' "${ui_file}"
  assert_success

  run grep -q 'def close_document_view' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
open_body = ui_source.split("def open_document_view", 1)[1].split("\ndef ", 1)[0]
close_body = ui_source.split("def close_document_view", 1)[1].split("\ndef ", 1)[0]
render_main_body = ui_source.split("def render_main_view", 1)[1].split("\ndef ", 1)[0]
deactivate_body = ui_source.split("def deactivate_terminal_document_view", 1)[1].split("\ndef ", 1)[0]
assert 'terminal_document_view_is_active() and document_key != "TERMINAL"' in open_body
assert "deactivate_terminal_document_view()" in open_body
assert "if terminal_document_view_is_active():" in close_body
assert "deactivate_terminal_document_view()" in close_body
assert "if not terminal_document_view_is_active():" in render_main_body
assert "stop_ttyd_session()" in render_main_body
assert "stop_ttyd_session()" in deactivate_body
assert "TERMINAL_READY_STATUS_SHOWN_KEY" in deactivate_body
PY
  assert_success

  run grep -q 'def terminal_document_title' "${ui_file}"
  assert_success

  run grep -q 'return "Remote Terminal"' "${ui_file}"
  assert_success

  run grep -q 'return "Terminal"' "${ui_file}"
  assert_success

  run grep -q '<h2> {html.escape(title)}</h2>' "${ui_file}"
  assert_success

  run grep -q 'def ttyd_binary' "${ui_file}"
  assert_success

  run grep -q '/opt/homebrew/opt/ttyd/bin/ttyd' "${ui_file}"
  assert_success

  run grep -q 'def ttyd_font_family' "${ui_file}"
  assert_success

  run grep -q 'def ttyd_font_file' "${ui_file}"
  assert_success

  run grep -q 'Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.otf' "${ui_file}"
  assert_success

  run grep -q 'def ensure_ttyd_index_file' "${ui_file}"
  assert_success

  run grep -q 'def fetch_ttyd_default_index' "${ui_file}"
  assert_success

  run grep -q 'def inject_ttyd_font' "${ui_file}"
  assert_success

  run grep -q 'def ttyd_font_face_style' "${ui_file}"
  assert_success

  run grep -q 'data:{mime_type};base64,{encoded_font}' "${ui_file}"
  assert_success

  run grep -q 'background:#000000!important;' "${ui_file}"
  assert_success

  run grep -q 'hhs-ttyd-font-index-v10' "${ui_file}"
  assert_success

  run grep -q 'padding:0!important;' "${ui_file}"
  assert_success

  run grep -q 'left:0!important;' "${ui_file}"
  assert_success

  run grep -q 'top:0!important;' "${ui_file}"
  assert_success

  run grep -q 'right:0!important;' "${ui_file}"
  assert_success

  run grep -q 'bottom:0!important;' "${ui_file}"
  assert_success

  run grep -q 'scrollbar-gutter:stable!important;' "${ui_file}"
  assert_success

  run grep -q '::-webkit-scrollbar-thumb' "${ui_file}"
  assert_success

  run grep -q 'transform:translate(5px,5px)!important;' "${ui_file}"
  assert_failure

  run grep -q 'const inset = 5' "${ui_file}"
  assert_success

  run grep -Fq 'frame.style.left = `${{rect.left + inset}}px`' "${ui_file}"
  assert_success

  run grep -Fq 'frame.style.width = `${{Math.max(0, rect.width - (inset * 2))}}px`' "${ui_file}"
  assert_success

  run grep -q 'background:transparent!important;' "${ui_file}"
  assert_success

  run grep -q 'width:calc(100% - 10px)!important;' "${ui_file}"
  assert_failure

  run grep -q 'def ttyd_bridge_script' "${ui_file}"
  assert_success

  run grep -q 'registerOscHandler(777' "${ui_file}"
  assert_success

  run grep -q "window.term.clear()" "${ui_file}"
  assert_success

  run grep -q "hhs-ttyd-event" "${ui_file}"
  assert_success

  run grep -q 'TTYD_INDEX_FILE = (' "${constants_file}"
  assert_failure

  run grep -q 'TTYD_INDEX_FILE = HHS_CACHE_DIR / ".streamlit-ttyd-index.html"' "${constants_file}"
  assert_success

  run grep -q '"TTYD_INDEX_FILE"' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'return hhs_ui.APP_FONT_FAMILY' "${ui_file}"
  assert_success

  run grep -q 'def build_ttyd_command' "${ui_file}"
  assert_success

  run grep -q 'def ttyd_shell_hook_script' "${ui_file}"
  assert_success

  run grep -q 'def build_ttyd_hooked_bash_command' "${ui_file}"
  assert_success

  run grep -q '__hhs_ttyd_emit_cwd "cd"' "${ui_file}"
  assert_success

  run grep -q '__hhs_ttyd_emit_cwd "pushd"' "${ui_file}"
  assert_success

  run grep -q '__hhs_ttyd_emit_cwd "popd"' "${ui_file}"
  assert_success

  run grep -q 'elif \[\[ -r "${HOME}/.bashrc" \]\]; then' "${ui_file}"
  assert_success

  run grep -q 'fontFamily={ttyd_font_family()}, monospace' "${ui_file}"
  assert_success

  run grep -q 'theme={"background":"#000000"}' "${ui_file}"
  assert_success

  run grep -q 'cursorBlink=true' "${ui_file}"
  assert_success

  run grep -q 'command.extend(("-I", index_file))' "${ui_file}"
  assert_success

  run grep -q 'def build_ttyd_remote_command' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
remote_body = ui_source.split("def build_ttyd_remote_command", 1)[1].split("\ndef ", 1)[0]
assert '"ssh",' in remote_body
assert '"-tt",' in remote_body
PY
  assert_success

  run grep -q 'ControlPath={ssh_control_path(host)}' "${ui_file}"
  assert_success

  run grep -q 'def ensure_ttyd_session' "${ui_file}"
  assert_success

  run grep -q 'def cleanup_session_resources' "${ui_file}"
  assert_success

  run grep -q 'def store_ttyd_event' "${ui_file}"
  assert_success

  run grep -q 'def normalize_ttyd_event' "${ui_file}"
  assert_success

  run grep -q 'def sync_ttyd_event_state' "${ui_file}"
  assert_success

  run grep -q 'def ttyd_event_url' "${ui_file}"
  assert_success

  run grep -q 'def ensure_ttyd_cleanup_server' "${ui_file}"
  assert_success

  run grep -q 'def render_browser_cleanup_script' "${ui_file}"
  assert_success

  run grep -q 'navigator.sendBeacon(cleanupUrl, "")' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.addEventListener("pagehide", cleanup, {{ once: true }})' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.addEventListener("beforeunload", cleanup, {{ once: true }})' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.addEventListener("message"' "${ui_file}"
  assert_success

  run grep -q 'cleanup_all_registered_sessions' "${ui_file}"
  assert_success

  run grep -q 'atexit.register(cleanup_all_registered_sessions)' "${ui_file}"
  assert_success

  run grep -q 'build_ssh_disconnect_command(ssh_host)' "${ui_file}"
  assert_success

  run grep -q 'ttyd_process_is_running(process)' "${ui_file}"
  assert_success

  run grep -q '"-q",' "${ui_file}"
  assert_success

  run grep -q 'update_browser_cleanup_registration()' "${ui_file}"
  assert_success

  run grep -q 'start_new_session=True' "${ui_file}"
  assert_success

  run grep -q 'os.killpg(process_group, signal.SIGTERM)' "${ui_file}"
  assert_success

  run grep -q 'os.killpg(process_group, signal.SIGKILL)' "${ui_file}"
  assert_success

  run grep -q 'subprocess.Popen(' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
main_body = ui_source.split("def main()", 1)[1].split('\nif __name__ == "__main__":', 1)[0]
disconnect_index = main_body.index("execute_pending_ssh_disconnection()")
connect_index = main_body.index("execute_pending_ssh_connection()")
footer_actions_index = main_body.index("handle_footer_actions()")
shell_dialog_index = main_body.index("render_footer_shell_version_dialog()")
cleanup_index = main_body.index("render_browser_cleanup_script()")
sidebar_index = main_body.index("render_sidebar()")
main_view_index = main_body.index("render_main_view()")
footer_index = main_body.index("render_footer()")
floating_status_index = main_body.index("render_floating_status()")
assert disconnect_index < connect_index < footer_actions_index < shell_dialog_index
assert shell_dialog_index < sidebar_index < main_view_index
assert footer_index < floating_status_index < cleanup_index
PY
  assert_success

  run grep -q 'def render_ttyd_terminal_frame' "${ui_file}"
  assert_success

  run grep -q 'hhs-persistent-ttyd-frame' "${ui_file}"
  assert_success

  run grep -q 'dataset.src !== src' "${ui_file}"
  assert_success

  run grep -q 'def render_ttyd_terminal_frame_cleanup_script' "${ui_file}"
  assert_success

  run grep -q 'render_ttyd_terminal_frame_cleanup_script()' "${ui_file}"
  assert_success

  run grep -q 'stop_ttyd_session()' "${ui_file}"
  assert_success

  run grep -q 'TERMINAL_READY_STATUS_SHOWN_KEY = "terminal_ready_status_shown"' "${constants_file}"
  assert_success

  run grep -q 'st.session_state.setdefault(hhs_ui.TERMINAL_CWD_KEY, footer_working_directory())' "${ui_file}"
  assert_success

  run grep -q '"HomeSetup terminal is ready."' "${ui_file}"
  assert_success

  run grep -q 'ttyd_url = ensure_ttyd_session()' "${ui_file}"
  assert_success

  run grep -q 'def hhs_terminal_component' "${ui_file}"
  assert_failure

  run grep -q 'def render_terminal_component' "${ui_file}"
  assert_failure

  run grep -q 'def execute_terminal_command' "${ui_file}"
  assert_failure

  run grep -q 'TERMINAL_COMPONENT_DIR' "${constants_file}"
  assert_failure

  run grep -q 'TERMINAL_TRANSCRIPT_KEY' "${constants_file}"
  assert_failure

  run grep -q '.st-key-hhs_terminal_component iframe' "${css_file}"
  assert_failure

  run grep -q '.hhs-ttyd-terminal-frame' "${css_file}"
  assert_success

  run grep -q '.hhs-ttyd-terminal-placeholder' "${css_file}"
  assert_success

  run grep -q 'padding: 5px' "${css_file}"
  assert_success

  run grep -q 'height: calc(100dvh - var(--hhs-footer-guard-height) - 4.75rem)' "${css_file}"
  assert_success

  run grep -q 'max-height: var(--hhs-ttyd-max-height, 760px)' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-terminal-background-color, #000000)' "${css_file}"
  assert_success

  run grep -q 'height: calc(100% - 10px)' "${css_file}"
  assert_success

  run grep -q 'width: calc(100% - 10px)' "${css_file}"
  assert_success

  for theme_file in "${HHS_REPO_DIR}"/bin/apps/py/hhs_ui/themes/*.css; do
    run grep -q -- '--hhs-terminal-background-color: #000000' "${theme_file}"
    assert_success

    run grep -q 'background: var(--hhs-terminal-background-color)' "${theme_file}"
    assert_success
  done

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
assert ui_source.count("@st.dialog(") == 1
PY
  assert_success

  run grep -q 'st.warning("Clear the chat and reset AI context entirely?")' "${ui_file}"
  assert_failure

  run grep -q '@st.dialog("Confirm model change")' "${ui_file}"
  assert_failure

  run grep -q '@st.dialog("Confirm model deletion")' "${ui_file}"
  assert_failure
}

@test "when remote terminal prints wrapper chatter then command output should be filtered" {
  run python3 - "${ui_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def terminal_output_line_is_noise(")
end = source.index("def strip_ansi(")
namespace = {
    "re": re,
    "strip_ansi": lambda value: value,
    "strip_ssh_shared_connection_notice": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

stdout = (
    "[bash] HomeSetup is starting...\n"
    "[Linux-ubuntu/bash]   Welcome root to HomeSetup v1.9.18 \n"
    "Shell option expand_aliases set to on \n"
    "Shell option checkwinsize set to on \n"
    "bash: cd: /etc/gabiroba: No such file or directory\n"
    "exit\n"
    "__HHS_TERMINAL_CWD__/etc/ssl\n"
)
output = namespace["filter_terminal_output_noise"](stdout)
assert "HomeSetup is starting" not in output
assert "Welcome root" not in output
assert "Shell option expand_aliases" not in output
assert "\nexit\n" not in f"\n{output}\n"
assert "bash: cd: /etc/gabiroba: No such file or directory" in output
assert "__HHS_TERMINAL_CWD__" in output

stderr = "Shared connection to 167.99.120.81 closed.\nConnection to host closed.\nreal error\n"
filtered = namespace["filter_terminal_output_noise"](stderr)
assert "Shared connection" not in filtered
assert "Connection to host closed" not in filtered
assert filtered == "real error\n"
PY
  assert_success
}

# TC - 13
@test "when using Ask AI then chat and model settings should support context, reset, select, and delete" {
  run grep -q 'APP_AI_USER_AVATAR_FILE = APP_DIR / "assets/images/user.png"' "${constants_file}"
  assert_success

  run grep -q 'APP_AI_OLLAMA_AVATAR_FILE = APP_DIR / "assets/images/ollama.png"' "${constants_file}"
  assert_success

  run grep -q 'APP_AI_HOMESETUP_AVATAR_FILE = APP_DIR / "assets/images/homesetup.png"' "${constants_file}"
  assert_success

  run grep -q 'APP_FAVICON_FILE = APP_DIR / "assets/images/favicon.png"' "${constants_file}"
  assert_success

  run grep -q 'APP_FAVICON_FILE' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run test -s "${ask_prompt_file}"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/user.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/ollama.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/homesetup.png"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/images/favicon.png"
  assert_success

  run grep -q 'page_icon=str(hhs_ui.APP_FAVICON_FILE)' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-k", message\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-c"\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-p"\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-r"\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-i", file_path\])' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_ask_execute_command(\["-m"\])' "${ui_file}"
  assert_success

  run grep -q 'def render_ai_context_panel' "${ui_file}"
  assert_success

  run grep -q 'def render_ai_prompt_file_panel' "${ui_file}"
  assert_success

  run grep -q 'def render_ai_context_output_panel' "${ui_file}"
  assert_success

  run grep -q 'def refresh_ai_context' "${ui_file}"
  assert_success

  run grep -q 'def clear_ai_context_history' "${ui_file}"
  assert_success

  run grep -q 'def refresh_ai_prompt' "${ui_file}"
  assert_success

  run grep -q 'def refresh_ai_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'def save_ai_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'def revert_ai_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_ask_prompt_file_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_save_ask_prompt_file_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_revert_ask_prompt_file_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_ask_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_save_ask_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_revert_ask_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'cat "${HHS_OLLAMA_PROMPT_FILE}"' "${ui_file}"
  assert_success

  run grep -q 'prompt_file="${HHS_OLLAMA_PROMPT_FILE}"' "${ui_file}"
  assert_success

  run grep -q 'cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}"' "${ui_file}"
  assert_success

  run grep -q 'def ingest_ai_context_upload' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_ask_ingest' "${ui_file}"
  assert_success

  run grep -q 'AI_CONTEXT_UPLOAD_TYPES = (' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/constants.py"
  assert_success

  run grep -q 'st.file_uploader(' "${ui_file}"
  assert_success

  run grep -q '\[data-testid="stFileUploader"\] button' "${css_file}"
  assert_success

  run grep -q '\[data-testid="stFileUploader"\] button \*' "${css_file}"
  assert_success

  run grep -q '.stButton button' "${css_file}"
  assert_success

  run grep -q '.stButton button \*' "${css_file}"
  assert_success

  run grep -q 'type=hhs_ui_constants.AI_CONTEXT_UPLOAD_TYPES' "${ui_file}"
  assert_success

  run grep -q 'key="ai_context_upload"' "${ui_file}"
  assert_success

  run grep -q 'key="ai_ingest_context_button"' "${ui_file}"
  assert_success

  run grep -q '" Ingest"' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
refresh_body = ui_source.split("def refresh_ai_context", 1)[1].split("\ndef ", 1)[0]
context_body = ui_source.split("def render_ai_context_panel", 1)[1].split("\ndef ", 1)[0]
clear_context_body = ui_source.split("def clear_ai_context_history", 1)[1].split("\ndef ", 1)[0]
assert "run_hhs_ask_context()" in refresh_body
assert "run_hhs_ask_context()" not in context_body
assert "run_hhs_ask_prompt()" not in context_body
assert "render_ai_prompt_file_panel()" in context_body
assert "render_ai_context_output_panel()" in context_body
assert "run_hhs_ask_reset(close_dialogs=True)" in clear_context_body
assert 'st.session_state["ai_context_output"] = ""' in clear_context_body
assert 'st.session_state["ai_context_error"] = ""' in clear_context_body
assert 'st.session_state["ai_chat_messages"] = []' not in clear_context_body
PY
  assert_success

  run grep -q 'key="ai_refresh_context_button"' "${ui_file}"
  assert_success

  run grep -q 'key="ai_clear_context_button"' "${ui_file}"
  assert_success

  run grep -q 'on_click=clear_ai_context_history' "${ui_file}"
  assert_success

  run grep -q 'key="ai_prompt_context_button"' "${ui_file}"
  assert_failure

  run grep -q '" Refresh"' "${ui_file}"
  assert_success

  run grep -q '" Prompt"' "${ui_file}"
  assert_failure

  run grep -q 'with st.expander("Prompt", expanded=False):' "${ui_file}"
  assert_success

  run grep -q 'with st.expander("History", expanded=True):' "${ui_file}"
  assert_success

  run grep -q 'key="ai_prompt_editor"' "${ui_file}"
  assert_success

  run grep -q 'key="ai_prompt_save_button"' "${ui_file}"
  assert_success

  run grep -q 'key="ai_prompt_revert_button"' "${ui_file}"
  assert_success

  run grep -q 'on_click=save_ai_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'on_click=revert_ai_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'upload_col, ingest_col, clear_col, refresh_col = st.columns(' "${ui_file}"
  assert_success

  run grep -q '\[1.35, 0.7, 0.7, 0.8\], vertical_alignment="center"' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ai_context_output"\]' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ai_context_error"\]' "${ui_file}"
  assert_success

  run grep -q '"ai_context_output"' "${constants_file}"
  assert_success

  run grep -q '"ai_context_error"' "${constants_file}"
  assert_success

  run grep -q '"ai_prompt_editor"' "${constants_file}"
  assert_success

  run grep -q '"ai_prompt_error"' "${constants_file}"
  assert_success

  run grep -q '"ai_prompt_loaded"' "${constants_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("ai_context_output", "")' "${ui_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("ai_context_error", "")' "${ui_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("ai_prompt_editor", "")' "${ui_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("ai_prompt_error", "")' "${ui_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("ai_prompt_loaded", False)' "${ui_file}"
  assert_success

  run grep -q 'st.markdown("### AI context is clear")' "${ui_file}"
  assert_success

  run grep -q 'elif ai_view == "CONTEXT"' "${ui_file}"
  assert_success

  run grep -q 'render_ai_context_panel()' "${ui_file}"
  assert_success

  run grep -q 'render_terminal_output(context_output)' "${ui_file}"
  assert_success

  run grep -q 'key="ai_show_context_button"' "${ui_file}"
  assert_failure

  run grep -q 'show_ai_chat_context' "${ui_file}"
  assert_failure

  run grep -q '" Clear"' "${ui_file}"
  assert_success

  run grep -q 'run_hhs_ask_reset(close_dialogs=True)' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ai_context_output"\] = ""' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ai_context_error"\] = ""' "${ui_file}"
  assert_success

  run grep -q -- '-i|--ingest' "${ask_file}"
  assert_success

  run grep -q -- '-p | --prompt' "${ask_file}"
  assert_success

  run grep -q 'function show_prompt' "${ask_file}"
  assert_success

  run grep -q 'function seed_ollama_prompt_file' "${ask_file}"
  assert_failure

  run grep -q 'function load_ollama_prompt' "${ask_file}"
  assert_success

  run grep -q 'function render_ollama_prompt_template' "${ask_file}"
  assert_success

  run grep -q 'HHS_OLLAMA_PROMPT_SOURCE="${HHS_OLLAMA_PROMPT_SOURCE:-${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md}"' "${ask_file}"
  assert_success

  run grep -q 'HHS_OLLAMA_PROMPT_FILE="${HHS_OLLAMA_PROMPT_FILE:-${HHS_DIR}/hhs-ask-ollama.md}"' "${ask_file}"
  assert_success

  run grep -q 'HHS_OLLAMA_PROMPT="### INSTRUCTIONS ###' "${ask_file}"
  assert_failure

  run grep -q 'copy_file "${INSTALL_DIR}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md" "${HHS_DIR}/hhs-ask-ollama.md"' "${HHS_REPO_DIR}/install.bash"
  assert_success

  run grep -q 'export HHS_OLLAMA_PROMPT_SOURCE="${HHS_HOME}"/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md' "${hhsrc_file}"
  assert_success

  run grep -q 'export HHS_OLLAMA_PROMPT_FILE="${HHS_DIR}"/hhs-ask-ollama.md' "${hhsrc_file}"
  assert_success

  run grep -q 'if ! \[\[ -s "${HHS_OLLAMA_PROMPT_FILE}" \]\]; then' "${hhsrc_file}"
  assert_success

  run grep -q '\\cp -f "${HHS_OLLAMA_PROMPT_SOURCE}" "${HHS_OLLAMA_PROMPT_FILE}"' "${hhsrc_file}"
  assert_success

  run bash --noprofile --norc -c '
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/hhs"
    export HHS_OLLAMA_HISTORY_FILE="${2}/history.md"
    export HHS_SETUP_FILE="${2}/setup.toml"
    export HHS_MY_SHELL="bash"
    export HHS_MY_OS="Darwin"
    export HHS_MY_OS_RELEASE="test"
    export HHS_GITHUB_URL="https://example.invalid/hhs"
    export IS_PIPED=0
    mkdir -p "${HHS_DIR}"
    cp "${HHS_HOME}/bin/apps/bash/hhs-app/plugins/ask/hhs-ask-ollama.md" "${HHS_DIR}/hhs-ask-ollama.md"
    function __hhs_toml_get() { printf "hhs_ollama_model=llama3.1:latest\n"; }
    function quit() { return "${1:-0}"; }
    source "${1}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
    [[ -s "${HHS_DIR}/hhs-ask-ollama.md" ]]
    show_prompt
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}"
  assert_success
  assert_output --partial '### INSTRUCTIONS ###'
  assert_output --partial 'You execute inside a bash shell on test'
  refute_output --partial '${HHS_MY_SHELL}'
  refute_output --partial '${HHS_HOME}'

  run bash --noprofile --norc -c '
    export HHS_HOME="${1}"
    export HHS_DIR="${2}/override-hhs"
    export HHS_OLLAMA_HISTORY_FILE="${2}/history.md"
    export HHS_SETUP_FILE="${2}/setup.toml"
    export HHS_MY_SHELL="bash"
    export HHS_MY_OS="Darwin"
    export HHS_MY_OS_RELEASE="test"
    export HHS_GITHUB_URL="https://example.invalid/hhs"
    export HHS_OLLAMA_PROMPT="custom prompt"
    export IS_PIPED=0
    function __hhs_toml_get() { printf "hhs_ollama_model=llama3.1:latest\n"; }
    function quit() { return "${1:-0}"; }
    source "${1}/bin/apps/bash/hhs-app/plugins/ask/ask.bash"
    show_prompt
  ' -- "${HHS_REPO_DIR}" "${BATS_TEST_TMPDIR}"
  assert_success
  assert_output 'custom prompt'

  run grep -q 'function ingest_context' "${ask_file}"
  assert_success

  run grep -q 'is_text_context_file' "${ask_file}"
  assert_success

  run grep -Fq '(${ctx} * 0.7)/1' "${ask_file}"
  assert_success

  run grep -q -- '-r|--reset) clear_context' "${ask_file}"
  assert_success

  run grep -q 'disabled=not st.session_state\["ai_chat_messages"\]' "${ui_file}"
  assert_failure

  run grep -q 'st.markdown("### There is no chat history")' "${ui_file}"
  assert_success

  run grep -q 'meta_col, clear_col = st.columns(\[3.6, 0.4\], vertical_alignment="center")' "${ui_file}"
  assert_success

  run grep -q '.st-key-ai_show_context_button button' "${css_file}"
  assert_failure

  run grep -q '.st-key-ai_clear_chat_button button' "${css_file}"
  assert_failure

  run grep -q 'build_hhs_ask_execute_command(\["-s", model_name\])' "${ui_file}"
  assert_success

  run grep -q 'def hhs_ask_timeout_seconds' "${ui_file}"
  assert_success

  run grep -q 'return 180 if connected_ssh_host() else 90' "${ui_file}"
  assert_success

  run grep -q 'timeout_seconds=hhs_ask_timeout_seconds()' "${ui_file}"
  assert_success

  run grep -q 'AI_PERFORMANCE_MIN_SAMPLES = 3' "${constants_file}"
  assert_success

  run grep -q 'AI_PERFORMANCE_TIMING_LIMIT = 100' "${constants_file}"
  assert_success

  run grep -q 'AI_PERFORMANCE_MIN_SAMPLES' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'AI_PERFORMANCE_RECALC_INTERVAL' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'AI_PERFORMANCE_TIMING_LIMIT' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q '"ai_model_performance_timings"' "${constants_file}"
  assert_success

  run grep -q '"ai_model_performance_averages"' "${constants_file}"
  assert_success

  run grep -q '"ai_model_performance_sample_counts"' "${constants_file}"
  assert_success

  run grep -q 'def record_ai_model_request_duration' "${ui_file}"
  assert_success

  run grep -q 'def ai_chat_meta_html' "${ui_file}"
  assert_success

  run grep -q 'def parse_context_window_kib' "${ui_file}"
  assert_success

  run grep -q 'def ai_context_used_percent' "${ui_file}"
  assert_success

  run grep -q 'def ai_context_used_color' "${ui_file}"
  assert_success

  run grep -q 'def ai_context_used_meta_html' "${ui_file}"
  assert_success

  run grep -q 'def html_tooltip_chip' "${ui_file}"
  assert_success

  run grep -q 'def model_characteristics_tooltip_html' "${ui_file}"
  assert_success

  run grep -q 'def ai_context_used_tooltip_html' "${ui_file}"
  assert_success

  run grep -q 'def ai_model_recent_duration_tooltip_html' "${ui_file}"
  assert_success

  run grep -q 'def ollama_history_file' "${ui_file}"
  assert_success

  run grep -q 'def ollama_prompt_file' "${ui_file}"
  assert_success

  run grep -q 'def file_size_bytes' "${ui_file}"
  assert_success

  run grep -q 'HHS_OLLAMA_HISTORY_FILE' "${ui_file}"
  assert_success

  run grep -q 'HHS_OLLAMA_PROMPT_FILE' "${ui_file}"
  assert_success

  run grep -q '".ollama_history"' "${ui_file}"
  assert_success

  run grep -q '"hhs-ask-ollama.md"' "${ui_file}"
  assert_success

  run grep -q 'prompt_size = file_size_bytes(ollama_prompt_file())' "${ui_file}"
  assert_success

  run grep -q 'history_size = file_size_bytes(ollama_history_file())' "${ui_file}"
  assert_success

  run grep -q 'percent_of_context(prompt_size + history_size' "${ui_file}"
  assert_success

  run grep -q '"Ctx Used"' "${ui_file}"
  assert_success

  run grep -q 'Current logged user' "${ui_file}"
  assert_success

  run grep -q 'Prompt: ' "${ui_file}"
  assert_success

  run grep -q 'Context: ' "${ui_file}"
  assert_success

  run grep -q 'parse_ollama_model_rows(model_output, ollama_model)' "${ui_file}"
  assert_success

  run grep -q 'timing_durations_for_model(model_name)\[-5:\]' "${ui_file}"
  assert_success

  run grep -q 'hhs-tooltip-content' "${css_file}"
  assert_success

  run grep -q '.hhs-ai-chat-meta .hhs-tooltip:hover .hhs-tooltip-content' "${css_file}"
  assert_success

  run grep -q 'hhs-ai-chat-model hhs-ai-chat-user' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-chat-model hhs-ai-context-used' "${ui_file}"
  assert_success

  run grep -q 'var(--hhs-danger)' "${ui_file}"
  assert_success

  run grep -q 'var(--hhs-warning)' "${ui_file}"
  assert_success

  run grep -q 'var(--hhs-success)' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-chat-model hhs-ai-chat-duration' "${ui_file}"
  assert_success

  run grep -q 'meta_placeholder = st.empty()' "${ui_file}"
  assert_success

  run grep -q 'meta_placeholder.markdown(' "${ui_file}"
  assert_success

  run grep -q 'model_sample_count == hhs_ui.AI_PERFORMANCE_MIN_SAMPLES' "${ui_file}"
  assert_success

  run grep -q 'def ai_model_performance_timings' "${ui_file}"
  assert_success

  run grep -q -- '-hhs_ui.AI_PERFORMANCE_TIMING_LIMIT' "${ui_file}"
  assert_success

  run grep -q 'use_cache=False' "${ui_file}"
  assert_success

  run grep -q 'ask_started_at = time.perf_counter()' "${ui_file}"
  assert_success

  run grep -q 'record_ai_model_request_duration(ollama_model, request_duration)' "${ui_file}"
  assert_success

  run grep -q '"Latency"' "${ui_file}"
  assert_success

  run grep -q 'def parse_ollama_model_rows' "${ui_file}"
  assert_success

  run grep -q 'def first_downloaded_ollama_model' "${ui_file}"
  assert_success

  run grep -q 'Delete Model' "${ui_file}"
  assert_success

  run grep -q 'Select Model' "${ui_file}"
  assert_success
}

# TC - 14
@test "when selecting missing Ask model then ask plugin should download it instead of the UI" {
  run grep -q 'ollama pull "${model_name}"' "${ask_file}"
  assert_success

  run grep -q '__hhs_toml_set "${HHS_SETUP_FILE}" "hhs_ollama_model=${model_name}" "ollama"' "${ask_file}"
  assert_success

  run grep -q 'ollama pull' "${ui_file}"
  assert_failure

  run grep -q 'build_ollama_download_and_select_model_command' "${ui_file}"
  assert_failure
}

# TC - 15
@test "when rendering AI model settings then status, scrolling, and footer guard should be present" {
  run grep -q 'AI_MODEL_TABLE_KEY = "ai_model_table"' "${constants_file}"
  assert_success

  run grep -q 'AI_MODEL_ACTION_SCROLL_HELPER_HEIGHT = 0' "${constants_file}"
  assert_success

  run grep -q 'def scroll_to_ai_model_actions' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-model-action-footer-guard' "${ui_file}"
  assert_success

  run grep -q 'hhs-ai-model-action-footer-guard' "${css_file}"
  assert_success

  run python3 - "${css_file}" <<'PY'
import sys
from pathlib import Path

css = Path(sys.argv[1]).read_text(encoding="utf-8")
assert ".hhs-ai-model-action-footer-guard" in css
assert "min-height: 8rem" in css[
    css.index(".hhs-ai-model-action-footer-guard"):
    css.index(".st-key-ai_confirm_clear_button")
]
PY
  assert_success

  run grep -q 'status == "Downloaded"' "${ui_file}"
  assert_success

  run grep -q 'color: #4da3ff' "${ui_file}"
  assert_success

  run grep -q -- '--hhs-model-accent: #4da3ff' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/themes/dracula.css"
  assert_success
}

# TC - 16
@test "when rendering monitor panes then process listing and process kill should be wired" {
  run grep -q 'PROCESS_TABLE_KEY = "monitor_process_table"' "${constants_file}"
  assert_success

  run grep -q 'PROCESS_LIST_LINE_PATTERN' "${constants_file}"
  assert_success

  run grep -q 'PROCESS_FILTERS = ("All", "Active", "Inactive", "Ghost", "Other")' "${constants_file}"
  assert_success

  run grep -q 'PROCESS_FILTER_COLUMNS = \[2.65, 1.35\]' "${constants_file}"
  assert_success

  run grep -q '"monitor_process_other_filter"' "${constants_file}"
  assert_success

  run grep -q 'def build_hhs_process_list_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_process_kill_command' "${ui_file}"
  assert_success

  run grep -q '__hhs_process_list' "${ui_file}"
  assert_success

  run grep -q '__hhs_process_kill -f' "${ui_file}"
  assert_success

  run grep -q 'def render_monitor_processes_panel' "${ui_file}"
  assert_success

  run grep -q '"monitor_process_filter"' "${ui_file}"
  assert_success

  run grep -q '"monitor_process_other_filter"' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.PROCESS_FILTERS' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.PROCESS_FILTER_COLUMNS' "${ui_file}"
  assert_success

  run grep -q 'def filter_process_rows' "${ui_file}"
  assert_success

  run grep -q 'filter_process_rows(' "${ui_file}"
  assert_success

  run grep -q 'render_table_controls_panel(render_process_controls)' "${ui_file}"
  assert_success

  run grep -q 'monitor_process_filter_apply_button' "${ui_file}"
  assert_failure

  run grep -q 'apply_monitor_process_filter' "${ui_file}"
  assert_failure

  run grep -q '.st-key-monitor_process_other_filter' "${css_file}"
  assert_success
}

@test "when filtering monitor processes then status and other filters should use parsed rows" {
  run python3 - "${ui_file}" <<'PY'
import ast
import re
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {
    node.name: ast.get_source_segment(source, node)
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
assert namespace["filter_process_rows"](rows, "All") == rows
PY
  assert_success
}

# TC - 17
@test "when rendering logs then VT100 colors and tail refresh should be handled in the LOGS panel" {
  run grep -q 'LOG_TAILOR_RULES' "${constants_file}"
  assert_success

  run grep -q 'LOG_LEVELS = (' "${constants_file}"
  assert_success

  run grep -q 'LOG_LEVELS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q '"monitor_log_level"' "${constants_file}"
  assert_success

  run grep -q 'def colorize_log_output' "${ui_file}"
  assert_success

  run grep -q 'def selected_monitor_log_level' "${ui_file}"
  assert_success

  run grep -q 'def monitor_log_level_label' "${ui_file}"
  assert_success

  run grep -q 'def clear_monitor_log_file' "${ui_file}"
  assert_success

  run grep -q 'def render_monitor_logs_panel' "${ui_file}"
  assert_success

  run grep -q 'def render_log_controls' "${ui_file}"
  assert_success

  run grep -q 'def toggle_monitor_logs_tail' "${ui_file}"
  assert_success

  run grep -q 'selected_log, selected_level, tail_enabled = render_table_controls_panel(' "${ui_file}"
  assert_success

  run grep -q 'render_log_controls' "${ui_file}"
  assert_success

  run grep -q 'st.container(key="monitor_log_controls")' "${ui_file}"
  assert_success

  run grep -q '\[0.42, 1.0, 0.52, 1.0, 0.16, 0.16\], vertical_alignment="center"' "${ui_file}"
  assert_success

  run grep -q 'Log file:' "${ui_file}"
  assert_success

  run grep -q 'Log level:' "${ui_file}"
  assert_success

  run grep -q 'key="monitor_logs_tail_button"' "${ui_file}"
  assert_success

  run grep -q '"" if tail_enabled_value else ""' "${ui_file}"
  assert_success

  run grep -q 'tail_enabled_value = st.checkbox' "${ui_file}"
  assert_failure

  run grep -q 'on_click=toggle_monitor_logs_tail' "${ui_file}"
  assert_success

  run grep -q 'key="monitor_log_clear_button"' "${ui_file}"
  assert_success

  run grep -q 'key="monitor_log_level"' "${ui_file}"
  assert_success

  run grep -q '__hhs logs' "${ui_file}"
  assert_success

  run grep -q 'shlex.quote(safe_log_level)' "${ui_file}"
  assert_success

  run grep -q 'run_hhs_logs(selected_log, 200, selected_level)' "${ui_file}"
  assert_success

  run grep -Fq 'awk -v level="${level}" '\''toupper($3) == level'\''' "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/functions/built-ins.bash"
  assert_success

  run grep -q 'grep -i "${level}"' "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/functions/built-ins.bash"
  assert_failure

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

  run grep -q '.st-key-monitor_log_clear_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-monitor_logs_tail_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-monitor_log_controls \[data-testid="stHorizontalBlock"\]' "${css_file}"
  assert_success

  run grep -q 'gap: var(--hhs-element-std-gap) !important' "${css_file}"
  assert_success

  run grep -q 'flex-wrap: nowrap !important' "${css_file}"
  assert_success

  run grep -q '.st-key-monitor_log_controls \[data-testid="stHorizontalBlock"\] > div\[data-testid="stColumn"\]:nth-child(1)' "${css_file}"
  assert_success

  run grep -q '.st-key-monitor_log_controls \[data-testid="stHorizontalBlock"\] > div\[data-testid="stColumn"\]:nth-child(3)' "${css_file}"
  assert_success

  run grep -q 'min-width: max-content' "${css_file}"
  assert_success

  run grep -q 'flex: 1 1 0 !important' "${css_file}"
  assert_success

  run grep -q '.st-key-monitor_log_controls \[data-testid="stHorizontalBlock"\] > div\[data-testid="stColumn"\]:nth-child(5)' "${css_file}"
  assert_success

  run grep -q 'flex: 0 0 2rem !important' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-chrome-height: 8.5rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-height: 230px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-height: calc(100dvh - var(--hhs-log-chrome-height) - var(--hhs-footer-guard-height) - var(--hhs-log-expander-height))' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-max-height: calc(var(--hhs-ttyd-max-height, 760px) - var(--hhs-log-expander-height))' "${css_file}"
  assert_success

  run grep -q 'height: var(--hhs-log-height)' "${css_file}"
  assert_success

  run grep -q 'max-height: min(var(--hhs-log-height), var(--hhs-log-max-height))' "${css_file}"
  assert_success

  run grep -q 'min-height: 280px' "${css_file}"
  assert_success

  run grep -q '@st.fragment(run_every="5s")' "${ui_file}"
  assert_success

  run grep -q 'white-space: pre' "${css_file}"
  assert_success

  run grep -q 'margin: 0.55rem 0 var(--hhs-element-std-gap)' "${css_file}"
  assert_success

  run grep -q '.hhs-log-output' "${css_file}"
  assert_success

  run grep -q 'margin: 0;' "${css_file}"
  assert_success
}

# TC - 18
@test "when rendering configs then current command-backed tables and filters should be wired" {
  run grep -q '__hhs_envs' "${ui_file}"
  assert_success

  run grep -q '__hhs_paths' "${ui_file}"
  assert_success

  run grep -q '__hhs_load_dir -l' "${ui_file}"
  assert_success

  run grep -q '__hhs_command -l' "${ui_file}"
  assert_success

  run grep -q '__hhs_aliases' "${ui_file}"
  assert_success

  run grep -q 'def render_env_rows' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_env_action_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_env_action' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_path_action_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_path_action' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_dir_action_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_dir_action' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_command_action_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_command_action' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_alias_action_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_alias_action' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_shopt_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_shopt_setup_command' "${ui_file}"
  assert_success

  run grep -q '\[\[ ! -s "${HHS_SHOPTS_FILE}" \]\]' "${ui_file}"
  assert_success

  run grep -q 'awk.*print \$1.*=.*\$2' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_shopt_load_saved_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_shopt_action_command' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_shopt' "${ui_file}"
  assert_success

  run grep -q 'def run_hhs_shopt_action' "${ui_file}"
  assert_success

  run grep -q 'def parse_hhs_shopt' "${ui_file}"
  assert_success

  run grep -q 'SHOPT_DESCRIPTIONS = {' "${ui_file}"
  assert_success

  run grep -q '"cdspell": "Corrects minor spelling errors in directory names used with cd."' "${ui_file}"
  assert_success

  run grep -q 'def shopt_description' "${ui_file}"
  assert_success

  run grep -q '"Description": shopt_description(match.group(3).strip())' "${ui_file}"
  assert_success

  run grep -q 'headers=\["Status", "Option", "Description"\]' "${ui_file}"
  assert_success

  run grep -q 'SHOPT_LINE_PATTERN = re.compile' "${constants_file}"
  assert_success

  run grep -q 'def filter_shopt_rows' "${ui_file}"
  assert_success

  run grep -q 'def apply_home_shopt_action' "${ui_file}"
  assert_success

  run grep -q 'def refresh_home_shopts_listing' "${ui_file}"
  assert_success

  run grep -q 'f"__hhs_shopt {action} {shlex.quote(option_name)}"' "${ui_file}"
  assert_success

  run grep -q 'build_hhs_shopt_load_saved_command()' "${ui_file}"
  assert_success

  run grep -q '__hhs_shopt -p' "${ui_file}"
  assert_success

  run grep -q 'shopt -s "${option}" 2>/dev/null || true' "${ui_file}"
  assert_success

  run grep -q 'shopt -u "${option}" 2>/dev/null || true' "${ui_file}"
  assert_success

  run grep -q '"Status": shopt_status_value(state)' "${ui_file}"
  assert_success

  run grep -q 'action_buttons=\[' "${ui_file}"
  assert_success

  run grep -q '"label": " Turn ON"' "${ui_file}"
  assert_success

  run grep -q '"label": " Turn OFF"' "${ui_file}"
  assert_success

  run grep -q 'action_column_weights=\[1, 1\]' "${ui_file}"
  assert_success

  run grep -q 'f"__hhs_paths {action_args}"' "${ui_file}"
  assert_success

  run grep -q 'action_args = f"-a {safe_path}"' "${ui_file}"
  assert_success

  run grep -q 'action_args = f"-r {safe_path}"' "${ui_file}"
  assert_success

  run grep -q 'f"__hhs_save_dir {action_args}"' "${ui_file}"
  assert_success

  run grep -q 'f"__hhs_command {action_args}"' "${ui_file}"
  assert_success

  run grep -q 'f"__hhs_aliases {action_args}"' "${ui_file}"
  assert_success

  run grep -q -- "-a {shlex.quote(f'{name}={value}')}" "${ui_file}"
  assert_success

  run grep -q 'safe_path = shlex.quote(path_value)' "${ui_file}"
  assert_success

  run grep -q 'action_args = f"{shlex.quote(value)} {safe_name}"' "${ui_file}"
  assert_success

  run grep -q 'action_args = f"-a {safe_name} {shlex.quote(value)}"' "${ui_file}"
  assert_success

  run grep -q 'f"-r {safe_name}" if operation == "del" else f"{safe_name} {shlex.quote(value)}"' "${ui_file}"
  assert_success

  run grep -q 'apply_selected_env_value(name, str(st.session_state.get(editor_key, "")))' "${ui_file}"
  assert_success

  run grep -q -- '--del {safe_name}' "${ui_file}"
  assert_success

  run grep -q 'apply_env_add_form_value' "${ui_file}"
  assert_success

  run grep -q 'with st.form(f"{key_prefix}_add_form", border=False)' "${ui_file}"
  assert_success

  run grep -q 'st.form_submit_button(' "${ui_file}"
  assert_success

  run grep -q 'key=f"{key_prefix}_add_submit"' "${ui_file}"
  assert_success

  run grep -q 'env_add_button' "${ui_file}"
  assert_failure

  run grep -q '"Custom Variable"' "${ui_file}"
  assert_success

  run grep -q 'def render_path_add_controls' "${ui_file}"
  assert_success

  run grep -q 'def render_dir_add_controls' "${ui_file}"
  assert_success

  run grep -q 'def request_folder_picker' "${ui_file}"
  assert_success

  run grep -q 'def apply_folder_picker_selection' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["_hhs_folder_picker_selected_dir"\] = child_directories\[0\]' "${ui_file}"
  assert_success

  run grep -q 'st.container(key="folder_picker_action_grid")' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q '"ﰸ"' "${ui_file}"
  assert_success

  run grep -q '" Parent"' "${ui_file}"
  assert_failure

  run grep -q '"label": " Select"' "${ui_file}"
  assert_failure

  run grep -q 'buttons=()' "${ui_file}"
  assert_success

  run grep -q '.st-key-folder_picker_select_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-folder_picker_action_grid,' "${css_file}"
  assert_success

  run grep -q '.st-key-folder_picker_action_grid \[data-testid="stVerticalBlock"\]' "${css_file}"
  assert_success

  run grep -q 'grid-auto-flow: column' "${css_file}"
  assert_success

  run grep -q 'grid-template-columns: repeat(4, 2rem)' "${css_file}"
  assert_success

  run grep -q 'min-width: 2rem' "${css_file}"
  assert_success

  run grep -q 'justify-content: center' "${css_file}"
  assert_success

  run grep -q '"Include .dot-folders"' "${ui_file}"
  assert_success

  run grep -q '_hhs_folder_picker_include_dot_folders' "${ui_file}"
  assert_success

  run grep -q 'include_dot_folders or not path.name.startswith(".")' "${ui_file}"
  assert_success

  run grep -q '_hhs_folder_picker_on_select' "${ui_file}"
  assert_failure

  run grep -q 'key=f"{key_prefix}_folder_picker_button"' "${ui_file}"
  assert_success

  run grep -q 'name_col, value_col, _spacer_col, folder_col = st.columns(' "${ui_file}"
  assert_success

  run grep -q '\[1.25, 4.05, 0.012, 0.15\], vertical_alignment="center"' "${ui_file}"
  assert_success

  run grep -q 'value_group_col.columns(' "${ui_file}"
  assert_failure

  run grep -q '\[1, 0.012, 0.035\], vertical_alignment="center"' "${ui_file}"
  assert_failure

  run grep -q 'value_group_col = st.columns' "${ui_file}"
  assert_failure

  run grep -q 'args=(f"{key_prefix}_add_value", value_placeholder)' "${ui_file}"
  assert_success

  run grep -q 'def render_cmd_add_controls' "${ui_file}"
  assert_success

  run grep -q 'def render_alias_add_controls' "${ui_file}"
  assert_success

  run grep -q 'render_table_controls_panel(render_env_controls)' "${ui_file}"
  assert_success

  run grep -q 'render_table_controls_panel(render_path_controls)' "${ui_file}"
  assert_success

  run grep -q 'render_table_controls_panel(render_dir_controls)' "${ui_file}"
  assert_success

  run grep -q 'render_table_controls_panel(render_cmd_controls)' "${ui_file}"
  assert_success

  run grep -q 'render_table_controls_panel(render_alias_controls)' "${ui_file}"
  assert_success

  run grep -q 'render_table_filter_controls' "${ui_file}"
  assert_success

  run grep -q 'status_message = clean_command_status_message(' "${ui_file}"
  assert_success

  run grep -q 'env_action_message' "${ui_file}"
  assert_failure

  run grep -q '""' "${ui_file}"
  assert_failure

  run grep -q 'on_click": apply_env_delete' "${ui_file}"
  assert_success

  run grep -q '"glyph": ""' "${ui_file}"
  assert_success

  run grep -q 'def render_path_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_dir_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_cmd_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_alias_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_dirs_table' "${ui_file}"
  assert_success

  run grep -q 'def render_cmds_table' "${ui_file}"
  assert_success

  run grep -q 'def render_aliases_table' "${ui_file}"
  assert_success

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
    body = source.split(f"def {function_name}", 1)[1].split("\ndef ", 1)[0]
    assert "st.error(" not in body, function_name
    assert "if result.returncode != 0:" not in body, function_name
    assert "if result.returncode == 0 else []" in body, function_name
PY
  assert_success

  run grep -q 'selected_editable=True' "${ui_file}"
  assert_success

  run grep -q 'selected_edit_key=lambda row, _index: env_value_editor_key(row\["Name"\])' "${ui_file}"
  assert_success

  run grep -q 'selected_edit_key=lambda _row, index: path_value_editor_key(index)' "${ui_file}"
  assert_success

  run grep -q 'selected_edit_key=lambda _row, index: dir_value_editor_key(index)' "${ui_file}"
  assert_success

  run grep -q 'selected_edit_folder_picker=True' "${ui_file}"
  assert_success

  run grep -q 'selected_edit_key=lambda _row, index: cmd_value_editor_key(index)' "${ui_file}"
  assert_success

  run grep -q 'selected_edit_key=lambda _row, index: alias_value_editor_key(index)' "${ui_file}"
  assert_success

  run grep -q 'on_click": apply_path_delete' "${ui_file}"
  assert_success

  run grep -q 'on_click": apply_dir_delete' "${ui_file}"
  assert_success

  run grep -q 'on_click": apply_cmd_delete' "${ui_file}"
  assert_success

  run grep -q 'on_click": apply_alias_delete' "${ui_file}"
  assert_success

  run grep -q 'selected_value: Callable\[\[dict\[str, str\], int\], str\] | None = None' "${ui_file}"
  assert_success

  run grep -q 'selected_value=lambda row, _index: row.get("Value", "")' "${ui_file}"
  assert_success

  run python3 - <<'PY'
import ast
from pathlib import Path

tree = ast.parse(Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())
functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
required_refresh_calls = {
    "execute_pending_ai_model_selection": "refresh_ai_model_listing",
    "execute_pending_ai_model_deletion": "refresh_ai_model_listing",
    "apply_selected_env_value": "refresh_env_listing",
    "apply_env_delete": "refresh_env_listing",
    "apply_selected_path_value": "refresh_path_listing",
    "apply_path_delete": "refresh_path_listing",
    "apply_selected_dir_value": "refresh_dir_listing",
    "apply_dir_delete": "refresh_dir_listing",
    "apply_selected_cmd_value": "refresh_cmd_listing",
    "apply_cmd_delete": "refresh_cmd_listing",
    "apply_selected_alias_value": "refresh_alias_listing",
    "apply_alias_delete": "refresh_alias_listing",
    "apply_home_shopt_action": "refresh_home_shopts_listing",
    "execute_pending_home_tool_action": "refresh_home_tools_listing",
    "apply_selected_service_action": "refresh_service_listing",
    "apply_selected_process_kill": "refresh_process_listing",
}
for function_name, refresh_name in required_refresh_calls.items():
    function = functions[function_name]
    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == refresh_name
        for node in ast.walk(function)
    ):
        raise SystemExit(f"{function_name} should call {refresh_name}")

required_add_success_clears = {
    "apply_env_add_form_value": ("apply_selected_env_value", "clear_add_form_fields"),
    "apply_path_add_form_value": ("apply_selected_path_value", "clear_add_form_fields"),
    "apply_dir_add_form_value": ("apply_selected_dir_value", "clear_add_form_fields"),
    "apply_cmd_add_form_value": ("apply_selected_cmd_value", "clear_add_form_fields"),
    "apply_alias_add_form_value": ("apply_selected_alias_value", "clear_add_form_fields"),
}
for function_name, (apply_name, clear_name) in required_add_success_clears.items():
    function = functions[function_name]
    if not any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Call)
        and isinstance(node.test.func, ast.Name)
        and node.test.func.id == apply_name
        and any(
            isinstance(body_node, ast.Call)
            and isinstance(body_node.func, ast.Name)
            and body_node.func.id == clear_name
            for body_node in ast.walk(ast.Module(body=node.body, type_ignores=[]))
        )
        for node in ast.walk(function)
    ):
        raise SystemExit(f"{function_name} should clear fields after {apply_name} succeeds")

required_delete_command_fragments = {
    "build_hhs_env_action_command": "--del {safe_name}",
    "build_hhs_path_action_command": "-r {safe_path}",
    "build_hhs_dir_action_command": "-r {safe_name}",
    "build_hhs_command_action_command": "-r {safe_name}",
    "build_hhs_alias_action_command": "-r {safe_name}",
}
source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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
  run grep -q 'message = strip_ansi(result.stdout).strip() or "No directories recorded yet"' "${ui_file}"
  assert_success

  run grep -q 'st.info(message)' "${ui_file}"
  assert_success
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

@test "when rendering table rows then path values are visually abbreviated with env vars" {
  run python3 - "${ui_file}" <<'PY'
import os
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def env_path_aliases()")
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

@test "when selecting table rows then command overlays should be suppressed" {
  run python3 - "${ui_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def table_selection_key_prefixes()")
end = source.index("def render_table(")
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
exec("from __future__ import annotations\n" + source[start:end], namespace)

assert namespace["table_selection_widget_key"]("env_vars_table_0") is True
assert namespace["table_selection_widget_key"]("unrelated") is False
assert namespace["table_selection_rows"]({"selection": {"rows": [2]}}) == (2,)
assert namespace["table_selection_rerun_in_progress"]() is True
namespace["remember_table_selection"]("env_vars_table_0", {"selection": {"rows": [2]}})
assert namespace["table_selection_rerun_in_progress"]() is False

snapshot_start = source.index("def command_result_snapshots()")
snapshot_end = source.index("def cache_set(")
snapshot_namespace = {
    "st": SimpleNamespace(session_state={}),
    "hhs_ui_constants": SimpleNamespace(
        COMMAND_RESULT_SNAPSHOT_KEY="_hhs_command_result_snapshots",
        COMMAND_RESULT_SNAPSHOT_LIMIT=2,
    ),
    "safe_cache_tag": lambda value: value,
}
exec("from __future__ import annotations\n" + source[snapshot_start:snapshot_end], snapshot_namespace)
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

@test "when parsing footer working directory then startup banners should be ignored" {
  run python3 - "${ui_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def parse_footer_working_directory_output(")
end = source.index("def footer_working_directory(")
namespace = {
    "strip_ansi": lambda value: re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value),
}
exec(source[start:end], namespace)

noisy_output = (
    "[bash] HomeSetup is starting...\r\n"
    "[Linux-ubuntu/bash] Welcome root to HomeSetup v1.9.18\r\n"
    "__HHS_UI_PWD__/root\r\n"
)
assert namespace["parse_footer_working_directory_output"](noisy_output) == "/root"
assert namespace["parse_footer_working_directory_output"]("banner only") == ""
PY
  assert_success
}

@test "when rendering footer working directory then local cwd should not issue pwd" {
  run python3 - "${ui_file}" <<'PY'
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def footer_working_directory(")
end = source.index("def run_hhs_updater_check(")
session_state = {}
namespace = {
    "hhs_ui_constants": SimpleNamespace(
        FOOTER_LOCAL_WORKING_DIR_KEY="_hhs_footer_local_working_dir",
        FOOTER_REMOTE_WORKING_DIR_KEY="_hhs_footer_remote_working_dir",
    ),
    "sync_ttyd_event_state": lambda: None,
    "st": SimpleNamespace(session_state=session_state),
    "os": SimpleNamespace(getcwd=lambda: "/local/cwd"),
}
exec(source[start:end], namespace)

assert namespace["footer_working_directory"]() == "/local/cwd"
session_state["_hhs_footer_local_working_dir"] = "/terminal/local"
assert namespace["footer_working_directory"]() == "/terminal/local"
session_state["ssh_connection_status"] = "connected"
assert namespace["footer_working_directory"]() == "/local/cwd"
session_state["_hhs_footer_remote_working_dir"] = "/remote/cwd"
assert namespace["footer_working_directory"]() == "/remote/cwd"
PY
  assert_success
}

@test "when checking updates then updater should refresh installed version from .VERSION" {
  local updater_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/updater/updater.bash"

  run grep -q 'refresh_hhs_version' "${updater_file}"
  assert_success

  run grep -q 'HHS_VERSION="$(grep -m 1 . "${version_file}")"' "${updater_file}"
  assert_success

  run grep -q 'export HHS_VERSION' "${updater_file}"
  assert_success

  run grep -q 'cmd="$1"' "${updater_file}"
  assert_success

  run grep -q 'refresh_hhs_version' "${updater_file}"
  assert_success

  run grep -q 'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")";' "${ui_file}"
  assert_success

  run grep -q 'run_hhs_envs("^HHS_VERSION$", refresh_cache=refresh_cache)' "${ui_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("footer_hhs_version_cache_loaded", False)' "${ui_file}"
  assert_success
}

@test "when parsing Docker command output then tables should preserve columns" {
  run python3 - "${ui_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def escape_markdown_table_cell(")
end = source.index("def command_env(")
namespace = {"re": re, "strip_ansi": lambda value: value}
exec(source[start:end], namespace)

sample = (
    "CONTAINER ID   IMAGE                          COMMAND                  CREATED      STATUS       PORTS                    NAMES\n"
    "f9eae755ef6e   yorevs/homeselect:ui-0.0.7.6   \"/docker-entrypoint\"   2 days ago   Up 2 days    127.0.0.1:8888->80/tcp   homeselect-webapp\n"
)

rows = namespace["docker_cli_table_rows"](sample)
assert rows == [
    {
        "CONTAINER ID": "f9eae755ef6e",
        "IMAGE": "yorevs/homeselect:ui-0.0.7.6",
        "COMMAND": "\"/docker-entrypoint\"",
        "CREATED": "2 days ago",
        "STATUS": "Up 2 days",
        "PORTS": "127.0.0.1:8888->80/tcp",
        "NAMES": "homeselect-webapp",
    }
]
containers_rows = namespace["docker_cli_table_rows"](
    sample, omitted_columns=("COMMAND", "PORTS")
)
assert containers_rows == [
    {
        "CONTAINER ID": "f9eae755ef6e",
        "IMAGE": "yorevs/homeselect:ui-0.0.7.6",
        "CREATED": "2 days ago",
        "STATUS": "Up 2 days",
        "NAMES": "homeselect-webapp",
    }
]
assert namespace["docker_container_is_up"](containers_rows[0]) is True
assert namespace["docker_container_is_up"]({"STATUS": "Exited (0) 2 hours ago"}) is False
remote_output = (
    "[bash] HomeSetup is starting...\n"
    "[Linux-ubuntu/bash] Welcome root to HomeSetup v1.9.18\n"
    + sample
)
remote_rows = namespace["docker_cli_table_rows"](
    remote_output, omitted_columns=("COMMAND", "PORTS")
)
assert remote_rows[0]["NAMES"] == "homeselect-webapp"
image_sample = (
    "REPOSITORY            TAG          IMAGE ID       CREATED       SIZE\n"
    "yorevs/homeselect     api-0.0.7.6  a1b2c3d4e5f6   2 days ago    314MB\n"
)
image_rows = namespace["docker_cli_table_rows"](
    "[bash] HomeSetup is starting...\n"
    "[Linux-ubuntu/bash] Welcome root to HomeSetup v1.9.18\n"
    + image_sample
)
assert image_rows == [
    {
        "REPOSITORY": "yorevs/homeselect",
        "TAG": "api-0.0.7.6",
        "IMAGE ID": "a1b2c3d4e5f6",
        "CREATED": "2 days ago",
        "SIZE": "314MB",
    }
]
formatted_image_sample = (
    "REPOSITORY\tTAG\tIMAGE ID\tSIZE\tCREATED AT\n"
    "yorevs/homeselect\tui-0.0.7.6\tf6b43e69bb9b\t203MB\t2026-06-19 00:21:26 -0300 -03\n"
)
formatted_image_rows = namespace["docker_cli_table_rows"](
    "[bash] HomeSetup is starting...\n" + formatted_image_sample
)
assert formatted_image_rows == [
    {
        "REPOSITORY": "yorevs/homeselect",
        "TAG": "ui-0.0.7.6",
        "IMAGE ID": "f6b43e69bb9b",
        "SIZE": "203MB",
        "CREATED AT": "2026-06-19 00:21:26 -0300 -03",
    }
]
assert namespace["docker_cli_table_rows"]("") == []
PY
  assert_success
}

# TC - 19
@test "when rendering UI then deprecated table approaches should stay removed" {
  run grep -q 'st.data_editor' "${ui_file}"
  assert_failure

  run grep -q 'st.table(' "${ui_file}"
  assert_failure

  run grep -q 'render_env_table_html' "${ui_file}"
  assert_failure

  run grep -q 'hhs-env-table-scroll' "${css_file}"
  assert_failure

  run grep -q '<style>' "${css_file}"
  assert_failure
}
