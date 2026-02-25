from __future__ import annotations

from dataclasses import dataclass, field

from werewolf_gm.domain import FirstDaySeerRule, Game, GamePhase, GameRules

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
    setup_day_seconds: int = 180
    setup_night_seconds: int = 90
    setup_first_day_seer: FirstDaySeerRule = FirstDaySeerRule.FREE_SELECT
    is_rpp_mode: bool = False
    rpp_selected_ids: set[str] = field(default_factory=set)

    show_result_overlay: bool = False
    last_action_result: bool | None = None

    timer_seconds: int = 0
    timer_running: bool = True
    reveal: RevealState | None = None
    last_morning_result: str | None = None

    def __post_init__(self) -> None:
        self.sync_setup_rules_from_game()
        self.reset_timer_for_current_phase()

    def reset_game(self) -> None:
        self.game = Game()
        self.apply_setup_rules_to_game()
        self.selected_tab = GameTab.PROGRESS
        self.logs.clear()
        self.reset_rpp_mode()

        self.show_result_overlay = False
        self.last_action_result = None
        
        self.timer_running = True
        self.reveal = None
        self.last_morning_result = None
        self.reset_timer_for_current_phase()

    @property
    def can_start_game(self) -> bool:
        return len(self.game.players) >= MIN_PLAYERS_TO_START

    def reset_timer_for_current_phase(self) -> None:
        self.timer_seconds = self._initial_seconds_for_phase(self.game.phase)

    def reset_rpp_mode(self) -> None:
        self.is_rpp_mode = False
        self.rpp_selected_ids.clear()

    def sync_setup_rules_from_game(self) -> None:
        self.setup_day_seconds = self.game.rules.day_seconds
        self.setup_night_seconds = self.game.rules.night_seconds
        self.setup_first_day_seer = self.game.rules.first_day_seer

    def apply_setup_rules_to_game(self) -> None:
        self.game.rules = GameRules(
            day_seconds=self.setup_day_seconds,
            night_seconds=self.setup_night_seconds,
            first_day_seer=self.setup_first_day_seer,
        )

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

    def _initial_seconds_for_phase(self, phase: GamePhase) -> int:
        if phase in {GamePhase.DAY, GamePhase.VOTING}:
            return self.game.rules.day_seconds
        if phase in {
            GamePhase.NIGHT_SEER,
            GamePhase.NIGHT_MEDIUM,
            GamePhase.NIGHT_KNIGHT,
            GamePhase.NIGHT_WEREWOLF,
        }:
            return self.game.rules.night_seconds
        if phase is GamePhase.FINISHED:
            return 0
        return self.game.rules.day_seconds
