#!/usr/bin/env bash

#  Script: hhs-text.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Highlight words from the piped stream.
# @param $1..$N [Opt] : Optional grep flags, followed by the search pattern and optional filename.
# shellcheck disable=SC2120
function __hhs_highlight() {

  local search file hl_color="${HHS_HIGHLIGHT_COLOR}"
  local -a grep_opts

  grep_opts=(-E -i --color=always)

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [grep_flags...] <text_to_highlight> [filename]"
    echo ''
    echo '  Notes: '
    echo '    grep_flags: Optional grep-compatible flags such as -i, -v or -n.'
    echo '                Use -- before the pattern if it starts with a dash.'
    echo '    filename: If not provided, stdin will be used instead.'
    return 1
  else
    while [[ $# -gt 0 ]]; do
      case "$1" in
      --)
        shift
        break
        ;;
      -*)
        grep_opts+=("$1")
        shift
        ;;
      *)
        break
        ;;
      esac
    done

    search="${1:-.*}"
    file="${2:-/dev/stdin}"
    hl_color=${HHS_HIGHLIGHT_COLOR//\e[/}
    hl_color=${HHS_HIGHLIGHT_COLOR/m/}
    GREP_COLOR="${hl_color}" grep "${grep_opts[@]}" "${search}" "${file}"
  fi

  return 0
}

# @function: Pretty print (format) JSON from file, string, or piped input.
# @param $1 [Opt]: JSON string or path to JSON file.
__hhs_json_print() {
  # Show help if no args or if help is requested and stdin is not piped
  if [[ "$1" == "-h" || "$1" == "--help" || ( $# -eq 0 && -t 0 ) ]]; then
    echo "Usage: ${FUNCNAME[0]} [JSON_STRING_OR_FILE]"
    echo
    echo "Formats and pretty-prints JSON using jq or json_pp."
    echo
    echo "Accepted input formats:"
    echo "  1. Direct string  => __hhs_json_print '{\"a\":1}'"
    echo "  2. File path      => __hhs_json_print ./data.json"
    echo "  3. Piped input    => echo '{\"a\":1}' | __hhs_json_print"
    echo
    echo "Options:"
    echo "  -h, --help        Show this help message"
    return 1
  fi

  local input="${1:-}"
  local from_stdin=false
  local use_file=false
  local formatter=""
  local raw_json=""

  # Detect piped input
  if [[ ! -t 0 ]]; then
    from_stdin=true
    raw_json="$(cat -)"
  elif [[ -n "${input}" && -f "${input}" && -s "${input}" ]]; then
    use_file=true
  else
    raw_json="${input}"
  fi

  # Choose available JSON formatter
  if __hhs_has "jq"; then
    formatter="jq"
  elif __hhs_has "json_pp"; then
    formatter="json_pp"
  fi

  # Apply formatter
  if [[ "${from_stdin}" == true ]]; then
    case "${formatter}" in
      jq)       echo "${raw_json}" | jq ;;
      json_pp)  echo "${raw_json}" | json_pp -f json -t json -json_opt pretty,indent,escape_slash ;;
      *)        echo -e "${BLUE}${raw_json}${NC}" ;;
    esac
  elif [[ "${use_file}" == true ]]; then
    # shellcheck disable=SC2119
    case "${formatter}" in
      jq)       jq < "${input}" ;;
      json_pp)  json_pp -f json -t json -json_opt pretty,indent,escape_slash < "${input}" ;;
      *)        __hhs_highlight < "${input}" ;;
    esac
  elif [[ -n "${raw_json}" ]]; then
    case "${formatter}" in
      jq)       echo "${raw_json}" | jq ;;
      json_pp)  echo "${raw_json}" | json_pp -f json -t json -json_opt pretty,indent,escape_slash ;;
      *)        echo -e "${BLUE}${raw_json}${NC}" ;;
    esac
  else
    echo -e "${ORANGE}WARNING${NC}: No input provided. Use --help for usage." >&2
    return 1
  fi

  return 0
}

# @function: Pretty print (format) XML/HTML string.
# @param $1 [Opt]: XML string or path to XML file.
__hhs_xml_print() {
  local input="$1"

  # Show help if no args or if help is requested and stdin is not piped
  if [[ "$1" == "-h" || "$1" == "--help" || ( $# -eq 0 && -t 0 ) ]]; then
    echo "Usage: ${FUNCNAME[0]} [XML_OR_HTML_FILE]"
    echo
    echo "Formats and pretty-prints XML or HTML using xmllint (preferred) or Python fallback."
    echo
    echo "Accepted input formats:"
    echo "  1. Direct string  => echo '<root><a>1</a></root>' | ${FUNCNAME[0]}"
    echo "  2. File path      => ${FUNCNAME[0]} ./data.xml"
    echo "  3. Piped input    => cat ./data.xml | ${FUNCNAME[0]}"
    echo
    echo "Options:"
    echo "  -h, --help        Show this help message"
    return 1
  fi

  if __hhs_has "xmllint"; then
    if [[ -f "${input}" && -s "${input}" ]]; then
      xmllint --format "${input}"
    else
      xmllint --format <(echo "${input}")
    fi
  else
    # Fallback to Python if xmllint is not available
    if [[ -f "${input}" && -s "${input}" ]]; then
      python3 -c "import xml.dom.minidom; print(xml.dom.minidom.parse('${input}').toprettyxml())"
    else
      python3 -c "import sys, xml.dom.minidom; print(xml.dom.minidom.parseString(sys.stdin.read()).toprettyxml())" <<<"${input}"
    fi
  fi

  return $?
}

# @function: Convert string into it's decimal ASCII representation.
# @param $1 [Req] : The string to convert.
function __hhs_ascof() {

  if [[ $# -eq 0 || '-h' == "$1" ]]; then
    echo "usage: ${FUNCNAME[0]} <string>"
    return 1
  elif __hhs_has od; then
    echo ''
    echo -en "${GREEN}Dec:${NC}"
    echo -en "${@}" | od -An -t uC | head -n1 | awk '{for(i=1;i<=NF;i++)printf " %03d",$i;print ""}'
    echo -en "${GREEN}Hex:${NC}"
    echo -en "${@}" | od -An -t xC | head -n 1 | awk '{for(i=1;i<=NF;i++)printf " %2d",$i;print ""}'
    echo -en "${GREEN}Str:${NC}"
    echo -e " ${*}"
    echo ''
  else
    __hhs_errcho "${FUNCNAME[0]}: 'od' command is required to run this function."
    return 1
  fi

  return 0
}

if __hhs_has "hexdump"; then

  # @function: Convert unicode to hexadecimal.
  # @param $1..$N [Req] : The unicode values to convert.
  function __hhs_utoh() {

    local result converted uni ret_val=1

    if [[ $# -le 0 || "$1" == "-h" || "$1" == "--help" ]]; then
      echo "usage: ${FUNCNAME[0]} <4d-unicode...>"
      echo ''
      echo '  Notes: '
      echo '    - unicode is a four digits hexadecimal number. E.g:. F205'
      echo '    - exceeding digits will be ignored'
      return 1
    else
      echo ''
      for next in "$@"; do
        hexa="${next:0:4}"
        # More digits will be ignored
        uni="$(printf '%04s' "${hexa}")"
        [[ ${uni} =~ [0-9A-Fa-f]{4} ]] || continue
        echo -en "[${HHS_HIGHLIGHT_COLOR}Unicode:'\u"
        # shellcheck disable=SC2016
        echo -n "${uni}"
        echo -en "'${NC}]"
        converted=$(python3 -c "import struct; print(bytes.decode(struct.pack('<I', int('${uni}', 16)), 'utf_32_le'))" | hexdump -Cb)
        ret_val=$?
        result=$(awk '
        NR == 1 {printf "  Hex => "; print "\\\\x"$2"\\\\x"$3"\\\\x"$4}
        NR == 2 {printf "  Oct => "; print "\\"$2"\\"$3"\\"$4}
        NR == 1 {printf "  Icn => "; print "\\x"$2"\\x"$3"\\x"$4}
        ' <<<"${converted}")
        echo -e "${GREEN}${result}${NC}\n"
      done
    fi

    return ${ret_val}
  }
fi

# @function: View markdown files with syntax highlighting.
# @param $1..$N [Req] : The markdown file(s) to view
function __hhs_md_viewer() {
  # Glow
  if __hhs_has 'glow'; then
    glow -w 120 -s "dark" "${@}"
  elif __hhs_has 'mdless'; then
    mdless "${@}"
  elif __hhs_has 'bat'; then
    bat "${@}"
  else
    cat "${@}"
  fi
}
