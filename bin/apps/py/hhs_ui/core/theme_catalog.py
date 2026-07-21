"""Theme catalog discovery, naming, and path resolution helpers."""

from __future__ import annotations

from pathlib import Path

THEME_VARIANTS = ("dark", "light")
THEME_LABEL_OVERRIDES = {"homesetup": "HomeSetup"}


def theme_option_from_path(theme_file: Path, themes_dir: Path) -> str:
    """Return a folder-qualified theme option for a stylesheet path."""
    try:
        relative_theme = theme_file.relative_to(themes_dir)
    except ValueError:
        return ""
    if relative_theme.parent.name not in THEME_VARIANTS:
        return ""
    return relative_theme.with_suffix("").as_posix()


def discover_theme_options(themes_dir: Path) -> tuple[str, ...]:
    """Return paired dark and light theme options sorted by palette name."""
    theme_files = (
        theme_file
        for variant in THEME_VARIANTS
        for theme_file in (themes_dir / variant).glob("*.css")
        if theme_file.is_file()
    )
    sorted_files = sorted(
        theme_files,
        key=lambda theme_file: (
            theme_file.stem.casefold(),
            THEME_VARIANTS.index(theme_file.parent.name),
        ),
    )
    return tuple(
        theme_option
        for theme_file in sorted_files
        if (theme_option := theme_option_from_path(theme_file, themes_dir))
    )


def normalize_theme_option(theme_name: object, theme_options: tuple[str, ...]) -> str:
    """Return a canonical theme option, including legacy-name migrations."""
    selected_theme = str(theme_name or "").strip()
    if selected_theme in theme_options:
        return selected_theme
    if not selected_theme or "/" in selected_theme:
        return ""
    if selected_theme.endswith("-light"):
        migrated_theme = f"light/{selected_theme.removesuffix('-light')}"
    else:
        migrated_theme = f"dark/{selected_theme}"
    return migrated_theme if migrated_theme in theme_options else ""


def default_theme_option(
    default_theme_file: Path,
    themes_dir: Path,
    theme_options: tuple[str, ...],
) -> str:
    """Return the configured default theme option or the first available option."""
    default_theme = theme_option_from_path(default_theme_file, themes_dir)
    if default_theme in theme_options:
        return default_theme
    return theme_options[0] if theme_options else ""


def resolve_theme_file(
    theme_name: object,
    themes_dir: Path,
    default_theme_file: Path,
) -> Path:
    """Return the stylesheet path for a selectable theme option."""
    theme_options = discover_theme_options(themes_dir)
    selected_theme = normalize_theme_option(theme_name, theme_options)
    if not selected_theme:
        selected_theme = default_theme_option(
            default_theme_file,
            themes_dir,
            theme_options,
        )
    theme_file = themes_dir / f"{selected_theme}.css"
    return theme_file if theme_file.is_file() else default_theme_file


def theme_option_label(theme_option: object) -> str:
    """Return a readable palette-and-variant label for a theme option."""
    normalized_option = str(theme_option or "").strip()
    variant, separator, palette = normalized_option.partition("/")
    if not separator or variant not in THEME_VARIANTS or not palette:
        return normalized_option
    palette_label = THEME_LABEL_OVERRIDES.get(
        palette,
        palette.replace("-", " ").title(),
    )
    return f"{palette_label} ({variant.title()})"
