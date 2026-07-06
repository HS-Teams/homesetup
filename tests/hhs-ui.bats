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

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
clear_body = source.split("def clear_disconnected_ssh_host", 1)[1].split("\ndef ", 1)[0]
assert "queue_search_directory_home_reset()" in clear_body
assert "reset_search_directory_to_home()" not in clear_body
assert "def apply_pending_search_directory_home_reset" in source
main_body = source.split("def main(", 1)[1].split('\n\nif __name__ == "__main__":', 1)[0]
pending_reset_index = main_body.index("apply_pending_search_directory_home_reset()")
initialize_search_index = main_body.index("initialize_search_directory_home_default()")
render_main_index = main_body.index("render_main_view()")
assert pending_reset_index < initialize_search_index < render_main_index
PY
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
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def remote_command_startup_line_is_noise(")
end = source.index("def ssh_output_is_only_shared_close(")
namespace = {
    "re": re,
    "subprocess": subprocess,
    "strip_ansi": lambda value: value,
    "homesetup_home": lambda: Path(".").resolve(),
    "lru_cache": lru_cache,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

motd_fragments = namespace["homesetup_motd_fragment_groups"]()[0]
hhs_version = os.environ.get("HHS_VERSION") or Path(".VERSION").read_text(encoding="utf-8").strip()
rendered_motd = f"[Linux-ubuntu/bash] {' root '.join(motd_fragments)} v{hhs_version} "
assert namespace["remote_command_motd_line_is_boundary"](
    rendered_motd
)
ubuntu_motd = """Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-134-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Sun Jul  5 01:47:39 -03 2026

  System load:  0.02               Processes:             128
  Usage of /:   35.4% of 32.86GB   Users logged in:       0
  Memory usage: 48%                IPv4 address for eth0: 167.99.120.81
  Swap usage:   43%                IPv4 address for eth0: 10.17.0.5

Expanded Security Maintenance for Applications is not enabled.

1 update can be applied immediately.
To see these additional updates run: apt list --upgradable

4 additional security updates can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm


"""
noisy_stdout = (
    "[bash] HomeSetup is starting...\n"
    "dynamic shell setup output\n"
    "\n"
    f"{ubuntu_motd}"
    f"{rendered_motd}\n"
    "\n"
    "GNU bash, version 5.2.21(1)-release\n"
)
noisy_stderr = "Shell option expand_aliases set to on\nreal error\n"
result = subprocess.CompletedProcess(["cmd"], 0, noisy_stdout, noisy_stderr)
remote = namespace["sanitize_remote_command_result"]("remote-host", result)
assert remote.stdout == "GNU bash, version 5.2.21(1)-release\n"
assert remote.stderr == "real error\n"
assert "Welcome to Ubuntu" not in remote.stdout
assert "Expanded Security Maintenance" not in remote.stdout

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
        VIEWS=("Home", "Configs", "Services", "SSH", "History", "Monitor", "AI"),
    ),
    "st": SimpleNamespace(session_state=session_state),
    "activate_terminal_document_view": lambda: activated.append(True),
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["restore_terminal_document_view"](False)
assert session_state == {}
assert activated == []

session_state["active_view"] = "Monitor"
session_state["document_previous_view"] = "SSH"
namespace["restore_terminal_document_view"](True)
assert session_state["document_view_active"] is True
assert session_state["document_previous_view"] == "SSH"
assert session_state["document_selected"] == "TERMINAL"
assert activated == [True]

session_state["document_previous_view"] = "Missing"
namespace["restore_terminal_document_view"](True)
assert session_state["document_previous_view"] == "Home"
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

  run grep -q 'UI_COMMAND_LOCAL_TIMEOUT_SECONDS = 30' "${constants_file}"
  assert_success

  run grep -q 'UI_COMMAND_REMOTE_TIMEOUT_SECONDS = 60' "${constants_file}"
  assert_success

  run grep -q 'UI_COMMAND_DEFAULT_TIMEOUT_SECONDS = UI_COMMAND_LOCAL_TIMEOUT_SECONDS' "${constants_file}"
  assert_success

  run grep -q '"search_query"' "${constants_file}"
  assert_failure

  run grep -q '"search_directories"' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_TERM_HISTORY_CACHE_KEY = "search_terms:history"' "${constants_file}"
  assert_success

  run grep -q '"search_ignore_case"' "${constants_file}"
  assert_success

  run grep -q '"search_words"' "${constants_file}"
  assert_success

  run grep -q '"search_binary"' "${constants_file}"
  assert_success

  run grep -q '"search_result_query"' "${constants_file}"
  assert_failure

  run grep -q '"search_result_path"' "${constants_file}"
  assert_failure

  run grep -q '"search_result_type"' "${constants_file}"
  assert_failure

  run python3 - <<'PY'
import ast
import types
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
assert 'f"{remote_status_markup}{shell_controls_markup}"' in ui_source
assert "{status_group_markup}" in footer_template
assert "st.html(" in ui_source
assert 'class="hhs-footer-glyph"></span>' in ui_source
assert 'Connected to remote  {connected_host_display}' in ui_source
assert 'os.environ.get("HHS_GITHUB_URL", "#")' in ui_source
homesetup_version_body = ui_source.split("def homesetup_version", 1)[1].split("\ndef ", 1)[0]
assert 'run_hhs_envs("^HHS_VERSION$", refresh_cache=refresh_cache)' in homesetup_version_body
assert 'st.session_state["footer_hhs_version_cache_loaded"] = True' in homesetup_version_body
assert 'parse_rows_cached("env", result.stdout, parse_hhs_envs)' in homesetup_version_body
assert 'complete_cached_background_command(' in homesetup_version_body
assert 'cached_background_command_result(command, "env")' in homesetup_version_body
assert 'hhs_ui.VERSION' not in homesetup_version_body
constants_source = Path("bin/apps/py/hhs_ui/constants.py").read_text()
init_source = Path("bin/apps/py/hhs_ui/__init__.py").read_text()
assert 'FOOTER_OPEN_WORKING_DIR_QUERY_PARAM = "hhs_open_working_dir"' in constants_source
assert 'FOOTER_RUN_UPDATER_QUERY_PARAM = "hhs_run_updater_update"' in constants_source
assert 'FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM = "hhs_show_shell_version"' in constants_source
assert 'FOOTER_CLEAR_CACHE_QUERY_PARAM = "hhs_clear_cache"' in constants_source
assert 'FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM = "hhs_clear_application_cache"' in constants_source
assert 'FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM = "hhs_clear_application_states"' in constants_source
assert 'FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM = "hhs_clear_ai_history"' in constants_source
assert 'FOOTER_SHOW_SHELL_VERSION_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_CACHE_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM' in init_source
assert 'FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM' in init_source
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
assert 'class="hhs-footer-shell-group"' in ui_source
assert 'def footer_cache_clear_menu_markup' in ui_source
assert 'def render_footer_cache_clear_menu_script' in ui_source
assert '<details class="hhs-footer-cache-clear-menu">' in ui_source
assert '<summary class="hhs-footer-cache-clear-trigger"' in ui_source
assert '<form class="hhs-footer-cache-clear-form" method="get">' in ui_source
assert '<button type="submit">OK</button>' in ui_source
assert 'form.querySelector(\'input[type="checkbox"]:checked\')' in ui_source
assert 'event.preventDefault()' in ui_source
assert 'menu.removeAttribute("open")' in ui_source
assert 'render_footer_cache_clear_menu_script()' in ui_source
assert 'href="{cache_clear_url}"' not in ui_source
assert 'key="footer_cache_clear_button"' not in ui_source
assert 'on_click=open_footer_cache_clear_menu' not in ui_source
assert 'f\'<span class="hhs-footer-glyph"></span>\'' in ui_source
assert '<span class="hhs-footer-cache-refresh-glyph">♻</span>' in ui_source
assert '<a class="hhs-footer-cache-clear-button" href="{cache_clear_url}"' not in ui_source
assert '<span class="hhs-footer-glyph"></span><span class="hhs-footer-cache-refresh-glyph">♻</span></a>' not in ui_source
assert 'def render_footer_cache_clear_menu(' not in ui_source
assert 'st.container(key="footer_cache_clear_menu")' not in ui_source
assert '>Clear application cache</span>' in ui_source
assert '>Clear application states</span>' in ui_source
assert '>Clear AI history</span>' in ui_source
assert '>OK</button>' in ui_source
assert 'def build_open_directory_command' in ui_source
assert 'def run_open_working_directory' in ui_source
assert 'def open_footer_working_directory' in ui_source
open_footer_working_directory_body = ui_source.split("def open_footer_working_directory", 1)[1].split("\ndef ", 1)[0]
assert 'if connected_ssh_host():' in open_footer_working_directory_body
assert 'st.session_state["active_view"] = hhs_ui.SSH_VIEW' in open_footer_working_directory_body
assert 'st.session_state["ssh_view"] = "FILES"' in open_footer_working_directory_body
assert 'open_remote_explorer_path(working_dir)' in open_footer_working_directory_body
assert 'run_open_working_directory()' in open_footer_working_directory_body
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
handle_footer_actions_body = ui_source.split("def handle_footer_actions", 1)[1].split("\ndef ", 1)[0]
assert "open_footer_working_directory()" in handle_footer_actions_body
footer_working_directory_body = ui_source.split("def footer_working_directory", 1)[1].split("\ndef ", 1)[0]
assert 'run_footer_working_directory()' not in footer_working_directory_body
assert 'hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY' in footer_working_directory_body
assert 'return os.getcwd()' in footer_working_directory_body
assert 'def run_shell_version' in ui_source
assert 'def shell_version_command' in ui_source
assert 'return r"${BASH:-bash} --version"' in ui_source
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
assert 'hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM' in footer_actions_body
assert 'hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM' in footer_actions_body
assert 'remove_footer_cache_clear_query_params()' in footer_actions_body
assert 'apply_footer_cache_clear_options(' in footer_actions_body
assert 'open_footer_cache_clear_menu()' not in footer_actions_body
assert 'clear_cached_ui_data_preserving_state()' not in footer_actions_body
assert 'def cache_delete_command' in ui_source
assert 'cache_delete_command(command, "env")' in ui_source
clear_cache_body = ui_source.split("def clear_cached_ui_data_preserving_state", 1)[1].split("\ndef ", 1)[0]
assert "cache_clear()" in clear_cache_body
assert "st.session_state.clear()" not in clear_cache_body
assert "UI_STATE_FILE" not in clear_cache_body
assert "push_floating_status" in clear_cache_body
apply_cache_options_body = ui_source.split("def apply_footer_cache_clear_options", 1)[1].split("\ndef ", 1)[0]
assert "clear_cached_ui_data_preserving_state(show_status=False)" in apply_cache_options_body
assert "clear_application_state_data()" in apply_cache_options_body
assert "clear_ai_chat_history_data()" in apply_cache_options_body
assert "selected_footer_cleanup_labels(" in apply_cache_options_body
assert "st.rerun()" not in apply_cache_options_body
remove_cache_params_body = ui_source.split("def remove_footer_cache_clear_query_params", 1)[1].split("\ndef ", 1)[0]
assert "hhs_ui.FOOTER_CLEAR_CACHE_QUERY_PARAM" in remove_cache_params_body
assert "hhs_ui.FOOTER_CLEAR_APPLICATION_CACHE_QUERY_PARAM" in remove_cache_params_body
assert "hhs_ui.FOOTER_CLEAR_APPLICATION_STATES_QUERY_PARAM" in remove_cache_params_body
assert "hhs_ui.FOOTER_CLEAR_AI_HISTORY_QUERY_PARAM" in remove_cache_params_body
state_clear_body = ui_source.split("def clear_application_state_data", 1)[1].split("\ndef ", 1)[0]
assert "hhs_ui.UI_STATE_FILE.unlink" in state_clear_body
assert "is_persisted_ui_key" in state_clear_body
assert 'def updater_output_has_updates' in ui_source
assert 'def updater_check_due' in ui_source
assert 'def updater_check_context' in ui_source
assert 'def restore_local_updater_status' in ui_source
assert 'def reset_updater_remote_check_state' in ui_source
assert 'def start_updater_check' in ui_source
assert 'def store_updater_check_result' in ui_source
assert 'def execute_due_updater_check' in ui_source
assert 'execute_due_updater_check()' in ui_source
constants_source = Path("bin/apps/py/hhs_ui/constants.py").read_text()
assert "UPDATER_CHECK_INTERVAL_SECONDS = 24 * 60 * 60" in constants_source
store_updater_body = ui_source.split("def store_updater_check_result", 1)[1].split("\ndef ", 1)[0]
assert 'context: str = "local"' in store_updater_body
assert 'st.session_state["updater_check_started_context"] = ""' in store_updater_body
assert 'st.session_state["updater_check_context"] = context' in store_updater_body
assert 'st.session_state["updater_last_check_epoch"] = time.time()' in store_updater_body
assert 'st.session_state["updater_last_check_output"] = output' in store_updater_body
assert 'result.returncode == 0 and updater_output_has_updates(output)' in store_updater_body
assert 'if context == "local":' in store_updater_body
assert 'st.session_state["updater_remote_checked_context"] = context' in store_updater_body
assert 'save_ui_state()' in store_updater_body
execute_updater_body = ui_source.split("def execute_due_updater_check", 1)[1].split("\ndef ", 1)[0]
assert 'current_context = updater_check_context()' in execute_updater_body
assert 'restore_local_updater_status()' in execute_updater_body
assert 'updater_remote_checked_context' in execute_updater_body
assert 'start_updater_check(current_context, force_local=False)' in execute_updater_body
assert 'start_updater_check("local", force_local=True)' in execute_updater_body
start_updater_body = ui_source.split("def start_updater_check", 1)[1].split("\ndef ", 1)[0]
assert 'metadata={"updater_context": context}' in start_updater_body
assert 'st.session_state["updater_check_started_context"] = context' in start_updater_body
reset_updater_body = ui_source.split("def reset_updater_remote_check_state", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["updater_check_started_context"] = ""' in reset_updater_body
assert 'st.session_state["updater_remote_checked_context"] = ""' in reset_updater_body
assert 'st.session_state["updater_check_context"] = ""' in reset_updater_body
assert 'st.session_state["updater_update_available"] = False' in reset_updater_body
assert '__hhs updater execute "{safe_operation}"' in ui_source
assert 'export HHS_VERSION="$(grep -m 1 . "${HHS_HOME}/.VERSION" 2>/dev/null || printf "%s" "${HHS_VERSION}")";' in ui_source
assert 'printf "y\\\\n" | ' in ui_source
assert 'def handle_footer_actions' in ui_source
assert 'force_local=not bool(connected_ssh_host())' in footer_actions_body
assert 'metadata={"updater_context": updater_check_context()}' in footer_actions_body
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
shell_group_block = re.search(r"\.hhs-footer-shell-group\s*\{([^}]*)\}", base_css).group(1)
cache_menu_block = re.search(r"\.hhs-footer-cache-clear-menu\s*\{([^}]*)\}", base_css).group(1)
cache_trigger_block = re.search(r"\.hhs-footer-cache-clear-trigger\s*\{([^}]*)\}", base_css).group(1)
cache_form_block = re.search(r"^\.hhs-footer-cache-clear-form\s*\{([^}]*)\}", base_css, re.M).group(1)
cache_form_label_block = re.search(r"\.hhs-footer-cache-clear-form label\s*\{([^}]*)\}", base_css).group(1)
cache_form_checkbox_block = re.search(r"\.hhs-footer-cache-clear-form input\[type=\"checkbox\"\]\s*\{([^}]*)\}", base_css).group(1)
cache_form_button_block = re.search(r"\.hhs-footer-cache-clear-form button\s*\{([^}]*)\}", base_css).group(1)
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
assert ".hhs-footer-shell-group" in base_css
assert ".hhs-footer-cache-clear-menu" in base_css
assert ".hhs-footer-cache-clear-trigger" in base_css
assert ".hhs-footer-cache-clear-form" in base_css
assert ".st-key-footer_cache_clear_button" not in base_css
assert ".hhs-footer-remote-status" in base_css
assert ".hhs-footer-status-group" in base_css
assert ".hhs-footer-repository-link:hover" in base_css
assert ".hhs-footer-working-dir-link:hover" in base_css
assert ".hhs-footer-shell-status:hover" in base_css
assert ".hhs-footer-shell-name" in base_css
assert "text-decoration: none !important" in shell_name_block
assert "text-decoration: underline !important" in shell_name_hover_block
assert "text-decoration: underline" not in shell_status_hover_block
assert "gap: var(--hhs-element-std-gap)" in shell_group_block
assert "font-size: 0.68rem" in cache_menu_block
assert "height: 1.18rem" in cache_menu_block
assert "position: relative" in cache_menu_block
assert "cursor: pointer" in cache_trigger_block
assert "height: 1.18rem" in cache_trigger_block
assert "list-style: none" in cache_trigger_block
assert "padding: 0 0.12rem" in cache_trigger_block
assert ".hhs-footer-cache-refresh-glyph" in base_css
assert "font-size: 2.5em" in base_css
assert ".hhs-footer-cache-clear-button" not in base_css
assert ".hhs-footer-cache-clear-trigger:hover" in base_css
assert "bottom: calc(var(--hhs-footer-guard-height) + 0.7rem)" in base_css
assert "right: 1rem" in base_css
assert "background: var(--hhs-theme-secondary-background-color)" in cache_form_block
assert "box-shadow: 0 1rem 2rem" in cache_form_block
assert "gap: var(--hhs-element-std-gap)" in cache_form_block
assert "position: fixed" in cache_form_block
assert "width: min(22rem, calc(100vw - 2rem)) !important" in cache_form_block
assert "width: 100%" in cache_form_label_block
assert "min-height: 2.25rem" in cache_form_label_block
assert "accent-color: var(--hhs-theme-primary-color)" in cache_form_checkbox_block
assert "height: 1rem" in cache_form_checkbox_block
assert "background: transparent" in cache_form_button_block
assert "height: 2.25rem" in cache_form_button_block
assert "width: 100%" in cache_form_button_block
assert ".hhs-footer-cache-clear-form label:hover" in base_css
assert ".hhs-footer-cache-clear-form button:hover" in base_css
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
assert ".st-key-ssh_view" in base_css
assert ".st-key-ai_view" in base_css
assert "margin-top: 0 !important" in view_key_block
assert "padding-top: 0 !important" in view_key_block
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-active_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-home_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ssh_view)' in base_css
assert '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.st-key-ai_view)' in base_css
assert '.st-key-home_view [data-baseweb="button-group"]' in base_css
assert '.st-key-ssh_view [data-baseweb="button-group"]' in base_css
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
assert "--hhs-modal-scrim-z-index: 1000001" in base_css
assert "--hhs-modal-z-index: 1000002" in base_css
assert "--hhs-command-overlay-z-index: 1000010" in base_css
assert '[data-testid="stDialog"][data-baseweb="modal"]' in base_css
assert '[data-testid="stDialog"][data-baseweb="modal"] > div' in base_css
assert '[data-testid="stDialog"][data-baseweb="modal"] [role="dialog"]' in base_css
assert "min-height: 100dvh !important" in base_css
assert 'body:has(div[role="dialog"]) .hhs-app-footer' in base_css
assert 'body:has([data-testid="stDialog"][data-baseweb="modal"]) .hhs-app-footer' in base_css
assert 'body:has(div[role="dialog"]) .hhs-sidebar-clock' in base_css
assert "z-index: calc(var(--hhs-modal-scrim-z-index) - 1) !important" in base_css
assert "z-index: var(--hhs-modal-z-index) !important" in base_css
assert "z-index: var(--hhs-command-overlay-z-index)" in base_css
main_body = ui_source.split("def main()", 1)[1].split('if __name__ == "__main__"', 1)[0]
assert main_body.index("render_footer()") < main_body.index("render_floating_status()")
assert main_body.index("render_floating_status()") < main_body.index("render_folder_picker_dialog()")
assert main_body.index("render_folder_picker_dialog()") < main_body.index("render_browser_cleanup_script()")
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
    streamlit.session_state["search_directories"] = ["/tmp", "/var"]
    streamlit.session_state["search_query"] = "admin"
    streamlit.session_state["search_result_query"] = "admin"
    streamlit.session_state["search_result_path"] = "/tmp"
    streamlit.session_state["search_result_type"] = "Strings"
    ui.save_ui_state()
    saved_state = json.loads(ui.hhs_ui.UI_STATE_FILE.read_text(encoding="utf-8"))
    assert saved_state["theme_selected"] == "tokyo-night"
    assert saved_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] is True
    assert saved_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] == "TERMINAL"
    assert saved_state[ui.hhs_ui.DOCUMENT_PREVIOUS_VIEW_KEY] == "Home"
    assert saved_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] == "homeserver"
    assert saved_state["search_directories"] == ["/tmp", "/var"]
    assert "search_query" not in saved_state
    assert "search_result_query" not in saved_state
    assert "search_result_path" not in saved_state
    assert "search_result_type" not in saved_state

    streamlit.session_state.clear()
    ui.restore_ui_state()
    assert streamlit.session_state["theme_selected"] == "tokyo-night"
    assert streamlit.session_state[ui.hhs_ui.DOCUMENT_VIEW_ACTIVE_KEY] is True
    assert streamlit.session_state[ui.hhs_ui.DOCUMENT_SELECTED_KEY] == "TERMINAL"
    assert streamlit.session_state[ui.hhs_ui.SSH_RECONNECT_HOST_KEY] == "homeserver"
    assert streamlit.session_state["search_directories"] == ["/tmp", "/var"]
    assert "search_query" not in streamlit.session_state
    assert "search_result_query" not in streamlit.session_state
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
  run grep -q 'VIEWS = ("Home", "Configs", "Services", "Monitor", "Search", "History")' "${constants_file}"
  assert_success

  run grep -q 'AI_VIEW = "AI"' "${constants_file}"
  assert_success

  run grep -q 'SSH_VIEW = "SSH"' "${constants_file}"
  assert_success

  run grep -q 'SSH_VIEWS = ("TUNNELS", "FILES")' "${constants_file}"
  assert_success

  run grep -q '"TUNNELS": " Tunnels"' "${constants_file}"
  assert_success

  run grep -q '"FILES": " Explorer"' "${constants_file}"
  assert_success

  run grep -q 'SSH_TUNNEL_FILTERS = ("All", "Reachable", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_FILTERS = ("All", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'HISTORY_FILTERS = ("All", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'ENV_FILTERS = ("All", "HHS", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'LIST_FILTERS = ("All", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_PAGE_SIZE = 20' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_SUBMIT_PRELOADER_DELAY_MS = 700' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_DIRECTORY_HISTORY_LIMIT = 20' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_TERM_HISTORY_LIMIT = 20' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_TERM_HISTORY_CACHE_KEY = "search_terms:history"' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_TERM_HISTORY_TTL_SECONDS = UI_CACHE_LOW_CHANGE_TTL_SECONDS' "${constants_file}"
  assert_success

  run grep -q 'SSH_EXPLORER_COMPONENT_DIR = APP_DIR / "components/ssh_explorer"' "${constants_file}"
  assert_success

  run grep -q '"ssh_view"' "${constants_file}"
  assert_success

  run grep -q '"ssh_explorer_local_path"' "${constants_file}"
  assert_success

  run grep -q '"ssh_explorer_remote_path"' "${constants_file}"
  assert_success

  run grep -q '"ssh_tunnel_filter"' "${constants_file}"
  assert_success

  run grep -q '"ssh_tunnel_other_filter"' "${constants_file}"
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

  run grep -q '"Search": " Search"' "${constants_file}"
  assert_success

  run grep -q '"History": " History"' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_TYPES = ("Files", "Folders", "Strings")' "${constants_file}"
  assert_success

  run grep -q 'SEARCH_FILTERS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
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

  run grep -q '<h2> Search</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> History</h2>' "${ui_file}"
  assert_success

  run grep -q '<h2> Remote Connection</h2>' "${ui_file}"
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

  run grep -q 'def docker_agent_failure_message' "${ui_file}"
  assert_success

  run grep -q 'def docker_agent_is_running' "${ui_file}"
  assert_success

  run grep -q 'def build_docker_agent_check_command' "${ui_file}"
  assert_success

  run grep -q 'Docker agent is not running' "${ui_file}"
  assert_success

  run grep -q 'Docker command timedout' "${ui_file}"
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

  run grep -q 'return "docker ps -q >/dev/null 2>&1"' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
for function_name in ("run_docker_ps", "run_docker_images"):
    body = source.split(f"def {function_name}", 1)[1].split("\ndef ", 1)[0]
    assert "use_cache=False" not in body, function_name
agent_body = source.split("def docker_agent_is_running", 1)[1].split("\ndef ", 1)[0]
assert "use_cache=False" not in agent_body
assert "show_overlay=False" not in agent_body
docker_body = source.split("def render_home_docker_panel", 1)[1].split("\ndef ", 1)[0]
assert "command_timeout_seconds()" in docker_body
assert "docker_agent_failure_message(agent_result)" in docker_body
required_index = docker_body.index("render_docker_agent_required_view(")
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

  run grep -q 'HOME_TOOLS_FILTERS = ("All", "Installed", "Not Installed", "Aliased", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'HOME_TOOLS_FILTERS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'hhs_ui.HOME_TOOLS_FILTERS' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.FIVE_OPTION_FILTER_COLUMNS' "${ui_file}"
  assert_success

  run grep -q 'home_tool_is_installed(row)' "${ui_file}"
  assert_success

  run grep -q 'home_tool_is_not_found(row)' "${ui_file}"
  assert_success

  run grep -q '"home_tools_other_filter"' "${ui_file}"
  assert_success

  run grep -q 'SHOPTS_FILTERS = ("All", "ON", "OFF", "Containing")' "${constants_file}"
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

  run grep -q 'FIVE_OPTION_FILTER_COLUMNS = \[2.75, 1.25\]' "${constants_file}"
  assert_success

  run grep -q 'FIVE_OPTION_FILTER_COLUMNS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
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

  run grep -q 'div\[data-testid="stHorizontalBlock"\]:has(.st-key-home_tools_filter)' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stHorizontalBlock"\]:has(.st-key-ssh_tunnel_filter)' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stHorizontalBlock"\]:has(.st-key-ssh_tunnel_other_filter)' "${css_file}"
  assert_success

  run grep -q 'div\[data-testid="stHorizontalBlock"\]:has(.st-key-ssh_tunnel_filter) > div\[data-testid="stColumn"\]:first-child' "${css_file}"
  assert_success

  run grep -q '.st-key-ssh_tunnel_filter \[role="radiogroup"\]' "${css_file}"
  assert_failure

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

  run grep -q 'elif active_view == "Search":' "${ui_file}"
  assert_success

  run grep -q 'render_search_view()' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_search_command' "${ui_file}"
  assert_success

  run grep -q 'def parse_hhs_search_results' "${ui_file}"
  assert_success

  run grep -q 'def render_search_controls' "${ui_file}"
  assert_success

  run grep -q 'placeholder="Search for files, folders, or strings"' "${ui_file}"
  assert_success

  run grep -q 'key="search_path"' "${ui_file}"
  assert_success

  run grep -q 'key="search_path_folder_picker_button"' "${ui_file}"
  assert_success

  run grep -q 'on_click=request_path_picker' "${ui_file}"
  assert_success

  run grep -q 'args=("search_path", st.session_state.get("search_path", ""), "folder")' "${ui_file}"
  assert_success

  run grep -q 'st.container(key="search_controls")' "${ui_file}"
  assert_success

  run grep -q 'with st.expander("Search", expanded=True):' "${ui_file}"
  assert_success

  run grep -q 'st.container(key="search_results")' "${ui_file}"
  assert_success

  run grep -q 'def render_search_filters' "${ui_file}"
  assert_success

  run grep -q 'st.container(key="search_filter_controls")' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.SEARCH_FILTERS' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("def render_search_filters", 1)[1].split("\ndef ", 1)[0]
assert "render_table_filter_controls" not in body
assert "[1.15, 3.0, 0.22, 0.22, 0.22, 0.22]" in body
assert 'vertical_alignment="center"' in body
assert "key=\"search_filter\"" in body
assert "key=\"search_other_filter\"" in body
assert 'render_search_option_toggle(\n                "search_ignore_case", "Aa", "Ignore case (-i)"' in body
assert 'render_search_option_toggle("search_words", "", "Match words (-w)")' in body
assert 'render_search_option_toggle("search_binary", "", "Search binary files (-b)")' in body
assert "key=\"search_other_filter_clear\"" in body
assert "width=\"stretch\"" in body
PY
  assert_success

  run grep -q '"search_filter",' "${ui_file}"
  assert_success

  run grep -q '"search_other_filter",' "${ui_file}"
  assert_success

  run grep -q 'options=hhs_ui_constants.SEARCH_TYPES' "${ui_file}"
  assert_success

  run grep -q 'st.columns(' "${ui_file}"
  assert_success

  run grep -q '\[1.15, 3.0, 3.0, 0.22, 0.22\], vertical_alignment="bottom"' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("def render_search_controls", 1)[1].split("\ndef ", 1)[0]
assert '[1.15, 3.0, 3.0, 0.22, 0.22], vertical_alignment="bottom"' in body
assert (
    '"Kind",\n'
    '                options=hhs_ui_constants.SEARCH_TYPES,\n'
    '                key="search_type",'
) in body
assert (
    '"Search terms",\n'
    '                options=search_term_options(),\n'
    '                index=None,\n'
    '                key="search_query",\n'
    '                placeholder="Search for files, folders, or strings",\n'
    '                accept_new_options=True,\n'
    '                on_change=submit_search_query,\n'
    '                width="stretch",'
) in body
assert (
    '"Search directory",\n'
    '                options=search_directory_options(),\n'
    '                key="search_path",\n'
    '                accept_new_options=True,\n'
    '                on_change=apply_search_directory_change,\n'
    '                width="stretch",'
) in body
assert 'st.text_input(\n                "Search terms"' not in body
assert 'st.text_input(\n                "Search directory"' not in body
assert 'label_visibility="collapsed"' not in body
assert body.index('key="search_path_folder_picker_button"') < body.index(
    'key="search_submit_button"'
)
assert "render_search_submit_preloader_script()" in body
PY
  assert_success

  run grep -q '\[5.0, 0.85\], vertical_alignment="center"' "${ui_file}"
  assert_failure

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q 'if st.button("Search", key="search_submit_button"' "${ui_file}"
  assert_failure

  run grep -q 'def render_search_submit_preloader_script' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsSearchSubmitPreloaderCleanup' "${ui_file}"
  assert_success

  run grep -q 'const buttonSelector = ".st-key-search_submit_button button"' "${ui_file}"
  assert_success

  run grep -q "const querySelector = \".st-key-search_query \\[role='combobox'\\], .st-key-search_query input\"" "${ui_file}"
  assert_success

  run grep -q "const pathSelector = \".st-key-search_path \\[role='combobox'\\], .st-key-search_path input\"" "${ui_file}"
  assert_success

  run grep -q 'delay_ms = int(hhs_ui_constants.SEARCH_SUBMIT_PRELOADER_DELAY_MS)' "${ui_file}"
  assert_success

  run grep -q 'const delayMs = ' "${ui_file}"
  assert_success

  run grep -q 'const clearPendingSearchOverlay = ()' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsSearchSubmitPreloaderDelayTimer' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.setTimeout(' "${ui_file}"
  assert_success

  run grep -q 'showOverlay(query, searchPath)' "${ui_file}"
  assert_success

  run grep -q 'doc.addEventListener("click", onClick, true)' "${ui_file}"
  assert_success

  run grep -q 'doc.addEventListener("keydown", onKeydown, true)' "${ui_file}"
  assert_success

  run grep -q 'event.key === "Enter"' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("def render_combobox_vt100_shortcuts_script", 1)[1].split("\ndef ", 1)[0]
assert "parentWindow.__hhsComboboxVt100Cleanup" in body
assert 'node.closest(\'[data-baseweb="select"]\')' in body
assert "event.ctrlKey || event.metaKey" in body
assert 'case "a":' in body
assert 'case "e":' in body
assert 'case "b":' in body
assert 'case "f":' in body
assert 'case "d":' in body
assert 'case "h":' in body
assert 'case "k":' in body
assert 'case "u":' in body
assert 'case "w":' in body
assert "setCaret(node, 0, state.value.length)" in body
assert "setCaret(node, state.value.length, state.value.length)" in body
assert 'replaceRange(node, state.start, state.value.length, "", "deleteContentForward")' in body
assert 'doc.addEventListener("keydown", onKeydown, true)' in body
assert "render_combobox_vt100_shortcuts_script()" in source
PY
  assert_success

  run grep -q 'event.target.closest(".st-key-search_path")' "${ui_file}"
  assert_failure

  run grep -q 'label.append("Searching for ", queryNode, " in ", pathNode)' "${ui_file}"
  assert_success

  run grep -q 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-search.bash";' "${ui_file}"
  assert_success

  run grep -q 'def search_loader_message' "${ui_file}"
  assert_success

  run grep -q 'search_loader_message(query, search_path)' "${ui_file}"
  assert_success

  run grep -q 'Searching for %primary_color%{query}%primary_color%' "${ui_file}"
  assert_success

  run grep -q 'in %secondary_color%{search_path}%secondary_color%' "${ui_file}"
  assert_success

  run grep -q 'timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS' "${ui_file}"
  assert_success

  run grep -q 'show_overlay=False' "${ui_file}"
  assert_success

  run grep -q 'clear_preloader()' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_open_search_result_command' "${ui_file}"
  assert_success

  run grep -q 'def open_search_result_path' "${ui_file}"
  assert_success

  run grep -q '__hhs_open' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM' "${ui_file}"
  assert_success

  run grep -q 'search_result_path_link(row)' "${ui_file}"
  assert_success

  run grep -q 'render_search_path_results(rows)' "${ui_file}"
  assert_failure

  run grep -q 'render_search_path_results(visible_rows, search_type, total_count)' "${ui_file}"
  assert_success

  run grep -q 'def visible_search_rows' "${ui_file}"
  assert_success

  run grep -q 'def render_search_load_more' "${ui_file}"
  assert_success

  run grep -q 'if visible_count >= total_count:' "${ui_file}"
  assert_success

  run grep -q 'def render_search_auto_load_more' "${ui_file}"
  assert_success

  run grep -q 'def render_search_auto_load_more_cleanup' "${ui_file}"
  assert_success

  run grep -q 'render_search_auto_load_more_cleanup()' "${ui_file}"
  assert_success

  run grep -q 'key="search_load_more_button"' "${ui_file}"
  assert_success

  run grep -q 'render_search_auto_load_more(displayed_count, total_count)' "${ui_file}"
  assert_success

  run grep -q 'const buttonSelector = ".st-key-search_load_more_button button";' "${ui_file}"
  assert_success

  run grep -q 'const renderToken = ' "${ui_file}"
  assert_success

  run grep -q 'const loadingMarkup = `' "${ui_file}"
  assert_success

  run grep -q 'hhs-search-load-more-preloader-spinner" aria-hidden="true"><' "${ui_file}"
  assert_success

  run grep -q 'Loading more results...' "${ui_file}"
  assert_success

  run grep -q 'button.innerHTML = loadingMarkup' "${ui_file}"
  assert_success

  run grep -q 'let requested = false;' "${ui_file}"
  assert_success

  run grep -q 'let userReachedBottom = false;' "${ui_file}"
  assert_success

  run grep -q 'activeController.displayedCount > displayedCount' "${ui_file}"
  assert_success

  run grep -q 'button.dataset.hhsAutoLoadRequested' "${ui_file}"
  assert_failure

  run grep -q 'const componentFrame = window.frameElement' "${ui_file}"
  assert_success

  run grep -q 'const loadMoreContainer = doc.querySelector(".st-key-search_load_more")' "${ui_file}"
  assert_success

  run grep -q 'const sentinel = loadMoreContainer || componentFrame' "${ui_file}"
  assert_success

  run grep -q 'const bottomThreshold = 12;' "${ui_file}"
  assert_success

  run grep -q 'target.getBoundingClientRect' "${ui_file}"
  assert_success

  run grep -q 'rect.top <= viewportHeight - bottomThreshold' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.IntersectionObserver' "${ui_file}"
  assert_success

  run grep -q 'observer.observe(sentinel)' "${ui_file}"
  assert_success

  run grep -q 'rootMargin: "0px", threshold: 0.25' "${ui_file}"
  assert_success

  run grep -q 'scrollTargets.forEach((target)' "${ui_file}"
  assert_success

  run grep -q 'button.click()' "${ui_file}"
  assert_success

  run grep -q 'userReachedBottom = nearBottom()' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsSearchAutoLoadController' "${ui_file}"
  assert_success

  run grep -q 'delete parentWindow.__hhsSearchAutoLoadController' "${ui_file}"
  assert_success

  run grep -q 'pageHeight - 120' "${ui_file}"
  assert_failure

  run grep -q 'f"Load more results ({displayed_count}/{total_count}) ..."' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui_constants.SEARCH_PAGE_SIZE' "${ui_file}"
  assert_success

  run grep -q 'cache_delete_tag("search")' "${ui_file}"
  assert_success

  run grep -q 'ttl_seconds=hhs_ui.UI_CACHE_NORMAL_TTL_SECONDS' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
submit_body = source.split("def submit_search_query", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["search_result_ignore_case"] = bool(' in submit_body
assert 'st.session_state.get("search_ignore_case", False)' in submit_body
assert 'st.session_state["search_result_words"] = bool(' in submit_body
assert 'st.session_state.get("search_words", False)' in submit_body
assert 'st.session_state["search_result_binary"] = bool(' in submit_body
assert 'st.session_state.get("search_binary", False)' in submit_body

results_body = source.split("def render_search_results", 1)[1].split("\ndef ", 1)[0]
assert (
    "build_hhs_search_command(\n"
    "            search_type, query, search_path, ignore_case, words, binary"
) in results_body
assert (
    "search_command_cache_key(\n"
    "            search_type, query, search_path, ignore_case, words, binary"
) in results_body
PY
  assert_success

  run grep -q 'render_search_string_results(rows, query, text_filter)' "${ui_file}"
  assert_failure

  run grep -q 'render_search_string_results(visible_rows, query, text_filter, total_count)' "${ui_file}"
  assert_success

  run grep -q '<th>Path</th><th>Line</th><th>Match</th></tr></thead>' "${ui_file}"
  assert_success

  run grep -q 'return \["Path", "Size", "Modified"\]' "${ui_file}"
  assert_success

  run grep -q 'return \["Path", "Modified"\]' "${ui_file}"
  assert_success

  run grep -q '__hhs_search_file' "${ui_file}"
  assert_success

  run grep -q '__hhs_search_dir' "${ui_file}"
  assert_success

  run grep -q '__hhs_search_string' "${ui_file}"
  assert_success

  run grep -q 'SSH_TUNNEL_TABLE_KEY = "ssh_tunnel_table"' "${constants_file}"
  assert_success

  run grep -q 'SSH_EXPLORER_COMPONENT_DIR' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'SSH_EXPLORER_LOCAL_TABLE_KEY' "${constants_file}"
  assert_failure

  run grep -q 'SSH_EXPLORER_REMOTE_TABLE_KEY' "${constants_file}"
  assert_failure

  run grep -q 'SSH_EXPLORER_LOCAL_TABLE_KEY' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_failure

  run grep -q 'SSH_EXPLORER_REMOTE_TABLE_KEY' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_failure

  run grep -q 'st.session_state.setdefault("ssh_view", "TUNNELS")' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["ssh_view"\] not in hhs_ui.SSH_VIEWS' "${ui_file}"
  assert_success

  run grep -q 'SSH_VIEW_LABELS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'SSH_VIEWS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
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

  run grep -q 'def scroll_to_table_selection_content' "${ui_file}"
  assert_success

  run grep -q 'table_selected_bottom_' "${ui_file}"
  assert_success

  run grep -q 'scroll_to_table_selection_content(anchor_key)' "${ui_file}"
  assert_success

  run grep -q 'target.scrollIntoView' "${ui_file}"
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

  run grep -q '.st-key-search_path_folder_picker_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_submit_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_load_more_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_load_more {' "${css_file}"
  assert_success

  run grep -q '.hhs-search-load-more-preloader' "${css_file}"
  assert_success

  run grep -q '.hhs-search-load-more-preloader-spinner' "${css_file}"
  assert_success

  run grep -q 'animation: hhs-search-load-more-spin 0.8s linear infinite' "${css_file}"
  assert_success

  run grep -q '@keyframes hhs-search-load-more-spin' "${css_file}"
  assert_success

  run grep -q '.hhs-search-load-more-preloader-track' "${css_file}"
  assert_failure

  run grep -q 'hhs-search-load-more-slide' "${css_file}"
  assert_failure

  run grep -q '.st-key-search_other_filter_clear button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_ignore_case_toggle_idle button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_ignore_case_toggle_selected button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_words_toggle_idle button' "${css_file}"
  assert_success

  run grep -q '.st-key-search_binary_toggle_selected button' "${css_file}"
  assert_success

  run grep -q 'box-shadow: inset 0 0 0 1px var(--hhs-theme-primary-color)' "${css_file}"
  assert_success

  run grep -q '.st-key-search_submit_button {' "${css_file}"
  assert_success

  run grep -q '.st-key-search_controls \[data-testid="stVerticalBlock"\]' "${css_file}"
  assert_success

  run grep -q '.st-key-search_controls \[data-testid="stHorizontalBlock"\]' "${css_file}"
  assert_success

  run grep -q 'align-items: end' "${css_file}"
  assert_success

  run grep -q '> div\[data-testid="stColumn"\]:nth-child(4)' "${css_file}"
  assert_success

  run grep -q '> div\[data-testid="stColumn"\]:nth-child(5)' "${css_file}"
  assert_success

  run grep -q 'margin-bottom: 0.28rem' "${css_file}"
  assert_success

  run grep -q '.st-key-search_filter_controls \[data-testid="stHorizontalBlock"\]' "${css_file}"
  assert_success

  run grep -q 'grid-template-columns: minmax(9rem, 1.15fr)' "${css_file}"
  assert_success

  run grep -q 'grid-template-columns: max-content minmax(0, 1fr) 2rem 2rem 2rem 2rem' "${css_file}"
  assert_success

  run grep -q 'grid-column: 2' "${css_file}"
  assert_success

  run grep -q '.st-key-search_filter_controls \[role="radiogroup"\]\[aria-label$="filter"\]' "${css_file}"
  assert_success

  run grep -q 'overflow-x: visible' "${css_file}"
  assert_success

  run grep -q '.st-key-search_controls {' "${css_file}"
  assert_success

  run grep -q 'margin-top: var(--hhs-element-std-gap) !important' "${css_file}"
  assert_success

  run grep -q '.st-key-search_results {' "${css_file}"
  assert_success

  run grep -q '.hhs-search-results' "${css_file}"
  assert_success

  run grep -q '.hhs-search-result-path-link' "${css_file}"
  assert_success

  run grep -q '.hhs-search-result-index' "${css_file}"
  assert_success

  run grep -q 'min-width: 1ch' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-theme-secondary-background-color)' "${css_file}"
  assert_success

  run grep -q 'border: 1px solid var(--hhs-theme-dataframe-border-color)' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-theme-dataframe-header-background-color)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-primary)' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-theme-link-color)' "${css_file}"
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

  run grep -q 'def normalized_history_stats_top_n' "${ui_file}"
  assert_success

  run grep -q 'DEFAULT_TOP_N = 10' "${constants_file}"
  assert_success

  run grep -q 'MIN_TOP_N = 1' "${constants_file}"
  assert_success

  run grep -q 'MAX_TOP_N = 100' "${constants_file}"
  assert_success

  run grep -q 'def normalized_monitor_top_n' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["history_stats_top_n"\] = normalized_history_stats_top_n' "${ui_file}"
  assert_success

  run grep -q 'min_value=hhs_ui_constants.MIN_TOP_N' "${ui_file}"
  assert_success

  run grep -q 'max_value=hhs_ui_constants.MAX_TOP_N' "${ui_file}"
  assert_success

  run grep -q '"monitor_cpu_top_n"' "${constants_file}"
  assert_success

  run grep -q '"monitor_mem_top_n"' "${constants_file}"
  assert_success

  run grep -q 'def monitor_disk_directory_for_host' "${ui_file}"
  assert_success

  run grep -q 'def synchronize_monitor_disk_directory_with_host' "${ui_file}"
  assert_success

  run grep -q '"ssh_files"' "${ui_file}"
  assert_success

  run grep -q 'return 10' "${ui_file}"
  assert_success

  run grep -q 'key="monitor_disk_top_n_input"' "${ui_file}"
  assert_success

  run grep -q 'on_change=handle_monitor_disk_top_n_change' "${ui_file}"
  assert_success

  run grep -q 'def monitor_process_top_n_state_key' "${ui_file}"
  assert_success

  run grep -q 'def handle_monitor_process_top_n_change' "${ui_file}"
  assert_success

  run grep -q 'on_change=handle_monitor_process_top_n_change' "${ui_file}"
  assert_success

  run grep -q 'on_click=apply_monitor_process_controls' "${ui_file}"
  assert_success

  run grep -q 'for metric in ("CPU", "MEM"):' "${ui_file}"
  assert_success

  run grep -q 'build_process_monitor_command(metric, normalized_monitor_process_top_n(metric))' "${ui_file}"
  assert_success

  run grep -q 'process_monitor_chart_rows(result.stdout, metric, applied_top_n)' "${ui_file}"
  assert_success

  run grep -q 'Top {applied_top_n} {title} processes' "${ui_file}"
  assert_success

  run grep -q 'def process_monitor_chart_rows' "${ui_file}"
  assert_success

  run grep -q 'top -b -n 2 -d 1 -o {linux_sort} -w 512' "${ui_file}"
  assert_success

  run grep -q 'No CPU usage above 0.0% found.' "${ui_file}"
  assert_success

  run grep -q 'SERVICE_FILTERS = ("All", "Up", "Down", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'PATH_FILTERS = ("All", "Shell", "Private", "Custom", "Containing")' "${constants_file}"
  assert_success

  run python3 - <<'PY'
import ast
import os
import re
import shlex
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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

  run python3 - <<'PY'
import ast
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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

  run python3 - <<'PY'
import ast
import re
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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
  run grep -q 'DEFAULT_TOP_N = 10' "${constants_file}"
  assert_success

  run grep -q 'MIN_TOP_N = 1' "${constants_file}"
  assert_success

  run grep -q 'MAX_TOP_N = 100' "${constants_file}"
  assert_success

  run python3 - <<'PY'
import ast
import types
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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
) < history_body.index("st.number_input(")
assert source.count("min_value=hhs_ui_constants.MIN_TOP_N") >= 3
assert source.count("max_value=hhs_ui_constants.MAX_TOP_N") >= 3
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
start_body = source.split("def execute_pending_ssh_connection", 1)[1].split("\ndef ", 1)[0]
complete_body = source.split("def complete_ssh_connection", 1)[1].split("\ndef ", 1)[0]
body = f"{start_body}\n{complete_body}"
snapshot_index = body.index("was_terminal_active = terminal_document_view_is_active()")
reset_index = body.index("clear_host_scoped_session_state()")
status_index = body.index('st.session_state["ssh_connection_status"] = "connected"')
remote_cwd_index = body.index("update_remote_footer_working_directory()")
restore_index = body.index("restore_terminal_document_view(was_terminal_active)")
availability_refresh_index = complete_body.index(
    "schedule_ollama_service_availability_refresh()"
)
assert snapshot_index < reset_index
assert reset_index < status_index
assert status_index < remote_cwd_index < restore_index
assert complete_body.index("register_ssh_connection(host)") < availability_refresh_index
assert availability_refresh_index < complete_body.index("save_ui_state()")
assert "set_overlay(True" not in body
assert "set_overlay(False" not in body
assert "show_overlay=False" not in body
assert "cache_clear()" in source.split("def clear_host_scoped_session_state", 1)[1].split("\ndef ", 1)[0]
assert "cache_clear()" in source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state.pop("ssh_reconnect_restore_view_state", False)' in body
assert "reset_updater_remote_check_state()" in complete_body
assert "reconnect_view_state_snapshot()" in body
assert "restore_reconnect_view_state(reconnect_state)" in body
assert '"ssh_view"' in source.split("def reconnect_view_state_snapshot", 1)[1].split("\ndef ", 1)[0]
assert '"ssh_explorer_local_path"' in source.split("def reconnect_view_state_snapshot", 1)[1].split("\ndef ", 1)[0]
assert '"ssh_explorer_remote_path"' in source.split("def reconnect_view_state_snapshot", 1)[1].split("\ndef ", 1)[0]
restore_reconnect_index = body.index("restore_reconnect_view_state(reconnect_state)")
assert reset_index < restore_reconnect_index < status_index
disconnect_body = source.split("def execute_pending_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
assert "st.session_state.pop(hhs_ui_constants.FOOTER_REMOTE_WORKING_DIR_KEY, None)" in disconnect_body
assert 'st.session_state[hhs_ui.SSH_RECONNECT_HOST_KEY] = ""' in disconnect_body
clear_disconnect_body = source.split("def clear_completed_ssh_disconnection", 1)[1].split("\ndef ", 1)[0]
disconnect_snapshot_index = clear_disconnect_body.index("disconnect_view_state = reconnect_view_state_snapshot()")
disconnect_reset_index = clear_disconnect_body.index("clear_host_scoped_session_state()")
disconnect_restore_index = clear_disconnect_body.index("restore_reconnect_view_state(disconnect_view_state)")
disconnect_availability_refresh_index = clear_disconnect_body.index(
    "schedule_ollama_service_availability_refresh()"
)
assert disconnect_snapshot_index < disconnect_reset_index < disconnect_restore_index
assert clear_disconnect_body.index("cache_clear()") < disconnect_availability_refresh_index
assert disconnect_availability_refresh_index < clear_disconnect_body.index("save_ui_state()")
restore_body = source.split("def restore_registered_ssh_connection_on_session_start", 1)[1].split("\ndef ", 1)[0]
assert "registered_ssh_connection_host() or reconnect_host" in restore_body
assert "clear_disconnected_ssh_host(host)" not in restore_body
assert 'st.session_state["ssh_connect_pending"] = reconnect_host' in restore_body
assert 'st.session_state["ssh_connect_pending_message"] = (' in restore_body
assert 'st.session_state["ssh_reconnect_restore_view_state"] = True' in restore_body
assert "reset_updater_remote_check_state()" in restore_body
restore_registered_snapshot_index = restore_body.index("reconnect_state = reconnect_view_state_snapshot()")
restore_registered_reset_index = restore_body.index("clear_host_scoped_session_state()")
restore_registered_restore_index = restore_body.index("restore_reconnect_view_state(reconnect_state)")
restore_registered_status_index = restore_body.index('st.session_state["ssh_connection_status"] = "connected"')
assert (
    restore_registered_snapshot_index
    < restore_registered_reset_index
    < restore_registered_restore_index
    < restore_registered_status_index
)
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

  run grep -q 'def filter_ssh_tunnel_rows' "${ui_file}"
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

  run grep -q 'on_select: Callable\[\[\], None\] | str = "rerun"' "${ui_file}"
  assert_success

  run grep -q 'st.column_config.LinkColumn' "${ui_file}"
  assert_success

  run grep -F -q 'display_text=r"http://(127\.0\.0\.1:\d+)"' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_view' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_tunnels_panel' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_files_panel' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_row_style' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_entry_is_visible' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_sort_key' "${ui_file}"
  assert_success

  run grep -q 'def synchronize_ssh_explorer_table_selection' "${ui_file}"
  assert_failure

  run grep -q 'def ssh_explorer_component' "${ui_file}"
  assert_success

  run grep -q 'components.declare_component(' "${ui_file}"
  assert_success

  run grep -q 'def handle_ssh_explorer_component_event' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_component_event_paths' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_explorer_component' "${ui_file}"
  assert_success

  run grep -q 'def remote_explorer_parent_path' "${ui_file}"
  assert_success

  run grep -q 'def normalize_local_explorer_path' "${ui_file}"
  assert_success

  run grep -q 'def normalize_remote_explorer_path' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_local_default_path' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_remote_default_path' "${ui_file}"
  assert_success

  run grep -q 'def open_ssh_explorer_parent' "${ui_file}"
  assert_success

  run grep -q 'def refresh_ssh_explorer_paths' "${ui_file}"
  assert_success

  run grep -q 'def set_remote_footer_working_directory' "${ui_file}"
  assert_success

  run grep -q 'def build_recoverable_delete_command' "${ui_file}"
  assert_success

  run grep -q 'def request_ssh_explorer_delete_confirmation' "${ui_file}"
  assert_success

  run grep -q 'def render_ssh_explorer_delete_dialog' "${ui_file}"
  assert_success

  run grep -q 'def create_ssh_explorer_folder' "${ui_file}"
  assert_success

  run grep -q 'def resolve_css_custom_property' "${ui_file}"
  assert_success

  run grep -q 'def ssh_explorer_component_theme' "${ui_file}"
  assert_success

  run grep -q 'def open_ssh_explorer_selection' "${ui_file}"
  assert_success

  run grep -q 'def build_remote_explorer_listing_command' "${ui_file}"
  assert_success

  run grep -q 'def remote_explorer_target_assignment' "${ui_file}"
  assert_success

  run grep -q 'def build_remote_explorer_create_folder_command' "${ui_file}"
  assert_success

  run grep -q 'def parse_remote_explorer_created_dir' "${ui_file}"
  assert_success

  run grep -q 'def parse_remote_explorer_rows' "${ui_file}"
  assert_success

  run grep -q 'def build_scp_to_remote_command' "${ui_file}"
  assert_success

  run grep -q 'def build_scp_to_local_command' "${ui_file}"
  assert_success

  run grep -q 'SSH_FILE_TRANSFER_JOB = "ssh_file_transfer"' "${ui_file}"
  assert_success

  run grep -q '"ssh_files"' "${ui_file}"
  assert_success

  run grep -q 'scp -r' "${ui_file}"
  assert_success

  run grep -q 'Copying local file(s)/folder(s) to remote' "${ui_file}"
  assert_success

  run grep -q 'Copying remote file(s)/folder(s) to local' "${ui_file}"
  assert_success

  run grep -q 'paths = ssh_explorer_component_event_paths(event)' "${ui_file}"
  assert_success

  run grep -q 'ControlPath=' "${ui_file}"
  assert_success

  run grep -q 'ssh_config_option()' "${ui_file}"
  assert_success

  run grep -q 'def ssh_view_label' "${ui_file}"
  assert_success

  run grep -q 'options=hhs_ui.SSH_VIEWS' "${ui_file}"
  assert_success

  run grep -q 'format_func=ssh_view_label' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_view"' "${ui_file}"
  assert_success

  run grep -q 'render_ssh_tunnels_panel(host)' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.SSH_TUNNEL_FILTERS' "${ui_file}"
  assert_success

  run grep -q '"ssh_tunnel_filter"' "${ui_file}"
  assert_success

  run grep -q '"ssh_tunnel_other_filter"' "${ui_file}"
  assert_success

  run grep -q 'filter_ssh_tunnel_rows(rows, tunnel_filter, other_filter)' "${ui_file}"
  assert_success

  run grep -q 'st.session_state.setdefault("ssh_tunnel_filter", "All")' "${ui_file}"
  assert_success

  run grep -q 'render_ssh_files_panel()' "${ui_file}"
  assert_success

  run grep -q 'event = render_ssh_explorer_component(' "${ui_file}"
  assert_success

  run grep -q 'handle_ssh_explorer_component_event(event)' "${ui_file}"
  assert_success

  run grep -q 'if action == "create_folder"' "${ui_file}"
  assert_success

  run grep -q 'if action == "refresh"' "${ui_file}"
  assert_success

  run grep -q 'refresh_ssh_explorer_paths(' "${ui_file}"
  assert_success

  run grep -q 'if action == "delete"' "${ui_file}"
  assert_success

  run grep -q 'request_ssh_explorer_delete_confirmation(' "${ui_file}"
  assert_success

  run grep -q 'st.rerun()' "${ui_file}"
  assert_success

  run grep -q 'key="ssh_explorer_component"' "${ui_file}"
  assert_success

  run grep -q 'localRows=local_rows' "${ui_file}"
  assert_success

  run grep -q 'localLoading=local_loading' "${ui_file}"
  assert_success

  run grep -q 'remoteRows=remote_rows or \[\]' "${ui_file}"
  assert_success

  run grep -q 'remoteLoading=remote_loading' "${ui_file}"
  assert_success

  run grep -q 'loading=explorer_loading' "${ui_file}"
  assert_success

  run grep -q 'explorer_loading = local_loading or remote_loading' "${ui_file}"
  assert_success

  run grep -q 'tableHeight=table_height(hhs_ui.ENV_TABLE_HEIGHT)' "${ui_file}"
  assert_success

  run grep -q 'theme=ssh_explorer_component_theme()' "${ui_file}"
  assert_success

  run grep -q '"ssh_explorer_local_path", ssh_explorer_local_default_path()' "${ui_file}"
  assert_success

  run grep -q '"ssh_explorer_remote_path", ssh_explorer_remote_default_path()' "${ui_file}"
  assert_success

  run grep -q 'selectionHint=False' "${ui_file}"
  assert_success

  run grep -q 'component_height = table_height(hhs_ui.ENV_TABLE_HEIGHT)' "${ui_file}"
  assert_success

  run grep -q 'height=component_height' "${ui_file}"
  assert_success

  run grep -q 'on_select=reset_ssh_explorer_remote_table_selection' "${ui_file}"
  assert_failure

  run grep -q 'on_select=reset_ssh_explorer_local_table_selection' "${ui_file}"
  assert_failure

  run grep -q 'key_prefix": "ssh_explorer_local_open_button"' "${ui_file}"
  assert_failure

  run grep -q 'key_prefix": "ssh_explorer_remote_open_button"' "${ui_file}"
  assert_failure

  run grep -q '.st-key-ssh_explorer_layout' "${css_file}"
  assert_failure

  run grep -q '.st-key-ssh_explorer_component iframe' "${css_file}"
  assert_success

  run grep -q 'background: var(--hhs-background) !important' "${css_file}"
  assert_success

  run grep -q -- '--hhs-ssh-explorer-height: calc(100dvh - var(--hhs-footer-guard-height) - 4.75rem - (var(--hhs-view-gap) \* 3) - 55px)' "${css_file}"
  assert_success

  run grep -q 'height: var(--hhs-ssh-explorer-height) !important' "${css_file}"
  assert_success

  run grep -q 'margin-bottom: var(--hhs-view-gap)' "${css_file}"
  assert_success

  run grep -q 'min-height: 0' "${css_file}"
  assert_success

  run grep -q 'overflow: hidden !important' "${css_file}"
  assert_success

  run grep -F -q 'div:not([class*="st-key-ssh_explorer_component"]):has(iframe[height="0"])' "${css_file}"
  assert_success

  run grep -q '.st-key-ssh_explorer_transfer_controls' "${css_file}"
  assert_failure

  run grep -q '.st-key-ssh_explorer_open_selected button' "${css_file}"
  assert_failure

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run test -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  run cmp -s "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2" "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.woff2"
  assert_success

  run grep -q 'grid-template-columns: minmax(0, 1fr) 3.2rem minmax(0, 1fr)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'height: 100vh' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'flex: 1 1 auto' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q -- '--hhs-panel-bg: color-mix' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'background: var(--hhs-panel-bg)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'overflow-y: auto' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'overflow-y: scroll' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_failure

  run grep -q 'scrollbar-color: var(--hhs-scrollbar)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'scrollbar-gutter: stable' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'padding-right: var(--hhs-scrollbar-size)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '.icon-button:hover:not(:disabled)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'selectionHint: false' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'loading: false' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'localLoading: false' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function explorerIsLoading' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'return Boolean(args.loading || args.localLoading || args.remoteLoading)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function createLoadingState' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_failure

  run grep -q 'app.replaceChildren()' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'Streamlit.setFrameHeight(0)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '.loading-state' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_failure

  run grep -q 'Loading files' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_failure

  run grep -q 'theme: {}' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function applyTheme' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'message.theme' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'themeValues.background || themeValues.backgroundColor' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '"--hhs-primary": themeValues.primary || themeValues.primaryColor' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'border-color: var(--hhs-primary)' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '.panel.active .panel-title' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'let activePanel = "local"' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function activatePanel' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'classList.toggle("active"' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'localBasePath: args.localPath' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'remoteBasePath: args.remotePath' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'sendCommand("parent", activeExplorerPanel(), "")' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'sendCommand("create_folder", activeExplorerPanel(), "")' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'Folder created on local {created_name}' "${ui_file}"
  assert_success

  run grep -q 'Folder created on remote {created_name}' "${ui_file}"
  assert_success

  run grep -q 'Folder ready' "${ui_file}"
  assert_failure

  run python3 - <<'PY'
from pathlib import Path

component = Path("bin/apps/py/hhs_ui/components/ssh_explorer/index.html").read_text(
    encoding="utf-8"
)
controls = component[
    component.index("function createTransferControls") : component.index("function resizeFrame")
]
assert controls.index('""') < controls.index('""') < controls.index('""')
assert controls.index('"﬋"') < controls.index('""')
assert '""' in controls
assert '""' in controls
PY
  assert_success

  run grep -q 'args.selectionHint ? "Select a row to interact" : ""' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function selectRow' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function sendCommand' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'Streamlit.setComponentValue' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '""' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '""' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'sendCommand("refresh", "all", "")' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '""' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '""' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'sendCommand("delete", activeExplorerPanel(), "")' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '""' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '"﬌"' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q '"﬋"' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

component = Path("bin/apps/py/hhs_ui/components/ssh_explorer/index.html").read_text(
    encoding="utf-8"
)
select_body = component[
    component.index("function selectRow") : component.index("function createElement")
]
assert "setComponentValue" not in select_body
assert "sendCommand" not in select_body
assert "activatePanel(panel, false)" in select_body
assert "selectedPanel = panel" in select_body
assert "selectedPaths[panel]" in select_body
assert "paths.add(path)" in select_body
assert "paths.delete(path)" in select_body
assert "render();" in select_body
PY
  assert_success

  run grep -q 'let selectedPaths = {' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function selectedPathList' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'function selectedRows' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -q 'paths,' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -F -q 'Selected: [${rows.map((row) => stringValue(row.Path)).join(", ")}]' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/components/ssh_explorer/index.html"
  assert_success

  run grep -F -q '<p>Connected to remote' "${ui_file}"
  assert_failure

  run grep -q 'key=hhs_ui.SSH_TUNNEL_TABLE_KEY' "${ui_file}"
  assert_success

  run grep -q 'checkbox=False' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
import csv
import hashlib
import os
import posixpath
import re
import shlex
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def split_ssh_command(")
end = source.index("def parse_hhs_history(")
namespace = {
    "csv": csv,
    "datetime": datetime,
    "hashlib": hashlib,
    "hhs_ui": SimpleNamespace(
        PORTS_DEFAULT_FILE=Path("assets/devel/ports-default.csv"),
        THEME_SELECTED_KEY="theme_selected",
    ),
    "lru_cache": lru_cache,
    "Path": Path,
    "posixpath": posixpath,
    "re": re,
    "shlex": shlex,
    "ssh_control_path": lambda host: f"/tmp/{host}.sock",
    "ssh_config_option": lambda: '-F "${HOME}/.ssh/config"',
    "ssh_config_file": lambda: Path.home() / ".ssh" / "config",
    "st": SimpleNamespace(session_state={"theme_selected": "test-theme"}),
    "textwrap": textwrap,
    "row_matches_text_filter": lambda row, text: (
        not text.strip()
        or text.strip().lower()
        in " ".join(str(value).lower() for value in row.values())
    ),
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
filter_rows = [
    {"Bind": "15432", "Destination": "127.0.0.1:5432", "Status": "Reachable"},
    {"Bind": "8080", "Destination": "localhost:80", "Status": "Not reachable"},
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "All") == filter_rows
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Reachable") == []
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "PostgreSQL") == [
    filter_rows[0]
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Other", "http") == [
    filter_rows[1]
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Containing", "http") == [
    filter_rows[1]
]
assert namespace["filter_ssh_tunnel_rows"](filter_rows, "Other", "localhost") == []
assert namespace["ssh_tunnel_kind"]({"Type": "Local", "Destination": "localhost:80"}) == "HTTP"
assert namespace["ssh_tunnel_kind"]({"Type": "Dynamic", "Bind": "127.0.0.1:1080"}) == "SOCKS"

explorer_start = source.index("def ssh_explorer_mtime_text(")
explorer_end = source.index("def render_ssh_view(")
exec("from __future__ import annotations\n" + source[explorer_start:explorer_end], namespace)

assert namespace["remote_explorer_parent_path"]("/home/me/project") == "/home/me"
assert namespace["remote_explorer_parent_path"]("/root") == "/"
assert namespace["remote_explorer_parent_path"]("/") == "/"
assert namespace["remote_explorer_parent_path"](".") == ".."
assert namespace["ssh_explorer_size_text"]("4096", "Dir") == "--"
assert namespace["ssh_explorer_size_text"]("2048", "File") == "2.0 KB"
assert namespace["ssh_explorer_row"](
    "Dir", "project", "4096", "0", "/tmp/project"
)["Size"] == "--"
assert namespace["normalize_remote_explorer_path"](".", "/root") == "/root"
assert namespace["normalize_remote_explorer_path"]("..", "/root") == "/"
assert namespace["normalize_remote_explorer_path"]("alerts", "/root") == "/root/alerts"
local_base = Path.cwd().resolve()
assert namespace["normalize_local_explorer_path"](".", str(local_base)) == str(local_base)
assert namespace["normalize_local_explorer_path"]("..", str(local_base)) == str(local_base.parent)
assert namespace["local_explorer_directory"]("/tmp/hhs-missing-explorer-dir") == Path.home().resolve()
assert namespace["ssh_explorer_local_default_path"]() == str(Path.home().resolve())
assert namespace["ssh_explorer_remote_default_path"]() == "~"
refresh_body = source.split("def refresh_ssh_explorer_paths", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["ssh_explorer_local_path"]' in refresh_body
assert 'st.session_state["ssh_explorer_remote_path"]' in refresh_body
assert 'set_remote_footer_working_directory(normalized_remote_path)' in refresh_body
assert 'cache_delete_tag("ssh_files")' in refresh_body
open_remote_body = source.split("def open_remote_explorer_path", 1)[1].split("\ndef ", 1)[0]
assert 'set_remote_footer_working_directory(normalized_path)' in open_remote_body
remote_rows_body = source.split("def remote_explorer_rows", 1)[1].split("\ndef ", 1)[0]
assert "set_remote_footer_working_directory(resolved_remote_path)" in remote_rows_body
delete_command = namespace["build_recoverable_delete_command"](
    ["/tmp/delete-one.txt", "/tmp/delete two"]
)
assert "gtrash put" in delete_command
assert "trash-put" in delete_command
assert "gio trash" in delete_command
assert "kioclient" in delete_command
assert "${HOME}/.Trash" in delete_command
assert "trash_with_freedesktop" in delete_command
assert "/tmp/delete-one.txt" in delete_command
assert "'/tmp/delete two'" in delete_command
assert namespace["ssh_explorer_delete_message"](
    "remote", ["/srv/app/file.txt", "/srv/app/folder"]
) == "Are you sure you want to delete file.txt, folder?"
target_assignment = namespace["remote_explorer_target_assignment"]("~/project")
assert 'raw_target=' in target_assignment
assert 'target="${HOME:-.}/${raw_target#*/}"' in target_assignment
theme_properties = {
    "hhs-background": "var(--hhs-theme-background-color)",
    "hhs-theme-background-color": "#19181f",
    "hhs-theme-primary-color": "#f1fa8c",
    "hhs-panel": "var(--missing-panel, #14131a)",
}
namespace["theme_custom_properties"] = lambda _theme_name: theme_properties
assert namespace["resolve_css_custom_property"](
    theme_properties, "hhs-background", "#000000"
) == "#19181f"
assert namespace["resolve_css_custom_property"](
    theme_properties, "hhs-panel", "#000000"
) == "#14131a"
theme = namespace["ssh_explorer_component_theme"]()
assert theme["primary"] == "#f1fa8c"

explorer_rows = namespace["parse_remote_explorer_rows"](
    "__HHS_CWD__\t/home/me\n"
    "__HHS_FILE__\tDir\t.\t0\t1710000000\t/home/me/.\n"
    "__HHS_FILE__\tDir\t..\t0\t1710000000\t/home/me/..\n"
    "__HHS_FILE__\tDir\t.hidden\t0\t1710000000\t/home/me/.hidden\n"
    "__HHS_FILE__\tFile\t.env\t100\t1710000000\t/home/me/.env\n"
    "__HHS_FILE__\tFile\tnotes.txt\t2048\t1710000000\t/home/me/notes.txt\n"
)
assert namespace["parse_remote_explorer_cwd"](
    "__HHS_CWD__\t/home/me\n"
) == "/home/me"
assert namespace["ssh_explorer_entry_is_visible"]("src") is True
assert namespace["ssh_explorer_entry_is_visible"](".env") is False
assert namespace["ssh_explorer_entry_is_visible"](".config") is False
sort_rows = [
    {"_kind": "File", "_name": "zeta.txt"},
    {"_kind": "Dir", "_name": "beta"},
    {"_kind": "File", "_name": "alpha.txt"},
    {"_kind": "Dir", "_name": "Alpha"},
]
assert [
    row["_name"] for row in sorted(sort_rows, key=namespace["ssh_explorer_sort_key"])
] == ["Alpha", "beta", "alpha.txt", "zeta.txt"]
dir_style = namespace["ssh_explorer_row_style"]({"Name": " src", "_kind": "Dir"})
file_style = namespace["ssh_explorer_row_style"]({"Name": " notes.txt", "_kind": "File"})
assert all("#38bdf8" in style for style in dir_style)
assert all("font-weight: 800" in style for style in dir_style)
assert all("#ffffff" in style for style in file_style)
assert len(explorer_rows) == 1
assert explorer_rows[0]["Name"].endswith("notes.txt")
assert explorer_rows[0]["_name"] == "notes.txt"
assert explorer_rows[0]["_kind"] == "File"
assert explorer_rows[0]["Size"] == "2.0 KB"
assert explorer_rows[0]["Path"] == "/home/me/notes.txt"
mixed_rows = namespace["parse_remote_explorer_rows"](
    "__HHS_FILE__\tFile\tzeta.txt\t1\t1710000000\t/home/me/zeta.txt\n"
    "__HHS_FILE__\tDir\tbeta\t0\t1710000000\t/home/me/beta\n"
    "__HHS_FILE__\tFile\talpha.txt\t1\t1710000000\t/home/me/alpha.txt\n"
    "__HHS_FILE__\tDir\tAlpha\t0\t1710000000\t/home/me/Alpha\n"
)
assert [row["_name"] for row in mixed_rows] == [
    "Alpha",
    "beta",
    "alpha.txt",
    "zeta.txt",
]
listing_command = namespace["build_remote_explorer_listing_command"]("/tmp")
assert "__HHS_FILE__" in listing_command
assert "__HHS_CWD__" in listing_command
assert "\\t..\\t" not in listing_command
assert '"${abs_dir}"/.[!.]*' not in listing_command
assert 'case "${name}" in .*|"."|"..") continue ;; esac' in listing_command
assert "target=${HOME:-.}" in listing_command
assert "exit 1" not in listing_command
assert "stat -c %s" in listing_command
assert "stat -f %z" in listing_command
with tempfile.TemporaryDirectory() as tmp_dir:
    fake_home = Path(tmp_dir) / "home"
    fake_home.mkdir()
    (fake_home / "fallback.txt").write_text("ok", encoding="utf-8")
    missing_dir = Path(tmp_dir) / "deleted" / "teste"
    fallback_command = namespace["build_remote_explorer_listing_command"](
        str(missing_dir)
    )
    result = subprocess.run(
        ["bash", "-lc", fallback_command],
        capture_output=True,
        check=False,
        env={"HOME": str(fake_home), "PATH": os.environ.get("PATH", "")},
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert f"__HHS_CWD__\t{fake_home.resolve()}" in result.stdout
    assert "fallback.txt" in result.stdout
with tempfile.TemporaryDirectory() as tmp_dir:
    target_folder = Path(tmp_dir) / "parent" / "new-folder"
    create_folder_command = namespace["build_remote_explorer_create_folder_command"](
        str(target_folder)
    )
    result = subprocess.run(
        ["bash", "-lc", create_folder_command],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert target_folder.is_dir()
    created_dir = namespace["parse_remote_explorer_created_dir"](result.stdout)
    assert Path(created_dir).resolve() == target_folder.resolve()

assert "__HHS_CREATED_DIR__" in create_folder_command
assert "mkdir -p" in create_folder_command
assert 'abs_dir=$(cd "${target}" && pwd -P)' in create_folder_command
assert "New Folder" not in create_folder_command
assert namespace["parse_remote_explorer_created_dir"](
    "__HHS_CREATED_DIR__\t/root/new-folder\n"
) == "/root/new-folder"
to_remote = namespace["build_scp_to_remote_command"](
    "/local/file.txt", "/remote dir", "host.example"
)
to_local = namespace["build_scp_to_local_command"](
    "/remote/file.txt", "/local dir", "host.example"
)
multi_to_remote = namespace["build_scp_to_remote_command"](
    ["/local/file one.txt", "/local/file two.txt"], "/remote dir", "host.example"
)
multi_to_local = namespace["build_scp_to_local_command"](
    ["/remote/file-one.txt", "/remote/file-two.txt"], "/local dir", "host.example"
)
assert "scp -r" in to_remote
assert "-F \"${HOME}/.ssh/config\"" in to_remote
assert "-o ControlPath=" in to_remote
assert "/local/file.txt" in to_remote
assert "host.example:'/remote dir'" in to_remote
assert "host.example:/remote/file.txt" in to_local
assert "'/local dir'" in to_local
assert "'/local/file one.txt' '/local/file two.txt'" in multi_to_remote
assert "host.example:/remote/file-one.txt" in multi_to_local
assert "host.example:/remote/file-two.txt" in multi_to_local
PY
  assert_success

  run grep -q 'timeout_seconds: int | None = None' "${ui_file}"
  assert_success

  run grep -q 'def command_timeout_seconds' "${ui_file}"
  assert_success

  run grep -q 'return hhs_ui.UI_COMMAND_REMOTE_TIMEOUT_SECONDS' "${ui_file}"
  assert_success

  run grep -q 'return hhs_ui.UI_COMMAND_LOCAL_TIMEOUT_SECONDS' "${ui_file}"
  assert_success

  run grep -q 'def effective_command_timeout_seconds' "${ui_file}"
  assert_success

  run grep -q 'return max(1, int(timeout_seconds))' "${ui_file}"
  assert_success

  run grep -q 'effective_timeout = effective_command_timeout_seconds(' "${ui_file}"
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

  run grep -q 'timeout_seconds=effective_timeout' "${ui_file}"
  assert_success

  run grep -q 'overlay.id = "hhs-command-overlay"' "${ui_file}"
  assert_success

  run grep -q 'overlay.style.inset = "0"' "${ui_file}"
  assert_success

  run grep -q 'overlay.style.height = "100dvh"' "${ui_file}"
  assert_success

  run grep -q 'overlay.style.alignItems = "center"' "${ui_file}"
  assert_success

  run grep -q 'overlay.style.justifyContent = "center"' "${ui_file}"
  assert_success

  run grep -q 'doc.body.appendChild(overlay)' "${ui_file}"
  assert_success

  run grep -q 'doc.body.dataset.hhsCommandOverlayHidden = "false"' "${ui_file}"
  assert_success

  run grep -q 'const clearedAt = Number(parentWindow.__hhsCommandOverlayClearedAt || 0)' "${ui_file}"
  assert_success

  run grep -q 'createdAt <= clearedAt' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsCommandOverlayToken = overlayToken' "${ui_file}"
  assert_success

  run grep -q 'overlay.dataset.hhsOverlayToken = overlayToken' "${ui_file}"
  assert_success

  run grep -q 'overlay.dataset.hhsOverlayCreatedAt = String(createdAt)' "${ui_file}"
  assert_success

  run grep -q 'def clear_preloader()' "${ui_file}"
  assert_success

  run grep -q 'clear_preloader()' "${ui_file}"
  assert_success

  run grep -q 'doc.body.dataset.hhsCommandOverlayHidden = "true"' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsCommandOverlayClearedAt = Date.now()' "${ui_file}"
  assert_success

  run grep -q 'const observer = new parentWindow.MutationObserver(remove_overlay)' "${ui_file}"
  assert_success

  run grep -q 'observer.observe(doc.body, { childList: true })' "${ui_file}"
  assert_success

  run grep -q 'overlayCreatedAt > clearedAt' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.setTimeout(remove_overlay, 50)' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.setTimeout(remove_overlay, 250)' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.setTimeout(remove_overlay, 1000)' "${ui_file}"
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

  run grep -q 'def loader_label_html' "${ui_file}"
  assert_success

  run grep -q '"%primary_color%": "hhs-loader-primary"' "${ui_file}"
  assert_success

  run grep -q '"%secondary_color%": "hhs-loader-secondary"' "${ui_file}"
  assert_success

  run grep -q 'safe_message_html = loader_label_html(message)' "${ui_file}"
  assert_success

  run grep -q 'label.innerHTML = {json.dumps(safe_message_html)}' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import html
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def loader_label_html(")
end = source.index("def render_command_loader_timer(")
namespace = {"html": html}
exec("from __future__ import annotations\n" + source[start:end], namespace)
rendered = namespace["loader_label_html"](
    "Searching for %primary_color%<term>%primary_color% "
    "in %secondary_color%/tmp/a&b%secondary_color%"
)
assert '<span class="hhs-loader-primary">&lt;term&gt;</span>' in rendered
assert '<span class="hhs-loader-secondary">/tmp/a&amp;b</span>' in rendered
PY
  assert_success

  run grep -q 'time.sleep(0.1)' "${ui_file}"
  assert_success

  run grep -q 'render_script_html(' "${ui_file}"
  assert_success

  run grep -q 'components.html(' "${ui_file}"
  assert_failure

  run grep -q 'overlay.style.zIndex = "1000010"' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsCommandOverlayTimer = parentWindow.setInterval(render_elapsed, 1000)' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.__hhsCommandOverlayExpiryTimer = parentWindow.setTimeout' "${ui_file}"
  assert_success

  run grep -q 'data-timeout-seconds' "${ui_file}"
  assert_success

  run grep -q 'elapsed_ratio >= 0.3 && elapsed_ratio < 0.6' "${ui_file}"
  assert_success

  run grep -q 'elapsed_ratio >= 0.6' "${ui_file}"
  assert_success

  run grep -q 'hhs-loader-elapsed-warning' "${ui_file}"
  assert_success

  run grep -q 'hhs-loader-elapsed-danger' "${ui_file}"
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

  run grep -q '.hhs-command-loader {' "${css_file}"
  assert_success

  run grep -q 'margin: 0.5rem auto' "${css_file}"
  assert_success

  run grep -q 'justify-content: center' "${css_file}"
  assert_success

  run grep -q '.hhs-tab-loader-elapsed.hhs-loader-elapsed-warning' "${css_file}"
  assert_success

  run grep -q '.hhs-loader-primary' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-primary)' "${css_file}"
  assert_success

  run grep -q '.hhs-loader-secondary' "${css_file}"
  assert_success

  run grep -q 'color: var(--hhs-secondary)' "${css_file}"
  assert_success

  run grep -q 'color: #facc15 !important' "${css_file}"
  assert_success

  run grep -q '.hhs-tab-loader-elapsed.hhs-loader-elapsed-danger' "${css_file}"
  assert_success

  run grep -q 'color: #ff5555 !important' "${css_file}"
  assert_success

  run grep -F -q 'div[class*="st-key-command_overlay_slot_"]' "${css_file}"
  assert_failure

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:empty' "${css_file}"
  assert_success

  run grep -F -q '[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has([data-testid="stMarkdownContainer"] style)' "${css_file}"
  assert_success

  run grep -F -q 'div:not([class*="st-key-ssh_explorer_component"]):has(iframe[height="0"])' "${css_file}"
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

  run grep -q 'def render_pending_streamlit_dialog_dismiss' "${ui_file}"
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

  run grep -q 'render_pending_streamlit_dialog_dismiss()' "${ui_file}"
  assert_success

  run grep -q 'st.session_state\["_hhs_dialog_dismiss_requested"\] = True' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
callback_body = source.split("def handle_dialog_button_click", 1)[1].split("\ndef ", 1)[0]
dismiss_body = source.split("def dismiss_streamlit_dialog", 1)[1].split("\ndef ", 1)[0]
assert "render_script_html(" not in callback_body
assert "st.html(" not in callback_body
assert "render_script_html(" not in dismiss_body
assert "st.html(" not in dismiss_body
PY
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

  run grep -q 'def schedule_cleanup_session_resources' "${ui_file}"
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

  run grep -q 'PROCESS_RESOURCE_STATE_KEY = "_hhs_ui_process_resource_state"' "${ui_file}"
  assert_success

  run grep -q 'def process_resource_state' "${ui_file}"
  assert_success

  run grep -q 'def process_resource_registry' "${ui_file}"
  assert_success

  run grep -q 'schedule_cleanup_session_resources(token)' "${ui_file}"
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

  run grep -q 'parentWindow.__hhsTtydCleanupHandler' "${ui_file}"
  assert_success

  run grep -q 'parentWindow.removeEventListener(' "${ui_file}"
  assert_success

  run python3 - <<'PY'
from pathlib import Path

ui_source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
handler_body = ui_source.split("def handle_cleanup_request", 1)[1].split("\n    def ", 1)[0]
assert handler_body.index("self.send_response(204)") < handler_body.index(
    "schedule_cleanup_session_resources(token)"
)
schedule_body = ui_source.split("def schedule_cleanup_session_resources", 1)[1].split("\ndef ", 1)[0]
assert "threading.Thread(" in schedule_body
assert "daemon=True" in schedule_body
state_body = ui_source.split("def process_resource_state", 1)[1].split("\ndef ", 1)[0]
assert "setattr(sys, PROCESS_RESOURCE_STATE_KEY, state)" in state_body
registry_body = ui_source.split("def process_resource_registry", 1)[1].split("\n\nTTYD_CLEANUP_REGISTRY", 1)[0]
assert "state[key] = registry" in registry_body
assert "process_resource_registry(\n    \"ttyd_cleanup_registry\"" in ui_source
assert "process_resource_registry(\n    \"ttyd_event_registry\"" in ui_source
ensure_body = ui_source.split("def ensure_ttyd_cleanup_server", 1)[1].split("\ndef ", 1)[0]
assert "process_resource_state()" in ensure_body
assert "ThreadingHTTPServer(" in ensure_body
assert 'state["ttyd_cleanup_server"] = server' in ensure_body
assert 'state["ttyd_cleanup_server_port"] = port' in ensure_body
assert 'state["ttyd_cleanup_atexit_registered"] = True' in ensure_body
browser_cleanup_body = ui_source.split("def render_browser_cleanup_script", 1)[1].split("\ndef ", 1)[0]
assert browser_cleanup_body.index("removeEventListener(") < browser_cleanup_body.index(
    "parentWindow.addEventListener(\"pagehide\", cleanup"
)
assert "parentWindow.__hhsTtydCleanupHandler = cleanup" in browser_cleanup_body
PY
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
updater_index = main_body.index("execute_due_updater_check()")
ssh_dialog_index = main_body.index("render_ssh_connection_dialog()")
ai_initialize_index = main_body.index("initialize_ollama_service_availability()")
ai_refresh_index = main_body.index("update_ollama_service_availability_refresh()")
active_view_validation_index = main_body.index('if st.session_state["active_view"] not in main_views():')
footer_actions_index = main_body.index("handle_footer_actions()")
shell_dialog_index = main_body.index("render_footer_shell_version_dialog()")
cleanup_index = main_body.index("render_browser_cleanup_script()")
sidebar_index = main_body.index("render_sidebar()")
main_view_index = main_body.index("render_main_view()")
footer_index = main_body.index("render_footer()")
client_status_index = main_body.index("render_footer_client_error_bridge_script()")
drain_status_index = main_body.index("drain_footer_status_log_records()")
floating_status_index = main_body.index("render_floating_status()")
assert main_body.index("install_footer_status_log_handler()") < main_body.index(
    "selected_theme = persisted_theme_name()"
)
assert 'st.session_state.setdefault("updater_check_context", "local")' in main_body
assert 'st.session_state.setdefault("updater_check_started_context", "")' in main_body
assert 'st.session_state.setdefault("updater_remote_checked_context", "")' in main_body
assert disconnect_index < connect_index < updater_index < ssh_dialog_index
assert ssh_dialog_index < ai_initialize_index < ai_refresh_index < active_view_validation_index
assert active_view_validation_index < footer_actions_index < shell_dialog_index
assert shell_dialog_index < sidebar_index < main_view_index
assert footer_index < client_status_index < drain_status_index < floating_status_index < cleanup_index
assert "class FooterStatusLogHandler(logging.Handler)" in ui_source
assert "logging.captureWarnings(True)" in ui_source
assert "def drain_footer_status_log_records(" in ui_source
assert "def render_footer_client_error_bridge_script(" in ui_source
assert "Missing Submit Button" in ui_source or "missing submit button" in ui_source
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
from functools import lru_cache
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def terminal_output_line_is_noise(")
end = source.index("def strip_ansi(")
motd_start = source.index("def homesetup_motd_template(")
motd_end = source.index("def strip_remote_command_motd_block(")
namespace = {
    "re": re,
    "strip_ansi": lambda value: value,
    "strip_ssh_shared_connection_notice": lambda value: value,
    "homesetup_home": lambda: Path(".").resolve(),
    "lru_cache": lru_cache,
}
exec(
    "from __future__ import annotations\n"
    + source[motd_start:motd_end]
    + "\n"
    + source[start:end],
    namespace,
)
motd_fragments = namespace["homesetup_motd_fragment_groups"]()[0]
rendered_motd = f"[Linux-ubuntu/bash] {' root '.join(motd_fragments)} v1.9.18 "

stdout = (
    "[bash] HomeSetup is starting...\n"
    f"{rendered_motd}\n"
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
import ast
import re
from pathlib import Path
from types import SimpleNamespace

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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
    ),
}
exec(
    "from __future__ import annotations\n"
    + "\n\n".join(
        functions[name]
        for name in (
            "strip_ansi",
            "interpret_terminal_edit_sequences",
            "clean_hhs_ask_output",
        )
    ),
    namespace,
)
raw_output = (
    "\x1b[H\x1b[2J\x1b[3J"
    "✨ llama3.1:latest[128K]:\n"
    "allows for fr\x1b[2D\x1b[Kfree use\n"
    "Using HomeSe\x1b[6D\x1b[KHomeSetup\n"
)
clean_output = namespace["clean_hhs_ask_output"](raw_output)
assert "allows for free use" in clean_output
assert "Using HomeSetup" in clean_output
assert "[2D" not in clean_output
assert "[K" not in clean_output
assert "frfree" not in clean_output
PY
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
  assert_output --partial '### ROLE'
  assert_output --partial 'Shell: bash'
  assert_output --partial 'Operating system: test'
  assert_output --partial 'OS family: Darwin'
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

  run grep -q 'parse_rows_cached(' "${ui_file}"
  assert_success

  run grep -q 'parse_ollama_model_rows(output, ollama_model)' "${ui_file}"
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

  run grep -q 'PROCESS_FILTERS = ("All", "Active", "Inactive", "Ghost", "Containing")' "${constants_file}"
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
  run grep -q 'LOG_TAILOR_RULES' "${constants_file}"
  assert_success

  run grep -q 'LOG_LEVELS = (' "${constants_file}"
  assert_success

  run grep -q 'LOG_FILTERS = ("All", "Containing")' "${constants_file}"
  assert_success

  run grep -q 'LOG_LEVELS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q 'LOG_FILTERS' "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py"
  assert_success

  run grep -q '"monitor_log_filter"' "${constants_file}"
  assert_success

  run grep -q '"monitor_log_other_filter"' "${constants_file}"
  assert_success

  run grep -q '"monitor_log_level"' "${constants_file}"
  assert_success

  run grep -q 'def colorize_log_output' "${ui_file}"
  assert_success

  run grep -q 'def log_filter_highlight_ranges' "${ui_file}"
  assert_success

  run grep -q 'def filter_log_output' "${ui_file}"
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

  run grep -q 'selected_log, selected_level, tail_enabled, log_filter, log_text_filter = (' "${ui_file}"
  assert_success

  run grep -q 'render_log_controls' "${ui_file}"
  assert_success

  run grep -q 'render_table_filter_controls(' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui.LOG_FILTERS' "${ui_file}"
  assert_success

  run grep -q 'other_options=("Containing",)' "${ui_file}"
  assert_failure

  run grep -q 'other_options: tuple\[str, ...\] = ("Other", "Others", "Containing")' "${ui_file}"
  assert_success

  run grep -q '"monitor_log_filter"' "${ui_file}"
  assert_success

  run grep -q '"monitor_log_other_filter"' "${ui_file}"
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

  run python3 - <<'PY'
import ast
import re
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
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
    }
]
namespace = {
    "html": __import__("html"),
    "re": re,
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
PY
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

  run grep -q '.hhs-log-filter-match' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-collapsed-height: 3.4rem' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-open-height: 230px' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-height: var(--hhs-log-expander-collapsed-height)' "${css_file}"
  assert_success

  run grep -Fq '[data-testid="stVerticalBlock"]:has(.hhs-log-output):has(details[open])' "${css_file}"
  assert_success

  run grep -q -- '--hhs-log-expander-height: var(--hhs-log-expander-open-height)' "${css_file}"
  assert_success

  run grep -q 'background-color: #2563eb' "${css_file}"
  assert_success

  run grep -q 'color: #ffffff !important' "${css_file}"
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

  run grep -q -- '--hhs-log-expander-open-height: 230px' "${css_file}"
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

  run grep -q 'def build_hhs_path_environment_command' "${ui_file}"
  assert_success

  run grep -q 'def build_hhs_paths_raw_entries_command' "${ui_file}"
  assert_success

  run grep -q 'HHS_PATHS_RAW_ENTRY_MARKER' "${ui_file}"
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

  run grep -q 'sync_folder_picker_child_selection(child_directories)' "${ui_file}"
  assert_success

  run grep -q 'def folder_picker_child_selection_widget_key' "${ui_file}"
  assert_success

  run grep -q '_hhs_folder_picker_selected_dir_widget_' "${ui_file}"
  assert_success

  run grep -q 'prune_folder_picker_child_selection_widget_keys(selected_widget_key)' "${ui_file}"
  assert_success

  run grep -q '"key": selected_widget_key' "${ui_file}"
  assert_success

  run grep -q 'placeholder": empty_caption' "${ui_file}"
  assert_success

  run grep -q 'disabled": not bool(child_directories)' "${ui_file}"
  assert_success

  run grep -q 'st.caption(empty_caption)' "${ui_file}"
  assert_failure

  run grep -q 'def folder_picker_browsing_directory' "${ui_file}"
  assert_success

  run grep -q 'rerun_after_folder_picker_navigation()' "${ui_file}"
  assert_failure

  run grep -q 'st.container(key="folder_picker_action_grid")' "${ui_file}"
  assert_success

  run grep -q '_left_spacer,' "${ui_file}"
  assert_success

  run grep -q '_parent_open_gap,' "${ui_file}"
  assert_failure

  run grep -q '\[1.0, 0.12, 0.12, 0.12, 0.12, 1.0\]' "${ui_file}"
  assert_success

  run grep -q 'gap="small"' "${ui_file}"
  assert_success

  run grep -q 'width="content"' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q '""' "${ui_file}"
  assert_success

  run grep -q '"﬌"' "${ui_file}"
  assert_success

  run grep -q '"ﰸ"' "${ui_file}"
  assert_success

  run grep -q '" Parent"' "${ui_file}"
  assert_failure

  run grep -q '"label": "﬌ Select"' "${ui_file}"
  assert_failure

  run grep -q 'buttons=()' "${ui_file}"
  assert_success

  run grep -q '.st-key-folder_picker_select_button button' "${css_file}"
  assert_success

  run grep -q '.st-key-folder_picker_action_grid,' "${css_file}"
  assert_failure

  run grep -q '.st-key-folder_picker_action_grid \[data-testid="stVerticalBlock"\]' "${css_file}"
  assert_failure

  run grep -q '.st-key-folder_picker_action_grid \[data-testid="stHorizontalBlock"\]' "${css_file}"
  assert_success

  run grep -q 'gap: var(--hhs-element-std-gap) !important' "${css_file}"
  assert_success

  run grep -q 'grid-auto-flow: column' "${css_file}"
  assert_failure

  run grep -q 'grid-template-columns: repeat(4, 2rem)' "${css_file}"
  assert_failure

  run grep -q 'var(--hhs-element-std-gap)' "${css_file}"
  assert_success

  run grep -q 'nth-child(8)' "${css_file}"
  assert_failure

  run grep -q 'nth-child(5)' "${css_file}"
  assert_success

  run grep -q 'min-width: 2rem' "${css_file}"
  assert_success

  run grep -q 'justify-content: center' "${css_file}"
  assert_success

  run grep -q '"Include .dot-folders"' "${ui_file}"
  assert_success

  run grep -q '"Loading directories and files..."' "${ui_file}"
  assert_success

  run grep -q 'def render_path_picker_open_preloader_script' "${ui_file}"
  assert_success

  run grep -q 'render_path_picker_open_preloader_script()' "${ui_file}"
  assert_success

  run grep -q '__hhsPathPickerOpenPreloaderCleanup' "${ui_file}"
  assert_success

  run grep -q 'path-picker-' "${ui_file}"
  assert_success

  run grep -Fq '[class*="st-key-"][class*="_folder_picker_button"] button' "${ui_file}"
  assert_success

  run grep -q '.st-key-folder_picker_open_button button' "${ui_file}"
  assert_success

  run grep -q '.st-key-folder_picker_parent_button button' "${ui_file}"
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
    assert "parse_rows_cached(" in body, function_name
    assert "if result.returncode == 0" in body, function_name
    assert "else []" in body, function_name
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

@test "when connected over SSH then reusable path picker should list remote paths" {
  run python3 - "${ui_file}" <<'PY'
import os
import posixpath
import shlex
import subprocess
import sys
import textwrap
import types
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def folder_picker_start_directory(")
end = source.index("def homesetup_version(")
host = "remote-box"
statuses = []
commands = []
session_state = {
    "_hhs_folder_picker_mode": "file",
    "_hhs_folder_picker_current_dir": "/home/root",
    "_hhs_folder_picker_current_dir_input": "/home/root/readme.md",
}

def run_bash_command(command, *args, **kwargs):
    commands.append((command, kwargs))
    if "raw_target=/home/root/app" in command:
        return subprocess.CompletedProcess(
            ["ssh"],
            0,
            "__HHS_PICKER_CWD__\t/home/root/app\n"
            "__HHS_PICKER_ENTRY__\tDir\t/home/root/app/logs\n"
            "__HHS_PICKER_ENTRY__\tDir\t/home/root/app/tmp\n",
            "",
        )
    output = (
        "__HHS_PICKER_CWD__\t/home/root\n"
        "__HHS_PICKER_ENTRY__\tDir\t/home/root/app\n"
    )
    if "picker_mode=file" in command:
        output += "__HHS_PICKER_ENTRY__\tFile\t/home/root/readme.md\n"
    return subprocess.CompletedProcess(
        ["ssh"],
        0,
        output,
        "",
    )

namespace = {
    "Path": Path,
    "os": os,
    "posixpath": posixpath,
    "shlex": shlex,
    "subprocess": subprocess,
    "textwrap": textwrap,
    "hhs_ui": types.SimpleNamespace(UI_CACHE_REALTIME_TTL_SECONDS=1),
    "hhs_ui_constants": types.SimpleNamespace(
        FOOTER_REMOTE_WORKING_DIR_KEY="footer_remote_cwd",
        UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS=30,
    ),
    "st": types.SimpleNamespace(session_state=session_state),
    "connected_ssh_host": lambda: host,
    "run_bash_command": run_bash_command,
    "strip_ansi": lambda value: value,
    "push_floating_status": lambda message, level: statuses.append((message, level)),
    "clean_command_status_message": lambda value: str(value).strip(),
    "dismiss_streamlit_dialog": lambda: None,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

dialog_body = source.split("def render_path_picker_dialog", 1)[1].split("\ndef ", 1)[0]
assert "dialog_rendered = pop_dialog(" in dialog_body
assert dialog_body.index("dialog_rendered = pop_dialog(") < dialog_body.rindex(
    "clear_preloader()"
)
assert dialog_body.index("prepare_path_picker_dialog_listing(mode)") < dialog_body.index(
    "dialog_rendered = pop_dialog("
)
render_body = dialog_body.split("def render_body", 1)[1].split(
    "dialog_rendered = pop_dialog", 1
)[0]
assert "current_directory = folder_picker_browsing_directory()" in dialog_body
assert "sync_folder_picker_child_selection(child_directories)" in dialog_body
assert render_body.index(
    "current_directory = folder_picker_browsing_directory()"
) < render_body.index("path_picker_child_paths(")
assert render_body.index("path_picker_child_paths(") < render_body.index(
    "st.text_input("
)
assert render_body.index(
    "sync_folder_picker_child_selection(child_directories)"
) < render_body.index("st.text_input(")
assert "st.caption(empty_caption)" not in render_body
assert '"placeholder": empty_caption' in render_body
assert '"disabled": not bool(child_directories)' in render_body
assert render_body.index("st.selectbox(") < render_body.index("st.checkbox(")
assert namespace["path_picker_uses_remote"]()
assert namespace["remote_path_picker_default_directory"]() == "$HOME"
assert namespace["request_path_picker"]("search_path", "", "folder") is None
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"
children = namespace["path_picker_child_paths"]("$HOME", "folder", False)
assert children == ["/home/root/app"]
assert len(commands) == 1
assert "raw_target='$HOME'" in commands[0][0]
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"
children = namespace["path_picker_child_paths"]("/home/root", "folder", False)
assert children == ["/home/root/app"]
assert len(commands) == 1

assert namespace["request_path_picker"]("search_path", "/srv", "folder") is None
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"

command_count = len(commands)
session_state["_hhs_folder_picker_mode"] = "folder"
session_state["_hhs_folder_picker_current_dir"] = "/home/root"
session_state["_hhs_folder_picker_current_dir_input"] = "/home/root"
session_state["_hhs_folder_picker_path_kinds"] = {"/home/root/app": "Dir"}
session_state["_hhs_folder_picker_selected_dir"] = "/home/root/app"
namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root/app"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/app"
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
assert session_state["_hhs_folder_picker_path_kinds"]["/home/root/app/logs"] == "Dir"
assert len(commands) == command_count + 1
namespace["sync_folder_picker_child_selection"](
    ["/home/root/app/logs", "/home/root/app/tmp"]
)
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
namespace["sync_folder_picker_child_selection"](
    ["/home/root/app/logs", "/home/root/app/tmp"]
)
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
session_state["_hhs_folder_picker_selected_dir"] = "/home/root/app/tmp"
namespace["sync_folder_picker_child_selection"](
    ["/home/root/app/logs", "/home/root/app/tmp"]
)
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/tmp"
namespace["sync_folder_picker_child_selection"]([])
assert "_hhs_folder_picker_selected_dir" not in session_state

namespace["open_folder_picker_parent"]()
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root"
assert len(commands) == command_count + 1
session_state["_hhs_folder_picker_selected_dir"] = "/home/root/app"
namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root/app"
assert session_state["_hhs_folder_picker_selected_dir"] == "/home/root/app/logs"
assert len(commands) == command_count + 1

session_state["_hhs_folder_picker_mode"] = "file"
session_state["_hhs_folder_picker_current_dir"] = "/home/root"
session_state["_hhs_folder_picker_current_dir_input"] = "/home/root/readme.md"
children = namespace["path_picker_child_paths"]("/home/root", "file", False)
assert children == ["/home/root/app", "/home/root/readme.md"]
assert commands[-1][1]["show_overlay"] is False
assert commands[-1][1]["cache_tag"] == "path_picker"
assert commands[-1][1]["timeout_seconds"] == 30
assert session_state["_hhs_folder_picker_current_dir"] == "/home/root"
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/readme.md"
assert session_state["_hhs_folder_picker_path_kinds"]["/home/root/readme.md"] == "File"

session_state["_hhs_folder_picker_selected_dir"] = "/home/root/readme.md"
namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir_input"] == "/home/root/readme.md"
assert namespace["selected_folder_picker_path"]() == "/home/root/readme.md"
assert "raw_target=/home/root" in commands[-1][0]
assert statuses == []
PY
  assert_success
}

@test "when local path picker opens a child folder then its children should be selected" {
  run python3 - "${ui_file}" "${BATS_TEST_TMPDIR}" <<'PY'
import hashlib
import os
import posixpath
import shlex
import subprocess
import sys
import textwrap
import types
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tmpdir = Path(sys.argv[2])
start = source.index("def folder_picker_start_directory(")
end = source.index("def homesetup_version(")
home = tmpdir / "home"
apps = home / "Applications"
alpha = apps / "alpha"
beta = apps / "Beta"
for directory in (alpha, beta):
    directory.mkdir(parents=True, exist_ok=True)
other_widget_key = "_hhs_folder_picker_selected_dir_widget_stale"
session_state = {
    "_hhs_folder_picker_mode": "folder",
    "_hhs_folder_picker_current_dir": str(home),
    "_hhs_folder_picker_current_dir_input": str(home),
    "_hhs_folder_picker_selected_dir": str(apps),
    other_widget_key: str(apps),
}

namespace = {
    "Path": Path,
    "hashlib": hashlib,
    "os": os,
    "posixpath": posixpath,
    "shlex": shlex,
    "subprocess": subprocess,
    "textwrap": textwrap,
    "st": types.SimpleNamespace(
        session_state=session_state,
    ),
    "connected_ssh_host": lambda: "",
    "dismiss_streamlit_dialog": lambda: None,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

namespace["open_folder_picker_selected_directory"]()
assert session_state["_hhs_folder_picker_current_dir"] == str(apps.resolve())
assert session_state["_hhs_folder_picker_current_dir_input"] == str(apps.resolve())
assert session_state["_hhs_folder_picker_selected_dir"] == str(alpha.resolve())

session_state["_hhs_folder_picker_current_dir"] = str(home)
session_state["_hhs_folder_picker_current_dir_input"] = str(apps)
assert namespace["folder_picker_browsing_directory"]() == str(apps.resolve())
children = namespace["path_picker_child_paths"](
    namespace["folder_picker_browsing_directory"](), "folder", False
)
assert children == [str(alpha.resolve()), str(beta.resolve())]

widget_key = namespace["folder_picker_child_selection_widget_key"](
    str(apps.resolve()), "folder", False
)
session_state[widget_key] = str(beta.resolve())
namespace["prune_folder_picker_child_selection_widget_keys"](widget_key)
assert session_state[widget_key] == str(beta.resolve())
assert other_widget_key not in session_state
assert widget_key.startswith("_hhs_folder_picker_selected_dir_widget_")
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

@test "when building ENV rows then the command should load HomeSetup shell environment" {
  run python3 - "${ui_file}" "${BATS_TEST_TMPDIR}" "${HHS_REPO_DIR}" <<'PY'
import os
import shlex
import subprocess
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
tmp_dir = Path(sys.argv[2])
repo_dir = Path(sys.argv[3])
start = source.index("def build_hhs_env_environment_command()")
end = source.index("def run_hhs_envs(")
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
  run python3 - "${ui_file}" <<'PY'
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
  run python3 - "${ui_file}" <<'PY'
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
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
assert list(rows[0]) == ["Type", "Origin", "Path Value"], rows
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

@test "when rerendering command tables then parsed rows should be cached in session state" {
  run python3 - "${ui_file}" <<'PY'
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def command_result_snapshots()")
end = source.index("def cache_set(")
session_state = {}
namespace = {
    "hashlib": hashlib,
    "st": SimpleNamespace(session_state=session_state),
    "hhs_ui_constants": SimpleNamespace(
        COMMAND_RESULT_SNAPSHOT_KEY="_hhs_command_result_snapshots",
        COMMAND_RESULT_SNAPSHOT_LIMIT=2,
        PARSED_ROWS_CACHE_KEY="_hhs_parsed_rows_cache",
        PARSED_ROWS_CACHE_LIMIT=2,
        LOG_RENDER_CACHE_KEY="_hhs_log_render_cache",
        LOG_RENDER_CACHE_LIMIT=2,
    ),
    "filter_log_output": lambda output, _filter, text: output.replace(text, text.upper()),
    "colorize_log_output": lambda output, highlight: f"{highlight}:{output}",
    "safe_cache_tag": lambda value: value,
}
exec("from __future__ import annotations\n" + source[start:end], namespace)

calls = []

def parser(output):
    calls.append(output)
    return [{"Name": output}]

first = namespace["parse_rows_cached"]("sample", "one", parser)
second = namespace["parse_rows_cached"]("sample", "one", parser)
assert first == [{"Name": "one"}]
assert second == [{"Name": "one"}]
assert calls == ["one"]

first[0]["Name"] = "mutated"
third = namespace["parse_rows_cached"]("sample", "one", parser)
assert third == [{"Name": "one"}]

rendered = namespace["rendered_log_output_cached"]("hello needle", "Containing", "needle")
cached = namespace["rendered_log_output_cached"]("hello needle", "Containing", "needle")
assert rendered == "needle:hello NEEDLE"
assert cached == rendered
PY
  assert_success
}

@test "when using table filters then shared filter controls should persist filter keys" {
  run python3 - "${ui_file}" <<'PY'
import ast
import sys
from pathlib import Path

tree = ast.parse(Path(sys.argv[1]).read_text(encoding="utf-8"))
functions = {
    node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
}
filter_controls = functions["render_table_filter_controls"]
normalizer = functions["normalized_table_filter_selection"]

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
assert "handle_monitor_disk_top_n_change" not in ast.unparse(filter_controls)
assert "Containing" in ast.unparse(filter_controls)
assert "Containing" in ast.unparse(normalizer)
PY
  assert_success
}

@test "when filtering table rows then status and text filters should reduce rows" {
  run python3 - "${ui_file}" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = source.index("def env_filter_pattern(")
end = source.index("def parse_hhs_envs(")
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
exec("from __future__ import annotations\n" + source[start:end], namespace)

assert namespace["env_filter_pattern"]("Containing", "PATH") == "PATH"
assert namespace["env_filter_pattern"]("Other", "PATH") == "PATH"

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

@test "when reading UI cache then expired entries should not be written back during load" {
  run grep -q 'key.startswith("search_terms:")' "${ui_file}"
  assert_success

  run grep -q 'def ui_cache_preserved_on_clear_key' "${ui_file}"
  assert_success

  run grep -q 'hhs_ui_constants.SEARCH_TERM_HISTORY_CACHE_KEY' "${ui_file}"
  assert_success

  run grep -q 'if ui_cache_preserved_on_clear_key(key)' "${ui_file}"
  assert_success

  run python3 - "${ui_file}" <<'PY'
import ast
import sys
from pathlib import Path

tree = ast.parse(Path(sys.argv[1]).read_text(encoding="utf-8"))

for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "load_ui_cache":
        load_ui_cache = node
        break
else:
    raise AssertionError("load_ui_cache not found")

save_calls = [
    call
    for call in ast.walk(load_ui_cache)
    if isinstance(call, ast.Call)
    and isinstance(call.func, ast.Name)
    and call.func.id == "save_ui_cache"
]
assert save_calls == []
PY
  assert_success
}

@test "when rendering main navigation then AI visibility should not start service jobs" {
  run python3 - "${ui_file}" <<'PY'
import ast
import sys
from pathlib import Path

tree = ast.parse(Path(sys.argv[1]).read_text(encoding="utf-8"))
functions = {
    node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
}

main_views = functions["main_views"]
ollama_available = functions["ollama_service_is_available"]
initialize_available = functions["initialize_ollama_service_availability"]
for function_node in (main_views, ollama_available, initialize_available):
    called_names = {
        call.func.id
        for call in ast.walk(function_node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    assert "start_hhs_services_list_refresh" not in called_names
    assert "complete_hhs_services_list_refresh" not in called_names
    assert "poll_background_job_completion" not in called_names

remember = functions["remember_ollama_service_availability"]
remember_calls = {
    call.func.id
    for call in ast.walk(remember)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "ollama_service_is_available_from_output" in remember_calls

schedule = functions["schedule_ollama_service_availability_refresh"]
schedule_calls = {
    call.func.id
    for call in ast.walk(schedule)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "stop_background_job" in schedule_calls
assert "cache_delete_tag" in schedule_calls
assert "start_hhs_services_list_refresh" in schedule_calls

update = functions["update_ollama_service_availability_refresh"]
update_calls = {
    call.func.id
    for call in ast.walk(update)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "complete_hhs_services_list_refresh" in update_calls
assert "background_job_is_running" in update_calls
assert "poll_background_job_completion" in update_calls

main = functions["main"]
main_calls = {
    call.func.id
    for call in ast.walk(main)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
}
assert "initialize_ollama_service_availability" in main_calls
assert "main_views" in main_calls
assert "update_ollama_service_availability_refresh" in main_calls
PY
  assert_success
}

@test "when building Search commands then query type should choose the matching hhs helper" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import hashlib
import html
import os
import posixpath
import re
import shlex
import subprocess
import types
import urllib.parse

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text(encoding="utf-8")
start = source.index("def search_type_label(")
end = source.index("def render_ai_models_result(")
namespace = {
    "posixpath": posixpath,
    "re": re,
    "shlex": shlex,
    "urllib": types.SimpleNamespace(parse=urllib.parse),
    "hhs_ui": types.SimpleNamespace(
        SEARCH_OPEN_RESULT_QUERY_PARAM="hhs_open_search_result",
    ),
    "hhs_ui_constants": types.SimpleNamespace(
        SEARCH_TYPES=("Files", "Folders", "Strings"),
        SEARCH_DIRECTORY_HISTORY_LIMIT=3,
        SEARCH_TERM_HISTORY_CACHE_KEY="search_terms:history",
        SEARCH_TERM_HISTORY_LIMIT=3,
        SEARCH_TERM_HISTORY_TTL_SECONDS=900,
        SEARCH_PAGE_SIZE=20,
        UI_CACHE_NORMAL_TTL_SECONDS=300,
        SEARCH_TYPE_LABELS={
            "Files": "Files",
            "Folders": "Folders",
            "Strings": "Strings",
        },
    ),
    "st": types.SimpleNamespace(session_state={}),
    "Path": Path,
    "os": os,
    "html": html,
    "hashlib": hashlib,
    "safe_cache_tag": lambda value: value,
    "display_path_value": lambda value: value,
    "footer_working_directory": lambda: "/work/current",
    "connected_ssh_host": lambda: namespace.get("connected_host", ""),
    "run_bash_command": lambda command, *args, **kwargs: remote_commands.append(
        (command, kwargs)
    )
    or subprocess.CompletedProcess(
        ["remote-env"],
        0,
        "__HHS_UI_ENV__\nHOME\t/remote/home\nHHS_HOME\t/opt/hhs\n",
        "",
    ),
    "push_floating_status": lambda message, level: statuses.append((message, level)),
    "cache_delete_tag": lambda tag: deleted_cache_tags.append(tag),
    "save_ui_state": lambda: None,
    "strip_ansi": lambda value: value,
    "ssh_explorer_mtime_text": lambda value: f"mtime:{value}",
    "ssh_explorer_size_text": lambda value, kind: (
        "2.0 KB" if value == "2048" and kind == "File" else f"{kind}:{value}"
    ),
    "row_matches_text_filter": lambda row, value: value.lower() in " ".join(
        str(item).lower() for item in row.values()
    ),
    "log_filter_highlight_ranges": lambda value, text_filter: [
        (match.start(), match.end(), "filter-match")
        for match in re.finditer(re.escape(text_filter), value, flags=re.IGNORECASE)
    ]
    if text_filter
    else [],
}
term_cache = {}
cache_writes = []
statuses = []
deleted_cache_tags = []
remote_commands = []

def cache_get(key):
    return term_cache.get(key)

def cache_set(key, value, ttl_seconds):
    cache_writes.append((key, value, ttl_seconds))
    term_cache[key] = value

namespace["cache_get"] = cache_get
namespace["cache_set"] = cache_set
exec("from __future__ import annotations\n" + source[start:end], namespace)

controls_body = source.split("def render_search_controls", 1)[1].split("\ndef ", 1)[0]
assert (
    '"Search directory",\n'
    '                options=search_directory_options(),\n'
    '                key="search_path",\n'
    '                accept_new_options=True,\n'
    '                on_change=apply_search_directory_change,\n'
    '                width="stretch",'
) in controls_body
submit_body = source.split("def submit_search_query", 1)[1].split("\ndef ", 1)[0]
assert 'st.session_state["search_type"] =' not in submit_body
assert 'st.session_state["search_result_type"] = search_type' in submit_body
assert "query = remember_search_term(query)" in submit_body
assert "search_path = remember_search_directory(search_path)" in submit_body
assert submit_body.index("search_path = remember_search_directory(search_path)") < (
    submit_body.index('if not query:')
)
assert namespace["normalized_search_type"]("Folders") == "Folders"
assert namespace["normalized_search_type"]("Unknown") == "Files"
assert namespace["search_glob_from_query"]("report") == "*report*"
assert namespace["search_glob_from_query"]("*.md") == "*.md"
local_home = str(Path.home().resolve())
assert namespace["default_search_directory"]() == local_home
namespace["st"].session_state["search_path"] = "/persisted/path"
namespace["st"].session_state["search_directories"] = ["/persisted/path", "/tmp"]
namespace["initialize_search_directory_home_default"]()
assert namespace["st"].session_state["search_path"] == local_home
assert namespace["st"].session_state["search_result_path"] == local_home
assert namespace["st"].session_state["search_result_query"] == ""
assert namespace["st"].session_state["_hhs_search_home_context"] == "local"
namespace["st"].session_state["search_path"] = "$HOME/projects"
assert namespace["remember_search_directory"]("$HOME/projects") == f"{local_home}/projects"
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_result_query"] = "homeselect"
namespace["initialize_search_directory_home_default"]()
assert namespace["st"].session_state["search_path"] == "/srv/homeselect"
namespace["connected_host"] = "remote-box"
namespace["initialize_search_directory_home_default"]()
assert namespace["st"].session_state["search_path"] == "/remote/home"
assert namespace["st"].session_state["search_result_query"] == ""
assert namespace["st"].session_state["_hhs_search_home_context"] == "ssh:remote-box"
assert any("__HHS_UI_ENV__" in command for command, _kwargs in remote_commands)
assert namespace["remember_search_directory"]("$HHS_HOME/projects") == "/opt/hhs/projects"
assert namespace["normalize_search_directories"](
    ["/tmp", " /var ", "/tmp", "", "/opt"],
    "/home",
) == ["/home", "/tmp", "/var"]
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_directories"] = ["/tmp", "/var"]
assert namespace["search_directory_options"]() == ["/srv/homeselect", "/tmp", "/var"]
assert namespace["st"].session_state["search_path"] == "/srv/homeselect"
namespace["st"].session_state["search_query"] = None
namespace["st"].session_state["search_path"] = "$HHS_HOME/selected"
statuses_before = list(statuses)
namespace["apply_search_directory_change"]()
assert namespace["st"].session_state["search_path"] == "/opt/hhs/selected"
assert namespace["st"].session_state["search_directories"] == [
    "/opt/hhs/selected",
    "/srv/homeselect",
    "/tmp",
]
assert statuses == statuses_before
namespace["st"].session_state["search_query"] = None
namespace["st"].session_state["search_path"] = ""
namespace["submit_search_query"]()
assert namespace["st"].session_state["search_directories"] == [
    "/remote/home",
    "/opt/hhs/selected",
    "/srv/homeselect",
]
assert namespace["st"].session_state["search_result_query"] == ""
assert statuses[-1] == ("Enter a search query before searching.", "warn")
namespace["st"].session_state["search_query"] = "homeselect"
namespace["st"].session_state["search_path"] = "/srv/homeselect"
namespace["st"].session_state["search_type"] = "Files"
namespace["submit_search_query"]()
assert namespace["st"].session_state["search_result_query"] == "homeselect"
assert namespace["st"].session_state["search_result_path"] == "/srv/homeselect"
assert deleted_cache_tags[-1] == "search"
assert namespace["normalize_search_terms"](
    ["admin", " saridon ", "admin", "", "root"],
    "needle",
) == ["needle", "admin", "saridon"]
assert namespace["clean_search_term_value"](None) == ""
assert namespace["clean_search_term_value"]("None") == ""
assert namespace["normalize_search_terms"](["None", None, "admin"], None) == ["admin"]
namespace["st"].session_state["search_query"] = None
term_cache["search_terms:history"] = {"terms": ["saridon", "admin"]}
assert namespace["search_term_options"]() == ["saridon", "admin"]
assert namespace["st"].session_state["search_query"] is None
term_cache.clear()
cache_writes.clear()
namespace["st"].session_state["search_query"] = "admin"
assert namespace["search_term_options"]() == ["admin"]
assert namespace["remember_search_term"](" saridon ") == "saridon"
assert term_cache["search_terms:history"]["terms"] == ["saridon"]
assert cache_writes[-1] == (
    "search_terms:history",
    {"terms": ["saridon"]},
    900,
)
assert namespace["remember_search_term"](" admin ") == "admin"
assert term_cache["search_terms:history"]["terms"] == ["admin", "saridon"]
assert namespace["remember_search_term"]("saridon") == "saridon"
assert term_cache["search_terms:history"]["terms"] == ["saridon", "admin"]
namespace["st"].session_state["search_query"] = "None"
term_cache["search_terms:history"] = {"terms": ["None", "admin", None]}
assert namespace["search_term_options"]() == ["admin"]
assert namespace["st"].session_state["search_query"] is None
assert namespace["remember_search_term"](None) == ""
assert namespace["st"].session_state["search_query"] is None
assert namespace["normalized_search_option_values"]("Files", True, True, True) == (
    False,
    False,
    False,
)
assert namespace["normalized_search_option_values"]("Strings", True, False, True) == (
    True,
    False,
    True,
)
assert namespace["search_string_option_flags"](True, True, True) == ["-i", "-w", "-b"]
files_command = namespace["build_hhs_search_command"](
    "Files", "report", "/tmp/search root"
)
folders_command = namespace["build_hhs_search_command"](
    "Folders", "docs", "/tmp/search root"
)
strings_command = namespace["build_hhs_search_command"](
    "Strings", "needle value", "/tmp/search root"
)
strings_options_command = namespace["build_hhs_search_command"](
    "Strings", "needle value", "/tmp/search root", True, True, True
)
home_files_command = namespace["build_hhs_search_command"]("Files", "report", "$HOME")
home_child_command = namespace["build_hhs_search_command"](
    "Files", "report", "$HOME/Project Files"
)
for command in (files_command, folders_command, strings_command):
    assert 'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash";' in command
    assert 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-text.bash";' in command
    assert 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-search.bash";' in command
    assert "function __hhs_highlight() { cat -; };" in command
assert "__hhs_search_file '/tmp/search root' '*report*'" in files_command
assert "__HHS_SEARCH_RESULT__" in files_command
assert "stat -c %s" in files_command
assert '""|Searching\\ for*) ;;' in files_command
assert "__hhs_search_dir '/tmp/search root' '*docs*'" in folders_command
assert "__HHS_SEARCH_RESULT__" in folders_command
assert strings_command.endswith("__hhs_search_string '/tmp/search root' 'needle value'")
assert strings_options_command.endswith(
    "__hhs_search_string '/tmp/search root' -i -w -b 'needle value'"
)
assert '__hhs_search_file "${HOME:-.}"' in home_files_command
assert '__hhs_search_file "${HOME:-.}"/' in home_child_command
assert "'Project Files'" in home_child_command
assert "__HHS_SEARCH_RESULT__" not in strings_command
assert namespace["search_command_cache_key"]("Files", "*.mp4", "/tmp/search root") == (
    "command_tag:search:"
    + hashlib.md5(
        "Files\n*.mp4\n/tmp/search root\nFalse\nFalse\nFalse".encode("utf-8")
    ).hexdigest()
)
assert namespace["search_command_cache_key"](
    "Strings", "needle", "/tmp/search root", True, True, True
) == (
    "command_tag:search:"
    + hashlib.md5(
        "Strings\nneedle\n/tmp/search root\nTrue\nTrue\nTrue".encode("utf-8")
    ).hexdigest()
)
open_command = namespace["build_hhs_open_search_result_command"](
    "/tmp/search root/report.txt"
)
assert 'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash";' in open_command
assert "__hhs_open '/tmp/search root/report.txt'" in open_command
assert namespace["search_relative_path"](
    "/tmp/search root/docs/report.txt", "/tmp/search root"
) == "docs/report.txt"
assert namespace["search_relative_path"](
    "/tmp/other/report.txt", "/tmp/search root"
) == "/tmp/other/report.txt"
string_rows = namespace["parse_hhs_search_results"](
    'Searching for "regex" matching: "target" in "."\n'
    "/tmp/search root/report.txt:12:Alpha target line\n",
    "Strings",
    "/tmp/search root",
)
assert string_rows == [
    {
        "Type": "String",
        "Path": "report.txt",
        "FullPath": "/tmp/search root/report.txt",
        "Modified": "",
        "Size": "",
        "Line": "12",
        "LineNumber": "",
        "Match": "Alpha target line",
    }
]
assert namespace["parse_hhs_search_results"](
    "Searching for %primary_color%homeselect%primary_color% "
    "in %secondary_color%${HHS_HOME}%secondary_color%\n",
    "Files",
    "/tmp/search root",
) == []
assert namespace["parse_hhs_search_results"](
    '__HHS_SEARCH_RESULT__\tSearching for files matching: "*homeselect*" '
    'in "${HHS_HOME}"\t0\t\n',
    "Files",
    "/tmp/search root",
) == []
file_rows = namespace["parse_hhs_search_results"](
    "Searching for files matching: [movie] in .\n"
    "__HHS_SEARCH_RESULT__\t/tmp/search root/movie.mp4\t1710000000\t2048\n",
    "Files",
    "/tmp/search root",
)
assert file_rows == [
    {
        "Type": "File",
        "Path": "movie.mp4",
        "FullPath": "/tmp/search root/movie.mp4",
        "Modified": "mtime:1710000000",
        "Size": "2.0 KB",
        "Line": "",
        "LineNumber": "",
        "Match": "",
    }
]
folder_rows = namespace["parse_hhs_search_results"](
    "Searching for folders matching: [docs] in .\n"
    "__HHS_SEARCH_RESULT__\t/tmp/search root/docs\t1710000000\t\n",
    "Folders",
    "/tmp/search root",
)
assert folder_rows == [
    {
        "Type": "Folder",
        "Path": "docs",
        "FullPath": "/tmp/search root/docs",
        "Modified": "mtime:1710000000",
        "Size": "",
        "Line": "",
        "LineNumber": "",
        "Match": "",
    }
]
assert namespace["search_result_headers"]("Files") == ["Path", "Size", "Modified"]
assert namespace["search_result_headers"]("Folders") == ["Path", "Modified"]
assert namespace["search_result_headers"]("Strings") == ["Path", "Line", "Match"]
assert namespace["search_result_index_width"](0) == "1ch"
assert namespace["search_result_index_width"](9) == "1ch"
assert namespace["search_result_index_width"](100) == "3ch"
assert namespace["search_result_index_header"](100) == (
    '<th class="hhs-search-result-index" style="width: 3ch;"></th>'
)
assert namespace["search_result_index_cell"](12) == (
    '<td class="hhs-search-result-index">12</td>'
)
link = namespace["search_result_path_link"](string_rows[0])
assert 'class="hhs-search-result-path-link"' in link
assert "hhs_open_search_result=%2Ftmp%2Fsearch+root%2Freport.txt" in link
assert 'title="/tmp/search root/report.txt"' in link
assert 'data-hhs-open-path="/tmp/search root/report.txt"' in link
assert ">report.txt</a>" in link
rows = [{"Path": str(index)} for index in range(45)]
assert len(namespace["visible_search_rows"](rows)) == 20
namespace["increase_search_visible_count"]()
assert len(namespace["visible_search_rows"](rows)) == 40
assert namespace["search_loader_message"]("*.md", "/tmp/search root") == (
    "Searching for %primary_color%*.md%primary_color% "
    "in %secondary_color%/tmp/search root%secondary_color%"
)
assert namespace["filter_search_rows"](string_rows, "All", "missing") == string_rows
assert namespace["filter_search_rows"](string_rows, "Containing", "target") == string_rows
assert namespace["filter_search_rows"](string_rows, "Containing", "missing") == []
highlighted_line = namespace["colorize_search_result_line"](
    "Alpha target line", "target"
)
assert '<span class="hhs-log-filter-match">target</span>' in highlighted_line
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

  run grep -q "https://raw.githubusercontent.com/HS-Teams/homesetup/master/.VERSION" "${updater_file}"
  assert_success

  run grep -q "https://github.com/HS-Teams/homesetup/blob/master/.VERSION" "${updater_file}"
  assert_failure

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

# TC - 20
@test "when rendering keyed widgets then session state should not also be passed as defaults" {
  run grep -q 'default=st.session_state' "${ui_file}"
  assert_failure

  run grep -q 'value=st.session_state' "${ui_file}"
  assert_failure

  run grep -q 'index=.*session_state' "${ui_file}"
  assert_failure

  run python3 - <<'PY'
from pathlib import Path

source = Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
body = source.split("def render_table_filter_controls", 1)[1].split("\ndef ", 1)[0]
assert "st.session_state[key] = options[safe_index]" in body
assert "index=None" in body
assert "index=index" not in body
search_filter_body = source.split("def render_search_filters", 1)[1].split("\ndef ", 1)[0]
assert "key=\"search_filter\"" in search_filter_body
assert "index=None" in search_filter_body
main_view_body = source.split("def render_main_view", 1)[1].split("\ndef ", 1)[0]
assert "key=\"active_view\"" in main_view_body
assert "index=None" in main_view_body
PY
  assert_success
}
