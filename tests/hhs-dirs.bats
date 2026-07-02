#!/usr/bin/env bats

load test_helper
load "${HHS_FUNCTIONS_DIR}/hhs-dirs.bash"
load_bats_libs

__HHS_MSELECT_STUB_RESPONSES=()
__HHS_MSELECT_STUB_STATUS=""

setup() {
  __HHS_ORIG_PWD="$PWD"
  TEST_ROOT="$(mktemp -d)"
  export HHS_DIR="${TEST_ROOT}/hhs"
  export HOME="${TEST_ROOT}/home"
  mkdir -p "${HHS_DIR}" "${HOME}"
  export HHS_SAVED_DIRS_FILE="${HHS_DIR}/.saved_dirs"
  : >"${HHS_SAVED_DIRS_FILE}"
  export OLDIFS="${IFS}"
  WORK_DIR="${TEST_ROOT}/workspace"
  mkdir -p "${WORK_DIR}"
  cd "${WORK_DIR}" || fail "failed to change to test workspace directory"
  __HHS_MSELECT_STUB_RESPONSES=()
  __HHS_MSELECT_STUB_STATUS=""
}

teardown() {
  cd "${__HHS_ORIG_PWD}" || fail "failed to change to test workspace directory"
  rm -rf "${TEST_ROOT}"
  __HHS_MSELECT_STUB_RESPONSES=()
  __HHS_MSELECT_STUB_STATUS=""
}

# TC - 1
@test "change_dir changes into provided directory" {
  mkdir -p "alpha"
  __hhs_change_dir "${WORK_DIR}/alpha"
  local exit_code=$?
  assert_equal "${exit_code}" 0
  assert_equal "$(pwd)" "${WORK_DIR}/alpha"
  assert_equal "${CURPWD}" "${WORK_DIR}/alpha"
  [[ -f "${HHS_DIR}/.last_dirs" ]] || fail "expected .last_dirs to be created"
}

# TC - 2
@test "change_dir reports missing directories" {
  run __hhs_change_dir "${WORK_DIR}/missing"
  assert_failure
  assert_output --partial "Directory \"${WORK_DIR}/missing\" was not found !"
}

# TC - 3
@test "changeback_ndirs navigates backwards multiple levels" {
  mkdir -p "one/two/three"
  __hhs_change_dir "${WORK_DIR}/one/two/three"
  local out_file
  out_file="$(mktemp)"
  __hhs_changeback_ndirs 2 >"${out_file}"
  local exit_code=$?
  assert_equal "${exit_code}" 0
  assert_equal "$(pwd)" "${WORK_DIR}/one"
  assert_equal "${OLDPWD}" "${WORK_DIR}/one/two/three"
  run cat "${out_file}"
  assert_output --partial "Changed directory backwards by 2 time(s)"
  rm -f "${out_file}"
}

# TC - 4
@test "changeback_ndirs surfaces seq errors for invalid counts" {
  mkdir -p "base/nested"
  __hhs_change_dir "${WORK_DIR}/base/nested"
  local err_file out_file
  err_file="$(mktemp)"
  out_file="$(mktemp)"
  __hhs_changeback_ndirs invalid >"${out_file}" 2>"${err_file}"
  local exit_code=$?
  assert_equal "${exit_code}" 0
  assert_equal "$(pwd)" "${WORK_DIR}/base/nested"
  run cat "${err_file}"
  assert_output --partial "invalid floating point argument"
  rm -f "${out_file}" "${err_file}"
}

# TC - 5
@test "godir cd into provided path directly" {
  mkdir -p "direct"
  __hhs_godir "${WORK_DIR}/direct"
  local exit_code=$?
  assert_equal "${exit_code}" 0
  assert_equal "$(pwd)" "${WORK_DIR}/direct"
}

# TC - 6
@test "godir reports when directory is missing" {
  mkdir -p "search"
  cd "${WORK_DIR}/search"
  run __hhs_godir "${WORK_DIR}/search" nomatch
  assert_failure
  assert_output --partial "No matches for directory with name \"nomatch\""
}

# TC - 7
@test "mkcd creates dotted path and jumps into it" {
  run __hhs_mkcd "foo.bar.baz"
  assert_success
  [[ -d "${WORK_DIR}/foo/bar/baz" ]] || fail "expected directory tree to exist"
  assert_output --partial "Current dir changed to: ${WORK_DIR}/foo/bar/baz"
}

# TC - 8
@test "mkcd fails when path points to existing file" {
  touch "conflict"
  run __hhs_mkcd conflict
  assert_failure
  assert_output --partial "File exists"
}

# TC - 9
@test "dirs returns failure when selection is cancelled" {
  mkdir -p "first" "second"
  __hhs_change_dir "${WORK_DIR}/first"
  __hhs_change_dir "${WORK_DIR}/second"
  __HHS_MSELECT_STUB_RESPONSES=()
  __HHS_MSELECT_STUB_STATUS=1
  run __hhs_dirs
  assert_failure
}

# TC - 10
@test "save_dir persists absolute path entries" {
  mkdir -p "persist"
  run __hhs_save_dir "${WORK_DIR}/persist" workspace
  assert_success
  assert_output --partial "saved as WORKSPACE"
  run cat "${HHS_SAVED_DIRS_FILE}"
  assert_output --partial "WORKSPACE=${WORK_DIR}/persist"
}

# TC - 11
@test "save_dir warns when directory is absent" {
  run __hhs_save_dir "${WORK_DIR}/missing" ghost
  assert_success
  assert_output --partial "Directory \"${WORK_DIR}/missing\" does not exist"
  [[ ! -s "${HHS_SAVED_DIRS_FILE}" ]] || fail "unexpected entry for missing directory"
}

# TC - 12
@test "load_dir changes to saved alias" {
  mkdir -p "persist"
  run __hhs_save_dir "${WORK_DIR}/persist" WORK
  assert_success
  run __hhs_load_dir WORK
  assert_success
  assert_output "Directory changed to: \"${WORK_DIR}/persist\""
}

# TC - 13
@test "load_dir warns about missing saved path" {
    mkdir -p "persist"
  run __hhs_save_dir "${WORK_DIR}/persist" WORK
  assert_success
  run __hhs_load_dir GHOST
  assert_failure
  assert_output --partial "✘ Fatal: __hhs_load_dir  Alias \"GHOST\" not found in saved directories !"
}
