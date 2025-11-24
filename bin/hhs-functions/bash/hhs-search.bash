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

  local names expr file_globs dir full_cmd

  if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <search_path> [file_globs...]"
    echo ''
    echo '  Notes: '
    echo '    - <file_globs...>: Comma separated globs. E.g: "*.txt,*.md,*.rtf"'
    return 1
  else
    dir="${1}"
    file_globs="${2}"
    expr="e=\"${file_globs}\"; a=e.split(','); print(' -o '.join(['-iname \"{}\"'.format(s) for s in a]))"
    names=$(python3 -c "${expr}")
    full_cmd="find -L ${dir} -type f \( ${names} \) 2> /dev/null | __hhs_highlight \"(${file_globs//\*/.*}|$)\""
    echo "${YELLOW}Searching for files matching: \"${file_globs}\" in \"${dir}\" ${NC}"
    __hhs_log "DEBUG" "${FUNCNAME[0]} ${full_cmd}"
    eval "${full_cmd}"

    return $?
  fi
}

# @function: Search for directories and links to directories recursively.
# @param $1 [Req] : The base search path.
# @param $2 [Opt] : The search glob expressions.
# @compatible: bash zsh
function __hhs_search_dir() {

  local names expr dir dir_globs full_cmd

  if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <search_path> [dir_globs...]"
    echo ''
    echo '  Notes: '
    echo '    - <dir_globs...>: Comma separated directories. E.g:. "dir1,dir2,dir2"'
    return 1
  else
    dir="${1}"
    dir_globs="${2}"
    expr="e=\"${dir_globs}\"; a=e.split(','); print(' -o '.join(['-iname \"{}\"'.format(s) for s in a]))"
    names=$(python3 -c "${expr}")
    full_cmd="find -L ${dir} -type d \( ${names} \) 2> /dev/null | __hhs_highlight \"(${dir_globs//\*/.*}|$)\""

    # Execute the search command.
    echo "${YELLOW}Searching for folders matching: [${dir_globs}] in \"${dir}\" ${NC}"
    __hhs_log "DEBUG" "${FUNCNAME[0]} ${full_cmd}"
    eval "${full_cmd}"

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

  local gflags extra_str replace names file_globs_type='regex' gflags='-HnEI' sflags='g'
  local names_expr search_str base_cmd full_cmd dir repl_str

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
    names_expr="e=\"${file_globs}\"; a=e.split(','); print(' -o '.join(['-iname \"{}\"'.format(s) for s in a]))"
    names=$(python3 -c "${names_expr}")
    base_cmd="find -L ${dir} -type f \( ${names} \) -exec grep ${gflags} \"${search_str}\" {}"

    echo "${YELLOW}Searching for \"${file_globs_type}\" matching: \"${search_str}\" in \"${dir}\" , file_globs = [${file_globs}] ${extra_str} ${NC}"

    if [[ -n "${replace}" ]]; then
      if [[ "${file_globs_type}" = 'string' ]]; then
        __hhs_errcho "${FUNCNAME[0]}" "Can't search and replace non-Regex expressions !"
        return 1
      else
        [[ "${HHS_MY_OS}" == "Darwin" ]] && ised="sed -i '' -E"
        [[ "${HHS_MY_OS}" == "Linux" ]] && ised="sed -i'' -r"
        full_cmd="${base_cmd} \; -exec $ised \"s/${search_str}/${repl_str}/${sflags}\" {} + | sed \"s/${search_str}/${repl_str}/${sflags}\"  | __hhs_highlight \"${repl_str}\""
      fi
    else
      full_cmd="${base_cmd} + 2> /dev/null | __hhs_highlight \"${search_str}\""
    fi

    # Execute the search command.
    __hhs_log "DEBUG" "${FUNCNAME[0]} ${full_cmd}"
    eval "${full_cmd}"

    return $?
  fi
}
