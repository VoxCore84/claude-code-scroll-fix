# claude-code-scroll-fix

**Stop Claude Code from hijacking your scroll position.**

When Claude Code streams output (especially during thinking), the terminal viewport jumps to where content is being rewritten — yanking you away from what you're reading. This is one of the most common complaints in the Claude Code issue tracker ([#34242](https://github.com/anthropics/claude-code/issues/34242), [#33367](https://github.com/anthropics/claude-code/issues/33367), [#33814](https://github.com/anthropics/claude-code/issues/33814), [#34052](https://github.com/anthropics/claude-code/issues/34052), [#34400](https://github.com/anthropics/claude-code/issues/34400), [#10835](https://github.com/anthropics/claude-code/issues/10835)).

This repo collects **working workarounds** until Anthropic fixes it upstream.

## Why It Happens

Claude Code uses ANSI escape sequences to update content in-place — the thinking spinner, streaming text blocks, and progress indicators. When your terminal re-renders lines above your current viewport, it follows the cursor position back up to where the rewrite is happening. Result: you're reading line 200, and the terminal snaps back to line 50.

## Fixes (pick one or stack them)

### Fix 1: Windows Terminal — `snapOnOutput: false` (recommended)

**Time: 30 seconds. Works immediately.**

Open your Windows Terminal settings (`Ctrl+Shift+,` to open `settings.json`) and add `snapOnOutput: false` to your profile defaults:

```jsonc
"profiles": {
    "defaults": {
        "snapOnOutput": false
        // your other settings...
    }
}
```

Windows Terminal hot-reloads settings — this takes effect in all open tabs instantly.

**Trade-off:** When Claude finishes a response, you may need to scroll down to see the end. Worth it.

You can also run the included install script:

```bash
python install_wt_fix.py
```

### Fix 2: WezTerm — alternative terminal

[WezTerm](https://wezfurlong.org/wezterm/) is a GPU-accelerated terminal that gives you more control over scroll behavior.

Install:
```bash
winget install wez.wezterm
```

Copy the included config:
```bash
cp wezterm.lua ~/.wezterm.lua
```

Key setting — `scroll_to_bottom_on_input = false` prevents the terminal from auto-scrolling at all. You control the viewport.

### Fix 3: tmux — scroll buffer isolation

Running Claude Code inside tmux completely decouples your scroll position from the terminal's cursor tracking. tmux maintains its own scroll buffer that doesn't care what escape sequences the inner program is sending.

```bash
# Linux/macOS
sudo apt install tmux  # or brew install tmux

# Windows (WSL)
wsl -d Ubuntu
tmux
claude

# Scroll: Ctrl+B [ then arrow keys/PgUp/PgDn
# Exit scroll: q
```

This is the most robust solution — tmux scroll is completely immune to in-place terminal rewrites.

### Fix 4: `--no-thinking` flag

The thinking blocks are the worst offender because they update a spinner at the top of the output area on every tick. If you don't need to see thinking:

```bash
claude --no-thinking
```

This significantly reduces the escape-sequence churn that causes viewport jumping.

## What Each Fix Does

| Fix | Mechanism | Platform | Downsides |
|-----|-----------|----------|-----------|
| `snapOnOutput: false` | Tells terminal not to follow cursor on output | Windows Terminal | Must manually scroll to see new output |
| WezTerm | Different terminal with better scroll control | Windows/Mac/Linux | New app to learn |
| tmux | Independent scroll buffer | Any terminal | Extra keybindings to learn |
| `--no-thinking` | Removes the main source of in-place rewrites | Any terminal | Lose visibility into thinking |

## Stacking

These fixes are complementary. The strongest combo is **Fix 1 + Fix 4** (terminal stops chasing + less rewriting to chase). If that's not enough, **Fix 3** (tmux) is the nuclear option.

## Platform Notes

- **macOS Terminal.app / iTerm2**: iTerm2 has "Scroll to bottom on output" in Preferences > Profiles > Terminal. Uncheck it. Terminal.app has no equivalent — use tmux.
- **Linux**: Most terminals (GNOME Terminal, Konsole, Alacritty) have similar "scroll on output" settings. Check your terminal's preferences.
- **VS Code integrated terminal**: Settings > `terminal.integrated.scrollOnOutput` — set to `false`.

## Contributing

Found another fix? Open a PR. The more workarounds we collect, the better — until Anthropic fixes the root cause in Claude Code itself.

## License

MIT
