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

# Set an explicit output width for deterministic truncation checks.
export COLUMNS=60

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
@test "when-history-has-duplicate-commands-then-each-event-index-is-rendered" {
  run __hhs_history "ls -la"

  assert_success
  assert_output --partial '  12'
  assert_output --partial '  22'
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
  COLUMNS=120

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

# TC - 9
@test "when-listing-history-non-interactively-then-helper-clears-before-loading-file" {
  export HISTFILE="${BATS_TEST_TMPDIR}/history"
  touch "${HISTFILE}"
  call_log="${BATS_TEST_TMPDIR}/history-calls"

  # shellcheck disable=SC2329
  function history() {
    printf '%s\n' "$*" >>"${call_log}"
    case "$1" in
    -c | -r)
      return 0
      ;;
    esac

    cat <<'EOF'
   1  gcm first command
   2  echo second command
EOF
  }

  run __hhs_history

  assert_success
  assert_output --partial '   1'
  assert_output --partial 'gcm first'

  run sed -n '1,2p' "${call_log}"
  assert_success
  assert_line --index 0 '-c'
  assert_line --index 1 "-r ${HISTFILE}"
}

# TC - 10
@test "when-non-interactive-terminal-width-is-unavailable-then-history-is-not-truncated" {
  # shellcheck disable=SC2329
  function tput() {
    return 1
  }
  unset COLUMNS

  run __hhs_history

  assert_success
  assert_output --partial 'verylongcommand-with-many-arguments --flag value'
  assert_output --partial 'git status'
  assert_output --partial 'npm test'
  refute_output --partial ' g...'
}
