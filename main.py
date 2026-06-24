# main.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from ui import NovelGeneratorGUI
from ui.styles import WIDGET_SCALING

def main():
    ctk.set_widget_scaling(WIDGET_SCALING)
    app = ctk.CTk()
    gui = NovelGeneratorGUI(app)
    app.mainloop()

if __name__ == "__main__":
    main()
