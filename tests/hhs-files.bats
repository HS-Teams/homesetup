#!/usr/bin/env bats

#  Script: hhs-files.bats
# Purpose: hhs-files tests.
# Created: Mar 12, 2025
#  Author: ChatGPT
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-files.bash"
load_bats_libs

setup() {
  TEST_ROOT="$(mktemp -d)"
  WORK_DIR="${TEST_ROOT}/workspace"
  mkdir -p "${WORK_DIR}"

  export TRASH="${TEST_ROOT}/trash"
  mkdir -p "${TRASH}"

  ORIGINAL_PWD="$PWD"
  cd "${WORK_DIR}"

  ORIGINAL_PATH="$PATH"
}

teardown() {
  cd "${ORIGINAL_PWD}"
  PATH="${ORIGINAL_PATH}"
  rm -rf "${TEST_ROOT}"
}

# TC - 1
@test "when-colorls-is-available-then-should-execute-colorls" {
  stub_dir="${TEST_ROOT}/stubs"
  mkdir -p "${stub_dir}"
  cat <<'STUB' > "${stub_dir}/colorls"
#!/usr/bin/env bash
printf 'colorls called with: %s\n' "$*"
STUB
  chmod +x "${stub_dir}/colorls"
  PATH="${stub_dir}:${ORIGINAL_PATH}"

  run __hhs_ls_sorted time

  assert_success
  assert_output "colorls called with: --long --sort=time"
}

# TC - 2
@test "when-colorls-is-not-available-then-should-sort-with-ls" {
  PATH="/usr/bin:/bin"
  touch apple banana

  run __hhs_ls_sorted name

  assert_success
  sorted_names=()
  while IFS= read -r sorted_name; do
    sorted_names+=("${sorted_name}")
  done < <(printf '%s\n' "$output" | awk '{print $9}' | grep -E 'apple|banana')
  assert_equal "${sorted_names[0]}" "apple"
  assert_equal "${sorted_names[1]}" "banana"

  run __hhs_ls_sorted name -reverse

  assert_success
  reversed_names=()
  while IFS= read -r reversed_name; do
    reversed_names+=("${reversed_name}")
  done < <(printf '%s\n' "$output" | awk '{print $9}' | grep -E 'apple|banana')
  assert_equal "${reversed_names[0]}" "banana"
  assert_equal "${reversed_names[1]}" "apple"
}

# TC - 3
@test "when-running-in-dry-run-mode-then-should-only-report-matches" {
  touch "${WORK_DIR}/sample.log"

  run __hhs_del_tree "${WORK_DIR}" "*.log"

  assert_success
  assert_output --regexp "Would delete .*sample\\.log"
  [[ -f "${WORK_DIR}/sample.log" ]]
}

# TC - 4
@test "when-running-in-force-mode-then-should-move-matches-to-trash" {
  target="${WORK_DIR}/force-target.txt"
  echo 'data' > "${target}"

  run __hhs_del_tree -f "${WORK_DIR}" "*.txt"

  assert_success
  assert_output --regexp "Trashed => .*force-target.txt"
  [[ ! -e "${target}" ]]
  trash_entry=$(find "${TRASH}" -maxdepth 1 -name 'force-target.txt*' -print -quit)
  [[ -n "${trash_entry}" ]]
}

# TC - 5
@test "when-running-in-interactive-mode-then-should-respect-confirmation" {
  target="${WORK_DIR}/interactive-target.tmp"
  echo 'data' > "${target}"

  export -f __hhs_del_tree __hhs_errcho __hhs_has

  run bash -c 'printf y | __hhs_del_tree -i "$1" "$2"' bash "${WORK_DIR}" "*.tmp"

  assert_success
  assert_output --partial "Deleting files from ${WORK_DIR} matching *.tmp"
  [[ ! -e "${target}" ]]
  trash_entry=$(find "${TRASH}" -maxdepth 1 -name 'interactive-target.tmp*' -print -quit)
  [[ -n "${trash_entry}" ]]
}
