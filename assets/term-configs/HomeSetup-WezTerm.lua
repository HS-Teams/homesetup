local wezterm = require "wezterm"

local dimmer = { brightness = 0.05 }
local bash_path = "/opt/homebrew/opt/bash/bin/bash"
local config = wezterm.config_builder()
local mux = wezterm.mux

wezterm.on("gui-startup", function(cmd)
  local _, _, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)

-- Shell
config.term = "xterm-256color"
config.default_prog = { bash_path, "-l" }
config.exit_behavior = "Close"
config.window_close_confirmation = "AlwaysPrompt"
config.skip_close_confirmation_for_processes_named = {}

-- Input
-- Preserve dead-key composition for accented characters without enabling the macOS IME.
config.use_dead_keys = true
config.use_ime = false
config.bold_brightens_ansi_colors = "BrightAndBold"

-- Window
config.window_padding = {
  left = 10,
  right = 10,
  top = 10,
  bottom = 10,
}
config.window_decorations = "TITLE | RESIZE"

-- Font
config.harfbuzz_features = { "calt=1", "clig=1", "liga=1" }
config.font_size = 16.0
config.font_dirs = { os.getenv("HOME") .. "/Library/Fonts" }
config.font = wezterm.font_with_fallback({
  "MesloLGS Nerd Font Mono",
  "DroidSansMono Nerd Font",
})
config.line_height = 1.2

-- Scroll
config.scrollback_lines = 5000
config.enable_scroll_bar = true
config.min_scroll_bar_height = "3cell"

-- Background settings
config.background = {
    {
      source = {
        File = os.getenv('HOME') .. "/HomeSetup/assets/images/hs-cover.png",
      },
      width = '100%',
      height = '100%',
      repeat_x = 'NoRepeat',
      repeat_y = 'NoRepeat',
      attachment = "Fixed",
      hsb = dimmer,
      opacity = 0.9,
    },
}

-- Appearance
config.colors = {
  scrollbar_thumb = "#75e9be",
}
config.macos_window_background_blur = 10
config.use_fancy_tab_bar = true
config.adjust_window_size_when_changing_font_size = false
config.hide_tab_bar_if_only_one_tab = true

-- Cursor
config.default_cursor_style = "BlinkingUnderline"
config.cursor_blink_rate = 500
config.cursor_thickness = 2.0

-- Keyboard shortcuts
-- Modifiers: CTRL|SHIFT|CMD|ALT|OPT|META
config.keys = {
  { key = "t", mods = "CMD", action = wezterm.action.SpawnTab("CurrentPaneDomain") },
  { key = "w", mods = "CMD", action = wezterm.action.CloseCurrentTab({ confirm = true }) },
  { key = "k", mods = "CMD", action = wezterm.action.ClearScrollback("ScrollbackAndViewport") },
  { key = "1", mods = "CMD", action = wezterm.action.ActivateTab(0) },
  { key = "2", mods = "CMD", action = wezterm.action.ActivateTab(1) },
  { key = "3", mods = "CMD", action = wezterm.action.ActivateTab(2) },
  { key = "4", mods = "CMD", action = wezterm.action.ActivateTab(3) },
}

return config
