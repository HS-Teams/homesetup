#!/usr/bin/env python3
"""Reusable Streamlit table, chart, and styled-data helpers for HomeSetup."""

from __future__ import annotations

import html
import json
import os
import re
from collections.abc import Callable
from typing import Literal, TypeVar

import altair as alt
import pandas as pd
import streamlit as st

import hhs_ui
import hhs_ui.core.constants as hhs_ui_constants
from hhs_ui.core.theme_assets import theme_custom_properties
from hhs_ui.core.ui_state import save_ui_state

TableControlsResult = TypeVar("TableControlsResult")


def home_shopt_is_on(row: dict[str, str]) -> bool:
    """Return whether a shell option row is currently enabled."""
    return row.get("State") == "ON"


def home_shopt_is_off(row: dict[str, str]) -> bool:
    """Return whether a shell option row is currently disabled."""
    return row.get("State") == "OFF"


def tool_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for tool check statuses."""
    value_text = str(value).lower()
    if "not found" in value_text:
        return "color: #ff5555; font-weight: 800;"
    if "not installed" in value_text:
        return "color: #ff5555; font-weight: 800;"
    if "installed" in value_text:
        return "color: #50fa7b; font-weight: 800;"
    if "aliased" in value_text:
        return "color: #8be9fd; font-weight: 800;"
    if "function" in value_text:
        return "color: #bd93f9; font-weight: 800;"
    return "color: #f8f8f2; font-weight: 800;"


def styled_tool_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return tool rows with styled Status cells."""
    dataframe = pd.DataFrame(rows)
    styler = dataframe.style
    if "Status" in dataframe:
        styler = styler.map(tool_status_cell_style, subset=["Status"])
    return styler


def shopt_status_cell_style(value: object) -> str:
    """Return the dataframe cell style for shell option statuses."""
    value_text = str(value).lower()
    if "off" in value_text:
        return "color: #ff5555; font-weight: 800;"
    if "on" in value_text:
        return "color: #50fa7b; font-weight: 800;"
    return "color: #f8f8f2; font-weight: 800;"


def styled_shopt_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return shell option rows with styled Status cells."""
    dataframe = pd.DataFrame(rows)
    styler = dataframe.style
    if "Status" in dataframe:
        styler = styler.map(shopt_status_cell_style, subset=["Status"])
    return styler


def home_tool_status_text(row: dict[str, str]) -> str:
    """Return a normalized Home tool status for action button decisions."""
    return str(row.get("Status", "")).lower()


def home_tool_is_installed(row: dict[str, str]) -> bool:
    """Return whether a Home tool row is currently installed."""
    status = home_tool_status_text(row)
    return "installed" in status and "not installed" not in status


def home_tool_is_not_found(row: dict[str, str]) -> bool:
    """Return whether a Home tool row is currently missing."""
    status = home_tool_status_text(row)
    return "not found" in status or "not installed" in status


def home_tool_is_aliased(row: dict[str, str]) -> bool:
    """Return whether a Home tool row resolves through a shell alias."""
    return "aliased" in home_tool_status_text(row)


def selected_item_editing_key(table_key: str | None, selected_index: int) -> str:
    """Return the session key for a selected table row edit mode."""
    safe_key = table_key or "hhs_table"
    return f"{safe_key}_selected_editing_{selected_index}"


def table_component_key(table_key: str | None, suffix: str) -> str:
    """Return a stable Streamlit key for table-adjacent helper components."""
    safe_key = table_key or "hhs_table"
    return f"{safe_key}_{suffix}"


def enable_selected_item_edit(
    editing_key: str, edit_key: str | None = None, edit_value: str = ""
) -> None:
    """Enable inline editing for the current selected table row."""
    st.session_state[editing_key] = True
    if edit_key:
        st.session_state[edit_key] = edit_value


def cancel_selected_item_edit(
    editing_key: str,
    edit_key: str | None = None,
    reset_selection: Callable[[], None] | None = None,
) -> None:
    """Cancel inline editing and clear the current selected table row."""
    st.session_state[editing_key] = False
    if edit_key:
        st.session_state.pop(edit_key, None)
    if reset_selection:
        reset_selection()


def selected_label_parts(text: str) -> tuple[str, str]:
    """Return the selected label and value parts from display text."""
    label, separator, value = text.partition(":")
    if not separator:
        return text, ""
    return f"{label}:", value.strip()


def table_editable_flag(
    editable: bool | Callable[[dict[str, str], int], bool],
    row: dict[str, str],
    row_index: int,
) -> bool:
    """Return whether the selected table row supports inline editing."""
    if callable(editable):
        return bool(editable(row, row_index))
    return bool(editable)


def table_edit_args(
    edit_args: (
        Callable[[dict[str, str], int], tuple[object, ...]] | tuple[object, ...] | None
    ),
    row: dict[str, str],
    row_index: int,
) -> tuple[object, ...]:
    """Return callback args for a selected row edit widget."""
    if callable(edit_args):
        return edit_args(row, row_index)
    return edit_args or ()


def table_edit_key(
    edit_key: Callable[[dict[str, str], int], str] | str | None,
    row: dict[str, str],
    row_index: int,
) -> str:
    """Return the Streamlit key for a selected row edit widget."""
    if callable(edit_key):
        return edit_key(row, row_index)
    return str(edit_key or f"selected_table_edit_value_{row_index}")


def table_edit_value(
    edit_value: Callable[[dict[str, str], int], str] | str | None,
    row: dict[str, str],
    row_index: int,
) -> str:
    """Return the initial value for a selected row edit widget."""
    if callable(edit_value):
        return edit_value(row, row_index)
    if edit_value is not None:
        return str(edit_value)
    return str(row.get("Value", ""))


def render_selected_table_item(
    label: str,
    value: str,
    selected_index: int,
    table_key: str | None,
    editable: bool,
    edit_key: str | None = None,
    edit_value: str = "",
    edit_label: str = "Selected value",
    edit_height: int = hhs_ui.ENV_VALUE_EDITOR_HEIGHT,
    edit_max_chars: int | None = None,
    edit_on_change: Callable[..., None] | None = None,
    edit_args: tuple[object, ...] = (),
    edit_folder_picker: bool = False,
    folder_picker_callback: Callable[[str, str], None] | None = None,
    reset_selection: Callable[[], None] | None = None,
    selected_actions: list[dict[str, object]] | None = None,
) -> None:
    """Render the normalized selected table row summary and optional editor."""
    if edit_folder_picker and folder_picker_callback is None:
        raise ValueError(
            "folder_picker_callback is required when edit_folder_picker is true"
        )
    editing_key = selected_item_editing_key(table_key, selected_index)
    is_editing = bool(st.session_state.get(editing_key, False)) and editable
    if editable and edit_key is not None:
        st.session_state.setdefault(edit_key, edit_value)
    visible_actions = selected_actions or []
    edit_action_count = 1 + len(visible_actions) + int(edit_folder_picker)
    action_weights = [0.035] * edit_action_count

    if is_editing and edit_key is not None:
        columns = st.columns(
            [1, *action_weights],
            vertical_alignment="center",
            gap="small",
            width="stretch",
        )
        with columns[0]:
            st.text_input(
                f"{value}:",
                key=edit_key,
                max_chars=edit_max_chars,
                help=f"Edit {edit_label.lower()}.",
                on_change=edit_on_change,
                placeholder=edit_label,
                args=edit_args,
            )
        action_start_index = 1
        if edit_folder_picker:
            with columns[action_start_index]:
                st.button(
                    "",
                    key=f"{editing_key}_folder_picker_button",
                    help="Select folder",
                    on_click=folder_picker_callback,
                    args=(edit_key, edit_value),
                    width="stretch",
                )
            action_start_index += 1
        with columns[action_start_index]:
            st.button(
                "ﰸ",
                key=f"{editing_key}_cancel_button",
                help="Cancel edit",
                on_click=cancel_selected_item_edit,
                args=(editing_key, edit_key, reset_selection),
                width="stretch",
            )
        render_selected_table_actions(
            visible_actions, columns[action_start_index + 1 :], selected_index
        )
        return

    if editable:
        columns = st.columns(
            [1, *action_weights],
            vertical_alignment="center",
            gap="small",
            width="stretch",
        )
        value_col = columns[0]
        action_cols = columns[1:]
    else:
        if visible_actions:
            columns = st.columns(
                [1, *[0.035] * len(visible_actions)],
                vertical_alignment="center",
                gap="small",
                width="stretch",
            )
            value_col = columns[0]
            action_cols = columns[1:]
        else:
            value_col = st.container()
            action_cols = []
    display_value = display_table_value(value)
    with value_col:
        st.markdown(
            (
                '<span class="hhs-selected-item-line">'
                f'<span class="hhs-selected-item-label">{html.escape(label)}</span>'
                f'<span class="hhs-selected-item-value">{html.escape(str(display_value))}</span>'
                "</span>"
            ),
            unsafe_allow_html=True,
        )
    if editable and action_cols:
        with action_cols[0]:
            st.button(
                "",
                key=f"{editing_key}_button",
                help="Edit",
                on_click=enable_selected_item_edit,
                args=(editing_key, edit_key, edit_value),
                width="stretch",
            )
        render_selected_table_actions(visible_actions, action_cols[1:], selected_index)
    elif action_cols:
        render_selected_table_actions(visible_actions, action_cols, selected_index)


def render_selected_table_actions(
    actions: list[dict[str, object]],
    columns: list[object],
    selected_index: int,
) -> None:
    """Render selected-row glyph action buttons beside edit controls."""
    for column, action in zip(columns, actions):
        label = str(action.get("glyph", action.get("label", "")))
        key_prefix = str(action.get("key_prefix", label.lower().replace(" ", "_")))
        with column:
            st.button(
                label,
                disabled=bool(action.get("disabled", False)),
                help=action.get("help") or str(action.get("label", "")),
                key=f"{key_prefix}_{selected_index}_selected",
                on_click=execute_selected_table_action,
                args=(
                    action.get("reset_selection"),
                    action.get("on_click"),
                    tuple(action.get("args", ())),
                ),
                width=str(action.get("width", "stretch")),
            )


def execute_selected_table_action(
    reset_selection: Callable[[], None] | None,
    callback: Callable[..., None] | None,
    callback_args: tuple[object, ...],
) -> None:
    """Run a selected-row action and optionally clear the table selection first."""
    if reset_selection:
        reset_selection()
    if callback:
        callback(*callback_args)


def env_path_aliases(
    environment_values: dict[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Return known environment variables that visually abbreviate absolute paths."""
    values = environment_values if environment_values is not None else os.environ
    aliases = []
    for raw_name, raw_value in values.items():
        name = str(raw_name).strip()
        value = str(raw_value).strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            continue
        if not value.startswith(os.sep) or os.pathsep in value or value == os.sep:
            continue
        aliases.append((name, value.rstrip(os.sep)))
    return sorted(aliases, key=lambda item: len(item[1]), reverse=True)


def display_path_value(
    value: str,
    environment_values: dict[str, str] | None = None,
) -> str:
    """Return a display-only path value with known environment-variable prefixes."""
    display_value = value
    for name, path_prefix in env_path_aliases(environment_values):
        replacement = f"${{{name}}}"
        escaped_prefix = re.escape(path_prefix)
        display_value = re.sub(
            rf"(?<![A-Za-z0-9_.-]){escaped_prefix}(?=$|{re.escape(os.sep)}|[:\s'\"`])",
            replacement,
            display_value,
        )
    return display_value


def display_table_value(
    value: object,
    environment_values: dict[str, str] | None = None,
) -> object:
    """Return the table-only representation for a row value."""
    if not isinstance(value, str):
        return value
    if os.sep not in value:
        return value
    return display_path_value(value, environment_values)


def display_table_rows(
    rows: list[dict[str, str]],
    environment_values: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    """Return table rows with visual-only path abbreviations applied."""
    return [
        {
            name: display_table_value(value, environment_values)
            for name, value in row.items()
        }
        for row in rows
    ]


def history_command_display_index(value: object) -> str:
    """Return the visible History Commands index value."""
    clean_value = str(value).strip()
    if not clean_value:
        return ""
    return f"!{clean_value}"


def history_index_column_width(rows: list[dict[str, str]]) -> int:
    """Return the pixel width for a history table Index column."""
    index_widths = [
        len(history_command_display_index(row.get("Index", ""))) for row in rows
    ]
    index_width = max([1, *index_widths])
    return max(
        hhs_ui_constants.HISTORY_INDEX_COLUMN_MIN_WIDTH,
        hhs_ui_constants.HISTORY_INDEX_COLUMN_PADDING
        + (index_width * hhs_ui_constants.HISTORY_INDEX_COLUMN_DIGIT_WIDTH),
    )


def history_command_column_config(rows: list[dict[str, str]]) -> dict[str, object]:
    """Return column settings for the History Commands table."""
    return {
        "_index": st.column_config.TextColumn(
            "",
            disabled=True,
            width=history_index_column_width(rows),
        ),
        "Value": st.column_config.TextColumn("Value", disabled=True),
    }


def history_command_table_data(rows: list[dict[str, str]]) -> pd.DataFrame:
    """Return History Commands table data with Index rendered as row labels."""
    dataframe = pd.DataFrame(display_table_rows(rows), columns=["Index", "Value"])
    dataframe["Index"] = [
        history_command_display_index(row.get("Index", "")) for row in rows
    ]
    dataframe = dataframe.set_index("Index")
    dataframe.index.name = ""
    return dataframe


def history_directory_column_config() -> dict[str, object]:
    """Return column settings for the History Directories table."""
    return {
        "_index": st.column_config.TextColumn(
            "",
            disabled=True,
            width=hhs_ui_constants.HISTORY_DIRECTORY_TYPE_COLUMN_WIDTH,
        ),
        "Value": st.column_config.TextColumn("Value", disabled=True),
    }


def history_directory_table_data(rows: list[dict[str, str]]) -> pd.DataFrame:
    """Return History Directories table data with Type rendered as row labels."""
    dataframe = pd.DataFrame(display_table_rows(rows), columns=["Type", "Value"])
    dataframe = dataframe.set_index("Type")
    dataframe.index.name = ""
    return dataframe


def cmd_column_config() -> dict[str, object]:
    """Return column settings for the Configs Saved Cmds table."""
    return {
        "Index": st.column_config.TextColumn(
            "Index",
            disabled=True,
            width=hhs_ui_constants.CMD_INDEX_COLUMN_WIDTH,
        ),
    }


def table_selection_key_prefixes() -> tuple[str, ...]:
    """Return Streamlit dataframe key prefixes that represent selectable tables."""
    return (
        hhs_ui.AI_MODEL_TABLE_KEY,
        hhs_ui.ALIAS_TABLE_KEY,
        hhs_ui.CMD_TABLE_KEY,
        hhs_ui.DIR_TABLE_KEY,
        hhs_ui.DOCKER_CONTAINER_TABLE_KEY,
        hhs_ui.DOCKER_IMAGE_TABLE_KEY,
        hhs_ui.ENV_TABLE_KEY,
        hhs_ui.HISTORY_COMMAND_TABLE_KEY,
        hhs_ui.HISTORY_DIRECTORY_TABLE_KEY,
        hhs_ui.HOME_SHOPTS_TABLE_KEY,
        hhs_ui.HOME_TOOLS_TABLE_KEY,
        hhs_ui.PATH_TABLE_KEY,
        hhs_ui.PROCESS_TABLE_KEY,
        hhs_ui.SERVICE_TABLE_KEY,
        hhs_ui.SSH_TUNNEL_TABLE_KEY,
    )


def table_selection_widget_key(key: object) -> bool:
    """Return whether a Streamlit session key belongs to a selectable dataframe."""
    key_text = str(key)
    return any(
        key_text == prefix or key_text.startswith(f"{prefix}_")
        for prefix in table_selection_key_prefixes()
    )


def table_selection_rows(selection_state: object) -> tuple[int, ...]:
    """Return selected row indexes from a Streamlit dataframe selection state."""
    selection = getattr(selection_state, "selection", None)
    if selection is None and isinstance(selection_state, dict):
        selection = selection_state.get("selection", selection_state)
    rows = getattr(selection, "rows", None)
    if rows is None and isinstance(selection, dict):
        rows = selection.get("rows")
    if rows is None:
        return ()
    return tuple(int(row) for row in rows)


def table_selection_snapshots() -> dict[str, tuple[int, ...]]:
    """Return remembered dataframe selections keyed by Streamlit widget key."""
    snapshots = st.session_state.setdefault(
        hhs_ui_constants.TABLE_SELECTION_SNAPSHOT_KEY, {}
    )
    if not isinstance(snapshots, dict):
        snapshots = {}
        st.session_state[hhs_ui_constants.TABLE_SELECTION_SNAPSHOT_KEY] = snapshots
    return snapshots


def table_selection_rerun_in_progress() -> bool:
    """Return whether the current rerun was caused by a table row selection."""
    snapshots = table_selection_snapshots()
    for key in st.session_state:
        if not table_selection_widget_key(key):
            continue
        rows = table_selection_rows(st.session_state.get(key))
        previous_rows = tuple(snapshots.get(str(key), ()))
        if rows != previous_rows:
            return True
    return False


def remember_table_selection(key: str | None, selection_state: object) -> None:
    """Remember the latest dataframe selection after a table render."""
    if key is None:
        return
    snapshots = table_selection_snapshots()
    snapshots[str(key)] = table_selection_rows(selection_state)


def scroll_to_table_selection_content(anchor_key: str) -> None:
    """Scroll the browser viewport to the bottom of a selected table row component."""
    selector = f'div[class*="st-key-{anchor_key}"]'
    st.html(
        f"""<span class="hhs-script-only" aria-hidden="true"></span>
        <script>
          (() => {{
            const table_selection_selector = {selector!r};
            const scroll_to_table_selection = () => {{
              const doc = window.parent.document;
              const target = doc.querySelector(table_selection_selector);
              if (!target) {{
                return;
              }}
              target.scrollIntoView({{
                behavior: "smooth",
                block: "end",
                inline: "nearest"
              }});
            }};
            window.setTimeout(scroll_to_table_selection, 75);
            window.setTimeout(scroll_to_table_selection, 250);
          }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def render_table(
    rows: list[dict[str, str]],
    key: str | None,
    empty_hint: str = "Select a row to interact",
    action_hint: str = "",
    headers: list[str] | None = None,
    checkbox: bool = True,
    height: int | None = None,
    width: str | None = None,
    hide_index: bool = True,
    table_data: object | None = None,
    row_style: Callable[[pd.Series], list[str]] | None = None,
    selected_label: Callable[[dict[str, str], int], str] | None = None,
    selected_editable: bool | Callable[[dict[str, str], int], bool] = False,
    selected_edit_key: Callable[[dict[str, str], int], str] | str | None = None,
    selected_edit_value: Callable[[dict[str, str], int], str] | str | None = None,
    selected_edit_label: str = "Selected value",
    selected_edit_height: int = hhs_ui.ENV_VALUE_EDITOR_HEIGHT,
    selected_edit_max_chars: int | None = None,
    selected_edit_on_change: Callable[..., None] | None = None,
    selected_edit_args: (
        Callable[[dict[str, str], int], tuple[object, ...]] | tuple[object, ...] | None
    ) = None,
    selected_edit_folder_picker: bool = False,
    folder_picker_callback: Callable[[str, str], None] | None = None,
    reset_selection: Callable[[], None] | None = None,
    selected_action_buttons: list[dict[str, object]] | None = None,
    action_buttons: list[dict[str, object]] | None = None,
    action_column_weights: list[float] | None = None,
    on_select: Callable[[], None] | str = "rerun",
    column_config: dict[str, object] | None = None,
    translate_paths: bool = True,
) -> tuple[int | None, dict[str, str] | None]:
    """Render a reusable HomeSetup table and return the selected row."""
    display_rows = display_table_rows(rows) if translate_paths else rows
    rendered_data = table_data if table_data is not None else display_rows
    if row_style is not None:
        rendered_data = pd.DataFrame(display_rows).style.apply(row_style, axis=1)

    dataframe_args: dict[str, object] = {"hide_index": hide_index}
    if key is not None:
        dataframe_args["key"] = key
    if headers is not None:
        dataframe_args["column_order"] = headers
    if column_config is not None:
        dataframe_args["column_config"] = column_config
    if height is not None:
        dataframe_args["height"] = table_height(height)
    if width is not None:
        dataframe_args["width"] = width
    else:
        dataframe_args["width"] = "stretch"
    if checkbox:
        dataframe_args["on_select"] = on_select
        dataframe_args["selection_mode"] = "single-row"

    selection = st.dataframe(rendered_data, **dataframe_args)
    if checkbox:
        remember_table_selection(key, selection)
    if not checkbox:
        return None, None

    selected_rows = selection.selection.rows if selection else []
    if not selected_rows or selected_rows[0] >= len(rows):
        if empty_hint:
            with st.container(key=table_component_key(key, "table_empty_hint")):
                st.caption(empty_hint)
        return None, None

    selected_index = selected_rows[0]
    selected_row = rows[selected_index]
    visible_selected_actions = selected_table_actions(
        selected_action_buttons or [], selected_row, selected_index, reset_selection
    )
    if action_hint:
        with st.container(
            key=table_component_key(key, f"table_action_hint_{selected_index}")
        ):
            st.caption(action_hint)
    if selected_label is not None:
        label = selected_label(selected_row, selected_index)
        selected_item_label, selected_item_value = selected_label_parts(label)
        with st.container(
            key=table_component_key(key, f"table_selected_panel_{selected_index}")
        ):
            render_selected_table_item(
                selected_item_label,
                selected_item_value,
                selected_index,
                key,
                table_editable_flag(selected_editable, selected_row, selected_index),
                edit_key=(
                    table_edit_key(selected_edit_key, selected_row, selected_index)
                    if selected_edit_key is not None
                    else None
                ),
                edit_value=table_edit_value(
                    selected_edit_value, selected_row, selected_index
                ),
                edit_label=selected_edit_label,
                edit_height=selected_edit_height,
                edit_max_chars=selected_edit_max_chars,
                edit_on_change=selected_edit_on_change,
                edit_args=table_edit_args(
                    selected_edit_args, selected_row, selected_index
                ),
                edit_folder_picker=selected_edit_folder_picker,
                folder_picker_callback=folder_picker_callback,
                reset_selection=reset_selection,
                selected_actions=visible_selected_actions,
            )

    visible_actions = [
        action
        for action in action_buttons or []
        if table_action_visible(action, selected_row, selected_index)
    ]
    if visible_actions:
        with st.container(
            key=table_component_key(key, f"table_actions_{selected_index}")
        ):
            weights = action_column_weights or [1.0] * len(visible_actions)
            columns = st.columns(weights)
            for column, action in zip(columns, visible_actions):
                label = str(action["label"])
                key_prefix = str(
                    action.get("key_prefix", label.lower().replace(" ", "_"))
                )
                with column:
                    st.button(
                        label,
                        disabled=table_action_disabled(
                            action, selected_row, selected_index
                        ),
                        help=action.get("help"),
                        key=f"{key_prefix}_{selected_index}",
                        on_click=action.get("on_click"),
                        args=table_action_args(action, selected_row, selected_index),
                        width=str(action.get("width", "stretch")),
                    )

    anchor_key = table_component_key(key, f"table_selected_bottom_{selected_index}")
    with st.container(key=anchor_key):
        st.markdown(
            '<span class="hhs-table-selected-bottom-anchor"></span>',
            unsafe_allow_html=True,
        )
    scroll_to_table_selection_content(anchor_key)
    return selected_index, selected_row


def selected_table_actions(
    actions: list[dict[str, object]],
    row: dict[str, str],
    index: int,
    reset_selection: Callable[[], None] | None = None,
) -> list[dict[str, object]]:
    """Return selected-row table actions with row-specific values resolved."""
    resolved_actions = []
    for action in actions:
        if not table_action_visible(action, row, index):
            continue
        resolved_action = {
            **action,
            "disabled": table_action_disabled(action, row, index),
            "args": table_action_args(action, row, index),
            "reset_selection": reset_selection,
        }
        resolved_actions.append(resolved_action)
    return resolved_actions


def table_height(height: int) -> int:
    """Return the app table height after applying the global viewport reduction."""
    return max(1, height - hhs_ui.TABLE_HEIGHT_REDUCTION)


def bar_chart_height(height: int = hhs_ui.BAR_CHART_HEIGHT) -> int:
    """Return the app bar chart height after applying the global viewport reduction."""
    return max(1, height - hhs_ui.BAR_CHART_HEIGHT_REDUCTION)


def render_bar_chart(
    rows: list[dict[str, object]],
    x: alt.X,
    y: alt.Y,
    tooltip: list[alt.Tooltip],
    color: str = "#ffb86c",
    height: int = hhs_ui.BAR_CHART_HEIGHT,
) -> None:
    """Render a reusable responsive bar chart with app-wide sizing."""
    fallback_height = bar_chart_height(height)
    chart = (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(color=color)
        .encode(
            x=x,
            y=y,
            tooltip=tooltip,
        )
        .properties(height=fallback_height)
        .configure_view(continuousHeight=fallback_height)
    )
    st.altair_chart(chart, width="stretch", height=fallback_height)


def render_chart_control_label(label: str) -> None:
    """Render a normalized inline label for chart control rows."""
    clean_label = str(label or "").strip()
    if clean_label and not clean_label.endswith(":"):
        clean_label = f"{clean_label}:"
    st.markdown(
        f'<span class="hhs-inline-form-label">{html.escape(clean_label)}</span>',
        unsafe_allow_html=True,
    )


def render_chart_refresh_button(
    key: str,
    on_click: Callable[..., None] | None = None,
    args: tuple[object, ...] = (),
) -> bool:
    """Render the standard chart refresh glyph button and return click state."""
    button_kwargs: dict[str, object] = {
        "key": key,
        "help": "Refresh",
        "width": "stretch",
    }
    if on_click is not None:
        button_kwargs["on_click"] = on_click
        button_kwargs["args"] = args
    return bool(st.button("", **button_kwargs))


def render_standard_number_spinner(label: str, **input_kwargs: object) -> int:
    """Render the standard compact number spinner used by chart controls."""
    help_text = str(input_kwargs.pop("help", f"Set {label.rstrip(':').lower()}."))
    return int(st.number_input(label, help=help_text, **input_kwargs))


def render_chart_top_n_input(
    key: str,
    on_change: Callable[..., None] | None = None,
    args: tuple[object, ...] = (),
) -> None:
    """Render the standard 150px Top N chart number input."""
    input_kwargs: dict[str, object] = {
        "min_value": hhs_ui_constants.MIN_TOP_N,
        "max_value": hhs_ui_constants.MAX_TOP_N,
        "step": 1,
        "key": key,
        "label_visibility": "collapsed",
        "help": "Set the number of items shown in the chart.",
        "width": 150,
    }
    if on_change is not None:
        input_kwargs["on_change"] = on_change
        input_kwargs["args"] = args
    render_standard_number_spinner("Top N", **input_kwargs)


def render_chart_text_input(
    key: str,
    label: str,
    on_change: Callable[..., None] | None = None,
    args: tuple[object, ...] = (),
) -> None:
    """Render a chart text input using the shared row distribution."""
    input_kwargs: dict[str, object] = {
        "key": key,
        "label_visibility": "collapsed",
    }
    if on_change is not None:
        input_kwargs["on_change"] = on_change
        input_kwargs["args"] = args
    help_text = str(input_kwargs.pop("help", f"Enter {label.rstrip(':').lower()}."))
    st.text_input(label, help=help_text, **input_kwargs)


def render_chart_controls(
    key: str,
    *,
    has_top_n: bool = True,
    top_n_key: str | None = None,
    top_n_label: str = "Top N:",
    top_n_on_change: Callable[..., None] | None = None,
    top_n_args: tuple[object, ...] = (),
    has_input: bool = False,
    input_key: str | None = None,
    input_label: str | None = None,
    input_on_change: Callable[..., None] | None = None,
    input_args: tuple[object, ...] = (),
    has_refresh_btn: bool = True,
    refresh_key: str | None = None,
    refresh_on_click: Callable[..., None] | None = None,
    refresh_args: tuple[object, ...] = (),
) -> bool:
    """Render the standard chart controls expander and return refresh clicks."""
    if has_top_n and not top_n_key:
        raise ValueError("top_n_key is required when has_top_n is true")
    if has_input and (not input_key or not input_label):
        raise ValueError(
            "input_key and input_label are required when has_input is true"
        )
    if has_refresh_btn and not refresh_key:
        raise ValueError("refresh_key is required when has_refresh_btn is true")

    refresh_clicked = False
    with st.container(key=key):
        with st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True):
            if has_top_n and has_input:
                (
                    top_label_col,
                    top_input_col,
                    input_label_col,
                    input_col,
                    action_col,
                ) = st.columns(
                    [0.55, 0.75, 0.85, 3.0, 0.45],
                    gap="small",
                    vertical_alignment="center",
                )
                with top_label_col:
                    render_chart_control_label(top_n_label)
                with top_input_col:
                    render_chart_top_n_input(
                        str(top_n_key), top_n_on_change, top_n_args
                    )
                with input_label_col:
                    render_chart_control_label(str(input_label))
                with input_col:
                    render_chart_text_input(
                        str(input_key),
                        str(input_label).rstrip(":"),
                        input_on_change,
                        input_args,
                    )
                if has_refresh_btn:
                    with action_col:
                        refresh_clicked = render_chart_refresh_button(
                            str(refresh_key), refresh_on_click, refresh_args
                        )
            elif has_top_n:
                top_label_col, top_input_col, _spacer_col, action_col = st.columns(
                    [0.55, 0.75, 3.0, 0.45],
                    gap="small",
                    vertical_alignment="center",
                )
                with top_label_col:
                    render_chart_control_label(top_n_label)
                with top_input_col:
                    render_chart_top_n_input(
                        str(top_n_key), top_n_on_change, top_n_args
                    )
                if has_refresh_btn:
                    with action_col:
                        refresh_clicked = render_chart_refresh_button(
                            str(refresh_key), refresh_on_click, refresh_args
                        )
            elif has_input:
                input_label_col, input_col, action_col = st.columns(
                    [0.85, 4.0, 0.45],
                    gap="small",
                    vertical_alignment="center",
                )
                with input_label_col:
                    render_chart_control_label(str(input_label))
                with input_col:
                    render_chart_text_input(
                        str(input_key),
                        str(input_label).rstrip(":"),
                        input_on_change,
                        input_args,
                    )
                if has_refresh_btn:
                    with action_col:
                        refresh_clicked = render_chart_refresh_button(
                            str(refresh_key), refresh_on_click, refresh_args
                        )
    return refresh_clicked


def plot_chart(
    data: list[dict[str, object]],
    type: Literal["HBars", "VBars", "Pie"],
    title: str,
    has_top_n: bool = True,
    top_n_label: str = "Top N:",
    has_input: bool = False,
    input_label: str | None = None,
    has_refresh_btn: bool = True,
    *,
    x: alt.X | None = None,
    y: alt.Y | None = None,
    tooltip: list[alt.Tooltip] | None = None,
    color: str = "#ffb86c",
    height: int = hhs_ui.BAR_CHART_HEIGHT,
    title_is_html: bool = False,
) -> None:
    """Render a titled chart using the shared HomeSetup chart component style."""
    render_view_subtitle(title, content_is_html=title_is_html)
    if type in {"HBars", "VBars"}:
        if x is None or y is None:
            raise ValueError("x and y encodings are required for bar charts")
        render_bar_chart(
            data,
            x=x,
            y=y,
            tooltip=tooltip or [],
            color=color,
            height=height,
        )
        return
    if type == "Pie":
        fallback_height = bar_chart_height(height)
        chart = (
            alt.Chart(alt.Data(values=data))
            .mark_arc()
            .encode(
                theta=alt.Theta("Value:Q"),
                color=alt.Color("Label:N"),
                tooltip=tooltip or [],
            )
            .properties(height=fallback_height)
            .configure_view(continuousHeight=fallback_height)
        )
        st.altair_chart(chart, width="stretch", height=fallback_height)
        return
    raise ValueError(f"Unsupported chart type: {type}")


def table_action_visible(
    action: dict[str, object], row: dict[str, str], index: int
) -> bool:
    """Return whether a renderTable action button should be visible."""
    visible = action.get("visible", True)
    return bool(visible(row, index) if callable(visible) else visible)


def table_action_disabled(
    action: dict[str, object], row: dict[str, str], index: int
) -> bool:
    """Return whether a renderTable action button should be disabled."""
    disabled = action.get("disabled", False)
    return bool(disabled(row, index) if callable(disabled) else disabled)


def table_action_args(
    action: dict[str, object], row: dict[str, str], index: int
) -> tuple[object, ...]:
    """Return callback arguments for a renderTable action button."""
    args = action.get("args", ())
    if callable(args):
        args = args(row, index)
    return tuple(args) if isinstance(args, tuple | list) else (args,)


def render_table_controls_panel(
    render_controls: Callable[[], TableControlsResult],
) -> TableControlsResult:
    """Render table filters and entry controls inside the shared foldable panel."""
    with st.expander(hhs_ui.TABLE_CONTROLS_PANEL_TITLE, expanded=True):
        return render_controls()


def clear_table_other_filter(other_key: str) -> None:
    """Clear a typed table text filter and persist the updated UI state."""
    st.session_state[other_key] = ""
    save_ui_state()


def clean_table_text_filter_value(value: object) -> str:
    """Return a safe string value for a typed table text filter."""
    if value is None:
        return ""
    return str(value)


def normalize_table_text_filter_state(other_key: str) -> str:
    """Normalize one typed table text filter key before its widget is rendered."""
    clean_value = clean_table_text_filter_value(st.session_state.get(other_key, ""))
    if st.session_state.get(other_key) != clean_value:
        st.session_state[other_key] = clean_value
    return clean_value


def normalize_persisted_table_text_filter_states(*other_keys: str) -> None:
    """Normalize persisted typed table filter values before widgets are rendered."""
    for other_key in other_keys:
        clean_value = clean_table_text_filter_value(st.session_state.get(other_key, ""))
        if clean_value == "None":
            clean_value = ""
        st.session_state[other_key] = clean_value


def render_table_filter_controls(
    options: tuple[str, ...],
    key: str,
    other_key: str,
    columns: list[float],
    index: int = 0,
    other_options: tuple[str, ...] = ("Other", "Others", "Containing"),
    placeholder: str = "Type filter text",
) -> tuple[str, str]:
    """Render normalized table filter controls and return the selected filter text."""
    if key not in st.session_state or st.session_state.get(key) not in options:
        safe_index = max(0, min(index, len(options) - 1))
        st.session_state[key] = options[safe_index] if options else ""
    filter_col, other_filter_col, clear_filter_col = st.columns(
        [*columns, 0.18], vertical_alignment="center", gap="small"
    )
    with filter_col:
        selected_filter = st.radio(
            "Table filter",
            options,
            horizontal=True,
            index=None,
            key=key,
            label_visibility="collapsed",
            help="Filter the table rows.",
            on_change=save_ui_state,
        )

    other_filter = ""
    if selected_filter in other_options:
        normalize_table_text_filter_state(other_key)
        with other_filter_col:
            other_filter = st.text_input(
                "Filters",
                key=other_key,
                label_visibility="collapsed",
                on_change=save_ui_state,
                placeholder=placeholder,
                help="Filter the table rows by text.",
            )
        with clear_filter_col:
            st.button(
                "",
                key=f"{other_key}_clear",
                help="Clear filter text",
                on_click=clear_table_other_filter,
                args=(other_key,),
                disabled=not bool(clean_table_text_filter_value(other_filter)),
                width="content",
            )
    return selected_filter, clean_table_text_filter_value(other_filter)


def normalized_table_filter_selection(
    value: object, options: tuple[str, ...], default: str = "All"
) -> str:
    """Return a valid table filter selection while migrating legacy text labels."""
    if value is None:
        return default
    selected_value = str(value or "").strip()
    if not selected_value or selected_value == "None":
        return default
    if selected_value in {"Other", "Others"} and "Containing" in options:
        selected_value = "Containing"
    if selected_value not in options:
        return default
    return selected_value


def table_filter_mapping(options: tuple[str, ...]) -> dict[str, str | None]:
    """Return Config filter labels mapped to their returned filter values."""
    return {option: None for option in options}


def config_filter_columns(filters: dict[str, str | None]) -> list[float]:
    """Return Config filter column weights based on the number of filter options."""
    filter_count = len(filters)
    if filter_count >= 5:
        return hhs_ui.PATH_FILTER_COLUMNS
    if filter_count == 4:
        return hhs_ui.FOUR_OPTION_FILTER_COLUMNS
    if filter_count >= 3:
        return hhs_ui.THREE_OPTION_FILTER_COLUMNS
    return hhs_ui.TWO_OPTION_FILTER_COLUMNS


def config_filter_display_label(
    filters: dict[str, str | None],
    selected_value: object,
    default_label: str,
) -> str:
    """Return the display label that matches a persisted Config filter value."""
    selected_text = str(selected_value or "").strip()
    if selected_text in filters:
        return selected_text
    for label, filter_value in filters.items():
        if filter_value is not None and str(filter_value) == selected_text:
            return label
    return default_label


def config_filter_return_value(
    filters: dict[str, str | None],
    selected_label: str,
) -> str:
    """Return the semantic filter value for a selected Config filter label."""
    filter_value = filters.get(selected_label)
    return selected_label if filter_value is None else str(filter_value)


def render_view_subtitle(content: str, content_is_html: bool = False) -> None:
    """Render a normalized secondary page heading."""
    safe_content = content if content_is_html else html.escape(content)
    st.markdown(
        f'<h3 class="hhs-view-subtitle">{safe_content}</h3>',
        unsafe_allow_html=True,
    )


def path_origin_cell_style(value: object) -> str:
    """Return the dataframe cell style for PATH origin labels."""
    origin = str(value).strip().lower()
    if origin.startswith("custom path"):
        return "color: #8be9fd;"
    if origin.startswith("private system path"):
        return "color: #ff79c6;"
    return ""


def path_type_style_value(row: dict[str, str]) -> str:
    """Return the PATH Type value with status metadata for styling."""
    return f"{row.get('_Path Status', '')}{row.get('Type', '')}"


def path_type_display_value(value: object) -> str:
    """Return the visible PATH Type value without status metadata."""
    return re.sub(r"^[]", "", str(value), count=1)


def path_type_cell_style(value: object) -> str:
    """Return the dataframe cell style for PATH type values."""
    path_type = str(value)
    if "" in path_type:
        return "color: #ffb86c;"
    if "" in path_type:
        return "color: #50fa7b;"
    return ""


def path_column_config() -> dict[str, object]:
    """Return column settings for the Configs Paths table."""
    return {
        "Type": st.column_config.TextColumn(
            "Type",
            disabled=True,
            width=hhs_ui_constants.PATH_TYPE_COLUMN_WIDTH,
        ),
        "Origin": st.column_config.TextColumn("Origin", disabled=True),
        "Path Value": st.column_config.TextColumn("Path Value", disabled=True),
    }


def styled_path_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return PATH rows with styled Type and Origin cells."""
    visible_rows = display_table_rows(rows)
    for index, row in enumerate(visible_rows):
        if index < len(rows):
            row["Type"] = path_type_style_value(rows[index])
    dataframe = pd.DataFrame(
        visible_rows,
        columns=["Type", "Origin", "Path Value"],
    )
    styler = dataframe.style
    if "Type" in dataframe:
        styler = styler.map(path_type_cell_style, subset=["Type"])
        styler = styler.format(path_type_display_value, subset=["Type"])
    if "Origin" in dataframe:
        styler = styler.map(path_origin_cell_style, subset=["Origin"])
    return styler


def render_read_only_rows(
    rows: list[dict[str, str]],
    table_key: str,
    empty_caption: str = "Select a row to interact",
    selected_value: Callable[[dict[str, str], int], str] | None = None,
    headers: list[str] | None = None,
    hide_index: bool = True,
    table_data: object | None = None,
    column_config: dict[str, object] | None = None,
) -> None:
    """Render selectable read-only configuration rows."""
    render_table(
        rows,
        key=table_key,
        empty_hint=empty_caption,
        headers=headers,
        height=hhs_ui.ENV_TABLE_HEIGHT,
        hide_index=hide_index,
        table_data=table_data,
        width=hhs_ui.ENV_TABLE_WIDTH,
        column_config=column_config,
        selected_label=lambda row, _index: (
            "Selected: "
            + (
                selected_value(row, _index)
                if selected_value is not None
                else row.get("Name") or row.get("Index") or row.get("Value", "")
            )
        ),
    )


def service_name_cell_style(_: object) -> str:
    """Return the dataframe cell style for service names."""
    return (
        "background-color: #21222c;"
        "border-radius: 3px;"
        "color: #8be9fd;"
        "font-weight: 800;"
    )


def service_value_cell_style(value: object) -> str:
    """Return the dataframe cell style for service status values."""
    value_text = str(value).lower()
    base_style = "background-color: #21222c; border-radius: 3px; font-weight: 800;"
    if "up" in value_text:
        return f"{base_style} color: #50fa7b;"
    if "down" in value_text:
        return f"{base_style} color: #ff5555;"
    return f"{base_style} color: #f8f8f2;"


def styled_service_rows(rows: list[dict[str, str]]) -> pd.io.formats.style.Styler:
    """Return service rows with styled Name and Value cells."""
    dataframe = pd.DataFrame(rows)
    styler = dataframe.style
    if "Name" in dataframe:
        styler = styler.map(service_name_cell_style, subset=["Name"])
    if "Value" in dataframe:
        styler = styler.map(service_value_cell_style, subset=["Value"])
    return styler


def themed_markdown_table_data(
    table_data: pd.DataFrame,
    column_text_colors: dict[str, str] | None,
) -> object:
    """Return markdown table data with optional resolved themed text colors."""
    if not column_text_colors:
        return table_data
    theme_properties = theme_custom_properties(
        st.session_state.get(hhs_ui.THEME_SELECTED_KEY, "")
    )
    fallback_text_color = resolve_css_custom_property(
        theme_properties,
        "hhs-theme-text-color",
        "#f8f8f2",
    )
    styler = table_data.style
    for column_label, text_color in column_text_colors.items():
        if column_label not in table_data:
            continue
        resolved_text_color = resolve_css_value(
            theme_properties,
            text_color,
            fallback_text_color,
        )
        styler = styler.map(
            lambda _value, color=resolved_text_color: f"color: {color};",
            subset=[column_label],
        )
    return styler


def markdown_table_single_selected_index(
    selection_state: object,
    row_count: int,
) -> int | None:
    """Return the single selected markdown table row index."""
    selected_rows = table_selection_rows(selection_state)
    if selected_rows and 0 <= selected_rows[0] < row_count:
        return selected_rows[0]
    return None


def markdown_table_single_selection_marks(
    row_count: int,
    selected_index: int | None,
) -> list[str]:
    """Return radio-style mark glyphs for a singular markdown table."""
    return ["◉" if index == selected_index else "○" for index in range(row_count)]


def render_markdown_table(
    caption: str,
    headers: list[str],
    items: list[str],
    values: list[bool],
    key_prefix: str,
    value_keys: list[str] | None = None,
    disabled: bool = False,
    value_column_label: str = "Mark",
    variable_column_label: str = "Variable",
    item_column_label: str = "Setting",
    variable_values: list[str] | None = None,
    extra_columns: dict[str, list[str]] | None = None,
    min_row_count: int = 0,
    multi_selection: bool = True,
    column_text_colors: dict[str, str] | None = None,
    show_value_column: bool = True,
) -> list[bool]:
    """Render a reusable selectable markdown table and return selected values."""
    if len(items) != len(values) or len(items) != len(headers):
        raise ValueError("headers, items, and values must have the same length")
    if value_keys is not None and len(items) != len(value_keys):
        raise ValueError("items and value_keys must have the same length")
    if variable_values is not None and len(items) != len(variable_values):
        raise ValueError("items and variable_values must have the same length")
    if multi_selection and not show_value_column:
        raise ValueError("multi-selection tables require a visible value column")

    extra_columns = extra_columns or {}
    base_column_labels = {
        variable_column_label,
        item_column_label,
    }
    if show_value_column:
        base_column_labels.add(value_column_label)
    duplicate_column_labels = base_column_labels.intersection(extra_columns)
    if duplicate_column_labels:
        duplicate_labels = ", ".join(sorted(duplicate_column_labels))
        raise ValueError(f"extra columns duplicate base columns: {duplicate_labels}")
    for column_label, column_values in extra_columns.items():
        if len(items) != len(column_values):
            raise ValueError(
                f"items and extra column {column_label!r} must have the same length"
            )

    editor_key = (
        f"{key_prefix}_markdown_table_editor_v"
        f"{hhs_ui_constants.MARKDOWN_TABLE_LAYOUT_VERSION}"
    )
    selection_key = f"{editor_key}_single_selection"
    token_key = f"_{editor_key}_token"
    token = json.dumps(
        {
            "extra_columns": extra_columns,
            "headers": headers,
            "items": items,
            "multi_selection": multi_selection,
            "show_value_column": show_value_column,
            "values": values,
            "variable_values": variable_values,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    if st.session_state.get(token_key) != token:
        st.session_state.pop(editor_key, None)
        st.session_state.pop(selection_key, None)
        st.session_state[token_key] = token

    rendered_variable_values = (
        variable_values if variable_values is not None else [header.upper() for header in headers]
    )
    table_columns = {
        variable_column_label: rendered_variable_values,
        item_column_label: headers,
    }
    if show_value_column:
        table_columns[value_column_label] = [bool(value) for value in values]
    table_columns.update(extra_columns)
    extra_column_labels = list(extra_columns)
    column_config: dict[str, object] = {
        variable_column_label: st.column_config.TextColumn(
            variable_column_label,
            disabled=True,
        ),
        item_column_label: st.column_config.TextColumn(
            item_column_label,
            disabled=True,
        ),
    }
    if show_value_column:
        column_config[value_column_label] = st.column_config.CheckboxColumn(
            value_column_label,
            disabled=disabled,
            help="Select rows for the available actions.",
            width=hhs_ui_constants.MARKDOWN_TABLE_MARK_COLUMN_WIDTH,
        )
    for column_label in extra_column_labels:
        column_config[column_label] = st.column_config.TextColumn(
            column_label,
            disabled=True,
        )

    with st.container(key=f"{key_prefix}_markdown_table"):
        st.markdown(
            f'<div class="hhs-markdown-table-caption">{html.escape(caption)}</div>',
            unsafe_allow_html=True,
        )
        table_data_columns = {
        }
        if show_value_column:
            table_data_columns[value_column_label] = pd.Series(
                table_columns[value_column_label], dtype="bool"
            )
        for text_column_label in [
            variable_column_label,
            item_column_label,
            *extra_column_labels,
        ]:
            table_data_columns[text_column_label] = pd.Series(
                table_columns[text_column_label], dtype="string"
            )
        table_data = pd.DataFrame(table_data_columns)
        if multi_selection:
            edited_data = st.data_editor(
                themed_markdown_table_data(table_data, column_text_colors),
                key=editor_key,
                hide_index=True,
                num_rows="fixed",
                column_order=[
                    value_column_label,
                    item_column_label,
                    variable_column_label,
                    *extra_column_labels,
                ],
                height=markdown_table_editor_height(max(len(items), min_row_count)),
                disabled=(
                    [variable_column_label, item_column_label, *extra_column_labels]
                    if not disabled
                    else True
                ),
                column_config=column_config,
            )
            edited_values = [
                bool(value) for value in edited_data[value_column_label].tolist()
            ]
        else:
            st.markdown(
                '<span class="hhs-markdown-table-single-selection"></span>',
                unsafe_allow_html=True,
            )
            selected_index = markdown_table_single_selected_index(
                st.session_state.get(selection_key),
                len(items),
            )
            selection_table_data = table_data.copy()
            if show_value_column:
                selection_table_data[value_column_label] = pd.Series(
                    markdown_table_single_selection_marks(len(items), selected_index),
                    dtype="string",
                )
            selection_column_order = [
                item_column_label,
                variable_column_label,
                *extra_column_labels,
            ]
            if show_value_column:
                selection_column_order.insert(0, value_column_label)
            selection_column_config = {
                column_label: config
                for column_label, config in column_config.items()
                if column_label != value_column_label
            }
            if show_value_column:
                selection_column_config = {
                    value_column_label: st.column_config.TextColumn(
                        value_column_label,
                        disabled=True,
                        width=hhs_ui_constants.MARKDOWN_TABLE_MARK_COLUMN_WIDTH,
                    ),
                    **selection_column_config,
                }
            selection_args: dict[str, object] = {
                "key": selection_key,
                "hide_index": True,
                "column_order": selection_column_order,
                "height": markdown_table_editor_height(max(len(items), min_row_count)),
                "width": "stretch",
                "column_config": selection_column_config,
            }
            if not disabled:
                selection_args["on_select"] = "rerun"
                selection_args["selection_mode"] = "single-row"
            selection = st.dataframe(
                themed_markdown_table_data(selection_table_data, column_text_colors),
                **selection_args,
            )
            edited_values = [False] * len(items)
            if not disabled:
                selected_index = markdown_table_single_selected_index(
                    selection,
                    len(items),
                )
                if selected_index is not None:
                    edited_values[selected_index] = True
    if value_keys is not None:
        for value_key, value in zip(value_keys, edited_values, strict=True):
            st.session_state[value_key] = value
    return edited_values


def markdown_table_editor_height(row_count: int) -> int:
    """Return the fixed HHS markdown table editor height."""
    del row_count
    return hhs_ui_constants.MARKDOWN_TABLE_HEIGHT


def resolve_css_custom_property(
    properties: dict[str, str], property_name: str, fallback: str
) -> str:
    """Return a CSS custom property value with simple var references resolved."""
    value = properties.get(property_name, fallback).strip()
    visited = {property_name}
    while value.startswith("var(--") and value.endswith(")"):
        referenced_name = value[6:-1].strip()
        if "," in referenced_name:
            referenced_name, fallback_value = referenced_name.split(",", 1)
            fallback = fallback_value.strip()
        if referenced_name in visited:
            return fallback
        visited.add(referenced_name)
        value = properties.get(referenced_name, fallback).strip()
    return value or fallback


def resolve_css_value(
    properties: dict[str, str], css_value: str, fallback: str
) -> str:
    """Return a CSS value with a top-level custom property reference resolved."""
    clean_value = css_value.strip()
    if not clean_value.startswith("var(--") or not clean_value.endswith(")"):
        return clean_value or fallback
    referenced_name = clean_value[6:-1].strip()
    fallback_value = fallback
    if "," in referenced_name:
        referenced_name, fallback_value = referenced_name.split(",", 1)
        fallback_value = fallback_value.strip()
    referenced_name = referenced_name.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", referenced_name):
        return fallback
    resolved_value = resolve_css_custom_property(
        properties,
        referenced_name,
        fallback_value,
    ).strip()
    if resolved_value.startswith("var("):
        return fallback
    return resolved_value or fallback
