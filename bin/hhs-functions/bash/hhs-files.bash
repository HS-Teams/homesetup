#!/usr/bin/env bash

#  Script: hhs-files.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: List files sorted by the specified column.
# @param $1 [Opt] : The column to sort; 9 (filename) by default
function __hhs_ls_sorted() {

  local col_number

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    if __hhs_has 'colorls'; then
      \colorls --help
      return 0
    else
      echo "usage: ${FUNCNAME[0]} [column_name] [-reverse]"
      echo ''
      echo '  Columns:'
      echo '    type  : First column gives the type of the file/dir and the file permissions.'
      echo '    links : Second column is the number of links to the file/dir.'
      echo '    owner : Third column is the user who owns the file.'
      echo '    group : Fourth column is the Unix group of users to which the file belongs.'
      echo '    size  : Fifth column is the size of the file in bytes.'
      echo '    month : Sixth column is the Month at which the file was last changed.'
      echo '    day   : Seventh column is the Day at which the file was last changed.'
      echo '    time  : Eighth column is the Year or Time at which the file was last changed.'
      echo '    name  : The last column is the name of the file.'
      echo ''
      echo ''
      echo '  Notes: '
      echo '    - If -reverse is specified, reverse the order or sorting'
    fi
    return 0
  else
    if __hhs_has 'colorls'; then
      \colorls --long --sort="${1:-size}"
      return 0
    else
      col_number="${1:-9}"
      col_number="${col_number//type/1}"  ; col_number="${col_number//links/2}"
      col_number="${col_number//owner/3}" ; col_number="${col_number//group/4}"
      col_number="${col_number//size/5}"  ; col_number="${col_number//month/6}"
      col_number="${col_number//day/7}"   ; col_number="${col_number//time/8}"
      col_number="${col_number//name/9}"
      # shellcheck disable=SC2012
      if [[ "${2}" == "-reverse" ]]; then
        \ls -la | sort -r -k "${col_number}"
      else
        \ls -la | sort -k "${col_number}"
      fi
    fi
    return $?
  fi
}

# @function: Move files recursively to the Trash.
# @param $1 [Req] : The GLOB expression of the file/directory search.
function __hhs_del_tree() {

  local all trash_dest search_path glob dry_run='Y' ans

  if [[ $# -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [-n|-f|-i] <search_path> <glob_expr>"
    echo ''
    echo '  Options:'
    echo '    -n | --dry-run      : Just show what would be deleted instead of removing it.'
    echo '    -f | --force        : Actually delete all files/directories it finds.'
    echo '    -i | --interactive  : Interactive deleting files/directories.'
    echo '  Notes:'
    echo '    - If no option is specified, dry-run is default.'
    return 1
  else

    case "$1" in
    '-f' | '--force')
      dry_run='N'
      shift
      ;;
    '-n' | '--dry-run')
      dry_run='Y'
      shift
      ;;
    '-i' | '--interactive')
      dry_run='I'
      shift
      ;;
    esac

    if [[ "$1" == '/' ]] || [[ "$(pwd)" == '/' && "$1" == '.' ]]; then
      __hhs_errcho "${FUNCNAME[0]}" "Can't del-tree the root folder"
      return 1
    fi

    search_path="$1"
    glob="${2:-*.*}"
    echo -e "${BLUE}Deleting files from ${search_path} matching ${glob}${NC}"
    all=$(find -L "${search_path}" -name "${glob}" 2>/dev/null)

    if [[ -n "${all}" ]]; then
      if [[ "${dry_run}" == 'N' || "${dry_run}" == 'I' ]]; then
        for next in ${all}; do
          [[ "${dry_run}" == 'I' ]] && read -r -n 1 -p "Delete ${next} y/[n]? " ans && echo ''
          [[ "${dry_run}" == 'I' ]] || ans='Y'
          if [[ "${ans}" == 'y' || "${ans}" == 'Y' ]]; then
            trash_dest="${next##*/}"
            while [[ -e "${TRASH}/${trash_dest}" ]]; do
              trash_dest="${next##*/}-$(\date '+%s%S')"
            done
            if \mv "${next}" "${TRASH}/${trash_dest}" &>/dev/null; then
              echo -e "${ORANGE}Trashed => ${WHITE}${next} -> ${TRASH}/${trash_dest}${NC}"
            else
              __hhs_errcho "${FUNCNAME[0]}" "Could not move \"${next}\" to ${TRASH}/${trash_dest}"
            fi
          fi
        done
      else
        for next in ${all}; do
          echo -e "${YELLOW}Would delete ${WHITE}-> ${next}${NC}"
        done
      fi
    else
      echo ' '
      echo "${ORANGE}No files or folders matching \"${glob}\" were found in \"$1\" !${NC}"
      echo ' '
    fi
  fi

  return 0
}
