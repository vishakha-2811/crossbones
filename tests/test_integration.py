"""Integration tests for the Crossbones end-to-end pipeline.

Covers tasks 12.1 (P5 round-trip: placer → verifier) and
12.2 (P5 CLI end-to-end: crossbones.main).

Fixture repo: tests/fixtures/sample_repo
  Contains utils.py and models.py with 13 usable symbols.
"""

import contextlib
import io
import os
import re
import unittest
import unittest.mock

import placer
import verifier
import crossbones
from extractor import extract_symbols
from crossbones import select_candidates

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_repo")


class TestP5PlacerOutputAccepted(unittest.TestCase):
    """Task 12.1 — P5 round-trip: placer output is accepted by verifier with
    zero failures when run against the fixture repo.
    """

    def test_p5_placer_output_accepted(self):
        symbols = extract_symbols(FIXTURE_PATH)
        candidates = select_candidates(symbols)
        grid, entries = placer.build_grid(candidates, seed=0)

        # The fixture must yield a real crossword (at least 2 placed entries).
        self.assertGreaterEqual(
            len(entries), 2,
            f"Expected at least 2 entries, got {len(entries)}: {entries}",
        )

        symbol_map = {s["answer"]: s for s in symbols}
        failures = verifier.verify_grid(grid, entries, symbol_map, {})

        # P5: every placed entry must pass all applicable checks.
        self.assertEqual(
            failures, [],
            f"verifier.verify_grid reported failures:\n"
            + "\n".join(f"  {f}" for f in failures),
        )


class TestP5CliEndToEnd(unittest.TestCase):
    """Task 12.2 — P5 CLI end-to-end: crossbones.main exits 0 and prints a
    complete crossword (ACROSS/DOWN sections with file:line origins).
    """

    def test_p5_cli_end_to_end(self):
        fixture_abs = os.path.abspath(FIXTURE_PATH)
        argv = ["crossbones.py", fixture_abs]

        buf = io.StringIO()
        with (
            unittest.mock.patch(
                "crossbones.clues.get_clues", return_value={}
            ),
            unittest.mock.patch(
                "crossbones.html_export.write_html", return_value="x"
            ),
            contextlib.redirect_stdout(buf),
        ):
            rc = crossbones.main(argv)

        output = buf.getvalue()

        # Must exit cleanly.
        self.assertEqual(rc, 0, f"crossbones.main returned {rc!r}")

        # Must contain ACROSS and DOWN section headers.
        self.assertIn(
            "ACROSS", output,
            "Output missing 'ACROSS' section",
        )
        self.assertIn(
            "DOWN", output,
            "Output missing 'DOWN' section",
        )

        # Every clue line must carry a file:line origin (e.g. "utils.py:4").
        # The renderer emits lines like:  "  1.   -> PARSECONFIG  (utils.py:4)"
        # We check that ".py:" appears in the output at least once.
        self.assertRegex(
            output,
            r"\.py:\d+",
            "Output does not contain any 'file.py:line' origin reference",
        )


if __name__ == "__main__":
    unittest.main()
