from __future__ import annotations

import asyncio

import flet as ft

from .state import AppState
from .tabs import GameTab, build_navigation_bar
from .views import build_game_tab_content, build_home_view, build_setup_view


class WerewolfApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState()
        self.confirm_dialog: ft.AlertDialog | None = None
        self._timer_loop_active = False

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

        if self.page.route == "/game":
            self._ensure_timer_loop()

    def _build_game_view(self) -> ft.View:
        return ft.View(
            route="/game",
            controls=[
                ft.SafeArea(
                    ft.Container(
                        expand=True,
                        content=build_game_tab_content(
                            self.state,
                            on_decrease_timer=self._on_decrease_timer,
                            on_increase_timer=self._on_increase_timer,
                            on_toggle_timer=self._on_toggle_timer,
                            on_next_phase=self._on_next_phase,
                        ),
                    )
                )
            ],
            navigation_bar=build_navigation_bar(
                on_change=self._on_navigation_change,
                selected_tab=self.state.selected_tab,
            ),
        )

    def _refresh_game_view(self) -> None:
        if self.page.route != "/game" or not self.page.views:
            return
        self.page.views[-1] = self._build_game_view()
        self.page.update()

    def _on_navigation_change(self, event: ft.ControlEvent) -> None:
        selected_index = int(event.control.selected_index)
        selected_tab = GameTab(selected_index)

        if selected_tab is GameTab.ABORT:
            self._open_abort_dialog()
            return

        self.state.selected_tab = selected_tab
        if selected_tab is GameTab.LOG:
            self.state.logs.append("ログ画面を開きました")

        self._refresh_game_view()

    def _on_decrease_timer(self, _: ft.ControlEvent) -> None:
        self.state.adjust_timer(-30)
        if self.state.timer_seconds == 0:
            self.state.timer_running = False
        self._refresh_game_view()

    def _on_increase_timer(self, _: ft.ControlEvent) -> None:
        self.state.adjust_timer(30)
        self._refresh_game_view()

    def _on_toggle_timer(self, _: ft.ControlEvent) -> None:
        if not self.state.timer_running and self.state.timer_seconds == 0:
            self.state.reset_timer_for_current_phase()

        self.state.toggle_timer_running()
        self._refresh_game_view()

        if self.state.timer_running:
            self._ensure_timer_loop()

    def _on_next_phase(self, _: ft.ControlEvent) -> None:
        self.state.game.proceed_to_next_phase()
        self.state.reset_timer_for_current_phase()
        self.state.timer_running = True
        self.state.logs.append(
            f"{self.state.game.day}日目 {self.state.game.phase.value} に移行しました"
        )
        self._refresh_game_view()
        self._ensure_timer_loop()

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
        self._refresh_game_view()

    def _confirm_abort(self, _: ft.ControlEvent) -> None:
        self.state.reset_game()

        if self.confirm_dialog is not None:
            self.confirm_dialog.open = False

        self.page.go("/setup")

    def _ensure_timer_loop(self) -> None:
        if self._timer_loop_active:
            return
        if not self.state.timer_running:
            return
        if self.state.timer_seconds <= 0:
            return
        self.page.run_task(self._timer_loop)

    async def _timer_loop(self) -> None:
        self._timer_loop_active = True
        try:
            while self.state.timer_running and self.state.timer_seconds > 0:
                await asyncio.sleep(1)
                if not self.state.timer_running:
                    break

                self.state.timer_seconds = max(0, self.state.timer_seconds - 1)

                if self.page.route == "/game" and self.state.selected_tab is GameTab.PROGRESS:
                    self._refresh_game_view()

            if self.state.timer_seconds == 0:
                self.state.timer_running = False
                self.state.logs.append("タイマーが終了しました")
                if self.page.route == "/game":
                    self._refresh_game_view()
        finally:
            self._timer_loop_active = False
            if self.state.timer_running and self.state.timer_seconds > 0:
                self._ensure_timer_loop()
