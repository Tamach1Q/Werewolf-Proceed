from __future__ import annotations

from typing import Callable

import flet as ft

from werewolf_gm.domain import FirstDaySeerRule, GamePhase, Role, Team

from .components import build_timer_panel
from .state import AppState, MIN_PLAYERS_TO_START
from .tabs import GameTab


def build_home_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/",
        controls=[
            ft.SafeArea(
                ft.Container(
                    expand=True,
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text("人狼GMサポート", size=28, weight=ft.FontWeight.BOLD),
                            ft.Text("ホーム画面です", size=16),
                            ft.FilledButton("セットアップへ", on_click=lambda _: page.go("/setup")),
                        ],
                    ),
                )
            )
        ],
    )


def build_setup_view(
    page: ft.Page,
    state: AppState,
    *,
    on_add_player: Callable[[str, Role], None],
    on_remove_player: Callable[[str], None],
    on_start_game: Callable[[int, int, FirstDaySeerRule], None],
) -> ft.View:
    name_input = ft.TextField(
        label="プレイヤー名",
        hint_text="例: Alice",
        width=340,
    )
    role_selector = ft.Dropdown(
        label="役職",
        width=340,
        value=Role.CITIZEN.value,
        options=[ft.dropdown.Option(key=role.value, text=_role_label(role)) for role in Role],
    )

    def handle_add(_: ft.ControlEvent) -> None:
        role_value = role_selector.value or Role.CITIZEN.value
        on_add_player((name_input.value or "").strip(), Role(role_value))

    day_seconds_selector = ft.Dropdown(
        label="昼の議論時間",
        width=340,
        value=str(state.setup_day_seconds),
        options=[ft.dropdown.Option(key=str(seconds), text=f"{seconds}秒") for seconds in _rule_day_seconds_options()],
    )
    night_seconds_selector = ft.Dropdown(
        label="夜の行動時間",
        width=340,
        value=str(state.setup_night_seconds),
        options=[ft.dropdown.Option(key=str(seconds), text=f"{seconds}秒") for seconds in _rule_night_seconds_options()],
    )
    first_day_seer_selector = ft.Dropdown(
        label="初日占いルール",
        width=340,
        value=state.setup_first_day_seer.value,
        options=[
            ft.dropdown.Option(key=rule.value, text=_first_day_seer_label(rule))
            for rule in FirstDaySeerRule
        ],
    )

    def handle_day_seconds_change(event: ft.ControlEvent) -> None:
        selected = event.control.value
        if selected:
            state.setup_day_seconds = int(selected)

    def handle_night_seconds_change(event: ft.ControlEvent) -> None:
        selected = event.control.value
        if selected:
            state.setup_night_seconds = int(selected)

    def handle_first_day_seer_change(event: ft.ControlEvent) -> None:
        selected = event.control.value
        if selected:
            state.setup_first_day_seer = FirstDaySeerRule(selected)

    day_seconds_selector.on_change = handle_day_seconds_change
    night_seconds_selector.on_change = handle_night_seconds_change
    first_day_seer_selector.on_change = handle_first_day_seer_change

    def handle_start(_: ft.ControlEvent) -> None:
        day_seconds = int(day_seconds_selector.value or state.setup_day_seconds)
        night_seconds = int(night_seconds_selector.value or state.setup_night_seconds)
        first_day_seer = FirstDaySeerRule(first_day_seer_selector.value or state.setup_first_day_seer.value)
        on_start_game(day_seconds, night_seconds, first_day_seer)

    player_rows = [
        _build_setup_player_row(player_id=player.id, name=player.name, role=player.role, on_remove_player=on_remove_player)
        for player in state.game.players
    ]

    participant_list: ft.Control
    if player_rows:
        participant_list = ft.Column(
            controls=player_rows,
            spacing=8,
        )
    else:
        participant_list = ft.Text("参加者はまだいません", color=ft.Colors.GREY_600)

    return ft.View(
        route="/setup",
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.SafeArea(
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Text("セットアップ", size=28, weight=ft.FontWeight.BOLD),
                            name_input,
                            role_selector,
                            ft.FilledButton("追加", on_click=handle_add, width=340),
                            ft.Text(
                                f"参加者 {len(state.game.players)} 人 / 開始には{MIN_PLAYERS_TO_START}人以上が必要",
                                color=ft.Colors.BLUE_GREY_700,
                            ),
                            ft.Divider(height=10),
                            ft.Text("参加者リスト", size=18, weight=ft.FontWeight.W_600),
                            participant_list,
                            ft.Divider(height=10),
                            ft.Text("ルール設定", size=18, weight=ft.FontWeight.W_600),
                            day_seconds_selector,
                            night_seconds_selector,
                            first_day_seer_selector,
                            ft.FilledButton(
                                "ゲーム開始",
                                on_click=handle_start,
                                width=340,
                                disabled=not state.can_start_game,
                            ),
                            ft.TextButton("ホームに戻る", on_click=lambda _: page.go("/")),
                        ],
                    ),
                )
            )
        ],
    )


def _build_setup_player_row(
    *,
    player_id: str,
    name: str,
    role: Role,
    on_remove_player: Callable[[str], None],
) -> ft.Control:
    def handle_remove(_: ft.ControlEvent) -> None:
        on_remove_player(player_id)

    return ft.Container(
        padding=10,
        border_radius=10,
        bgcolor=ft.Colors.BLUE_GREY_50,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(name, weight=ft.FontWeight.W_600),
                        ft.Text(_role_label(role), color=ft.Colors.BLUE_GREY_700),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_500,
                    tooltip="削除",
                    on_click=handle_remove,
                ),
            ],
        ),
    )


def build_reveal_view(state: AppState, *, on_close_reveal: Callable[[ft.ControlEvent], None]) -> ft.View:
    assert state.reveal is not None

    reveal = state.reveal
    body = ft.Container(
        expand=True,
        bgcolor=reveal.background_color,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=24,
            controls=[
                ft.Text(
                    f"{reveal.role_label}の結果",
                    size=24,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    reveal.result_text,
                    size=54,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    f"対象: {reveal.target_name}",
                    size=22,
                    color=ft.Colors.WHITE,
                ),
                ft.FilledButton(
                    "確認終了",
                    on_click=on_close_reveal,
                    width=300,
                    height=56,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.WHITE, color=ft.Colors.BLACK),
                ),
                ft.Text(
                    "画面タップでも戻れます",
                    size=14,
                    color=ft.Colors.WHITE,
                ),
            ],
        ),
    )

    return ft.View(
        route="/game",
        controls=[
            ft.GestureDetector(
                on_tap=on_close_reveal,
                content=body,
            )
        ],
    )


def build_game_tab_content(
    state: AppState,
    *,
    timer_text_ref: ft.Ref[ft.Text] | None,
    on_decrease_timer: Callable[[ft.ControlEvent], None],
    on_increase_timer: Callable[[ft.ControlEvent], None],
    on_toggle_timer: Callable[[ft.ControlEvent], None],
    on_next_phase: Callable[[ft.ControlEvent], None],
    on_previous_phase: Callable[[ft.ControlEvent], None],
    on_toggle_rpp: Callable[[ft.ControlEvent], None],
    on_toggle_rpp_selection: Callable[[str, bool], None],
    on_execute_rpp: Callable[[ft.ControlEvent], None],
    on_confirm_vote: Callable[[str], None],
    on_confirm_night_action: Callable[[str], None],
    on_finish_game: Callable[[ft.ControlEvent], None],
) -> ft.Control:
    if state.selected_tab is GameTab.PROGRESS:
        return _build_progress_content(
            state,
            timer_text_ref=timer_text_ref,
            on_decrease_timer=on_decrease_timer,
            on_increase_timer=on_increase_timer,
            on_toggle_timer=on_toggle_timer,
            on_next_phase=on_next_phase,
            on_previous_phase=on_previous_phase,
            on_toggle_rpp=on_toggle_rpp,
            on_toggle_rpp_selection=on_toggle_rpp_selection,
            on_execute_rpp=on_execute_rpp,
            on_confirm_vote=on_confirm_vote,
            on_confirm_night_action=on_confirm_night_action,
            on_finish_game=on_finish_game,
        )

    if state.selected_tab is GameTab.DASHBOARD:
        return _build_dashboard_content(state)

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Text("ログ画面", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("進行ログ"),
                ft.Divider(),
                ft.ListView(
                    expand=True,
                    spacing=8,
                    controls=[ft.Text(log) for log in state.logs] or [ft.Text("ログはまだありません")],
                ),
            ]
        ),
    )


def _build_progress_content(
    state: AppState,
    *,
    timer_text_ref: ft.Ref[ft.Text] | None,
    on_decrease_timer: Callable[[ft.ControlEvent], None],
    on_increase_timer: Callable[[ft.ControlEvent], None],
    on_toggle_timer: Callable[[ft.ControlEvent], None],
    on_next_phase: Callable[[ft.ControlEvent], None],
    on_previous_phase: Callable[[ft.ControlEvent], None],
    on_toggle_rpp: Callable[[ft.ControlEvent], None],
    on_toggle_rpp_selection: Callable[[str, bool], None],
    on_execute_rpp: Callable[[ft.ControlEvent], None],
    on_confirm_vote: Callable[[str], None],
    on_confirm_night_action: Callable[[str], None],
    on_finish_game: Callable[[ft.ControlEvent], None],
) -> ft.Control:
    if state.game.phase is GamePhase.FINISHED:
        return _build_finished_content(state, on_finish_game=on_finish_game)

    phase_label = _phase_label(state.game.phase)
    phase_actor_label = _phase_actor_label(state)
    morning_result = _build_morning_result(state)
    action_panel = _build_phase_action_panel(
        state,
        on_next_phase=on_next_phase,
        on_previous_phase=on_previous_phase,
        on_toggle_rpp=on_toggle_rpp,
        on_toggle_rpp_selection=on_toggle_rpp_selection,
        on_execute_rpp=on_execute_rpp,
        on_confirm_vote=on_confirm_vote,
        on_confirm_night_action=on_confirm_night_action,
    )

    phase_header_controls: list[ft.Control] = [
        ft.Text(
            f"{state.game.day}日目 - {phase_label}",
            size=30,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
    ]
    if phase_actor_label is not None:
        phase_header_controls.append(
            ft.Text(
                phase_actor_label,
                size=20,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.BLUE_GREY_700,
            )
        )
    phase_header_controls.append(morning_result)

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=phase_header_controls,
                ),
                ft.Container(
                    alignment=ft.Alignment(0, 0),
                    content=build_timer_panel(
                        timer_text=state.format_timer(),
                        is_running=state.timer_running,
                        timer_text_ref=timer_text_ref,
                        on_decrease_30=on_decrease_timer,
                        on_increase_30=on_increase_timer,
                        on_toggle_running=on_toggle_timer,
                    ),
                ),
                ft.Container(width=340, content=action_panel),
            ],
        ),
    )


def _build_phase_action_panel(
    state: AppState,
    *,
    on_next_phase: Callable[[ft.ControlEvent], None],
    on_previous_phase: Callable[[ft.ControlEvent], None],
    on_toggle_rpp: Callable[[ft.ControlEvent], None],
    on_toggle_rpp_selection: Callable[[str, bool], None],
    on_execute_rpp: Callable[[ft.ControlEvent], None],
    on_confirm_vote: Callable[[str], None],
    on_confirm_night_action: Callable[[str], None],
) -> ft.Control:
    alive_players = state.game.alive_players()

    def add_previous_phase_button(controls: list[ft.Control]) -> ft.Control:
        if state.game.phase in {GamePhase.NIGHT_MEDIUM, GamePhase.NIGHT_KNIGHT, GamePhase.NIGHT_WEREWOLF}:
            controls = [*controls, ft.TextButton("1つ前の役職に戻る", on_click=on_previous_phase)]
        return ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=controls)

    if state.game.phase is GamePhase.DAY:
        return ft.FilledButton("投票フェーズへ進む", on_click=on_next_phase, width=340, height=52)

    if state.game.phase is GamePhase.VOTING:
        if not alive_players:
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("投票対象がいません"),
                    ft.FilledButton("次へ進む", on_click=on_next_phase, width=340),
                ],
            )

        target_dropdown = ft.Dropdown(
            label="処刑対象",
            width=340,
            value=alive_players[0].id,
            options=[ft.dropdown.Option(key=p.id, text=p.name) for p in alive_players],
        )

        def handle_vote(_: ft.ControlEvent) -> None:
            if target_dropdown.value:
                on_confirm_vote(target_dropdown.value)

        controls: list[ft.Control] = [
            target_dropdown,
            ft.FilledButton("処刑を確定する", on_click=handle_vote, width=340, height=52),
            ft.TextButton("RPP（ランダム処刑）モードを開く/閉じる", on_click=on_toggle_rpp),
        ]

        if state.is_rpp_mode:
            controls.append(ft.Text("RPP候補", weight=ft.FontWeight.W_600))
            for player in alive_players:
                checkbox = ft.Checkbox(label=player.name, value=player.id in state.rpp_selected_ids)

                def handle_change(event: ft.ControlEvent, player_id: str = player.id) -> None:
                    on_toggle_rpp_selection(player_id, bool(event.control.value))

                checkbox.on_change = handle_change
                controls.append(checkbox)

            controls.append(
                ft.FilledButton(
                    "選ばれた人の中からランダムに1名を処刑",
                    on_click=on_execute_rpp,
                    width=340,
                    height=52,
                    disabled=not state.rpp_selected_ids,
                )
            )

        return ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=controls)

    if state.game.phase is GamePhase.NIGHT_WEREWOLF and state.game.day == 0:
        return add_previous_phase_button(
            [
                ft.Text(
                    "0日目は人狼の顔合わせです。タイマー終了後に次へ進んでください",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.FilledButton("次へ進む", on_click=on_next_phase, width=340, height=52),
            ]
        )

    night_role, confirm_label = _night_phase_role_and_label(state.game.phase)
    if night_role is not None:
        if (
            state.game.phase is GamePhase.NIGHT_SEER
            and state.game.day == 0
            and state.game.rules.first_day_seer is FirstDaySeerRule.NONE
        ):
            return add_previous_phase_button(
                [
                    ft.Text("初日の占いはありません", text_align=ft.TextAlign.CENTER),
                    ft.FilledButton("次へ進む", on_click=on_next_phase, width=340, height=52),
                ]
            )

        if not state.game.has_alive_role(night_role):
            return add_previous_phase_button(
                [
                    ft.Text(
                        "対象の役職は生存していません。待機してから次へ進んでください",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.FilledButton("次へ進む", on_click=on_next_phase, width=340, height=52),
                ]
            )

        random_white_note: ft.Control | None = None
        excluded_role = {
            GamePhase.NIGHT_SEER: Role.SEER,
            GamePhase.NIGHT_KNIGHT: Role.KNIGHT,
            GamePhase.NIGHT_WEREWOLF: Role.WEREWOLF,
        }.get(state.game.phase)

        def with_role_restriction(players: list) -> list:
            if excluded_role is None:
                return players
            return [player for player in players if player.role is not excluded_role]

        if state.game.phase is GamePhase.NIGHT_MEDIUM:
            executed_player = state.game.get_executed_player_on_day(state.game.day)
            if executed_player is None:
                return add_previous_phase_button(
                    [
                        ft.Text("本日の処刑者はいません"),
                        ft.FilledButton("次へ進む", on_click=on_next_phase, width=340, height=52),
                    ]
                )

            target_players = [executed_player]
        elif state.game.phase is GamePhase.NIGHT_SEER and state.game.day == 0:
            if state.game.rules.first_day_seer is FirstDaySeerRule.RANDOM_WHITE:
                target_players = []
                if state.game.first_day_white_target_id is not None:
                    try:
                        target_player = state.game.get_player(state.game.first_day_white_target_id)
                        if target_player.is_alive:
                            target_players = [target_player]
                    except ValueError:
                        target_players = []
                random_white_note = ft.Text("※ランダム白対象（自動選択）", color=ft.Colors.BLUE_GREY_700)
            else:
                target_players = with_role_restriction(alive_players)
        else:
            target_players = with_role_restriction(alive_players)

        if not target_players:
            fallback_message = "行動対象がいません"
            if (
                state.game.phase is GamePhase.NIGHT_SEER
                and state.game.day == 0
                and state.game.rules.first_day_seer is FirstDaySeerRule.RANDOM_WHITE
            ):
                fallback_message = "ランダム白対象を決定できませんでした"
            return add_previous_phase_button(
                [
                    ft.Text(fallback_message, text_align=ft.TextAlign.CENTER),
                    ft.FilledButton("次へ進む", on_click=on_next_phase, width=340, height=52),
                ]
            )

        target_dropdown = ft.Dropdown(
            label="行動対象",
            width=340,
            value=target_players[0].id,
            options=[ft.dropdown.Option(key=p.id, text=p.name) for p in target_players],
        )

        def handle_night_action(_: ft.ControlEvent) -> None:
            if target_dropdown.value:
                on_confirm_night_action(target_dropdown.value)

        action_controls: list[ft.Control] = []
        if random_white_note is not None:
            action_controls.append(random_white_note)
        action_controls.extend(
            [
                target_dropdown,
                ft.FilledButton(confirm_label, on_click=handle_night_action, width=340, height=52),
            ]
        )
        return add_previous_phase_button(action_controls)

    return ft.FilledButton("次のフェーズへ進む", on_click=on_next_phase, width=340, height=52)


def _build_morning_result(state: AppState) -> ft.Control:
    if state.game.phase is not GamePhase.DAY or not state.last_morning_result:
        return ft.Container()

    return ft.Container(
        width=340,
        padding=12,
        border_radius=10,
        bgcolor=ft.Colors.AMBER_100,
        content=ft.Text(
            state.last_morning_result,
            size=16,
            weight=ft.FontWeight.W_600,
            text_align=ft.TextAlign.CENTER,
        ),
    )


def _build_finished_content(state: AppState, *, on_finish_game: Callable[[ft.ControlEvent], None]) -> ft.Control:
    winner_text = _winner_label(state)

    rows: list[ft.Control] = []
    for player in state.game.players:
        is_alive = player.is_alive
        text_color = ft.Colors.BLACK if is_alive else ft.Colors.GREY_500
        status_text = "生存" if is_alive else "死亡"

        rows.append(
            ft.Card(
                elevation=1,
                content=ft.Container(
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(player.name, color=text_color, weight=ft.FontWeight.W_600),
                                    ft.Text(_role_label(player.role), color=text_color),
                                ],
                            ),
                            ft.Text(status_text, color=text_color),
                        ],
                    ),
                ),
            )
        )

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text(winner_text, size=34, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("最終結果", size=20, weight=ft.FontWeight.W_600),
                ft.ListView(expand=True, spacing=8, controls=rows),
                ft.FilledButton(
                    "ホームに戻る（ゲーム終了）",
                    on_click=on_finish_game,
                    width=340,
                    height=52,
                ),
            ],
        ),
    )


def _night_phase_role_and_label(phase: GamePhase) -> tuple[Role | None, str]:
    if phase is GamePhase.NIGHT_SEER:
        return Role.SEER, "占いを確定する"
    if phase is GamePhase.NIGHT_MEDIUM:
        return Role.MEDIUM, "霊媒を確定する"
    if phase is GamePhase.NIGHT_KNIGHT:
        return Role.KNIGHT, "護衛を確定する"
    if phase is GamePhase.NIGHT_WEREWOLF:
        return Role.WEREWOLF, "襲撃を確定する"
    return None, ""


def _build_dashboard_content(state: AppState) -> ft.Control:
    if not state.game.players:
        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Text("ダッシュボード", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("プレイヤーが未登録です。セットアップで追加してください。"),
                ]
            ),
        )

    cards = []
    for player in state.game.players:
        is_alive = player.is_alive
        text_color = ft.Colors.BLACK if is_alive else ft.Colors.GREY_500
        status_text = "生存" if is_alive else "死亡"
        status_color = ft.Colors.GREEN_700 if is_alive else ft.Colors.GREY_500
        status_icon = ft.Icons.PERSON if is_alive else ft.Icons.PERSON_OFF

        cards.append(
            ft.Card(
                elevation=1,
                content=ft.Container(
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(status_icon, color=text_color),
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(player.name, size=16, weight=ft.FontWeight.W_600, color=text_color),
                                            ft.Text(_role_label(player.role), color=text_color),
                                        ],
                                    ),
                                ]
                            ),
                            ft.Text(status_text, color=status_color, weight=ft.FontWeight.W_600),
                        ],
                    ),
                ),
            )
        )

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Text("ダッシュボード", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"登録プレイヤー数: {len(state.game.players)}"),
                ft.ListView(expand=True, spacing=8, controls=cards),
            ]
        ),
    )


def _phase_label(phase: GamePhase) -> str:
    if phase is GamePhase.DAY:
        return "昼の議論"
    if phase is GamePhase.VOTING:
        return "昼の投票"
    if phase is GamePhase.NIGHT_SEER:
        return "夜 - 占い師"
    if phase is GamePhase.NIGHT_MEDIUM:
        return "夜 - 霊媒師"
    if phase is GamePhase.NIGHT_KNIGHT:
        return "夜 - 騎士"
    if phase is GamePhase.NIGHT_WEREWOLF:
        return "夜 - 人狼"
    if phase is GamePhase.FINISHED:
        return "ゲーム終了"
    return "セットアップ"


def _phase_actor_label(state: AppState) -> str | None:
    role_by_phase = {
        GamePhase.NIGHT_SEER: Role.SEER,
        GamePhase.NIGHT_MEDIUM: Role.MEDIUM,
        GamePhase.NIGHT_KNIGHT: Role.KNIGHT,
        GamePhase.NIGHT_WEREWOLF: Role.WEREWOLF,
    }
    role = role_by_phase.get(state.game.phase)
    if role is None:
        return None

    names = [player.name for player in state.game.alive_players() if player.role is role]
    suffix = ", ".join(names) if names else "生存者なし"
    return f"行動プレイヤー: {suffix}"


def _winner_label(state: AppState) -> str:
    winner = state.game.victory.winner
    if winner is Team.VILLAGER:
        return "市民陣営の勝利！"
    if winner is Team.WEREWOLF:
        return "人狼陣営の勝利！"
    return "ゲーム終了"


def _role_label(role: Role) -> str:
    labels = {
        Role.CITIZEN: "市民",
        Role.WEREWOLF: "人狼",
        Role.MADMAN: "狂人",
        Role.SEER: "占い師",
        Role.KNIGHT: "騎士",
        Role.MEDIUM: "霊媒師",
    }
    return labels[role]


def _first_day_seer_label(rule: FirstDaySeerRule) -> str:
    labels = {
        FirstDaySeerRule.RANDOM_WHITE: "ランダム白",
        FirstDaySeerRule.FREE_SELECT: "自由選択",
        FirstDaySeerRule.NONE: "なし",
    }
    return labels[rule]


def _rule_day_seconds_options() -> list[int]:
    return [120, 180, 240, 300, 420]


def _rule_night_seconds_options() -> list[int]:
    return [60, 90, 120, 150, 180]
