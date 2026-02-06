"""Integration tests for the CLI."""

import os
import shutil
import subprocess
import sys
import tempfile

import pytest


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def ragged_file(tmp_dir):
    """Copy ragged.md to a temp dir for modification tests."""
    src = os.path.join(os.path.dirname(__file__), "fixtures", "ragged.md")
    dst = os.path.join(tmp_dir, "ragged.md")
    shutil.copy2(src, dst)
    return dst


def run_raggedy(*args):
    """Run raggedy as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, "-m", "raggedy", *args],
        capture_output=True,
        text=True,
    )


class TestCheck:
    def test_check_exits_1_when_changes_needed(self, ragged_file):
        result = run_raggedy("--check", ragged_file)
        assert result.returncode == 1

    def test_check_exits_0_when_no_changes(self, ragged_file):
        # First fix the file
        run_raggedy(ragged_file)
        # Then check should pass
        result = run_raggedy("--check", ragged_file)
        assert result.returncode == 0

    def test_check_does_not_modify(self, ragged_file):
        with open(ragged_file) as f:
            before = f.read()
        run_raggedy("--check", ragged_file)
        with open(ragged_file) as f:
            after = f.read()
        assert before == after


class TestDiff:
    def test_diff_shows_changes(self, ragged_file):
        result = run_raggedy("--diff", ragged_file)
        assert result.returncode == 0
        assert "---" in result.stdout
        assert "+++" in result.stdout

    def test_diff_does_not_modify(self, ragged_file):
        with open(ragged_file) as f:
            before = f.read()
        run_raggedy("--diff", ragged_file)
        with open(ragged_file) as f:
            after = f.read()
        assert before == after


class TestInPlace:
    def test_edits_in_place(self, ragged_file):
        expected_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "expected.md"
        )
        with open(expected_path) as f:
            expected = f.read()

        run_raggedy(ragged_file)

        with open(ragged_file) as f:
            result = f.read()
        assert result == expected

    def test_backup(self, ragged_file):
        with open(ragged_file) as f:
            original = f.read()

        run_raggedy("-b", ragged_file)

        bak = ragged_file + ".bak"
        assert os.path.exists(bak)
        with open(bak) as f:
            assert f.read() == original

    def test_idempotent(self, ragged_file):
        """Running twice produces the same output."""
        run_raggedy(ragged_file)
        with open(ragged_file) as f:
            first = f.read()

        run_raggedy(ragged_file)
        with open(ragged_file) as f:
            second = f.read()

        assert first == second


class TestErrors:
    def test_missing_file(self):
        result = run_raggedy("--check", "/nonexistent/file.md")
        assert result.returncode == 2

    def test_no_args(self):
        result = run_raggedy()
        assert result.returncode == 2
