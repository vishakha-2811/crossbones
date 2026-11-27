import json
import os
import sys

import clues
import html_export
import placer
import renderer
import verifier
from extractor import extract_symbols


def select_candidates(symbols, limit=25):
    usable = []
    for s in symbols:
        answer = s["answer"]
        if not (answer.isalpha() and 4 <= len(answer) <= 15):
            continue
        doc = s.get("doc") or ""
        if answer.lower() in doc.lower():
            continue  # its own docstring would give the answer away
        usable.append(s)
    usable.sort(key=lambda s: (not s.get("doc"), -len(s["answer"])))
    seen, chosen = set(), []
    for s in usable:
        if s["answer"] not in seen:
            seen.add(s["answer"])
            chosen.append(s)
    return chosen[:limit]


def load_clues(path="clues_cache.json"):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Warning: clues_cache.json is malformed, ignoring it.", file=sys.stderr)
        return {}


def main(argv):
    if len(argv) < 2 or not os.path.isdir(argv[1]):
        print("Usage: python crossbones.py <repo_path>", file=sys.stderr)
        return 1

    symbols = extract_symbols(argv[1])
    if not symbols:
        print("No symbols found.")
        return 0

    candidates = select_candidates(symbols)
    grid, entries = placer.build_grid(candidates)
    if not entries:
        print("No symbols found.")
        return 0

    symbol_map = {s["answer"]: s for s in symbols}
    clue_map = clues.get_clues(entries, symbol_map)
    failures = verifier.verify_grid(grid, entries, symbol_map, clue_map)
    for f in failures:
        print(f"VERIFY FAILED: {f.entry.answer} "
              f"({f.entry.file}:{f.entry.line}) check={f.check}")
    if not failures:
        print(f"Verified: all {len(entries)} entries are real symbols.\n")

    print(renderer.render(grid, entries, clue_map))
    path = html_export.write_html(grid, entries, clue_map)
    print(f"\nPlayable crossword written to {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))