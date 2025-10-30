#!/usr/bin/env bats

#  Script: hhs-toml.bats
# Purpose: hhs-toml tests.
# Created: Dec 05, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-text.bash"
load "${HHS_FUNCTIONS_DIR}/hhs-toml.bash"
load_bats_libs

test_file=

setup() {

  test_file=$(mktemp)

  # Stub the toml entries
  echo "
    default.root.key.1 = any root value one
    default.root.key.2 = any root value two

    [tests]

    test.key.1 = any test value one
    test.key.2 = any test value two

    [my.group]

    valid_key_two = my valid value two
    valid_key_one = my valid value one
  " >> "${test_file}"
}

teardown() {
  [[ -f "${test_file}" ]] && \rm -f "${test_file}"
}

# TC - 1
@test "when-invoking-with-help-option-then-toml-get-should-print-usage" {
  run __hhs_toml_get -h
  assert_failure
  assert_output --partial "usage: __hhs_toml_get <file> <key> [group]"
}

# TC - 2
@test "when-invoking-with-missing-file-then-toml-get-should-raise-an-error" {
  run __hhs_toml_get ''
  assert_failure
  assert_output --partial "The file parameter must be provided."
}

# TC - 3
@test "when-invoking-with-missing-key-then-toml-get-should-raise-an-error" {
  run __hhs_toml_get "${test_file}" ''
  assert_failure
  assert_output --partial "The key parameter must be provided."
}

# TC - 4
@test "when-invoking-with-invalid-file-then-toml-get-should-raise-an-error" {
  run __hhs_toml_get "non-existent.toml" "any_key"
  assert_failure
  assert_output --partial "The file \"non-existent.toml\" does not exists or is empty."
}

# TC - 5
@test "when-invoking-with-with-incorrect-key-value-pair-then-should-raise-an-error" {
  run __hhs_toml_set "${test_file}" "test.key.1" "tests"
  assert_failure
  assert_output --partial "The key/value parameter must be on the form of 'key=value', but it was 'test.key.1'."
}

# TC - 6
@test "when-invoking-without-group-then-toml-get-should-get-it" {
  run __hhs_toml_get "${test_file}" "default.root.key.2"
  assert_success
  assert_output "default.root.key.2=any root value two"
}

# TC - 7
@test "when-invoking-with-with-correct-options-then-toml-get-should-get-it" {
  run __hhs_toml_get "${test_file}" "valid_key_one" "my.group"
  assert_success
  assert_output "valid_key_one=my valid value one"
}

# TC - 8
@test "when-invoking-with-with-correct-options-then-toml-set-should-set-it" {
  run __hhs_toml_set "${test_file}" "test.key.1=new updated value" "tests"
  assert_success
  assert_output ""

  run __hhs_toml_get "${test_file}" "test.key.1" "tests"
  assert_success
  assert_output "test.key.1=new updated value"
}
