#!/usr/bin/env bats

load test_helper
load_bats_libs

setup() {
  CHECK_IP_TMPDIR="$(mktemp -d)"
  export CHECK_IP_TMPDIR

  mkdir -p "${CHECK_IP_TMPDIR}/hhs/bin"

  cat <<'COMMONS' >"${CHECK_IP_TMPDIR}/hhs/bin/app-commons.bash"
#!/usr/bin/env bash

quit() {
  local exit_code=${1:-0}
  shift || true
  local message="$*"
  if [[ ${exit_code} -ne 0 && -n "${message}" ]]; then
    printf '%s\n' "${message}" 1>&2
  elif [[ ${exit_code} -eq 0 && -n "${message}" ]]; then
    printf '%s\n' "${message}"
  fi
  exit "${exit_code}"
}

usage() {
  local exit_code=${1:-0}
  shift || true
  printf '%s' "${USAGE:-}" 1>&2
  if [[ $# -gt 0 ]]; then
    printf '\n' 1>&2
  fi
  quit "${exit_code}" "$@"
}

version() {
  quit 0 "${APP_NAME:-check-ip.bash} v${VERSION:-}"
}

__hhs_errcho() {
  local prefix message
  if [[ $# -gt 1 ]]; then
    prefix="$1"
    shift
  fi
  message="$1"
  if [[ -n "${CHECK_IP_ERR_LOG:-}" ]]; then
    if [[ -n "${prefix}" ]]; then
      printf '%s %s\n' "${prefix}" "${message}" >>"${CHECK_IP_ERR_LOG}"
    else
      printf '%s\n' "${message}" >>"${CHECK_IP_ERR_LOG}"
    fi
  fi
  if [[ -n "${prefix}" ]]; then
    printf '%s %s\n' "${prefix}" "${message}" 1>&2
  else
    printf '%s\n' "${message}" 1>&2
  fi
}

__hhs_ip_info() {
  local ip="$1"
  if [[ -n "${CHECK_IP_INFO_LOG:-}" ]]; then
    printf '%s\n' "${ip}" >>"${CHECK_IP_INFO_LOG}"
  fi
  printf 'info:%s\n' "${ip}"
}
COMMONS
  chmod +x "${CHECK_IP_TMPDIR}/hhs/bin/app-commons.bash"

  REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"
  export REPO_ROOT
}

teardown() {
  rm -rf "${CHECK_IP_TMPDIR}"
}

run_check_ip() {
  local -a args
  args=("$@")
  run env PATH="${CHECK_IP_TMPDIR}:${PATH}" \
    HHS_DIR="${CHECK_IP_TMPDIR}/hhs" \
    HHS_HOME="${REPO_ROOT}" \
    "${REPO_ROOT}/bin/apps/bash/check-ip.bash" \
    "${args[@]}"
}

@test "valid private class C address reports expected metadata" {
  run_check_ip 192.168.0.10

  assert_success
  assert_output --partial 'Valid IP: 192.168.0.10'
  assert_output --partial 'Class: C'
  assert_output --partial 'Scope: Private'
}

@test "invalid address exits with failure and logs error" {
  export CHECK_IP_ERR_LOG="${CHECK_IP_TMPDIR}/error.log"

  run_check_ip 999.10.0.1

  assert_failure

  run cat "${CHECK_IP_ERR_LOG}"
  assert_output --partial 'Invalid IP: 999.10.0.1'
}

@test "172.15.x.x is public while 172.16.x.x is private" {
  run_check_ip 172.15.1.1

  assert_success
  assert_output --partial 'Scope: Public'

  run_check_ip 172.16.1.1

  assert_success
  assert_output --partial 'Scope: Private'
}

@test "reserved range keeps limited broadcast distinct" {
  run_check_ip 240.0.0.1

  assert_success
  assert_output --partial 'Scope: Reserved'

  run_check_ip 255.255.255.255

  assert_success
  assert_output --partial 'Scope: Limited Broadcast'
}

@test "--info triggers info lookup output" {
  export CHECK_IP_INFO_LOG="${CHECK_IP_TMPDIR}/info.log"

  run_check_ip --info 8.8.8.8

  assert_success
  assert_output --partial 'info:8.8.8.8'

  run cat "${CHECK_IP_INFO_LOG}"
  assert_output '8.8.8.8'
}
