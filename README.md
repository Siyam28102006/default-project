# 🌙 Midnight Pomodoro Timer

Premium OLED-dark desktop Pomodoro app (Python + CustomTkinter).

## Why you'll love it
- True-black midnight theme, glowing progress ring
- Mode colors: ember Focus, teal Short Break, violet Long Break
- Big 46px Start / Pause + Reset / Skip, keyboard shortcuts
- Stats row: cycle, completed, tasks done
- Always-on-top, auto-start breaks, richer finish chime
- Tasks with clear-done + persistent settings in `pomodoro_data.json`

## Features
- Focus 25 / Short 5 / Long 15 (all editable) + cycle length
- Start / Pause / Reset / Skip — buttons or `Space / R / S / 1-2-3`
- Auto-switch: long break every N sessions
- Ring progress, session dots, streak + stats
- Sound + auto-start + always-on-top (toggleable)
- Task list with save (add / check / delete / clear done)
- Settings + tasks persist in `pomodoro_data.json`

## ⬇️ Download the app (no Python needed)

**Windows:** [Download MidnightPomodoro.exe v1.0.0](https://github.com/Siyam28102006/default-project/releases/tag/v1.0.0)
— download and double-click to run.

## Run from source
```bash
pip install -r requirements.txt
python pomodoro.py
```

## Files
- `pomodoro.py` — the whole app (single file)
- `requirements.txt` — `customtkinter`
- `pomodoro_data.json` — auto-created on first use (your settings/tasks, ignored by git)
