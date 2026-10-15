#!/usr/bin/env python3
"""Rename this template into a new project (run once, right after cloning).

Usage:
    python3 scripts/bootstrap.py my-project-name [--dry-run]

Steps performed:
    1. Validate the new distribution name.
    2. Rename ``src/python_llm_template`` to ``src/<module_name>``.
    3. Rewrite ``python_llm_template`` / ``python-llm-template`` references in
       the files under the paths listed in ``EDIT_PATHS`` (nothing else is
       touched).
    4. Regenerate ``uv.lock`` if ``uv`` is on PATH (otherwise print a reminder).

Afterwards run ``make setup`` and ``make check``.
"""

from __future__ import annotations

import argparse
import keyword
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

OLD_DIST = "python-llm-template"
OLD_MODULE = "python_llm_template"

# Files and directories (relative to the repo root) that may contain the name.
EDIT_PATHS = [
    "pyproject.toml",
    "README.md",
    "AGENTS.md",
    "Makefile",
    "docs",
    "src",
    "tests",
]

DIST_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


def parse_args() -> argparse.Namespace:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="new distribution name, e.g. my-project")
    parser.add_argument("--dry-run", action="store_true", help="show the changes")
    return parser.parse_args()


def validate(name: str) -> str:
    """Return the new module name, or exit with a clear message."""
    if not DIST_NAME_PATTERN.match(name):
        sys.exit(
            f"error: '{name}' is not a valid distribution name.\n"
            "Use lowercase letters, digits, and inner hyphens/underscores/dots, "
            "e.g. 'my-project'."
        )
    if name == OLD_DIST:
        sys.exit("error: name is unchanged; nothing to do.")
    module_name = re.sub(r"[-.]", "_", name)
    if not module_name.isidentifier() or keyword.iskeyword(module_name):
        sys.exit(f"error: '{module_name}' is not a valid Python module name.")
    return module_name


def iter_editable_files() -> list[Path]:
    """List existing files under the allowlisted paths."""
    files: list[Path] = []
    for rel in EDIT_PATHS:
        path = REPO_ROOT / rel
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def files_to_change() -> list[Path]:
    """List files that still contain one of the old names."""
    paths: list[Path] = []
    for path in iter_editable_files():
        text = path.read_text(encoding="utf-8")
        if OLD_MODULE in text or OLD_DIST in text:
            paths.append(path)
    return paths


def main() -> None:
    args = parse_args()
    module_name = validate(args.name)

    source_dir = REPO_ROOT / "src" / OLD_MODULE
    if not source_dir.is_dir():
        sys.exit(f"error: {source_dir} not found; already bootstrapped?")

    target_dir = REPO_ROOT / "src" / module_name
    if target_dir.exists():
        sys.exit(f"error: {target_dir} already exists; refusing to overwrite.")

    paths = files_to_change()
    verb = "would update" if args.dry_run else "updated"
    for path in paths:
        if not args.dry_run:
            text = path.read_text(encoding="utf-8")
            text = text.replace(OLD_MODULE, module_name).replace(OLD_DIST, args.name)
            path.write_text(text, encoding="utf-8")
        print(f"{verb}: {path.relative_to(REPO_ROOT)}")

    if args.dry_run:
        print(f"would rename: src/{OLD_MODULE} -> src/{module_name}")
        return

    shutil.move(str(source_dir), str(target_dir))
    print(f"renamed: src/{OLD_MODULE} -> src/{module_name}")

    if shutil.which("uv") is not None:
        subprocess.run(["uv", "lock"], cwd=REPO_ROOT, check=True)
        print("regenerated: uv.lock")
    else:
        print("note: run `uv lock` (or `make setup`) to regenerate uv.lock.")

    print(f"\ndone. Next: `make setup`, then `make check`, for '{args.name}'.")


if __name__ == "__main__":
    main()
