"""
GUI code extracted from your original script.
Imports helpers and constants from libs.lib.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json, os, shutil, zipfile
from functools import partial

from .lib import (
    APP_TITLE, THEME_STYLES, BROWSER_EVENT_PRESETS, KEYBOARD_EVENT_PRESETS,
    CURSOR_PRESETS, md5_bytes, compute_payload_hash, ensure_dir,
    is_nonempty_list_of_dicts, collect_referenced_paths_from_payload,
    SILENT_MP3_BYTES
)

class GXModBuilder:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1180x820")

        # Theme State
        self.current_theme = "dark"  # Default to dark
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # relpath -> src path or bytes
        self.files_to_include = {}

        # core data structure: mod payload (schema v2-ish)
        payload_keys = [
            'app_icon','background_music','browser_sounds','keyboard_sounds','cursors','fonts',
            'mobile_image_overrides','splash_screen','theme','wallpaper','page_styles'
        ]
        empty_payload = {k: [] for k in payload_keys}

        self.data = {
            "name": "GX Mod",
            "version": "1.0.0",
            "author": "",
            "developer": {"name": ""},
            "icons": {"512": "icon_512.png"},
            "manifest_version": 3,
            "mod": {"schema_version": 2, "payload": empty_payload},
            "update_url": ""
        }

        self.widgets = {}

        self.create_toolbar()
        
        self.build_ui()
        self.apply_theme() # Initial theme

    def create_toolbar(self):
        """Creates the top bar with the Dark/Light toggle."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side="top", fill="x", padx=5, pady=2)
        
        # Theme Toggle Button
        self.theme_btn_text = tk.StringVar(value="Switch to Light Mode")
        btn = ttk.Button(toolbar, textvariable=self.theme_btn_text, command=self.toggle_theme)
        btn.pack(side="right", padx=5, pady=2)

        ttk.Label(toolbar, text=APP_TITLE, font=("Helvetica", 12, "bold")).pack(side="left", padx=5)

    def toggle_theme(self):
        """Switches between Dark and Light mode and updates the UI."""
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.theme_btn_text.set("Switch to Dark Mode")
        else:
            self.current_theme = "dark"
            self.theme_btn_text.set("Switch to Light Mode")
        
        self.apply_theme()

    def apply_theme(self):
        """Applies the color scheme to the root and ttk widgets."""
        colors = THEME_STYLES[self.current_theme]

        # Configure root window
        self.root.configure(bg=colors["bg"])
        
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TButton", background=colors["input_bg"], foreground=colors["fg"], bordercolor=colors["fg"])
        self.style.map("TButton", background=[('active', colors["select_bg"])], foreground=[('active', colors["select_fg"])])
        
        self.style.configure("TEntry", fieldbackground=colors["input_bg"], foreground=colors["fg"], insertcolor=colors["fg"])
        
        text_bg = colors["input_bg"]
        text_fg = colors["fg"]
        text_sel_bg = colors["select_bg"]
        text_sel_fg = colors["select_fg"]

        for name, widget in self.widgets.items():
            if isinstance(widget, tk.Text):
                widget.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg, 
                                selectbackground=text_sel_bg, selectforeground=text_sel_fg)
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=text_bg, fg=text_fg, selectbackground=text_sel_bg, selectforeground=text_sel_fg)

        self.style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TRadiobutton", background=colors["bg"], foreground=colors["fg"])
        
        self.style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=colors["bg"], foreground=colors["fg"], padding=[10, 5])
        self.style.map("TNotebook.Tab", 
                       background=[("selected", colors["input_bg"]), ("active", colors["bg"])],
                       expand=[("selected", [1, 1, 1, 0])])

    # ---------------- UI ----------------
    def build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        tabs = {}
        tab_names = ["Info", "Import", "App Icons", "Music", "Browser Sounds", "Keyboard Sounds",
                     "Cursors", "Fonts", "Mobile Overrides", "Splash", "Theme", "Wallpaper",
                     "Page Styles", "Files", "Validator/Export"]
        for t in tab_names:
            frame = ttk.Frame(nb)
            nb.add(frame, text=t)
            tabs[t] = frame

        self.build_info_tab(tabs["Info"])
        self.build_import_tab(tabs["Import"])
        self.build_app_icon_tab(tabs["App Icons"])
        self.build_music_tab(tabs["Music"])
        self.build_sound_pack_tab(tabs["Browser Sounds"], "browser_sounds", "sounds")
        self.build_sound_pack_tab(tabs["Keyboard Sounds"], "keyboard_sounds", "keyboard")
        self.build_cursors_tab(tabs["Cursors"])
        self.build_fonts_tab(tabs["Fonts"])
        self.build_mobile_tab(tabs["Mobile Overrides"])
        self.build_splash_tab(tabs["Splash"])
        self.build_theme_tab(tabs["Theme"])
        self.build_wallpaper_tab(tabs["Wallpaper"])
        self.build_page_styles_tab(tabs["Page Styles"])
        self.build_files_tab(tabs["Files"])
        self.build_validator_tab(tabs["Validator/Export"])

    # Info tab
    def build_info_tab(self, parent):
        f = ttk.Frame(parent, padding=10); f.pack(fill="both", expand=True)
        self.widgets['name'] = tk.StringVar(value=self.data.get('name',''))
        self.widgets['version'] = tk.StringVar(value=self.data.get('version','1.0.0'))
        self.widgets['author'] = tk.StringVar(value=self.data.get('author',''))
        self.widgets['developer'] = tk.StringVar(value=self.data.get('developer',{}).get('name',''))
        self.widgets['update_url'] = tk.StringVar(value=self.data.get('update_url',''))

        for label, key in (("Name","name"),("Version","version"),("Author","author"),("Developer","developer"),("Update URL","update_url")):
            r = ttk.Frame(f); r.pack(fill="x", pady=4)
            ttk.Label(r, text=label + ":", width=14).pack(side="left")
            ttk.Entry(r, textvariable=self.widgets[key]).pack(side="left", fill="x", expand=True)

        ttk.Label(f, text="Description:").pack(anchor="w", pady=(8,0))
        self.widgets['description'] = tk.Text(f, height=6)
        self.widgets['description'].pack(fill="both", expand=True, pady=4)

    # Import tab
    def build_import_tab(self, parent):
        f = ttk.Frame(parent, padding=10); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Import manifest.json and auto-register files (looks relative to manifest)").pack(anchor="w")
        btn_frame = ttk.Frame(f); btn_frame.pack(fill="x", pady=8)
        ttk.Button(btn_frame, text="Import manifest.json", command=self.import_manifest).pack(side="left")
        ttk.Button(btn_frame, text="Auto-scan folder for referenced files", command=self.auto_register_from_manifest_folder).pack(side="left", padx=8)
        self.widgets['import_log'] = tk.Text(f, height=18); self.widgets['import_log'].pack(fill="both", expand=True)

    # App icons tab
    def build_app_icon_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="App icons (app_icon array)").pack(anchor="w")
        self.widgets['app_icon_list'] = tk.Listbox(f, height=8); self.widgets['app_icon_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add App Icon", command=self.add_app_icon).pack(side="left")
        ttk.Button(rb, text="Edit Selected", command=self.edit_app_icon).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove Selected", command=partial(self.remove_list_selection, 'app_icon')).pack(side="left", padx=6)

    # Music tab
    def build_music_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Background music sets").pack(anchor="w")
        self.widgets['bgmusic_list'] = tk.Listbox(f, height=8); self.widgets['bgmusic_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Music Set", command=self.add_bg_music_set).pack(side="left")
        ttk.Button(rb, text="Add Track(s) to Selected Set", command=self.add_tracks_to_bg_music).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove Selected Set", command=partial(self.remove_list_selection, 'background_music')).pack(side="left", padx=6)

    # Generic sound pack tabs (browser, keyboard)
    def build_sound_pack_tab(self, parent, pack_key, folder):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        title = "Browser Sound Packs" if pack_key == "browser_sounds" else "Keyboard Sound Packs"
        ttk.Label(f, text=title).pack(anchor="w")
        lb = tk.Listbox(f, height=12); lb.pack(fill="both", expand=True)
        self.widgets[f'{pack_key}_listbox'] = lb
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Pack", command=partial(self.add_sound_pack, pack_key)).pack(side="left")
        ttk.Button(rb, text="Add event-file(s) to selected", command=partial(self.add_event_files, pack_key, folder)).pack(side="left", padx=6)
        ttk.Button(rb, text="Edit Selected pack JSON", command=partial(self.edit_pack_json, pack_key)).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove Selected", command=partial(self.remove_list_selection, pack_key)).pack(side="left", padx=6)

    # Cursors
    def build_cursors_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Cursor packs").pack(anchor="w")
        self.widgets['cursors_list'] = tk.Listbox(f, height=8); self.widgets['cursors_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Cursor Pack", command=self.add_cursor_pack).pack(side="left")
        ttk.Button(rb, text="Add cursor files to selected", command=self.add_cursor_files).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'cursors')).pack(side="left", padx=6)

    # Fonts
    def build_fonts_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Font packs").pack(anchor="w")
        self.widgets['fonts_list'] = tk.Listbox(f, height=8); self.widgets['fonts_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Font Pack", command=self.add_font_pack).pack(side="left")
        ttk.Button(rb, text="Add font files to selected", command=self.add_font_files).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'fonts')).pack(side="left", padx=6)

    # Mobile overrides
    def build_mobile_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Mobile image overrides (mobile_image_overrides)").pack(anchor="w")
        self.widgets['mobile_list'] = tk.Listbox(f, height=6); self.widgets['mobile_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Mobile Override", command=self.add_mobile_override).pack(side="left")
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'mobile_image_overrides')).pack(side="left", padx=6)

    # Splash
    def build_splash_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Splash screens").pack(anchor="w")
        self.widgets['splash_list'] = tk.Listbox(f, height=6); self.widgets['splash_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Splash", command=self.add_splash).pack(side="left")
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'splash_screen')).pack(side="left", padx=6)

    # Theme
    def build_theme_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Theme entries (dark/light HSL)").pack(anchor="w")
        self.widgets['theme_list'] = tk.Listbox(f, height=8); self.widgets['theme_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Theme Entry", command=self.add_theme).pack(side="left")
        ttk.Button(rb, text="Edit selected", command=partial(self.edit_theme)).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'theme')).pack(side="left", padx=6)

    # Wallpaper
    def build_wallpaper_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Wallpaper entries").pack(anchor="w")
        self.widgets['wp_list'] = tk.Listbox(f, height=8); self.widgets['wp_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Wallpaper Entry", command=self.add_wallpaper).pack(side="left")
        ttk.Button(rb, text="Edit selected", command=partial(self.edit_wallpaper)).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'wallpaper')).pack(side="left", padx=6)

    # Page styles
    def build_page_styles_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Page styles (webmodding css)").pack(anchor="w")
        self.widgets['pages_list'] = tk.Listbox(f, height=8); self.widgets['pages_list'].pack(fill="both", expand=True)
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Add Page Style", command=self.add_page_style).pack(side="left")
        ttk.Button(rb, text="Edit selected", command=partial(self.edit_page_style)).pack(side="left", padx=6)
        ttk.Button(rb, text="Remove selected", command=partial(self.remove_list_selection, 'page_styles')).pack(side="left", padx=6)

    # Files tab
    def build_files_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Files: icon_512.png, license.txt, key text").pack(anchor="w")
        row = ttk.Frame(f); row.pack(fill="x", pady=4)
        ttk.Label(row, text="icon_512.png:", width=16).pack(side="left")
        self.widgets['icon_entry'] = tk.StringVar(); ttk.Entry(row, textvariable=self.widgets['icon_entry']).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse & Register", command=lambda: self.register_file('icon_512.png', self.widgets['icon_entry'])).pack(side="left", padx=6)

        row2 = ttk.Frame(f); row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="license.txt:", width=16).pack(side="left")
        self.widgets['license_entry'] = tk.StringVar(); ttk.Entry(row2, textvariable=self.widgets['license_entry']).pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="Browse & Register", command=lambda: self.register_file('license.txt', self.widgets['license_entry'])).pack(side="left", padx=6)

        row3 = ttk.Frame(f); row3.pack(fill="x", pady=4)
        ttk.Label(row3, text="Key (text)", width=16).pack(side="left")
        self.widgets['key_text'] = tk.StringVar(); ttk.Entry(row3, textvariable=self.widgets['key_text']).pack(side="left", fill="x", expand=True)
        ttk.Button(row3, text="Load key file", command=self.load_key_file).pack(side="left", padx=6)

    # Validator & Export
    def build_validator_tab(self, parent):
        f = ttk.Frame(parent, padding=8); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Validator (pre-export) and Export").pack(anchor="w")
        rb = ttk.Frame(f); rb.pack(fill="x", pady=6)
        ttk.Button(rb, text="Run Validation", command=self.run_validation).pack(side="left")
        ttk.Button(rb, text="Auto-Fix detected problems", command=self.autofix_all).pack(side="left", padx=6)
        ttk.Button(rb, text="Preview manifest.json", command=self.preview_manifest).pack(side="left", padx=6)
        ttk.Button(rb, text="Export folder (Load unpacked)", command=self.export_folder).pack(side="left", padx=6)
        ttk.Button(rb, text="Export ZIP", command=self.export_zip).pack(side="left", padx=6)
        self.widgets['validator_log'] = tk.Text(f, height=18); self.widgets['validator_log'].pack(fill="both", expand=True, pady=6)

    # ---------------- Functional helpers ----------------
    def register_file(self, relpath, var=None):
        p = filedialog.askopenfilename()
        if not p:
            return
        self.files_to_include[relpath] = p
        if var is not None:
            var.set(p)
        self.log_import(f"Registered {p} -> {relpath}")

    def load_key_file(self):
        p = filedialog.askopenfilename(filetypes=[("Text","*.txt *.pem *.key"),("All","*.*")])
        if not p: return
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read().strip()
            if txt:
                self.data['mod']['key'] = txt
                self.widgets['key_text'].set(f"[loaded: {os.path.basename(p)}]")
                self.log_import(f"Loaded key text from {p}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------- Add/Edit actions ----------
    # App icons
    def add_app_icon(self):
        dlg = self.simple_entry_dialog("App Icon", ("id","name"),
                                       auto_id_prefix="app_icon", existing=self.data['mod']['payload'].get('app_icon', []))
        if not dlg: return
        id_, name = dlg['id'], dlg['name']
        p = filedialog.askopenfilename(title="Select app icon image")
        if not p: return
        dest = f"app_icon/{os.path.basename(p)}"
        self.files_to_include[dest] = p
        entry = {"id": id_, "name": name, "path": dest}
        self.data['mod']['payload'].setdefault('app_icon', []).append(entry)
        self.widgets['app_icon_list'].insert("end", f"{id_} : {name} -> {dest}")

    def edit_app_icon(self):
        sel = self.widgets['app_icon_list'].curselection()
        if not sel: return
        idx = sel[0]
        entry = self.data['mod']['payload']['app_icon'][idx]
        messagebox.showinfo("App Icon JSON", json.dumps(entry, indent=2, ensure_ascii=False))

    # Background music
    def add_bg_music_set(self):
        dlg = self.simple_entry_dialog("Music set", ("id","name"),
                                       auto_id_prefix="bgm", existing=self.data['mod']['payload'].get('background_music', []))
        if not dlg: return
        entry = {"id": dlg['id'], "name": dlg['name'], "tracks": []}
        self.data['mod']['payload'].setdefault('background_music', []).append(entry)
        self.widgets['bgmusic_list'].insert("end", f"{dlg['id']} : {dlg['name']}")

    def add_tracks_to_bg_music(self):
        sel = self.widgets['bgmusic_list'].curselection()
        if not sel:
            if messagebox.askyesno("No set", "No music set selected. Create one now?"):
                self.add_bg_music_set()
                return
            messagebox.showwarning("Select", "Select a music set first")
            return
        idx = sel[0]
        files = filedialog.askopenfilenames(filetypes=[("MP3","*.mp3"),("All","*.*")])
        if not files: return
        entry = self.data['mod']['payload']['background_music'][idx]
        for f in files:
            dest = f"music/{os.path.basename(f)}"
            self.files_to_include[dest] = f
            entry.setdefault('tracks', []).append(dest)
            self.log_import(f"Registered music {f} -> {dest}")

    # Sound packs
    def add_sound_pack(self, pack_key):
        dlg = self.simple_entry_dialog("Pack", ("id","name"),
                                       auto_id_prefix=pack_key, existing=self.data['mod']['payload'].get(pack_key, []))
        if not dlg: return
        pack = {"id": dlg['id'], "name": dlg['name'], "sounds": {}}
        self.data['mod']['payload'].setdefault(pack_key, []).append(pack)
        lb = self.widgets.get(f'{pack_key}_listbox')
        if lb:
            lb.insert("end", f"{dlg['id']} : {dlg['name']}")

    def add_event_files(self, pack_key, dest_folder):
        lb = self.widgets.get(f'{pack_key}_listbox')
        if not lb:
            return
        sel = lb.curselection()
        if not sel:
            if messagebox.askyesno("No pack", "No pack selected. Create a new pack now?"):
                self.add_sound_pack(pack_key)
                return
            messagebox.showwarning("Select", "Select a pack first")
            return
        idx = sel[0]
        pack = self.data['mod']['payload'][pack_key][idx]

        # event chooser with presets
        presets = BROWSER_EVENT_PRESETS if pack_key == 'browser_sounds' else KEYBOARD_EVENT_PRESETS
        ev = self.choose_from_list("Choose Event", presets + ["-- Custom / Typed --"])
        if not ev:
            return
        if ev == "-- Custom / Typed --":
            ev = self.prompt_simple("Event name", "Event id (exact):")
            if not ev: return

        files = filedialog.askopenfilenames(filetypes=[("Audio","*.wav *.mp3 *.ogg"),("All","*.*")])
        if not files:
            if messagebox.askyesno("No files chosen", "No files were selected. Insert silent filler for this event?"):
                silent_name = f"{dest_folder}/empty_{ev}.mp3"
                self.files_to_include[silent_name] = SILENT_MP3_BYTES
                pack['sounds'][ev] = [silent_name]
                self.log_import(f"No files chosen for event {ev}, inserted silent filler -> {silent_name}")
                self.update_pack_listbox(pack_key)
            return

        arr = pack['sounds'].setdefault(ev, [])
        for f in files:
            dest = f"{dest_folder}/{os.path.basename(f)}"
            self.files_to_include[dest] = f
            arr.append(dest)
            self.log_import(f"Registered sound {f} -> {dest} for event {ev}")
        self.update_pack_listbox(pack_key)

    def edit_pack_json(self, pack_key):
        lb = self.widgets.get(f'{pack_key}_listbox')
        if not lb: return
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Select", "Select a pack first")
            return
        idx = sel[0]
        pack = self.data['mod']['payload'][pack_key][idx]
        messagebox.showinfo("Pack JSON", json.dumps(pack, indent=2, ensure_ascii=False))

    def update_pack_listbox(self, pack_key):
        lb = self.widgets.get(f'{pack_key}_listbox')
        if not lb:
            return
        lb.delete(0, "end")
        for p in self.data['mod']['payload'].get(pack_key, []):
            lb.insert("end", f"{p.get('id','?')} : {p.get('name','')}")

    # Cursors
    def add_cursor_pack(self):
        dlg = self.simple_entry_dialog("Cursor pack", ("id","name"),
                                       auto_id_prefix="cursor", existing=self.data['mod']['payload'].get('cursors', []))
        if not dlg: return
        pack = {"id": dlg['id'], "name": dlg['name'], "items": [], "preview": None}
        self.data['mod']['payload'].setdefault('cursors', []).append(pack)
        self.widgets['cursors_list'].insert("end", f"{dlg['id']} : {dlg['name']}")

    def add_cursor_files(self):
        sel = self.widgets['cursors_list'].curselection()
        if not sel:
            if messagebox.askyesno("No pack", "No cursor pack selected. Create a new pack now?"):
                self.add_cursor_pack()
                return
            messagebox.showwarning("Select", "Select a cursor pack first")
            return
        idx = sel[0]
        pack = self.data['mod']['payload']['cursors'][idx]
        files = filedialog.askopenfilenames(title="Select cursor files")
        if not files: return
        ctype = self.choose_from_list("Cursor Type", CURSOR_PRESETS + ["-- Custom --"])
        if ctype == "-- Custom --":
            ctype = self.prompt_simple("Cursor type", "Type label (e.g. POINTER)")
            if not ctype: ctype = "POINTER"
        for f in files:
            dest = f"cursors/{os.path.basename(f)}"
            self.files_to_include[dest] = f
            pack['items'].append({"path": dest, "type": ctype})
            self.log_import(f"Registered cursor {f} -> {dest} type={ctype}")
        self.update_listbox('cursors')

    def update_listbox(self, key):
        if key == 'cursors':
            lb = self.widgets.get('cursors_list')
            if not lb: return
            lb.delete(0, "end")
            for p in self.data['mod']['payload'].get('cursors', []):
                lb.insert("end", f"{p.get('id')} : {p.get('name')} ({len(p.get('items',[]))} items)")

    # Fonts
    def add_font_pack(self):
        dlg = self.simple_entry_dialog("Font pack", ("id","name"),
                                       auto_id_prefix="font", existing=self.data['mod']['payload'].get('fonts', []))
        if not dlg: return
        pack = {"id": dlg['id'], "name": dlg['name'], "header": {}, "body": {}}
        self.data['mod']['payload'].setdefault('fonts', []).append(pack)
        self.widgets['fonts_list'].insert("end", f"{dlg['id']} : {dlg['name']}")

    def add_font_files(self):
        sel = self.widgets['fonts_list'].curselection()
        if not sel:
            messagebox.showwarning("Select", "Select a font pack first")
            return
        idx = sel[0]; pack = self.data['mod']['payload']['fonts'][idx]
        files = filedialog.askopenfilenames(title="Select font files", filetypes=[("Fonts","*.ttf *.otf *.woff *.woff2"),("All","*.*")])
        if not files: return
        for i,f in enumerate(files):
            dest = f"font/{os.path.basename(f)}"
            self.files_to_include[dest] = f
            if i == 0:
                pack.setdefault('header', {}).setdefault('variants', []).append({'path': dest})
            else:
                pack.setdefault('body', {}).setdefault('variants', []).append({'path': dest})
            self.log_import(f"Registered font {f} -> {dest}")

    # Mobile override
    def add_mobile_override(self):
        dlg = self.simple_entry_dialog("Mobile override", ("id","name"),
                                       auto_id_prefix="mobile", existing=self.data['mod']['payload'].get('mobile_image_overrides', []))
        if not dlg: return
        entry = {"id": dlg['id'], "name": dlg['name'], "images": {}}
        self.data['mod']['payload'].setdefault('mobile_image_overrides', []).append(entry)
        self.widgets['mobile_list'].insert("end", f"{dlg['id']} : {dlg['name']}")

    # Splash
    def add_splash(self):
        dlg = self.simple_entry_dialog("Splash", ("id","name"),
                                       auto_id_prefix="splash", existing=self.data['mod']['payload'].get('splash_screen', []))
        if not dlg: return
        p = filedialog.askopenfilename(title="Select splash video", filetypes=[("Video","*.mp4 *.webm *.mkv"),("All","*.*")])
        if not p: return
        dest = f"splash/{os.path.basename(p)}"
        self.files_to_include[dest] = p
        entry = {"id": dlg['id'], "name": dlg['name'], "path": dest}
        self.data['mod']['payload'].setdefault('splash_screen', []).append(entry)
        self.widgets['splash_list'].insert("end", f"{dlg['id']} : {dlg['name']} -> {dest}")

    # Theme
    def add_theme(self):
        dlg = self.simple_entry_dialog("Theme", ("id","name"),
                                       auto_id_prefix="theme", existing=self.data['mod']['payload'].get('theme', []))
        if not dlg: return
        values = {}
        for k in ("dark_h","dark_s","dark_l","dark_sec_h","dark_sec_s","dark_sec_l",
                  "light_h","light_s","light_l","light_sec_h","light_sec_s","light_sec_l"):
            v = self.prompt_simple("Theme value " + k, "Enter " + k + " (0-360 or 0-100)")
            try:
                values[k] = int(v) if v else 0
            except:
                values[k] = 0
        theme_obj = {
            "id": dlg['id'], "name": dlg['name'],
            "dark": {
                "gx_accent": {"h": values['dark_h'], 's': values['dark_s'], 'l': values['dark_l']},
                "gx_secondary_base": {"h": values['dark_sec_h'], 's': values['dark_sec_s'], 'l': values['dark_sec_l']}
            },
            "light": {
                "gx_accent": {"h": values['light_h'], 's': values['light_s'], 'l': values['light_l']},
                "gx_secondary_base": {"h": values['light_sec_h'], 's': values['light_sec_s'], 'l': values['light_sec_l']}
            }
        }
        self.data['mod']['payload'].setdefault('theme', []).append(theme_obj)
        self.widgets['theme_list'].insert("end", f"{dlg['id']} : {dlg['name']}")

    def edit_theme(self):
        sel = self.widgets['theme_list'].curselection()
        if not sel: return
        obj = self.data['mod']['payload']['theme'][sel[0]]
        messagebox.showinfo("Theme JSON", json.dumps(obj, indent=2, ensure_ascii=False))

    # Wallpaper
    def add_wallpaper(self):
        dlg = self.simple_entry_dialog("Wallpaper", ("id","name"),
                                       auto_id_prefix="wp", existing=self.data['mod']['payload'].get('wallpaper', []))
        if not dlg: return
        obj = {"id": dlg['id'], "name": dlg['name'], "dark": {}, "light": {}}
        self.data['mod']['payload'].setdefault('wallpaper', []).append(obj)
        self.widgets['wp_list'].insert("end", f"{dlg['id']} : {dlg['name']}")

    def edit_wallpaper(self):
        sel = self.widgets['wp_list'].curselection()
        if not sel:
            if messagebox.askyesno("No wallpaper", "No wallpaper entry selected. Create one now?"):
                self.add_wallpaper()
                return
            return
        idx = sel[0]
        obj = self.data['mod']['payload']['wallpaper'][idx]
        p_dark = filedialog.askopenfilename(title="Select dark image (or Cancel)")
        if p_dark:
            dest = f"wallpaper/{os.path.basename(p_dark)}"
            self.files_to_include[dest] = p_dark
            obj.setdefault('dark', {})['image'] = dest
            self.log_import(f"Registered wallpaper dark image {p_dark} -> {dest}")
        p_light = filedialog.askopenfilename(title="Select light image (or Cancel)")
        if p_light:
            dest = f"wallpaper/{os.path.basename(p_light)}"
            self.files_to_include[dest] = p_light
            obj.setdefault('light', {})['image'] = dest
            self.log_import(f"Registered wallpaper light image {p_light} -> {dest}")
        tc = self.prompt_simple("Dark text color", "hex color (e.g. #FFFFFF) or blank")
        if tc:
            obj.setdefault('dark', {})['text_color'] = tc
        tl = self.prompt_simple("Light text color", "hex color (e.g. #000000) or blank")
        if tl:
            obj.setdefault('light', {})['text_color'] = tl
        self.log_import(f"Updated wallpaper {obj.get('id')}")

    # Page styles
    def add_page_style(self):
        css_files = filedialog.askopenfilenames(title="Select CSS files", filetypes=[("CSS","*.css"),("All","*.*")])
        if not css_files: return
        matches = self.prompt_simple("Matches", "Comma-separated match patterns")
        id_ = self.prompt_simple("ID", "optional id")
        name = self.prompt_simple("Name", "optional name")
        css_paths = []
        for fpath in css_files:
            dest = f"webmodding/{os.path.basename(fpath)}"
            self.files_to_include[dest] = fpath
            css_paths.append(dest)
            self.log_import(f"Registered css {fpath} -> {dest}")
        entry = {"css": css_paths, "id": id_ or "", "matches": [m.strip() for m in (matches or "").split(",") if m.strip()], "name": name or ""}
        self.data['mod']['payload'].setdefault('page_styles', []).append(entry)
        self.widgets['pages_list'].insert("end", f"{entry['id']} : {entry['name']} -> {', '.join(css_paths)}")

    def edit_page_style(self):
        sel = self.widgets['pages_list'].curselection()
        if not sel: return
        idx = sel[0]
        entry = self.data['mod']['payload']['page_styles'][idx]
        messagebox.showinfo("Page style JSON", json.dumps(entry, indent=2, ensure_ascii=False))

    # Remove helper
    def remove_list_selection(self, payload_key):
        mapping = {
            'app_icon': 'app_icon_list',
            'background_music': 'bgmusic_list',
            'browser_sounds': 'browser_sounds_listbox',
            'keyboard_sounds': 'keyboard_sounds_listbox',
            'cursors': 'cursors_list',
            'fonts': 'fonts_list',
            'mobile_image_overrides': 'mobile_list',
            'splash_screen': 'splash_list',
            'theme': 'theme_list',
            'wallpaper': 'wp_list',
            'page_styles': 'pages_list'
        }
        lbname = mapping.get(payload_key)
        if not lbname:
            return
        lb = self.widgets.get(lbname)
        if not lb:
            return
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        lb.delete(idx)
        try:
            lst = self.data['mod']['payload'].get(payload_key)
            if isinstance(lst, list):
                lst.pop(idx)
                if len(lst) == 0:
                    self.data['mod']['payload'].pop(payload_key, None)
            self.log_import(f"Removed {payload_key}[{idx}]")
        except Exception:
            pass

    # ---------- Import & Auto-register ----------
    def import_manifest(self):
        p = filedialog.askopenfilename(title="Select manifest.json", filetypes=[("JSON","*.json")])
        if not p: return
        try:
            with open(p, "r", encoding="utf-8") as f:
                m = json.load(f)
        except Exception as e:
            messagebox.showerror("Import error", f"Failed to read or parse JSON: {e}")
            return

        self.widgets['import_log'].insert("end", f"Loaded manifest: {p}\n")
        base_dir = os.path.dirname(p)

        # populate top-level info only when meaningful
        name_val = m.get('name')
        if isinstance(name_val, str) and name_val.strip():
            self.widgets['name'].set(name_val.strip())
        version_val = m.get('version')
        if isinstance(version_val, str) and version_val.strip():
            self.widgets['version'].set(version_val.strip())
        author_val = m.get('author')
        if isinstance(author_val, str) and author_val.strip():
            self.widgets['author'].set(author_val.strip())
        dev_val = m.get('developer', {})
        if isinstance(dev_val, dict):
            dn = dev_val.get('name')
            if isinstance(dn, str) and dn.strip():
                self.widgets['developer'].set(dn.strip())
        update_val = m.get('update_url')
        if isinstance(update_val, str) and update_val.strip():
            self.widgets['update_url'].set(update_val.strip())
        desc_val = m.get('description')
        if isinstance(desc_val, str) and desc_val.strip():
            self.widgets['description'].delete("1.0","end"); self.widgets['description'].insert("1.0", desc_val.strip())

        mod = m.get('mod', {}) if isinstance(m.get('mod', {}), dict) else {}
        payload = mod.get('payload', {}) if isinstance(mod.get('payload', {}), dict) else {}

        def register_if_exists(relpath):
            if not relpath or not isinstance(relpath, str): return False
            if os.path.isabs(relpath) and os.path.exists(relpath):
                self.files_to_include[relpath] = relpath; return True
            candidate = os.path.join(base_dir, relpath)
            if os.path.exists(candidate):
                self.files_to_include[relpath] = candidate; return True
            bn = os.path.basename(relpath)
            candidate2 = os.path.join(base_dir, bn)
            if os.path.exists(candidate2):
                self.files_to_include[relpath] = candidate2; return True
            return False

        # Import only the sections that exist in the source manifest and are valid
        # app_icon
        if 'app_icon' in payload and isinstance(payload.get('app_icon'), list):
            self.data['mod']['payload'].setdefault('app_icon', [])
            for a in payload.get('app_icon', []):
                if isinstance(a, dict):
                    self.data['mod']['payload']['app_icon'].append(a)
                    path = a.get('path')
                    if path and register_if_exists(path):
                        self.log_import(f"Auto-registered app_icon {path}")
                    self.widgets['app_icon_list'].insert("end", f"{a.get('id')} : {a.get('name')} -> {a.get('path')}")
            if not self.data['mod']['payload'].get('app_icon'):
                self.data['mod']['payload'].pop('app_icon', None)

        # background_music
        if 'background_music' in payload and isinstance(payload.get('background_music'), list):
            self.data['mod']['payload'].setdefault('background_music', [])
            for bg in payload.get('background_music', []):
                if not isinstance(bg, dict):
                    continue
                tracks = []
                for t in bg.get('tracks', []):
                    if isinstance(t, str) and register_if_exists(t):
                        self.log_import(f"Auto-registered bg track {t}")
                    tracks.append(t)
                bgobj = {"id": bg.get('id','0'), "name": bg.get('name','Background Music'), "tracks": tracks}
                self.data['mod']['payload']['background_music'].append(bgobj)
                self.widgets['bgmusic_list'].insert("end", f"{bgobj['id']} : {bgobj['name']}")
            if not self.data['mod']['payload'].get('background_music'):
                self.data['mod']['payload'].pop('background_music', None)

        # browser & keyboard
        def import_packs(key):
            if key not in payload or not isinstance(payload.get(key), list):
                return
            self.data['mod']['payload'].setdefault(key, [])
            for pack in payload.get(key, []):
                if not isinstance(pack, dict):
                    continue
                sounds = {}
                for ev, arr in pack.get('sounds', {}).items():
                    if not isinstance(ev, str) or not isinstance(arr, list):
                        continue
                    norm = []
                    for it in arr:
                        if isinstance(it, str):
                            if register_if_exists(it):
                                self.log_import(f"Auto-registered sound {it}")
                            norm.append(it)
                        elif isinstance(it, dict) and 'src' in it and isinstance(it['src'], str):
                            src = it['src']
                            if register_if_exists(src):
                                self.log_import(f"Auto-registered sound {src}")
                            norm.append(src)
                    if norm:
                        sounds[ev] = norm
                newpack = {"id": pack.get('id','0'), "name": pack.get('name',''), "sounds": sounds}
                self.data['mod']['payload'][key].append(newpack)
                lb = self.widgets.get(f'{key}_listbox')
                if lb: lb.insert("end", f"{newpack['id']} : {newpack['name']}")
            if not self.data['mod']['payload'].get(key):
                self.data['mod']['payload'].pop(key, None)

        import_packs('browser_sounds')
        import_packs('keyboard_sounds')

        # cursors
        if 'cursors' in payload and isinstance(payload.get('cursors'), list):
            self.data['mod']['payload'].setdefault('cursors', [])
            for cpack in payload.get('cursors', []):
                if not isinstance(cpack, dict):
                    continue
                self.data['mod']['payload']['cursors'].append(cpack)
                for item in cpack.get('items', []):
                    pth = item.get('path')
                    if pth and register_if_exists(pth):
                        self.log_import(f"Auto-registered cursor {pth}")
                self.widgets['cursors_list'].insert("end", f"{cpack.get('id')} : {cpack.get('name')}")
            if not self.data['mod']['payload'].get('cursors'):
                self.data['mod']['payload'].pop('cursors', None)

        # fonts
        if 'fonts' in payload and isinstance(payload.get('fonts', list)):
            self.data['mod']['payload'].setdefault('fonts', [])
            for fpack in payload.get('fonts', []):
                if not isinstance(fpack, dict):
                    continue
                self.data['mod']['payload']['fonts'].append(fpack)
                for part in ('header','body'):
                    for var in fpack.get(part, {}).get('variants', []):
                        pth = var.get('path')
                        if pth and register_if_exists(pth):
                            self.log_import(f"Auto-registered font {pth}")
                self.widgets['fonts_list'].insert("end", f"{fpack.get('id')} : {fpack.get('name')}")
            if not self.data['mod']['payload'].get('fonts'):
                self.data['mod']['payload'].pop('fonts', None)

        # mobile_image_overrides
        if 'mobile_image_overrides' in payload and isinstance(payload.get('mobile_image_overrides'), list):
            self.data['mod']['payload']['mobile_image_overrides'] = payload.get('mobile_image_overrides', [])
            for mo in self.data['mod']['payload']['mobile_image_overrides']:
                for v in (mo.get('images') or {}).values():
                    if v and isinstance(v, str) and "/" in v and register_if_exists(v):
                        self.log_import(f"Auto-registered mobile image {v}")
                self.widgets['mobile_list'].insert("end", f"{mo.get('id')} : {mo.get('name')}")
            if not self.data['mod']['payload'].get('mobile_image_overrides'):
                self.data['mod']['payload'].pop('mobile_image_overrides', None)

        # splash
        if 'splash_screen' in payload and isinstance(payload.get('splash_screen'), list):
            self.data['mod']['payload'].setdefault('splash_screen', [])
            for sp in payload.get('splash_screen', []):
                if not isinstance(sp, dict):
                    continue
                self.data['mod']['payload']['splash_screen'].append(sp)
                if sp.get('path') and register_if_exists(sp['path']):
                    self.log_import(f"Auto-registered splash {sp['path']}")
                self.widgets['splash_list'].insert("end", f"{sp.get('id')} : {sp.get('name')}")
            if not self.data['mod']['payload'].get('splash_screen'):
                self.data['mod']['payload'].pop('splash_screen', None)

        # theme
        if 'theme' in payload and isinstance(payload.get('theme'), list):
            self.data['mod']['payload']['theme'] = payload.get('theme', [])
            for t in self.data['mod']['payload']['theme']:
                self.widgets['theme_list'].insert("end", f"{t.get('id')} : {t.get('name')}")
            if not self.data['mod']['payload'].get('theme'):
                self.data['mod']['payload'].pop('theme', None)

        # wallpaper
        if 'wallpaper' in payload:
            wpval = payload.get('wallpaper')
            if isinstance(wpval, list):
                self.data['mod']['payload']['wallpaper'] = wpval
            elif isinstance(wpval, dict):
                self.data['mod']['payload']['wallpaper'] = [wpval]
            for w in self.data['mod']['payload'].get('wallpaper', []):
                for mode in ('dark','light'):
                    mo = w.get(mode, {})
                    for k,v in mo.items():
                        if isinstance(v, str) and "/" in v and register_if_exists(v):
                            self.log_import(f"Auto-registered wallpaper image {v}")
                self.widgets['wp_list'].insert("end", f"{w.get('id')} : {w.get('name')}")
            if not self.data['mod']['payload'].get('wallpaper'):
                self.data['mod']['payload'].pop('wallpaper', None)

        # page_styles
        if 'page_styles' in payload:
            psval = payload.get('page_styles')
            if isinstance(psval, list):
                self.data['mod']['payload']['page_styles'] = psval
            elif isinstance(psval, dict):
                self.data['mod']['payload']['page_styles'] = [psval]
            for ps in self.data['mod']['payload'].get('page_styles', []):
                for css in ps.get('css', []):
                    if isinstance(css, str) and register_if_exists(css):
                        self.log_import(f"Auto-registered css {css}")
                self.widgets['pages_list'].insert("end", f"{ps.get('id')} : {ps.get('name')}")
            if not self.data['mod']['payload'].get('page_styles'):
                self.data['mod']['payload'].pop('page_styles', None)

        # license/icon - only register if path exists
        lic = mod.get('license') or m.get('mod', {}).get('license')
        if lic and isinstance(lic, str):
            candidate = os.path.join(base_dir, lic) if not os.path.isabs(lic) else lic
            if os.path.exists(candidate):
                self.files_to_include['license.txt'] = candidate
                self.widgets['license_entry'].set(candidate)

        icons = m.get('icons', {})
        if isinstance(icons, dict):
            icon512 = icons.get('512')
            if isinstance(icon512, str):
                cands = [icon512, os.path.join(base_dir, icon512), os.path.join(base_dir, os.path.basename(icon512))]
                for c in cands:
                    if c and os.path.exists(c):
                        self.files_to_include['icon_512.png'] = c
                        self.widgets['icon_entry'].set(c)
                        break

        self.widgets['import_log'].insert("end", "Import complete — review registered files and payload entries.\n")

    def auto_register_from_manifest_folder(self):
        refs = self.collect_current_references()
        if not refs:
            messagebox.showinfo("Auto-scan", "No referenced files found in payload.")
            return
        folder = filedialog.askdirectory(title="Choose folder to scan (manifest folder recommended)")
        if not folder:
            return
        found = 0
        basenames = {os.path.basename(r): r for r in refs}
        for root_dir, _, files in os.walk(folder):
            for fname in files:
                if fname in basenames:
                    rels = [r for r in refs if os.path.basename(r) == fname]
                    for rel in rels:
                        full = os.path.join(root_dir, fname)
                        self.files_to_include[rel] = full
                        found += 1
                        self.log_import(f"Auto-registered {rel} -> {full}")
        messagebox.showinfo("Auto-scan", f"Auto-scan complete: registered {found} files (if any).")

    def collect_current_references(self):
        return collect_referenced_paths_from_payload(self.data['mod']['payload'])

    # ---------- Validation & Auto-fix ----------
    def run_validation(self):
        log = self.widgets['validator_log']
        log.delete("1.0","end")
        issues = []
        payload = self.data['mod']['payload']

        # Only validate structure of optional sections if they exist.
        if 'background_music' in payload:
            bg = payload.get('background_music')
            if not is_nonempty_list_of_dicts(bg):
                issues.append("background_music is present but must be a non-empty array of dicts.")
            else:
                for i, el in enumerate(bg):
                    if not el.get('tracks'):
                        issues.append(f"background_music[{i}] has empty 'tracks' array.")

        for key in ('keyboard_sounds','browser_sounds'):
            if key in payload:
                val = payload.get(key)
                if not is_nonempty_list_of_dicts(val):
                    issues.append(f"{key} is present but must be a non-empty array of pack objects (id,name,sounds).")

        wp = payload.get('wallpaper')
        if wp is not None and not is_nonempty_list_of_dicts(wp):
            issues.append("wallpaper must be a non-empty array of objects when present.")

        # referenced files
        referenced = collect_referenced_paths_from_payload(payload)
        missing = [p for p in referenced if p not in self.files_to_include]
        if missing:
            issues.append("Referenced asset files not registered: " + ", ".join(missing[:8]) + ("" if len(missing)<=8 else " ..."))

        # informative note about icon (not an error)
        if 'icon_512.png' not in self.files_to_include:
            log.insert("end", "NOTE: icon_512.png not registered. Manifest will omit icons unless you register one.\n")

        if not issues:
            log.insert("end", "Validation OK: present sections look valid and referenced files appear registered.\n")
        else:
            for i in issues:
                log.insert("end", "ISSUE: " + i + "\n")
        return issues

    def autofix_all(self):
        payload = self.data['mod']['payload']
        # Only normalize existing sections; do not insert defaults.

        for key in ('keyboard_sounds','browser_sounds'):
            if key not in payload:
                continue
            val = payload.get(key)
            if isinstance(val, dict):
                payload[key] = [{"id": f"{key}_0", "name": key, "sounds": val}]
                self.log_import(f"Auto-fixed {key}: wrapped dict into pack array")
            elif isinstance(val, list):
                newlist = []
                for el in val:
                    if isinstance(el, dict):
                        if 'sounds' not in el:
                            sounds = {}
                            for k, v in el.items():
                                if isinstance(v, list):
                                    sounds[k] = v
                            newlist.append({"id": el.get('id','0'), "name": el.get('name',''), "sounds": sounds})
                            self.log_import(f"Auto-normalized pack in {key}")
                        else:
                            newlist.append(el)
                if newlist:
                    payload[key] = newlist
                else:
                    payload.pop(key, None)
                    self.log_import(f"Removed empty {key}")

        if 'background_music' in payload:
            bg = payload.get('background_music')
            if isinstance(bg, list) and not is_nonempty_list_of_dicts(bg):
                if all(isinstance(i, str) for i in bg):
                    payload['background_music'] = [{"id":"bgm_0","name":"Background Music","tracks": bg}]
                    self.log_import("Auto-fixed background_music: wrapped string array into pack")
                else:
                    newbg = []
                    for el in bg:
                        if isinstance(el, dict) and el.get('tracks'):
                            newbg.append(el)
                        elif isinstance(el, str):
                            newbg.append({"id":"bgm_0","name":"Background Music","tracks":[el]})
                    if newbg:
                        payload['background_music'] = newbg
                        self.log_import("Auto-normalized background_music entries")
                    else:
                        payload.pop('background_music', None)
                        self.log_import("Removed empty background_music (none valid)")

        # wallpaper dict -> array (only if present and is dict)
        if 'wallpaper' in payload:
            wp = payload.get('wallpaper')
            if isinstance(wp, dict):
                payload['wallpaper'] = [wp] if wp else None
                self.log_import("Wrapped wallpaper dict into array")
            if not payload.get('wallpaper'):
                payload.pop('wallpaper', None)

        # page_styles dict -> array (only if present)
        if 'page_styles' in payload:
            ps = payload.get('page_styles')
            if isinstance(ps, dict):
                payload['page_styles'] = [ps]
                self.log_import("Wrapped page_styles dict into array")
            if not payload.get('page_styles'):
                payload.pop('page_styles', None)

        messagebox.showinfo("Auto-fix", "Auto-fix completed. Run Validation again.")

    # ---------- Manifest / Export ----------
    def build_manifest(self):
        manifest = {}
        # include only meaningful top-level fields
        name = self.widgets['name'].get().strip()
        if name:
            manifest['name'] = name
        version = self.widgets['version'].get().strip()
        if version:
            manifest['version'] = version
        author = self.widgets['author'].get().strip()
        if author:
            manifest['author'] = author
        desc = self.widgets['description'].get("1.0","end").strip()
        if desc:
            manifest['description'] = desc
        dev_name = self.widgets['developer'].get().strip()
        if dev_name:
            manifest['developer'] = {"name": dev_name}
        update_url = self.widgets['update_url'].get().strip()
        if update_url:
            manifest['update_url'] = update_url

        # icons: include only if the user registered icon_512.png
        if 'icon_512.png' in self.files_to_include:
            manifest['icons'] = {"512": "icon_512.png"}

        manifest['manifest_version'] = 3

        # Build payload including only keys that exist and are non-empty
        payload = {}
        for key in ('app_icon','background_music','browser_sounds','keyboard_sounds','cursors','fonts',
                    'mobile_image_overrides','splash_screen','theme','wallpaper','page_styles'):
            val = self.data['mod']['payload'].get(key)
            if val:
                payload[key] = val

        mod_obj = {"schema_version": 2}
        if payload:
            mod_obj['payload'] = payload

        # license support: include only when user registered license.txt
        if 'license.txt' in self.files_to_include:
            mod_obj['license'] = 'license.txt'

        manifest['mod'] = mod_obj

        # key (top-level) if present in internal data
        if 'key' in self.data.get('mod', {}) and self.data['mod'].get('key'):
            manifest['key'] = self.data['mod']['key']

        return manifest

    def preview_manifest(self):
        manifest = self.build_manifest()
        s = json.dumps(manifest, indent=2, ensure_ascii=False)
        w = tk.Toplevel(self.root); w.title("manifest.json preview")
        t = tk.Text(w, width=100, height=40); t.pack(fill="both", expand=True)
        t.insert("1.0", s); t.config(state="disabled")

    def export_folder(self):
        out = filedialog.askdirectory(title="Export folder (Load unpacked)")
        if not out: return
        manifest = self.build_manifest()
        referenced = collect_referenced_paths_from_payload(manifest.get('mod', {}).get('payload', {}))

        missing = [p for p in referenced if p not in self.files_to_include]
        if missing:
            if not messagebox.askyesno("Missing files", "Referenced files not registered:\n" + "\n".join(missing[:20]) + "\nContinue export (missing files will be absent)?"):
                return

        payload_map = {k:v for k,v in self.files_to_include.items() if not k.startswith('icon_')}
        flavor_hash = compute_payload_hash(payload_map) if payload_map else md5_bytes(b"")
        manifest.setdefault('mod', {}).setdefault('flavor', {})
        manifest['mod']['flavor']['hash'] = flavor_hash
        manifest['mod']['flavor']['parent_hash'] = md5_bytes(b"")

        try:
            for rel, src in sorted(self.files_to_include.items()):
                dest = os.path.join(out, rel)
                ensure_dir(os.path.dirname(dest))
                if isinstance(src, (bytes, bytearray)):
                    with open(dest, "wb") as fw: fw.write(src)
                    self.log_validator(f"Wrote generated bytes -> {rel}")
                else:
                    if os.path.exists(src):
                        shutil.copy2(src, dest)
                        self.log_validator(f"Copied {src} -> {rel}")
                    else:
                        self.log_validator(f"WARNING: missing source {src} (skipped)")
            # write manifest
            with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as mf:
                json.dump(manifest, mf, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Exported mod folder to:\n{out}\nflavor.hash={flavor_hash}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def export_zip(self):
        out = filedialog.asksaveasfilename(title="Save ZIP as", defaultextension=".zip", filetypes=[("Zip","*.zip")])
        if not out: return
        manifest = self.build_manifest()
        payload_map = {k:v for k,v in self.files_to_include.items() if not k.startswith('icon_')}
        flavor_hash = compute_payload_hash(payload_map) if payload_map else md5_bytes(b"")
        manifest.setdefault('mod', {}).setdefault('flavor', {})
        manifest['mod']['flavor']['hash'] = flavor_hash
        manifest['mod']['flavor']['parent_hash'] = md5_bytes(b"")
        try:
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                for rel, src in sorted(self.files_to_include.items()):
                    if isinstance(src, (bytes, bytearray)):
                        zf.writestr(rel, src)
                        self.log_validator(f"Wrote bytes -> {rel}")
                    else:
                        if os.path.exists(src):
                            zf.write(src, rel)
                            self.log_validator(f"Added {src} -> {rel}")
                        else:
                            self.log_validator(f"WARNING: missing source {src} (skipped)")
                zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            messagebox.showinfo("ZIP Exported", f"Wrote ZIP: {out}\nflavor.hash={flavor_hash}")
        except Exception as e:
            messagebox.showerror("ZIP error", str(e))

    # ---------- Utility dialogs ----------
    def generate_auto_id(self, prefix, existing_list):
        used = set()
        for e in existing_list:
            if isinstance(e, dict) and 'id' in e:
                used.add(str(e['id']))
        i = 0
        base = prefix.replace(" ", "_")
        while True:
            candidate = f"{base}_{i}"
            if candidate not in used:
                return candidate
            i += 1

    def simple_entry_dialog(self, title, fields, auto_id_prefix=None, existing=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.transient(self.root); win.grab_set()
        vars = {}
        auto_var = tk.BooleanVar(value=True)

        for f in fields:
            r = ttk.Frame(win); r.pack(fill="x", padx=8, pady=4)
            ttk.Label(r, text=f + ":", width=12).pack(side="left")
            v = tk.StringVar(); vars[f] = v
            ttk.Entry(r, textvariable=v).pack(side="left", fill="x", expand=True)
            if f == "id" and auto_id_prefix:
                def apply_auto(v=v):
                    if auto_var.get():
                        v.set(self.generate_auto_id(auto_id_prefix, existing or []))
                chk = ttk.Checkbutton(r, text="AUTO", variable=auto_var, command=apply_auto)
                chk.pack(side="right", padx=6)
                apply_auto()

        res = {'ok': False}
        def on_ok():
            res['ok'] = True
            win.destroy()
        ttk.Button(win, text="OK", command=on_ok).pack(pady=8)
        win.wait_window()
        if not res['ok']:
            return None
        return {k: vars[k].get().strip() for k in fields}

    def choose_from_list(self, title, options):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.transient(self.root); win.grab_set()
        ttk.Label(win, text=title).pack(padx=8, pady=6)
        lb = tk.Listbox(win, height=min(12, max(6, len(options)+1)))
        lb.pack(fill="both", expand=True, padx=8, pady=4)
        for o in options:
            lb.insert("end", o)
        res = {'v': None}
        def ok():
            sel = lb.curselection()
            if sel:
                res['v'] = lb.get(sel[0])
            win.destroy()
        ttk.Button(win, text="OK", command=ok).pack(pady=6)
        win.wait_window()
        return res['v']

    def prompt_simple(self, title, prompt):
        win = tk.Toplevel(self.root)
        win.title(title); win.transient(self.root); win.grab_set()
        ttk.Label(win, text=prompt).pack(padx=8, pady=6)
        v = tk.StringVar(); ttk.Entry(win, textvariable=v).pack(fill="x", padx=8)
        res = {'v': None}
        def ok():
            res['v'] = v.get().strip(); win.destroy()
        ttk.Button(win, text="OK", command=ok).pack(pady=6)
        win.wait_window()
        return res['v']

    # ---------- Import / log helpers ----------
    def log_import(self, txt):
        try:
            self.widgets['import_log'].insert("end", txt + "\n"); self.widgets['import_log'].see("end")
        except Exception:
            print(txt)

    def log_validator(self, txt):
        try:
            self.widgets['validator_log'].insert("end", txt + "\n"); self.widgets['validator_log'].see("end")
        except Exception:
            print(txt)

    # ---------- Small helpers ----------
    def choose_from_combobox(self, title, options):
        return self.choose_from_list(title, options)
