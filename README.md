# claude-code-scroll-fix

**Stop Claude Code from hijacking your scroll position.**

When Claude Code streams output (especially during thinking), the terminal viewport jumps to where content is being rewritten — yanking you away from what you're reading. This is one of the most common complaints in the Claude Code issue tracker ([#34242](https://github.com/anthropics/claude-code/issues/34242), [#33367](https://github.com/anthropics/claude-code/issues/33367), [#33814](https://github.com/anthropics/claude-code/issues/33814), [#34052](https://github.com/anthropics/claude-code/issues/34052), [#34400](https://github.com/anthropics/claude-code/issues/34400), [#10835](https://github.com/anthropics/claude-code/issues/10835)).

This repo collects **working workarounds** until Anthropic fixes it upstream.

## Why It Happens

Claude Code uses ANSI escape sequences to update content in-place — the thinking spinner, streaming text blocks, and progress indicators. These updates use **cursor repositioning** (CSI escape codes that move the cursor up to earlier lines) to rewrite the thinking block on every tick. Your terminal follows the cursor position, so the viewport snaps back to wherever the rewrite is happening — even if you've scrolled past it.

There are two layers to the problem:
1. **Output-triggered scrolling** — terminal auto-scrolls when new output appears (`snapOnOutput` fixes this)
2. **Cursor-repositioning** — terminal follows the cursor when Claude rewrites the thinking spinner in-place (`snapOnOutput` does NOT fully fix this — tmux does)

## Fixes (pick one or stack them)

### Fix 1: Windows Terminal — `snapOnOutput: false` (quick win)

**Time: 30 seconds. Reduces jumping ~60-70%.**

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

**Limitations:** Does not fix cursor-repositioning jumps. You'll still see occasional jumping when the thinking spinner updates. For a complete fix, add Fix 3 (tmux).

You can also run the included install script:

```bash
python install_wt_fix.py
```

### Fix 2: tmux — scroll buffer isolation (complete fix)

**This is the real fix.** Running Claude Code inside tmux completely decouples your scroll position from the terminal's cursor tracking. tmux maintains its own virtual terminal — Claude's cursor repositioning happens inside tmux's PTY, but your viewport is completely independent. **It literally cannot jump.**

Bonus: tmux scroll mode lets you **freeze the viewport and scroll freely** while Claude keeps working in the background. Press `q` to snap back to the live input instantly. This solves the "I can't type because I scrolled up" problem.

#### Quick start (Linux / macOS)

```bash
sudo apt install tmux   # Debian/Ubuntu
# or: brew install tmux  # macOS

tmux
claude
```

#### Quick start (Windows — via WSL)

Claude Code needs to be installed inside WSL (the Windows install won't work inside tmux):

```bash
# One-time setup — install Node.js and Claude Code in WSL:
wsl -d Ubuntu
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs tmux
npm install -g @anthropic-ai/claude-code

# Then every time:
wsl -d Ubuntu
cd /mnt/c/Users/YourName/YourProject
tmux
claude
```

#### Windows Terminal profile (one-click launch)

Add this to your Windows Terminal `settings.json` profiles list for a one-click tmux+Claude tab:

```jsonc
{
    "commandline": "wsl.exe -d Ubuntu -- bash -c \"cd /mnt/c/Users/YourName/YourProject && tmux new-session -A -s claude 'claude'\"",
    "name": "Claude - tmux (no scroll jump)",
    "hidden": false,
    "guid": "{b2c3d4e5-f6a7-8901-bcde-f12345678901}"
}
```

#### tmux scroll cheatsheet

| Action | Keys |
|--------|------|
| Enter scroll mode | `Ctrl+B [` |
| Scroll | Arrow keys, PgUp/PgDn, mouse wheel (if mouse mode on) |
| Exit scroll mode (back to input) | `q` |
| Enable mouse support | Add `set -g mouse on` to `~/.tmux.conf` |

The included `tmux.conf` enables mouse scrolling and sets a large scrollback buffer. Copy it:

```bash
cp tmux.conf ~/.tmux.conf
```

### Fix 3: WezTerm — alternative terminal

[WezTerm](https://wezfurlong.org/wezterm/) is a GPU-accelerated terminal with more control over scroll behavior.

Install:
```bash
winget install wez.wezterm  # Windows
# or: brew install --cask wezterm  # macOS
```

Copy the included config:
```bash
cp wezterm.lua ~/.wezterm.lua
```

Key setting — `scroll_to_bottom_on_input = false` prevents the terminal from auto-scrolling when you type. Similar to `snapOnOutput` but for a different terminal.

**Note:** WezTerm does NOT have a `scroll_to_bottom_on_output` setting (despite what some guides claim). The only scroll-related config is `scroll_to_bottom_on_input`.

### Fix 4: `--no-thinking` flag

The thinking blocks are the worst offender because they update a spinner at the top of the output area on every tick. If you don't need to see thinking:

```bash
claude --no-thinking
```

This significantly reduces the escape-sequence churn that causes viewport jumping.

## What Each Fix Does

| Fix | Fixes output scroll | Fixes cursor reposition | Platform | Downsides |
|-----|:---:|:---:|----------|-----------|
| `snapOnOutput: false` | Yes | No | Windows Terminal | Must scroll down to see new output |
| tmux | Yes | **Yes** | Any terminal | Extra keybindings to learn |
| WezTerm | Yes | No | Windows/Mac/Linux | New app to learn |
| `--no-thinking` | Partial | Partial | Any terminal | Lose visibility into thinking |

## Recommended Setup

**Best combo:** Fix 1 (`snapOnOutput`) + Fix 2 (tmux). The terminal setting catches the easy cases, tmux handles cursor repositioning. Together they eliminate the jumping completely.

If you don't want to set up WSL/tmux, Fix 1 + Fix 4 gets you most of the way there.

## Platform Notes

- **macOS Terminal.app / iTerm2**: iTerm2 has "Scroll to bottom on output" in Preferences > Profiles > Terminal. Uncheck it. Terminal.app has no equivalent — use tmux.
- **Linux**: Most terminals (GNOME Terminal, Konsole, Alacritty) have similar "scroll on output" settings. Check your terminal's preferences.
- **VS Code integrated terminal**: Settings > `terminal.integrated.scrollOnOutput` — set to `false`.

## Contributing

Found another fix? Open a PR. The more workarounds we collect, the better — until Anthropic fixes the root cause in Claude Code itself.

## License

MIT
