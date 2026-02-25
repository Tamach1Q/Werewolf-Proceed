from __future__ import annotations

from enum import IntEnum

import flet as ft


class GameTab(IntEnum):
    PROGRESS = 0
    DASHBOARD = 1
    LOG = 2
    ABORT = 3


def build_navigation_bar(on_change, selected_tab: GameTab) -> ft.NavigationBar:
    return ft.NavigationBar(
        selected_index=int(selected_tab),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.PLAY_ARROW, label="進行"),
            ft.NavigationBarDestination(icon=ft.Icons.GRID_VIEW, label="ダッシュボード"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label="ログ"),
            ft.NavigationBarDestination(icon=ft.Icons.CANCEL, label="中止"),
        ],
        on_change=on_change,
    )
