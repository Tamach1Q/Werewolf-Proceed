from __future__ import annotations

from enum import Enum


class Team(str, Enum):
    VILLAGER = "villager"
    WEREWOLF = "werewolf"


class VictoryState(str, Enum):
    ONGOING = "ongoing"
    VILLAGER_WIN = "villager_win"
    WEREWOLF_WIN = "werewolf_win"


class Role(str, Enum):
    CITIZEN = "citizen"
    WEREWOLF = "werewolf"
    MADMAN = "madman"
    SEER = "seer"
    KNIGHT = "knight"
    MEDIUM = "medium"

    @property
    def team(self) -> Team:
        if self in {Role.WEREWOLF, Role.MADMAN}:
            return Team.WEREWOLF
        return Team.VILLAGER

    @property
    def is_actual_werewolf(self) -> bool:
        return self is Role.WEREWOLF


class GamePhase(str, Enum):
    SETUP = "setup"
    DAY = "day"
    VOTING = "voting"
    NIGHT_SEER = "night_seer"
    NIGHT_MEDIUM = "night_medium"
    NIGHT_KNIGHT = "night_knight"
    NIGHT_WEREWOLF = "night_werewolf"
    FINISHED = "finished"


class DeathReason(str, Enum):
    EXECUTED = "executed"
    ATTACKED = "attacked"
    OTHER = "other"
