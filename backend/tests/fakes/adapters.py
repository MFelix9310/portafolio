"""Fakes de los puertos de aplicacion: reloj, storage y revalidacion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.application.ports.clock import ClockPort
from src.application.ports.media_storage import MediaStoragePort, UploadTicket
from src.application.ports.revalidation import (
    FrontendRevalidationPort,
    RevalidationResult,
)

FIXED_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


class FixedClock(ClockPort):
    def __init__(self, moment: datetime = FIXED_NOW) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


class FakeMediaStorage(MediaStoragePort):
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.issued: list[str] = []

    async def create_upload_url(self, filename: str, content_type: str) -> UploadTicket:
        path = f"uploads/{filename}"
        self.issued.append(path)
        return UploadTicket(
            upload_url=f"https://storage.test/upload/{path}",
            storage_path=path,
            public_url=self.public_url(path),
            expires_at=FIXED_NOW + timedelta(minutes=10),
            token="fake-token",
        )

    def public_url(self, storage_path: str) -> str:
        return f"https://storage.test/object/public/media/{storage_path}"

    async def delete(self, storage_path: str) -> bool:
        self.deleted.append(storage_path)
        return True


class FakeRevalidation(FrontendRevalidationPort):
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    async def revalidate(self, paths: tuple[str, ...]) -> RevalidationResult:
        self.calls.append(paths)
        return RevalidationResult(requested_paths=paths, accepted=True)
