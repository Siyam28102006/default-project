"""
Midnight Pomodoro - premium dark desktop timer (CustomTkinter).
Run:  pip install -r requirements.txt
      python pomodoro.py
Shortcuts: Space = start/pause, R = reset, S = skip, 1/2/3 = modes
"""

import json
import os
import customtkinter as ctk

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(APP_DIR, "pomodoro_data.json")


def _find_icon():
    candidates = [os.path.join(APP_DIR, "pomodoro.ico")]
    try:
        import sys
        base = getattr(sys, "_MEIPASS", None)
        if base:
            candidates.insert(0, os.path.join(base, "pomodoro.ico"))
    except Exception:
        pass
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


ICON_FILE = _find_icon()

# ---------- OLED midnight palette ----------
BG = "#07070b"          # app background (near-black)
CARD = "#121218"        # card surface
CARD2 = "#1a1a22"       # raised surface
BORDER = "#26262f"      # subtle border
TEXT = "#f2f2f5"
MUTED = "#8b8b98"
ACCENT = "#ff5c39"      # pomodoro ember
ACCENT_HOVER = "#e04a2b"
FOCUS = "#ff5c39"
SHORT = "#2dd4bf"
LONG = "#a78bfa"

DEFAULTS = {
    "focus_min": 25,
    "short_min": 5,
    "long_min": 15,
    "sessions_before_long": 4,
    "auto_start_breaks": True,
    "sound_on": True,
    "always_on_top": False,
    "tasks": [],
    "completed_total": 0,
}

MODE_COLOR = {"Focus": FOCUS, "Short Break": SHORT, "Long Break": LONG}
MODE_EMOJI = {"Focus": "Focus", "Short Break": "Recharge", "Long Break": "Rest"}


def play_chime(mode="Focus"):
    """Richer finish chime. Winsound on Windows, Tk bell fallback."""
    try:
        import winsound
        if mode == "Focus":
            for freq, ms in ((784, 220), (784, 220), (1046, 420)):
                winsound.Beep(freq, ms)
        else:
            for freq, ms in ((660, 220), (880, 380)):
                winsound.Beep(freq, ms)
    except Exception:
        try:
            root = ctk._default_root
            if root is not None:
                for _ in range(3):
                    root.bell()
                    root.update()
        except Exception:
            print("\a")


class RingTimer(ctk.CTkFrame):
    """Circular progress ring with big time text in the middle."""

    def __init__(self, master, size=230, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.canvas = ctk.CTkCanvas(
            self, width=size, height=size, bg=CARD,
            highlightthickness=0, bd=0)
        self.canvas.pack()
        # centered time label over the canvas
        self.time_var = ctk.StringVar(value="25:00")
        self.time_label = ctk.CTkLabel(
            self, textvariable=self.time_var,
            font=("Segoe UI", 52, "bold"), text_color=TEXT,
            fg_color=CARD)
        self.time_label.place(relx=0.5, rely=0.46, anchor="center")
        self.sub_label = ctk.CTkLabel(
            self, text="FOCUS", font=("Segoe UI", 12, "bold"),
            text_color=MUTED, fg_color=CARD)
        self.sub_label.place(relx=0.5, rely=0.66, anchor="center")
        self.frac = 0.0
        self.color = FOCUS
        self.draw()

    def set(self, frac, timestr, modelabel, color):
        self.frac = max(0.0, min(1.0, frac))
        self.color = color
        self.time_var.set(timestr)
        self.sub_label.configure(text=modelabel.upper(), text_color=color)
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        s = self.size
        pad, w = 14, 10
        # track
        c.create_oval(pad, pad, s - pad, s - pad, outline="#23232c", width=w)
        # progress arc (starts at top, goes clockwise)
        if self.frac > 0.001:
            c.create_arc(pad, pad, s - pad, s - pad, start=90,
                         extent=-360 * self.frac, outline=self.color,
                         width=w, style="arc", capstyle="round")
        # glowing tip dot
        import math
        if self.frac > 0.001:
            ang = math.radians(90 + 360 * self.frac)
            r = (s - 2 * pad) / 2
            cx = cy = s / 2
            x = cx - r * math.cos(ang)
            y = cy - r * math.sin(ang)
            c.create_oval(x - 5, y - 5, x + 5, y + 5,
                          fill=self.color, outline=self.color)


class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.data = self.load_data()
        ctk.set_appearance_mode("dark")

        self.configure(fg_color=BG)
        self.title("Midnight Pomodoro")
        self.geometry("440x960")
        self.resizable(False, False)
        try:
            if ICON_FILE:
                self.iconbitmap(ICON_FILE)
        except Exception:
            pass
        self.attributes("-topmost", bool(self.data.get("always_on_top")))

        self.mode = "Focus"
        self.running = False
        self.remaining = self.data["focus_min"] * 60
        self.completed_in_cycle = 0
        self._job = None
        self._flash = None

        self.build_ui()
        self.set_mode("Focus", reset=True)
        self.render_tasks()
        self.bind_shortcuts()

    # ---------- persistence ----------
    def load_data(self):
        data = dict(DEFAULTS)
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                data.update(saved)
            except Exception:
                pass
        return data

    def save_data(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    # ---------- UI ----------
    def card(self, **kw):
        return ctk.CTkFrame(self, fg_color=CARD, corner_radius=16,
                            border_width=1, border_color=BORDER, **kw)

    def build_ui(self):
        # header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 2))
        ctk.CTkLabel(header, text="●  MIDNIGHT POMODORO",
                     font=("Segoe UI", 13, "bold"),
                     text_color=ACCENT).pack(side="left")
        self.streak_label = ctk.CTkLabel(
            header, text="", font=("Segoe UI", 12), text_color=MUTED)
        self.streak_label.pack(side="right")

        # timer card
        timer_card = self.card()
        timer_card.pack(padx=20, pady=10, fill="x")
        self.ring = RingTimer(timer_card)
        self.ring.pack(pady=(16, 4))

        # mode pills
        pills = ctk.CTkFrame(timer_card, fg_color="transparent")
        pills.pack(pady=(6, 4))
        self.pill_btns = {}
        for m in ("Focus", "Short Break", "Long Break"):
            b = ctk.CTkButton(pills, text=m, width=110, height=30,
                              corner_radius=20, font=("Segoe UI", 12, "bold"),
                              fg_color=CARD2, text_color=MUTED,
                              hover_color="#23232e",
                              command=lambda mm=m: self.set_mode(mm, reset=True))
            b.pack(side="left", padx=4)
            self.pill_btns[m] = b

        self.status_label = ctk.CTkLabel(
            timer_card, text="", font=("Segoe UI", 12), text_color=MUTED)
        self.status_label.pack(pady=(2, 12))

        # controls
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=2)
        self.start_btn = ctk.CTkButton(
            controls, text="▶  Start", height=46, corner_radius=14,
            font=("Segoe UI", 15, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
            command=self.toggle)
        self.start_btn.pack(fill="x")
        row = ctk.CTkFrame(controls, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        for txt, cmd in (("↺  Reset", self.reset), ("Skip  ⏭", self.skip)):
            ctk.CTkButton(row, text=txt, height=36, corner_radius=12,
                          font=("Segoe UI", 12, "bold"),
                          fg_color=CARD2, text_color=TEXT,
                          border_width=1, border_color=BORDER,
                          hover_color="#23232e",
                          command=cmd).pack(side="left", fill="x", expand=True,
                                            padx=(0, 4) if txt.startswith("↺") else (4, 0))

        # stats
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=(10, 0))
        self.stat_cycle = self._stat_box(stats, "CYCLE")
        self.stat_cycle.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stat_total = self._stat_box(stats, "COMPLETED")
        self.stat_total.pack(side="left", fill="x", expand=True, padx=(4, 4))
        self.stat_tasks = self._stat_box(stats, "TASKS DONE")
        self.stat_tasks.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # settings card
        settings = self.card()
        settings.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(settings, text="CUSTOMIZE TIMERS",
                     font=("Segoe UI", 11, "bold"),
                     text_color=MUTED).pack(pady=(12, 2))

        self.focus_entry = self._stepper_row(settings, "Focus length", self.data["focus_min"], 1, 180, "min")
        self.short_entry = self._stepper_row(settings, "Short break", self.data["short_min"], 1, 60, "min")
        self.long_entry = self._stepper_row(settings, "Long break", self.data["long_min"], 1, 90, "min")
        self.cycle_entry = self._stepper_row(settings, "Long break every", self.data["sessions_before_long"], 2, 12, "sessions", step=1)

        presets = ctk.CTkFrame(settings, fg_color="transparent")
        presets.pack(pady=(8, 2))
        for name, vals in (("Classic 25/5", (25, 5, 15, 4)),
                           ("Quick 15/3", (15, 3, 10, 4)),
                           ("Deep 50/10", (50, 10, 30, 4))):
            ctk.CTkButton(presets, text=name, width=110, height=28,
                          corner_radius=14, font=("Segoe UI", 11, "bold"),
                          fg_color=CARD2, text_color=TEXT,
                          border_width=1, border_color=BORDER,
                          hover_color="#23232e",
                          command=lambda v=vals: self.apply_preset(v)).pack(
                              side="left", padx=4)

        ctk.CTkLabel(settings, text="Changes apply instantly when paused.",
                     font=("Segoe UI", 11), text_color="#55555f").pack(pady=(2, 4))

        toggles = ctk.CTkFrame(settings, fg_color="transparent")
        toggles.pack(pady=(6, 12))
        self.auto_var = ctk.BooleanVar(value=self.data["auto_start_breaks"])
        self.sound_var = ctk.BooleanVar(value=self.data["sound_on"])
        self.top_var = ctk.BooleanVar(value=self.data.get("always_on_top", False))
        for txt, var in (("Auto-start", self.auto_var),
                         ("Sound", self.sound_var),
                         ("On top", self.top_var)):
            ctk.CTkCheckBox(toggles, text=txt, variable=var,
                            font=("Segoe UI", 12), text_color=TEXT,
                            fg_color=ACCENT, hover_color=ACCENT_HOVER,
                            border_color=BORDER,
                            command=self.save_settings_from_ui).pack(
                                side="left", padx=10)

        # tasks card
        tasks = self.card()
        tasks.pack(padx=20, pady=(0, 8), fill="both", expand=True)
        top = ctk.CTkFrame(tasks, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 2))
        ctk.CTkLabel(top, text="TASKS", font=("Segoe UI", 11, "bold"),
                     text_color=MUTED).pack(side="left")
        ctk.CTkButton(top, text="Clear done", width=90, height=26,
                      corner_radius=8, font=("Segoe UI", 11),
                      fg_color="transparent", text_color=MUTED,
                      hover_color=CARD2,
                      command=self.clear_done).pack(side="right")

        add_row = ctk.CTkFrame(tasks, fg_color="transparent")
        add_row.pack(fill="x", padx=12, pady=4)
        self.task_entry = ctk.CTkEntry(
            add_row, placeholder_text="Add a task, press Enter…",
            height=36, corner_radius=10, font=("Segoe UI", 13),
            fg_color=CARD2, border_color=BORDER, text_color=TEXT,
            placeholder_text_color=MUTED)
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.task_entry.bind("<Return>", lambda _e: self.add_task())
        ctk.CTkButton(add_row, text="+", width=44, height=36,
                      corner_radius=10, font=("Segoe UI", 18, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.add_task).pack(side="right")

        self.task_list = ctk.CTkScrollableFrame(
            tasks, height=110, fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=MUTED)
        self.task_list.pack(fill="both", expand=True, padx=8, pady=(2, 8))

        ctk.CTkLabel(self, text="Space start/pause  •  R reset  •  S skip  •  1/2/3 modes",
                     font=("Segoe UI", 11), text_color="#55555f").pack(pady=(0, 12))

    def _stat_box(self, parent, title):
        box = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color=BORDER)
        v = ctk.CTkLabel(box, text="0", font=("Segoe UI", 20, "bold"),
                         text_color=TEXT)
        v.pack(pady=(10, 0))
        ctk.CTkLabel(box, text=title, font=("Segoe UI", 10, "bold"),
                     text_color=MUTED).pack(pady=(0, 10))
        box.value_label = v  # type: ignore
        return box

    def _stepper_row(self, parent, label, value, lo, hi, unit, step=5):
        """A labeled - [value] + stepper. Typing works too; saves live."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(row, text=label, font=("Segoe UI", 13),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(row, text=unit, font=("Segoe UI", 11),
                     text_color=MUTED).pack(side="right", padx=(6, 0))

        def bump(delta):
            try:
                cur = int(entry.get())
            except Exception:
                cur = value
            entry.delete(0, "end")
            entry.insert(0, str(max(lo, min(hi, cur + delta))))
            self.save_settings_from_ui()

        plus = ctk.CTkButton(row, text="+", width=34, height=30,
                             corner_radius=9, font=("Segoe UI", 15, "bold"),
                             fg_color=CARD2, text_color=TEXT,
                             border_width=1, border_color=BORDER,
                             hover_color="#23232e",
                             command=lambda: bump(step))
        plus.pack(side="right", padx=(4, 0))

        entry = ctk.CTkEntry(row, width=58, height=30, corner_radius=9,
                             justify="center", font=("Segoe UI", 14, "bold"),
                             fg_color=CARD2, border_color=BORDER, text_color=TEXT)
        entry.insert(0, str(value))
        entry.pack(side="right")
        entry.bind("<Return>", lambda _e: self.save_settings_from_ui())
        entry.bind("<FocusOut>", lambda _e: self.save_settings_from_ui())

        minus = ctk.CTkButton(row, text="−", width=34, height=30,
                              corner_radius=9, font=("Segoe UI", 15, "bold"),
                              fg_color=CARD2, text_color=TEXT,
                              border_width=1, border_color=BORDER,
                              hover_color="#23232e",
                              command=lambda: bump(-step))
        minus.pack(side="right", padx=(0, 4))
        return entry

    def apply_preset(self, vals):
        f, s, l, c = vals
        for entry, v in ((self.focus_entry, f), (self.short_entry, s),
                         (self.long_entry, l), (self.cycle_entry, c)):
            entry.delete(0, "end")
            entry.insert(0, str(v))
        self.save_settings_from_ui()

    def bind_shortcuts(self):
        self.bind("<space>", lambda _e: self.toggle())
        self.bind("r", lambda _e: self.reset())
        self.bind("R", lambda _e: self.reset())
        self.bind("s", lambda _e: self.skip())
        self.bind("S", lambda _e: self.skip())
        self.bind("1", lambda _e: self.set_mode("Focus", reset=True))
        self.bind("2", lambda _e: self.set_mode("Short Break", reset=True))
        self.bind("3", lambda _e: self.set_mode("Long Break", reset=True))

    # ---------- timer logic ----------
    def minutes_for(self, mode):
        return {"Focus": self.data["focus_min"],
                "Short Break": self.data["short_min"],
                "Long Break": self.data["long_min"]}[mode]

    def set_mode(self, mode, reset=True):
        self.mode = mode
        if reset:
            self.stop_tick()
            self.running = False
            self.start_btn.configure(text="▶  Start", fg_color=MODE_COLOR[mode],
                                     hover_color=MODE_COLOR[mode])
            self.remaining = self.minutes_for(mode) * 60
        # highlight active pill
        for m, b in self.pill_btns.items():
            if m == mode:
                b.configure(fg_color=MODE_COLOR[m], text_color="white")
            else:
                b.configure(fg_color=CARD2, text_color=MUTED)
        self.update_display()

    def toggle(self):
        if self.running:
            self.running = False
            self.stop_tick()
            self.start_btn.configure(text="⏵  Resume")
        else:
            self.running = True
            self.start_btn.configure(text="⏸  Pause")
            self.tick()

    def reset(self):
        self.stop_tick()
        self.running = False
        self.start_btn.configure(text="▶  Start")
        self.remaining = self.minutes_for(self.mode) * 60
        self.update_display()

    def skip(self):
        self.stop_tick()
        self.running = False
        self.start_btn.configure(text="▶  Start")
        self.set_mode("Short Break" if self.mode == "Focus" else "Focus")

    def stop_tick(self):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def tick(self):
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self.update_display()
            self._job = self.after(1000, self.tick)
        else:
            self.finish()

    def finish(self):
        self.running = False
        self.start_btn.configure(text="▶  Start")
        finished = self.mode
        if self.data["sound_on"]:
            play_chime(finished)
        if finished == "Focus":
            self.data["completed_total"] += 1
            self.completed_in_cycle += 1
            self.save_data()
            if self.completed_in_cycle >= self.data["sessions_before_long"]:
                self.completed_in_cycle = 0
                self.set_mode("Long Break")
            else:
                self.set_mode("Short Break")
        else:
            self.set_mode("Focus")
        self.flash_ring()
        self.update_display()
        if self.data["auto_start_breaks"] and self.mode != "Focus":
            self.toggle()

    def flash_ring(self):
        """Brief glow pulse so the finish is unmissable."""
        try:
            self.attributes("-topmost", True)
            self.after(1200, lambda: self.attributes(
                "-topmost", bool(self.top_var.get())))
        except Exception:
            pass

    def update_display(self):
        m, s = divmod(max(0, self.remaining), 60)
        total = max(1, self.minutes_for(self.mode) * 60)
        elapsed = 1 - self.remaining / total
        color = MODE_COLOR[self.mode]
        self.ring.set(elapsed, f"{m:02d}:{s:02d}", MODE_EMOJI[self.mode], color)
        dots = "●" * self.completed_in_cycle + "○" * max(
            0, self.data["sessions_before_long"] - self.completed_in_cycle)
        self.status_label.configure(
            text=f"{dots}   ·   {self.mode} {self.minutes_for(self.mode)} min")
        self.streak_label.configure(
            text=f"🔥 {self.data['completed_total']} sessions")
        self.stat_cycle.value_label.configure(
            text=f"{self.completed_in_cycle}/{self.data['sessions_before_long']}")
        self.stat_total.value_label.configure(
            text=str(self.data["completed_total"]))
        done = sum(1 for t in self.data["tasks"] if t["done"])
        self.stat_tasks.value_label.configure(
            text=f"{done}/{len(self.data['tasks'])}")

    # ---------- settings ----------
    def _safe_int(self, entry, fallback, lo=1, hi=180):
        try:
            v = int(entry.get())
            return max(lo, min(hi, v))
        except Exception:
            return fallback

    def save_settings_from_ui(self):
        self.data["focus_min"] = self._safe_int(self.focus_entry, 25, 1, 180)
        self.data["short_min"] = self._safe_int(self.short_entry, 5, 1, 60)
        self.data["long_min"] = self._safe_int(self.long_entry, 15, 1, 90)
        self.data["sessions_before_long"] = self._safe_int(self.cycle_entry, 4, 2, 12)
        # reflect clamped values back into the boxes
        for entry, val in ((self.focus_entry, self.data["focus_min"]),
                           (self.short_entry, self.data["short_min"]),
                           (self.long_entry, self.data["long_min"]),
                           (self.cycle_entry, self.data["sessions_before_long"])):
            try:
                if entry.get().strip() != str(val):
                    entry.delete(0, "end")
                    entry.insert(0, str(val))
            except Exception:
                pass
        self.data["auto_start_breaks"] = bool(self.auto_var.get())
        self.data["sound_on"] = bool(self.sound_var.get())
        self.data["always_on_top"] = bool(self.top_var.get())
        try:
            self.attributes("-topmost", self.data["always_on_top"])
        except Exception:
            pass
        self.save_data()
        if not self.running:
            self.remaining = self.minutes_for(self.mode) * 60
            self.update_display()

    # ---------- tasks ----------
    def add_task(self):
        text = self.task_entry.get().strip()
        if not text:
            return
        self.data["tasks"].append({"text": text, "done": False})
        self.task_entry.delete(0, "end")
        self.save_data()
        self.render_tasks()
        self.update_display()

    def render_tasks(self):
        for w in self.task_list.winfo_children():
            w.destroy()
        if not self.data["tasks"]:
            ctk.CTkLabel(self.task_list,
                         text="No tasks yet — add your first focus goal 👆",
                         font=("Segoe UI", 12), text_color=MUTED).pack(pady=10)
            return
        for i, t in enumerate(self.data["tasks"]):
            row = ctk.CTkFrame(self.task_list, fg_color=CARD2,
                               corner_radius=10)
            row.pack(fill="x", pady=3, padx=2)
            var = ctk.BooleanVar(value=t["done"])
            cb = ctk.CTkCheckBox(row, text=t["text"], variable=var,
                                 font=("Segoe UI", 13),
                                 text_color=MUTED if t["done"] else TEXT,
                                 fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                 border_color=BORDER,
                                 command=lambda idx=i, v=var: self.toggle_task(idx, v))
            cb.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            ctk.CTkButton(row, text="✕", width=30, height=28,
                          corner_radius=8, font=("Segoe UI", 12),
                          fg_color="transparent", text_color=MUTED,
                          hover_color="#2a2a34",
                          command=lambda idx=i: self.delete_task(idx)).pack(
                              side="right", padx=6)

    def toggle_task(self, idx, var):
        self.data["tasks"][idx]["done"] = bool(var.get())
        self.save_data()
        self.render_tasks()
        self.update_display()

    def delete_task(self, idx):
        del self.data["tasks"][idx]
        self.save_data()
        self.render_tasks()
        self.update_display()

    def clear_done(self):
        self.data["tasks"] = [t for t in self.data["tasks"] if not t["done"]]
        self.save_data()
        self.render_tasks()
        self.update_display()


if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
