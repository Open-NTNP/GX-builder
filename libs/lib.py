"""
Library / helper code extracted from the original builder script.
Contains constants, presets, and utility functions used by the GUI.
"""

import os
import hashlib

APP_TITLE = "GX Builder"

# ---------- Theme Configuration ----------
def is_windows_or_linux():
    return os.name in ('nt', 'posix')

# Styles for LIGHT and DARK background(theme for the program)
THEME_STYLES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "select_bg": "#0078d4",
        "select_fg": "#ffffff",
        "input_bg": "#ffffff",
        "input_fg": "#000000",
    },
    "dark": {
        "bg": "#2b2b2b",
        "fg": "#ffffff",
        "select_bg": "#005a9e",
        "select_fg": "#ffffff",
        "input_bg": "#1e1e1e",
        "input_fg": "#ffffff",
    }
}

# ---------- Presets / Enums ----------
BROWSER_EVENT_PRESETS = [
    "CLICK", "HOVER", "HOVER_UP", "TAB_INSERT", "TAB_CLOSE", "TAB_SLASH",
    "SWITCH_TAB", "WINDOW_OPEN", "WINDOW_CLOSE", "LIMITER_ON", "LIMITER_OFF",
    "FEATURE_SWITCH_ON", "FEATURE_SWITCH_OFF", "DOWNLOAD_START", "DOWNLOAD_FINISH",
    "IMPORTANT_CLICK"
]
KEYBOARD_EVENT_PRESETS = [
    "TYPING_LETTER", "TYPING_SPACE", "TYPING_ENTER", "TYPING_BACKSPACE", "TYPING_DELETE", "TYPING_TAB"
]
CURSOR_PRESETS = [
    "POINTER", "HAND", "WAIT", "PROGRESS", "I_BEAM", "MOVE", "HELP",
    "NORTH_RESIZE", "SOUTH_RESIZE", "EAST_RESIZE", "WEST_RESIZE",
    "NORTH_EAST_SOUTH_WEST_RESIZE", "NORTH_WEST_SOUTH_EAST_RESIZE",
    "ALIAS", "COPY", "NO_DROP", "GRAB", "GRABBING", "ZOOM_IN", "ZOOM_OUT"
]

# A tiny silent mp3 filler (empty bytes placeholder). Replace with real silent mp3 bytes if desired.
SILENT_MP3_BYTES = b""

def md5_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()

def compute_payload_hash(file_map: dict) -> str:
    """file_map: relpath -> abs path or bytes"""
    m = hashlib.md5()
    for rel in sorted(file_map.keys()):
        src = file_map[rel]
        try:
            if isinstance(src, (bytes, bytearray)):
                m.update(src)
            else:
                with open(src, "rb") as f:
                    m.update(f.read())
        except Exception:
            continue
    return m.hexdigest()

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def is_nonempty_list_of_dicts(x):
    return isinstance(x, list) and len(x) > 0 and all(isinstance(i, dict) for i in x)

def collect_referenced_paths_from_payload(payload):
    referenced = set()
    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for i in o: walk(i)
        elif isinstance(o, str):
            if "/" in o:
                referenced.add(o)
    walk(payload)
    return referenced
