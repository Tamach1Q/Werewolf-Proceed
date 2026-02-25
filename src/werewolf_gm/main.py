from __future__ import annotations

import flet as ft

try:
    from werewolf_gm.ui import WerewolfApp
except ModuleNotFoundError as exc:
    if exc.name != "werewolf_gm":
        raise
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from werewolf_gm.ui import WerewolfApp


def main(page: ft.Page) -> None:
    app = WerewolfApp(page)
    app.start()


if __name__ == "__main__":
    ft.app(target=main)
