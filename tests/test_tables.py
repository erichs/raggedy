"""Unit tests for markdown table fixing."""

from raggedy.tables import fix_tables


class TestFixTables:
    def test_simple_table(self):
        text = (
            "| A | B |\n"
            "|---|---|\n"
            "| hello | x |\n"
            "| y | world |\n"
        )
        result = fix_tables(text)
        lines = result.strip().split("\n")
        # All rows should have consistent column widths
        assert lines[0] == "| A     | B     |"
        assert lines[1] == "| ------- | ------- |"
        assert lines[2] == "| hello | x     |"
        assert lines[3] == "| y     | world |"

    def test_already_aligned(self):
        text = (
            "| Name  | Value |\n"
            "| ----- | ----- |\n"
            "| alpha | one   |\n"
        )
        result = fix_tables(text)
        lines = result.strip().split("\n")
        assert lines[0] == "| Name  | Value |"
        assert lines[2] == "| alpha | one   |"

    def test_preserves_alignment_markers(self):
        text = (
            "| Left | Center | Right |\n"
            "|:---|:---:|---:|\n"
            "| a | b | c |\n"
        )
        result = fix_tables(text)
        lines = result.strip().split("\n")
        # Separator should preserve alignment
        assert ":---" in lines[1]  # left
        assert "---:" in lines[1]  # right

    def test_no_table(self):
        text = "Just some text\nwith no tables\n"
        assert fix_tables(text) == text

    def test_preserves_surrounding_content(self):
        text = (
            "# Header\n"
            "\n"
            "| A | B |\n"
            "|---|---|\n"
            "| x | y |\n"
            "\n"
            "More text\n"
        )
        result = fix_tables(text)
        lines = result.split("\n")
        assert lines[0] == "# Header"
        assert lines[1] == ""
        assert lines[5] == ""
        assert lines[6] == "More text"

    def test_preserves_trailing_newline(self):
        text = "| A |\n|---|\n| B |\n"
        result = fix_tables(text)
        assert result.endswith("\n")
