from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .enums import DeathReason, GamePhase, Role, VictoryState
from .player import Player
from .victory import VictoryJudge, VictoryResult


@dataclass(slots=True)
class Game:
    players: list[Player] = field(default_factory=list)
    phase: GamePhase = GamePhase.SETUP
    day: int = 0
    victory: VictoryResult = field(
        default_factory=lambda: VictoryResult(
            state=VictoryState.ONGOING,
            winner=None,
            reason="Game not evaluated yet.",
        )
    )

    def add_player(self, name: str, role: Role) -> Player:
        if any(p.name == name for p in self.players):
            raise ValueError(f"Player name already exists: {name}")
        player = Player(name=name, role=role)
        self.players.append(player)
        return player

    def get_player(self, player_id: str) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player
        raise ValueError(f"Player not found: {player_id}")

    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.is_alive]

    def kill_player(self, player_id: str, reason: DeathReason) -> None:
        player = self.get_player(player_id)
        player.kill(reason)
        self.refresh_victory()

    def refresh_victory(self) -> VictoryResult:
        alive = self.alive_players()
        alive_werewolves = self._count_actual_werewolves(alive)
        alive_non_werewolves = len(alive) - alive_werewolves

        self.victory = VictoryJudge.evaluate(
            alive_werewolves=alive_werewolves,
            alive_non_werewolves=alive_non_werewolves,
        )

        if self.victory.state is not VictoryState.ONGOING:
            self.phase = GamePhase.FINISHED

        return self.victory

    @staticmethod
    def _count_actual_werewolves(players: Iterable[Player]) -> int:
        return sum(1 for p in players if p.role is Role.WEREWOLF)
