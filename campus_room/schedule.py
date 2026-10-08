from datetime import datetime


class Schedule:
    """A closed-open time window: [start, end). Composition target for Booking."""

    def __init__(self, start: datetime, end: datetime):
        if end <= start:
            raise ValueError("Schedule end must be after start.")
        self._start = start
        self._end = end

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self._end

    def overlaps(self, other: "Schedule") -> bool:
        """True when two intervals share any time.

        [A, B) overlaps [C, D) iff A < D and C < B.
        Back-to-back bookings (one ends when the next starts) do not conflict.
        """
        return self._start < other._end and other._start < self._end

    def __repr__(self) -> str:
        return f"{self._start:%Y-%m-%d %H:%M}–{self._end:%H:%M}"
