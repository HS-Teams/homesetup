#!/usr/bin/env bats

#  Script: hhs-shopt.bats
# Purpose: __hhs_shopt tests.
# Created: Nov 28, 2024
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-text.bash"
load "${HHS_FUNCTIONS_DIR}/hhs-toml.bash"
load "${HHS_FUNCTIONS_DIR}/hhs-shell-utils.bash"
load_bats_libs

# Test suite for the `__hhs_shopt` function
# @purpose: Validate the behavior of the __hhs_shopt function with various arguments.

# Setup and teardown functions
setup() {
  # Create any required temporary resources or configurations
  export HHS_SHOPTS_FILE="shopt_test_output.txt"
  shopt | awk '{print $1" = "$2}' >"${HHS_SHOPTS_FILE}"
}

teardown() {
  # Clean up temporary resources or configurations
  rm -f "${HHS_SHOPTS_FILE}"
}

# TC - 1
@test "display-all-on-and-off-options" {
  run __hhs_shopt
  assert_success
  assert_output --partial "OFF"
  assert_output --partial "ON"
}

# TC - 2
@test "display-all-settable-options-with-p" {
  run __hhs_shopt -p
  assert_success
  assert_output --partial "OFF"
  assert_output --partial "ON"
}

# TC - 2.1
@test "when-listing-with-p-then-should-load-saved-options" {
  printf "nocaseglob = on\n" >"${HHS_SHOPTS_FILE}"
  shopt -u nocaseglob

  __hhs_shopt -p >"${BATS_TEST_TMPDIR}/shopt-output.txt"
  run grep -E "ON.*nocaseglob" "${BATS_TEST_TMPDIR}/shopt-output.txt"
  assert_success

  run shopt -q nocaseglob
  assert_success
}

# TC - 3
@test "display-all-unset-options" {
  run __hhs_shopt off
  assert_success
  assert_output --partial "OFF"
  run ! assert_output --partial "ON"
}

# TC - 4
@test "display-all-set-options" {
  run __hhs_shopt on
  assert_success
  assert_output --partial "ON"
  run ! assert_output --partial "OFF"
}

# TC - 5
@test "when-set-options-with-s" {
  run __hhs_shopt -s cdspell
  assert_success
  assert_output --partial "Shell option cdspell set to on"
  run __hhs_toml_get "${HHS_SHOPTS_FILE}" "cdspell"
  assert_output --partial "cdspell=on"
}

# TC - 6
@test "when-unset-options-with-u" {
  run __hhs_shopt -u cdspell
  assert_success
  assert_output --partial "Shell option cdspell set to off"
  run __hhs_toml_get "${HHS_SHOPTS_FILE}" "cdspell"
  assert_output --partial "cdspell=off"
}

# TC - 7
@test "when-output-is-suppressed-with-q-for-set-options" {
  __hhs_shopt -s cdspell
  run __hhs_shopt -q cdspell
  assert_success
  [ -z "$output" ]
  [ -z "$error" ]
}

# TC - 8
@test "when-output-is-suppressed-with-q-for-unset-options" {
  __hhs_shopt -u cdspell
  run __hhs_shopt -q cdspell
  assert_failure
  [ -z "$output" ]
  [ -z "$error" ]
}

# TC - 9
@test "when-restrict-optname-values-with-o" {
  run __hhs_shopt -o
  assert_success
  assert_output --partial "errexit"
}

# TC - 10
@test "when-handle-invalid-options-gracefully" {
  run __hhs_shopt -z
  assert_failure
  assert_output --partial "-z: invalid shell option"
}
