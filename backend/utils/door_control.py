# backend/utils/door_control.py
import time
try:
    import RPi.GPIO as GPIO           # real pins when you deploy
    GPIO.setmode(GPIO.BCM)
    RELAY = 18
    GPIO.setup(RELAY, GPIO.OUT, initial=GPIO.LOW)
    def _set(state): GPIO.output(RELAY, state)
except (ImportError, RuntimeError):
    # Windows/mock fallback
    def _set(state): print(f"[MockGPIO] relay -> {state}")

def open_door(seconds=5):
    _set(True)
    time.sleep(seconds)
    close_door()

def close_door():
    _set(False)
    time.sleep(0.5)  # debounce time
    _set(True)  # reset to initial state