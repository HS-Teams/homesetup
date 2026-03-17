#!/usr/bin/env bats

#  Script: hhs-security.bats
# Purpose: hhs-security tests.
# Created: Mar 17, 2026
#  Author: OpenAI Assistant
# License: MIT

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-security.bash"
load_bats_libs

# TC - 1
@test "when-invoking-pwgen-help-then-prints-usage-and-exits-successfully" {
  run __hhs_pwgen --help

  assert_success
  assert_output --partial "usage: __hhs_pwgen"
  assert_output --partial "-h, --help"
}

# TC - 2
@test "when-invoking-pwgen-with-unknown-option-then-fails-with-help-hint" {
  run __hhs_pwgen --unknown

  assert_failure
  assert_output --partial "Unknown option: --unknown"
  assert_output --partial "usage: __hhs_pwgen"
}

# TC - 3
@test "when-pwgen-length-value-is-missing-then-fails-with-clear-error" {
  run __hhs_pwgen --length

  assert_failure
  assert_output --partial "Missing value for --length"
}

# TC - 4
@test "when-pwgen-type-value-is-missing-then-fails-with-clear-error" {
  run __hhs_pwgen --type

  assert_failure
  assert_output --partial "Missing value for --type"
}

# TC - 5
@test "when-pwgen-length-is-zero-then-fails-validation" {
  run __hhs_pwgen --length 0 --type 4

  assert_failure
  assert_output --partial "Password length must be a positive integer"
}
