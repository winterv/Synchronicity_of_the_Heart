import os
import sys
import threading
import time
import vlc
from gpiod.line import Bias, Direction, Value
import gpiod


# --- Configuration ---
AUDIO_FILE = "heartbeat.mp3"  # Path to your MP3 file
SPEED_INTERVAL_SEC = 3
SPEED_INCREASE_PCT = 0.10   # 10% per step
MAX_SPEED = 2.0             # 200%
MIN_SPEED = 0.7             # 40%

# Raspberry Pi GPIO (only used on Pi)
OUTPUT_PIN_FOR_GROUND = 17
button_play_audio = 4
INCREASE_SPEED_PIN = 5  # GPIO 5 (BCM) - monitored for button press

IS_WINDOWS = sys.platform == "win32"

global player
instance = vlc.Instance()
if instance is None:
    print("Could not create VLC instance.")
    sys.exit(1)

path = os.path.abspath(AUDIO_FILE)
if not os.path.isfile(path):
    print(f"Audio file not found: {path}")
    sys.exit(1)

player = instance.media_player_new()
media = instance.media_new(path)
media.add_option('input-repeat=65535') # Loop infinitely
player.set_media(media)
global rate
rate = 1.0 
CHIP_NAME = 'gpiochip0'
_playing_lock = threading.Lock()



def play_mp3():
    """Play the MP3 in a continuous loop with VLC; ramp speed by 10% every 3s up to 300%."""
    global player
    if not player.is_playing():
        with _playing_lock: 
            try:
                print("Playing audio.")
                player.play( )
                time.sleep(0.5) # Wait for the audio to start playing
            except Exception as e:
                print(f"Playback error: {e}")



DEBOUNCE_SEC = 0.2
if not IS_WINDOWS:
    chip = None
    output_line = None
    button_line = None
    try:
        # Open the GPIO chip
        chip = gpiod.Chip("/dev/gpiochip0")

        # Request the output line (HIGH / 3.3V)
        output_line = chip.request_lines(
            config={
                OUTPUT_PIN_FOR_GROUND: gpiod.LineSettings(
                    direction=Direction.OUTPUT,
                    output_value=Value.INACTIVE,
                )
            },
            consumer="output_control",
        )

        # Request the input line with internal pull-up (button to GND when pressed)
        button_line = chip.request_lines(
            config={
                button_play_audio: gpiod.LineSettings(
                    direction=Direction.INPUT,
                    bias=Bias.PULL_UP,
                )
            },
            consumer="button_detect",
        )

        print(f"Set GPIO {OUTPUT_PIN_FOR_GROUND} (physical pin 18) to 3.3V (HIGH)")
        print(f"Monitoring button press on GPIO {button_play_audio}")

        while True:
            # Read the input line value
            # Value.ACTIVE (High) means the button is NOT pressed (due to pull-up)
            # Value.INACTIVE (Low) means the button IS pressed (connected to GND)
            button_state = button_line.get_values()[0]
            
            if button_state == Value.INACTIVE:
                print("Button pressed!")
                threading.Thread(target=play_mp3, daemon=True).start()
            time.sleep(0.1) # Small delay to prevent excessive CPU usage
    except KeyboardInterrupt:
        print("Program stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if output_line:
            output_line.release()
        if button_line:
            button_line.release()
        if chip:
            chip.close()
else:
    from pynput.keyboard import Key, Listener



def increase_speed():
    """Increase the speed of the audio playback (Pi button; placeholder)."""
    global player
    global rate
    if player.is_playing():
        with _playing_lock: 
            try:
                print("Increasing speed.")
                rate = min(rate * (1 + SPEED_INCREASE_PCT), MAX_SPEED)
                if player.set_rate(rate) == -1:
                    print(f"Could not set rate to {rate:.2f}x")
                else:
                    print(f"Playback speed: {rate * 100:.0f}%")
            except Exception as e:
                print(f"Increase speed error: {e}")


def decrease_speed():
    """Decrease the speed of the audio playback."""
    global player
    global rate
    if player.is_playing():
        print("Decreasing speed.") 
        rate = max(rate * (1 - SPEED_INCREASE_PCT), MIN_SPEED)
        if player.set_rate(rate) == -1:
            print(f"Could not set rate to {rate:.2f}x")
        else:
            print(f"Playback speed: {rate * 100:.0f}%")

def on_key_press(key):
    """Windows: trigger play on Space."""
    try:
        if key == Key.space:
            on_play_triggered()
        elif key == Key.up:
            on_increase_speed_triggered()
        elif key == Key.down:
            on_decrease_speed_triggered()
    except AttributeError:
        pass

def on_play_triggered():
    """Start playback (from GPIO button or keyboard)."""
    threading.Thread(target=play_mp3, daemon=True).start()
def on_increase_speed_triggered():
    """Called when the increase-speed button on pin 5 is pressed (Pi only)."""
    print("Increase speed button pressed.")
    threading.Thread(target=increase_speed, daemon=True).start()
def on_decrease_speed_triggered():
    """Decrease the speed of the audio playback."""
    threading.Thread(target=decrease_speed, daemon=True).start()

if IS_WINDOWS:
    print("Windows mode. Press SPACE to play the MP3 and up to increase speed. Ctrl+C to exit.")
    listener = Listener(on_press=on_key_press)
    listener.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop()
else:
    print("Raspberry Pi mode. GPIO {OUTPUT_PIN_FOR_GROUND} is high. Press the button (GPIO {button_play_audio}) to play. Ctrl+C to exit.")
