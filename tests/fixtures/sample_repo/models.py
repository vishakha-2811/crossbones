"""Core data structures for the sample fixture repository."""


class DataModel:
    """Container for a single logical record with validation.

    Attributes are stored in a plain dictionary internally; access via
    properties so invalid values raise immediately instead of hiding
    problems until render time.
    """

    def __init__(self, identifier, fields=None):
        self.identifier = identifier
        self.fields = fields or {}

    def get(self, key, default=None):
        return self.fields.get(key, default)

    def set(self, key, value):
        self.fields[key] = value
        return self


class ResultStore:
    """In-memory sink that keeps outcomes grouped by label.

    Append any object; retrieval supports both a full dump and a
    filtered view keyed by label, so consumers never iterate raw
    internal state.
    """

    def __init__(self):
        self._groups = {}

    def add(self, label, outcome):
        self._groups.setdefault(label, []).append(outcome)

    def by_label(self, label):
        return list(self._groups.get(label, []))

    def dump(self):
        return {label: list(items) for label, items in self._groups.items()}
