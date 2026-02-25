from werewolf_gm.domain import DeathReason, FirstDaySeerRule, Game, GamePhase, Role


def _build_sample_game() -> Game:
    game = Game()
    game.add_player("Wolf", Role.WEREWOLF)
    game.add_player("Seer", Role.SEER)
    game.add_player("Knight", Role.KNIGHT)
    game.add_player("Citizen", Role.CITIZEN)
    return game


def test_start_game_initializes_zero_night() -> None:
    game = Game()
    game.start_game()

    assert game.day == 0
    assert game.phase is GamePhase.NIGHT_SEER
    assert game.first_day_white_target_id is None


def test_start_game_sets_random_white_target() -> None:
    game = _build_sample_game()
    game.rules.first_day_seer = FirstDaySeerRule.RANDOM_WHITE
    game.start_game()

    assert game.first_day_white_target_id is not None
    target = game.get_player(game.first_day_white_target_id)
    assert target.role is not Role.WEREWOLF
    assert target.role is not Role.SEER


def test_start_game_random_white_target_can_be_none_when_no_candidate() -> None:
    game = Game()
    game.add_player("Wolf", Role.WEREWOLF)
    game.add_player("Seer", Role.SEER)
    game.rules.first_day_seer = FirstDaySeerRule.RANDOM_WHITE

    game.start_game()

    assert game.first_day_white_target_id is None


def test_phase_flow_skips_medium_and_knight_on_day_zero_night() -> None:
    game = _build_sample_game()
    game.start_game()

    assert game.proceed_to_next_phase() is GamePhase.NIGHT_WEREWOLF
    assert game.proceed_to_next_phase() is GamePhase.DAY
    assert game.day == 1


def test_phase_flow_cycles_day_voting_night_subphases_day() -> None:
    game = _build_sample_game()
    game.start_game()
    game.proceed_to_next_phase()
    game.proceed_to_next_phase()

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


def test_medium_target_accepts_executed_player() -> None:
    game = _build_sample_game()
    citizen = next(p for p in game.players if p.name == "Citizen")

    game.kill_player(citizen.id, DeathReason.EXECUTED)
    game.set_medium_target(citizen.id)

    assert game.medium_target_id == citizen.id


def test_remove_player_deletes_from_list() -> None:
    game = _build_sample_game()
    seer = next(p for p in game.players if p.name == "Seer")

    game.remove_player(seer.id)

    assert all(p.id != seer.id for p in game.players)


def test_revert_to_previous_night_phase_from_night_medium() -> None:
    game = _build_sample_game()
    game.phase = GamePhase.NIGHT_MEDIUM
    game.seer_target_id = "dummy-seer-target"

    reverted = game.revert_to_previous_night_phase()

    assert reverted is True
    assert game.phase is GamePhase.NIGHT_SEER
    assert game.seer_target_id is None


def test_revert_to_previous_night_phase_from_night_knight() -> None:
    game = _build_sample_game()
    game.phase = GamePhase.NIGHT_KNIGHT
    game.medium_target_id = "dummy-medium-target"

    reverted = game.revert_to_previous_night_phase()

    assert reverted is True
    assert game.phase is GamePhase.NIGHT_MEDIUM
    assert game.medium_target_id is None


def test_revert_to_previous_night_phase_from_night_werewolf_day_zero() -> None:
    game = _build_sample_game()
    game.day = 0
    game.phase = GamePhase.NIGHT_WEREWOLF
    game.seer_target_id = "dummy-seer-target"
    game.attacked_player_id = "dummy-attack-target"

    reverted = game.revert_to_previous_night_phase()

    assert reverted is True
    assert game.phase is GamePhase.NIGHT_SEER
    assert game.seer_target_id is None
    assert game.attacked_player_id is None


def test_revert_to_previous_night_phase_from_night_werewolf_day_one() -> None:
    game = _build_sample_game()
    game.day = 1
    game.phase = GamePhase.NIGHT_WEREWOLF
    game.guard_target_id = "dummy-guard-target"
    game.attacked_player_id = "dummy-attack-target"

    reverted = game.revert_to_previous_night_phase()

    assert reverted is True
    assert game.phase is GamePhase.NIGHT_KNIGHT
    assert game.guard_target_id is None
    assert game.attacked_player_id is None


def test_revert_to_previous_night_phase_returns_false_on_other_phase() -> None:
    game = _build_sample_game()
    game.phase = GamePhase.NIGHT_SEER

    reverted = game.revert_to_previous_night_phase()

    assert reverted is False
