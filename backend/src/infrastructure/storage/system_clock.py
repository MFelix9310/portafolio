"""Reloj del sistema."""

from __future__ import annotations

from datetime import UTC, datetime

from ...application.ports.clock import ClockPort


class SystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(UTC)
