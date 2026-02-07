"""Core diagram detection and fixing logic."""

from __future__ import annotations

import re

# Characters that start a box-drawing line
LEFT_BORDER_CHARS = set("│┌├└+|")

# Right border counterparts
RIGHT_BORDER = {
    "┌": "┐",
    "├": "┤",
    "└": "┘",
    "│": "│",
    "+": "+",
    "|": "|",
}

# Horizontal rule characters (used for fill)
HRULE_CHARS = set("─-═")

# Horizontal rule left chars (lines that get extended with fill)
HRULE_LEFT = set("┌├└+")

# Characters that act as inner junctions in horizontal rules
JUNCTION_CHARS = set("┬┴┼╦╩╬╤╧╪┰┸")

# Language tags that indicate code (not diagrams)
CODE_LANG_TAGS = {
    "python", "py", "javascript", "js", "typescript", "ts", "rust", "go",
    "java", "c", "cpp", "c++", "csharp", "cs", "ruby", "rb", "php", "perl",
    "swift", "kotlin", "scala", "haskell", "hs", "lua", "r", "sql", "bash",
    "sh", "zsh", "fish", "powershell", "ps1", "html", "css", "scss", "sass",
    "less", "xml", "json", "yaml", "yml", "toml", "ini", "conf", "cfg",
    "dockerfile", "docker", "makefile", "make", "cmake", "elixir", "ex",
    "erlang", "erl", "clojure", "clj", "ocaml", "ml", "fsharp", "fs",
    "dart", "zig", "nim", "v", "vlang", "groovy", "matlab", "julia", "jl",
    "objc", "objective-c", "assembly", "asm", "nasm", "wasm", "graphql",
    "gql", "protobuf", "proto", "thrift", "csv", "diff", "patch",
}

# Tags that should be treated as potential diagram blocks
DIAGRAM_TAGS = {"text", "ascii", "diagram", "txt", ""}


def _display_width(s: str) -> int:
    """Return the display width of a string, counting characters."""
    return len(s)


def _is_fence(line: str) -> tuple[bool, str]:
    """Check if a line is a fenced code block delimiter.

    Returns (is_fence, tag) where tag is the language tag (or "").
    """
    stripped = line.strip()
    for fence in ("```", "~~~"):
        if stripped.startswith(fence):
            tag = stripped[len(fence):].strip().lower()
            # Remove anything after whitespace in the tag
            tag = tag.split()[0] if tag else ""
            return True, tag
    return False, ""


def _is_diagram_block(lines: list[str]) -> bool:
    """Determine if a code block's contents look like a diagram."""
    border_starts = 0
    has_hrule = False

    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            continue
        if stripped[0] in LEFT_BORDER_CHARS:
            border_starts += 1
        for ch in stripped:
            if ch in HRULE_CHARS:
                has_hrule = True
                break

    return border_starts >= 3 and has_hrule


def _split_groups(lines: list[str]) -> list[list[tuple[int, str]]]:
    """Split diagram lines into groups separated by blank/non-border lines.

    Returns list of groups, each group is a list of (original_index, line_text).
    """
    groups: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped and stripped[0] in LEFT_BORDER_CHARS:
            current.append((i, line))
        else:
            if current:
                groups.append(current)
                current = []
    if current:
        groups.append(current)

    return groups


def _find_fill_char(line: str) -> str:
    """Find the horizontal fill character used in a line."""
    for ch in line:
        if ch in HRULE_CHARS:
            return ch
    return "─"


def _fix_hrule_line(line: str, target_width: int, left_char: str) -> str:
    """Fix a horizontal rule line to the target width."""
    right_char = RIGHT_BORDER[left_char]
    stripped = line.rstrip()

    # Remove existing right border if present
    if stripped and stripped[-1] == right_char:
        stripped = stripped[:-1]

    fill_char = _find_fill_char(stripped)

    # Find the last junction character position
    last_junction = -1
    for i in range(len(stripped) - 1, 0, -1):
        if stripped[i] in JUNCTION_CHARS:
            last_junction = i
            break

    if last_junction > 0:
        # Preserve everything up to and including the last junction
        prefix = stripped[: last_junction + 1]
        # Fill from after the last junction to target_width - 1
        needed = target_width - 1 - len(prefix)
        if needed > 0:
            result = prefix + fill_char * needed + right_char
        else:
            result = prefix + right_char
    else:
        # No junctions — just extend fill
        # Keep the left char and any existing content
        needed = target_width - 1 - len(stripped)
        if needed > 0:
            result = stripped + fill_char * needed + right_char
        else:
            result = stripped + right_char

    return result


def _fix_content_line(line: str, target_width: int, left_char: str) -> str:
    """Fix a content line (│...│ or |...|) to the target width."""
    right_char = RIGHT_BORDER[left_char]
    stripped = line.rstrip()

    # Remove existing right border if present
    if stripped and stripped[-1] == right_char:
        stripped = stripped[:-1]

    # Pad with spaces to target_width - 1, then add right border
    needed = target_width - 1 - len(stripped)
    if needed > 0:
        result = stripped + " " * needed + right_char
    else:
        result = stripped + right_char

    return result


def _fix_group(group: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Fix a single diagram group to have consistent right edges."""
    lines = [text for _, text in group]

    # Compute the effective width each line needs.
    # For each line, strip trailing whitespace, then if it ends with the
    # expected right border char, that's its width; otherwise it needs +1
    # for the missing right border.
    effective_widths = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            continue
        first = stripped[0]
        rstripped = line.rstrip()
        width = len(rstripped)
        if first in LEFT_BORDER_CHARS:
            right_char = RIGHT_BORDER[first]
            if not rstripped.endswith(right_char):
                width += 1  # needs a right border char added
        effective_widths.append(width)

    target_width = max(effective_widths) if effective_widths else 0

    # Fix each line
    result = []
    for orig_idx, line in group:
        stripped = line.lstrip()
        if not stripped:
            result.append((orig_idx, line))
            continue

        first = stripped[0]
        # Compute leading whitespace
        leading = line[: len(line) - len(stripped)]

        if first in HRULE_LEFT:
            fixed = _fix_hrule_line(stripped, target_width - len(leading), first)
        elif first in ("│", "|"):
            fixed = _fix_content_line(stripped, target_width - len(leading), first)
        else:
            fixed = stripped
            # Pad to target width if it starts with a border char
            if first in LEFT_BORDER_CHARS:
                right_char = RIGHT_BORDER[first]
                fixed_stripped = stripped.rstrip()
                if fixed_stripped and fixed_stripped[-1] == right_char:
                    fixed_stripped = fixed_stripped[:-1]
                needed = target_width - len(leading) - 1 - len(fixed_stripped)
                if needed > 0:
                    fixed = fixed_stripped + " " * needed + right_char
                else:
                    fixed = fixed_stripped + right_char

        result.append((orig_idx, leading + fixed))

    # After fixing the outer box, recursively fix nested boxes
    result = _fix_nested_in_group(result)

    return result


def _fix_nested_in_group(
    fixed_group: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """Fix nested boxes within the content lines of a fixed group.

    After the outer box is fixed, content lines (│...│) may contain inner
    box structures with their own ragged edges. This function detects and
    fixes those inner boxes recursively.
    """
    result = list(fixed_group)

    # Find runs of consecutive content lines (starting with │ or |)
    i = 0
    while i < len(result):
        _, line = result[i]
        stripped = line.lstrip()
        if not stripped or stripped[0] not in ("│", "|"):
            i += 1
            continue

        # Collect consecutive content lines with the same outer border char
        outer_char = stripped[0]
        outer_right = RIGHT_BORDER[outer_char]
        run_start = i
        while i < len(result):
            _, l = result[i]
            s = l.lstrip()
            if s and s[0] == outer_char:
                i += 1
            else:
                break
        run_end = i

        if run_end - run_start < 3:
            continue  # Need at least 3 lines for a diagram

        # Extract inner content by stripping the outer left and right border chars
        run = result[run_start:run_end]
        inner_lines = []
        for _, l in run:
            # Line is: <outer_left><inner_content><outer_right>
            # Strip the first and last character (outer borders)
            if len(l) >= 2 and l[-1] == outer_right:
                inner_lines.append(l[1:-1])
            else:
                inner_lines.append(l[1:])

        # Check if inner content contains a diagram
        if not _is_diagram_block(inner_lines):
            continue

        # The outer box width (all lines same width after outer fix)
        outer_width = len(run[0][1])
        inner_width = outer_width - 2  # minus two outer border chars

        # Fix inner diagram groups
        inner_groups = _split_groups(inner_lines)
        for inner_group in inner_groups:
            inner_fixed = _fix_group(inner_group)  # recursive via _fix_group
            for inner_idx, inner_text in inner_fixed:
                # Re-pad inner text to maintain outer box width
                if len(inner_text) < inner_width:
                    inner_text += " " * (inner_width - len(inner_text))
                elif len(inner_text) > inner_width:
                    # Inner content exceeds outer constraint; skip
                    continue

                # Re-assemble with outer borders
                new_line = run[0][1][0] + inner_text + outer_right
                actual_idx = run_start + inner_idx
                result[actual_idx] = (result[actual_idx][0], new_line)

    return result


def fix_diagrams(text: str) -> str:
    """Fix all diagrams in a markdown document.

    Identifies fenced code blocks that contain ASCII/Unicode box diagrams
    and fixes their right edges to be consistent.
    """
    lines = text.split("\n")
    # Track whether we end with a newline
    ends_with_newline = text.endswith("\n")

    in_fence = False
    fence_tag = ""
    fence_start = -1  # line index of the opening fence (exclusive — content starts at +1)

    i = 0
    while i < len(lines):
        is_fence, tag = _is_fence(lines[i])

        if not in_fence:
            if is_fence:
                in_fence = True
                fence_tag = tag
                fence_start = i
        else:
            if is_fence:
                # End of fenced block
                block_lines = lines[fence_start + 1: i]

                # Decide whether to process this block
                should_process = (
                    fence_tag in DIAGRAM_TAGS
                    and fence_tag not in CODE_LANG_TAGS
                    and _is_diagram_block(block_lines)
                )

                if should_process:
                    groups = _split_groups(block_lines)
                    for group in groups:
                        fixed = _fix_group(group)
                        for orig_idx, new_text in fixed:
                            lines[fence_start + 1 + orig_idx] = new_text

                in_fence = False
                fence_tag = ""
                fence_start = -1
        i += 1

    result = "\n".join(lines)
    # Preserve original trailing newline behavior
    if ends_with_newline and not result.endswith("\n"):
        result += "\n"
    elif not ends_with_newline and result.endswith("\n"):
        result = result.rstrip("\n")

    return result
