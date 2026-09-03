"""Puerto de reloj. Permite que los tests fijen `now` sin parchear datetime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class ClockPort(ABC):
    @abstractmethod
    def now(self) -> datetime:
        """Instante actual, siempre con tzinfo."""
