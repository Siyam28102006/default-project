# Midnight Pomodoro in Docker (runs anywhere, no Python needed).
# The app shows up in your BROWSER at http://localhost:5800 via built-in noVNC.
FROM jlesage/baseimage-gui:debian-12-v4

# System deps: Python + Tk + a decent font. `add-pkg` cleans apt cache for us.
RUN add-pkg python3 python3-tk python3-pip fonts-dejavu \
    && pip3 install --no-cache-dir --break-system-packages customtkinter

# App files.
COPY pomodoro.py /app/pomodoro.py
COPY pomodoro.png /app/pomodoro.png
COPY startapp.sh /startapp.sh
RUN chmod +x /startapp.sh

# Data (settings/tasks) lives here so it can be mounted as a volume.
ENV POMODORO_DATA_FILE=/config/pomodoro_data.json

RUN set-cont-env APP_NAME "Midnight Pomodoro"
