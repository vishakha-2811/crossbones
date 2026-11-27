import placer
import verifier
from extractor import extract_symbols
import crossbones
import sys

repo = sys.argv[1]
symbols = extract_symbols(repo)
symbol_map = {s["answer"]: s for s in symbols}
grid, entries = placer.build_grid(crossbones.select_candidates(symbols))

print("1) Honest puzzle:")
print("   failures:", len(verifier.verify_grid(grid, entries, symbol_map, {})))

# Invent a word that is NOT in the repo, and force it into the puzzle
fake = entries[0]
fake.answer = "BANANASPLIT"
for i, ch in enumerate(fake.answer):
    key = (fake.row, fake.col + i) if fake.direction == "across" else (fake.row + i, fake.col)
    grid[key] = ch

print("\n2) After sneaking in a made-up answer 'BANANASPLIT':")
failures = verifier.verify_grid(grid, entries, symbol_map, {})
fake_fails = [f for f in failures if f.entry.answer == "BANANASPLIT"]
checks = sorted({f.check for f in fake_fails})
print(f"   REJECTED: BANANASPLIT is not a real symbol in this repo")
print(f"   checks failed: {', '.join(checks)}")
print(f"   total problems caught: {len(failures)}")