"""Markdown table fixing logic."""

from __future__ import annotations

import re


def _is_separator_row(line: str) -> bool:
    """Check if a line is a markdown table separator (e.g., |---|---|)."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    # Remove outer pipes and check cells
    inner = stripped.strip("|")
    cells = inner.split("|")
    return all(re.match(r"^\s*:?-+:?\s*$", cell) for cell in cells if cell.strip())


def _is_table_row(line: str) -> bool:
    """Check if a line looks like a markdown table row."""
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _parse_table_cells(line: str) -> list[str]:
    """Parse a table row into its cell contents (without outer pipes)."""
    stripped = line.strip()
    # Remove leading and trailing pipe
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _rebuild_separator(widths: list[int], alignments: list[str]) -> str:
    """Rebuild a separator row with the given column widths."""
    cells = []
    for w, align in zip(widths, alignments):
        if align == "center":
            cells.append(":" + "-" * (w) + ":")
        elif align == "right":
            cells.append("-" * (w + 1) + ":")
        elif align == "left-explicit":
            cells.append(":" + "-" * (w + 1))
        else:
            cells.append("-" * (w + 2))
    return "| " + " | ".join(
        cell.center(w + 2) if len(cell) < w + 2 else cell
        for cell, w in zip(cells, widths)
    ).rstrip() + " |"


def _detect_alignment(cell: str) -> str:
    """Detect alignment from a separator cell."""
    cell = cell.strip()
    if cell.startswith(":") and cell.endswith(":"):
        return "center"
    if cell.endswith(":"):
        return "right"
    if cell.startswith(":"):
        return "left-explicit"
    return "left"


def fix_tables(text: str) -> str:
    """Fix markdown tables to have consistent column widths."""
    lines = text.split("\n")
    ends_with_newline = text.endswith("\n")

    i = 0
    while i < len(lines):
        # Look for start of a table
        if not _is_table_row(lines[i]):
            i += 1
            continue

        # Collect all consecutive table rows
        table_start = i
        while i < len(lines) and _is_table_row(lines[i]):
            i += 1
        table_end = i

        table_lines = lines[table_start:table_end]

        # Must have at least a header + separator + one data row
        if len(table_lines) < 2:
            continue

        # Find the separator row
        sep_idx = None
        for j, line in enumerate(table_lines):
            if _is_separator_row(line):
                sep_idx = j
                break

        if sep_idx is None:
            continue

        # Parse all rows into cells
        all_cells = [_parse_table_cells(line) for line in table_lines]

        # Determine number of columns
        num_cols = max(len(cells) for cells in all_cells)

        # Pad cell lists to have equal columns
        for cells in all_cells:
            while len(cells) < num_cols:
                cells.append("")

        # Find max width per column (from non-separator rows)
        col_widths = [0] * num_cols
        for j, cells in enumerate(all_cells):
            if j == sep_idx:
                continue
            for k, cell in enumerate(cells):
                col_widths[k] = max(col_widths[k], len(cell))

        # Ensure minimum width of 3 for readability
        col_widths = [max(w, 3) for w in col_widths]

        # Detect alignments from separator
        sep_cells = _parse_table_cells(table_lines[sep_idx])
        while len(sep_cells) < num_cols:
            sep_cells.append("---")
        alignments = [_detect_alignment(cell) for cell in sep_cells]

        # Rebuild the table
        for j, cells in enumerate(all_cells):
            if j == sep_idx:
                # Rebuild separator
                parts = []
                for k, w in enumerate(col_widths):
                    align = alignments[k]
                    if align == "center":
                        parts.append(":" + "-" * w + ":")
                    elif align == "right":
                        parts.append("-" * (w + 1) + ":")
                    elif align == "left-explicit":
                        parts.append(":" + "-" * (w + 1))
                    else:
                        parts.append("-" * (w + 2))
                lines[table_start + j] = "| " + " | ".join(parts) + " |"
            else:
                # Rebuild content row
                parts = []
                for k, cell in enumerate(cells):
                    parts.append(cell.ljust(col_widths[k]))
                lines[table_start + j] = "| " + " | ".join(parts) + " |"

    result = "\n".join(lines)
    if ends_with_newline and not result.endswith("\n"):
        result += "\n"
    elif not ends_with_newline and result.endswith("\n"):
        result = result.rstrip("\n")

    return result
