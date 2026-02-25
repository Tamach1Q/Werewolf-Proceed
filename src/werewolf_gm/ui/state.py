from __future__ import annotations

from dataclasses import dataclass, field

from werewolf_gm.domain import Game, GamePhase

from .tabs import GameTab

MIN_PLAYERS_TO_START = 4


@dataclass(slots=True)
class RevealState:
    role_label: str
    target_name: str
    result_text: str
    background_color: str


@dataclass(slots=True)
class AppState:
    game: Game = field(default_factory=Game)
    selected_tab: GameTab = GameTab.PROGRESS
    logs: list[str] = field(default_factory=list)
    timer_seconds: int = 0
    timer_running: bool = True
    reveal: RevealState | None = None

    def __post_init__(self) -> None:
        self.reset_timer_for_current_phase()

    def reset_game(self) -> None:
        self.game = Game()
        self.selected_tab = GameTab.PROGRESS
        self.logs.clear()
        self.timer_running = True
        self.reveal = None
        self.reset_timer_for_current_phase()

    @property
    def can_start_game(self) -> bool:
        return len(self.game.players) >= MIN_PLAYERS_TO_START

    def reset_timer_for_current_phase(self) -> None:
        self.timer_seconds = self._initial_seconds_for_phase(self.game.phase)

    def adjust_timer(self, delta_seconds: int) -> None:
        self.timer_seconds = max(0, self.timer_seconds + delta_seconds)

    def toggle_timer_running(self) -> None:
        self.timer_running = not self.timer_running

    def format_timer(self) -> str:
        minutes, seconds = divmod(self.timer_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def open_reveal(self, *, role_label: str, target_name: str, is_werewolf: bool) -> None:
        self.reveal = RevealState(
            role_label=role_label,
            target_name=target_name,
            result_text="人狼である" if is_werewolf else "人狼ではない",
            background_color="#C62828" if is_werewolf else "#1565C0",
        )

    def close_reveal(self) -> None:
        self.reveal = None

    @staticmethod
    def _initial_seconds_for_phase(phase: GamePhase) -> int:
        if phase is GamePhase.DAY:
            return 180
        if phase is GamePhase.VOTING:
            return 90
        if phase in {
            GamePhase.NIGHT_SEER,
            GamePhase.NIGHT_MEDIUM,
            GamePhase.NIGHT_KNIGHT,
            GamePhase.NIGHT_WEREWOLF,
        }:
            return 90
        if phase is GamePhase.FINISHED:
            return 0
        return 180
