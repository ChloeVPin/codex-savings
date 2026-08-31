#!/usr/bin/env python3
"""Reject U+2014 in text artifacts under a skill directory."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple


FORBIDDEN_CHARACTER = "\u2014"


def _text_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        yield path


def find_violations(root: Path) -> List[Tuple[Path, int]]:
    violations: List[Tuple[Path, int]] = []
    for path in _text_files(root):
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        count = content.count(FORBIDDEN_CHARACTER)
        if count:
            violations.append((path, count))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    violations = find_violations(args.root)
    if violations:
        for path, count in violations:
            print(f"{path}: {count} forbidden U+2014 character(s)")
        return 1

    print(f"No forbidden U+2014 characters found under {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
