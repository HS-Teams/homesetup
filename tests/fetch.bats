#!/usr/bin/env bats

load test_helper
load_bats_libs

@test "--headers forwards each value to curl" {
  local tmpdir
  tmpdir="$(mktemp -d)"
  export CURL_STUB_LOG="${tmpdir}/curl.log"

  cat <<'STUB' >"${tmpdir}/curl"
#!/usr/bin/env bash
printf '%s\n' "$@" > "${CURL_STUB_LOG}"
output_file=
while [[ $# -gt 0 ]]; do
  if [[ "$1" == "--output" ]]; then
    shift
    output_file="$1"
  fi
  shift
done
if [[ -n "${output_file}" ]]; then
  printf 'stubbed-body' > "${output_file}"
fi
printf '200'
STUB
  chmod +x "${tmpdir}/curl"

  mkdir -p "${tmpdir}/hhs/bin"
  cat <<'COMMONS' >"${tmpdir}/hhs/bin/app-commons.bash"
#!/usr/bin/env bash

function quit() {
  local exit_code=${1:-0}
  shift || true
  local message="$*"
  [[ ${exit_code} -ne 0 && -n "${message}" ]] && printf '%s\n' "${message}" 1>&2
  [[ ${exit_code} -eq 0 && -n "${message}" ]] && printf '%s\n' "${message}" 1>&2
  exit "${exit_code}"
}

function usage() {
  local exit_code=${1:-0}
  shift || true
  printf '%s' "${USAGE:-}" 1>&2
  [[ $# -gt 0 ]] && printf '\n' 1>&2
  quit "${exit_code}" "$@"
}

function format_json() {
  cat
}

__hhs_errcho() {
  printf '%s %s\n' "$1" "$2" 1>&2
}
COMMONS
  chmod +x "${tmpdir}/hhs/bin/app-commons.bash"

  local repo_root
  repo_root="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"

  run env PATH="${tmpdir}:${PATH}" \
    CURL_STUB_LOG="${CURL_STUB_LOG}" \
    HHS_DIR="${tmpdir}/hhs" \
    HHS_HOME="${repo_root}" \
    "${repo_root}/bin/apps/bash/fetch.bash" \
    GET --headers 'Header-One: foo, Header-Two: bar' https://example.com

  assert_success

  mapfile -t invoked <"${CURL_STUB_LOG}"

  local -i header_flag_count=0 header_one_index=-1 header_two_index=-1
  for i in "${!invoked[@]}"; do
    case "${invoked[i]}" in
      -H)
        ((header_flag_count++))
        ;;
      'Header-One: foo')
        header_one_index=i
        ;;
      'Header-Two: bar')
        header_two_index=i
        ;;
    esac
  done

  (( header_flag_count == 2 ))
  (( header_one_index > 0 ))
  (( header_two_index > 0 ))
  [[ "${invoked[header_one_index-1]}" == "-H" ]]
  [[ "${invoked[header_two_index-1]}" == "-H" ]]

  rm -rf "${tmpdir}"
}
