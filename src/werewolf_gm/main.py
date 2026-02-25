from __future__ import annotations

import flet as ft

from werewolf_gm.ui import WerewolfApp


def main(page: ft.Page) -> None:
    app = WerewolfApp(page)
    app.start()


if __name__ == "__main__":
    ft.app(target=main)
