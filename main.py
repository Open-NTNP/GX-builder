#!/usr/bin/env python3
"""
Entry point: starts the GX Mod Builder GUI.
Keep this file next to the `libs` folder.
"""
import tkinter as tk
from libs.gui import GXModBuilder

def main():
    root = tk.Tk()
    app = GXModBuilder(root)
    root.mainloop()

if __name__ == "__main__":
    main()
