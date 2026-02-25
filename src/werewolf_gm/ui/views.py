from __future__ import annotations

from typing import Callable

import flet as ft

from werewolf_gm.domain import GamePhase

from .components import build_timer_panel
from .state import AppState
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


def build_setup_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/setup",
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
                            ft.Text("セットアップ画面です", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("ここに人数・役職設定UIを追加予定", size=14),
                            ft.FilledButton("ゲーム進行画面へ", on_click=lambda _: page.go("/game")),
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
        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("ダッシュボードです", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"登録プレイヤー数: {len(state.game.players)}"),
                ]
            ),
        )

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
