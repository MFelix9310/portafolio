"""Intervalo de fechas, abierto por la derecha cuando el puesto sigue vigente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DateRange:
    start: date
    end: date | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end < self.start:
            raise ValueError(f"end ({self.end}) anterior a start ({self.start})")

    @property
    def is_open(self) -> bool:
        return self.end is None

    def contains(self, moment: date) -> bool:
        if moment < self.start:
            return False
        return self.end is None or moment <= self.end

    def overlaps(self, other: "DateRange") -> bool:
        left_end = self.end or date.max
        right_end = other.end or date.max
        return self.start <= right_end and other.start <= left_end
