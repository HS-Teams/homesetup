"""Pure Search helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import posixpath
import re
import shlex
import urllib.parse

from . import constants as hhs_ui_constants


def search_type_label(search_type: str) -> str:
    """Return the display label for a Search type key."""
    return hhs_ui_constants.SEARCH_TYPE_LABELS.get(search_type, search_type)


def normalized_search_type(search_type: object) -> str:
    """Return a valid Search type key."""
    candidate = str(search_type or "").strip()
    if candidate in hhs_ui_constants.SEARCH_TYPES:
        return candidate
    return hhs_ui_constants.SEARCH_TYPES[0]


def search_glob_from_query(query: str) -> str:
    """Return the file or folder glob used for a Search query."""
    clean_query = query.strip()
    if any(character in clean_query for character in "*?[],"):
        return clean_query
    return f"*{clean_query}*"


def build_hhs_search_setup_command() -> str:
    """Build shell setup for HomeSetup Search helper functions."""
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-text.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-search.bash"; '
        "function __hhs_highlight() { cat -; }; "
    )


def build_hhs_search_modified_results_command(search_command: str) -> str:
    """Wrap a Search command so path results include metadata columns."""
    return (
        f"{search_command} | while IFS= read -r line; do "
        'case "${line}" in '
        '""|Searching\\ for*) ;; '
        "*) "
        'if [ -e "${line}" ]; then '
        'if modified=$(stat -c %Y "${line}" 2>/dev/null); then :; '
        'else modified=$(stat -f %m "${line}" 2>/dev/null || printf "0"); fi; '
        'if [ -f "${line}" ]; then '
        'if size=$(stat -c %s "${line}" 2>/dev/null); then :; '
        'else size=$(stat -f %z "${line}" 2>/dev/null || printf ""); fi; '
        'else size=""; fi; '
        'else modified=0; size=""; fi; '
        'printf "__HHS_SEARCH_RESULT__\\t%s\\t%s\\t%s\\n" "${line}" "${modified}" "${size}" ;; '
        "esac; "
        "done"
    )


def shell_home_path_argument(path_value: str) -> str:
    """Return a shell-safe path argument, expanding home tokens on the target host."""
    clean_path = path_value.strip() or "."
    if clean_path in {"~", "$HOME", "${HOME}"}:
        return '"${HOME:-.}"'
    for home_prefix in ("~/", "$HOME/", "${HOME}/"):
        if clean_path.startswith(home_prefix):
            suffix = clean_path[len(home_prefix) :]
            if not suffix:
                return '"${HOME:-.}"'
            return f'"${{HOME:-.}}"/{shlex.quote(suffix)}'
    return shlex.quote(clean_path)


def normalized_search_option_values(
    search_type: str,
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
    replace: bool = False,
    replacement: object = "",
) -> tuple[bool, bool, bool, bool, str]:
    """Return Search option flags that apply to the selected Search type."""
    if normalized_search_type(search_type) != "Strings":
        return (False, False, False, False, "")
    should_replace = bool(replace)
    return (
        bool(ignore_case),
        bool(words) and not should_replace,
        bool(binary),
        should_replace,
        str(replacement or "") if should_replace else "",
    )


def search_string_option_flags(
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
    replace: bool = False,
    replacement: object = "",
) -> list[str]:
    """Return __hhs_search_string option arguments for selected Search toggles."""
    flags: list[str] = []
    if ignore_case:
        flags.append("-i")
    if words:
        flags.append("-w")
    if binary:
        flags.append("-b")
    if replace:
        flags.extend(("-r", str(replacement or "")))
    return flags


def build_hhs_search_command(
    search_type: str,
    query: str,
    search_path: str,
    ignore_case: bool = False,
    words: bool = False,
    binary: bool = False,
    replace: bool = False,
    replacement: object = "",
) -> str:
    """Build the HomeSetup search command for the selected Search type."""
    setup_command = build_hhs_search_setup_command()
    search_root = shell_home_path_argument(search_path)
    safe_query = shlex.quote(query.strip())
    if search_type == "Folders":
        safe_glob = shlex.quote(search_glob_from_query(query))
        search_command = f"{setup_command}__hhs_search_dir {search_root} {safe_glob}"
        return build_hhs_search_modified_results_command(search_command)
    if search_type == "Strings":
        option_values = normalized_search_option_values(
            search_type, ignore_case, words, binary, replace, replacement
        )
        option_args = " ".join(
            shlex.quote(flag) for flag in search_string_option_flags(*option_values)
        )
        if option_args:
            option_args = f" {option_args}"
        return f"{setup_command}__hhs_search_string {search_root}{option_args} {safe_query} '*'"
    safe_glob = shlex.quote(search_glob_from_query(query))
    search_command = f"{setup_command}__hhs_search_file {search_root} {safe_glob}"
    return build_hhs_search_modified_results_command(search_command)


def build_hhs_open_search_result_command(path: str) -> str:
    """Build the HomeSetup command used to open one Search result path."""
    safe_path = shlex.quote(path.strip())
    return (
        'export HHS_DIR="${HHS_DIR}"; '
        'source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"; '
        'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-built-ins.bash"; '
        f"__hhs_open {safe_path}"
    )


def search_result_download_name(path: str) -> str:
    """Return the local filename for a downloaded remote Search result."""
    clean_name = posixpath.basename(str(path).rstrip("/")).strip()
    return clean_name or "search-result"


def path_from_file_uri(path_or_uri: str) -> str:
    """Return the filesystem path from a plain path or file URI."""
    clean_value = path_or_uri.strip()
    parsed_uri = urllib.parse.urlparse(clean_value)
    if parsed_uri.scheme != "file":
        return clean_value
    return urllib.parse.unquote(parsed_uri.path)


def search_relative_path(path: str, search_path: str) -> str:
    """Return a Search result path relative to the submitted Search folder."""
    clean_path = path.strip()
    clean_search_path = search_path.strip()
    if not clean_path or not clean_search_path:
        return clean_path
    normalized_path = posixpath.normpath(clean_path)
    normalized_search_path = posixpath.normpath(clean_search_path)
    if posixpath.isabs(normalized_path) != posixpath.isabs(normalized_search_path):
        return clean_path
    try:
        relative_path = posixpath.relpath(normalized_path, normalized_search_path)
    except ValueError:
        return clean_path
    if relative_path == ".":
        return "."
    if relative_path.startswith("../"):
        return clean_path
    return relative_path


def search_full_path(path: str, search_path: str) -> str:
    """Return the full path represented by a Search result path."""
    clean_path = path.strip()
    clean_search_path = search_path.strip()
    if not clean_path:
        return ""
    if posixpath.isabs(clean_path) or not clean_search_path:
        return posixpath.normpath(clean_path)
    return posixpath.normpath(posixpath.join(clean_search_path, clean_path))


def search_output_line_is_status(line: str) -> bool:
    """Return whether one Search output line is helper or UI status text."""
    clean_line = hhs_ui_constants.ESCAPED_ANSI_ESCAPE_PATTERN.sub(
        "",
        hhs_ui_constants.ANSI_ESCAPE_PATTERN.sub("", line),
    )
    clean_line = re.sub(r"\s+", " ", clean_line).strip()
    return clean_line.startswith("Searching for")
