#!/usr/bin/env bats

#  Script: hhs-updater.bats
# Purpose: hhs updater plugin tests.
# Created: Jul 06, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

export HHS_REPO_DIR="${HHS_HOME:-$(cd "${BATS_TEST_DIRNAME}/.." && pwd)}"
export HHS_HOME="${HHS_REPO_DIR}"

load test_helper
load_bats_libs

setup() {
  export HHS_DIR="${BATS_TEST_TMPDIR}/hhs"
  export HHS_HOME="${BATS_TEST_TMPDIR}/HomeSetup"
  export OLDIFS="${IFS}"
  export HHS_MY_OS_RELEASE

  mkdir -p "${HHS_DIR}" "${HHS_HOME}"
  printf '1.10.7\n' >"${HHS_HOME}/.VERSION"
  export HHS_VERSION="1.10.7"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    HHS_MY_OS_RELEASE="macOS"
  else
    HHS_MY_OS_RELEASE="Linux"
  fi
  unset ANS
  set +e
  source "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/updater/updater.bash"
  set -e
}

# @purpose: Test replacement for app-commons quit.
quit() {
  local exit_code="${1:-0}"
  shift || true
  [[ $# -gt 0 ]] && printf '%s\n' "$*"
  return "${exit_code}"
}

# @purpose: Test replacement for app-commons usage.
usage() {
  local exit_code="${1:-1}"
  shift || true
  [[ $# -gt 0 ]] && printf '%s\n' "$*"
  return "${exit_code}"
}

# @purpose: Avoid clearing Bats output during updater tests.
clear() {
  return 0
}

# @purpose: Return the fake repository version and record network calls.
curl() {
  printf '1\n' >>"${HHS_DIR}/curl.calls"
  printf '%s\n' "${HHS_TEST_REPO_VERSION:-1.10.8}"
}

# TC - 1
@test "when-check-is-not-due-then-updater-should-not-fetch-repository-version" {
  printf '999999999999\n' >"${HHS_DIR}/.last_update"

  run update_check

  assert_success
  refute_output --partial "Updates Available"
  run test ! -f "${HHS_DIR}/curl.calls"
  assert_success
}

# TC - 2
@test "when-check-is-forced-then-updater-should-fetch-even-if-not-due" {
  printf '999999999999\n' >"${HHS_DIR}/.last_update"

  run update_check --force

  assert_success
  assert_output --partial "Updates Available"
  run test -s "${HHS_DIR}/curl.calls"
  assert_success
}

# TC - 3
@test "when-executing-check-with-force-then-updater-should-pass-force-option" {
  printf '999999999999\n' >"${HHS_DIR}/.last_update"

  run execute check --force

  assert_success
  assert_output --partial "Updates Available"
  run test -s "${HHS_DIR}/curl.calls"
  assert_success
}

# TC - 4
@test "when-check-is-due-and-update-exists-then-updater-should-not-prompt-or-install" {
  printf '0\n' >"${HHS_DIR}/.last_update"

  run update_check

  assert_success
  assert_output --partial "Updates Available"
  refute_output --partial "Do you want to install"
  run test -s "${HHS_DIR}/curl.calls"
  assert_success
}

# TC - 5
@test "when-check-stamp-is-missing-then-updater-should-fetch-repository-version" {
  run update_check

  assert_success
  assert_output --partial "Updates Available"
  run test -s "${HHS_DIR}/curl.calls"
  assert_success
}

# TC - 6
@test "when-update-is-called-manually-then-updater-should-always-fetch" {
  printf '999999999999\n' >"${HHS_DIR}/.last_update"

  run update_hhs <<<"n"

  assert_success
  assert_output --partial "Updates Available"
  run test -s "${HHS_DIR}/curl.calls"
  assert_success
}

# TC - 7
@test "when-repository-version-is-lower-then-updater-should-not-report-update" {
  repo_ver="1.9.99"

  run is_updated

  assert_success
  assert_output --partial "up-to-date"
  refute_output --partial "Updates Available"
}
