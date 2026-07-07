#!/usr/bin/env bats

load test_helper
load_bats_libs

# Define the app path from environment
setup() {
  APP="${HHS_APPS_DIR}/check-ip.bash"
  export HHS_DIR="${BATS_TEST_TMPDIR}/hhs-dir"
  mkdir -p "${HHS_DIR}/cache" "${HHS_DIR}/log"
}

# TC - 1
@test "valid private class C address reports expected metadata" {
  run "${APP}" 192.168.0.10

  assert_success
  assert_output --partial 'Valid IP: 192.168.0.10'
  assert_output --partial 'Class: C'
  assert_output --partial 'Scope: Private'
}

# TC - 2
@test "invalid address exits with failure and logs error" {
  run "${APP}" 999.10.0.1

  assert_failure
  assert_output --partial 'Invalid IP: 999.10.0.1'
}

# TC - 3
@test "172.15.x.x is public while 172.16.x.x is private" {
  run "${APP}" 172.15.1.1

  assert_success
  assert_output --partial 'Scope: Public'

  run "${APP}" 172.16.1.1

  assert_success
  assert_output --partial 'Scope: Private'
}

# TC - 4
@test "reserved range keeps limited broadcast distinct" {
  run "${APP}" 240.0.0.1

  assert_success
  assert_output --partial 'Scope: Reserved'

  run "${APP}" 255.255.255.255

  assert_success
  assert_output --partial 'Scope: Limited Broadcast'
}

# TC - 5
@test "--info triggers info lookup output" {
  ensure_json_print
  run "${APP}" --info 8.8.8.8

  RESP='
{
  "status": "success",
  "country": "United States",
  "countryCode": "US",
  "region": "VA",
  "regionName": "Virginia",
  "city": "Ashburn",
  "zip": "20149",
  "lat": 39.03,
  "lon": -77.5,
  "timezone": "America/New_York",
  "isp": "Google LLC",
  "org": "Google Public DNS",
  "as": "AS15169 Google LLC",
  "query": "8.8.8.8"
}'
  assert_success
  assert_output --partial "${RESP}"
}
