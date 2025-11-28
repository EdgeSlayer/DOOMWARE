import os
import sys
import json
import time
import random
import string
import math
import threading
import ctypes

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
except ImportError:
    print("Missing modules. Run:")
    print("   pip install pyautogui pyperclip requests pygetwindow keyboard")
    input("Press ENTER to exit...")
    raise SystemExit

pyautogui.FAILSAFE = True

try:
    import keyboard
except ImportError:
    keyboard = None

# --------------------- Admin + DPI (Win10/11) ---------------------
def ensure_admin():
    if os.name != "nt":
        return
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        params = " ".join(f'"{arg}"' for arg in sys.argv)
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
        except Exception as e:
            print("Failed to elevate:", e)
        raise SystemExit


def setup_windows_compat():
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# --------------------- Paths / Config ---------------------
APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
BASE_FOLDER = os.path.join(APPDATA, "Doomware")
os.makedirs(BASE_FOLDER, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(BASE_DIR, "doomware.ico")

# will be set per profile later
CFG_PATH = os.path.join(BASE_FOLDER, "doomware_profile_1.json")

DEFAULT_CFG = {
    "cooldown": 10,
    "cooldown_enabled": True,
    "discord_webhook": "",
    "speed_preset": "fast",       # slow / normal / fast / extreme / chaos
    "theme": "InfernalRed",       # theme key
    "topmost": True,
    "alpha_idle": 0.96,
    "alpha_running": 0.75,
    "clickthrough_running": True,
}

# --------------------- Chaos Roller (Profile 1) ---------------------
IMAGE_NAMES = [f"{i}.jpg" for i in range(1, 103)]
BASE_URL = "https://github.com/EdgeSlayer/my-images/blob/main/{image}?raw=true"


def generate_chaos_string(length=32):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def pick_new_image(last_image=None):
    choices = [img for img in IMAGE_NAMES if img != last_image]
    return random.choice(choices) if choices else random.choice(IMAGE_NAMES)


def perform_chaos_roll_github(last_image):
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


# --------------------- Themes ---------------------
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
    "Ghost": {
        "root_bg": "#060606",
        "panel_bg": "#101010",
        "top_bg": "#181818",
        "text": "#f0f0f0",
        "muted_text": "#a0a0a0",
        "accent": "#ffffff",
        "accent_soft": "#dddddd",
        "accent_ok": "#88ffcc",
        "accent_stop": "#ff7777",
        "entry_bg": "#181818",
        "button_bg": "#202020",
        "button_active_bg": "#303030",
        "button_fg": "#f8f8f8",
    },
}

SPEED_MULTIPLIERS = {
    "slow": 0.6,
    "normal": 1.0,
    "fast": 1.6,
    "extreme": 2.3,
    "chaos": 3.2,
}

# --------------------- ASCII ---------------------
ASCII_TITLE = """\
██████╗  ██████╗  ██████╗ ███╗   ███╗██╗    ██╗ █████╗ ██████╗ ███████╗
██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║██║    ██║██╔══██╗██╔══██╗██╔════╝
██║  ██║██║   ██║██║   ██║██╔████╔██║██║ █╗ ██║███████║██████╔╝█████╗  
██║  ██║██║   ██║██║   ██║██╔██╔██║██║███╗██║██╔══██║██╔══██╗██╔══╝   
██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║╚███╔███╔╝██║  ██║██║  ██║███████╗
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
"""


# --------------------- Profile chooser ---------------------
def choose_profile():
    root = tk.Tk()
    root.title("Select Doomware Profile")
    root.resizable(False, False)

    w, h = 260, 160
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 3
    root.geometry(f"{w}x{h}+{x}+{y}")

    var = tk.StringVar(value="Profile 1")

    font_lbl = tkFont.Font(family="Consolas", size=10, weight="bold")
    font_opt = tkFont.Font(family="Consolas", size=9)

    tk.Label(root, text="Choose profile to load:", font=font_lbl).pack(pady=(12, 6))

    for name in ["Profile 1", "Profile 2"]:
        tk.Radiobutton(
            root, text=name, value=name, variable=var,
            font=font_opt, anchor="w", justify="left"
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


# --------------------- GUI APP ---------------------
class DoomwareHUD(tk.Tk):
    def __init__(self, profile_name):
        super().__init__()

        self.profile_name = profile_name.strip()

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
            self.cfg.get("speed_preset", "fast"),
            SPEED_MULTIPLIERS["fast"],
        )
        self._global_hotkeys_started = False

        self._clickthrough_enabled = False
        self._hwnd = None
        if os.name == "nt":
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

        self.bind_all("<Escape>", self.on_escape)

        self.start_global_hotkeys()

    # ---------- config ----------
    def load_or_default_cfg(self):
        if not os.path.exists(CFG_PATH):
            return DEFAULT_CFG.copy()
        try:
            with open(CFG_PATH, "r") as f:
                data = json.load(f)
            for k, v in DEFAULT_CFG.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return DEFAULT_CFG.copy()

    def save_cfg(self):
        try:
            with open(CFG_PATH, "w") as f:
                json.dump(self.cfg, f, indent=4)
        except Exception:
            pass

    # ---------- UI ----------
    def center_window(self):
        self.update_idletasks()
        w = 920
        h = 480
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

        self.ascii_lbl = tk.Label(
            self.main,
            text=ASCII_TITLE,
            font=font_title,
            bg="#050509",
            fg="#ff3333",
            justify="left"
        )
        self.ascii_lbl.pack(anchor="w", pady=(4, 6))

        key_frame = tk.Frame(self.main, bg="#050509")
        key_frame.pack(anchor="w", fill="x", pady=(0, 4))

        self.keyhint_lbl = tk.Label(
            key_frame,
            text="[ESC] HARD QUIT  |  F6 TOPMOST  |  F7 CLICK-THROUGH  |  F8 END AFTER CURRENT  |  F9 START  |  F10 STOP",
            font=font_text, fg="#777777", bg="#050509",
            anchor="w", justify="left"
        )
        self.keyhint_lbl.pack(side="left", padx=(0, 8))

        self.profile_lbl = tk.Label(
            key_frame,
            text=f"PROFILE: {self.profile_name}",
            font=font_text, fg="#aaaaaa", bg="#050509",
            anchor="e", justify="right"
        )
        self.profile_lbl.pack(side="right")

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

        tk.Label(cfg_frame, text="COOLDOWN (S):", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=0, column=0, sticky="w")

        self.cooldown_enabled_var = tk.BooleanVar(value=self.cfg.get("cooldown_enabled", True))
        tk.Checkbutton(
            cfg_frame, text="Enable", variable=self.cooldown_enabled_var,
            font=font_text, fg="#cccccc", bg="#050509",
            selectcolor="#111111", activebackground="#050509",
            activeforeground="#ffffff"
        ).grid(row=0, column=1, sticky="w", padx=(4, 4))

        self.cooldown_var = tk.StringVar(value=str(self.cfg.get("cooldown", 10)))
        tk.Entry(
            cfg_frame, textvariable=self.cooldown_var, width=6,
            font=font_text, bg="#111111", fg="#ffffff", insertbackground="#ffffff"
        ).grid(row=0, column=2, padx=(4, 12))

        tk.Label(cfg_frame, text="SPEED:", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=0, column=3, sticky="w")

        self.speed_var = tk.StringVar(value=self.cfg.get("speed_preset", "fast"))
        self.speed_combo = ttk.Combobox(
            cfg_frame, textvariable=self.speed_var,
            values=list(SPEED_MULTIPLIERS.keys()),
            width=10, state="readonly"
        )
        self.speed_combo.grid(row=0, column=4, padx=(4, 12))

        tk.Label(cfg_frame, text="THEME:", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.theme_var = tk.StringVar(value=self.cfg.get("theme", "InfernalRed"))
        self.theme_combo = ttk.Combobox(
            cfg_frame, textvariable=self.theme_var,
            values=list(THEMES.keys()),
            width=14, state="readonly"
        )
        self.theme_combo.grid(row=1, column=1, padx=(4, 12), pady=(4, 0), sticky="w")

        self.topmost_var = tk.BooleanVar(value=self.cfg.get("topmost", True))
        tk.Checkbutton(
            cfg_frame, text="TOPMOST", variable=self.topmost_var,
            font=font_text, fg="#cccccc", bg="#050509",
            selectcolor="#111111", activebackground="#050509",
            activeforeground="#ffffff"
        ).grid(row=1, column=2, sticky="w", padx=(4, 8))

        self.clickthrough_run_var = tk.BooleanVar(
            value=self.cfg.get("clickthrough_running", True)
        )
        tk.Checkbutton(
            cfg_frame, text="Click-through while running", variable=self.clickthrough_run_var,
            font=font_text, fg="#cccccc", bg="#050509",
            selectcolor="#111111", activebackground="#050509",
            activeforeground="#ffffff"
        ).grid(row=1, column=3, columnspan=2, sticky="w", padx=(4, 8))

        tk.Label(cfg_frame, text="DISCORD WEBHOOK:", font=font_text,
                 fg="#cccccc", bg="#050509").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.webhook_var = tk.StringVar(value=self.cfg.get("discord_webhook", ""))
        tk.Entry(
            cfg_frame, textvariable=self.webhook_var, width=60,
            font=font_text, bg="#111111", fg="#ffffff", insertbackground="#ffffff"
        ).grid(row=2, column=1, columnspan=3, padx=(4, 0), pady=(4, 0), sticky="w")

        save_btn = tk.Button(
            cfg_frame, text="SAVE CONFIG",
            command=self.on_save_cfg,
            font=font_btn, bg="#222222", fg="#ffffff",
            activebackground="#444444", activeforeground="#ffffff",
            relief="flat"
        )
        save_btn.grid(row=0, column=5, rowspan=3, padx=(12, 0))

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
            ctrl, text="END AFTER CURRENT ROLL",
            command=self.request_end_after_current,
            font=font_btn, bg="#444444", fg="#ffffff",
            activebackground="#666666", activeforeground="#ffffff",
            relief="flat", width=22
        )
        self.end_after_btn.pack(side="left", padx=(8, 0))

        hint = tk.Label(
            self.main,
            text="Profile 1: CHAOS + macro   |   Profile 2: macro only   |   Loop: (optional cooldown between runs).",
            font=font_text, fg="#777777", bg="#050509",
            anchor="w", justify="left", wraplength=880
        )
        hint.pack(anchor="w", pady=(12, 12))

        self.status_lbl.config(text="READY. SET SETTINGS AND PRESS START.")

    # ---------- drag ----------
    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    # ---------- utils ----------
    def call_on_ui(self, func, *args, **kwargs):
        self.after(0, lambda: func(*args, **kwargs))

    # ---------- global hotkeys ----------
    def start_global_hotkeys(self):
        if getattr(self, "_global_hotkeys_started", False):
            return
        self._global_hotkeys_started = True

        if keyboard is None:
            print("Global hotkeys disabled: install 'keyboard' with: pip install keyboard")
            return

        def worker():
            try:
                keyboard.add_hotkey("f6", lambda: self.call_on_ui(self.kb_toggle_topmost))
                keyboard.add_hotkey("f7", lambda: self.call_on_ui(self.kb_toggle_clickthrough))
                keyboard.add_hotkey("f8", lambda: self.call_on_ui(self.kb_end_after_current))
                keyboard.add_hotkey("f9", lambda: self.call_on_ui(self.start_macro))
                keyboard.add_hotkey("f10", lambda: self.call_on_ui(self.stop_macro))
            except Exception as e:
                print("Error setting global hotkeys:", e)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- config handlers ----------
    def on_save_cfg(self):
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

    # ---------- uptime ----------
    def update_uptime(self):
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        self.uptime_lbl.config(text=f"UPTIME: {m:02d}:{s:02d}")
        self.after(1000, self.update_uptime)

    # ---------- theme / visuals ----------
    def apply_theme(self, key):
        if key not in THEMES:
            key = "InfernalRed"
        t = THEMES[key]

        self.config(bg=t["root_bg"])
        self.main.config(bg=t["panel_bg"])
        self.top.config(bg=t["top_bg"])

        self.title_lbl.config(bg=t["top_bg"], fg=t["accent"])
        self.ascii_lbl.config(bg=t["panel_bg"], fg=t["accent"])
        self.keyhint_lbl.config(bg=t["panel_bg"], fg=t["muted_text"])
        self.profile_lbl.config(bg=t["panel_bg"], fg=t["text"])
        self.status_lbl.config(bg=t["panel_bg"], fg=t["text"])
        self.chaos_lbl.config(bg=t["panel_bg"], fg=t["accent_soft"])
        self.url_lbl.config(bg=t["panel_bg"], fg=t["muted_text"])
        self.rolls_lbl.config(bg=t["panel_bg"], fg=t["text"])
        self.uptime_lbl.config(bg=t["panel_bg"], fg=t["text"])

        for w in self.main.winfo_children():
            if isinstance(w, tk.Frame) and w not in (self.main, self.top):
                w.config(bg=t["panel_bg"])

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
            bordercolor=t["accent"],
            lightcolor=t["panel_bg"],
            darkcolor=t["panel_bg"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["entry_bg"])],
            background=[("readonly", t["entry_bg"])],
            foreground=[("readonly", t["text"])],
        )
        self.speed_combo.configure(style="TCombobox")
        self.theme_combo.configure(style="TCombobox")

    def apply_idle_visuals(self):
        try:
            alpha = float(self.cfg.get("alpha_idle", 0.96))
            self.attributes("-alpha", alpha)
        except Exception:
            pass
        try:
            self.attributes("-topmost", bool(self.cfg.get("topmost", True)))
        except Exception:
            pass
        self.disable_clickthrough()

    def apply_running_visuals(self):
        try:
            alpha = float(self.cfg.get("alpha_running", 0.75))
            self.attributes("-alpha", alpha)
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

    # ---------- click-through (Windows only) ----------
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
        GWL_EXSTYLE = self.GWL_EXSTYLE
        WS_EX_LAYERED = self.WS_EX_LAYERED
        WS_EX_TRANSPARENT = self.WS_EX_TRANSPARENT
        user32 = self.ctypes.windll.user32

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= (WS_EX_LAYERED | WS_EX_TRANSPARENT)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self._clickthrough_enabled = True

    def disable_clickthrough(self):
        if self.ctypes is None:
            return
        if not self._clickthrough_enabled:
            return
        hwnd = self._get_hwnd()
        if not hwnd:
            return
        GWL_EXSTYLE = self.GWL_EXSTYLE
        WS_EX_TRANSPARENT = self.WS_EX_TRANSPARENT
        user32 = self.ctypes.windll.user32

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self._clickthrough_enabled = False

    # ---------- automation helpers ----------
    def sleep_scaled(self, base_min, base_max):
        dur = random.uniform(base_min, base_max)
        dur = dur * 0.25 / max(self.speed_factor, 0.1)
        time.sleep(max(dur, 0.0003))

    def random_offset(self, px=2):
        return random.randint(-px, px)

    def move_correct_if_moved(self, x, y, threshold=5):
        cur_x, cur_y = pyautogui.position()
        if abs(cur_x - x) > threshold or abs(cur_y - y) > threshold:
            pyautogui.moveTo(x, y)

    def human_flick(self, x, y):
        sx, sy = pyautogui.position()
        dx = x - sx
        dy = y - sy
        distance = math.hypot(dx, dy)
        base_steps = max(8, int(distance / 25))
        steps = max(5, int(base_steps / max(self.speed_factor, 0.6)))
        curve_strength = distance * 0.08
        cx = (sx + x) / 2 + random.uniform(-curve_strength, curve_strength)
        cy = (sy + y) / 2 + random.uniform(-curve_strength, curve_strength)
        for i in range(steps):
            t = i / steps
            nx = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t ** 2 * x
            ny = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t ** 2 * y
            nx += random.uniform(-0.4, 0.4)
            ny += random.uniform(-0.4, 0.4)
            pyautogui.moveTo(nx, ny)
            time.sleep(0.00025 / max(self.speed_factor, 0.4))
        pyautogui.moveTo(x, y)

    def move_and_click(self, x, y):
        self.human_flick(x, y)
        self.move_correct_if_moved(x, y)
        pyautogui.click()

    def wait_for_chrome(self, window_title_contains="Chrome"):
        while True:
            wins = gw.getWindowsWithTitle(window_title_contains)
            if wins:
                return wins[0]
            time.sleep(0.5)

    def run_macro_once(self):
        """Shared macro for both profiles. Profile 1 adds chaos before this."""
        # 1) send ctrl+alt+g
        pyautogui.hotkey("ctrl", "alt", "g")

        # 2) bring Chrome to front and maximize
        chrome_win = self.wait_for_chrome("Chrome")
        if chrome_win.isMinimized:
            chrome_win.restore()
            time.sleep(0.6)
        try:
            chrome_win.activate()
        except Exception:
            pass
        time.sleep(0.3)

        # 3) main click sequence
        # first up, 1255,101
        self.move_and_click(1255 + self.random_offset(), 101 + self.random_offset())
        self.sleep_scaled(0.4, 0.9)

        # then 870,716
        self.move_and_click(870 + self.random_offset(), 716 + self.random_offset())
        self.sleep_scaled(0.4, 0.9)

        # then 1400,966
        self.move_and_click(1400 + self.random_offset(), 966 + self.random_offset())
        self.sleep_scaled(0.4, 0.9)

        # then 695,730
        self.move_and_click(695 + self.random_offset(), 730 + self.random_offset())

        # wait about 15 seconds (real time, not speed-scaled)
        time.sleep(15.0)

        # random final click
        last_choices = [(746, 991), (746, 991), (963, 1031)]
        lx, ly = random.choice(last_choices)
        self.move_and_click(lx + self.random_offset(), ly + self.random_offset())
        self.sleep_scaled(0.4, 0.9)

    # ---------- chaos + ascii animation (Profile 1 only) ----------
    def do_chaos_cycle(self):
        img, url = perform_chaos_roll_github(self.last_image)

        base_text = ASCII_TITLE
        glitch_chars = "#$%@&X*"

        try:
            for _ in range(3):
                glitched_lines = []
                for line in base_text.splitlines():
                    new_line = "".join(
                        random.choice(glitch_chars)
                        if (c != " " and random.random() < 0.18)
                        else c
                        for c in line
                    )
                    glitched_lines.append(new_line)
                self.ascii_lbl.config(text="\n".join(glitched_lines), fg="#ff6666")
                self.update_idletasks()
                time.sleep(0.06)
            t = THEMES.get(self.cfg.get("theme", "InfernalRed"), THEMES["InfernalRed"])
            self.ascii_lbl.config(text=ASCII_TITLE, fg=t["accent"])
        except Exception:
            self.ascii_lbl.config(text=ASCII_TITLE)

        self.chaos_lbl.config(text="CHAOS STRING COPIED.")
        self.url_lbl.config(text=f"URL: {url}")
        self.last_image = img
        return img, url

    # ---------- macro control ----------
    def start_macro(self):
        if self.running:
            return
        self.on_save_cfg()
        self.running = True
        self.end_after_current = False
        self.roll_count = 0
        self.status_lbl.config(text="STARTING IN 15 SECONDS... OPEN CHROME AND GET READY.")
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
        self.status_lbl.config(text="WILL STOP AFTER CURRENT ROLL FINISHES.")

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
        for i in range(15, 0, -1):
            if not self.running:
                self.status_lbl.config(text="CANCELLED BEFORE START.")
                self.apply_idle_visuals()
                return
            self.status_lbl.config(text=f"STARTING IN: {i} SECONDS. OPEN CHROME AND GET READY.")
            time.sleep(1)

        self.status_lbl.config(text="RUNNING MACRO...")
        discord_timer = time.time()

        while self.running:
            # Profile 1: chaos + macro, Profile 2: macro only
            if self.profile_name.lower() == "profile 1":
                try:
                    self.last_image, url = self.do_chaos_cycle()
                except Exception as e:
                    self.status_lbl.config(text=f"CHAOS ERROR: {e}")
                    break

            try:
                self.run_macro_once()
            except Exception as e:
                self.status_lbl.config(text=f"MACRO ERROR: {e}")
                break

            self.roll_count += 1
            self.rolls_lbl.config(text=f"ROLLS: {self.roll_count}")

            if self.end_after_current:
                self.status_lbl.config(text="END-AFTER-CURRENT ROLL TRIGGERED. STOPPING.")
                break

            if self.cfg.get("discord_webhook") and time.time() - discord_timer >= 600:
                send_discord_webhook(
                    self.cfg["discord_webhook"],
                    "Doomware automation is still running.",
                )
                discord_timer = time.time()

            cd_enabled = bool(self.cfg.get("cooldown_enabled", True))
            cd = int(self.cfg.get("cooldown", 10))
            if cd_enabled and cd > 0:
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

    # ---------- key handlers ----------
    def on_escape(self, event=None):
        self.hard_quit()

    def kb_toggle_topmost(self, event=None):
        new_state = not self.topmost_var.get()
        self.topmost_var.set(new_state)
        try:
            self.attributes("-topmost", new_state)
        except Exception:
            pass
        self.cfg["topmost"] = new_state
        self.status_lbl.config(text=f"TOPMOST: {'ON' if new_state else 'OFF'} (F6)")

    def kb_toggle_clickthrough(self, event=None):
        new_state = not self.clickthrough_run_var.get()
        self.clickthrough_run_var.set(new_state)
        self.cfg["clickthrough_running"] = new_state

        if self.running and new_state:
            self.enable_clickthrough()
        else:
            self.disable_clickthrough()

        self.status_lbl.config(
            text=f"CLICK-THROUGH WHILE RUNNING: {'ON' if new_state else 'OFF'} (F7)"
        )

    def kb_end_after_current(self, event=None):
        if not self.running:
            self.status_lbl.config(text="F8: NO MACRO RUNNING.")
            return
        self.end_after_current = True
        self.status_lbl.config(text="END AFTER CURRENT ROLL (F8).")


# --------------------- main ---------------------
def main(profile_name):
    app = DoomwareHUD(profile_name)
    app.mainloop()


if __name__ == "__main__":
    ensure_admin()
    setup_windows_compat()
    profile_name = choose_profile()

    # set CFG_PATH per profile
    slug = profile_name.lower().replace(" ", "_")
    CFG_PATH = os.path.join(BASE_FOLDER, f"doomware_{slug}.json")

    main(profile_name)
