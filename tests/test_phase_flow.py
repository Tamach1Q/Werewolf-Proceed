from werewolf_gm.domain import DeathReason, Game, GamePhase, Role


def _build_sample_game() -> Game:
    game = Game()
    game.add_player("Wolf", Role.WEREWOLF)
    game.add_player("Seer", Role.SEER)
    game.add_player("Knight", Role.KNIGHT)
    game.add_player("Citizen", Role.CITIZEN)
    return game


def test_phase_flow_cycles_day_voting_night_subphases_day() -> None:
    game = Game()
    assert game.day == 1
    assert game.phase is GamePhase.DAY

    assert game.proceed_to_next_phase() is GamePhase.VOTING
    assert game.proceed_to_next_phase() is GamePhase.NIGHT_SEER
    assert game.proceed_to_next_phase() is GamePhase.NIGHT_MEDIUM
    assert game.proceed_to_next_phase() is GamePhase.NIGHT_KNIGHT
    assert game.proceed_to_next_phase() is GamePhase.NIGHT_WEREWOLF
    assert game.proceed_to_next_phase() is GamePhase.DAY
    assert game.day == 2


def test_finished_phase_does_not_advance() -> None:
    game = Game(phase=GamePhase.FINISHED, day=3)

    assert game.proceed_to_next_phase() is GamePhase.FINISHED
    assert game.day == 3


def test_night_resolution_kills_attacked_player_when_not_guarded() -> None:
    game = _build_sample_game()
    citizen = next(p for p in game.players if p.name == "Citizen")
    knight = next(p for p in game.players if p.name == "Knight")

    game.phase = GamePhase.NIGHT_KNIGHT
    game.set_guard_target(knight.id)
    game.proceed_to_next_phase()
    assert game.phase is GamePhase.NIGHT_WEREWOLF

    game.set_attack_target(citizen.id)
    game.proceed_to_next_phase()

    assert citizen.is_alive is False
    assert game.last_night_victim_id == citizen.id
    assert game.last_guard_target_id == knight.id
    assert game.last_attack_target_id == citizen.id
    assert game.guard_target_id is None
    assert game.attacked_player_id is None
    assert game.phase is GamePhase.DAY
    assert game.day == 2


def test_night_resolution_blocks_attack_when_guarded() -> None:
    game = _build_sample_game()
    citizen = next(p for p in game.players if p.name == "Citizen")

    game.phase = GamePhase.NIGHT_KNIGHT
    game.set_guard_target(citizen.id)
    game.proceed_to_next_phase()

    game.set_attack_target(citizen.id)
    game.proceed_to_next_phase()

    assert citizen.is_alive is True
    assert game.last_night_victim_id is None
    assert game.last_guard_target_id == citizen.id
    assert game.last_attack_target_id == citizen.id
    assert game.phase is GamePhase.DAY
    assert game.day == 2


def test_get_executed_player_on_day_returns_player() -> None:
    game = _build_sample_game()
    citizen = next(p for p in game.players if p.name == "Citizen")

    game.kill_player(citizen.id, DeathReason.EXECUTED)
    executed = game.get_executed_player_on_day(game.day)

    assert executed is not None
    assert executed.id == citizen.id


def test_remove_player_deletes_from_list() -> None:
    game = _build_sample_game()
    seer = next(p for p in game.players if p.name == "Seer")

    game.remove_player(seer.id)

    assert all(p.id != seer.id for p in game.players)
