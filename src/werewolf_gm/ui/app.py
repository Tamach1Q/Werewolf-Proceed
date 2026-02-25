from __future__ import annotations

import asyncio
import random

import flet as ft

from werewolf_gm.domain import DeathReason, FirstDaySeerRule, GamePhase, Role

from .state import AppState
from .tabs import GameTab, build_navigation_bar
from .views import build_game_tab_content, build_home_view, build_reveal_view, build_setup_view


class WerewolfApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState()
        self.confirm_dialog: ft.AlertDialog | None = None
        self._timer_loop_active = False
        self.timer_text_ref = ft.Ref[ft.Text]()

    def start(self) -> None:
        self._configure_page()
        self.page.on_route_change = self._on_route_change
        self.page.views.clear()
        self.page.views.append(self._build_view_for_route("/"))
        self.page.update()

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
                on_remove_player=self._on_remove_player,
                on_start_game=self._on_start_game,
            )
        if route == "/game":
            return self._build_game_view()

        return build_setup_view(
            self.page,
            self.state,
            on_add_player=self._on_add_player,
            on_remove_player=self._on_remove_player,
            on_start_game=self._on_start_game,
        )

    def _refresh_current_view(self) -> None:
        if not self.page.views:
            return

        self.page.views[-1] = self._build_view_for_route(self.page.route)
        self.page.update()

    def _build_game_view(self) -> ft.View:
        if self.state.reveal is not None:
            return build_reveal_view(self.state, on_close_reveal=self._on_close_reveal)

        view_scroll: ft.ScrollMode | None = None
        if self.state.selected_tab in {GameTab.DASHBOARD, GameTab.LOG}:
            view_scroll = ft.ScrollMode.AUTO
        elif (
            self.state.selected_tab is GameTab.PROGRESS
            and self.state.game.phase is GamePhase.FINISHED
        ):
            view_scroll = ft.ScrollMode.AUTO
        elif (
            self.state.selected_tab is GameTab.PROGRESS
            and self.state.game.phase is GamePhase.VOTING
            and self.state.is_rpp_mode
        ):
            view_scroll = ft.ScrollMode.AUTO

        return ft.View(
            route="/game",
            scroll=view_scroll,
            controls=[
                ft.SafeArea(
                    ft.Container(
                        expand=True,
                        content=build_game_tab_content(
                            self.state,
                            timer_text_ref=self.timer_text_ref,
                            on_decrease_timer=self._on_decrease_timer,
                            on_increase_timer=self._on_increase_timer,
                            on_toggle_timer=self._on_toggle_timer,
                            on_next_phase=self._on_next_phase,
                            on_previous_phase=self._on_previous_phase,
                            on_toggle_rpp=self._on_toggle_rpp,
                            on_toggle_rpp_selection=self._on_toggle_rpp_selection,
                            on_execute_rpp=self._on_execute_rpp,
                            on_confirm_vote=self._on_confirm_vote,
                            on_confirm_night_action=self._on_confirm_night_action,
                            on_finish_game=self._on_finish_game,
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

        self.state.logs.append(f"セットアップ: 参加者追加 {name}（{role.value}）")
        self._refresh_current_view()

    def _on_remove_player(self, player_id: str) -> None:
        try:
            player = self.state.game.get_player(player_id)
            self.state.game.remove_player(player_id)
        except ValueError as exc:
            self._show_message(str(exc))
            return

        self.state.logs.append(f"セットアップ: 参加者削除 {player.name}（{player.role.value}）")
        self._refresh_current_view()

    def _on_start_game(
        self,
        day_seconds: int,
        night_seconds: int,
        first_day_seer: FirstDaySeerRule,
    ) -> None:
        if not self.state.can_start_game:
            self._show_message("プレイヤーが不足しています")
            return

        self.state.setup_day_seconds = day_seconds
        self.state.setup_night_seconds = night_seconds
        self.state.setup_first_day_seer = first_day_seer
        self.state.apply_setup_rules_to_game()
        self.state.game.start_game()
        self.state.selected_tab = GameTab.PROGRESS
        self.state.last_morning_result = None
        self.state.reveal = None
        self.state.reset_rpp_mode()
        self.state.timer_running = True
        self.state.reset_timer_for_current_phase()
        self.page.go("/game")

    def _execute_vote(self, player_id: str) -> None:
        try:
            target = self.state.game.get_player(player_id)
            self.state.game.kill_player(player_id, DeathReason.EXECUTED)
        except ValueError as exc:
            self._show_message(str(exc))
            return

        self._add_log(f"投票で {target.name} が処刑された")
        self.state.reset_rpp_mode()
        self._open_vote_result_dialog(target.name)

    def _on_confirm_vote(self, player_id: str) -> None:
        try:
            target = self.state.game.get_player(player_id)
            if not target.is_alive:
                self._show_message("死亡済みのプレイヤーは処刑できません")
                return
        except ValueError as exc:
            self._show_message(str(exc))
            return

        def handle_cancel(_: ft.ControlEvent) -> None:
            self._close_active_dialog()

        def handle_confirm(_: ft.ControlEvent) -> None:
            self._close_active_dialog()
            self._execute_vote(player_id)

        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("処刑の確認"),
            content=ft.Text(f"本当に {target.name} を処刑しますか？"),
            actions=[
                ft.TextButton("いいえ", on_click=handle_cancel),
                ft.FilledButton("はい", on_click=handle_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(self.confirm_dialog)

    def _open_vote_result_dialog(self, target_name: str) -> None:
        def handle_next(_: ft.ControlEvent) -> None:
            self._close_active_dialog()
            self._advance_phase()

        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("処刑結果"),
            content=ft.Text(f"{target_name} が処刑されました。"),
            actions=[
                ft.FilledButton("次へ（夜のターンへ）", on_click=handle_next),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(self.confirm_dialog)

    def _on_toggle_rpp(self, _: ft.ControlEvent) -> None:
        if self.state.is_rpp_mode:
            self.state.reset_rpp_mode()
        else:
            self.state.is_rpp_mode = True
            self.state.rpp_selected_ids.clear()
        self._refresh_current_view()

    def _on_toggle_rpp_selection(self, player_id: str, is_checked: bool) -> None:
        if is_checked:
            self.state.rpp_selected_ids.add(player_id)
        else:
            self.state.rpp_selected_ids.discard(player_id)
        self._refresh_current_view()

    def _on_execute_rpp(self, _: ft.ControlEvent) -> None:
        alive_ids = {player.id for player in self.state.game.alive_players()}
        candidates = [player_id for player_id in self.state.rpp_selected_ids if player_id in alive_ids]
        if not candidates:
            self._show_message("RPP候補を1名以上選択してください")
            return

        candidate_names: list[str] = []
        for candidate_id in candidates:
            try:
                candidate_names.append(self.state.game.get_player(candidate_id).name)
            except ValueError:
                continue

        if not candidate_names:
            self._show_message("有効なRPP候補がいません")
            return

        quoted_names = "」か「".join(candidate_names)

        def handle_cancel(_: ft.ControlEvent) -> None:
            self._close_active_dialog()

        def handle_confirm(_: ft.ControlEvent) -> None:
            self._close_active_dialog()
            selected_player_id = random.choice(candidates)
            self._execute_vote(selected_player_id)

        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("処刑の確認"),
            content=ft.Text(f"本当に「{quoted_names}」を処刑しますか？"),
            actions=[
                ft.TextButton("いいえ", on_click=handle_cancel),
                ft.FilledButton("はい", on_click=handle_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(self.confirm_dialog)

    def _on_confirm_night_action(self, player_id: str) -> None:
        phase = self.state.game.phase

        try:
            target = self.state.game.get_player(player_id)
            if phase is GamePhase.NIGHT_SEER:
                self.state.game.set_seer_target(player_id)
                self._add_log(
                    f"占い師が {target.name} を占い、"
                    f"{'人狼である' if target.is_werewolf else '人狼ではない'} と判定"
                )
                self.state.open_reveal(
                    role_label="占い師",
                    target_name=target.name,
                    is_werewolf=target.is_werewolf,
                )
                self.state.timer_running = False
                self._refresh_current_view()
                return

            if phase is GamePhase.NIGHT_MEDIUM:
                executed_player = self.state.game.get_executed_player_on_day(self.state.game.day)
                if executed_player is None:
                    self._show_message("本日の処刑者はいません")
                    return
                if executed_player.id != player_id:
                    self._show_message("霊媒師は本日の処刑者のみ対象にできます")
                    return

                self.state.game.set_medium_target(player_id)
                self._add_log(
                    f"霊媒師が {target.name} を霊媒し、"
                    f"{'人狼である' if target.is_werewolf else '人狼ではない'} と判定"
                )
                self.state.open_reveal(
                    role_label="霊媒師",
                    target_name=target.name,
                    is_werewolf=target.is_werewolf,
                )
                self.state.timer_running = False
                self._refresh_current_view()
                return

            if phase is GamePhase.NIGHT_KNIGHT:
                self.state.game.set_guard_target(player_id)
                self._add_log(f"騎士が {target.name} を護衛対象に設定")
            elif phase is GamePhase.NIGHT_WEREWOLF:
                self.state.game.set_attack_target(player_id)
                self._add_log(f"人狼が {target.name} を襲撃対象に設定")
            else:
                self._show_message("現在は夜の行動フェーズではありません")
                return
        except ValueError as exc:
            self._show_message(str(exc))
            return

        self._advance_phase()

    def _on_close_reveal(self, _: ft.ControlEvent) -> None:
        if self.state.reveal is None:
            return

        current_phase = self.state.game.phase
        self.state.close_reveal()

        if current_phase in {GamePhase.NIGHT_SEER, GamePhase.NIGHT_MEDIUM}:
            self._advance_phase()
            return

        self._sync_timer_with_phase()
        self._refresh_current_view()
        self._ensure_timer_loop()

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

    def _on_previous_phase(self, _: ft.ControlEvent) -> None:
        if not self.state.game.revert_to_previous_night_phase():
            return

        self._add_log("GMが1つ前の行動に戻りました")
        self._sync_timer_with_phase()
        self._refresh_current_view()
        self._ensure_timer_loop()

    def _advance_phase(self) -> None:
        previous_phase = self.state.game.phase
        previous_day = self.state.game.day

        self.state.last_morning_result = None
        self.state.game.proceed_to_next_phase()
        self.state.reset_rpp_mode()

        if previous_phase is GamePhase.NIGHT_WEREWOLF:
            self.state.last_morning_result = self._build_morning_result_message()
            self._log_night_resolution()

        if (previous_day, previous_phase) != (self.state.game.day, self.state.game.phase):
            self._add_log(f"フェーズ移行 -> {self._phase_label_for_log(self.state.game.phase)}")

        self._sync_timer_with_phase()
        self._refresh_current_view()
        self._ensure_timer_loop()

    def _log_night_resolution(self) -> None:
        guard_id = self.state.game.last_guard_target_id
        attack_id = self.state.game.last_attack_target_id
        victim_id = self.state.game.last_night_victim_id

        guard_name = self._player_name(guard_id)
        attack_name = self._player_name(attack_id)

        if guard_id:
            self._add_log(f"夜行動: 騎士の護衛先は {guard_name}")
        if attack_id:
            self._add_log(f"夜行動: 人狼の襲撃先は {attack_name}")

        if victim_id:
            self._add_log(f"夜明け: {self._player_name(victim_id)} が襲撃で死亡")
        elif attack_id and attack_id == guard_id:
            self._add_log(f"夜明け: {attack_name} は護衛により生存")
        else:
            self._add_log("夜明け: 襲撃による犠牲者なし")

    def _build_morning_result_message(self) -> str:
        victim_id = self.state.game.last_night_victim_id
        if victim_id:
            return f"昨晩の犠牲者: {self._player_name(victim_id)}"
        return "昨晩の犠牲者はいません"

    def _on_finish_game(self, _: ft.ControlEvent) -> None:
        self.state.reset_game()
        self.page.go("/setup")

    def _sync_timer_with_phase(self) -> None:
        self.state.reset_timer_for_current_phase()
        self.state.timer_running = (
            self.state.game.phase is not GamePhase.FINISHED and self.state.reveal is None
        )

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
        self.page.show_dialog(self.confirm_dialog)

    def _cancel_abort(self, _: ft.ControlEvent) -> None:
        self._close_active_dialog()
        self._refresh_current_view()

    def _confirm_abort(self, _: ft.ControlEvent) -> None:
        self.state.reset_game()
        self._close_active_dialog()
        self.page.go("/setup")

    def _close_active_dialog(self) -> None:
        dialog = self.page.pop_dialog()
        if dialog is not None:
            dialog.open = False
        self.confirm_dialog = None
        self.page.update()

    def _show_message(self, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def _add_log(self, message: str) -> None:
        day = self.state.game.day
        phase = self._phase_label_for_log(self.state.game.phase)
        self.state.logs.append(f"{day}日目 {phase}: {message}")

    def _phase_label_for_log(self, phase: GamePhase) -> str:
        labels = {
            GamePhase.SETUP: "セットアップ",
            GamePhase.DAY: "昼",
            GamePhase.VOTING: "投票",
            GamePhase.NIGHT_SEER: "夜(占い)",
            GamePhase.NIGHT_MEDIUM: "夜(霊媒)",
            GamePhase.NIGHT_KNIGHT: "夜(護衛)",
            GamePhase.NIGHT_WEREWOLF: "夜(襲撃)",
            GamePhase.FINISHED: "終了",
        }
        return labels[phase]

    def _player_name(self, player_id: str | None) -> str:
        if not player_id:
            return "なし"
        try:
            return self.state.game.get_player(player_id).name
        except ValueError:
            return "不明"

    def _ensure_timer_loop(self) -> None:
        if self._timer_loop_active:
            return
        if not self.state.timer_running:
            return
        if self.state.timer_seconds <= 0:
            return
        if self.state.reveal is not None:
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
                self._update_timer_text_only()

            if self.state.timer_seconds == 0:
                self.state.timer_running = False
                self._add_log("タイマー終了")
                if self.page.route == "/game":
                    self._refresh_current_view()
        finally:
            self._timer_loop_active = False
            if self.state.timer_running and self.state.timer_seconds > 0:
                self._ensure_timer_loop()

    def _update_timer_text_only(self) -> None:
        if self.timer_text_ref.current is None:
            return
        if self.page.route != "/game":
            return
        if self.state.selected_tab is not GameTab.PROGRESS:
            return
        if self.state.reveal is not None:
            return

        self.timer_text_ref.current.value = self.state.format_timer()
        self.timer_text_ref.current.update()
