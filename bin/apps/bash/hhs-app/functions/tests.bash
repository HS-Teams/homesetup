#!/usr/bin/env bash

#  Script: tests.bash
# Purpose: Contains HomeSetup test functions.
# Created: Mar 04, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# shellcheck disable=SC2207

# @purpose: Run all HomeSetup automated tests.
# @param $1..$N [Opt] : The bats files/folders to test.
function tests() {

  local started finished log_file badge fail=0 pass=0 skip=0 status num details re_status re_len len re_skip
  local diff_time diff_time_sec diff_time_ms all_tests=("${@}") range_str old_next re_len re_skip re_status
  local total expected_total last_index test_case_selectors='' display_label total_tests selected_start selected_end
  local bats_args=()

  command -v bats &> /dev/null || quit 1 "'Bats' application not available on your PATH !"

  log_file="${HHS_LOG_DIR}/hhs-tests.log"
  badge="${HHS_HOME}/check-badge.svg"

  if [[ ${#all_tests[@]} -gt 0 ]]; then
    last_index=$((${#all_tests[@]} - 1))
    if is_test_case_selector "${all_tests[last_index]}"; then
      test_case_selectors="${all_tests[last_index]}"
      unset "all_tests[${last_index}]"
    fi
  fi

  # If no bat file is provided, then assume  that we want to run all HHS tests.
  [[ ${#all_tests[@]} -eq 0 ]] && {
    echo -e "\n${WHITE}[$(date +'%H:%M:%S')] Executing ALL HomeSetup tests"
    all_tests=("${HHS_HOME}/tests")
  }
  echo -n '' > "${log_file}"

  # Execute bats tests
  re_skip='^(ok|not ok) ([0-9]+) (.+) in .* # skip .*'
  re_status='^(ok|not ok) ([0-9]+) (.+) in .*'
  re_len='^([0-9]+)\.\.([0-9]+)$'
  started="$(python3 -c 'import time; print(int(time.time() * 1000))')"

  echo -e "\n${WHITE}[$(date +'%H:%M:%S')] Running (${#all_tests[@]}) Bats tests from $(pwd)"
  echo -e "${WHITE}[$(date +'%H:%M:%S')] Logs will be available at:${log_file}\n"
  echo -e "  ${BLUE}|-Bats\t: ${WHITE}v$(__hhs_version bats | head -n 1)"
  echo -e "  ${BLUE}|-Bash\t: ${WHITE}v$(__hhs_version bash | head -n 1)"
  echo -e "  ${BLUE}|-User\t: ${WHITE}${USER}"
  echo -en "${NC}"

  # If a folder is provided, find all bats files inside it.
  [[ ${#all_tests[@]} -eq 1 && -d "${all_tests[0]}" ]] && \
    all_tests=($(find "${all_tests[0]}" -maxdepth 1  -name "*.bats"))
  # If we did not find any test.
  [[ ${#all_tests[@]} -eq 0 ]] && quit 1 "There are no tests to execute!"

  for next in $(printf '%s\n' "${all_tests[@]}" | sort); do
    expected_total=0
    num=0
    bats_args=(-rtT --print-output-on-failure)
    [[ -s "${next}" ]] || {
      echo -en "\n${YELLOW}[${next##*/}]${NC} WARN: Was not found on current dir. Retrying from HomeSetup/tests ..."
      old_next="${next}"
      next="${HHS_HOME}/tests/${next}"
      [[ -s "${next}" ]] || {
        echo -en "\n${RED}[${next##*/}] ${WHITE}ERROR: \"${old_next}\" is empty or not found!${NC}\n"
        continue
      }
    }
    collect_bats_test_cases "${next}"
    total_tests="${#BATS_TEST_CASE_NAMES[@]}"
    BATS_SELECTED_TEST_CASE_NAMES=()
    BATS_SELECTED_TEST_CASE_LABELS=()
    BATS_SELECTED_TEST_CASE_INDICES=()
    if [[ -n "${test_case_selectors}" ]]; then
      if build_bats_test_case_filter "${next}" "${test_case_selectors}"; then
        bats_args+=(--filter "${BATS_TEST_CASE_FILTER_REGEX}")
      else
        echo -en "\n${RED}[${next##*/}] ${WHITE}ERROR: No test cases match selector \"${test_case_selectors}\".${NC}\n"
        ((fail += 1))
        continue
      fi
    fi
    selected_start="$(selected_test_case_start)"
    selected_end="$(selected_test_case_end)"
    while read -r result; do
      if [[ ${result} =~ ${re_skip} ]]; then
        status="${YELLOW} ${SKIP_ICN} SKIP${NC}"
        num="${BASH_REMATCH[2]}"
        details="${BASH_REMATCH[3]}"
        ((skip += 1))
      elif [[ ${result} =~ ${re_status} ]]; then
        status="${BASH_REMATCH[1]}"
        num="${BASH_REMATCH[2]}"
        details="${BASH_REMATCH[3]}"
        if [[ "${status}" == 'not ok' ]]; then
          status="${RED} ${FAIL_ICN} FAIL${NC}"
          ((fail += 1))
        elif [[ "${status}" == 'ok' ]]; then
          status="${GREEN} ${SUCCESS_ICN} PASS${NC}"
          ((pass += 1))
        else
          status="${YELLOW} ${ALERT_ICN} Unknown${NC}"
        fi
      elif [[ ${result} =~ ${re_len} ]]; then
        range_str="${YELLOW}${selected_start}..${selected_end}${NC}"
        echo -e "\n${CYAN}[${next##*/}] ${WHITE}Running tests [${range_str}${WHITE}] out of ${YELLOW}${total_tests}${NC}\n"
        len="${#BASH_REMATCH[2]}"
        expected_total=${BASH_REMATCH[2]}
        continue
      else
        echo -e "${result}" >> "${log_file}" 2>&1
        continue
      fi
      echo -en "${status} "
      if [[ -n "${test_case_selectors}" ]]; then
        display_label="$(selected_test_case_label "${details}")"
        [[ -n "${display_label}" ]] || printf -v display_label "TC-%0${len}d" "${num}"
        printf "${BLUE}%s${NC} %s\n" "${display_label}" "${details}"
      else
        printf "${BLUE}TC-%0${len}d${NC} %s\n" "${num}" "${details}"
      fi
    done < <(bats "${bats_args[@]}" "${next}" 2>&1)
    [[ $num -ne $expected_total ]] && {
      total="${num:-0}"
      echo -en "\n${RED}[${next##*/}] ${WHITE}ERROR: \"${next}\" tests (${total}) expected (${expected_total})!${NC}\n"
      ((fail += 1))
    }
  done

  finished="$(python3 -c 'import time; print(int(time.time() * 1000))')"
  diff_time=$((finished - started))
  diff_time_sec=$((diff_time / 1000))
  diff_time_ms=$((diff_time - (diff_time_sec * 1000)))

  echo -en "\n\n${WHITE}[$(date +'%H:%M:%S')] Finished running $((pass + fail + skip)) tests:\t"
  echo -e "${GREEN}${SUCCESS_ICN} Passed=${pass}   ${YELLOW}${SKIP_ICN} Skipped=${skip}   ${RED}${FAIL_ICN} Failed=${fail}${NC}"

  if [[ ${fail} -gt 0 ]]; then
    if [[ -s "${log_file}" ]]; then
      echo -e "${ORANGE}"
      echo -e "+----------------------------------------------+"
      echo -e "| -=- The following failures were reported -=- |"
      echo -e "+----------------------------------------------+"
      echo -e "${NC}"
      awk '{printf "\033[33;1m%4d\033[m  %s\n", NR, $0}' "${log_file}"
      echo ''
    fi
    curl 'https://img.shields.io/badge/tests-failed-red' --output "${badge}" 2> /dev/null
    echo -e " ${RED}${FAIL_ICN}${WHITE}  Bats tests ${RED}FAILED${WHITE} in ${diff_time_sec}s ${diff_time_ms}ms ${NC}"
    quit 2
  else
    echo ''
    curl 'https://img.shields.io/badge/tests-passed-green' --output "${badge}" 2> /dev/null
    echo -e " ${GREEN}${PASS_ICN}${NC}  ${WHITE}All Bats tests ${GREEN}PASSED${WHITE} in ${diff_time_sec}s ${diff_time_ms}ms ${NC}"
    quit 0
  fi

}

# @purpose: Run all terminal color palette tests.
function color-tests() {

  echo -e "\n${WHITE}[$(date +'%H:%M:%S')] Running HomeSetup color palette test${BLUE}\n"
  echo -e "  |-Terminal : ${TERM:-not-detected}"
  echo -e "  |-Terminal Program : ${TERM_PROGRAM:-not-detected}\n"

  echo -en "${BLACK}  BLACK "
  echo -en "${RED}    RED "
  echo -en "${GREEN}  GREEN "
  echo -en "${ORANGE} ORANGE "
  echo -en "${BLUE}   BLUE "
  echo -en "${PURPLE} PURPLE "
  echo -en "${CYAN}   CYAN "
  echo -en "${GRAY}   GRAY "
  echo -en "${WHITE}  WHITE "
  echo -en "${YELLOW} YELLOW "
  echo -en "${VIOLET} VIOLET "
  echo -e "${NC}\n"

  echo -e "--- 16 Colors Low\n"
  for c in {30..37}; do
    echo -en "\033[0;${c}mC16-${c} "
  done
  echo -e "${NC}\n"
  echo -e "--- 16 Colors High\n"
  for c in {90..97}; do
    echo -en "\033[0;${c}mC16-${c} "
  done

  if [[ "${TERM##*-}" == "256color" ]]; then
    echo -e "${NC}\n"
    echo -e "--- 256 Colors\n"
    for c in {1..256}; do
      echo -en "\033[38;5;${c}m"
      printf "C256-%-.3d " "${c}"
      [[ "$(echo "$c % 12" | bc)" -eq 0 ]] && echo ''
    done
    echo -e "${NC}\n"
  fi

  quit 0 ''
}

# @purpose: Checks whether an argument is a test case selector.
# @param $1 [Req] : The candidate argument.
is_test_case_selector() {
  [[ "${1:-}" =~ (^|,)[[:space:]]*\^?TC- ]]
}

# @purpose: Trim whitespace from a string.
# @param $1 [Req] : The value to trim.
trim_test_case_selector() {
  local value="${1:-}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf "%s" "${value}"
}

# @purpose: Escapes a test name so it can be used inside a Bats filter regex.
# @param $1 [Req] : The Bats test name.
escape_bats_filter_regex() {
  local value="${1}" escaped='' char i

  for ((i = 0; i < ${#value}; i++)); do
    char="${value:i:1}"
    case "${char}" in
      '\' | '.' | '[' | ']' | '(' | ')' | '{' | '}' | '^' | '$' | '*' | '+' | '?' | '|')
        escaped+="\\${char}"
        ;;
      *)
        escaped+="${char}"
        ;;
    esac
  done

  printf "%s" "${escaped}"
}

# @purpose: Collect Bats test case names and display labels for a file.
# @param $1 [Req] : The Bats file to scan.
collect_bats_test_cases() {
  local test_file="${1}" name index=0 label_len label

  BATS_TEST_CASE_NAMES=()
  BATS_TEST_CASE_LABELS=()

  while IFS= read -r name; do
    BATS_TEST_CASE_NAMES[${#BATS_TEST_CASE_NAMES[@]}]="${name}"
  done < <(sed -n 's/^[[:space:]]*@test[[:space:]]*"\(.*\)"[[:space:]]*{[[:space:]]*$/\1/p' "${test_file}")

  label_len="${#BATS_TEST_CASE_NAMES[@]}"
  label_len="${#label_len}"
  [[ "${label_len}" -gt 0 ]] || label_len=1

  for ((index = 1; index <= ${#BATS_TEST_CASE_NAMES[@]}; index++)); do
    printf -v label "TC-%0${label_len}d" "${index}"
    BATS_TEST_CASE_LABELS[${#BATS_TEST_CASE_LABELS[@]}]="${label}"
  done
}

# @purpose: Checks whether a test case label or number matches a selector list.
# @param $1 [Req] : The formatted test case label.
# @param $2 [Req] : The numeric test case index.
# @param $3 [Req] : The comma-separated selector list.
test_case_matches_selector() {
  local label="${1}" test_index="${2}" selectors="${3}" selector selector_number

  IFS=',' read -r -a selector_list <<< "${selectors}"
  for selector in "${selector_list[@]}"; do
    selector="$(trim_test_case_selector "${selector}")"
    [[ -n "${selector}" ]] || continue
    if [[ "${selector}" =~ ^TC-([0-9]+)$ ]]; then
      selector_number=$((10#${BASH_REMATCH[1]}))
      [[ "${selector_number}" -eq "${test_index}" ]] && return 0
    elif [[ "${label}" =~ ${selector} ]]; then
      return 0
    fi
  done

  return 1
}

# @purpose: Build a Bats test-name filter from user-facing TC selectors.
# @param $1 [Req] : The Bats file to scan.
# @param $2 [Req] : The comma-separated selector list.
build_bats_test_case_filter() {
  local test_file="${1}" selectors="${2}" index label name escaped filter=''

  BATS_SELECTED_TEST_CASE_NAMES=()
  BATS_SELECTED_TEST_CASE_LABELS=()
  BATS_SELECTED_TEST_CASE_INDICES=()
  BATS_TEST_CASE_FILTER_REGEX=''

  collect_bats_test_cases "${test_file}"
  for ((index = 0; index < ${#BATS_TEST_CASE_NAMES[@]}; index++)); do
    label="${BATS_TEST_CASE_LABELS[index]}"
    name="${BATS_TEST_CASE_NAMES[index]}"
    if test_case_matches_selector "${label}" "$((index + 1))" "${selectors}"; then
      BATS_SELECTED_TEST_CASE_LABELS[${#BATS_SELECTED_TEST_CASE_LABELS[@]}]="${label}"
      BATS_SELECTED_TEST_CASE_NAMES[${#BATS_SELECTED_TEST_CASE_NAMES[@]}]="${name}"
      BATS_SELECTED_TEST_CASE_INDICES[${#BATS_SELECTED_TEST_CASE_INDICES[@]}]=$((index + 1))
      escaped="$(escape_bats_filter_regex "${name}")"
      filter="${filter:+${filter}|}${escaped}"
    fi
  done

  [[ -n "${filter}" ]] || return 1
  BATS_TEST_CASE_FILTER_REGEX="^(${filter})$"
}

# @purpose: Resolve the original display label for a selected Bats test.
# @param $1 [Req] : The Bats test name from TAP output.
selected_test_case_label() {
  local details="${1}" index

  for ((index = 0; index < ${#BATS_SELECTED_TEST_CASE_NAMES[@]}; index++)); do
    if [[ "${BATS_SELECTED_TEST_CASE_NAMES[index]}" == "${details}" ]]; then
      printf "%s" "${BATS_SELECTED_TEST_CASE_LABELS[index]}"
      return 0
    fi
  done

  return 1
}

# @purpose: Return the first displayed test case number for a Bats run.
selected_test_case_start() {
  local index start=1

  if [[ ${#BATS_SELECTED_TEST_CASE_INDICES[@]} -gt 0 ]]; then
    start="${BATS_SELECTED_TEST_CASE_INDICES[0]}"
    for index in "${BATS_SELECTED_TEST_CASE_INDICES[@]}"; do
      [[ "${index}" -lt "${start}" ]] && start="${index}"
    done
  fi

  printf "%s" "${start}"
}

# @purpose: Return the last displayed test case number for a Bats run.
selected_test_case_end() {
  local index end="${#BATS_TEST_CASE_NAMES[@]}"

  if [[ ${#BATS_SELECTED_TEST_CASE_INDICES[@]} -gt 0 ]]; then
    end="${BATS_SELECTED_TEST_CASE_INDICES[0]}"
    for index in "${BATS_SELECTED_TEST_CASE_INDICES[@]}"; do
      [[ "${index}" -gt "${end}" ]] && end="${index}"
    done
  fi

  printf "%s" "${end}"
}
