from __future__ import annotations

import flet as ft

from .state import AppState
from .tabs import GameTab, build_navigation_bar
from .views import build_game_tab_content, build_home_view, build_setup_view


class WerewolfApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState()
        self.confirm_dialog: ft.AlertDialog | None = None

    def start(self) -> None:
        self._configure_page()
        self.page.on_route_change = self._on_route_change
        self.page.go(self.page.route or "/")

    def _configure_page(self) -> None:
        self.page.title = "Werewolf GM Support"
        self.page.window.width = 390
        self.page.window.height = 844
        self.page.window.resizable = False
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def _on_route_change(self, _: ft.RouteChangeEvent) -> None:
        self.page.views.clear()

        if self.page.route == "/":
            self.page.views.append(build_home_view(self.page))
        elif self.page.route == "/setup":
            self.page.views.append(build_setup_view(self.page))
        elif self.page.route == "/game":
            self.page.views.append(self._build_game_view())
        else:
            self.page.views.append(build_setup_view(self.page))

        self.page.update()

    def _build_game_view(self) -> ft.View:
        return ft.View(
            route="/game",
            controls=[
                ft.SafeArea(
                    ft.Container(
                        expand=True,
                        content=build_game_tab_content(self.state),
                    )
                )
            ],
            navigation_bar=build_navigation_bar(
                on_change=self._on_navigation_change,
                selected_tab=self.state.selected_tab,
            ),
        )

    def _on_navigation_change(self, event: ft.ControlEvent) -> None:
        selected_index = int(event.control.selected_index)
        selected_tab = GameTab(selected_index)

        if selected_tab is GameTab.ABORT:
            self._open_abort_dialog()
            return

        self.state.selected_tab = selected_tab
        if selected_tab is GameTab.LOG:
            self.state.logs.append("ログ画面を開きました")

        self.page.views[-1] = self._build_game_view()
        self.page.update()

    def _open_abort_dialog(self) -> None:
        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("ゲーム中止"),
            content=ft.Text("本当にゲームを中止してホームに戻りますか？"),
            actions=[
                ft.TextButton("いいえ", on_click=self._cancel_abort),
                ft.FilledButton("はい", on_click=self._confirm_abort),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.confirm_dialog
        self.confirm_dialog.open = True
        self.page.update()

    def _cancel_abort(self, _: ft.ControlEvent) -> None:
        if self.confirm_dialog is None:
            return
        self.confirm_dialog.open = False
        self.page.views[-1] = self._build_game_view()
        self.page.update()

    def _confirm_abort(self, _: ft.ControlEvent) -> None:
        self.state.reset_game()

        if self.confirm_dialog is not None:
            self.confirm_dialog.open = False

        self.page.go("/setup")
