from __future__ import annotations

from typing import Callable

import flet as ft

from werewolf_gm.domain import GamePhase, Role

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
                    alignment=ft.alignment.center,
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
    on_start_game: Callable[[ft.ControlEvent], None],
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
        options=[
            ft.dropdown.Option(key=role.value, text=_role_label(role)) for role in Role
        ],
    )

    def handle_add(_: ft.ControlEvent) -> None:
        role_value = role_selector.value or Role.CITIZEN.value
        on_add_player((name_input.value or "").strip(), Role(role_value))

    player_rows = [
        ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_50,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(player.name, weight=ft.FontWeight.W_600),
                    ft.Text(_role_label(player.role), color=ft.Colors.BLUE_GREY_700),
                ],
            ),
        )
        for player in state.game.players
    ]

    participant_list: ft.Control
    if player_rows:
        participant_list = ft.Column(
            controls=player_rows,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            height=240,
        )
    else:
        participant_list = ft.Text("参加者はまだいません", color=ft.Colors.GREY_600)

    return ft.View(
        route="/setup",
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
                            ft.FilledButton(
                                "ゲーム開始",
                                on_click=on_start_game,
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


def build_game_tab_content(
    state: AppState,
    *,
    on_decrease_timer: Callable[[ft.ControlEvent], None],
    on_increase_timer: Callable[[ft.ControlEvent], None],
    on_toggle_timer: Callable[[ft.ControlEvent], None],
    on_next_phase: Callable[[ft.ControlEvent], None],
) -> ft.Control:
    if state.selected_tab is GameTab.PROGRESS:
        return _build_progress_content(
            state,
            on_decrease_timer=on_decrease_timer,
            on_increase_timer=on_increase_timer,
            on_toggle_timer=on_toggle_timer,
            on_next_phase=on_next_phase,
        )

    if state.selected_tab is GameTab.DASHBOARD:
        return _build_dashboard_content(state)

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            controls=[
                ft.Text("ログ画面です", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("イベント履歴の表示をここに実装予定"),
                ft.Divider(),
                ft.Column([ft.Text(log) for log in state.logs] or [ft.Text("ログはまだありません")]),
            ]
        ),
    )


def _build_progress_content(
    state: AppState,
    *,
    on_decrease_timer: Callable[[ft.ControlEvent], None],
    on_increase_timer: Callable[[ft.ControlEvent], None],
    on_toggle_timer: Callable[[ft.ControlEvent], None],
    on_next_phase: Callable[[ft.ControlEvent], None],
) -> ft.Control:
    phase_label = _phase_label(state.game.phase)

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
                    controls=[
                        ft.Text(
                            f"{state.game.day}日目 - {phase_label}",
                            size=30,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
                ft.Container(
                    alignment=ft.alignment.center,
                    content=build_timer_panel(
                        timer_text=state.format_timer(),
                        is_running=state.timer_running,
                        on_decrease_30=on_decrease_timer,
                        on_increase_30=on_increase_timer,
                        on_toggle_running=on_toggle_timer,
                    ),
                ),
                ft.FilledButton(
                    "次のフェーズへ進む",
                    on_click=on_next_phase,
                    width=320,
                    height=52,
                ),
            ],
        ),
    )


def _build_dashboard_content(state: AppState) -> ft.Control:
    if not state.game.players:
        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
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
    if phase is GamePhase.NIGHT:
        return "夜の行動"
    if phase is GamePhase.FINISHED:
        return "ゲーム終了"
    return "セットアップ"


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
