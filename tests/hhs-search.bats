#!/usr/bin/env bats

#  Script: hhs-search.bats
# Purpose: __hhs_search_* tests.
# Created: May 11, 2025
#  Author: OpenAI Assistant
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load_bats_libs
load "${HHS_FUNCTIONS_DIR}/hhs-search.bash"

# Override highlighter to keep assertions simple during testing.
__hhs_highlight() {
  cat -
}

setup() {
  FIXTURE_ROOT="$(mktemp -d)"
  export HHS_LOG_FILE="${FIXTURE_ROOT}/hhs.log"
  export HHS_VERBOSE_LOGS=1
  export HHS_MY_OS="Linux"
  : >"${HHS_LOG_FILE}"

  export SEARCH_FIXTURES="${FIXTURE_ROOT}/workspace"
  mkdir -p "${SEARCH_FIXTURES}/docs" "${SEARCH_FIXTURES}/configs" "${SEARCH_FIXTURES}/nested/inner"

  cat <<'TXT' >"${SEARCH_FIXTURES}/docs/report.txt"
Alpha target line
Second target line
TXT

  cat <<'TXT' >"${SEARCH_FIXTURES}/docs/notes.md"
Markdown content
TXT

  cat <<'TXT' >"${SEARCH_FIXTURES}/configs/app.conf"
PORT=8080
FeatureFlag=Disabled
TXT

  cat <<'TXT' >"${SEARCH_FIXTURES}/configs/case_sensitive.conf"
ErrorCode=TeStInG
TXT

  cat <<'TXT' >"${SEARCH_FIXTURES}/configs/replace.conf"
mode=alpha
TXT

  touch "${SEARCH_FIXTURES}/nested/inner/keep.txt"
}

teardown() {
  rm -rf "${FIXTURE_ROOT}"
}

# TC - 1
@test "when-search-file-with-insufficient-arguments-then-prints-usage" {
  run __hhs_search_file -h
  assert_failure
  assert_output --partial "usage: __hhs_search_file <search_path> [file_globs...]"
}

# TC - 2
@test "when-search-file-with-globs-then-builds-find-command" {
  : >"${HHS_LOG_FILE}"
  run __hhs_search_file "${SEARCH_FIXTURES}" "*.txt"
  assert_success
  assert_output --partial "report.txt"

  run tail -n1 "${HHS_LOG_FILE}"
  assert_success
  assert_output --partial "find -L ${SEARCH_FIXTURES} -type f"
  assert_output --partial "-iname \"*.txt\""
}

# TC - 3
@test "when-search-dir-with-insufficient-arguments-then-prints-usage" {
  run __hhs_search_dir --help
  assert_failure
  assert_output --partial "usage: __hhs_search_dir <search_path> [dir_globs...]"
}

# TC - 4
@test "when-search-dir-with-globs-then-builds-find-command" {
  : >"${HHS_LOG_FILE}"
  run __hhs_search_dir "${SEARCH_FIXTURES}" "*nested*"
  assert_success
  assert_output --partial "nested"

  run tail -n1 "${HHS_LOG_FILE}"
  assert_success
  assert_output --partial "find -L ${SEARCH_FIXTURES} -type d"
  assert_output --partial "-iname \"*nested*\""
}

# TC - 5
@test "when-search-string-with-default-regex-options-then-runs-grep-command" {
  : >"${HHS_LOG_FILE}"
  run __hhs_search_string "${SEARCH_FIXTURES}" "target" "*.txt"
  assert_success
  assert_output --partial "report.txt:1:Alpha target line"

  run tail -n1 "${HHS_LOG_FILE}"
  assert_success
  assert_output --partial "grep -HnEI \"target\""
}

@test "when-searching-inside-spaced-path-then-results-are-returned" {
  spaced_root="${FIXTURE_ROOT}/workspace with spaces"
  mkdir -p "${spaced_root}/docs" "${spaced_root}/nested folder"
  printf '%s\n' "Alpha target line" >"${spaced_root}/docs/report.txt"

  run __hhs_search_file "${spaced_root}" "*.txt"
  assert_success
  assert_output --partial "report.txt"

  run __hhs_search_dir "${spaced_root}" "*nested*"
  assert_success
  assert_output --partial "nested folder"

  run __hhs_search_string "${spaced_root}" "target" "*.txt"
  assert_success
  assert_output --partial "report.txt:1:Alpha target line"
}

# TC - 6
@test "when-search-string-with-word-option-then-uses-fixed-word-grep" {
  : >"${HHS_LOG_FILE}"
  run __hhs_search_string "${SEARCH_FIXTURES}" -w "target" "*.txt"
  assert_success
  assert_output --partial "report.txt:1:Alpha target line"

  run tail -n1 "${HHS_LOG_FILE}"
  assert_success
  assert_output --partial "grep -HnFwI \"target\""
}

# TC - 7
@test "when-search-string-with-ignore-case-and-binary-options-then-updates-flags" {
  : >"${HHS_LOG_FILE}"
  run __hhs_search_string "${SEARCH_FIXTURES}" -i -b "testing" "*.conf"
  assert_success
  assert_output --partial "case_sensitive.conf:1:ErrorCode=TeStInG"

  run tail -n1 "${HHS_LOG_FILE}"
  assert_success
  assert_output --partial "grep -HnEi \"testing\""
}

# TC - 8
@test "when-search-string-with-replace-option-then-substitutes-content" {
  : >"${HHS_LOG_FILE}"
  run __hhs_search_string "${SEARCH_FIXTURES}" -r "beta" "alpha" "*.conf"
  assert_success
  assert_output --partial "replace.conf:1:mode=beta"

  run tail -n1 "${HHS_LOG_FILE}"
  assert_success
  assert_output --partial "sed -i'' -r"

  run cat "${SEARCH_FIXTURES}/configs/replace.conf"
  assert_success
  assert_output --partial "mode=beta"
}
