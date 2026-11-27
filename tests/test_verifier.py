"""Unit tests for verifier.verify_grid — symbol, grid-word, clue-containment, and crossing checks.

Covers tasks 11.1, 11.2, 6.3, and 6.4.
"""

import unittest

from placer import Entry
from verifier import verify_grid


def make_entry(answer, direction, row, col, name=None, kind="function",
               file="fake.py", line=1):
    return Entry(
        answer=answer,
        name=name or answer.lower(),
        kind=kind,
        file=file,
        line=line,
        direction=direction,
        row=row,
        col=col,
    )


class TestSymbolCheck(unittest.TestCase):
    """P4(a): an answer absent from the symbol set fails 'symbol'."""

    def test_p4_symbol_check(self):
        grid = {(0, i): ch for i, ch in enumerate("HELLOWORLD")}
        entry = make_entry("HELLOWORLD", "across", 0, 0)
        failures = verify_grid(grid, [entry], {"SOMEOTHER"}, {})
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "symbol")
        self.assertIn("HELLOWORLD", failures[0].detail)

    def test_valid_symbol_passes_symbol_check(self):
        grid = {(0, i): ch for i, ch in enumerate("HELLOWORLD")}
        entry = make_entry("HELLOWORLD", "across", 0, 0)
        failures = verify_grid(grid, [entry], {"HELLOWORLD"}, {})
        self.assertEqual(failures, [])


class TestGridWordCheck(unittest.TestCase):
    """P4(b): grid letters not spelling the answer fail 'grid-word'."""

    def test_p4_grid_word_check_mismatched_letters(self):
        grid = {(0, i): ch for i, ch in enumerate("XYZABC")}
        entry = make_entry("ABCDEF", "across", 0, 0)
        failures = verify_grid(grid, [entry], {"ABCDEF"}, {})
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "grid-word")
        self.assertIn("ABCDEF", failures[0].detail)

    def test_p4_grid_word_check_missing_cells(self):
        # Empty grid: every cell lookup returns "" — word can't match.
        entry = make_entry("ABCDEF", "across", 0, 0)
        failures = verify_grid({}, [entry], {"ABCDEF"}, {})
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "grid-word")

    def test_across_entry_matching_grid_passes(self):
        grid = {(0, i): ch for i, ch in enumerate("ABCDEF")}
        entry = make_entry("ABCDEF", "across", 0, 0)
        failures = verify_grid(grid, [entry], {"ABCDEF"}, {})
        self.assertEqual(failures, [])

    def test_down_entry_matching_grid_passes(self):
        grid = {(i, 0): ch for i, ch in enumerate("ABCDEF")}
        entry = make_entry("ABCDEF", "down", 0, 0)
        failures = verify_grid(grid, [entry], {"ABCDEF"}, {})
        self.assertEqual(failures, [])

    def test_down_entry_wrong_cells_fails(self):
        grid = {(i, 0): ch for i, ch in enumerate("XYZ")}
        entry = make_entry("ABCDEF", "down", 0, 0)
        failures = verify_grid(grid, [entry], {"ABCDEF"}, {})
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "grid-word")

    def test_entry_failing_both_checks_reports_both(self):
        grid = {(0, i): ch for i, ch in enumerate("XYZ")}
        entry = make_entry("ABCDEF", "across", 0, 0)
        failures = verify_grid(grid, [entry], {"OTHER"}, {})
        self.assertEqual(len(failures), 2)
        self.assertEqual({f.check for f in failures}, {"symbol", "grid-word"})


class TestClueContainmentCheck(unittest.TestCase):
    """P4(c): a clue containing its own answer fails 'clue-containment'."""

    def _entry_and_grid(self, answer="ABCDEF"):
        grid = {(0, i): ch for i, ch in enumerate(answer)}
        entry = make_entry(answer, "across", 0, 0)
        return grid, entry

    def test_clue_containing_answer_fails(self):
        grid, entry = self._entry_and_grid()
        clues = {"ABCDEF": "Call abcdef to parse the tree."}
        failures = verify_grid(grid, [entry], {"ABCDEF"}, clues)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "clue-containment")
        self.assertIn("ABCDEF", failures[0].detail)

    def test_clue_case_insensitive_match_fails(self):
        grid, entry = self._entry_and_grid()
        clues = {"ABCDEF": "helper AbCdEf function"}
        failures = verify_grid(grid, [entry], {"ABCDEF"}, clues)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "clue-containment")

    def test_clue_without_answer_passes(self):
        grid, entry = self._entry_and_grid()
        clues = {"ABCDEF": "Parses the configuration tree."}
        failures = verify_grid(grid, [entry], {"ABCDEF"}, clues)
        self.assertEqual(failures, [])

    def test_no_clue_skips_check(self):
        # Requirement 4.7: no clue available -> check skipped entirely.
        grid, entry = self._entry_and_grid()
        failures = verify_grid(grid, [entry], {"ABCDEF"}, {})
        self.assertEqual(failures, [])

    def test_empty_clue_string_skips_check(self):
        # Requirement 4.7: empty clue is treated as missing.
        grid, entry = self._entry_and_grid()
        clues = {"ABCDEF": ""}
        failures = verify_grid(grid, [entry], {"ABCDEF"}, clues)
        self.assertEqual(failures, [])

    def test_clue_for_other_answer_not_used(self):
        grid, entry = self._entry_and_grid()
        clues = {"OTHER": "mentions abcdef directly"}
        failures = verify_grid(grid, [entry], {"ABCDEF"}, clues)
        self.assertEqual(failures, [])

    def test_doc_fallback_containment_fails_when_doc_contains_answer(self):
        # Requirement 4.3 / 4.5: no cached clue, symbols is a dict with a doc
        # that contains the answer -> clue-containment failure.
        grid, entry = self._entry_and_grid("ABCDEF")
        symbols = {
            "ABCDEF": {
                "answer": "ABCDEF",
                "name": "abcdef",
                "kind": "function",
                "file": "fake.py",
                "line": 1,
                "doc": "Calls abcdef to process data.",
            }
        }
        failures = verify_grid(grid, [entry], symbols, {})
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].check, "clue-containment")

    def test_doc_fallback_no_failure_when_no_doc(self):
        # Requirement 4.7: symbols is a dict but doc is empty -> check skipped.
        grid, entry = self._entry_and_grid("ABCDEF")
        symbols = {
            "ABCDEF": {
                "answer": "ABCDEF",
                "name": "abcdef",
                "kind": "function",
                "file": "fake.py",
                "line": 1,
                "doc": "",
            }
        }
        failures = verify_grid(grid, [entry], symbols, {})
        self.assertEqual(failures, [])

    def test_other_failure_kinds_still_reported_with_bad_clue(self):
        # Bad grid + bad symbol + bad clue -> all three failures reported.
        grid = {(0, i): ch for i, ch in enumerate("XYZ")}
        entry = make_entry("ABCDEF", "across", 0, 0)
        clues = {"ABCDEF": "call abcdef here"}
        failures = verify_grid(grid, [entry], {"OTHER"}, clues)
        self.assertEqual(len(failures), 3)
        self.assertEqual(
            {f.check for f in failures},
            {"symbol", "grid-word", "clue-containment"},
        )


class TestCrossingCheck(unittest.TestCase):
    """Requirement 4.4: crossing conflicts are detected."""

    def _build_cross(self, across_word, down_word, cross_row, cross_col):
        """Helper: place *across_word* starting at (cross_row, 0) and
        *down_word* starting at (0, cross_col), so they intersect at
        (cross_row, cross_col).  Returns (grid, entries, symbols).
        """
        # Build a minimal but consistent grid.
        grid = {}
        for i, ch in enumerate(across_word):
            grid[(cross_row, i)] = ch
        for i, ch in enumerate(down_word):
            grid[(i, cross_col)] = ch  # may overwrite; caller must keep words consistent

        across_entry = make_entry(across_word, "across", cross_row, 0)
        down_entry = make_entry(down_word, "down", 0, cross_col)
        entries = [across_entry, down_entry]
        symbols = {across_word, down_word}
        return grid, entries, symbols

    def test_consistent_crossing_no_crossing_failure(self):
        # "ABCD" across row 2 starting col 0; "XBC" down col 1 starting row 1.
        # Intersection at (2,1): across letter 'B', down letter 'B' — consistent.
        across = make_entry("ABCD", "across", 2, 0)
        down   = make_entry("XBC", "down", 1, 1)
        # Cell (2,1): across[1]='B', down[1]='B'
        grid = {}
        for i, ch in enumerate("ABCD"):
            grid[(2, i)] = ch
        for i, ch in enumerate("XBC"):
            grid[(1 + i, 1)] = ch
        failures = verify_grid(grid, [across, down], {"ABCD", "XBC"}, {})
        self.assertEqual(failures, [])

    def test_crossing_conflict_detected(self):
        # "ABCD" across row 0; "ZXYZ" down col 1 — intersection at (0,1).
        # Across wants 'B' there; down wants 'X' — conflict.
        across = make_entry("ABCD", "across", 0, 0)
        down   = make_entry("ZXYZ", "down", 0, 1)
        # Build grid with across letters (down letter at (0,1) would be 'Z', but
        # we write the across letter 'B' so the grid itself is consistent with
        # across — the verifier detects the logical conflict between entries).
        grid = {(0, i): ch for i, ch in enumerate("ABCD")}
        for i, ch in enumerate("ZXYZ"):
            if (i, 1) not in grid:
                grid[(i, 1)] = ch
        failures = verify_grid(grid, [across, down], {"ABCD", "ZXYZ"}, {})
        crossing_failures = [f for f in failures if f.check == "crossing"]
        self.assertGreater(len(crossing_failures), 0)
        # At least one failure names the conflicting cell (0,1).
        self.assertTrue(
            any("(0,1)" in f.detail for f in crossing_failures),
            crossing_failures,
        )

    def test_no_crossing_failure_when_entries_do_not_share_cell(self):
        # Two parallel-ish entries that do not intersect at all.
        across1 = make_entry("HELLO", "across", 0, 0)
        across2 = make_entry("WORLD", "across", 2, 0)
        grid = {}
        for i, ch in enumerate("HELLO"):
            grid[(0, i)] = ch
        for i, ch in enumerate("WORLD"):
            grid[(2, i)] = ch
        failures = verify_grid(grid, [across1, across2], {"HELLO", "WORLD"}, {})
        self.assertEqual([f for f in failures if f.check == "crossing"], [])

    def test_crossing_failure_references_correct_entry(self):
        # Conflict: across "ACE" row 0; down "BXY" col 1 (expects 'B' at (0,1),
        # but across has 'C').
        across = make_entry("ACE", "across", 0, 0)
        down   = make_entry("BXY", "down", 0, 1)
        grid = {(0, i): ch for i, ch in enumerate("ACE")}
        for i, ch in enumerate("BXY"):
            if (i, 1) not in grid:
                grid[(i, 1)] = ch
        failures = verify_grid(grid, [across, down], {"ACE", "BXY"}, {})
        crossing = [f for f in failures if f.check == "crossing"]
        self.assertGreater(len(crossing), 0)
        # Every crossing failure must belong to one of our two entries.
        for f in crossing:
            self.assertIn(f.entry.answer, {"ACE", "BXY"})


if __name__ == "__main__":
    unittest.main()
