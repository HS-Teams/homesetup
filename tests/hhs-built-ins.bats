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
  run __hhs_do 2 'printf "%s\n" alpha; false; printf "%s\n" omega'
  assert_failure
  [[ "${lines[0]}" == "alpha" ]]
  [[ "${lines[1]}" == "omega" ]]
  [[ "${lines[2]}" == "alpha" ]]
  [[ "${lines[3]}" == "omega" ]]
  assert_output --partial "Command failed on iteration 1:"
  assert_output --partial "Command failed on iteration 2:"
}
