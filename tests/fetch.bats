#!/usr/bin/env bats

load test_helper
load_bats_libs

# Define the app path from environment
setup() {
  APP="${HHS_APPS_DIR}/fetch.bash"
  export HHS_DIR="${BATS_TEST_TMPDIR}/hhs-dir"
  STUB_BIN="${BATS_TEST_TMPDIR}/bin"
  mkdir -p "${STUB_BIN}" "${HHS_DIR}/cache" "${HHS_DIR}/log"
  export FETCH_CURL_ARGS_FILE="${BATS_TEST_TMPDIR}/curl-args"
  export PATH="${STUB_BIN}:${PATH}"

  cat >"${STUB_BIN}/curl" <<'CURL'
#!/usr/bin/env bash
printf '%s\n' "$@" >"${FETCH_CURL_ARGS_FILE}"
printf '%s200' '{"userId":1,"id":1,"title":"stub title","body":"stub body"}'
CURL
  chmod +x "${STUB_BIN}/curl"

  cat >"${STUB_BIN}/jq" <<'JQ'
#!/usr/bin/env bash
cat >/dev/null
cat <<'JSON'
{
  "userId": 1,
  "id": 1,
  "title": "stub title",
  "body": "stub body"
}
JSON
JQ
  chmod +x "${STUB_BIN}/jq"
}

# TC - 1
@test "--headers forwards each value to curl" {
  run "${APP}" \
    --headers 'X-Test-One: alpha, X-Test-Two: beta' GET https://jsonplaceholder.typicode.com/posts/1

  assert_success

  # Since jsonplaceholder does not echo headers, we only check response content
  [[ "${output}" =~ userId ]] || fail "Expected response JSON missing"

  run grep -qx -- '-H' "${FETCH_CURL_ARGS_FILE}"
  assert_success

  run grep -qx 'X-Test-One: alpha' "${FETCH_CURL_ARGS_FILE}"
  assert_success

  run grep -qx 'X-Test-Two: beta' "${FETCH_CURL_ARGS_FILE}"
  assert_success
}

# TC - 2
@test "--format routes the response through format_json" {
  run "${APP}" \
    --format --silent GET https://jsonplaceholder.typicode.com/posts/1

  assert_success

  assert_line --index 0 '{'
  assert_line --index 1 --partial '  "userId":'
  assert_line --index 2 --partial '  "id":'
  assert_line --index 3 --partial '  "title":'
  assert_line --index 4 --partial '  "body":'
  assert_line --index 5 '}'
}

# TC - 3
@test "fails when method is missing" {
  run "${APP}" https://example.com
  assert_failure
  assert_output --partial "fetch.bash  Invalid HTTP method: HTTPS://EXAMPLE.COM"
}

# TC - 4
@test "fails when URL is missing" {
  run "${APP}" GET
  assert_failure
  assert_output --partial "fetch.bash  Missing required argument <url>"
}

# TC - 5
@test "fails when both method and url are missing" {
  run "${APP}"
  assert_failure
  assert_output --partial "fetch.bash  Missing required arguments <method> and <url>"
}

# TC - 6
@test "fails on unknown method" {
  run "${APP}" INVALID https://example.com
  assert_failure
  assert_output --partial "fetch.bash  Invalid HTTP method: INVALID"
}

# TC - 7
@test "fails on unknown flag" {
  run "${APP}" --unknown GET https://example.com
  assert_failure
  assert_output --partial "fetch.bash  Unknown option"
}

# TC - 8
@test "fails on --body without value" {
  run "${APP}" -b GET https://example.com
  assert_failure
  assert_output --partial "fetch.bash  --body requires a value."
}

# TC - 9
@test "fails on --headers without value" {
  run "${APP}" -H GET https://example.com
  assert_failure
  assert_output --partial "fetch.bash  --headers requires a value."
}

# TC - 10
@test "fails on --timeout with non-numeric value" {
  run "${APP}" -t abc GET https://example.com
  assert_failure
  assert_output --partial "fetch.bash  --timeout requires a numeric value."
}
