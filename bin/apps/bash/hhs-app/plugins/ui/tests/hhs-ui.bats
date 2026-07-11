#!/usr/bin/env bats

#  Script: hhs-ui.bats
# Purpose: HomeSetup Streamlit UI core tests.
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

@test "when installing HomeSetup then Streamlit should be included as a Python package" {
  assert_file_contains_many "${HHS_REPO_DIR}/install.bash" \
"'streamlit'" "'ttyd'"
}

# TC - 2

@test "when uninstalling HomeSetup then Streamlit should be included as a removable Python package" {
  assert_file_contains_many "${HHS_REPO_DIR}/uninstall.bash" \
"'streamlit'" "REQUIRED_PACKAGES=(" "'ttyd'" "uninstall_required_packages"
}

@test "when loading shell environment then ttyd should be a default developer tool" {
  assert_file_contains "${bash_env_file}" "'ttyd'"
}

# TC - 4

@test "when registering plugins then ui plugin should expose required hhs functions" {
  assert_file_contains_many "${ui_plugin_file}" \
'^function help()' '^function version()' '^function cleanup()' '^function execute()'
  assert_file_contains_many "${hspm_plugin_file}" \
'reinstall <package...>' 'reinstall_recipe'
}

# TC - 4

@test "when installing Ollama on Linux then hspm should use the current official installer URL" {
  ollama_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/ollama.recipe"
  ollama_darwin_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/ollama.recipe"

  assert_file_contains "${ollama_recipe_file}" 'https://ollama.com/install.sh'

  assert_file_not_contains "${ollama_recipe_file}" 'OllamaInstall.sh'

  assert_file_contains_many "${ollama_recipe_file}" \
'systemctl stop ollama' "pkill -f 'ollama serve'"
  assert_file_contains "${ollama_darwin_recipe_file}" 'brew services stop ollama'
}

# TC - 5

@test "when loading hspm recipes then Bash syntax should be valid" {
  run bash --noprofile --norc -c '
    for recipe in "$1"/bin/apps/bash/hhs-app/plugins/hspm/recipes/*/*.recipe; do
      bash -n "${recipe}" || exit 1
    done
    for recipe in "$1"/bin/apps/bash/hhs-app/plugins/hspm/recipes/*/*.recipe; do
      default_recipe="${recipe%/*}/default.recipe"
      bash --noprofile --norc -c "
        set -u
        source \"\$1\"
        source \"\$2\"
        declare -F _depends_ _install_ _uninstall_ _which_ >/dev/null
      " -- "${default_recipe}" "${recipe}" || exit 1
    done
    if command -v shellcheck >/dev/null 2>&1; then
      shellcheck -e SC1090,SC1091 "$1"/bin/apps/bash/hhs-app/plugins/hspm/recipes/*/*.recipe
    fi
  ' -- "${HHS_REPO_DIR}"
  assert_success
}

# TC - 6

@test "when reviewing hspm recipes then known stale recipe targets should be updated" {
  nvm_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/nvm.recipe"
  vue_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Darwin/vue.recipe"
  jenkins_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/jenkins.recipe"

  assert_file_contains "${nvm_recipe_file}" 'https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.5/install.sh'

  assert_file_not_contains "${nvm_recipe_file}" 'creationix/nvm'

  assert_file_contains "${vue_recipe_file}" 'npm install -g @vue/cli'

  assert_file_contains_many "${jenkins_recipe_file}" \
    'openjdk-21-jre' 'jenkins.io-2026.key'
}

@test "when reviewing hspm recipes then install and uninstall workflows should be safe" {
  recipes_dir="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes"
  darwin_default="${recipes_dir}/Darwin/default.recipe"
  colima_recipe="${recipes_dir}/Darwin/colima.recipe"
  qt_recipe="${recipes_dir}/Darwin/qt.recipe"
  docker_recipe="${recipes_dir}/Linux/docker.recipe"
  ollama_recipe="${recipes_dir}/Linux/ollama.recipe"

  assert_file_contains "${darwin_default}" 'list --formula "$1"'
  assert_file_not_contains "${darwin_default}" 'info "$@"'
  assert_file_contains_many "${colima_recipe}" \
    'brew list --formula "${package}"' 'colima stop' 'brew uninstall "${package}"'
  assert_file_not_contains_many "${colima_recipe}" \
    'brew deps "$@"' 'cli-plugins/" -type f -print -delete'
  assert_file_contains_many "${qt_recipe}" \
    'if ! brew install qt; then' 'touch "${HHS_PATHS_FILE}"'
  assert_file_contains_many "${docker_recipe}" \
    "distribution='ubuntu'" "distribution='debian'" 'docker.sources' 'docker-compose-v2'
  assert_file_not_contains "${docker_recipe}" 'download.docker.com/linux/ubuntu'
  assert_file_contains_many "${ollama_recipe}" \
    'mktemp "${TMPDIR:-/tmp}/ollama-install.XXXXXX"' 'systemctl disable ollama' \
    'userdel ollama'
  assert_file_not_contains "${ollama_recipe}" 'ollama uninstall'
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

@test "when hspm has a stale OS environment then list uses the execution host" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_LOG_DIR="${1}/log"
    export HHS_MY_OS="Darwin"
    export HHS_MY_OS_RELEASE="test"
    export HHS_MY_OS_PACKMAN="test-packman"
    export HHS_DEV_TOOLS=""
    export HHS_HIGHLIGHT_COLOR=""
    export BLUE="" GREEN="" NC="" ORANGE="" RED="" WHITE="" YELLOW=""
    export OLDIFS="${IFS}"
    export PLUGINS_DIR="${1}/plugins"
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}" "${1}/bin" \
      "${PLUGINS_DIR}/hspm/recipes/Linux" "${PLUGINS_DIR}/hspm/recipes/Darwin"
    printf "%s\\n" "#!/usr/bin/env bash" "printf \"Linux\\n\"" > "${1}/bin/uname"
    chmod +x "${1}/bin/uname"
    export PATH="${1}/bin:${PATH}"
    touch "${PLUGINS_DIR}/hspm/recipes/Linux/linux-only.recipe"
    touch "${PLUGINS_DIR}/hspm/recipes/Darwin/darwin-only.recipe"
    touch "${PLUGINS_DIR}/hspm/catalog.toml"
    function usage() { return "${1:-0}"; }
    function quit() { return "${1:-0}"; }
    function __hhs_errcho() { printf "%s\\n" "$*" >&2; }
    function __hhs_toml_get() { printf "%s\\n" "about=Linux test package"; }
    source "${2}"
    execute list
    [[ "${HHS_MY_OS}" == "Linux" ]]
    [[ "$(hspm_recipe_path "linux-only@21")" == "${PLUGINS_DIR}/hspm/recipes/Linux/linux-only.recipe" ]]
  ' -- "${BATS_TEST_TMPDIR}" "${hspm_plugin_file}"
  assert_success
  assert_output --partial "Listing all available hspm 'Linux' packages"
  assert_output --partial "linux-only"
  refute_output --partial "darwin-only"
  refute_output --partial "Darwin"
  assert_file_contains_many "${hspm_plugin_file}" \
    'function hspm_recipe_path' \
    'HHS_MY_OS="\$(uname -s)"'
}

@test "when listing Temurin then supported Java versions are selectable" {
  temurin_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/temurin.recipe"
  legacy_recipe_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/recipes/Linux/adoptium17.recipe"
  hspm_catalog_file="${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/hspm/catalog.toml"

  run bash --noprofile --norc -c '
    source "$1"
    _catalog_
    _temurin_version_ temurin@21
  ' -- "${temurin_recipe_file}"
  assert_success
  assert_output --partial "temurin@17"
  assert_output --partial "temurin@21"
  refute [ -e "${legacy_recipe_file}" ]
  assert_file_contains_many "${hspm_catalog_file}" '[temurin]' '[ollama]'
}

# TC - 8

@test "when syncing hspm then only untracked user packages are added to recovery" {
  run bash --noprofile --norc -c '
    set -u
    export APP_NAME="hhs"
    export HHS_DIR="${1}/hhs"
    export HHS_LOG_DIR="${1}/log"
    export HHS_MY_OS="Darwin"
    export HHS_MY_OS_RELEASE="test"
    export HHS_MY_OS_PACKMAN="brew"
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
    mkdir -p "${HHS_DIR}" "${HHS_LOG_DIR}"
    printf "%s\n" "test:already-tracked" > "${HHS_DIR}/.hspm"
    function usage() { return "${1:-0}"; }
    function quit() { return "${1:-0}"; }
    function __hhs_errcho() { printf "%s\n" "$*" >&2; }
    function brew() {
      printf "%s\n" "already-tracked" "new-package" "new-package"
    }
    source "${2}"
    execute sync
  ' -- "${BATS_TEST_TMPDIR}" "${hspm_plugin_file}"
  assert_success
  assert_output --partial 'Synchronized 1 user-installed package(s) from brew.'
  assert_file_contains "${BATS_TEST_TMPDIR}/hhs/.hspm" 'test:already-tracked'
  assert_file_contains "${BATS_TEST_TMPDIR}/hhs/.hspm" 'test:new-package'
}

# TC - 9

@test "when connected to SSH then HSPM commands should use the remote command path" {
  run python3 - "${HHS_REPO_DIR}" <<'PY'
import __future__
import ast
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
hspm_ui_source = (repo / "bin/apps/py/hhs_ui/features/hhs_app_ui.py").read_text()
streamlit_ui_source = (repo / "bin/apps/py/hhs_ui/streamlit_ui.py").read_text()
ssh_runtime_source = (repo / "bin/apps/py/hhs_ui/features/ssh_runtime.py").read_text()
command_catalog_source = (repo / "bin/apps/py/hhs_ui/execution/command_catalog.py").read_text()

for function_name in (
    "start_pending_hhs_hspm_action",
    "render_hhs_hspm_catalog_slide",
    "render_hhs_hspm_recovery_slide",
):
    body = hspm_ui_source.split(f"def {function_name}", 1)[1].split("\ndef ", 1)[0]
    assert "force_local=False" in body, function_name

home_tool_action = streamlit_ui_source.split(
    "def execute_pending_home_tool_action", 1
)[1].split("\ndef ", 1)[0]
assert "build_hhs_hspm_command(operation, tool_name)" in home_tool_action
assert "force_local=False" in home_tool_action
assert "HHS_HSPM_ENV_OUTPUT_MARKER" in command_catalog_source

hspm_ui_tree = ast.parse(hspm_ui_source)
environment_parser = next(
    node
    for node in hspm_ui_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "parse_hhs_hspm_environment"
)
parser_namespace = {
    "HHS_HSPM_ENV_OUTPUT_MARKER": "__HHS_HSPM_ENV__",
    "strip_ansi": lambda value: re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value),
}
exec(
    compile(
        ast.Module(body=[environment_parser], type_ignores=[]),
        "hhs_app_ui.py",
        "exec",
        flags=__future__.annotations.compiler_flag,
    ),
    parser_namespace,
)
assert parser_namespace["parse_hhs_hspm_environment"](
    "__HHS_HSPM_ENV__\nHHS_MY_OS\tLinux\nHHS_MY_OS_PACKMAN\tapt-get\n"
) == {"HHS_MY_OS": "Linux", "HHS_MY_OS_PACKMAN": "apt-get"}

assert "hhs_hspm_catalog_recipes_v2" in (
    repo / "bin/apps/py/hhs_ui/core/ui_definitions.py"
).read_text()

tree = ast.parse(ssh_runtime_source)
function = next(
    node
    for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "effective_bash_command"
)
namespace = {
    "selected_ssh_host": lambda: "remote-host",
    "selected_host_is_local": lambda _host: False,
    "selected_ssh_host_is_connected": lambda _host: True,
    "build_ssh_wrapped_command": lambda command, host: f"{host}:{command}",
}
exec(compile(ast.Module(body=[function], type_ignores=[]), "ssh_runtime.py", "exec"), namespace)
assert namespace["effective_bash_command"]("__hhs hspm execute list") == (
    "remote-host:__hhs hspm execute list"
)
PY
  assert_success
}

# TC - 4

@test "when loading Streamlit UI source then Python syntax should be valid" {
  run python3 -c 'import ast, pathlib; ast.parse(pathlib.Path("bin/apps/py/hhs_ui/streamlit_ui.py").read_text())'
  assert_success

  assert_file_contains_many "${ui_file}" \
'^import os$' '^from pathlib import Path$' '^import sys$' \
    'sys.path.insert(0, str(Path(__file__).resolve().parents\[1\]))'
}

@test "when loading Streamlit UI imports then package reloads should not run at startup" {
  assert_file_contains_many "${ui_file}" \
'^import hhs_ui$' '^import hhs_ui.core.constants as hhs_ui_constants$'
  assert_file_not_contains_many "${ui_file}" \
'import importlib' 'importlib.reload'
}
