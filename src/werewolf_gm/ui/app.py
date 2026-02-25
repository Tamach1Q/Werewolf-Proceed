from __future__ import annotations

import asyncio

import flet as ft

from werewolf_gm.domain import DeathReason, GamePhase, Role

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
        self.page.views.append(self._build_view_for_route(self.page.route))
        self.page.update()

        if self.page.route == "/game":
            self._ensure_timer_loop()

    def _build_view_for_route(self, route: str) -> ft.View:
        if route == "/":
            return build_home_view(self.page)
        if route == "/setup":
            return build_setup_view(
                self.page,
                self.state,
                on_add_player=self._on_add_player,
                on_start_game=self._on_start_game,
            )
        if route == "/game":
            return self._build_game_view()

        return build_setup_view(
            self.page,
            self.state,
            on_add_player=self._on_add_player,
            on_start_game=self._on_start_game,
        )

    def _refresh_current_view(self) -> None:
        if not self.page.views:
            return

        self.page.views[-1] = self._build_view_for_route(self.page.route)
        self.page.update()

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
                            on_confirm_vote=self._on_confirm_vote,
                            on_confirm_night_action=self._on_confirm_night_action,
                        ),
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

        self._refresh_current_view()

    def _on_add_player(self, name: str, role: Role) -> None:
        if not name:
            self._show_message("プレイヤー名を入力してください")
            return

        try:
            self.state.game.add_player(name, role)
        except ValueError as exc:
            self._show_message(str(exc))
            return

        self.state.logs.append(f"参加者追加: {name} ({role.value})")
        self._refresh_current_view()

    def _on_start_game(self, _: ft.ControlEvent) -> None:
        if not self.state.can_start_game:
            self._show_message("プレイヤーが不足しています")
            return

        self.page.go("/game")

    def _on_confirm_vote(self, player_id: str) -> None:
        try:
            target = self.state.game.get_player(player_id)
            self.state.game.kill_player(player_id, DeathReason.EXECUTED)
        except ValueError as exc:
            self._show_message(str(exc))
            return

        self.state.logs.append(f"投票処刑: {target.name}")
        self._advance_phase()

    def _on_confirm_night_action(self, player_id: str) -> None:
        phase = self.state.game.phase

        try:
            target = self.state.game.get_player(player_id)
            if phase is GamePhase.NIGHT_SEER:
                self.state.game.set_seer_target(player_id)
                self.state.logs.append(f"占い対象を選択: {target.name}")
            elif phase is GamePhase.NIGHT_MEDIUM:
                self.state.game.set_medium_target(player_id)
                self.state.logs.append(f"霊媒対象を選択: {target.name}")
            elif phase is GamePhase.NIGHT_KNIGHT:
                self.state.game.set_guard_target(player_id)
                self.state.logs.append(f"護衛対象を選択: {target.name}")
            elif phase is GamePhase.NIGHT_WEREWOLF:
                self.state.game.set_attack_target(player_id)
                self.state.logs.append(f"襲撃対象を選択: {target.name}")
            else:
                self._show_message("現在は夜の行動フェーズではありません")
                return
        except ValueError as exc:
            self._show_message(str(exc))
            return

        self._advance_phase()

    def _on_decrease_timer(self, _: ft.ControlEvent) -> None:
        self.state.adjust_timer(-30)
        if self.state.timer_seconds == 0:
            self.state.timer_running = False
        self._refresh_current_view()

    def _on_increase_timer(self, _: ft.ControlEvent) -> None:
        self.state.adjust_timer(30)
        self._refresh_current_view()

    def _on_toggle_timer(self, _: ft.ControlEvent) -> None:
        if not self.state.timer_running and self.state.timer_seconds == 0:
            self.state.reset_timer_for_current_phase()

        self.state.toggle_timer_running()
        self._refresh_current_view()

        if self.state.timer_running:
            self._ensure_timer_loop()

    def _on_next_phase(self, _: ft.ControlEvent) -> None:
        self._advance_phase()

    def _advance_phase(self) -> None:
        previous_phase = self.state.game.phase
        previous_day = self.state.game.day

        self.state.game.proceed_to_next_phase()

        if previous_phase is GamePhase.NIGHT_WEREWOLF:
            if self.state.game.last_night_victim_id:
                victim = self.state.game.get_player(self.state.game.last_night_victim_id)
                self.state.logs.append(f"夜明け: {victim.name} が襲撃されました")
            else:
                self.state.logs.append("夜明け: 襲撃による犠牲者はいません")

        if self.state.game.phase is not GamePhase.FINISHED:
            if (previous_day, previous_phase) != (self.state.game.day, self.state.game.phase):
                self.state.logs.append(
                    f"フェーズ移行: {self.state.game.day}日目 {self.state.game.phase.value}"
                )

        self._sync_timer_with_phase()
        self._refresh_current_view()
        self._ensure_timer_loop()

    def _sync_timer_with_phase(self) -> None:
        self.state.reset_timer_for_current_phase()
        self.state.timer_running = self.state.game.phase is not GamePhase.FINISHED

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
        self._refresh_current_view()

    def _confirm_abort(self, _: ft.ControlEvent) -> None:
        self.state.reset_game()

        if self.confirm_dialog is not None:
            self.confirm_dialog.open = False

        self.page.go("/setup")

    def _show_message(self, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

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
                    self._refresh_current_view()

            if self.state.timer_seconds == 0:
                self.state.timer_running = False
                self.state.logs.append("タイマーが終了しました")
                if self.page.route == "/game":
                    self._refresh_current_view()
        finally:
            self._timer_loop_active = False
            if self.state.timer_running and self.state.timer_seconds > 0:
                self._ensure_timer_loop()
