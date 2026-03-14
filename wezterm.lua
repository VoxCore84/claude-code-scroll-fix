-- WezTerm config for Claude Code scroll fix
-- Copy to ~/.wezterm.lua
--
-- Key setting: scroll_to_bottom_on_input = false
-- This prevents WezTerm from auto-scrolling when Claude Code
-- rewrites output in-place (thinking spinner, streaming text).

local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- Prevent scroll jumping while Claude Code streams output
config.scroll_to_bottom_on_input = false

-- Large scrollback for long Claude sessions
config.scrollback_lines = 100000

-- Performance
config.front_end = 'WebGpu'
config.animation_fps = 1

-- Uncomment and customize:
-- config.font = wezterm.font('JetBrains Mono')
-- config.font_size = 14
-- config.color_scheme = 'Builtin Dark'
-- config.default_cwd = 'C:\\Users\\YourName\\Projects'
-- config.default_prog = { 'bash', '-l' }

return config
