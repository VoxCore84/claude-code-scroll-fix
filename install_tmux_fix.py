#!/usr/bin/env python3
"""
One-click setup: Claude Code + tmux in WSL + Windows Terminal profile.

This script:
1. Checks that WSL Ubuntu is available
2. Installs Node.js 22, tmux, and Claude Code inside WSL
3. Copies the tmux.conf with mouse scrolling enabled
4. Adds a "Claude - tmux (no scroll jump)" profile to Windows Terminal
5. Also applies snapOnOutput: false while it's in there

Run from any Windows terminal (PowerShell, cmd, Git Bash):
    python install_tmux_fix.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def check_wsl() -> str | None:
    """Check if WSL Ubuntu is available. Returns distro name or None."""
    result = run(["wsl", "--list", "--quiet"])
    if result.returncode != 0:
        return None
    # WSL output has UTF-16 null bytes
    distros = result.stdout.replace("\x00", "").strip().splitlines()
    for distro in distros:
        d = distro.strip()
        if d.lower() in ("ubuntu", "ubuntu-22.04", "ubuntu-24.04", "ubuntu-20.04"):
            return d
    return None


def wsl_run(distro: str, cmd: str, as_root: bool = False) -> subprocess.CompletedProcess:
    """Run a command inside WSL."""
    args = ["wsl", "-d", distro]
    if as_root:
        args += ["-u", "root"]
    args += ["--", "bash", "-c", cmd]
    return run(args, timeout=300)


def setup_wsl(distro: str):
    """Install Node.js 22, tmux, and Claude Code in WSL."""
    print(f"\nSetting up WSL ({distro})...")

    # Check if already installed
    result = wsl_run(distro, "claude --version 2>/dev/null && tmux -V 2>/dev/null")
    if "Claude Code" in result.stdout and "tmux" in result.stdout:
        print("  Claude Code and tmux already installed.")
        return

    # Install Node.js 22
    print("  Installing Node.js 22...")
    result = wsl_run(distro, "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -", as_root=True)
    if result.returncode != 0:
        print(f"  WARNING: Node.js repo setup failed: {result.stderr[:200]}")

    result = wsl_run(distro, "apt-get install -y nodejs tmux", as_root=True)
    if result.returncode != 0:
        print(f"  WARNING: apt install failed: {result.stderr[:200]}")
        return

    # Verify Node
    result = wsl_run(distro, "node --version")
    print(f"  Node.js: {result.stdout.strip()}")

    # Install Claude Code
    print("  Installing Claude Code...")
    result = wsl_run(distro, "npm install -g @anthropic-ai/claude-code 2>&1", as_root=True)
    if result.returncode != 0:
        print(f"  WARNING: Claude Code install failed: {result.stderr[:200]}")
        return

    result = wsl_run(distro, "claude --version 2>/dev/null")
    print(f"  Claude Code: {result.stdout.strip()}")

    # Copy tmux.conf
    print("  Copying tmux.conf...")
    tmux_conf = Path(__file__).parent / "tmux.conf"
    if tmux_conf.exists():
        conf_content = tmux_conf.read_text()
        # Escape for bash
        escaped = conf_content.replace("'", "'\\''")
        wsl_run(distro, f"cat > ~/.tmux.conf << 'TMUXEOF'\n{conf_content}\nTMUXEOF")
        print("  tmux.conf installed.")
    else:
        print("  tmux.conf not found in repo — skipping (add set -g mouse on to ~/.tmux.conf manually)")

    print("  WSL setup complete.")


def find_wt_settings() -> Path | None:
    """Find Windows Terminal settings.json."""
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return None

    store = Path(local) / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"
    if store.exists():
        return store

    portable = Path(local) / "Microsoft" / "Windows Terminal" / "settings.json"
    if portable.exists():
        return portable

    return None


def parse_jsonc(raw: str) -> dict:
    """Parse JSONC (JSON with comments and trailing commas)."""
    lines = []
    for line in raw.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            lines.append("")
            continue
        in_string = False
        result = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"' and (i == 0 or line[i - 1] != '\\'):
                in_string = not in_string
            if not in_string and ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
                break
            result.append(ch)
            i += 1
        lines.append("".join(result))
    clean = "\n".join(lines)
    clean = re.sub(r',(\s*[}\]])', r'\1', clean)
    return json.loads(clean)


def setup_wt_profile(distro: str, project_dir: str | None = None):
    """Add tmux profile to Windows Terminal and apply snapOnOutput fix."""
    settings_path = find_wt_settings()
    if not settings_path:
        print("\nWindows Terminal settings not found — skipping profile setup.")
        print("You can still run manually: wsl -d Ubuntu -- bash -c 'tmux new-session claude'")
        return

    print(f"\nUpdating Windows Terminal settings ({settings_path})...")

    with open(settings_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    data = parse_jsonc(raw)

    # Apply snapOnOutput fix
    defaults = data.setdefault("profiles", {}).setdefault("defaults", {})
    if defaults.get("snapOnOutput") is not False:
        defaults["snapOnOutput"] = False
        print("  Applied snapOnOutput: false")
    else:
        print("  snapOnOutput: false already set")

    # Check if tmux profile already exists
    profiles_list = data.get("profiles", {}).get("list", [])
    tmux_guid = "{b2c3d4e5-f6a7-8901-bcde-f12345678901}"

    if any(p.get("guid") == tmux_guid for p in profiles_list):
        print("  tmux profile already exists — skipping")
    else:
        # Build the command
        cd_part = f"cd /mnt/c/Users/{os.environ.get('USERNAME', 'User')}"
        if project_dir:
            wsl_path = project_dir.replace("\\", "/").replace("C:", "/mnt/c")
            cd_part = f"cd {wsl_path}"

        profile = {
            "commandline": f'wsl.exe -d {distro} -- bash -c "{cd_part} && tmux new-session -A -s claude \'claude\'"',
            "name": "Claude - tmux (no scroll jump)",
            "hidden": False,
            "guid": tmux_guid,
        }
        profiles_list.append(profile)
        data["profiles"]["list"] = profiles_list
        print(f'  Added profile: "Claude - tmux (no scroll jump)"')

    # Backup
    backup = settings_path.with_suffix(".json.backup")
    if not backup.exists():
        shutil.copy2(settings_path, backup)
        print(f"  Backed up to {backup.name}")

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("  Windows Terminal updated (hot-reloads automatically)")


def main():
    print("=" * 60)
    print("Claude Code Scroll Fix — tmux + Windows Terminal Setup")
    print("=" * 60)

    if sys.platform != "win32":
        print("\nThis installer is for Windows. On Linux/macOS:")
        print("  sudo apt install tmux  # or: brew install tmux")
        print("  cp tmux.conf ~/.tmux.conf")
        print("  tmux")
        print("  claude")
        sys.exit(0)

    # Step 1: Check WSL
    print("\nChecking WSL...")
    distro = check_wsl()
    if not distro:
        print("ERROR: No Ubuntu WSL distro found.")
        print("Install WSL first: wsl --install -d Ubuntu")
        sys.exit(1)
    print(f"  Found: {distro}")

    # Step 2: Setup WSL (Node + Claude + tmux)
    setup_wsl(distro)

    # Step 3: Setup Windows Terminal profile
    project_dir = os.getcwd()
    setup_wt_profile(distro, project_dir)

    # Done
    print("\n" + "=" * 60)
    print("DONE! Open a new tab in Windows Terminal and select:")
    print('  "Claude - tmux (no scroll jump)"')
    print("")
    print("Scroll with mouse wheel or Ctrl+B [ then PgUp/PgDn.")
    print("Press q to snap back to the input.")
    print("=" * 60)


if __name__ == "__main__":
    main()
