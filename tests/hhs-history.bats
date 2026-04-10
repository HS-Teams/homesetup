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

# @function: Stub terminal width for deterministic truncation checks.
# shellcheck disable=SC2329
function tput() {
  if [[ "$1" == "cols" ]]; then
    echo '60'
    return 0
  fi

  return 1
}

# @function: Stub the shell history builtin so tests can control the input.
# shellcheck disable=SC2329
function history() {
  cat <<'EOF'
  12  [hjunior, 2026-03-09 10:00:00] ls -la
  18  [hjunior, 2026-03-10 08:00:00] git status
  22  2026-03-10 09:00:00 ls -la
  31  [hjunior, 2026-03-10T09:30:00] npm test
  44  [hjunior, 2026-03-10 10:15:00] verylongcommand-with-many-arguments --flag value
  52  [hjunior, 2026-03-10 12:00:00] echo a
b
  60  [hjunior, 2026-03-10 12:10:00] \rm -rf .gradle-local/
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
  assert_output --partial 'verylongcom...'
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
@test "when-history-has-duplicate-commands-then-only-the-oldest-entry-is-rendered" {
  run __hhs_history "ls -la"

  assert_success
  assert_output --partial '  12'
  refute_output --partial '  22'
}

# TC - 4
@test "when-filter-matches-no-history-command-then-command-fails" {
  run __hhs_history "docker"

  assert_failure
  assert_output ''
}

# TC - 5
@test "when-history-command-spans-multiple-lines-then-newlines-are-replaced-by-spaces" {
  run __hhs_history "echo a b"

  assert_success
  assert_output --partial 'echo a b'
}

# TC - 6
@test "when-history-command-contains-backslash-r-then-it-is-rendered-literally" {
  run __hhs_history

  assert_success
  assert_output --partial '\rm -rf .gr...'
}

# TC - 7
@test "when-history-command-contains-quotes-and-exclamation-then-it-is-rendered-literally" {
  function tput() {
    if [[ "$1" == "cols" ]]; then
      echo '120'
      return 0
    fi

    return 1
  }

  # shellcheck disable=SC2329
  function history() {
    cat <<'EOF'
  22  [hjunior, 2026-03-21 15:23:04]  rg 'Encounter: Relay Saboteur attacks you!'
EOF
  }

  run __hhs_history "Encounter: Relay Saboteur attacks you!"

  assert_success
  assert_output --partial "rg 'Encounter: Relay Saboteur attacks you!'"
}

# TC - 8
@test "when-history-contains-non-utf8-bytes-then-parser-does-not-fail" {
  # shellcheck disable=SC2329
  function history() {
    printf '  22  [hjunior, 2026-03-21 15:23:04]  rg bad\377cmd\n'
  }

  run __hhs_history

  assert_success
  refute_output --partial 'towc:'
}
