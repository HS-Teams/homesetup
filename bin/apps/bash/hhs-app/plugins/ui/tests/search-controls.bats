#!/usr/bin/env bats

#  Script: search-controls.bats
# Purpose: HomeSetup Streamlit UI search control tests.
# Created: Jul 09, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

repo_dir="${BATS_TEST_DIRNAME}"
while [[ ! -f "${repo_dir}/install.bash" ]]; do
  repo_dir="${repo_dir}/.."
done
export HHS_REPO_DIR="$(cd "${repo_dir}" && pwd)"
export HHS_HOME="${HHS_REPO_DIR}"

load "${HHS_REPO_DIR}/tests/test_helper"
load_bats_libs
load "${HHS_REPO_DIR}/bin/apps/bash/hhs-app/plugins/ui/tests/hhs-ui-test-helpers.bash"

@test "when rendering Search controls then options, history, and submit state should be wired" {
  assert_file_contains_many "${constants_file}" \
'SEARCH_TYPES = ("Files", "Folders", "Strings")' 'SEARCH_FILTERS = ("All", "Containing")' \
    'SEARCH_PAGE_SIZE = 20' 'SEARCH_DIRECTORY_HISTORY_LIMIT = 20' \
    'SEARCH_TERM_HISTORY_LIMIT = 20' 'SEARCH_TERM_HISTORY_CACHE_KEY = "search_terms:history"' \
    'SEARCH_TERM_HISTORY_TTL_SECONDS = UI_CACHE_LOW_CHANGE_TTL_SECONDS'
  assert_file_not_contains "${constants_file}" 'SEARCH_SUBMIT_PRELOADER_DELAY_MS'
  assert_file_contains "${HHS_REPO_DIR}/bin/apps/py/hhs_ui/__init__.py" 'SEARCH_FILTERS'

  assert_file_contains_many "${ui_file}" \
'elif active_view == "Search":' 'render_search_view()' 'def build_hhs_search_command' \
    'def parse_hhs_search_results' 'def render_search_controls' \
    'placeholder="Search for files, folders, or strings"' 'key="search_path"' \
    'key="search_path_folder_picker_button"' 'on_click=request_path_picker' \
    'args=("search_path", st.session_state.get("search_path", ""), "folder")' \
    'st.container(key="search_controls")' 'with st.expander("Search Parameters", expanded=True):' \
    'def render_search_panel' '@st.fragment()' 'st.container(key="search_results")' \
    'def render_search_filters' 'st.container(key="search_filter_controls")' 'hhs_ui.SEARCH_FILTERS'

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("def render_search_controls", 1)[1].split("\ndef ", 1)[0]
assert '[1.15, 3.0, 0.22, 3.0, 0.22], vertical_alignment="bottom"' in body
assert (
    '"Kind",\n'
    '                options=hhs_ui_constants.SEARCH_TYPES,\n'
    '                key="search_type",'
) in body
assert "on_change=apply_search_type_change" in body
assert (
    '"Search terms",\n'
    '                options=search_term_options(),\n'
    '                index=None,\n'
    '                key="search_query",\n'
    '                placeholder="Search for files, folders, or strings",\n'
    '                accept_new_options=True,\n'
    '                on_change=submit_search_query,\n'
    '                width="stretch",'
) in body
assert (
    '"Search directory",\n'
    '                options=search_directory_options(),\n'
    '                key="search_path",\n'
    '                accept_new_options=True,\n'
    '                on_change=apply_search_directory_change,\n'
    '                width="stretch",'
) in body
assert 'st.text_input(\n                "Search terms"' not in body
assert 'st.text_input(\n                "Search directory"' not in body
assert 'label_visibility="collapsed"' not in body
assert body.index('key="search_path"') < body.index(
    'key="search_path_folder_picker_button"'
)
assert body.index('key="search_path_folder_picker_button"') < body.index(
    'key="search_query"'
)
assert body.index('key="search_query"') < body.index('key="search_submit_button"')
assert "render_search_submit_preloader_script()" not in body
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'"search_filter",' '"search_other_filter",' 'options=hhs_ui_constants.SEARCH_TYPES' \
    'st.columns(' '\[1.15, 3.0, 0.22, 3.0, 0.22\], vertical_alignment="bottom"'
  assert_file_contains "${ui_file}" '""'
  assert_file_not_contains_many "${ui_file}" \
'if st.button("Search", key="search_submit_button"' 'def render_search_submit_preloader_script' \
    'parentWindow.__hhsSearchSubmitPreloaderCleanup' 'search-submit-'
}

@test "when rendering Search filters then replace and option toggles should use stable state" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("def render_search_filters", 1)[1].split("\ndef ", 1)[0]
assert "render_table_filter_controls" not in body
assert "return selected_filter" not in body
assert "[1.15, 3.0, 0.22, 0.22, 0.22, 0.22, 0.22]" in body
assert "[1.15, 3.0, 0.22, 0.22, 0.22, 0.22]" in body
assert 'vertical_alignment="center"' in body
assert "key=\"search_filter\"" in body
assert "key=\"search_other_filter\"" in body
assert "if strings_selected:" in body
assert "with replace_column:" in body
assert "disabled=not strings_selected" not in body
for expected_toggle in (
    '"search_replace"',
    '"﯒"',
    '"Show replacement controls"',
    '"search_ignore_case", "Aa", "Ignore case (-i)"',
    '"search_words"',
    '""',
    '"Match words (-w)"',
    '"search_binary", "", "Search binary files (-b)"',
):
    assert expected_toggle in body
assert 'disabled=bool(st.session_state.get("search_replace", False))' in body
assert "key=\"search_other_filter_clear\"" in body
assert "width=\"stretch\"" in body
panel_decorator = source[: source.index("def render_search_panel")].rstrip().splitlines()[-1]
assert panel_decorator == "@st.fragment()"
panel_body = source.split("def render_search_panel", 1)[1].split("\ndef ", 1)[0]
assert "render_search_controls()" in panel_body
assert "render_search_replace_controls()" in panel_body
assert "render_search_filters()" in panel_body
assert "render_search_results()" in panel_body
assert "search_filter, search_text_filter" not in panel_body
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'def render_search_replace_controls' 'st.container(key="search_replace_controls")' \
    '<span class="hhs-search-replace-label">Replace by:</span>' 'key="search_replacement"' \
    'placeholder="Replacement string"' 'key="search_replace_submit_button"' '""' \
    'help="Search and Replace"' 'args=(True,)' '\[1.15, 6.22, 0.22\]'
  assert_file_not_contains "${ui_file}" '\[5.0, 0.85\], vertical_alignment="center"'
}

@test "when rendering Search comboboxes then VT100 shortcuts should be scoped to search terms" {
  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
body = source.split("def render_combobox_vt100_shortcuts_script", 1)[1].split("\ndef ", 1)[0]
assert "parentWindow.__hhsComboboxVt100Cleanup" in body
assert 'node.closest(\'[data-baseweb="select"]\')' in body
assert 'node.closest(".st-key-search_query")' in body
assert 'event.key === "Enter"' in body
assert "!event.ctrlKey" in body
assert "!event.metaKey" in body
assert "!event.altKey" in body
assert "selectPendingSearchTermAddOption(node)" in body
assert 'lowerText.startsWith("add:")' in body
assert "lowerText.includes(lowerValue)" in body
assert 'doc.querySelectorAll(optionSelectors.join(","))' in body.replace("\\n", "")
assert 'new MouseEvent(eventName' in body
assert "event.ctrlKey || event.metaKey" in body
for key in ("a", "e", "b", "f", "d", "h", "k", "u", "w"):
    assert f'case "{key}":' in body
assert "setCaret(node, 0, state.value.length)" in body
assert "setCaret(node, state.value.length, state.value.length)" in body
assert 'replaceRange(node, state.start, state.value.length, "", "deleteContentForward")' in body
assert 'doc.addEventListener("keydown", onKeydown, true)' in body
assert "render_combobox_vt100_shortcuts_script()" in source
PY
  assert_success
}

@test "when running Search then loader, result paging, and replace status should be wired" {
  assert_file_not_contains_many "${ui_file}" \
'event.target.closest(".st-key-search_path")' 'clearPendingSearchOverlay();' \
    'label.append("Searching for ", queryNode, " in ", pathNode)'
  assert_file_contains_many "${ui_file}" \
'source "${HHS_HOME}/bin/hhs-functions/bash/hhs-search.bash";' 'def search_loader_message' \
    'search_loader_message(query, search_path)' 'Searching for %primary_color%{query}%primary_color%' \
    'in %secondary_color%{search_path}%secondary_color%' \
    'timeout_seconds=hhs_ui_constants.UI_COMMAND_SLOW_READ_TIMEOUT_SECONDS'

  run python3 - "${ui_file}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start_search_body = source.split("def start_search_command", 1)[1].split("\ndef ", 1)[0]
render_controls_body = source.split("def render_search_controls", 1)[1].split("\ndef ", 1)[0]
assert "render_search_submit_preloader_script()" not in render_controls_body
assert "show_overlay=False" not in start_search_body
assert "show_preloader_event=True" in start_search_body

submit_body = source.split("def submit_search_query", 1)[1].split("\ndef ", 1)[0]
assert "def submit_search_query(replace_requested: bool = False)" in source
assert "replace = bool(replace_requested) and search_type == \"Strings\" and bool(" in submit_body
assert 'st.session_state["search_result_ignore_case"] = bool(' in submit_body
assert 'st.session_state.get("search_ignore_case", False)' in submit_body
assert 'st.session_state["search_result_words"] = bool(' in submit_body
assert 'st.session_state.get("search_words", False)' in submit_body
assert 'st.session_state["search_result_binary"] = bool(' in submit_body
assert 'st.session_state.get("search_binary", False)' in submit_body
assert 'st.session_state["search_result_replace"] = replace' in submit_body
assert 'st.session_state["search_result_replacement"] = replacement' in submit_body
assert 'st.session_state["_search_replace_status_cache_key"] = ""' in submit_body
assert 'push_floating_status("Enter replacement text before replacing.", "warn")' in submit_body

results_body = source.split("def render_search_results", 1)[1].split("\ndef ", 1)[0]
assert "search_filter = selected_search_result_filter()" in results_body
assert "text_filter = selected_search_result_text_filter()" in results_body
assert "replaced_count = len(rows)" in results_body
assert "push_search_replace_status(cache_key, replaced_count)" in results_body
assert "command = build_hhs_search_command(" in results_body
assert "cache_key = search_command_cache_key(" in results_body
for expected_argument in (
    "search_type",
    "query",
    "search_path",
    "ignore_case",
    "words",
    "binary",
    "replace",
    "replacement",
):
    assert expected_argument in results_body
PY
  assert_success

  assert_file_contains_many "${ui_file}" \
'clear_preloader()' 'def open_file' 'def open_search_result_path' \
    '__hhs_open' 'hhs_ui.SEARCH_OPEN_RESULT_QUERY_PARAM' 'search_result_path_link(row)'
  assert_file_not_contains "${ui_file}" 'render_search_path_results(rows)'
  assert_file_not_contains "${ui_file}" 'render_search_string_results(rows, query, text_filter)'
  assert_file_contains_many "${ui_file}" \
'render_search_path_results(visible_rows, search_type, total_count)' \
    'render_search_string_results(visible_rows, query, text_filter, total_count)' \
    '<th>Path</th><th>Line</th><th>Match</th></tr></thead>' \
    'return \["Path", "Size", "Modified"\]' 'return \["Path", "Modified"\]' \
    '__hhs_search_file' '__hhs_search_dir' '__hhs_search_string'
}

@test "when rendering Search load-more controls then automatic paging should be viewport based" {
  assert_file_contains_many "${ui_file}" \
'def visible_search_rows' 'def render_search_load_more' 'if visible_count >= total_count:' \
    'def render_search_auto_load_more' 'def render_search_auto_load_more_cleanup' \
    'render_search_auto_load_more_cleanup()' 'key="search_load_more_button"' \
    'render_search_auto_load_more(displayed_count, total_count)' \
    'const buttonSelector = ".st-key-search_load_more_button button";' 'const renderToken = ' \
    'const loadingMarkup = `' 'hhs-search-load-more-preloader-spinner" aria-hidden="true"><' \
    'Loading more results...' 'button.innerHTML = loadingMarkup' 'let requested = false;' \
    'let userReachedBottom = false;' 'activeController.displayedCount > displayedCount'
  assert_file_not_contains "${ui_file}" 'button.dataset.hhsAutoLoadRequested'

  assert_file_contains_many "${ui_file}" \
'const componentFrame = window.frameElement' \
    'const loadMoreContainer = doc.querySelector(".st-key-search_load_more")' \
    'const sentinel = loadMoreContainer || componentFrame' 'const bottomThreshold = 12;' \
    'target.getBoundingClientRect' 'rect.top <= viewportHeight - bottomThreshold' \
    'parentWindow.IntersectionObserver' 'observer.observe(sentinel)' \
    'rootMargin: "0px", threshold: 0.25' 'scrollTargets.forEach((target)' \
    'button.click()' 'userReachedBottom = nearBottom()' \
    'parentWindow.__hhsSearchAutoLoadController' 'delete parentWindow.__hhsSearchAutoLoadController'
  assert_file_not_contains "${ui_file}" 'pageHeight - 120'

  assert_file_contains_many "${ui_file}" \
'f"Load more results ({displayed_count}/{total_count}) ..."' \
    'hhs_ui_constants.SEARCH_PAGE_SIZE' 'cache_delete_tag("search")' \
    '"ttl_seconds": hhs_ui.UI_CACHE_NORMAL_TTL_SECONDS'
}

@test "when styling Search controls then result and toggle controls should share layout tokens" {
  assert_file_contains_many "${css_file}" \
'.st-key-search_path_folder_picker_button button' '.st-key-search_submit_button button' \
    '.st-key-search_load_more_button button' '.st-key-search_load_more {' \
    '.hhs-search-load-more-preloader' '.hhs-search-load-more-preloader-spinner' \
    'animation: hhs-search-load-more-spin 0.8s linear infinite' \
    '@keyframes hhs-search-load-more-spin'
  assert_file_not_contains_many "${css_file}" \
'.hhs-search-load-more-preloader-track' 'hhs-search-load-more-slide'

  assert_file_contains_many "${css_file}" \
'.st-key-search_other_filter_clear button' '.st-key-search_ignore_case_toggle_idle button' \
    '.st-key-search_replace_toggle_idle button' '.st-key-search_replace_toggle_selected button' \
    '.st-key-search_replace_controls' '.st-key-search_replace_submit_button button' \
    '.hhs-search-replace-label' '.st-key-search_ignore_case_toggle_selected button' \
    '.st-key-search_words_toggle_idle button' '.st-key-search_binary_toggle_selected button' \
    'box-shadow: inset 0 0 0 1px var(--hhs-theme-primary-color)' \
    '.st-key-search_submit_button {' '.st-key-search_controls \[data-testid="stVerticalBlock"\]' \
    '.st-key-search_controls \[data-testid="stHorizontalBlock"\]' 'align-items: end' \
    '> div\[data-testid="stColumn"\]:nth-child(3)' \
    '> div\[data-testid="stColumn"\]:nth-child(5)' 'margin-bottom: 0.28rem' \
    '.st-key-search_filter_controls \[data-testid="stHorizontalBlock"\]' \
    'grid-template-columns: minmax(9rem, 1.15fr)' \
    'grid-template-columns: max-content minmax(0, 1fr)' \
    'grid-template-columns: max-content minmax(0, 1fr) 2rem 2rem 2rem 2rem' \
    ':has(> div\[data-testid="stColumn"\]:nth-child(7))' 'grid-column: 2' \
    'white-space: nowrap' \
    '.st-key-search_filter_controls \[role="radiogroup"\]\[aria-label$="filter"\]' \
    'overflow-x: visible' '.st-key-search_controls {' \
    '\[data-testid="stExpanderDetails"\] > \[data-testid="stVerticalBlock"\]:has(.st-key-search_controls)' \
    'row-gap: var(--hhs-element-std-gap) !important' '.st-key-search_filter_controls {' \
    'margin-top: 0 !important' '.st-key-search_results {' '.hhs-search-results' \
    '.hhs-search-result-path-link' '.hhs-search-result-index' \
    'color: var(--hhs-theme-text-muted-color)' 'min-width: 1ch' \
    'background: var(--hhs-theme-secondary-background-color)' \
    'border: 1px solid var(--hhs-theme-dataframe-border-color)' \
    'background: var(--hhs-theme-dataframe-header-background-color)' 'color: var(--hhs-primary)' \
    'color: var(--hhs-theme-link-color)'
}
