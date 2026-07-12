"""Static asset and theme helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import re
from base64 import b64encode
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from streamlit import config as st_config

from . import constants as hhs_ui_constants


def file_mtime_token(file_path: Path) -> float:
    """Return a cache token that changes when a filesystem asset changes."""
    try:
        return file_path.stat().st_mtime
    except OSError:
        return 0.0


@lru_cache(maxsize=128)
def cached_text_file(file_path: str, mtime_token: float) -> str:
    """Return a UTF-8 text file body cached by path and modification time."""
    del mtime_token
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return ""


def load_text_file(file_path: Path) -> str:
    """Load a UTF-8 text file through the static asset cache."""
    return cached_text_file(str(file_path), file_mtime_token(file_path))


@lru_cache(maxsize=64)
def cached_data_uri(file_path: str, mime_type: str, mtime_token: float) -> str:
    """Return a browser data URI cached by path, MIME type, and modification time."""
    del mtime_token
    try:
        encoded_data = b64encode(Path(file_path).read_bytes()).decode("ascii")
    except OSError:
        encoded_data = ""
    return f"data:{mime_type};base64,{encoded_data}"


def load_data_uri(file_path: Path, mime_type: str) -> str:
    """Load a binary file as a browser data URI through the static asset cache."""
    return cached_data_uri(str(file_path), mime_type, file_mtime_token(file_path))


def static_asset_url(file_path: Path) -> str:
    """Return a cache-busted Streamlit static-serving URL for an app asset."""
    try:
        relative_path = file_path.resolve().relative_to(
            hhs_ui_constants.APP_STATIC_DIR.resolve()
        )
        modified_token = file_path.stat().st_mtime_ns
    except (OSError, ValueError):
        return ""
    encoded_path = quote(relative_path.as_posix(), safe="/")
    return f"/app/static/{encoded_path}?v={modified_token}"


def load_app_css() -> str:
    """Load the HomeSetup Streamlit UI stylesheet."""
    return load_text_file(hhs_ui_constants.APP_CSS_FILE)


def available_theme_options() -> tuple[str, ...]:
    """Return all selectable theme names from the themes folder."""
    return tuple(
        sorted(
            theme.stem
            for theme in hhs_ui_constants.APP_THEME_CSS_FILE.parent.glob("*.css")
        )
    )


def default_theme_name(theme_options: tuple[str, ...] | None = None) -> str:
    """Return the default selectable HomeSetup UI theme name."""
    options = theme_options if theme_options is not None else available_theme_options()
    if hhs_ui_constants.APP_THEME_CSS_FILE.stem in options:
        return hhs_ui_constants.APP_THEME_CSS_FILE.stem
    return options[0] if options else ""


def validated_theme_name(
    theme_name: object, theme_options: tuple[str, ...] | None = None
) -> str:
    """Return a valid selectable theme name or an empty string."""
    selected_theme = str(theme_name or "").strip()
    options = theme_options if theme_options is not None else available_theme_options()
    return selected_theme if selected_theme in options else ""


def theme_css_file(theme_name: object) -> Path:
    """Return the stylesheet path for a selectable UI theme."""
    theme_options = available_theme_options()
    selected_theme = validated_theme_name(theme_name, theme_options)
    if not selected_theme:
        selected_theme = default_theme_name(theme_options)
    theme_file = hhs_ui_constants.APP_THEME_CSS_FILE.with_name(f"{selected_theme}.css")
    if not theme_file.is_file():
        return hhs_ui_constants.APP_THEME_CSS_FILE
    return theme_file


def css_custom_properties(css_source: str) -> dict[str, str]:
    """Return CSS custom property values from a stylesheet source string."""
    properties: dict[str, str] = {}
    for property_name, property_value in re.findall(
        r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);", css_source
    ):
        properties[property_name] = property_value.strip()
    return properties


@lru_cache(maxsize=32)
def cached_css_custom_properties(css_source: str) -> dict[str, str]:
    """Return parsed CSS custom properties cached by stylesheet source."""
    return css_custom_properties(css_source)


def theme_custom_properties(theme_name: object) -> dict[str, str]:
    """Return parsed CSS custom properties for a selectable UI theme."""
    return cached_css_custom_properties(load_text_file(theme_css_file(theme_name)))


def css_theme_bool(value: str) -> bool | str:
    """Return a boolean value for CSS boolean tokens or the original string."""
    normalized_value = value.strip().lower()
    if normalized_value == "true":
        return True
    if normalized_value == "false":
        return False
    return value


def theme_config_options(theme_name: object) -> dict[str, object]:
    """Return Streamlit native theme options parsed from a selectable CSS theme."""
    theme_properties = theme_custom_properties(theme_name)
    option_tokens = {
        "theme.base": "hhs-theme-base",
        "theme.primaryColor": "hhs-theme-primary-color",
        "theme.backgroundColor": "hhs-theme-background-color",
        "theme.secondaryBackgroundColor": "hhs-theme-secondary-background-color",
        "theme.textColor": "hhs-theme-text-color",
        "theme.linkColor": "hhs-theme-link-color",
        "theme.borderColor": "hhs-theme-border-color",
        "theme.dataframeBorderColor": "hhs-theme-dataframe-border-color",
        "theme.dataframeHeaderBackgroundColor": (
            "hhs-theme-dataframe-header-background-color"
        ),
        "theme.codeBackgroundColor": "hhs-theme-code-background-color",
        "theme.baseRadius": "hhs-theme-base-radius",
        "theme.buttonRadius": "hhs-theme-button-radius",
        "theme.showWidgetBorder": "hhs-theme-show-widget-border",
        "theme.showSidebarBorder": "hhs-theme-show-sidebar-border",
    }
    return {
        option_name: css_theme_bool(theme_properties[token_name])
        for option_name, token_name in option_tokens.items()
        if token_name in theme_properties
    }


def load_app_theme_css() -> str:
    """Load the selected HomeSetup Streamlit UI theme stylesheet."""
    selected_theme = st.session_state.get(hhs_ui_constants.THEME_SELECTED_KEY, "")
    return load_text_file(theme_css_file(selected_theme))


def app_font_url() -> str:
    """Return the browser-cacheable URL for the HomeSetup UI font."""
    return static_asset_url(hhs_ui_constants.APP_FONT_FILE)


def load_app_image_data_uri(image_file: Path, mime_type: str) -> str:
    """Load a HomeSetup UI image as a browser-embeddable data URI."""
    return load_data_uri(image_file, mime_type)


def load_app_font_face_css() -> str:
    """Return the HomeSetup UI font-face rule using its static asset URL."""
    return (
        "@font-face {"
        f'font-family: "{hhs_ui_constants.APP_FONT_FAMILY}";'
        f'src: url("{app_font_url()}") format("woff2");'
        "font-style: normal;"
        "font-weight: 400;"
        "font-display: swap;"
        "}"
    )


def configure_app_font_theme(theme_name: object = "") -> None:
    """Configure Streamlit's selected theme for native components."""
    for option_name, option_value in theme_config_options(theme_name).items():
        st_config.set_option(option_name, option_value)
    st_config.set_option(
        "theme.fontFaces",
        [
            {
                "family": hhs_ui_constants.APP_FONT_FAMILY,
                "url": app_font_url(),
                "weight": "400",
                "style": "normal",
            }
        ],
    )
    st_config.set_option("theme.font", hhs_ui_constants.APP_FONT_FAMILY)
    st_config.set_option("theme.headingFont", hhs_ui_constants.APP_FONT_FAMILY)
    st_config.set_option("theme.codeFont", hhs_ui_constants.APP_FONT_FAMILY)


def render_styles() -> None:
    """Render cacheable app-level Streamlit styles."""
    app_css_url = static_asset_url(hhs_ui_constants.APP_CSS_FILE)
    theme_css_url = static_asset_url(
        theme_css_file(st.session_state.get(hhs_ui_constants.THEME_SELECTED_KEY, ""))
    )
    st.markdown(
        (
            f'<link rel="stylesheet" href="{app_css_url}">'
            f'<link rel="stylesheet" href="{theme_css_url}">'
            f"<style>{load_app_font_face_css()}{hhs_ui_constants.APP_CSS}</style>"
        ),
        unsafe_allow_html=True,
    )


def format_datetime(value: datetime) -> str:
    """Format a datetime value for the HomeSetup UI."""
    return value.strftime(hhs_ui_constants.DISPLAY_DATETIME_FORMAT)
