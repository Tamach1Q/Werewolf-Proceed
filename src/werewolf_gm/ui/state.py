from __future__ import annotations

from dataclasses import dataclass, field

from werewolf_gm.domain import Game

from .tabs import GameTab


@dataclass(slots=True)
class AppState:
    game: Game = field(default_factory=Game)
    selected_tab: GameTab = GameTab.PROGRESS
    logs: list[str] = field(default_factory=list)

    def reset_game(self) -> None:
        self.game = Game()
        self.selected_tab = GameTab.PROGRESS
        self.logs.clear()
