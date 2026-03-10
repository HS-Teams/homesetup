#!/usr/bin/env bats

#  Script: hhs-history.bats
# Purpose: __hhs_history tests.
# Created: Mar 10, 2026
#  Author: OpenAI Assistant
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-shell-utils.bash"
load_bats_libs

# @function: Stub the shell history builtin so tests can control the input.
function history() {
  cat <<'EOF'
  12  [hjunior, 2026-03-09 10:00:00] ls -la
  18  [hjunior, 2026-03-10 08:00:00] git status
  22  2026-03-10 09:00:00 ls -la
  31  [hjunior, 2026-03-10T09:30:00] npm test
EOF
}

# TC - 1
@test "when-listing-history-then-timestamps-are-replaced-by-arrow-format" {
  run __hhs_history

  assert_success
  assert_output --partial '...............'
  assert_output --partial ''
  assert_output --partial 'git status'
  assert_output --partial 'ls -la'
  assert_output --partial 'npm test'
  refute_output --partial '2026-03-10'
  refute_output --partial '09:30:00'
  refute_output --partial '[hjunior,'
}

# TC - 2
@test "when-filtering-history-then-only-matching-commands-are-rendered" {
  run __hhs_history "git|npm"

  assert_success
  assert_output --partial 'git status'
  assert_output --partial 'npm test'
  refute_output --partial 'ls -la'
}

# TC - 3
@test "when-filter-matches-no-history-command-then-command-fails" {
  run __hhs_history "docker"

  assert_failure
  assert_output ''
}
