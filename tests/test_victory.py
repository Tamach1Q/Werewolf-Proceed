from werewolf_gm.domain import DeathReason, Game, Role, Team, VictoryState


def _build_sample_game() -> Game:
    game = Game()
    game.add_player("Alice", Role.WEREWOLF)
    game.add_player("Bob", Role.MADMAN)
    game.add_player("Carol", Role.CITIZEN)
    game.add_player("Dave", Role.SEER)
    return game


def test_villager_win_when_all_werewolves_eliminated() -> None:
    game = _build_sample_game()
    werewolf = next(p for p in game.players if p.role is Role.WEREWOLF)

    game.kill_player(werewolf.id, DeathReason.EXECUTED)

    assert game.victory.state is VictoryState.VILLAGER_WIN
    assert game.victory.winner is Team.VILLAGER


def test_werewolf_win_on_parity_or_majority() -> None:
    game = _build_sample_game()

    carol = next(p for p in game.players if p.name == "Carol")
    dave = next(p for p in game.players if p.name == "Dave")

    game.kill_player(carol.id, DeathReason.EXECUTED)
    game.kill_player(dave.id, DeathReason.ATTACKED)

    assert game.victory.state is VictoryState.WEREWOLF_WIN
    assert game.victory.winner is Team.WEREWOLF


def test_game_ongoing_when_no_victory_condition_met() -> None:
    game = _build_sample_game()

    game.refresh_victory()

    assert game.victory.state is VictoryState.ONGOING
    assert game.victory.winner is None
