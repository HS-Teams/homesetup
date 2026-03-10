local wezterm = require 'wezterm'

local dimmer = { brightness = 0.05 }

local brew_prefix = "/opt/homebrew/bin/brew"

local mux = wezterm.mux
wezterm.on("gui-startup", function(cmd)
  local tab, pane, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)

local config = {

  -- What to set the TERM variable to
  term = "xterm-256color",
  default_prog = { "sh", "-c", "exec $(" .. brew_prefix .. " --prefix bash)/bin/bash -l" },
  exit_behavior = 'Close',
  window_close_confirmation = 'AlwaysPrompt',

  -- Don't ask the macOS IME/text services to compose input
  use_dead_keys = true,
  use_ime = false,
  bold_brightens_ansi_colors = "BrightAndBold",

  -- Window padding for macOS aesthetics
  window_padding = {
    left = 10,
    right = 10,
    top = 10,
    bottom = 10,
  },

  -- Window decorations
  window_decorations = "TITLE | RESIZE",

  -- Font rendering features
  harfbuzz_features = { "calt=1", "clig=1", "liga=1" },

  -- Scroll
  scrollback_lines = 5000,
  enable_scroll_bar = true,
  min_scroll_bar_height = '3cell',

  -- Font settings
  font_size = 16.0,
  font = wezterm.font_with_fallback({
    "DroidSansMono Nerd Font",
    "MesloLGS Nerd Font Mono",
  }),
  font_rules = {
    {
      italic = true,
      font = wezterm.font("DroidSansMono Nerd Font", { italic = true }),
      font = wezterm.font("MesloLGS Nerd Font Mono", { italic = true }),
    }
  },

  -- Background settings
  background = {
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
  },

  -- Appearance settings
  colors = {
    scrollbar_thumb = '#75e9be',
  },
  macos_window_background_blur = 10,
  use_fancy_tab_bar = true,
  adjust_window_size_when_changing_font_size = false,
  hide_tab_bar_if_only_one_tab = true,

  -- Cursor settings
  default_cursor_style = "BlinkingUnderline",
  cursor_blink_rate = 500,
  cursor_thickness = 2.0,
  line_height = 1.2,

  -- Keyboard shortcuts
  -- Modifiers: CTRL|SHIFT|CMD|ALT|OPT|META
  keys = {
    -- Existing shortcuts
    { key = "t", mods = "CMD", action = wezterm.action.SpawnTab("CurrentPaneDomain") },
    { key = "w", mods = "CMD", action = wezterm.action.CloseCurrentTab({ confirm = true }) },
    { key = "k", mods = "CMD", action = wezterm.action { ClearScrollback = "ScrollbackAndViewport" } },
    { key = "1", mods = "CMD", action = wezterm.action.ActivateTab(0) },
    { key = "2", mods = "CMD", action = wezterm.action.ActivateTab(1) },
    { key = "3", mods = "CMD", action = wezterm.action.ActivateTab(2) },
    { key = "4", mods = "CMD", action = wezterm.action.ActivateTab(3) },
  },
}

return config
