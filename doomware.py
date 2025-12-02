import os
import sys
import json
import time
import random
import string
import math
import threading

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk

# External deps:
#   pip install pyautogui pyperclip requests pygetwindow keyboard
try:
    import pyautogui
    import pyperclip
    import requests
    import pygetwindow as gw
    import keyboard
except ImportError:
    print("Missing modules. Run:")
    print("  pip install pyautogui pyperclip requests pygetwindow keyboard")
    input("Press ENTER to exit...")
    raise SystemExit

pyautogui.FAILSAFE = True

APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
BASE_FOLDER = os.path.join(APPDATA, "Doomware")
os.makedirs(BASE_FOLDER, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(BASE_DIR, "doomware.ico")

CFG_PATH = os.path.join(BASE_FOLDER, "doomware_config.json")

DEFAULT_CFG = {
    "cooldown": 10,
    "cooldown_enabled": True,
    "discord_webhook": "",
    "speed_preset": "fast",
    "theme": "InfernalRed",
    "topmost": True,
    "alpha_idle": 0.96,
    "alpha_running": 0.75,
    "clickthrough_running": True,
    "big_wait": 7,
    "p2_coords": {
        "step1": {"x": 1382, "y": 943},
        "step2": {"x": 700, "y": 714},
        "step3a": {"x": 749, "y": 969},
        "step3b": {"x": 1104, "y": 968},
        "step3c": {"x": 960, "y": 1013}
    },
}

IMAGE_NAMES = [f"{i}.jpg" for i in range(1, 103)]
BASE_URL = "https://github.com/EdgeSlayer/my-images/blob/main/{image}?raw=true"


def generate_chaos_string(length=32):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def pick_new_image(last_image=None):
    choices = [img for img in IMAGE_NAMES if img != last_image]
    return random.choice(choices) if choices else random.choice(IMAGE_NAMES)


def perform_chaos_roll(last_image):
    image = pick_new_image(last_image)
    chaos = generate_chaos_string()
    url = BASE_URL.format(image=image) + f"&token={chaos}"
    pyperclip.copy(url)
    return image, url


def send_discord_webhook(webhook_url, message):
    if not webhook_url:
        return
    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        return
    try:
        requests.post(webhook_url, json={"content": message}, timeout=5)
    except Exception:
        pass


THEMES = {
    "InfernalRed": {
        "root_bg": "#050509",
        "panel_bg": "#050509",
        "top_bg": "#111111",
        "text": "#cccccc",
        "muted_text": "#888888",
        "accent": "#ff3333",
        "accent_soft": "#ff6666",
        "accent_ok": "#33ff66",
        "accent_stop": "#ff3333",
        "entry_bg": "#111111",
        "button_bg": "#222222",
        "button_active_bg": "#444444",
        "button_fg": "#ffffff",
    },
    "Sakura": {
        "root_bg": "#0b0508",
        "panel_bg": "#160914",
        "top_bg": "#1c0c16",
        "text": "#f8e9f4",
        "muted_text": "#cba9cf",
        "accent": "#ff9ad5",
        "accent_soft": "#ffb7e3",
        "accent_ok": "#b4ffcf",
        "accent_stop": "#ff6b9c",
        "entry_bg": "#1e1018",
        "button_bg": "#2a1521",
        "button_active_bg": "#3b1c2c",
        "button_fg": "#ffe9ff",
    },
    "Neon": {
        "root_bg": "#05030a",
        "panel_bg": "#080515",
        "top_bg": "#120a2a",
        "text": "#d8cfff",
        "muted_text": "#9a8ed6",
        "accent": "#c064ff",
        "accent_soft": "#e28dff",
        "accent_ok": "#6dffda",
        "accent_stop": "#ff4fa8",
        "entry_bg": "#120a2a",
        "button_bg": "#1e0f3c",
        "button_active_bg": "#2d1755",
        "button_fg": "#f0e6ff",
    },
}

SPEED_MULTIPLIERS = {
    "slow": 0.7,
    "normal": 1.0,
    "fast": 1.4,
    "extreme": 1.9,
    "chaos": 2.4,
}

ASCII_TITLE = """\
██████╗  ██████╗  ██████╗ ███╗   ███╗██╗    ██╗ █████╗ ██████╗ ███████╗
██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║██║    ██║██╔══██╗██╔══██╗██╔════╝
██║  ██║██║   ██║██║   ██║██╔████╔██║██║ █╗ ██║███████║██████╔╝█████╗  
██║  ██║██║   ██║██║   ██║██╔██╔██║██║███╗██║██╔══██║██╔══██╗██╔══╝   
██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║╚███╔███╔╝██║  ██║██║  ██║███████╗
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
"""


def ensure_admin():
    if os.name != "nt":
        return
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("WARNING: Not running as admin. Global hotkeys / click-through may be limited.")
    except Exception:
        pass


def choose_profile():
    root = tk.Tk()
    root.title("Doomware Profile")
    root.configure(bg="#050509")
    root.resizable(False, False)

    w, h = 260, 150
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 3
    root.geometry(f"{w}x{h}+{x}+{y}")

    var = tk.StringVar(value="Profile 1")

    font_lbl = tkFont.Font(family="Consolas", size=10, weight="bold")
    font_opt = tkFont.Font(family="Consolas", size=9)

    tk.Label(root, text="Choose profile to load:", font=font_lbl, bg="#050509", fg="#ffffff").pack(pady=(12, 6))

    for name in ["Profile 1", "Profile 2"]:
        tk.Radiobutton(
            root, text=name, value=name, variable=var,
            font=font_opt, anchor="w", justify="left",
            bg="#050509", fg="#dddddd", selectcolor="#111111"
        ).pack(anchor="w", padx=24)

    def on_ok():
        root.quit()

    btn = tk.Button(root, text="Start", command=on_ok, width=10)
    btn.pack(pady=(10, 8))

    root.bind("<Return>", lambda e: on_ok())

    root.mainloop()
    choice = var.get()
    root.destroy()
    return choice


class DoomwareHUD(tk.Tk):
    def __init__(self, profile_name):
        super().__init__()

        self.profile_name = profile_name

        self.title("Doomware")
        self.config(bg="#050509")
        self.overrideredirect(True)

        if os.path.exists(ICO_PATH):
            try:
                self.iconbitmap(ICO_PATH)
            except Exception:
                pass

        self._drag_data = {"x": 0, "y": 0}

        self.cfg = self.load_or_default_cfg()
        self.running = False
        self.end_after_current = False
        self.last_image = None
        self.roll_count = 0
        self.start_time = time.time()
        self.macro_thread = None
        self.speed_factor = SPEED_MULTIPLIERS.get(
            self.cfg.get("speed_preset", "fast"), SPEED_MULTIPLIERS["fast"]
        )
        # Profile 2 coordinate state
        self.p2_coords = self.cfg.get("p2_coords", DEFAULT_CFG.get("p2_coords", {})).copy()
        self._capture_target = None

        # click-through stuff
        self._clickthrough_enabled = False
        self._hwnd = None
        if os.name == "nt":
            import ctypes
            self.ctypes = ctypes
            self.GWL_EXSTYLE = -20
            self.WS_EX_LAYERED = 0x00080000
            self.WS_EX_TRANSPARENT = 0x00000020
        else:
            self.ctypes = None

        self.build_ui()
        self.center_window()
        self.apply_theme(self.cfg.get("theme", "InfernalRed"))
        self.apply_idle_visuals()
        self.update_uptime()

        # ESC kills
        self.bind_all("<Escape>", self.on_escape)

        # global hotkeys
        if keyboard is not None:
            try:
                keyboard.add_hotkey("f8", self.toggle_topmost)
                keyboard.add_hotkey("f9", self.toggle_clickthrough)
                keyboard.add_hotkey("f10", self.request_end_after_current)
            except Exception:
                pass

    # ------------ config ------------
    def load_or_default_cfg(self):
        if not os.path.exists(CFG_PATH):
            return DEFAULT_CFG.copy()
        try:
            with open(CFG_PATH, "r") as f:
                data = json.load(f)

            # ensure all top-level keys exist
            for k, v in DEFAULT_CFG.items():
                if k not in data:
                    data[k] = v

            # ensure nested p2_coords exists and has all steps
            if "p2_coords" not in data:
                data["p2_coords"] = DEFAULT_CFG["p2_coords"].copy()
            else:
                for step_key, step_val in DEFAULT_CFG["p2_coords"].items():
                    if step_key not in data["p2_coords"]:
                        data["p2_coords"][step_key] = step_val

            return data
        except Exception:
            return DEFAULT_CFG.copy()

    def save_cfg(self):
        try:
            # keep p2_coords in sync with latest edits
            if hasattr(self, "p2_coords") and isinstance(self.p2_coords, dict):
                self.cfg["p2_coords"] = self.p2_coords
            with open(CFG_PATH, "w") as f:
                json.dump(self.cfg, f, indent=4)
        except Exception:
            pass

    # ------------ UI ------------
    def center_window(self):
        self.update_idletasks()
        w = 920
        h = 420
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 3
        self.geometry(f"{w}x{h}+{x}+{y}")

    def build_ui(self):
        font_title = tkFont.Font(family="Consolas", size=9)
        font_text = tkFont.Font(family="Consolas", size=10)
        font_btn = tkFont.Font(family="Consolas", size=10, weight="bold")

        self.main = tk.Frame(self, bg="#050509")
        self.main.pack(expand=True, fill="both", padx=8, pady=8)
        self.main.pack_propagate(False)

        self.top = tk.Frame(self.main, bg="#111111", height=28)
        self.top.pack(fill="x", side="top")
        self.top.pack_propagate(False)
        self.top.bind("<ButtonPress-1>", self.start_drag)
        self.top.bind("<B1-Motion>", self.do_drag)

        self.title_lbl = tk.Label(
            self.top, text=" DOOMWARE HUD", bg="#111111", fg="#ff3333",
            font=font_btn
        )
        self.title_lbl.pack(side="left", padx=4)
        self.title_lbl.bind("<ButtonPress-1>", self.start_drag)
        self.title_lbl.bind("<B1-Motion>", self.do_drag)

        close_btn = tk.Button(
            self.top, text="X", command=self.hard_quit,
            bg="#330000", fg="#ffffff",
            activebackground="#550000",
            activeforeground="#ffffff",
            relief="flat", font=font_btn, width=3
        )
        close_btn.pack(side="right", padx=4, pady=2)

        self.profile_lbl = tk.Label(
            self.top,
            text=f"PROFILE: {self.profile_name}",
            font=font_text, fg="#aaaaaa", bg="#111111",
            anchor="e", justify="right"
        )
        self.profile_lbl.pack(side="right")

        self.ascii_lbl = tk.Label(
            self.main,
            text=ASCII_TITLE,
            font=font_title,
            bg="#050509",
            fg="#ff3333",
            justify="left"
        )
        self.ascii_lbl.pack(anchor="w", pady=(4, 6))

        self.status_lbl = tk.Label(
            self.main, text="DOOMWARE LAUNCHING...",
            font=font_text, fg="#cccccc", bg="#050509", anchor="w", justify="left"
        )
        self.status_lbl.pack(anchor="w")

        self.chaos_lbl = tk.Label(
            self.main, text="CHAOS STRING: --------",
            font=font_text, fg="#66ccff", bg="#050509", anchor="w", justify="left"
        )
        self.chaos_lbl.pack(anchor="w", pady=(4, 0))

        self.url_lbl = tk.Label(
            self.main, text="URL: (none yet)",
            font=font_text, fg="#888888", bg="#050509",
            anchor="w", justify="left", wraplength=880
        )
        self.url_lbl.pack(anchor="w", pady=(2, 4))

        stats = tk.Frame(self.main, bg="#050509")
        stats.pack(anchor="w", pady=(4, 8))

        self.rolls_lbl = tk.Label(stats, text="ROLLS: 0",
                                  font=font_text, fg="#aaaaaa", bg="#050509")
        self.rolls_lbl.pack(side="left", padx=(0, 20))

        self.uptime_lbl = tk.Label(stats, text="UPTIME: 00:00",
                                   font=font_text, fg="#aaaaaa", bg="#050509")
        self.uptime_lbl.pack(side="left")

        cfg_frame = tk.Frame(self.main, bg="#050509")
        cfg_frame.pack(anchor="w", pady=(4, 8))

        # big wait
        tk.Label(cfg_frame, text="BIG WAIT (S):", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=0, column=0, sticky="w")
        self.big_wait_var = tk.StringVar(value=str(self.cfg.get("big_wait", 7)))
        tk.Entry(
            cfg_frame, textvariable=self.big_wait_var, width=6,
            font=font_text, bg="#111111", fg="#ffffff", insertbackground="#ffffff"
        ).grid(row=0, column=1, padx=(4, 12))

        # cooldown
        tk.Label(cfg_frame, text="COOLDOWN (S):", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=0, column=2, sticky="w")

        self.cooldown_enabled_var = tk.BooleanVar(value=self.cfg.get("cooldown_enabled", True))
        tk.Checkbutton(
            cfg_frame, text="Enable", variable=self.cooldown_enabled_var,
            font=font_text, fg="#cccccc", bg="#050509",
            selectcolor="#111111", activebackground="#050509",
            activeforeground="#ffffff"
        ).grid(row=0, column=3, sticky="w", padx=(4, 4))

        self.cooldown_var = tk.StringVar(value=str(self.cfg.get("cooldown", 10)))
        tk.Entry(
            cfg_frame, textvariable=self.cooldown_var, width=6,
            font=font_text, bg="#111111", fg="#ffffff", insertbackground="#ffffff"
        ).grid(row=0, column=4, padx=(4, 12))

        # speed
        tk.Label(cfg_frame, text="SPEED:", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.speed_var = tk.StringVar(value=self.cfg.get("speed_preset", "fast"))
        self.speed_combo = ttk.Combobox(
            cfg_frame, textvariable=self.speed_var,
            values=list(SPEED_MULTIPLIERS.keys()),
            width=10, state="readonly"
        )
        self.speed_combo.grid(row=1, column=1, padx=(4, 12), pady=(4, 0))

        # theme
        tk.Label(cfg_frame, text="THEME:", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=1, column=2, sticky="w", pady=(4, 0))
        self.theme_var = tk.StringVar(value=self.cfg.get("theme", "InfernalRed"))
        self.theme_combo = ttk.Combobox(
            cfg_frame, textvariable=self.theme_var,
            values=list(THEMES.keys()),
            width=14, state="readonly"
        )
        self.theme_combo.grid(row=1, column=3, padx=(4, 12), pady=(4, 0), sticky="w")

        # topmost
        self.topmost_var = tk.BooleanVar(value=self.cfg.get("topmost", True))
        tk.Checkbutton(
            cfg_frame, text="TOPMOST", variable=self.topmost_var,
            font=font_text, fg="#cccccc", bg="#050509",
            selectcolor="#111111", activebackground="#050509",
            activeforeground="#ffffff"
        ).grid(row=1, column=4, sticky="w", padx=(4, 8))

        # clickthrough
        self.clickthrough_run_var = tk.BooleanVar(
            value=self.cfg.get("clickthrough_running", True)
        )
        tk.Checkbutton(
            cfg_frame, text="Click-through while running", variable=self.clickthrough_run_var,
            font=font_text, fg="#cccccc", bg="#050509",
            selectcolor="#111111", activebackground="#050509",
            activeforeground="#ffffff"
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=(4, 8), pady=(4, 0))

        # webhook
        tk.Label(cfg_frame, text="DISCORD WEBHOOK:", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=3, column=0, sticky="w", pady=(4, 0))
        self.webhook_var = tk.StringVar(value=self.cfg.get("discord_webhook", ""))
        tk.Entry(
            cfg_frame, textvariable=self.webhook_var, width=60,
            font=font_text, bg="#111111", fg="#ffffff", insertbackground="#ffffff"
        ).grid(row=3, column=1, columnspan=3, padx=(4, 0), pady=(4, 0), sticky="w")

        save_btn = tk.Button(
            cfg_frame, text="SAVE CONFIG",
            command=self.on_save_cfg,
            font=font_btn, bg="#222222", fg="#ffffff",
            activebackground="#444444", activeforeground="#ffffff",
            relief="flat"
        )
        save_btn.grid(row=0, column=5, rowspan=4, padx=(12, 0))

        # controls
        ctrl = tk.Frame(self.main, bg="#050509")
        ctrl.pack(anchor="w", pady=(8, 0))

        self.start_btn = tk.Button(
            ctrl, text="START",
            command=self.start_macro,
            font=font_btn, bg="#33ff66", fg="#050509",
            activebackground="#22cc55", activeforeground="#050509",
            relief="flat", width=10
        )
        self.start_btn.pack(side="left")

        self.stop_btn = tk.Button(
            ctrl, text="STOP",
            command=self.stop_macro,
            font=font_btn, bg="#ff3333", fg="#ffffff",
            activebackground="#cc0000", activeforeground="#ffffff",
            relief="flat", width=10
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        self.end_after_btn = tk.Button(
            ctrl, text="END AFTER CURRENT",
            command=self.request_end_after_current,
            font=font_btn, bg="#444444", fg="#ffffff",
            activebackground="#666666", activeforeground="#ffffff",
            relief="flat", width=20
        )
        self.end_after_btn.pack(side="left", padx=(8, 0))

        # Profile 2 coordinate editor button
        self.p2_coord_btn = tk.Button(
            ctrl,
            text="PROFILE 2 COORDINATES",
            command=self.open_p2_editor,
            font=font_btn,
            bg="#222222",
            fg="#ffffff",
            activebackground="#444444",
            activeforeground="#ffffff",
            relief="flat",
            width=22
        )
        self.p2_coord_btn.pack(side="left", padx=(8, 0))

        hint = tk.Label(
            self.main,
            text="Profile 1: CHAOS + macro   |   Profile 2: macro only   |   Loop: (optional cooldown between runs).",
            font=font_text, fg="#777777", bg="#050509",
            anchor="w", justify="left", wraplength=880
        )
        hint.pack(anchor="w", pady=(12, 12))

        self.status_lbl.config(text="READY. SET SETTINGS AND PRESS START.")

    # ------------ Profile 2 coordinate editor ------------
    def open_p2_editor(self):
        # Only meaningful for Profile 2, but you can still open it.
        if hasattr(self, "p2_editor") and self.p2_editor.winfo_exists():
            self.p2_editor.lift()
            return

        self.p2_editor = tk.Toplevel(self)
        self.p2_editor.title("Profile 2 Coordinates")
        self.p2_editor.geometry("360x340")
        self.p2_editor.configure(bg="#111111")
        self.p2_editor.resizable(False, False)

        font_lbl = tkFont.Font(family="Consolas", size=10)
        font_btn = tkFont.Font(family="Consolas", size=10, weight="bold")

        container = tk.Frame(self.p2_editor, bg="#111111")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            container,
            text="PROFILE 2 CLICK COORDINATES (PIXELS)",
            fg="#ffffff",
            bg="#111111",
            font=font_lbl
        ).pack(anchor="w", pady=(0, 6))

        rows_frame = tk.Frame(container, bg="#111111")
        rows_frame.pack(fill="x", expand=True)

        def make_row(parent, label, key):
            row = tk.Frame(parent, bg="#111111")
            row.pack(fill="x", pady=4)

            tk.Label(row, text=label, fg="#ffffff", bg="#111111", font=font_lbl)\
                .pack(side="left")

            x_var = tk.StringVar(value=str(self.p2_coords.get(key, {}).get("x", 0)))
            x_entry = tk.Entry(
                row,
                textvariable=x_var,
                width=6,
                bg="#000000",
                fg="#00ff99",
                insertbackground="#00ff99"
            )
            x_entry.pack(side="left", padx=(6, 4))

            y_var = tk.StringVar(value=str(self.p2_coords.get(key, {}).get("y", 0)))
            y_entry = tk.Entry(
                row,
                textvariable=y_var,
                width=6,
                bg="#000000",
                fg="#00ff99",
                insertbackground="#00ff99"
            )
            y_entry.pack(side="left", padx=(4, 6))

            btn = tk.Button(
                row,
                text="SET",
                width=5,
                font=font_btn,
                bg="#222222",
                fg="#ffffff",
                activebackground="#444444",
                activeforeground="#ffffff",
                command=lambda: self.start_click_capture(key, x_var, y_var)
            )
            btn.pack(side="left")

            return x_var, y_var

        self.p2_vars = {
            "step1": make_row(rows_frame, "Step 1:", "step1"),
            "step2": make_row(rows_frame, "Step 2:", "step2"),
            "step3a": make_row(rows_frame, "Step 3A:", "step3a"),
            "step3b": make_row(rows_frame, "Step 3B:", "step3b"),
            "step3c": make_row(rows_frame, "Step 3C:", "step3c"),
        }

        save_btn = tk.Button(
            container,
            text="SAVE",
            font=font_btn,
            command=self.save_p2_editor,
            bg="#00aa44",
            fg="#ffffff",
            activebackground="#00cc55",
            activeforeground="#ffffff",
            relief="flat",
            width=10
        )
        save_btn.pack(pady=(12, 0))

    def save_p2_editor(self):
        # Read values from the popup and sync into self.p2_coords / cfg
        for key, (x_var, y_var) in self.p2_vars.items():
            try:
                x_val = int(x_var.get())
                y_val = int(y_var.get())
            except ValueError:
                continue
            if key not in self.p2_coords:
                self.p2_coords[key] = {}
            self.p2_coords[key]["x"] = x_val
            self.p2_coords[key]["y"] = y_val

        self.cfg["p2_coords"] = self.p2_coords
        self.save_cfg()
        self.status_lbl.config(text="PROFILE 2 COORDINATES SAVED.")

    def start_click_capture(self, key, x_var, y_var):
        # Hide HUD and editor, then wait for the next mouse move to capture position
        self._capture_target = (key, x_var, y_var)
        self._capture_initial_pos = pyautogui.position()

        # hide windows so they don't get in the way
        try:
            self.withdraw()
        except Exception:
            pass
        if hasattr(self, "p2_editor") and self.p2_editor.winfo_exists():
            try:
                self.p2_editor.withdraw()
            except Exception:
                pass

        # poll for a changed mouse position
        self.after(50, self._poll_capture_click)

    def _poll_capture_click(self):
        if not self._capture_target:
            return

        key, x_var, y_var = self._capture_target
        current = pyautogui.position()

        if current != getattr(self, "_capture_initial_pos", None):
            x, y = current
            x_var.set(str(x))
            y_var.set(str(y))

            if key not in self.p2_coords:
                self.p2_coords[key] = {}
            self.p2_coords[key]["x"] = x
            self.p2_coords[key]["y"] = y

            # restore windows
            try:
                self.deiconify()
            except Exception:
                pass
            if hasattr(self, "p2_editor") and self.p2_editor.winfo_exists():
                try:
                    self.p2_editor.deiconify()
                except Exception:
                    pass

            self.status_lbl.config(text=f"Captured for {key}: {x}, {y}")
            self._capture_target = None
            return

        # keep polling
        self.after(50, self._poll_capture_click)

    # ------------ drag ------------
    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    # ------------ config save ------------
    def on_save_cfg(self):
        try:
            bw = int(self.big_wait_var.get())
            if bw < 0:
                bw = 0
            self.cfg["big_wait"] = bw
        except ValueError:
            self.cfg["big_wait"] = DEFAULT_CFG["big_wait"]
            self.big_wait_var.set(str(self.cfg["big_wait"]))

        try:
            cd = int(self.cooldown_var.get())
            if cd < 0:
                cd = 0
            self.cfg["cooldown"] = cd
        except ValueError:
            self.cfg["cooldown"] = DEFAULT_CFG["cooldown"]
            self.cooldown_var.set(str(self.cfg["cooldown"]))

        self.cfg["cooldown_enabled"] = bool(self.cooldown_enabled_var.get())
        self.cfg["discord_webhook"] = self.webhook_var.get().strip()
        self.cfg["theme"] = self.theme_var.get()
        self.cfg["speed_preset"] = self.speed_var.get()
        self.cfg["topmost"] = bool(self.topmost_var.get())
        self.cfg["clickthrough_running"] = bool(self.clickthrough_run_var.get())

        self.speed_factor = SPEED_MULTIPLIERS.get(
            self.cfg["speed_preset"], SPEED_MULTIPLIERS["fast"]
        )

        self.save_cfg()
        self.apply_theme(self.cfg["theme"])
        self.apply_idle_visuals()
        self.status_lbl.config(text="CONFIG SAVED.")

    # ------------ uptime ------------
    def update_uptime(self):
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        self.uptime_lbl.config(text=f"UPTIME: {m:02d}:{s:02d}")
        self.after(1000, self.update_uptime)

    # ------------ visuals / theme ------------
    def apply_theme(self, key):
        if key not in THEMES:
            key = "InfernalRed"
        t = THEMES[key]

        self.config(bg=t["root_bg"])
        self.main.config(bg=t["panel_bg"])
        self.top.config(bg=t["top_bg"])

        self.title_lbl.config(bg=t["top_bg"], fg=t["accent"])
        self.profile_lbl.config(bg=t["top_bg"], fg=t["text"])
        self.ascii_lbl.config(bg=t["panel_bg"], fg=t["accent"])
        self.status_lbl.config(bg=t["panel_bg"], fg=t["text"])
        self.chaos_lbl.config(bg=t["panel_bg"], fg=t["accent_soft"])
        self.url_lbl.config(bg=t["panel_bg"], fg=t["muted_text"])
        self.rolls_lbl.config(bg=t["panel_bg"], fg=t["text"])
        self.uptime_lbl.config(bg=t["panel_bg"], fg=t["text"])

        for child in self.main.winfo_children():
            if isinstance(child, tk.Frame) and child not in (self.main, self.top):
                child.config(bg=t["panel_bg"])

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "TCombobox",
            fieldbackground=t["entry_bg"],
            background=t["entry_bg"],
            foreground=t["text"],
        )
        self.speed_combo.configure(style="TCombobox")
        self.theme_combo.configure(style="TCombobox")

    def apply_idle_visuals(self):
        try:
            self.attributes("-alpha", float(self.cfg.get("alpha_idle", 0.96)))
        except Exception:
            pass
        try:
            self.attributes("-topmost", bool(self.cfg.get("topmost", True)))
        except Exception:
            pass
        self.disable_clickthrough()

    def apply_running_visuals(self):
        try:
            self.attributes("-alpha", float(self.cfg.get("alpha_running", 0.75)))
        except Exception:
            pass
        try:
            self.attributes("-topmost", bool(self.cfg.get("topmost", True)))
        except Exception:
            pass
        if self.clickthrough_run_var.get():
            self.enable_clickthrough()
        else:
            self.disable_clickthrough()

    # ------------ click-through ------------
    def _get_hwnd(self):
        if self._hwnd is None:
            self.update_idletasks()
            self._hwnd = self.winfo_id()
        return self._hwnd

    def enable_clickthrough(self):
        if self.ctypes is None:
            return
        hwnd = self._get_hwnd()
        if not hwnd:
            return
        user32 = self.ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, self.GWL_EXSTYLE)
        style |= (self.WS_EX_LAYERED | self.WS_EX_TRANSPARENT)
        user32.SetWindowLongW(hwnd, self.GWL_EXSTYLE, style)
        self._clickthrough_enabled = True

    def disable_clickthrough(self):
        if self.ctypes is None:
            return
        if not self._clickthrough_enabled:
            return
        hwnd = self._get_hwnd()
        if not hwnd:
            return
        user32 = self.ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, self.GWL_EXSTYLE)
        style &= ~self.WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, self.GWL_EXSTYLE, style)
        self._clickthrough_enabled = False

    def toggle_topmost(self):
        v = not self.topmost_var.get()
        self.topmost_var.set(v)
        self.cfg["topmost"] = bool(v)
        self.apply_idle_visuals()

    def toggle_clickthrough(self):
        if self._clickthrough_enabled:
            self.disable_clickthrough()
        else:
            self.enable_clickthrough()

    # ------------ macro helpers ------------
    def sleep_scaled(self, base_min, base_max):
        dur = random.uniform(base_min, base_max)
        dur = dur / max(self.speed_factor, 0.1)
        time.sleep(max(dur, 0.001))

    def click_pct(self, x_pct, y_pct):
        screen_width, screen_height = pyautogui.size()
        x = int(screen_width * x_pct)
        y = int(screen_height * y_pct)
        pyautogui.moveTo(x, y)
        pyautogui.click()

    def wait_for_chrome(self, title_contains="Chrome"):
        while True:
            wins = gw.getWindowsWithTitle(title_contains)
            if wins:
                return wins[0]
            time.sleep(0.3)

    # ------------ profile macro bodies ------------
    def run_macro_once(self):
        """Shared macro body, profile 1 will add chaos before this."""
        # hotkey
        pyautogui.hotkey("ctrl", "alt", "g")

        # focus chrome
        chrome_win = self.wait_for_chrome("Chrome")
        if chrome_win.isMinimized:
            chrome_win.restore()
            time.sleep(0.4)
        try:
            chrome_win.activate()
        except Exception:
            pass
        time.sleep(0.3)

        if self.profile_name == "Profile 1":
            self._macro_profile1()
        else:
            self._macro_profile2()

    def _macro_profile1(self):
        """Original profile 1 sequence, using your 1920x1080 coords as %."""
        # 1255,101 → (0.653, 0.093)
        self.click_pct(0.653, 0.093)
        self.sleep_scaled(0.4, 0.9)

        # 870,716 → (0.453, 0.663)
        self.click_pct(0.453, 0.663)
        self.sleep_scaled(0.4, 0.9)

        # 1400,966 → (0.729, 0.894)
        self.click_pct(0.729, 0.894)
        self.sleep_scaled(0.4, 0.9)

        # 695,730 → (0.362, 0.676)
        self.click_pct(0.362, 0.676)

        # paste chaos URL
        pyautogui.hotkey("ctrl", "v")
        self.sleep_scaled(0.7, 1.4)

        final_pct_choices = [
            (0.389, 0.917),  # 746,991
            (0.389, 0.917),  # repeat
            (0.501, 0.954),  # 963,1031
        ]
        px, py = random.choice(final_pct_choices)
        self.click_pct(px, py)
        self.sleep_scaled(0.4, 0.9)

    def _macro_profile2(self):
        """Profile 2: coordinates driven by editable pixel values."""
        coords = self.cfg.get("p2_coords", DEFAULT_CFG.get("p2_coords", {}))

        def click_key(k):
            if k not in coords:
                return
            x = int(coords[k].get("x", 0))
            y = int(coords[k].get("y", 0))
            pyautogui.moveTo(x, y)
            pyautogui.click()

        # Step 1
        click_key("step1")
        self.sleep_scaled(0.4, 0.9)

        # Step 2
        click_key("step2")
        self.sleep_scaled(0.4, 0.9)

        # Step 3 - random A/B/C
        choice = random.choice(["step3a", "step3b", "step3c"])
        click_key(choice)
        self.sleep_scaled(0.4, 0.9)

    # ------------ chaos animation ------------
    def do_chaos_cycle(self):
        if self.profile_name != "Profile 1":
            return None, None

        img, url = perform_chaos_roll(self.last_image)

        base_text = ASCII_TITLE
        glitch_chars = "#$%@&X*"
        try:
            for _ in range(3):
                glitched = []
                for line in base_text.splitlines():
                    new_line = "".join(
                        random.choice(glitch_chars)
                        if (c != " " and random.random() < 0.18)
                        else c
                        for c in line
                    )
                    glitched.append(new_line)
                self.ascii_lbl.config(text="\n".join(glitched), fg="#ff6666")
                self.update_idletasks()
                time.sleep(0.05)
            t = THEMES.get(self.cfg.get("theme", "InfernalRed"), THEMES["InfernalRed"])
            self.ascii_lbl.config(text=ASCII_TITLE, fg=t["accent"])
        except Exception:
            self.ascii_lbl.config(text=ASCII_TITLE)

        self.chaos_lbl.config(text="CHAOS STRING COPIED.")
        self.url_lbl.config(text=f"URL: {url}")
        return img, url

    # ------------ macro control ------------
    def start_macro(self):
        if self.running:
            return
        self.on_save_cfg()
        self.running = True
        self.end_after_current = False
        self.roll_count = 0
        self.status_lbl.config(text="STARTING SOON... OPEN CHROME AND GET READY.")
        self.apply_running_visuals()

        self.macro_thread = threading.Thread(target=self._macro_worker, daemon=True)
        self.macro_thread.start()

    def stop_macro(self):
        self.running = False
        self.status_lbl.config(text="STOPPING MACRO...")
        self.apply_idle_visuals()

    def request_end_after_current(self):
        if not self.running:
            self.status_lbl.config(text="NO MACRO RUNNING.")
            return
        self.end_after_current = True
        self.status_lbl.config(text="WILL STOP AFTER CURRENT RUN.")

    def hard_quit(self, event=None):
        self.running = False
        self.end_after_current = False
        self.apply_idle_visuals()
        try:
            if keyboard is not None:
                keyboard.clear_all_hotkeys()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def _macro_worker(self):
        # big wait at start
        wait_time = int(self.big_wait_var.get())
        for i in range(wait_time, 0, -1):
            if not self.running:
                self.status_lbl.config(text="CANCELLED BEFORE START.")
                self.apply_idle_visuals()
                return
            self.status_lbl.config(text=f"STARTING IN: {i} SECONDS. OPEN CHROME AND GET READY.")
            time.sleep(1)

        self.status_lbl.config(text="RUNNING MACRO...")
        discord_timer = time.time()
        cooldown_enabled = self.cooldown_enabled_var.get()
        is_profile1 = (self.profile_name == "Profile 1")

        while self.running:
            # 1) Chaos roll (profile 1 only)
            if is_profile1:
                self.last_image, url = self.do_chaos_cycle()

            # 2) Macro
            try:
                self.run_macro_once()
            except Exception as e:
                self.status_lbl.config(text=f"MACRO ERROR: {e}")
                break

            # 3) roll count
            self.roll_count += 1
            self.rolls_lbl.config(text=f"ROLLS: {self.roll_count}")

            # 4) end-after-current
            if self.end_after_current:
                self.status_lbl.config(text="END-AFTER-CURRENT TRIGGERED. STOPPING.")
                break

            # 5) webhook ping every 10 min
            if self.cfg.get("discord_webhook") and time.time() - discord_timer >= 600:
                send_discord_webhook(
                    self.cfg["discord_webhook"],
                    f"Doomware ({self.profile_name}) is still running.",
                )
                discord_timer = time.time()

            # 6) cooldown between loops
            if cooldown_enabled:
                cd = int(self.cooldown_var.get())
                for i in range(cd, 0, -1):
                    if not self.running:
                        self.status_lbl.config(text="MACRO STOPPED.")
                        self.apply_idle_visuals()
                        return
                    self.status_lbl.config(text=f"NEXT RUN IN: {i} SECONDS.")
                    time.sleep(1)

        self.running = False
        self.apply_idle_visuals()
        self.status_lbl.config(text="MACRO STOPPED.")

    # ------------ key handler ------------
    def on_escape(self, event=None):
        self.hard_quit()


def main():
    ensure_admin()
    profile_name = choose_profile()
    app = DoomwareHUD(profile_name)
    app.mainloop()


if __name__ == "__main__":
    main()
