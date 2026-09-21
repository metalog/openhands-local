#!/usr/bin/env python3
"""Offline downgrade: remove ONLY the added profile field, preserving every other field.
Defaults to dry-run. Stop OpenHands services before --write. No conversation edits.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles_dir", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.profiles_dir.is_dir():
        parser.error("profiles_dir must be an existing agent-profiles directory")
    changes = []
    for path in sorted(args.profiles_dir.glob("*.json")):
        if path.is_symlink():
            raise RuntimeError("Refusing symlink: " + str(path))
        data = json.loads(path.read_text())
        if data.get("agent_kind") == "openhands" and "system_prompt" in data:
            del data["system_prompt"]
            changes.append((path, data))
    print(f"Profiles requiring conversion: {len(changes)}")
    if not args.write or not changes:
        return
    backup = args.profiles_dir.parent / ("system-prompt-rollback-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))
    backup.mkdir(mode=0o700)
    # Back up everything before the first write. Keep backups outside the profile scanner.
    for path, _ in changes:
        shutil.copy2(path, backup / path.name)
        (backup / path.name).chmod(0o600)
    for path, data in changes:
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".prompt-rollback-")
        try:
            with os.fdopen(fd, "w") as output:
                output.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
                output.flush()
                os.fsync(output.fileno())
            os.chmod(tmp, path.stat().st_mode & 0o777)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    print(f"Converted. Original profiles saved in {backup}")


if __name__ == "__main__":
    main()
