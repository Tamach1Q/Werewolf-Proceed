from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .enums import DeathReason, Role, Team


@dataclass(slots=True)
class Player:
    name: str
    role: Role
    id: str = field(default_factory=lambda: str(uuid4()))
    is_alive: bool = True
    death_reason: DeathReason | None = None
    death_day: int | None = None

    @property
    def team(self) -> Team:
        return self.role.team

    @property
    def is_werewolf(self) -> bool:
        return self.role.is_actual_werewolf

    def kill(self, reason: DeathReason) -> None:
        self.is_alive = False
        self.death_reason = reason
