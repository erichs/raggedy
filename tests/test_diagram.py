"""Unit tests for diagram detection and fixing."""

from raggedy.diagram import (
    _is_diagram_block,
    _is_fence,
    _split_groups,
    _fix_group,
    fix_diagrams,
)


class TestIsFence:
    def test_backtick_fence(self):
        assert _is_fence("```")[0] is True

    def test_tilde_fence(self):
        assert _is_fence("~~~")[0] is True

    def test_fence_with_tag(self):
        is_fence, tag = _is_fence("```python")
        assert is_fence is True
        assert tag == "python"

    def test_fence_with_tag_and_spaces(self):
        is_fence, tag = _is_fence("```  text  ")
        assert is_fence is True
        assert tag == "text"

    def test_not_fence(self):
        assert _is_fence("some text")[0] is False

    def test_empty_tag(self):
        _, tag = _is_fence("```")
        assert tag == ""


class TestIsDiagramBlock:
    def test_valid_diagram(self):
        lines = [
            "┌──────┐",
            "│ text │",
            "├──────┤",
            "│ more │",
            "└──────┘",
        ]
        assert _is_diagram_block(lines) is True

    def test_ascii_diagram(self):
        lines = [
            "+------+",
            "| text |",
            "+------+",
            "| more |",
            "+------+",
        ]
        assert _is_diagram_block(lines) is True

    def test_not_diagram_no_hrule(self):
        lines = [
            "│ text │",
            "│ more │",
            "│ even │",
        ]
        assert _is_diagram_block(lines) is False

    def test_not_diagram_too_few_borders(self):
        lines = [
            "┌──────┐",
            "some text",
            "└──────┘",
        ]
        assert _is_diagram_block(lines) is False

    def test_plain_text(self):
        lines = [
            "This is just text.",
            "No box-drawing chars here.",
            "Just plain content.",
        ]
        assert _is_diagram_block(lines) is False


class TestSplitGroups:
    def test_single_group(self):
        lines = [
            "┌──────┐",
            "│ text │",
            "└──────┘",
        ]
        groups = _split_groups(lines)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_two_groups(self):
        lines = [
            "┌──────┐",
            "│ A    │",
            "└──────┘",
            "",
            "┌──────┐",
            "│ B    │",
            "└──────┘",
        ]
        groups = _split_groups(lines)
        assert len(groups) == 2
        assert len(groups[0]) == 3
        assert len(groups[1]) == 3

    def test_preserves_indices(self):
        lines = [
            "┌──────┐",
            "│ text │",
            "└──────┘",
        ]
        groups = _split_groups(lines)
        assert groups[0][0] == (0, "┌──────┐")
        assert groups[0][1] == (1, "│ text │")
        assert groups[0][2] == (2, "└──────┘")


class TestFixGroup:
    def test_fix_missing_right_borders(self):
        group = [
            (0, "┌──────────┐"),
            (1, "│ text"),
            (2, "└──────────┘"),
        ]
        fixed = _fix_group(group)
        assert fixed[1][1] == "│ text     │"

    def test_fix_missing_corners(self):
        group = [
            (0, "┌──────────"),
            (1, "│ text     │"),
            (2, "└──────────"),
        ]
        fixed = _fix_group(group)
        assert fixed[0][1] == "┌──────────┐"
        assert fixed[2][1] == "└──────────┘"

    def test_fix_short_hrule(self):
        group = [
            (0, "├───┤"),
            (1, "│ content │"),
            (2, "├───┤"),
        ]
        fixed = _fix_group(group)
        # Should extend to match content width
        assert fixed[0][1] == "├─────────┤"
        assert fixed[2][1] == "├─────────┤"

    def test_content_wider_than_hrule(self):
        """Content that's wider than borders should expand the box."""
        group = [
            (0, "┌──────┐"),
            (1, "│ very long content here"),
            (2, "└──────┘"),
        ]
        fixed = _fix_group(group)
        # hrules should expand to match content width
        assert fixed[1][1] == "│ very long content here│"
        assert len(fixed[0][1]) == len(fixed[1][1])
        assert fixed[0][1].startswith("┌")
        assert fixed[0][1].endswith("┐")

    def test_ascii_box(self):
        group = [
            (0, "+--------+"),
            (1, "| text"),
            (2, "+--------+"),
        ]
        fixed = _fix_group(group)
        assert fixed[1][1] == "| text   |"


class TestFixDiagrams:
    def test_preserves_non_diagram_content(self):
        text = "Hello world\n\nSome text\n"
        assert fix_diagrams(text) == text

    def test_preserves_code_blocks(self):
        text = "```python\ndef hello():\n    pass\n```\n"
        assert fix_diagrams(text) == text

    def test_fixes_diagram_in_fence(self):
        text = (
            "# Title\n"
            "\n"
            "```\n"
            "┌──────┐\n"
            "│ text\n"
            "├──────┤\n"
            "│ more\n"
            "└──────┘\n"
            "```\n"
        )
        result = fix_diagrams(text)
        lines = result.split("\n")
        assert lines[4] == "│ text │"
        assert lines[6] == "│ more │"

    def test_ignores_non_diagram_unfenced(self):
        text = (
            "```\n"
            "This is just text.\n"
            "No diagrams here.\n"
            "Just plain content.\n"
            "```\n"
        )
        assert fix_diagrams(text) == text

    def test_preserves_trailing_newline(self):
        text = "```\n┌──┐\n│ x\n├──┤\n│ y\n└──┘\n```\n"
        result = fix_diagrams(text)
        assert result.endswith("\n")

    def test_no_trailing_newline(self):
        text = "```\n┌──┐\n│ x\n├──┤\n│ y\n└──┘\n```"
        result = fix_diagrams(text)
        assert not result.endswith("\n")

    def test_fixes_nested_box_right_edge(self):
        text = (
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────┐\n"
            "│  Correlation & Analytics                                              │\n"
            "│  ┌──────────────────────────────────────────────────────────────────┐ │\n"
            "│  │ Attack Paths │ Blast Radius │ Risk Scoring │ MITRE ATT&CK       │  │\n"
            "│  │ Trust Graph  │ Toxic Combos │ Cross-Account│ Priv Escalation    │  │\n"
            "│  └──────────────────────────────────────────────────────────────────┘ │\n"
            "└───────────────────────────────────────────────────────────────────────┘\n"
            "```\n"
        )
        expected = (
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────┐\n"
            "│  Correlation & Analytics                                              │\n"
            "│  ┌──────────────────────────────────────────────────────────────────┐ │\n"
            "│  │ Attack Paths │ Blast Radius │ Risk Scoring │ MITRE ATT&CK        │ │\n"
            "│  │ Trust Graph  │ Toxic Combos │ Cross-Account│ Priv Escalation     │ │\n"
            "│  └──────────────────────────────────────────────────────────────────┘ │\n"
            "└───────────────────────────────────────────────────────────────────────┘\n"
            "```\n"
        )
        assert fix_diagrams(text) == expected

    def test_multiple_diagrams(self):
        text = (
            "```\n"
            "┌────┐\n"
            "│ A\n"
            "└────┘\n"
            "```\n"
            "\n"
            "```\n"
            "┌──────┐\n"
            "│ B\n"
            "├──────┤\n"
            "│ C\n"
            "└──────┘\n"
            "```\n"
        )
        result = fix_diagrams(text)
        lines = result.split("\n")
        assert lines[2] == "│ A  │"
        assert lines[8] == "│ B    │"
        assert lines[10] == "│ C    │"

    def test_nested_box_inner_edges_fixed(self):
        """Inner boxes within an outer box should have aligned right edges."""
        text = (
            "```\n"
            "┌──────────────────────────┐\n"
            "│ Section A                │\n"
            "│ ┌────────────────────┐│\n"
            "│ │ inner long content ││\n"
            "│ │ short              ││\n"
            "│ └────────────────────┘│\n"
            "├──────────────────────────┤\n"
            "│ Section B                │\n"
            "└──────────────────────────┘\n"
            "```\n"
        )
        result = fix_diagrams(text)
        lines = result.split("\n")

        # All outer lines should be the same width
        box_lines = lines[1:10]  # the 9 lines inside the fence
        widths = [len(l) for l in box_lines]
        assert len(set(widths)) == 1, f"outer widths not uniform: {widths}"

        # Inner box right borders should all be at the same column
        inner_top = lines[3]     # │ ┌────...┐ │
        inner_row1 = lines[4]    # │ │ ...   │ │
        inner_row2 = lines[5]    # │ │ ...   │ │
        inner_bot = lines[6]     # │ └────...┘ │

        # Strip outer │ borders to get inner content
        def inner_right_pos(line):
            inner = line[1:-1]  # strip outer │ ... │
            return len(inner.rstrip())

        assert inner_right_pos(inner_top) == inner_right_pos(inner_row1)
        assert inner_right_pos(inner_top) == inner_right_pos(inner_row2)
        assert inner_right_pos(inner_top) == inner_right_pos(inner_bot)

    def test_nested_box_idempotent(self):
        """Fixing a nested diagram twice should produce the same result."""
        text = (
            "```\n"
            "┌─────────────────────┐\n"
            "│ Outer               │\n"
            "│ ┌───────────────┐│\n"
            "│ │ inner content ││\n"
            "│ └───────────────┘│\n"
            "├─────────────────────┤\n"
            "│ Footer              │\n"
            "└─────────────────────┘\n"
            "```\n"
        )
        first = fix_diagrams(text)
        second = fix_diagrams(first)
        assert first == second

    def test_nested_multiple_inner_boxes(self):
        """Multiple inner boxes at different vertical positions."""
        text = (
            "```\n"
            "┌────────────────────┐\n"
            "│ Top section        │\n"
            "│ ┌──────────────┐│\n"
            "│ │ box one      ││\n"
            "│ └──────────────┘│\n"
            "├────────────────────┤\n"
            "│ Mid section        │\n"
            "│ ┌──────────────┐│\n"
            "│ │ box two      ││\n"
            "│ └──────────────┘│\n"
            "└────────────────────┘\n"
            "```\n"
        )
        result = fix_diagrams(text)
        lines = result.split("\n")

        # Both inner boxes should have aligned borders
        for row_idx in (4, 9):
            inner_top = lines[row_idx - 1]
            inner_content = lines[row_idx]
            inner_bot = lines[row_idx + 1]

            def irp(line):
                return len(line[1:-1].rstrip())

            assert irp(inner_top) == irp(inner_content), (
                f"inner box at line {row_idx}: top vs content mismatch"
            )
            assert irp(inner_top) == irp(inner_bot), (
                f"inner box at line {row_idx}: top vs bottom mismatch"
            )

    def test_fixture_files(self):
        """Test that processing ragged.md produces expected.md."""
        import pathlib

        fixtures = pathlib.Path(__file__).parent / "fixtures"
        ragged = (fixtures / "ragged.md").read_text()
        expected = (fixtures / "expected.md").read_text()

        result = fix_diagrams(ragged)
        assert result == expected
