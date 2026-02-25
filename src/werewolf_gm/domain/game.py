from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable

from .enums import DeathReason, FirstDaySeerRule, GamePhase, Role, VictoryState
from .player import Player
from .victory import VictoryJudge, VictoryResult


@dataclass(slots=True)
class GameRules:
    day_seconds: int = 180
    night_seconds: int = 90
    first_day_seer: FirstDaySeerRule = FirstDaySeerRule.FREE_SELECT


@dataclass(slots=True)
class Game:
    players: list[Player] = field(default_factory=list)
    phase: GamePhase = GamePhase.DAY
    day: int = 1
    rules: GameRules = field(default_factory=GameRules)
    victory: VictoryResult = field(
        default_factory=lambda: VictoryResult(
            state=VictoryState.ONGOING,
            winner=None,
            reason="Game not evaluated yet.",
        )
    )
    seer_target_id: str | None = None
    medium_target_id: str | None = None
    guard_target_id: str | None = None
    attacked_player_id: str | None = None
    last_executed_player_id: str | None = None
    last_night_victim_id: str | None = None
    last_guard_target_id: str | None = None
    last_attack_target_id: str | None = None
    first_day_white_target_id: str | None = None

    def add_player(self, name: str, role: Role) -> Player:
        if any(p.name == name for p in self.players):
            raise ValueError(f"Player name already exists: {name}")
        player = Player(name=name, role=role)
        self.players.append(player)
        return player

    def remove_player(self, player_id: str) -> None:
        for idx, player in enumerate(self.players):
            if player.id == player_id:
                self.players.pop(idx)
                self._clear_player_reference(player_id)
                return
        raise ValueError(f"Player not found: {player_id}")

    def start_game(self) -> None:
        self.day = 0
        self.phase = GamePhase.NIGHT_SEER
        self.last_executed_player_id = None
        self.last_night_victim_id = None
        self.last_guard_target_id = None
        self.last_attack_target_id = None
        self.first_day_white_target_id = None
        if self.rules.first_day_seer is FirstDaySeerRule.RANDOM_WHITE:
            candidates = [
                player
                for player in self.players
                if player.role is not Role.WEREWOLF and player.role is not Role.SEER
            ]
            if candidates:
                self.first_day_white_target_id = random.choice(candidates).id
        self._reset_night_action_records()
        self.refresh_victory()

    def revert_to_previous_night_phase(self) -> bool:
        if self.phase is GamePhase.NIGHT_MEDIUM:
            self.phase = GamePhase.NIGHT_SEER
            self.seer_target_id = None
            return True

        if self.phase is GamePhase.NIGHT_KNIGHT:
            self.phase = GamePhase.NIGHT_MEDIUM
            self.medium_target_id = None
            return True

        if self.phase is GamePhase.NIGHT_WEREWOLF:
            self.attacked_player_id = None
            if self.day == 0:
                self.phase = GamePhase.NIGHT_SEER
                self.seer_target_id = None
                return True

            self.phase = GamePhase.NIGHT_KNIGHT
            self.guard_target_id = None
            return True

        return False

    def get_player(self, player_id: str) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player
        raise ValueError(f"Player not found: {player_id}")

    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.is_alive]

    def alive_players_by_role(self, role: Role) -> list[Player]:
        return [p for p in self.alive_players() if p.role is role]

    def has_alive_role(self, role: Role) -> bool:
        return any(True for _ in self.alive_players_by_role(role))

    def get_executed_player_on_day(self, day: int) -> Player | None:
        for player in self.players:
            if player.death_reason is DeathReason.EXECUTED and player.death_day == day:
                return player
        return None

    def kill_player(self, player_id: str, reason: DeathReason) -> None:
        player = self.get_player(player_id)
        if not player.is_alive:
            raise ValueError(f"Player already dead: {player.name}")

        player.kill(reason)
        player.death_day = self.day
        if reason is DeathReason.EXECUTED:
            self.last_executed_player_id = player_id
        self.refresh_victory()

    def set_seer_target(self, player_id: str) -> None:
        self.seer_target_id = self._require_alive_player(player_id).id

    def set_medium_target(self, player_id: str) -> None:
        self.medium_target_id = self.get_player(player_id).id

    def set_guard_target(self, player_id: str) -> None:
        self.guard_target_id = self._require_alive_player(player_id).id

    def set_attack_target(self, player_id: str) -> None:
        self.attacked_player_id = self._require_alive_player(player_id).id

    def resolve_night_actions(self) -> str | None:
        self.last_night_victim_id = None
        self.last_guard_target_id = self.guard_target_id
        self.last_attack_target_id = self.attacked_player_id

        if self.attacked_player_id and self.attacked_player_id != self.guard_target_id:
            target = self.get_player(self.attacked_player_id)
            if target.is_alive:
                self.kill_player(target.id, DeathReason.ATTACKED)
                self.last_night_victim_id = target.id

        self._reset_night_action_records()
        return self.last_night_victim_id

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

    def proceed_to_next_phase(self) -> GamePhase:
        if self.phase is GamePhase.FINISHED:
            return self.phase

        if self.phase is GamePhase.SETUP:
            self.phase = GamePhase.DAY
            self.day = max(self.day, 1)
            return self.phase

        if self.phase is GamePhase.DAY:
            self.phase = GamePhase.VOTING
            return self.phase

        if self.phase is GamePhase.VOTING:
            self.phase = GamePhase.NIGHT_SEER
            return self.phase

        if self.phase is GamePhase.NIGHT_SEER:
            if self.day == 0:
                self.phase = GamePhase.NIGHT_WEREWOLF
                return self.phase
            self.phase = GamePhase.NIGHT_MEDIUM
            return self.phase

        if self.phase is GamePhase.NIGHT_MEDIUM:
            self.phase = GamePhase.NIGHT_KNIGHT
            return self.phase

        if self.phase is GamePhase.NIGHT_KNIGHT:
            self.phase = GamePhase.NIGHT_WEREWOLF
            return self.phase

        # NIGHT_WEREWOLF -> next DAY
        if self.day == 0:
            self._reset_night_action_records()
            self.phase = GamePhase.DAY
            self.day = 1
            return self.phase

        self.resolve_night_actions()
        if self.phase is GamePhase.FINISHED:
            return self.phase

        self.phase = GamePhase.DAY
        self.day += 1
        return self.phase

    @staticmethod
    def _count_actual_werewolves(players: Iterable[Player]) -> int:
        return sum(1 for p in players if p.role is Role.WEREWOLF)

    def _require_alive_player(self, player_id: str) -> Player:
        player = self.get_player(player_id)
        if not player.is_alive:
            raise ValueError(f"Player is not alive: {player.name}")
        return player

    def _reset_night_action_records(self) -> None:
        self.seer_target_id = None
        self.medium_target_id = None
        self.guard_target_id = None
        self.attacked_player_id = None

    def _clear_player_reference(self, player_id: str) -> None:
        if self.seer_target_id == player_id:
            self.seer_target_id = None
        if self.medium_target_id == player_id:
            self.medium_target_id = None
        if self.guard_target_id == player_id:
            self.guard_target_id = None
        if self.attacked_player_id == player_id:
            self.attacked_player_id = None
        if self.last_executed_player_id == player_id:
            self.last_executed_player_id = None
        if self.last_night_victim_id == player_id:
            self.last_night_victim_id = None
        if self.last_guard_target_id == player_id:
            self.last_guard_target_id = None
        if self.last_attack_target_id == player_id:
            self.last_attack_target_id = None
        if self.first_day_white_target_id == player_id:
            self.first_day_white_target_id = None
