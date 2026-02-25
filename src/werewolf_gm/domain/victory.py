from __future__ import annotations

from dataclasses import dataclass

from .enums import Team, VictoryState


@dataclass(slots=True, frozen=True)
class VictoryResult:
    state: VictoryState
    winner: Team | None
    reason: str


class VictoryJudge:
    """Core victory judgment independent from UI framework."""

    @staticmethod
    def evaluate(*, alive_werewolves: int, alive_non_werewolves: int) -> VictoryResult:
        if alive_werewolves == 0:
            return VictoryResult(
                state=VictoryState.VILLAGER_WIN,
                winner=Team.VILLAGER,
                reason="All werewolves are eliminated.",
            )

        if alive_werewolves >= alive_non_werewolves:
            return VictoryResult(
                state=VictoryState.WEREWOLF_WIN,
                winner=Team.WEREWOLF,
                reason="Werewolves reached parity or majority against non-werewolves.",
            )

        return VictoryResult(
            state=VictoryState.ONGOING,
            winner=None,
            reason="The game continues.",
        )
