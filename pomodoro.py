"""
Easy Pomodoro Timer - desktop app built with CustomTkinter.
Run:  pip install -r requirements.txt
      python pomodoro.py
"""

import json
import os
import customtkinter as ctk

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(APP_DIR, "pomodoro_data.json")

DEFAULTS = {
    "focus_min": 25,
    "short_min": 5,
    "long_min": 15,
    "sessions_before_long": 4,
    "auto_start_breaks": True,
    "sound_on": True,
    "tasks": [],  # [{"text": str, "done": bool}]
    "completed_total": 0,
}

MODES = ("Focus", "Short Break", "Long Break")


def play_sound():
    """Cross-platform beep. Winsound on Windows, Tk bell otherwise."""
    try:
        import winsound
        winsound.Beep(880, 500)
        winsound.Beep(660, 300)
    except Exception:
        try:
            root_bell = ctk._default_root
            if root_bell is not None:
                root_bell.bell()
        except Exception:
            print("\a")


class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.data = self.load_data()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("Pomodoro Timer")
        self.geometry("420x720")
        self.resizable(False, False)

        self.mode = "Focus"
        self.running = False
        self.remaining = self.data["focus_min"] * 60
        self.completed_in_cycle = 0
        self._job = None

        self.build_ui()
        self.set_mode("Focus", reset=True)
        self.render_tasks()

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
    def build_ui(self):
        self.title_label = ctk.CTkLabel(self, text="🍅 Pomodoro Timer",
                                        font=("Arial", 22, "bold"))
        self.title_label.pack(pady=(16, 4))

        self.mode_menu = ctk.CTkSegmentedButton(self, values=list(MODES),
                                                command=self.on_mode_click)
        self.mode_menu.pack(pady=8)
        self.mode_menu.set("Focus")

        self.time_label = ctk.CTkLabel(self, text="25:00",
                                       font=("Arial", 64, "bold"))
        self.time_label.pack(pady=6)

        self.progress = ctk.CTkProgressBar(self, width=320)
        self.progress.pack(pady=4)
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.status_label.pack(pady=2)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)

        self.start_btn = ctk.CTkButton(btn_row, text="Start", width=110,
                                       command=self.toggle)
        self.start_btn.grid(row=0, column=0, padx=5)

        ctk.CTkButton(btn_row, text="Reset", width=90,
                      fg_color="gray", command=self.reset).grid(row=0, column=1, padx=5)

        ctk.CTkButton(btn_row, text="Skip ⏭", width=90,
                      fg_color="gray", command=self.skip).grid(row=0, column=2, padx=5)

        # Settings
        settings = ctk.CTkFrame(self)
        settings.pack(padx=16, pady=8, fill="x")

        ctk.CTkLabel(settings, text="Settings (minutes)",
                     font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=4, pady=(8, 4))

        self.focus_entry = self._num_field(settings, "Focus", 1, self.data["focus_min"])
        self.short_entry = self._num_field(settings, "Short", 2, self.data["short_min"])
        self.long_entry = self._num_field(settings, "Long", 3, self.data["long_min"])

        ctk.CTkLabel(settings, text="Long every").grid(row=3, column=0, padx=6, pady=4)
        self.cycle_entry = ctk.CTkEntry(settings, width=50)
        self.cycle_entry.insert(0, str(self.data["sessions_before_long"]))
        self.cycle_entry.grid(row=3, column=1, padx=6, pady=4)
        ctk.CTkLabel(settings, text="sessions").grid(row=3, column=2, padx=2)

        self.auto_var = ctk.BooleanVar(value=self.data["auto_start_breaks"])
        self.sound_var = ctk.BooleanVar(value=self.data["sound_on"])
        ctk.CTkCheckBox(settings, text="Auto-start breaks",
                        variable=self.auto_var,
                        command=self.save_settings_from_ui).grid(row=4, column=0, columnspan=2, pady=4)
        ctk.CTkCheckBox(settings, text="Sound",
                        variable=self.sound_var,
                        command=self.save_settings_from_ui).grid(row=4, column=2, columnspan=2, pady=4)

        ctk.CTkButton(settings, text="Apply", width=100,
                      command=self.save_settings_from_ui).grid(row=5, column=0, columnspan=4, pady=(4, 10))

        # Tasks
        tasks = ctk.CTkFrame(self)
        tasks.pack(padx=16, pady=4, fill="both", expand=True)

        ctk.CTkLabel(tasks, text="Tasks", font=("Arial", 13, "bold")).pack(pady=(8, 2))

        add_row = ctk.CTkFrame(tasks, fg_color="transparent")
        add_row.pack(fill="x", padx=8)
        self.task_entry = ctk.CTkEntry(add_row, placeholder_text="Add a task + Enter")
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.task_entry.bind("<Return>", lambda _e: self.add_task())
        ctk.CTkButton(add_row, text="+", width=40,
                      command=self.add_task).pack(side="right")

        self.task_list = ctk.CTkScrollableFrame(tasks, height=130)
        self.task_list.pack(fill="both", expand=True, padx=8, pady=8)

    def _num_field(self, parent, label, col, value):
        ctk.CTkLabel(parent, text=label).grid(row=1, column=col - 1, padx=6)
        entry = ctk.CTkEntry(parent, width=60)
        entry.insert(0, str(value))
        entry.grid(row=2, column=col - 1, padx=6)
        return entry

    # ---------- timer logic ----------
    def minutes_for(self, mode):
        return {"Focus": self.data["focus_min"],
                "Short Break": self.data["short_min"],
                "Long Break": self.data["long_min"]}[mode]

    def on_mode_click(self, value):
        self.set_mode(value, reset=True)

    def set_mode(self, mode, reset=True):
        self.mode = mode
        try:
            self.mode_menu.set(mode)
        except Exception:
            pass
        if reset:
            self.stop_tick()
            self.running = False
            self.start_btn.configure(text="Start")
            self.remaining = self.minutes_for(mode) * 60
        self.update_display()

    def toggle(self):
        if self.running:
            self.running = False
            self.stop_tick()
            self.start_btn.configure(text="Resume")
        else:
            self.running = True
            self.start_btn.configure(text="Pause")
            self.tick()

    def reset(self):
        self.stop_tick()
        self.running = False
        self.start_btn.configure(text="Start")
        self.remaining = self.minutes_for(self.mode) * 60
        self.update_display()

    def skip(self):
        self.stop_tick()
        self.running = False
        self.start_btn.configure(text="Start")
        self.next_mode()

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
        self.start_btn.configure(text="Start")
        if self.data["sound_on"]:
            play_sound()
        if self.mode == "Focus":
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
        self.update_display()
        if self.data["auto_start_breaks"] and self.mode != "Focus":
            self.toggle()  # auto-start the break

    def next_mode(self):
        if self.mode == "Focus":
            self.set_mode("Short Break")
        else:
            self.set_mode("Focus")

    def update_display(self):
        m, s = divmod(max(0, self.remaining), 60)
        self.time_label.configure(text=f"{m:02d}:{s:02d}")
        total = max(1, self.minutes_for(self.mode) * 60)
        self.progress.set(1 - self.remaining / total)
        dots = "●" * self.completed_in_cycle + "○" * max(
            0, self.data["sessions_before_long"] - self.completed_in_cycle)
        self.status_label.configure(
            text=f"{self.mode}  •  {dots}  •  Total done: {self.data['completed_total']}")

    # ---------- settings ----------
    def _safe_int(self, entry, fallback, lo=1, hi=180):
        try:
            v = int(entry.get())
            return max(lo, min(hi, v))
        except Exception:
            return fallback

    def save_settings_from_ui(self):
        self.data["focus_min"] = self._safe_int(self.focus_entry, 25)
        self.data["short_min"] = self._safe_int(self.short_entry, 5)
        self.data["long_min"] = self._safe_int(self.long_entry, 15)
        self.data["sessions_before_long"] = self._safe_int(self.cycle_entry, 4, 2, 12)
        self.data["auto_start_breaks"] = bool(self.auto_var.get())
        self.data["sound_on"] = bool(self.sound_var.get())
        self.save_data()
        # refresh current timer length if not running
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

    def render_tasks(self):
        for w in self.task_list.winfo_children():
            w.destroy()
        for i, t in enumerate(self.data["tasks"]):
            row = ctk.CTkFrame(self.task_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            var = ctk.BooleanVar(value=t["done"])
            cb = ctk.CTkCheckBox(row, text=t["text"], variable=var,
                                 command=lambda idx=i, v=var: self.toggle_task(idx, v))
            cb.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="✕", width=30, fg_color="transparent",
                          text_color="gray",
                          command=lambda idx=i: self.delete_task(idx)).pack(side="right")

    def toggle_task(self, idx, var):
        self.data["tasks"][idx]["done"] = bool(var.get())
        self.save_data()

    def delete_task(self, idx):
        del self.data["tasks"][idx]
        self.save_data()
        self.render_tasks()


if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
