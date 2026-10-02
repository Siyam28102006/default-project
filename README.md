# 🍅 Easy Pomodoro Timer

Simple desktop Pomodoro app built with Python + CustomTkinter.

## Features
- Focus 25 / Short 5 / Long 15 (all editable)
- Start / Pause / Reset / Skip
- Auto-switch: long break every 4 sessions
- Session dots + total completed counter
- Sound on finish + auto-start breaks (toggleable)
- Task list with save (add / check / delete)
- Settings + tasks persist in `pomodoro_data.json`

## Run
```bash
pip install -r requirements.txt
python pomodoro.py
```

## Files
- `pomodoro.py` — the whole app (single file)
- `requirements.txt` — `customtkinter`
- `pomodoro_data.json` — auto-created on first use (your settings/tasks, ignored by git)
