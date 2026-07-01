#!/usr/bin/env bats

#  Script: hhs-command.bats
# Purpose: hhs-command tests.
# Created: Apr 27, 2025
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-built-ins.bash"
load "${HHS_FUNCTIONS_DIR}/hhs-command.bash"
load_bats_libs

# Avoid terminal-specific side effects during tests.
clear() { :; }

# shellcheck disable=SC2120
tput() {
  echo 120
}

setup_file() {
  if [[ -z "${HHS_HOME}" ]]; then
    export HHS_HOME="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"
  fi
}

setup() {
  export OLDIFS="${IFS}"
  unset EDITOR

  export HHS_DIR="${BATS_TEST_TMPDIR}/hhs-dir"
  mkdir -p "${HHS_DIR}"

  export HHS_CMD_FILE="${BATS_TEST_TMPDIR}/cmd.XXXXXX"
}

teardown() {
  [[ -f "${HHS_CMD_FILE}" ]] && rm -f "${HHS_CMD_FILE}"
  unset HHS_CMD_FILE
  unset EDITOR

  # Restore any function stubs defined during individual tests.
  unset -f __hhs_mselect 2>/dev/null || true
}

# TC - 1
@test "when-adding-commands-then-list-should-show-entries" {
  run __hhs_command -a run echo run
  assert_success
  assert_output --partial "Command saved: \"RUN\""

  run __hhs_command -a try echo try
  assert_success
  assert_output --partial "Command saved: \"TRY\""

  run __hhs_command -l
  assert_success
  assert_output --partial "Available commands (2):"
  assert_output --partial "Command RUN"
  assert_output --partial "Command TRY"
}

# TC - 2
@test "when-adding-existing-command-alias-then-should-replace-entry" {
  run __hhs_command -a test_cmd ls -lt
  assert_success
  assert_output --partial "Command saved: \"TEST_CMD\""

  run __hhs_command -a test_cmd ls -lta
  assert_success
  assert_output --partial "Command saved: \"TEST_CMD\""

  run cat "${HHS_CMD_FILE}"
  assert_success
  assert_output "Command TEST_CMD: ls -lta"

  run grep -c '^Command TEST_CMD:' "${HHS_CMD_FILE}"
  assert_success
  assert_output "1"
}

# TC - 2
@test "when-removing-command-by-index-then-should-update-file" {
  run __hhs_command -a run echo run
  assert_success
  run __hhs_command -a try echo try
  assert_success

  run __hhs_command -r 1
  assert_success
  assert_output --partial "Command (1) removed!"

  run cat "${HHS_CMD_FILE}"
  assert_success
  assert_output --partial "Command TRY: echo try"
  refute_output --partial "Command RUN: echo run"
}

# TC - 4
@test "when-removing-command-by-padded-index-then-should-update-file" {
  run __hhs_command -a run echo run
  assert_success
  run __hhs_command -a try echo try
  assert_success

  run __hhs_command -r 001
  assert_success
  assert_output --partial "Command (1) removed!"

  run cat "${HHS_CMD_FILE}"
  assert_success
  assert_output --partial "Command TRY: echo try"
  refute_output --partial "Command RUN: echo run"
}


# TC - 3
@test "when-removing-command-by-alias-then-should-update-file" {
  run __hhs_command -a run echo run
  assert_success
  run __hhs_command -a try echo try
  assert_success

  run __hhs_command -r run
  assert_success
  assert_output --partial "Command \"RUN\" removed!"

  run cat "${HHS_CMD_FILE}"
  assert_success
  assert_output --partial "Command TRY: echo try"
  refute_output --partial "Command RUN: echo run"
}

# TC - 4
@test "when-editing-commands-file-then-should-use-configured-editor" {
  export EDITOR=true

  run __hhs_command -e
  assert_success
  assert_output ""
  [[ -f "${HHS_CMD_FILE}" ]]
}

# TC - 5
@test "when-executing-command-by-index-then-should-run-expression" {
  run __hhs_command -a run echo run-executed
  assert_success

  run __hhs_command 1
  assert_success
  assert_output --partial "#> echo run-executed"
  assert_output --partial "run-executed"
}

# TC - 6
@test "when-executing-command-by-alias-then-should-run-expression" {
  run __hhs_command -a run echo alias-executed
  assert_success

  run __hhs_command run
  assert_success
  assert_output --partial "#> echo alias-executed"
  assert_output --partial "alias-executed"
}

# TC - 7
@test "when-selecting-command-from-menu-then-should-execute-selection" {
  run __hhs_command -a run echo menu-run
  assert_success
  run __hhs_command -a try echo menu-try
  assert_success

  __hhs_mselect() {
    local target_file="$1"
    printf '%s\n' "Command TRY: echo menu-try" >"${target_file}"
    return 0
  }

  run __hhs_command
  assert_success
  assert_output --partial "#> echo menu-try"
  assert_output --partial "menu-try"
}
