# ui/styles.py
# -*- coding: utf-8 -*-
import platform
import shutil
import subprocess
import tkinter as tk
from tkinter import font as tkfont

FALLBACK_FONT_FAMILY = "TkDefaultFont"

PLATFORM_FONT_CANDIDATES = {
    "Windows": ("Microsoft YaHei", "SimHei"),
    "Darwin": ("PingFang SC", "Heiti SC"),
    "Linux": ("Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "Noto Sans CJK TC"),
}


def _available_font_families():
    root = tk.Tk()
    root.withdraw()
    try:
        return set(tkfont.families(root))
    finally:
        root.destroy()


def _fontconfig_matches(font_family):
    if not shutil.which("fc-match"):
        return False
    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{family}", font_family],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    matched_families = [item.strip() for item in result.stdout.split(",")]
    return font_family in matched_families


def choose_font_family():
    candidates = PLATFORM_FONT_CANDIDATES.get(platform.system(), ())
    if platform.system() == "Linux":
        for font_family in candidates:
            if _fontconfig_matches(font_family):
                return font_family

    try:
        available_fonts = _available_font_families()
    except tk.TclError:
        return candidates[0] if candidates else FALLBACK_FONT_FAMILY

    for font_family in candidates:
        if font_family in available_fonts:
            return font_family
    return FALLBACK_FONT_FAMILY


FONT_FAMILY = choose_font_family()

UI_FONT = (FONT_FAMILY, 15)
EDITOR_FONT = (FONT_FAMILY, 16)
SMALL_FONT = (FONT_FAMILY, 12)
BOLD_FONT = (FONT_FAMILY, 15, "bold")
TITLE_FONT = (FONT_FAMILY, 18, "bold")

WIDGET_SCALING = 1.15
