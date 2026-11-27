"""Shared helpers for the sample fixture repository."""


def parse_config(raw):
    """Turn a raw mapping into a validated settings dictionary.

    Missing keys are filled with sensible defaults, unknown keys are
    dropped, and values are coerced to their expected types.
    """
    defaults = {"host": "localhost", "port": 8080, "debug": False}
    config = dict(defaults)
    for key, value in (raw or {}).items():
        if key in defaults:
            config[key] = value
    return config


def load_data(path):
    """Read rows from a source and return them as a list of dicts.

    Blank lines and comment lines starting with '#' are skipped; every
    remaining line is split on commas into a record.
    """
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            rows.append(stripped.split(","))
    return rows


def save_result(payload, target):
    """Write a computed payload to the destination.

    The payload is serialised as text lines so the output remains
    human-readable and easy to diff.
    """
    lines = [f"{key}={value}" for key, value in payload.items()]
    with open(target, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


class BaseParser:
    """Abstract reader that normalises input before dispatching.

    Subclasses override ``handle`` to consume one record at a time; the
    base class takes care of iteration, error isolation, and counting.
    """

    def __init__(self):
        self.records = 0
        self.errors = 0

    def handle(self, record):
        raise NotImplementedError

    def parse(self, items):
        results = []
        for item in items:
            try:
                results.append(self.handle(item))
                self.records += 1
            except ValueError:
                self.errors += 1
        return results
