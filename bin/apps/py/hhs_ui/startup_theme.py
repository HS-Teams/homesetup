#!/usr/bin/env python3
"""Print Streamlit startup theme arguments for HomeSetup UI launchers."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
HHS_HOME = Path(os.environ.get("HHS_HOME", str(APP_DIR.parents[3]))).expanduser()
HHS_DIR = Path(os.environ.get("HHS_DIR", str(APP_DIR))).expanduser()
HHS_CACHE_DIR = Path(os.environ.get("HHS_CACHE_DIR", str(HHS_DIR / "cache"))).expanduser()
UI_STATE_FILE = HHS_CACHE_DIR / "streamlit-ui-state.json"
LEGACY_UI_STATE_FILE = HHS_CACHE_DIR / ".streamlit-ui-state"
THEMES_DIR = HHS_HOME / "bin/apps/py/hhs_ui/themes"
DEFAULT_THEME_NAME = "dracula"
THEME_SELECTED_KEY = "theme_selected"

THEME_OPTION_TOKENS = (
    ("theme.base", "hhs-theme-base"),
    ("theme.primaryColor", "hhs-theme-primary-color"),
    ("theme.backgroundColor", "hhs-theme-background-color"),
    ("theme.secondaryBackgroundColor", "hhs-theme-secondary-background-color"),
    ("theme.textColor", "hhs-theme-text-color"),
    ("theme.linkColor", "hhs-theme-link-color"),
    ("theme.borderColor", "hhs-theme-border-color"),
    ("theme.dataframeBorderColor", "hhs-theme-dataframe-border-color"),
    ("theme.dataframeHeaderBackgroundColor", "hhs-theme-dataframe-header-background-color"),
    ("theme.codeBackgroundColor", "hhs-theme-code-background-color"),
    ("theme.baseRadius", "hhs-theme-base-radius"),
    ("theme.buttonRadius", "hhs-theme-button-radius"),
    ("theme.showWidgetBorder", "hhs-theme-show-widget-border"),
    ("theme.showSidebarBorder", "hhs-theme-show-sidebar-border"),
)


def load_ui_state() -> dict[str, object]:
    """Return persisted UI state values from the HomeSetup cache file."""
    state_file = UI_STATE_FILE if UI_STATE_FILE.exists() else LEGACY_UI_STATE_FILE
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def available_theme_names() -> set[str]:
    """Return selectable theme names available to the HomeSetup UI."""
    try:
        return {theme_file.stem for theme_file in THEMES_DIR.glob("*.css")}
    except OSError:
        return set()


def selected_theme_name() -> str:
    """Return the persisted theme name or the default theme name."""
    selected_theme = str(load_ui_state().get(THEME_SELECTED_KEY, "")).strip()
    theme_names = available_theme_names()
    if selected_theme in theme_names:
        return selected_theme
    if DEFAULT_THEME_NAME in theme_names:
        return DEFAULT_THEME_NAME
    return sorted(theme_names)[0] if theme_names else DEFAULT_THEME_NAME


def css_custom_properties(css_source: str) -> dict[str, str]:
    """Return CSS custom properties parsed from a stylesheet."""
    return {
        property_name: property_value.strip()
        for property_name, property_value in re.findall(
            r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);", css_source
        )
    }


def resolve_css_value(value: str, properties: dict[str, str]) -> str:
    """Resolve simple CSS var() references in a custom property value."""
    resolved_value = value.strip()
    seen_properties: set[str] = set()
    while True:
        match = re.fullmatch(r"var\(\s*--([A-Za-z0-9_-]+)\s*\)", resolved_value)
        if not match:
            return resolved_value
        property_name = match.group(1)
        if property_name in seen_properties or property_name not in properties:
            return resolved_value
        seen_properties.add(property_name)
        resolved_value = properties[property_name].strip()


def valid_theme_option_value(option_name: str, value: str) -> bool:
    """Return whether a parsed CSS value is valid enough for Streamlit startup."""
    if not value or "var(" in value:
        return False
    if option_name == "theme.base":
        return value in {"light", "dark"}
    if option_name.startswith("theme.show"):
        return value.lower() in {"true", "false"}
    return True


def theme_config_options(theme_name: str) -> dict[str, str]:
    """Return Streamlit theme config options for a selected HomeSetup theme."""
    theme_file = THEMES_DIR / f"{theme_name}.css"
    try:
        properties = css_custom_properties(theme_file.read_text(encoding="utf-8"))
    except OSError:
        return {}
    options: dict[str, str] = {}
    for option_name, token_name in THEME_OPTION_TOKENS:
        if token_name not in properties:
            continue
        option_value = resolve_css_value(properties[token_name], properties)
        if valid_theme_option_value(option_name, option_value):
            options[option_name] = option_value
    return options


def streamlit_theme_args() -> list[str]:
    """Return Streamlit CLI arguments for the selected startup theme."""
    args: list[str] = []
    for option_name, option_value in theme_config_options(selected_theme_name()).items():
        args.extend((f"--{option_name}", option_value))
    return args


def main() -> int:
    """Print one Streamlit CLI theme argument per output line."""
    for argument in streamlit_theme_args():
        print(argument)
    return 0


if __name__ == "__main__":
    sys.exit(main())
