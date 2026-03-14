#!/usr/bin/env python3
"""
Adds snapOnOutput: false to Windows Terminal settings.

This prevents the terminal from chasing the cursor when Claude Code
rewrites output in-place, which causes the viewport to jump around.

Safe to run multiple times — skips if already applied.
"""

import json
import os
import shutil
import sys
from pathlib import Path


def find_settings() -> Path | None:
    """Find Windows Terminal settings.json."""
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return None

    # Store (Microsoft Store install)
    store = Path(local) / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"
    if store.exists():
        return store

    # Unpackaged / scoop / portable
    portable = Path(local) / "Microsoft" / "Windows Terminal" / "settings.json"
    if portable.exists():
        return portable

    return None


def apply_fix(settings_path: Path) -> bool:
    """Add snapOnOutput: false to profiles.defaults."""
    with open(settings_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    # Strip JSON comments (// style) for parsing
    lines = []
    for line in raw.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            lines.append("")
        else:
            # Remove inline // comments (naive but covers most cases)
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

    # Remove trailing commas before } or ] (common in jsonc)
    import re
    clean = re.sub(r',(\s*[}\]])', r'\1', clean)

    data = json.loads(clean)

    defaults = data.setdefault("profiles", {}).setdefault("defaults", {})

    if defaults.get("snapOnOutput") is False:
        print("Already applied — snapOnOutput is already false.")
        return False

    defaults["snapOnOutput"] = False

    # Backup original
    backup = settings_path.with_suffix(".json.backup")
    if not backup.exists():
        shutil.copy2(settings_path, backup)
        print(f"Backed up original to {backup}")

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Applied snapOnOutput: false to {settings_path}")
    print("Windows Terminal hot-reloads settings — active in all tabs now.")
    return True


def main():
    if sys.platform != "win32":
        print("This script is for Windows Terminal on Windows.")
        print("See README.md for fixes on other platforms.")
        sys.exit(0)

    settings = find_settings()
    if not settings:
        print("Could not find Windows Terminal settings.json")
        print("Try opening Windows Terminal settings (Ctrl+Shift+,) and adding manually:")
        print('  "profiles": { "defaults": { "snapOnOutput": false } }')
        sys.exit(1)

    print(f"Found settings at: {settings}")
    apply_fix(settings)


if __name__ == "__main__":
    main()
