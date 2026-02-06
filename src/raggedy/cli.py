"""Command-line interface for raggedy."""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys

from raggedy.diagram import fix_diagrams
from raggedy.tables import fix_tables


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="raggedy",
        description="Fix ragged right edges in ASCII/Unicode box diagrams.",
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="+",
        help="Markdown files to process",
    )
    parser.add_argument(
        "-b", "--backup",
        action="store_true",
        help="Create .bak backup before editing",
    )
    parser.add_argument(
        "--mdtable",
        action="store_true",
        help="Also fix markdown tables",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if changes needed (no modification; for CI)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diff without modifying",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    any_changes = False

    for filepath in args.files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                original = f.read()
        except FileNotFoundError:
            print(f"raggedy: error: {filepath}: No such file", file=sys.stderr)
            sys.exit(2)
        except OSError as e:
            print(f"raggedy: error: {filepath}: {e}", file=sys.stderr)
            sys.exit(2)

        fixed = fix_diagrams(original)
        if args.mdtable:
            fixed = fix_tables(fixed)

        if fixed != original:
            any_changes = True

        if args.check:
            # Don't modify, just track changes
            continue

        if args.diff:
            orig_lines = original.splitlines(keepends=True)
            fixed_lines = fixed.splitlines(keepends=True)
            diff = difflib.unified_diff(
                orig_lines, fixed_lines,
                fromfile=f"a/{filepath}",
                tofile=f"b/{filepath}",
            )
            sys.stdout.writelines(diff)
            continue

        if fixed != original:
            if args.backup:
                shutil.copy2(filepath, filepath + ".bak")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed)

    if args.check and any_changes:
        sys.exit(1)
