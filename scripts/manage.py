#!/usr/bin/env python3
"""Prepare, validate and build the pinned source patch. Never deploys services."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text())


def run(*args, cwd=ROOT, capture=False):
    return subprocess.check_output(args, cwd=cwd) if capture else subprocess.check_call(args, cwd=cwd)


def verify():
    for name, spec in MANIFEST["sources"].items():
        source = ROOT / "sources" / name
        patch = (ROOT / spec["patch"]).read_bytes()
        if hashlib.sha256(patch).hexdigest() != spec["patch_sha256"]:
            raise RuntimeError(f"{name}: patch hash differs from manifest; review and update the lock")
        head = run("git", "rev-parse", "HEAD", cwd=source, capture=True).decode().strip()
        if head != spec["commit"]:
            raise RuntimeError(f"{name}: unexpected upstream commit {head}")
        diff = run("git", "diff", "HEAD", "--binary", "--full-index", cwd=source, capture=True)
        if diff != patch:
            raise RuntimeError(f"{name}: checkout differs from the reviewed patch")
        extra = run("git", "ls-files", "--others", "--exclude-standard", cwd=source, capture=True)
        if extra.strip():
            raise RuntimeError(f"{name}: untracked files in source tree; refusing build")
    print("Pinned commits and exact patches verified.")


def prepare(target):
    target = Path(target).resolve()
    if target.exists():
        raise RuntimeError("Target must not exist; refusing to overwrite a checkout")
    # Copy only versioned bundle inputs, never local state, caches or credentials.
    target.mkdir(parents=True)
    for name in ["manifest.json", "Dockerfile", ".dockerignore", ".gitignore", ".gitattributes", "compose.custom.yaml", "README.md", "VERIFICATION.md"]:
        shutil.copy2(ROOT / name, target / name)
    for name in ["scripts", "patches"]:
        shutil.copytree(ROOT / name, target / name, ignore=shutil.ignore_patterns("__pycache__"))
    for name, spec in MANIFEST["sources"].items():
        patch = target / spec["patch"]
        if hashlib.sha256(patch.read_bytes()).hexdigest() != spec["patch_sha256"]:
            raise RuntimeError(f"{name}: patch hash mismatch")
        source = target / "sources" / name
        source.mkdir(parents=True)
        run("git", "init", "-q", cwd=source)
        run("git", "remote", "add", "origin", spec["url"], cwd=source)
        run("git", "fetch", "--depth=1", "origin", spec["commit"], cwd=source)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=source)
        run("git", "apply", "--check", str(patch), cwd=source)
        run("git", "apply", "--index", str(patch), cwd=source)
    run(sys.executable, str(target / "scripts/manage.py"), "verify", cwd=target)
    print(f"Prepared {target}; no running service was changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("build")
    sub.add_parser("test")
    sub.add_parser("prepare").add_argument("target")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(args.target)
    verify()
    if args.command == "build":
        run("docker", "build", "--build-arg", f"BASE_IMAGE={MANIFEST['base_image']}",
            "--build-arg", f"NODE_IMAGE={MANIFEST['node_image']}", "-t", MANIFEST["image"], ".")
    elif args.command == "test":
        run(sys.executable, str(ROOT / "scripts/test_rollback.py"))
        canvas = ROOT / "sources/canvas"
        run("npm", "ci", "--cache", str(ROOT / "artifacts/npm-cache"), "--no-audit", "--no-fund", cwd=canvas)
        run("npm", "run", "make-i18n", cwd=canvas)
        run("npm", "run", "check-translation-completeness", cwd=canvas)
        run("npx", "eslint", "src/api/agent-profiles-service/agent-profiles-service.api.ts",
            "src/components/features/settings/agent-profiles/agent-profiles-local-view.tsx",
            "src/hooks/mutation/use-create-conversation.ts", cwd=canvas)
        run("npm", "run", "typecheck", cwd=canvas)
        run("npx", "vitest", "run", "__tests__/components/settings/agent-profiles/agent-profiles-local-view.test.tsx",
            "__tests__/hooks/mutation/use-create-conversation.test.tsx", cwd=canvas)
        run("docker", "run", "--rm", "--user", "0", "--entrypoint", "sh",
            "-v", f"{ROOT / 'sources/sdk'}:/src:ro", "-w", "/src", MANIFEST["image"], "-c",
            "uv pip install --system pytest==9.0.2 pytest-asyncio==1.3.0 pytest-mock==3.15.1 && "
            "python -m pytest tests/sdk/profiles tests/sdk/settings tests/agent_server/test_agent_profiles_router.py tests/agent_server/test_agent_profile_conv_start.py --override-ini cache_dir=/tmp/pytest-cache")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
