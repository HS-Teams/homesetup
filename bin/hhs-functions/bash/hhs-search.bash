#!/usr/bin/env bash

#  Script: hhs-search.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Search for files and links to files recursively.
# @param $1 [Req] : The base search path.
# @param $2 [Req] : The search glob expressions.
# @compatible: bash zsh
function __hhs_search_file() {

  local names file_globs dir full_cmd glob
  local -a file_glob_values name_args

  if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <search_path> [file_globs...]"
    echo ''
    echo '  Notes: '
    echo '    - <file_globs...>: Comma separated globs. E.g: "*.txt,*.md,*.rtf"'
    return 1
  else
    dir="${1}"
    file_globs="${2}"
    IFS=',' read -r -a file_glob_values <<<"${file_globs}"
    for glob in "${file_glob_values[@]}"; do
      [[ -z "${glob}" ]] && continue
      [[ -n "${names}" ]] && names="${names} -o "
      names="${names}-iname \"${glob}\""
      [[ "${#name_args[@]}" -gt 0 ]] && name_args+=("-o")
      name_args+=("-iname" "${glob}")
    done
    full_cmd="find -L ${dir} -type f \( ${names} \) 2> /dev/null | __hhs_highlight \"(${file_globs//\*/.*}|$)\""
    echo "${YELLOW}Searching for files matching: \"${file_globs}\" in \"${dir}\" ${NC}"
    __hhs_log "DEBUG" "${FUNCNAME[0]} ${full_cmd}"
    find -L "${dir}" -type f \( "${name_args[@]}" \) 2>/dev/null |
      __hhs_highlight "(${file_globs//\*/.*}|$)"

    return $?
  fi
}

# @function: Search for directories and links to directories recursively.
# @param $1 [Req] : The base search path.
# @param $2 [Opt] : The search glob expressions.
# @compatible: bash zsh
function __hhs_search_dir() {

  local names dir dir_globs full_cmd glob
  local -a dir_glob_values name_args

  if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <search_path> [dir_globs...]"
    echo ''
    echo '  Notes: '
    echo '    - <dir_globs...>: Comma separated directories. E.g:. "dir1,dir2,dir2"'
    return 1
  else
    dir="${1}"
    dir_globs="${2}"
    IFS=',' read -r -a dir_glob_values <<<"${dir_globs}"
    for glob in "${dir_glob_values[@]}"; do
      [[ -z "${glob}" ]] && continue
      [[ -n "${names}" ]] && names="${names} -o "
      names="${names}-iname \"${glob}\""
      [[ "${#name_args[@]}" -gt 0 ]] && name_args+=("-o")
      name_args+=("-iname" "${glob}")
    done
    full_cmd="find -L ${dir} -type d \( ${names} \) 2> /dev/null | __hhs_highlight \"(${dir_globs//\*/.*}|$)\""

    # Execute the search command.
    echo "${YELLOW}Searching for folders matching: [${dir_globs}] in \"${dir}\" ${NC}"
    __hhs_log "DEBUG" "${FUNCNAME[0]} ${full_cmd}"
    find -L "${dir}" -type d \( "${name_args[@]}" \) 2>/dev/null |
      __hhs_highlight "(${dir_globs//\*/.*}|$)"

    return $?
  fi
}

# @function: Search in files for strings matching the specified criteria recursively.
# @param $1 [Req] : Search options.
# @param $2 [Req] : The base search path.
# @param $3 [Req] : The searching string.
# @param $4 [Req] : The GLOB expression of the file search.
# @param $5 [Opt] : Whether to replace the findings.
# @param $6 [Con] : Required if $4 is provided. This is the replacement string.
# @compatible: bash zsh
function __hhs_search_string() {

  local extra_str replace names file_globs_type='regex' gflags='-HnEI' sflags='g'
  local search_str base_cmd full_cmd dir repl_str file_globs glob ised sed_expr
  local -a file_glob_values name_args sed_args sed_filter_args pipeline_status

  if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <search_path> [options] <regex/string> [file_globs]"
    echo ''
    echo '    Options: '
    echo '      -i | --ignore-case            : Makes the search case INSENSITIVE.'
    echo '      -w | --words                  : Makes the search to use the STRING words instead of a REGEX.'
    echo '      -r | --replace <replacement>  : Makes the search to REPLACE all occurrences by the replacement string.'
    echo '      -b | --binary                 : Includes BINARY files in the search.'
    echo ''
    echo '  Notes: '
    echo '    - <file_globs...>: Comma separated file globs. E.g: "*.txt,*.md,*.rtf"'
    echo '    - If <file_globs> is not specified, it will assume "*.*"'
    return 1
  else
    dir="${1}"
    shift

    if [[ ! -d "${dir}" ]]; then
      __hhs_errcho "${FUNCNAME[0]}" "Search path does not exist: \"${dir}\""
      return 1
    fi

    while [[ -n "${1}" ]]; do
      case "$1" in
      -w | --words)
        gflags="${gflags//E/Fw}"
        file_globs_type=${file_globs_type//regex/string}
        ;;
      -i | --ignore-case)
        gflags="${gflags}i"
        sflags="${sflags}i"
        file_globs_type="${file_globs_type}+ignore-case"
        ;;
      -b | --binary)
        gflags="${gflags//I/}"
        file_globs_type="${file_globs_type}+binary"
        ;;
      -r | --replace)
        replace=1
        shift
        [[ -z "$1" ]] && __hhs_errcho "${FUNCNAME[0]}" "Missing replacement string !" && return 1
        repl_str="$1"
        extra_str=", replacement: \"${repl_str}\""
        ;;
      *)
        [[ ${1} =~ ^-[wibr] || "${1}" =~ ^--(words|ignore-case|binary|replace) ]] || break
        ;;
      esac
      shift
    done

    search_str="${1}"
    if [[ -z "${search_str}" ]]; then
      __hhs_errcho "${FUNCNAME[0]}" "Invalid search string: \"${search_str}\""
      return 1
    fi
    file_globs="${2:-*.*}"
    IFS=',' read -r -a file_glob_values <<<"${file_globs}"
    for glob in "${file_glob_values[@]}"; do
      [[ -z "${glob}" ]] && continue
      [[ -n "${names}" ]] && names="${names} -o "
      names="${names}-iname \"${glob}\""
      [[ "${#name_args[@]}" -gt 0 ]] && name_args+=("-o")
      name_args+=("-iname" "${glob}")
    done
    base_cmd="find -L ${dir} -type f \( ${names} \) -exec grep ${gflags} \"${search_str}\" {}"

    echo "${YELLOW}Searching for \"${file_globs_type}\" matching: \"${search_str}\" in \"${dir}\" , " \
      "file_globs = [${file_globs}] ${extra_str} ${NC}"

    if [[ -n "${replace}" ]]; then
      if [[ "${file_globs_type}" = 'string' ]]; then
        __hhs_errcho "${FUNCNAME[0]}" "Can't search and replace non-Regex expressions !"
        return 1
      else
        if [[ "${HHS_MY_OS:-$(uname -s)}" == "Darwin" ]]; then
          ised="sed -i '' -E"
          sed_args=(sed -i '' -E)
          sed_filter_args=(sed -E)
        else
          ised="sed -i'' -r"
          sed_args=(sed -i'' -r)
          sed_filter_args=(sed -r)
        fi
        sed_expr="$(__hhs_sed_substitution_expr "${search_str}" "${repl_str}" "${sflags}")"
        full_cmd="${base_cmd} \; -exec $ised \"${sed_expr}\" {} +"
        full_cmd="${full_cmd} | ${sed_filter_args[*]} \"${sed_expr}\""
        full_cmd="${full_cmd} | __hhs_highlight \"${repl_str}\""
      fi
    else
      full_cmd="${base_cmd} + 2> /dev/null | __hhs_highlight \"${search_str}\""
    fi

    # Execute the search command.
    __hhs_log "DEBUG" "${FUNCNAME[0]} ${full_cmd}"
    if [[ -n "${replace}" ]]; then
      find -L "${dir}" -type f \( "${name_args[@]}" \) \
        -exec grep "${gflags}" "${search_str}" {} \; \
        -exec "${sed_args[@]}" "${sed_expr}" {} + |
        "${sed_filter_args[@]}" "${sed_expr}" |
        __hhs_highlight "${repl_str}"
      pipeline_status=("${PIPESTATUS[@]}")
      return "${pipeline_status[0]}"
    else
      find -L "${dir}" -type f \( "${name_args[@]}" \) \
        -exec grep "${gflags}" "${search_str}" {} + 2>/dev/null |
        __hhs_highlight "${search_str}"
    fi

    return $?
  fi
}
