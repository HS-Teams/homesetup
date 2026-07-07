#!/usr/bin/env bats

#  Script: hhs-aliases.bats
# Purpose: hhs-aliases tests.
# Created: Mar 02, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-text.bash"
load "${HHS_FUNCTIONS_DIR}/hhs-aliases.bash"
load_bats_libs

setup() {
  export HHS_DIR="${BATS_TEST_TMPDIR}/hhs-dir"
  export HHS_ALIASES_FILE="${BATS_TEST_TMPDIR}/aliases"
  mkdir -p "${HHS_DIR}"
  touch "${HHS_ALIASES_FILE}"
}

teardown() {
  unset HHS_ALIASES_FILE
}

# TC - 1
@test "when-invoking-with-help-option-then-should-print-usage-message" {
  run __hhs_aliases -h
  assert_failure
  assert_output --partial "usage: __hhs_aliases <alias> <alias_expr>"
}

# TC - 2
@test "when-adding-non-existent-valid-alias-then-should-add-it" {
  run __hhs_aliases 'hhs-bats' ls -la
  assert_success
  assert_output --partial "Alias set: \"hhs-bats\" is 'ls -la'"
  ised "/^alias hhs-bats=.*$/d" "${HHS_ALIASES_FILE}"
}

# TC - 3
@test "when-removing-an-invalid-alias-then-should-raise-an-error" {
  run __hhs_aliases -r 'hhs-bats'
  assert_failure
  assert_output  --partial "Alias not found: \"hhs-bats\""
}

# TC - 4
@test "when-removing-an-existing-alias-then-should-remove-it" {
  __hhs_aliases 'hhs-bats' 'ls -la'
  run __hhs_aliases -r 'hhs-bats'
  assert_success
  assert_output --partial "Alias removed: \"hhs-bats\""
}

# TC - 5
@test "when-removing-an-alias-only-saved-on-disk-then-should-remove-it" {
  printf "alias hhs-bats='ls -la'\n" >> "${HHS_ALIASES_FILE}"
  run __hhs_aliases -r 'hhs-bats'
  assert_success
  assert_output --partial "Alias removed: \"hhs-bats\""
  refute grep -q "^alias hhs-bats=.*$" "${HHS_ALIASES_FILE}"
}
