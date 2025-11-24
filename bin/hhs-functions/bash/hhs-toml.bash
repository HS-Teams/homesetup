#!/usr/bin/env bash
# shellcheck disable=2094

#  Script: hhs-toml.bash
# Created: Nov 28, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# Internal: Trim leading and trailing whitespace preserving interior spacing.
__hhs_toml__trim() {

  local trimmed="${1}"

  trimmed="${trimmed#${trimmed%%[![:space:]]*}}"
  trimmed="${trimmed%${trimmed##*[![:space:]]}}"

  printf '%s' "${trimmed}"
}

# Internal: Remove inline comments that start with # outside quoted strings.
__hhs_toml__strip_comments() {

  local line="${1}" result="" char prev='' in_single=0 in_double=0
  local i length=${#line}

  for ((i = 0; i < length; i += 1)); do
    char="${line:i:1}"

    if [[ ${char} == '"' && ${in_single} -eq 0 ]]; then
      if [[ ${prev} != '\\' ]]; then
        ((in_double ^= 1))
      fi
      result+="${char}"
    elif [[ ${char} == "'" && ${in_double} -eq 0 ]]; then
      ((in_single ^= 1))
      result+="${char}"
    elif [[ ${char} == "#" && ${in_single} -eq 0 && ${in_double} -eq 0 ]]; then
      break
    else
      result+="${char}"
    fi

    prev="${char}"
  done

  printf '%s' "${result}"
}

# Internal: Normalize a TOML key removing surrounding quotes.
__hhs_toml__normalize_key() {

  local key="${1}"
  key="$(__hhs_toml__trim "${key}")"

  if [[ ${#key} -ge 2 && ${key:0:1} == '"' && ${key: -1} == '"' ]]; then
    key="${key:1:${#key}-2}"
  elif [[ ${#key} -ge 2 && ${key:0:1} == "'" && ${key: -1} == "'" ]]; then
    key="${key:1:${#key}-2}"
  fi

  printf '%s' "${key}"
}

# Internal: Escape regex metacharacters so sed/regex usage is safe.
__hhs_toml__escape_regex() {

  local text="${1}" escaped=""
  local i length=${#text} char

  for ((i = 0; i < length; i += 1)); do
    char="${text:i:1}"
    case "${char}" in
      '\\'|'.'|'?'|'*'|'+'|'('|')'|'['|']'|'{'|'}'|'|'|'^'|'-'|'$')
        escaped+="\\${char}"
        ;;
      *)
        escaped+="${char}"
        ;;
    esac
  done

  printf '%s' "${escaped}"
}

# Internal: Build the fully qualified group selector.
__hhs_toml__group_selector() {

  local group="${1}"

  if [[ -z "${group}" ]]; then
    printf '^'
  else
    printf '^\[%s\] *$' "$(__hhs_toml__escape_regex "${group}")"
  fi
}

# @function: Get the key's value from a toml file.
# @param $1 [Req] : The toml file read from.
# @param $2 [Req] : The key to get.
# @param $3 [Opt] : The group to get the key from (root if not provided).
function __hhs_toml_get() {

  local file="${1}" key="${2}" group="${3}" line trimmed current_group="" in_target=0
  local candidate_key candidate_value

  if [[ "${#}" -eq 0 || "${1}" == '-h' || "${1}" == '--help' ]]; then
    echo "usage: __hhs_toml_get <file> <key> [group]"
    return 1
  fi

  if [[ -z "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file parameter must be provided."
    return 1
  elif [[ -z "${key}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The key parameter must be provided."
    return 1
  elif [[ ! -s "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file \"${file}\" does not exists or is empty."
    return 1
  fi

  key="$(__hhs_toml__normalize_key "${key}")"

  while IFS= read -r line || [[ -n "${line}" ]]; do
    local raw="${line%$'\r'}"
    trimmed="$(__hhs_toml__strip_comments "${raw}")"
    trimmed="$(__hhs_toml__trim "${trimmed}")"

    if [[ -z "${trimmed}" ]]; then
      continue
    fi

    if [[ ${trimmed} =~ ^\[.*\]$ ]]; then
      current_group="${trimmed#[}"
      current_group="${current_group%]}"
      current_group="$(__hhs_toml__trim "${current_group}")"
      if [[ -n "${group}" && "${current_group}" == "${group}" ]]; then
        in_target=1
      else
        in_target=0
      fi
      continue
    fi

    if [[ -n "${group}" ]]; then
      [[ ${in_target} -eq 1 ]] || continue
    else
      [[ -z "${current_group}" ]] || continue
    fi

    if [[ ${trimmed} =~ ^([^=]+)=(.*)$ ]]; then
      candidate_key="$(__hhs_toml__normalize_key "${BASH_REMATCH[1]}")"
      candidate_value="$(__hhs_toml__trim "${BASH_REMATCH[2]}")"
      if [[ "${candidate_key}" == "${key}" ]]; then
        printf '%s=%s\n' "${candidate_key}" "${candidate_value}"
        return 0
      fi
    fi
  done <"${file}"

  return 1
}

# @function: Set the key's value from a toml file.
# @param $1 [Req] : The toml file read from..
# @param $2 [Req] : The key to set on the form: key=value
# @param $3 [Opt] : The group to set the key from (root if not provided).
function __hhs_toml_set() {

  local file="${1}" assignment="${2}" group="${3}" key value temp_file
  local candidate_key raw_line clean_line trimmed_line
  local line current_group="" group_found=0 key_updated=0 in_target=0

  if [[ "${#}" -eq 0 || "${1}" == '-h' || "${1}" == '--help' ]]; then
    echo "usage: __hhs_toml_set <file> <key=value> [group]"
    return 1
  fi

  if [[ -z "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file parameter must be provided."
    return 1
  elif [[ -z "${assignment}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The key/value parameter must be provided."
    return 1
  elif [[ ! -s "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file \"${file}\" does not exists or is empty."
    return 1
  fi

  if [[ "${assignment}" != *=* ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The key/value parameter must be on the form of 'key=value', but it was '${assignment}'."
    return 1
  fi

  key="$(__hhs_toml__normalize_key "${assignment%%=*}")"
  value="$(__hhs_toml__trim "${assignment#*=}")"

  temp_file="${file}.tmp"
  : >"${temp_file}"

  while IFS= read -r line || [[ -n "${line}" ]]; do
    raw_line="${line%$'\r'}"
    clean_line="$(__hhs_toml__strip_comments "${raw_line}")"
    trimmed_line="$(__hhs_toml__trim "${clean_line}")"

    if [[ ${trimmed_line} =~ ^\[.*\] ]]; then
      if [[ ${key_updated} -eq 0 && -n "${group}" && ${in_target} -eq 1 ]]; then
        printf '%s = %s\n' "${key}" "${value}" >>"${temp_file}"
        key_updated=1
      fi

      current_group="${trimmed_line#[}"
      current_group="${current_group%]}"
      current_group="$(__hhs_toml__trim "${current_group}")"

      if [[ -n "${group}" && "${current_group}" == "${group}" ]]; then
        in_target=1
        group_found=1
      else
        in_target=0
      fi
      printf '%s\n' "${raw_line}" >>"${temp_file}"
      continue
    fi

    if [[ ${trimmed_line} =~ ^([^=]+)=(.*)$ ]]; then
      candidate_key="$(__hhs_toml__normalize_key "${BASH_REMATCH[1]}")"
      if { [[ -z "${group}" && -z "${current_group}" ]] || [[ ${in_target} -eq 1 ]]; } && [[ "${candidate_key}" == "${key}" ]]; then
        printf '%s = %s\n' "${key}" "${value}" >>"${temp_file}"
        key_updated=1
        continue
      fi
    fi

    printf '%s\n' "${raw_line}" >>"${temp_file}"
  done <"${file}"

  if [[ ${key_updated} -eq 0 ]]; then
    if [[ -n "${group}" && ${group_found} -eq 0 ]]; then
      printf '\n[%s]\n%s = %s\n' "${group}" "${key}" "${value}" >>"${temp_file}"
    else
      printf '%s = %s\n' "${key}" "${value}" >>"${temp_file}"
    fi
  fi

  mv -f "${temp_file}" "${file}" &> /dev/null || return 1

  return 0
}

# @function: Print all toml file groups (tables).
# @param $1 [Req] : The toml file read from.
function __hhs_toml_groups() {

  local file="${1}" re_group count=0 line group

  if [[ "${#}" -eq 0 || "${1}" == '-h' || "${1}" == '--help' ]]; then
    echo "usage: __hhs_toml_groups <file>"
    return 1
  fi

  if [[ -z "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file parameter must be provided."
    return 1
  elif [[ ! -s "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file \"${file}\" does not exists or is empty."
    return 1
  fi

  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="$(__hhs_toml__strip_comments "${line%$'\r'}")"
    line="$(__hhs_toml__trim "${line}")"

    if [[ ${line} == \[*] ]]; then
      group="${line#[}"
      group="${group%]}"
      group="$(__hhs_toml__trim "${group}")"
      if [[ -n "${group}" ]]; then
        echo "${group}"
        ((count += 1))
      fi
    fi
  done <"${file}"

  [[ ${count} -gt 0 ]]
}

# @function: Print all toml file group keys (tables).
# @param $1 [Req] : The toml file read from.
# @param $2 [Opt] : The group to get the keys from (root if not provided).
function __hhs_toml_keys() {

  local file="${1}" group="${2}" count=0 line current_group="" re_group
  local raw_line clean_line trimmed_line

  re_group="$(__hhs_toml__group_selector "${group}")"

  if [[ "${#}" -eq 0 || "${1}" == '-h' || "${1}" == '--help' ]]; then
    echo "usage: __hhs_toml_keys <file> [group]"
    return 1
  fi

  if [[ -z "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file parameter must be provided."
    return 1
  elif [[ ! -s "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file \"${file}\" does not exists or is empty."
    return 1
  fi

  while IFS= read -r line || [[ -n "${line}" ]]; do
    raw_line="${line%$'\r'}"
    clean_line="$(__hhs_toml__strip_comments "${raw_line}")"
    trimmed_line="$(__hhs_toml__trim "${clean_line}")"

    [[ -z "${trimmed_line}" ]] && continue

    if [[ ${trimmed_line} =~ ^\[.*\] ]]; then
      if [[ ${trimmed_line} =~ ${re_group} ]]; then
        current_group="${group}"
        continue
      fi
      current_group="${trimmed_line#[}"
      current_group="${current_group%]}"
      current_group="$(__hhs_toml__trim "${current_group}")"
      if [[ -n "${group}" && "${current_group}" != "${group}" ]]; then
        continue
      elif [[ -z "${group}" ]]; then
        break
      fi
      continue
    fi

    if { [[ -z "${group}" && -z "${current_group}" ]] || [[ "${current_group}" == "${group}" ]]; }; then
      if [[ ${trimmed_line} =~ ^([^=]+)=([^=].*)$ ]]; then
        printf '%s\n' "$(__hhs_toml__trim "${BASH_REMATCH[0]}")"
        ((count += 1))
      fi
    fi
  done <"${file}"

  [[ ${count} -gt 0 ]]
}

# @function: Print all key=value pairs from a toml group.
# @param $1 [Req]: The toml file.
# @param $2 [Opt]: The group (root if omitted).
function __hhs_toml_get_all() {
  local file="${1}" group="${2}" re_group re_kv group_match

  if [[ -z "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file parameter must be provided."
    return 1
  elif [[ ! -s "${file}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "The file \"${file}\" does not exists or is empty."
    return 1
  fi

  re_group="^\[([a-zA-Z0-9_.]+)\] *"
  re_kv="^([a-zA-Z0-9_.]+) *= *(.*)"

  while read -r line; do
    if [[ -z "${group}" && ${line} =~ ${re_group} ]]; then
      break
    elif [[ -n "${group_match}" && ${line} =~ ${re_group} ]]; then
      break
    elif [[ ${line} =~ ${re_kv} ]]; then
      if [[ -z "${group}" ]]; then
        echo "${BASH_REMATCH[1]}=${BASH_REMATCH[2]//[\"\']/}"
      elif [[ -n "${group_match}" ]]; then
        echo "${BASH_REMATCH[1]}=${BASH_REMATCH[2]//[\"\']/}"
      fi
    elif [[ ${line} =~ ${re_group} ]]; then
      if [[ "${BASH_REMATCH[1]}" == "${group}" ]]; then
        group_match="${group}"
      fi
    fi
  done < "${file}"
}
