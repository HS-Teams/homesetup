"""Session-state persistence for the HomeSetup Streamlit UI."""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from . import constants as hhs_ui_constants
from .theme_assets import default_theme_name, validated_theme_name


def is_persisted_ui_key(key: str) -> bool:
    """Return whether a Streamlit session key should be persisted."""
    if key.endswith("_button"):
        return False
    return key in hhs_ui_constants.PERSISTED_UI_KEYS or key.startswith(
        hhs_ui_constants.PERSISTED_UI_KEY_PREFIXES
    )


def is_persistable_ui_value(value: object) -> bool:
    """Return whether a Streamlit session value is safe for JSON UI persistence."""
    if isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, list):
        return all(
            isinstance(item, (str, bool, int, float))
            or (
                isinstance(item, dict)
                and all(
                    isinstance(key, str)
                    and isinstance(dict_value, (str, bool, int, float))
                    for key, dict_value in item.items()
                )
            )
            for item in value
        )
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and isinstance(item, (str, bool, int, float))
            for key, item in value.items()
        )
    return False


def load_ui_state() -> dict[str, object]:
    """Load persisted Streamlit UI selections from disk."""
    state_file = ui_state_source_file()
    if state_file is None:
        return {}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str)
        and is_persisted_ui_key(key)
        and is_persistable_ui_value(value)
    }


def ui_state_files() -> tuple[Path, ...]:
    """Return current and legacy UI state file paths."""
    return (hhs_ui_constants.UI_STATE_FILE, *legacy_ui_state_files())


def legacy_ui_state_files() -> tuple[Path, ...]:
    """Return legacy hidden UI state file paths."""
    return (hhs_ui_constants.HHS_CACHE_DIR / ".streamlit-ui-state",)


def unlink_legacy_ui_state_files() -> None:
    """Remove legacy hidden UI state files after writing the visible state file."""
    for state_file in legacy_ui_state_files():
        try:
            state_file.unlink(missing_ok=True)
        except OSError:
            continue


def ui_state_source_file() -> Path | None:
    """Return the first existing current or legacy UI state file path."""
    for state_file in ui_state_files():
        if state_file.exists():
            return state_file
    return None


def persisted_theme_name() -> str:
    """Return the valid persisted UI theme or the default theme."""
    selected_theme = validated_theme_name(
        load_ui_state().get(hhs_ui_constants.THEME_SELECTED_KEY, "")
    )
    if selected_theme:
        return selected_theme
    return default_theme_name()


def restore_persisted_theme_selection() -> str:
    """Restore the persisted UI theme into Streamlit session state."""
    selected_theme = validated_theme_name(
        st.session_state.get(hhs_ui_constants.THEME_SELECTED_KEY, "")
    )
    if not selected_theme:
        selected_theme = validated_theme_name(
            load_ui_state().get(hhs_ui_constants.THEME_SELECTED_KEY, "")
        )
    if not selected_theme:
        selected_theme = default_theme_name()
    st.session_state[hhs_ui_constants.THEME_SELECTED_KEY] = selected_theme
    return selected_theme


def export_env_value_overrides(overrides: object) -> None:
    """Export persisted environment value overrides to the Streamlit process."""
    if not isinstance(overrides, dict):
        return
    for key, value in overrides.items():
        if isinstance(key, str) and isinstance(value, str):
            os.environ[key] = value


def restore_ui_state() -> None:
    """Restore persisted UI selections into Streamlit session state."""
    if st.session_state.get("ui_state_restored"):
        return
    for key, value in load_ui_state().items():
        st.session_state[key] = value
    restore_persisted_theme_selection()
    export_env_value_overrides(
        st.session_state.get(hhs_ui_constants.ENV_VALUE_OVERRIDES_KEY)
    )
    st.session_state["ui_state_restored"] = True


def save_ui_state() -> None:
    """Persist selected Streamlit UI values to disk."""
    current_state = load_ui_state()
    persisted_theme = validated_theme_name(
        current_state.get(hhs_ui_constants.THEME_SELECTED_KEY, "")
    )
    data = {
        key: st.session_state[key]
        for key in sorted(st.session_state)
        if is_persisted_ui_key(key)
        and is_persistable_ui_value(st.session_state.get(key))
    }
    selected_theme = validated_theme_name(
        data.get(hhs_ui_constants.THEME_SELECTED_KEY, "")
    )
    if selected_theme:
        data[hhs_ui_constants.THEME_SELECTED_KEY] = selected_theme
    elif persisted_theme:
        data[hhs_ui_constants.THEME_SELECTED_KEY] = persisted_theme
    else:
        data.pop(hhs_ui_constants.THEME_SELECTED_KEY, None)
    if data == current_state:
        return
    hhs_ui_constants.UI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    hhs_ui_constants.UI_STATE_FILE.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )
    unlink_legacy_ui_state_files()
