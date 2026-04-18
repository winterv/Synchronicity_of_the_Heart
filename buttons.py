import gpiod
import time
import signal
import sys
import os
os.environ['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
import vlc
import threading
from typing import Any, cast
from gpiod.line import Bias, Direction, Value
import neopixel
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_blinka.board.raspberrypi import raspi_40pin as pi_board


#*****************************button setup*************************************

# Configuration based on BCM numbering for Raspberry Pi 4
# GPIO Chip is typically 'gpiochip0' for older Pis (including Pi 4)
GPIO_CHIP = "gpiochip0"
OUTPUT_PIN = 17
INPUT_PIN = 4
OUTPUT_1_PIN = 27
INPUT_1_PIN = 22
chip = None
output_line = None
input_line = None

#*****************************Audio Setuo*************************************
AUDIO_FILE = "heartbeat.mp3"  # Path to your MP3 file
# AUDIO_FILE = "universfield-fast-heartbeat-151928.mp3"
# AUDIO_FILE = "freesound_community-futuristic-heartbeat-60-bpm-7074.mp3"  #bad
#AUDIO_FILE = "freesound_community-heartbeat-foley-34902.mp3"
#AUDIO_FILE = "freesound_community-heart-beating-5857.mp3" 
#AUDIO_FILE = "normalized.wav" 
#AUDIO_FILE = "heart1.mp3"
SPEED_INTERVAL_SEC = 3
SPEED_INCREASE_PCT = 0.10   # 10% per step
MAX_SPEED = 1.2             # 200%
MIN_SPEED = 0.01             # 40%
global rate
global player
global player_delay
rate = 1
player_delay = 0.1

instance = vlc.Instance()
path = os.path.abspath(AUDIO_FILE)
if not os.path.isfile(path):
    print(f"Audio file not found: {path}")
player = instance.media_player_new() if instance else None
media = instance.media_new(path) if instance else None
#media.add_option('input-repeat=65535') # Loop infinitely
player.set_media(media) if player and media else None
player.audio_set_volume(100) if player and player.audio_set_volume else None
global playback_rate
global playing
playing = False
playback_rate = 1.1

def set_bluetooth_output(player):
    # List all available audio output devices
    devices = player.audio_output_device_enum()
    
    if devices:
        curr = devices
        while curr:
            device_info = curr.contents
            device_name = device_info.device.decode('utf-8')
            device_description = device_info.description.decode('utf-8')
            print(f"Device: {device_name} - {device_description}")
            
            # Look for "Bluetooth" or your device's specific name (e.g., "EWA")
            if "Bluetooth" in device_description or "bluez" in device_name:
                print(f"✅ Found Bluetooth Device: {device_description}")
                player.audio_output_device_set(None, device_name)
                return True
            curr = curr.contents.next
    print("❌ Bluetooth device not found in VLC device list.")
    return False

set_bluetooth_output(player)  

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

play_mp3()

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


#*****************************LED Strip setup*************************************
# BCM GPIO 18 = physical pin 12. Blinka Pi uses Dn names; GPn is for Pico, not in raspi_40pin.
pixel_pin = pi_board.D10
num_pixels = 130        # The number of LEDs in your strip

# The order of the colors in the strip (can be GRB or RGB)
ORDER = neopixel.RGB
pixels = neopixel.NeoPixel(
    cast(Any, pixel_pin),
    num_pixels,
    brightness=0.8,
    auto_write=False,
    pixel_order=ORDER,
)
# Turn off all LEDs to start
pixels.fill((0, 0, 0))
pixels.show()
rainbow_animation = Rainbow(pixels, speed=0.01, period=2) # Adjust speed as needed
def color_wipe(pixels, color, wait):
    for i in range(len(pixels)):
        pixels[i] = color
        pixels.show() # Update the physical strip
        time.sleep(wait)

# # Set the first three pixels to R, G, B
# print("Lighting first 3 pixels...")
# pixels[0] = (255, 0, 0) # Red
# pixels[1] = (0, 255, 0) # Green
# pixels[2] = (0, 0, 255) # Blue
# pixels.show()



try:
    # Open the GPIO chip
    chip = gpiod.Chip("/dev/gpiochip0")

    # Request the output line (HIGH / 3.3V)
    output_line = chip.request_lines(
        config={
            OUTPUT_PIN: gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.INACTIVE,
            ),
            OUTPUT_1_PIN: gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.INACTIVE,
            )
        },
        consumer="output_control",
    )

    # Request the input line with internal pull-up (button to GND when pressed)
    input_line = chip.request_lines(
        config={
            INPUT_PIN: gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
            ),
            INPUT_1_PIN: gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
            )
        },
        consumer="button_detect",
    )
    
    print(f"Set GPIO {OUTPUT_PIN} (physical pin 18) to 3.3V (HIGH)")
    print(f"Monitoring button press on GPIO {INPUT_PIN}")

    while True:
        # Read the input line value
        # Value.ACTIVE (High) means the button is NOT pressed (due to pull-up)
        # Value.INACTIVE (Low) means the button IS pressed (connected to GND)
        button_state0 = input_line.get_values()[0]
        button_state1 = input_line.get_values()[1]
        
        if button_state0 == Value.INACTIVE:
            print("Button 0 pressed!")
            rainbow_animation.animate()
            threading.Thread(target=play_mp3, daemon=True).start()

            # Optional: Add your button press logic here
        elif button_state1 == Value.INACTIVE:
            print("Button 1 pressed!")
            WAIT_TIME = 0.02
            color_wipe(pixels, (255, 0, 0), WAIT_TIME) # Red

            # Optional: Add your button press logic here
        else:
            # print("Button not pressed") # Uncomment to see continuous updates
            pass
            
        time.sleep(0.1) # Small delay to prevent excessive CPU usage

except KeyboardInterrupt:
    print("Program stopped by user")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if output_line:
        output_line.release()
    if input_line:
        input_line.release()
    if chip:
        chip.close()
