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

  assert_file_contains_many "${ui_file}" \
'^import os$' '^from pathlib import Path$' '^import sys$' \
    'sys.path.insert(0, str(Path(__file__).resolve().parents\[1\]))'
}

@test "when loading Streamlit UI imports then package reloads should not run at startup" {
  assert_file_contains_many "${ui_file}" \
'^import hhs_ui$' '^import hhs_ui.constants as hhs_ui_constants$'
  assert_file_not_contains_many "${ui_file}" \
'import importlib' 'importlib.reload'
}
