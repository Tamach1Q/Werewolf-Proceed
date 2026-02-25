from __future__ import annotations

import os
import sys

import flet as ft

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from werewolf_gm.main import main


if __name__ == "__main__":
    ft.app(main)
