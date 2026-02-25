from __future__ import annotations

import flet as ft

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


def build_game_tab_content(state: AppState) -> ft.Control:
    if state.selected_tab is GameTab.PROGRESS:
        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("進行画面です", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"現在フェーズ: {state.game.phase.value}"),
                    ft.Text(f"日数: {state.game.day}"),
                ]
            ),
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
