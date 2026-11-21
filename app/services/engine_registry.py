from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EngineStatus:
    name: str
    available: bool
    version: str | None = None
    note: str = ""


class EngineRegistry:
    """Registry for optional local engines. No engine is downloaded or launched yet."""

    def __init__(self):
        self._engines: dict[str, EngineStatus] = {}

    def register(self, status: EngineStatus) -> None:
        self._engines[status.name] = status

    def get(self, name: str) -> EngineStatus | None:
        return self._engines.get(name)

    def list_all(self) -> list[EngineStatus]:
        return list(self._engines.values())
