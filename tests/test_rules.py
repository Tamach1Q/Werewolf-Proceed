from werewolf_gm.domain import FirstDaySeerRule, Game, GamePhase
from werewolf_gm.ui.state import AppState


def test_game_has_default_rules() -> None:
    game = Game()

    assert game.rules.day_seconds == 180
    assert game.rules.night_seconds == 90
    assert game.rules.first_day_seer is FirstDaySeerRule.FREE_SELECT


def test_app_state_timer_uses_game_rules() -> None:
    state = AppState()
    state.game.rules.day_seconds = 240
    state.game.rules.night_seconds = 75

    state.game.phase = GamePhase.DAY
    state.reset_timer_for_current_phase()
    assert state.timer_seconds == 240

    state.game.phase = GamePhase.VOTING
    state.reset_timer_for_current_phase()
    assert state.timer_seconds == 240

    state.game.phase = GamePhase.NIGHT_SEER
    state.reset_timer_for_current_phase()
    assert state.timer_seconds == 75


def test_app_state_apply_setup_rules_to_game() -> None:
    state = AppState()
    state.setup_day_seconds = 300
    state.setup_night_seconds = 120
    state.setup_first_day_seer = FirstDaySeerRule.NONE

    state.apply_setup_rules_to_game()

    assert state.game.rules.day_seconds == 300
    assert state.game.rules.night_seconds == 120
    assert state.game.rules.first_day_seer is FirstDaySeerRule.NONE
