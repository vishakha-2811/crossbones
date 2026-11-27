import sys


def number_entries(entries):
    """Standard crossword numbering: row-major order of entry start cells."""
    starts = sorted({(e.row, e.col) for e in entries})
    return {cell: n for n, cell in enumerate(starts, start=1)}


def render(grid, entries, clues=None):
    if not grid:
        return "Empty grid."
    utf8 = (sys.stdout.encoding or "").lower().replace("-", "") == "utf8"
    empty = "·" if utf8 else "#"
    numbers = number_entries(entries)
    rows = [r for r, _ in grid]
    cols = [c for _, c in grid]

    lines = []
    for r in range(min(rows), max(rows) + 1):
        cells = []
        for c in range(min(cols), max(cols) + 1):
            if (r, c) in grid:
                label = str(numbers.get((r, c), ""))
                cells.append(label.rjust(2) + grid[(r, c)])
            else:
                cells.append("  " + empty)
        lines.append(" ".join(cells))
        lines.append("")

    def section(title, direction):
        out = [title]
        chosen = [e for e in entries if e.direction == direction]
        for e in sorted(chosen, key=lambda e: numbers[(e.row, e.col)]):
            n = numbers[(e.row, e.col)]
            clue = (clues or {}).get(e.answer, "")
            out.append(f"  {n}. {clue}  -> {e.answer}  ({e.file}:{e.line})")
        return out

    lines += section("ACROSS", "across") + [""] + section("DOWN", "down")
    return "\n".join(lines)