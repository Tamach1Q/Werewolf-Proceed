from __future__ import annotations

from typing import Callable

import flet as ft


def build_timer_panel(
    *,
    timer_text: str,
    is_running: bool,
    timer_text_ref: ft.Ref[ft.Text] | None,
    on_decrease_30: Callable[[ft.ControlEvent], None],
    on_increase_30: Callable[[ft.ControlEvent], None],
    on_toggle_running: Callable[[ft.ControlEvent], None],
) -> ft.Control:
    toggle_label = "一時停止" if is_running else "再開"

    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(timer_text, ref=timer_text_ref, size=56, weight=ft.FontWeight.BOLD),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.OutlinedButton("-30秒", on_click=on_decrease_30),
                    ft.OutlinedButton("+30秒", on_click=on_increase_30),
                ],
            ),
            ft.FilledButton(toggle_label, on_click=on_toggle_running),
        ],
    )
