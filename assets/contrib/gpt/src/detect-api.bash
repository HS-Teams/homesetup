#!/usr/bin/env bash

# 
# Script Name: detect-api-calls.bash
# Purpose: Recursively search a Java/Gradle project for common external API and reactive client usages
# Created Date: Oct 14, 2025
# Author: Yore
# Required Packages: grep, find, awk, optionally: rg
# Powered by: HomeSetup (https://github.com/yorevs/homesetup)
# GPT: HHS-Script-Generator (https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator)
# 
# +------------------------------------------------------------------------------+
# | AIs CAN MAKE MISTAKES.                                                       |
# | For your safety, verify important information and code before executing it.  |
# |                                                                              |
# | This program comes with NO WARRANTY, to the extent permitted by law.         |
# +------------------------------------------------------------------------------+

# https://semver.org/ ; major.minor.patch
VERSION="0.0.12"

USAGE="Usage: ./detect-api-calls.bash [OPTIONS]

Options:
  -h, --help             Display help message and exit
  -s, --source <path>    Source directory to scan (default: src/main/java)
  -p, --pattern <regex>  Add custom pattern to scan for (can be used multiple times)
  -v, --version          Print version information and exit
  -f, --force-scan       Force Java scan even if no Gradle libraries are found

Examples:
  ./detect-api-calls.bash
  ./detect-api-calls.bash -s app/core -p ExternalService -p \"CustomClientImpl\" -f
"

SOURCE_DIR="src/main/java"
declare -a CUSTOM_PATTERNS=()
declare -a FOUND_LIBRARIES=()
declare -a MATCHING_FILES=()
USE_RG=false
SKIP_PATTERN_SCAN=false
FORCE_SCAN=false

# Counters
gradle_file_count=0
found_dependency_count=0
java_file_count=0
match_count=0

# @purpose: Cleanup on interrupt
cleanup() {
  echo -e "\n\033[31mINTERRUPTED\033[m: Script terminated early."
  print_summary
  exit 2
}

trap cleanup SIGINT SIGTERM

# @purpose: Print version
version() {
  echo "detect-api-calls.bash version ${VERSION}"
  exit 0
}

# @purpose: Print usage/help
usage() {
  echo "${USAGE}"
  exit 0
}

# @purpose: Parse CLI args
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -v|--version) version ;;
      -h|--help) usage ;;
      -s|--source)
        shift
        [[ -z "$1" ]] && echo -e "\033[31mERROR\033[m: --source requires a path." && exit 1
        SOURCE_DIR="$1"
        ;;
      -p|--pattern)
        shift
        [[ -z "$1" ]] && echo -e "\033[31mERROR\033[m: --pattern requires a value." && exit 1
        CUSTOM_PATTERNS+=("$1")
        ;;
      -f|--force-scan)
        FORCE_SCAN=true
        ;;
      *) echo -e "\033[31mERROR\033[m: Unknown option $1"; usage ;;
    esac
    shift
  done
}

# @purpose: Check for optional ripgrep (rg)
require_ripgrep() {
  if command -v rg >/dev/null 2>&1; then
    USE_RG=true
  fi
}

# @purpose: Scan Gradle files for API-related libraries
scan_gradle_dependencies() {
  echo -e "\n\033[34mINFORMATIVE\033[m: Checking Gradle files for potential API libraries..."

  local gradle_files
  gradle_files=$(find . -type f \( -name "build.gradle" -o -name "*.gradle" \) ! -path "*/test/*")
  gradle_file_count=$(echo "$gradle_files" | wc -l)

  local known_libraries=(
    'spring-boot-starter-webflux'
    'spring-boot-starter-web'
    'feign-core'
    'spring-cloud-starter-openfeign'
    'retrofit2'
    'okhttp'
    'webclient'
    'webflux'
    'spring-webflux'
    'spring-web'
    'resttemplate'
    'httpclient'
  )

  local match_flag=false

  while IFS= read -r file; do
    for lib in "${known_libraries[@]}"; do
      if grep -Eiq "${lib}" "$file"; then
        echo -e "\033[33m[!] Potential API access library found: ${lib} in ${file}\033[m"
        FOUND_LIBRARIES+=("${lib}")
        ((found_dependency_count++))
        match_flag=true
      fi
    done
  done <<< "${gradle_files}"

  if [[ "$match_flag" == false && "$FORCE_SCAN" == false ]]; then
    if [[ ${#CUSTOM_PATTERNS[@]} -eq 0 ]]; then
      echo -e "\033[33mWARNING\033[m: No known API libraries found in Gradle files and no custom patterns provided. Skipping Java pattern scan."
      SKIP_PATTERN_SCAN=true
    else
      echo -e "\033[34mINFORMATIVE\033[m: No known Gradle dependencies found, but custom patterns were provided. Proceeding with scan."
    fi
  fi
}

# @purpose: Build patterns only for found libraries
build_patterns_for_found_libs() {
  declare -A LIBRARY_PATTERN_MAP=(
    ["resttemplate"]="RestTemplate"
    ["spring-boot-starter-web"]="RestTemplate"
    ["spring-boot-starter-webflux"]="WebClient"
    ["spring-webflux"]="WebClient"
    ["webclient"]="WebClient"
    ["feign-core"]="FeignClient"
    ["spring-cloud-starter-openfeign"]="FeignClient"
    ["retrofit2"]="Retrofit"
    ["okhttp"]="OkHttpClient"
    ["httpclient"]="HttpClient"
  )

  local patterns=()

  for lib in "${FOUND_LIBRARIES[@]}"; do
    local key="${lib,,}"
    local p="${LIBRARY_PATTERN_MAP[$key]}"
    if [[ -n "$p" ]]; then
      patterns+=("$p")
    fi
  done

  if printf '%s\n' "${patterns[@]}" | grep -q "WebClient"; then
    patterns+=("WebClient\.create" "WebClient\.builder" "\.exchange\(" "\.retrieve\(")
  fi

  for pat in "${CUSTOM_PATTERNS[@]}"; do
    patterns+=("${pat}")
  done

  echo "${patterns[@]}"
}

# @purpose: Search Java files for relevant API patterns
search_api_calls() {
  if [[ "$SKIP_PATTERN_SCAN" == true ]]; then return; fi

  local src_dir="${SOURCE_DIR}"

  if [[ ! -d "${src_dir}" ]]; then
    echo -e "\033[31mERROR\033[m: Source directory '${src_dir}' not found."
    exit 1
  fi

  echo -e "\n\033[34mINFORMATIVE\033[m: Scanning directory: ${src_dir}"

  java_file_count=$(find "${src_dir}" -type f -name "*.java" ! -path "*/build/*" ! -path "*/test/*" | wc -l)

  local patterns
  IFS=' ' read -r -a patterns <<< "$(build_patterns_for_found_libs)"

  if [[ ${#patterns[@]} -eq 0 ]]; then
    echo -e "\033[33mWARNING\033[m: No pattern groups correspond to detected libraries or custom patterns. Skipping search."
    return
  fi

  if [[ "${USE_RG}" == true ]]; then
    for pattern in "${patterns[@]}"; do
      echo -e "\n\033[32m[+] Searching for: ${pattern}\033[m"
      local matches
      matches=$(rg --color=always --line-number --type java --ignore-case --hidden -g '!*/build/*' -g '!*/test/*' "${pattern}" "${src_dir}")
      if [[ -n "$matches" ]]; then
        echo "$matches"
        ((match_count++))
        MATCHING_FILES+=($(echo "$matches" | cut -d: -f1))
      fi
    done
  else
    find "${src_dir}" -type f -name "*.java" ! -path "*/build/*" ! -path "*/test/*" | while read -r file; do
      for pattern in "${patterns[@]}"; do
        if grep -Eiq "${pattern}" "${file}"; then
          echo -e "\n\033[32m[+] Match: ${pattern} in ${file}\033[m"
          grep -Ein "${pattern}" "${file}" | sed "s/^/    /"
          ((match_count++))
          MATCHING_FILES+=("${file}")
        fi
      done
    done
  fi
}

# @purpose: Print summary with aligned labels and deduplicated matching files
print_summary() {
  local label1="Gradle files scanned"
  local label2="Known dependencies found"
  local label3="Java files scanned"
  local label4="Pattern matches found"

  local max_len=0
  for label in "$label1" "$label2" "$label3" "$label4"; do
    [[ ${#label} -gt $max_len ]] && max_len=${#label}
  done
  local pad=4

  echo -e "\n\033[34m=== SUMMARY REPORT ===\033[m"
  printf "  %-${max_len}s:%*s%d\n" "$label1" $pad "" "$gradle_file_count"
  printf "  %-${max_len}s:%*s%d\n" "$label2" $pad "" $found_dependency_count
  printf "  %-${max_len}s:%*s%d\n" "$label3" $pad "" "$java_file_count"
  printf "  %-${max_len}s:%*s%d\n" "$label4" $pad "" $match_count

  echo -n -e "\n  Matching files: "

  if [[ ${#MATCHING_FILES[@]} -eq 0 ]]; then
    echo "[]"
  else
    local -a deduped=($(printf "%s\n" "${MATCHING_FILES[@]}" | sort -u))
    echo "["
    for file in "${deduped[@]}"; do
      echo "    - ${file},"
    done
    echo "  ]"
  fi
}

### === MAIN === ###
parse_args "$@"
require_ripgrep
scan_gradle_dependencies
search_api_calls
print_summary
exit 0
