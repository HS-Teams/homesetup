#!/usr/bin/env bats

#  Script: hhs-built-ins.bats
# Purpose: hhs built-ins tests.
# Created: Mar 26, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-built-ins.bash"
load_bats_libs

setup_file() {
  if [[ -z "${HHS_HOME}" ]]; then
    export HHS_HOME="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"
  fi
}

setup() {
  export HHS_ENV_FILE="${BATS_TEST_TMPDIR}/.env"
  export HHS_DIR="${BATS_TEST_TMPDIR}"
}

@test "when-resetting-then-ui-disposable-files-should-be-selectable" {
  local choices_file

  export HHS_BACKUP_DIR="${BATS_TEST_TMPDIR}/backup"
  export HHS_CACHE_DIR="${BATS_TEST_TMPDIR}/cache"
  export HHS_KEY_BINDINGS="${BATS_TEST_TMPDIR}/key-bindings"
  export HHS_LOG_DIR="${BATS_TEST_TMPDIR}/log"
  export HHS_OLLAMA_HISTORY_FILE="${BATS_TEST_TMPDIR}/ollama-history"
  export HHS_OLLAMA_PROMPT_FILE="${BATS_TEST_TMPDIR}/ollama-prompt"
  export HHS_SETUP_FILE="${BATS_TEST_TMPDIR}/setup"
  export HHS_SHOPTS_FILE="${BATS_TEST_TMPDIR}/shopts"
  export TMPDIR="${BATS_TEST_TMPDIR}/tmp/"
  choices_file="${BATS_TEST_TMPDIR}/reset-choices"
  mkdir -p "${HHS_BACKUP_DIR}" "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}" "${TMPDIR}"

  run bash --noprofile --norc -c '
    choices_file="$2"
    source "${1}/bin/apps/bash/hhs-app/functions/built-ins.bash"
    function __hhs_has() { return 1; }
    function __hhs_mchoose() {
      shift 2
      printf "%s\n" "$@" > "${choices_file}"
      return 1
    }
    reset
  ' -- "${HHS_HOME}" "${choices_file}"
  assert_success
  run grep -Fx "${HHS_CACHE_DIR}/*.*" "${choices_file}"
  assert_success
  run grep -Fx "${HHS_CACHE_DIR}/.*" "${choices_file}"
  assert_failure
}

@test "when-resetting-selected-ui-cache-pattern-then-reset-should-remove-cache-artifacts" {
  local search_dir stdout_file state_file

  export HHS_BACKUP_DIR="${BATS_TEST_TMPDIR}/backup"
  export HHS_CACHE_DIR="${BATS_TEST_TMPDIR}/cache"
  export HHS_KEY_BINDINGS="${BATS_TEST_TMPDIR}/key-bindings"
  export HHS_LOG_DIR="${BATS_TEST_TMPDIR}/log"
  export HHS_OLLAMA_HISTORY_FILE="${BATS_TEST_TMPDIR}/ollama-history"
  export HHS_OLLAMA_PROMPT_FILE="${BATS_TEST_TMPDIR}/ollama-prompt"
  export HHS_SETUP_FILE="${BATS_TEST_TMPDIR}/setup"
  export HHS_SHOPTS_FILE="${BATS_TEST_TMPDIR}/shopts"
  export TMPDIR="${BATS_TEST_TMPDIR}/tmp"
  mkdir -p "${HHS_BACKUP_DIR}" "${HHS_CACHE_DIR}" "${HHS_LOG_DIR}" "${TMPDIR}"
  search_dir="${HHS_CACHE_DIR}/hhs-search-open.dir"
  stdout_file="${HHS_CACHE_DIR}/search_command-stdout.log"
  state_file="${HHS_CACHE_DIR}/streamlit-ui-state.json"
  mkdir -p "${search_dir}"
  printf '%s\n' "output" > "${stdout_file}"
  printf '%s\n' "{}" > "${state_file}"

  run bash --noprofile --norc -c '
    source "${1}/bin/apps/bash/hhs-app/functions/built-ins.bash"
    function clear() { :; }
    function __hhs_has() { return 1; }
    function __hhs_mchoose() {
      printf "%s " "${HHS_CACHE_DIR}/*.*" > "$1"
      return 0
    }
    reset
  ' -- "${HHS_HOME}"
  assert_success
  [[ ! -e "${search_dir}" ]]
  [[ ! -e "${stdout_file}" ]]
  [[ ! -e "${state_file}" ]]
}

# TC - 1
@test "when-showing-help-then-do-should-print-usage" {
  run __hhs_do --help
  assert_failure
  assert_output --partial "usage: __hhs_do <N> <command; command; ...>"
  assert_output --partial "Examples:"
}

# TC - 2
@test "when-repeating-a-command-sequence-then-do-should-run-it-n-times" {
  run __hhs_do 2 'printf "%s\n" alpha; printf "%s\n" beta'
  assert_success
  [[ "${lines[0]}" == "alpha" ]]
  [[ "${lines[1]}" == "beta" ]]
  [[ "${lines[2]}" == "alpha" ]]
  [[ "${lines[3]}" == "beta" ]]
}

# TC - 3
@test "when-count-is-invalid-then-do-should-fail" {
  run __hhs_do 0 'printf "%s\n" alpha'
  assert_failure
  assert_output --partial "Argument must be a positive integer."
}

# TC - 4
@test "when-command-sequence-fails-then-do-should-continue" {
  local command_line
  local -a command_lines=()

  run __hhs_do 2 'printf "%s\n" alpha; false; printf "%s\n" omega'
  assert_failure
  while IFS= read -r command_line; do
    command_lines[${#command_lines[@]}]="${command_line}"
  done < <(printf '%s\n' "${output}" | grep -E '^(alpha|omega)$')
  [[ "${command_lines[0]}" == "alpha" ]]
  [[ "${command_lines[1]}" == "omega" ]]
  [[ "${command_lines[2]}" == "alpha" ]]
  [[ "${command_lines[3]}" == "omega" ]]
  assert_output --partial "Command failed on iteration 1:"
  assert_output --partial "Command failed on iteration 2:"
}

# TC - 5
@test "when-adding-env-var-then-env-file-should-contain-export" {
  run __hhs_envs --add "HHS_TEST_ENV=custom value"
  assert_success
  assert_output --partial "Environment variable saved: \"HHS_TEST_ENV\""
  run grep -qx 'export HHS_TEST_ENV="custom value"' "${HHS_ENV_FILE}"
  assert_success
}

# TC - 6
@test "when-adding-existing-env-var-then-env-file-should-update-it" {
  printf '%s\n' 'HHS_TEST_ENV=old' 'export OTHER_ENV="keep"' > "${HHS_ENV_FILE}"

  run __hhs_envs -a "HHS_TEST_ENV=new value"
  assert_success
  run grep -qx 'export HHS_TEST_ENV="new value"' "${HHS_ENV_FILE}"
  assert_success
  run grep -q '^HHS_TEST_ENV=old$' "${HHS_ENV_FILE}"
  assert_failure
}

# TC - 7
@test "when-deleting-env-var-then-env-file-should-remove-it" {
  printf '%s\n' 'export HHS_TEST_ENV="old"' 'export OTHER_ENV="keep"' > "${HHS_ENV_FILE}"

  run __hhs_envs --del HHS_TEST_ENV
  assert_success
  assert_output --partial "Environment variable removed: \"HHS_TEST_ENV\""
  run grep -q 'HHS_TEST_ENV' "${HHS_ENV_FILE}"
  assert_failure
  run grep -qx 'export OTHER_ENV="keep"' "${HHS_ENV_FILE}"
  assert_success
}

# TC - 8
@test "when-adding-env-var-with-assignment-token-then-env-file-should-contain-export" {
  run __hhs_envs --add HHS_TEST_ENV=custom
  assert_success
  run grep -qx 'export HHS_TEST_ENV="custom"' "${HHS_ENV_FILE}"
  assert_success
}

# TC - 9
@test "when-adding-env-var-with-name-equals-value-tokens-then-envs-should-fail" {
  run __hhs_envs --add HHS_TEST_ENV = custom
  assert_failure
  assert_output --partial "Use NAME=VALUE format."
}

# TC - 10
@test "when-adding-env-var-with-name-equals-prefix-then-envs-should-fail" {
  run __hhs_envs --add HHS_TEST_ENV= custom
  assert_failure
  assert_output --partial "Use NAME=VALUE format."
}

# TC - 11
@test "when-adding-env-var-with-equals-value-token-then-envs-should-fail" {
  run __hhs_envs --add HHS_TEST_ENV =custom
  assert_failure
  assert_output --partial "Use NAME=VALUE format."
}

# TC - 12
@test "when-updating-env-var-with-interactive-mv-alias-then-envs-should-not-prompt" {
  printf '%s\n' 'export HHS_TEST_ENV="old"' > "${HHS_ENV_FILE}"
  shopt -s expand_aliases
  alias mv='mv -iv'

  run __hhs_envs --add HHS_TEST_ENV=new
  assert_success
  refute_output --partial "overwrite"
  run grep -qx 'export HHS_TEST_ENV="new"' "${HHS_ENV_FILE}"
  assert_success
}

# TC - 13
@test "when-deleting-missing-env-var-then-envs-should-fail" {
  run __hhs_envs --del HHS_MISSING_ENV
  assert_failure
  assert_output --partial "Environment variable not found: \"HHS_MISSING_ENV\""
}

# TC - 14
@test "when-adding-invalid-env-var-then-envs-should-fail" {
  run __hhs_envs --add 1INVALID=value
  assert_failure
  assert_output --partial "Invalid environment variable name: \"1INVALID\""
}

# TC - 15
@test "when-editing-env-file-with-long-option-then-envs-should-open-editor" {
  export EDITOR=true

  run __hhs_envs --edit
  assert_success
  [[ -f "${HHS_ENV_FILE}" ]]
}
