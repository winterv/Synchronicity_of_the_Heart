import os
import sys
import threading
import time
import vlc

# --- Configuration ---
# AUDIO_FILE = "heartbeat.mp3"  # Path to your MP3 file
# AUDIO_FILE = "universfield-fast-heartbeat-151928.mp3"
# AUDIO_FILE = "freesound_community-futuristic-heartbeat-60-bpm-7074.mp3"  #bad
#AUDIO_FILE = "freesound_community-heartbeat-foley-34902.mp3"
#AUDIO_FILE = "freesound_community-heart-beating-5857.mp3" 
#AUDIO_FILE = "normalized.wav" 
AUDIO_FILE = "heart1.mp3"
SPEED_INTERVAL_SEC = 3
SPEED_INCREASE_PCT = 0.10   # 10% per step
MAX_SPEED = 1.2             # 200%
MIN_SPEED = 0.01             # 40%

# Raspberry Pi GPIO (only used on Pi)
POWER_PIN = 3   # GPIO 3 (BCM) - high to power the button 
BUTTON_PIN = 4  # GPIO 4 (BCM) - monitored for button press
INCREASE_SPEED_PIN = 5  # GPIO 5 (BCM) - monitored for button press

IS_WINDOWS = sys.platform == "win32"

# --- GPIO setup (Raspberry Pi only) ---
power_pin = None
button_play_audio = None
button_increase_speed = None
global rate
global player
global player_delay
rate = 1
player_delay = 0.1

instance = vlc.Instance()
path = os.path.abspath(AUDIO_FILE)
if not os.path.isfile(path):
    print(f"Audio file not found: {path}")
player = instance.media_player_new() 
media = instance.media_new(path)
#media.add_option('input-repeat=65535') # Loop infinitely
player.set_media(media)
player.audio_set_volume(100) 
global playback_rate
global playing
playing = False
playback_rate = 1.1



DEBOUNCE_SEC = 0.2
if not IS_WINDOWS:
    from gpiozero import Button, LED
    from signal import pause
    power_pin = LED(POWER_PIN)
    power_pin.on()
    button_play_audio = Button(BUTTON_PIN, pull_up=False, bounce_time=DEBOUNCE_SEC)
    button_increase_speed = Button(INCREASE_SPEED_PIN, pull_up=False, bounce_time=DEBOUNCE_SEC)
else:
    from pynput.keyboard import Key, Listener

_playing_lock = threading.Lock()

 
def play_mp3():
    """Play the MP3 in a continuous loop with VLC; ramp speed by 10% ever y 3s up to 300%."""
    global player
    global player_delay 
    global playback_rate
    global playing
    if not playing:
        playing = True
        while True:
            #if not player.is_playing():

            start_time = time.time()
        # print(f"Playing audio. with player_delay: {player_delay}")
            time.sleep(player_delay) # Wait for the audio to start playing
            #with _playing_lock: 
            try:                
                player.set_rate(playback_rate)
                player.play( )
            except Exception as e:
                print(f"Playback error: {e}")
            delay = 0.75/playback_rate
            #print(f"Playing audio. with playback_rate: {delay}")
            time.sleep(delay)
            player.stop()
            print(f"Time taken: {time.time() - start_time}")

    


def increase_speed():
    """Increase the speed of the audio playback (Pi button; placeholder)."""
    global player
    global rate
    global player_delay
    global playing

    #if player.is_playing():
    #    with _playing_lock: 

    try:
        rate = min(rate * (1 + SPEED_INCREASE_PCT), MAX_SPEED)
        #print(f"Rate: {rate}")
        player_delay= min(player_delay * (1 + SPEED_INCREASE_PCT), MAX_SPEED)
        print(f"Increasing speed. BPM coefficient: {player_delay}") 
        # if player.set_rate(rate) == -1:
        #     print(f"Could not set rate to {rate:.2f}x")
        # else:
        #     print(f"Playback speed: {rate * 100:.0f}%")
    except Exception as e:
        print(f"Increase speed error: {e}")


def decrease_speed():
    """Decrease the speed of the audio playback."""
    global player
    global rate
    global player_delay
    #if player.is_playing():
    rate = max(rate * (1 - SPEED_INCREASE_PCT), MIN_SPEED)
    player_delay = max(player_delay * (1 - SPEED_INCREASE_PCT), MIN_SPEED)
    #print(f"Rate: {rate}")
    print(f"Decreasing speed. BPM coefficient: {player_delay}")
    # if player.set_rate(rate) == -1:
    #     print(f"Could not set rate to {rate:.2f}x")
    # else: 
    #     print(f"Playback speed: {rate * 100:.0f}%")

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
            time.sleep(0.01)
    except KeyboardInterrupt: 
        listener.stop()
else:
    button_play_audio.when_pressed = on_play_triggered
    button_increase_speed.when_pressed = on_increase_speed_triggered
    print("Raspberry Pi mode. Pin 3 is high. Press the button (pin 4) to play. Ctrl+C to exit.")
    pause()
