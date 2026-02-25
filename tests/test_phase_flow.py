from werewolf_gm.domain import Game, GamePhase


def test_phase_flow_cycles_day_voting_night_day() -> None:
    game = Game()
    assert game.day == 1
    assert game.phase is GamePhase.DAY

    assert game.proceed_to_next_phase() is GamePhase.VOTING
    assert game.day == 1

    assert game.proceed_to_next_phase() is GamePhase.NIGHT
    assert game.day == 1

    assert game.proceed_to_next_phase() is GamePhase.DAY
    assert game.day == 2


def test_finished_phase_does_not_advance() -> None:
    game = Game(phase=GamePhase.FINISHED, day=3)

    assert game.proceed_to_next_phase() is GamePhase.FINISHED
    assert game.day == 3
