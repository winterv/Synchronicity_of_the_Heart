from visualization import Start_Audio_Visualization
import gpiod
import time
import math
import numpy as np
import colorsys
import control_pattern
import led
import config
import os
os.environ['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
import vlc
import threading
from typing import Any, cast
from gpiod.line import Bias, Direction, Value
import neopixel
from rpi_ws281x import Color
from adafruit_led_animation.helper import PixelMap, PixelSubset
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_blinka.board.raspberrypi import raspi_40pin as pi_board


global red_active
global green_active
global blue_active
red_active = False
green_active = False
blue_active = False

#*****************************Audio Setuo*************************************
#AUDIO_FILE = "heartbeat.mp3"  # Path to your MP3 file
# AUDIO_FILE = "universfield-fast-heartbeat-151928.mp3"
# AUDIO_FILE = "freesound_community-futuristic-heartbeat-60-bpm-7074.mp3"  #bad
#AUDIO_FILE = "freesound_community-heartbeat-foley-34902.mp3"
#AUDIO_FILE = "freesound_community-heart-beating-5857.mp3" 
#AUDIO_FILE = "normalized.wav" 

SPEED_INTERVAL_SEC = 3
SPEED_INCREASE_PCT = 0.10   # 10% per step
MAX_SPEED = 2             # 200%
MIN_SPEED = 0.50             # 40%
global rate
global player
global player_delay
rate = 1
player_delay = 0.1

instance = vlc.Instance()
Heartbeat_file = "music/heart1.mp3"
Background_file = "music/Endless Sunrise.mp3"
Heartbeat_path = os.path.abspath(Heartbeat_file)
Background_path = os.path.abspath(Background_file)
if not os.path.isfile(Heartbeat_path):
    print(f"Audio file not found: {Heartbeat_path}")
if not os.path.isfile(Background_path):
    print(f"Audio file not found: {Background_path}")
player = instance.media_player_new() if instance else None
background_player = instance.media_player_new() if instance else None
background_media = instance.media_new(Background_path) if instance else None
background_player.set_media(background_media) if background_player and background_media else None
background_player.audio_set_volume(30) if background_player and background_player.audio_set_volume else None
media = instance.media_new(Heartbeat_path) if instance else None
#media.add_option('input-repeat=65535') # Loop infinitely
player.set_media(media) if player and media else None
player.audio_set_volume(100) if player and player.audio_set_volume else None

_playing_lock = threading.Lock()

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



def play_mp3():
    """Play the MP3 in a continuous loop with VLC; ramp speed by 10% ever y 3s up to 300%."""
    global player
    global player_delay 
    global playback_rate
    global playing
    if player is None:
        print("VLC media player not initialized; skipping playback loop.")
        return
    if not playing:
        playing = True
        while True:
            #if not player.is_playing():
            start_time = time.time()
            time.sleep(0.1) # Wait for the audio to start playing
            #with _playing_lock: 
            try:                
                player.set_rate(playback_rate)
                player.play( )
            except Exception as e:
                print(f"Playback error: {e}")
            delay = 0.75/playback_rate
            time.sleep(delay)
            player.stop()
            print(f"Time taken: {(time.time() - start_time):.2f}s, player_delay: {(delay):.2f}s, playback_rate: {(playback_rate):.2f}")


def Standard_heart_animation():
    command_to_send = {
        "seg": [
            {
                #fx = 227 is the ID for sound reactive effect
                "col": [
                    [0, 0, 255],
                    [42, 15, 245],
                    [0, 255, 0]], # Primary color: Red (R, G, B)
                "fx": 29, # The ID of the effect/pattern for Heartbeat
                "sx": 55,
                "ix": 59,
                "pal": 0,
                "c1": 128,
                "c2": 128,
                "c3": 16,
            }
        ]
    }
    threading.Thread(target=control_pattern.send_wled_command_udp, args=(config.UDP_IP, config.UDP_PORT, command_to_send), daemon=True).start()


def increase_speed():
    """Increase the speed of the audio playback (Pi button; placeholder)."""
    global playback_rate
    with _playing_lock: 
        try:
            playback_rate = min(playback_rate * (1 + SPEED_INCREASE_PCT), MAX_SPEED)
            print(f"Increasing speed. BPM coefficient: {playback_rate}") 
        except Exception as e:
            print(f"Increase speed error: {e}")


def decrease_speed():
    """Decrease the speed of the audio playback."""
    global playback_rate
    with _playing_lock: 
        try:
            playback_rate = max(playback_rate * (1 - SPEED_INCREASE_PCT), MIN_SPEED)
            print(f"Decreasing speed. BPM coefficient: {playback_rate}")
        except Exception as e:
            print(f"Decrease speed error: {e}")

Standard_heart_animation()
#*****************************LED Strip setup*************************************
# BCM GPIO 18 = physical pin 12. Blinka Pi uses Dn names; GPn is for Pico, not in raspi_40pin.
pixel_pin = pi_board.D10
num_pixels = 48    # The number of LEDs in your strip

# The order of the colors in the strip (can be GRB or RGB)
ORDER = neopixel.RGB
pixels = neopixel.NeoPixel(
    cast(Any, pixel_pin),
    num_pixels,
    brightness=0.6,
    auto_write=False,
    pixel_order=ORDER,
)
# Turn off all LEDs to start
pixels.fill((0, 0, 0))
pixels.show()
 # Adjust speed as needed
def color_wipe(pixels, color, wait, pixel_offset):
    for i in range(pixel_offset, pixel_offset+16):
        pixels[i] = color
        pixels.show() # Update the physical strip
        #pixels.show()
        time.sleep(wait)

# def color_wipe(pixels, color, wait, pixel_offset):
#     for i in range(pixel_offset, pixel_offset+16):
#         pixels[i] = color
#         pixels.show() # Update the physical strip
#         #pixels.show()
#         time.sleep(wait)

def sym_pulse(local_pixels, hue_center, hue_range, speed=0.5):
    """Animation: Symmetrical outward pulse"""
    LED_COUNT = int(len(local_pixels) / 3)
    hue_center = 0
    hue_range = 256
    color_offset = 0    
    offset0 = 0
    offset1 = 16
    offset2 = 32

    while True:
        # Loop through only half to generate pattern
        for i in range(0,(LED_COUNT // 2)+1):
            # Normalize position (0.0 to 1.0)
            dist = i / (LED_COUNT // 2)
            
            # Color Rotation within range
            color_idx = (hue_center + int(dist * hue_range) + color_offset) % 256
            base_color = wheel(color_idx)
            
            # Fading based on sine wave
            pulse = (math.sin(time.monotonic() * 5 + dist * 10) + 1) / 2
            final_color = tuple(int(c * pulse) for c in base_color)
            
            # Apply to both halves
            if i == 0 :
                local_pixels[offset0+0] = final_color
                local_pixels[offset1+0] = final_color
                local_pixels[offset2+0] = final_color
            elif i == 8:
                local_pixels[offset0+8] = final_color
                local_pixels[offset1+8] = final_color
                local_pixels[offset2+8] = final_color
            else:
                local_pixels[offset0+i] = final_color
                local_pixels[offset1+i] = final_color
                local_pixels[offset2+i] = final_color
                local_pixels[offset0+16 - i] = final_color
                local_pixels[offset1+16 - i] = final_color
                local_pixels[offset2+16 - i] = final_color

        led.send_udp_led_data(local_pixels)
        color_offset = (color_offset + 1) % 256
        time.sleep(speed)

def heart_lights_updater():
    global timing_error
    if timing_error < 20:
        command_to_send = {
                "seg": [
                    {
                        #fx = 227 is the ID for sound reactive effect
                        "fx": 79,  # The ID of the effect/pattern for Chase
                        "col": [(0,0,255)], # Primary color: Red (R, G, B)
                        "pal": 63,
                        "sx": speed,
                        "ix": 28,
                    }
                ]
            }
        threading.Thread(target=control_pattern.send_wled_command_udp, args=(config.UDP_IP, config.UDP_PORT, command_to_send), daemon=True).start()
    elif timing_error < 10:
        background_player.play() if background_player and background_player.play else None



def wheel(pos):
    """Generates RGB colors (0-255 range)."""
    pos = 255 - pos
    if pos < 85: return (255 - pos * 3, 0, pos * 3)
    if pos < 170: pos -= 85; return (0, pos * 3, 255 - pos * 3)
    pos -= 170; return (pos * 3, 255 - pos * 3, 0)


def create_symmetric_hue_pulse(num_leds, time_step, pulse_speed=0.1, hue_range=1.0):
    """
    Creates a symmetric, hue-rotating pulse for an LED array.
    
    Args:
        num_leds: Total number of LEDs in the strip/array.
        time_step: Current time/frame (float) to animate the pulse.
        pulse_speed: How fast the hue rotates.
        hue_range: How much of the color wheel to use (0.0 to 1.0).
        
    Returns:
        A list of (R, G, B) tuples, each 0-255.
    """
    leds = []
    center = num_leds / 2
    
    for i in range(num_leds):
        # 1. Symmetric Distance calculation (0 at center/ends, max in middle)
        # Symmetrical pulse looks good when mirrored from the center
        dist = abs(i - center) / center  # 0.0 to 1.0
        
        # 2. Hue calculation: Rotate hue over time, modulated by distance
        # Create a "pulse" effect by mapping distance to saturation/brightness
        hue = (dist * hue_range + time_step * pulse_speed) % 1.0
        
        # 3. Brightness pulse: Bright in center, dim at ends (or vice versa)
        # Using a sine wave creates a smooth, pulsing "pulse"
        brightness = np.sin(dist * np.pi) * 0.5 + 0.5 # Smooth 0.5 to 1.0
        
        # 4. Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, brightness)
        leds.append((int(r * 255), int(g * 255), int(b * 255)))
        
    return leds

def run_hue_pulse():
    start_time = time.time()
    duration = 5.0
    while time.time() < start_time + duration:
        leds = create_symmetric_hue_pulse(48, time.time())
        led.send_udp_led_data(leds)
        time.sleep(0.01)


# # Set the first three pixels to R, G, B
# print("Lighting first 3 pixels...")
# pixels[0] = (255, 0, 0) # Red
# pixels[1] = (0, 255, 0) # Green
# pixels[2] = (0, 0, 255) # Blue
# pixels.show()
#threading.Thread(target=color_wipe, args=(pixels, (0, 255, 0), 0.2, 0), daemon=True).start()
#threading.Thread(target=color_wipe, args=(pixels, (0, 0, 255), 0.2, 16), daemon=True).start()
#threading.Thread(target=color_wipe, args=(pixels, (255, 0, 0), 0.2, 32), daemon=True).start()
#threading.Thread(target=Start_Audio_Visualization, daemon=True).start()

def run_pulse(pulse1, pulse2, pulse3):
    start_time = time.time()
    duration = 20
    red_heart = PixelSubset(pixels, 0, 16) 
    green_heart = PixelSubset(pixels, 16, 32) 
    blue_heart = PixelSubset(pixels, 32, 48) 



    while time.time() < start_time + duration:
        pulse1.animate()
        pulse2.animate()
        pulse3.animate()
        time.sleep(0.01)
    
    threading.Thread(target=sym_pulse, args=(red_heart, 0, 26, 0.01)).start()
    threading.Thread(target=sym_pulse, args=(green_heart, 0, 256, 0.01)).start()
    threading.Thread(target=sym_pulse, args=(blue_heart, 0, 56, 0.01)).start()
    

red_heart = PixelMap(pixels, [(0, 16)]) 
green_heart = PixelMap(pixels, [(16, 32)]) 
blue_heart = PixelMap(pixels, [(32, 48)]) 

speed = 0.05
period = 1
rainbow_animation_green = Rainbow(green_heart, speed=0.01, period=2)
rainbow_animation_blue = Rainbow(blue_heart, speed=0.01, period=2)
rainbow_animation_red = Rainbow(red_heart, speed=0.01, period=2)
pulse_animation_red = Pulse(green_heart, speed=speed, period=period, color=Color(0, 255, 0))
pulse_animation_green = Pulse(blue_heart, speed=speed, period=period, color=Color(0, 0, 255))
pulse_animation_blue = Pulse(red_heart, speed=speed, period=period, color=Color(255, 0, 0))

#threading.Thread(target=run_pulse, args=(pulse_animation_red, pulse_animation_green, pulse_animation_blue), daemon=False).start()
NUM_PIXELS = 48

heart_leds = [(0, 0, 0)] * NUM_PIXELS
threading.Thread(target=sym_pulse, args=(heart_leds, 0, 256, 0.01), daemon=False).start()
threading.Thread(target = heart_lights_updater).start()


threading.Thread(target=play_mp3, daemon=True).start()

def synchronization_check():
    global time_red
    global time_green
    global time_blue
    global timing_error
    if time_red and time_green and time_blue:
        timing_error = abs(time_red - time_green) + abs(time_red - time_blue) + abs(time_green - time_blue)
        print(f"Error: {timing_error}")
        

#*****************************button setup*************************************

# Configuration based on BCM numbering for Raspberry Pi 4
# GPIO Chip is typically 'gpiochip0' for older Pis (including Pi 4)
GPIO_CHIP = "gpiochip0"
OUTPUT_PIN = 4
OUTPUT_1_PIN = 27
INPUT_RED_BUTTON = 26
INPUT_GREEN_BUTTON = 24
INPUT_BLUE_BUTTON = 17
INPUT_UP_BUTTON = 14
INPUT_DOWN_BUTTON = 15
chip = None
output_line = None
input_line = None

# Open the GPIO chip
chip = gpiod.Chip("/dev/gpiochip0")
global time_red
global time_green
global time_blue
global timing_error
time_red=0
time_green =0 
time_blue =0
timing_error = 999999999

# Request the input line with internal pull-up (button to GND when pressed)
input_line = chip.request_lines(
    config={
        INPUT_RED_BUTTON: gpiod.LineSettings(
            direction=Direction.INPUT,
            bias=Bias.PULL_UP,
        ),
        INPUT_GREEN_BUTTON: gpiod.LineSettings(
            direction=Direction.INPUT,
            bias=Bias.PULL_UP,
        ),
        INPUT_BLUE_BUTTON: gpiod.LineSettings(
            direction=Direction.INPUT,
            bias=Bias.PULL_UP,
        ),
        INPUT_UP_BUTTON: gpiod.LineSettings(
            direction=Direction.INPUT,
            bias=Bias.PULL_UP,
        ),
        INPUT_DOWN_BUTTON: gpiod.LineSettings(
            direction=Direction.INPUT,
            bias=Bias.PULL_UP,
        )
    },
    consumer="button_detect",
)

try:
    while True:
        # Read the input line value
        # Value.ACTIVE (High) means the button is NOT pressed (due to pull-up)
        # Value.INACTIVE (Low) means the button IS pressed (connected to GND)
        button_state_red = input_line.get_values()[0]
        button_state_green = input_line.get_values()[1]
        button_state_blue = input_line.get_values()[2]
        button_state_up = input_line.get_values()[3]
        button_state_down = input_line.get_values()[4]
      
        
        if button_state_red == Value.INACTIVE:
            print("Button red pressed!")
            #rainbow_animation.animate()
            #threading.Thread(target=play_mp3, daemon=True).start()
            WAIT_TIME = 0.02
            pixel_offset = 0
            #color_wipe(pixels, (255, 255, 255), WAIT_TIME, pixel_offset) # White
            time_red = time.time()
            synchronization_check()

        elif button_state_green == Value.INACTIVE:
            print("Button green pressed!")
            WAIT_TIME = 0.02
            pixel_offset = 18
            #color_wipe(pixels, (255, 255, 255), WAIT_TIME, pixel_offset) # White
            time_green = time.time()
            synchronization_check()

        elif button_state_blue == Value.INACTIVE:
            print("Button blue pressed!")
            WAIT_TIME = 0.02
            pixel_offset = 36
            #color_wipe(pixels, (255, 255, 255), WAIT_TIME, pixel_offset) # White
            time_blue = time.time()
            synchronization_check()
    # --------------Speed Buttons--------------------------------
        elif button_state_up == Value.INACTIVE:
            print("Button up pressed!")
            increase_speed()
            #for speed in range(125,255,10):
            command_to_send = {
                "seg": [
                    {
                        #fx = 227 is the ID for sound reactive effect
                        "fx": 79,  # The ID of the effect/pattern for Chase
                        "col": [(0,0,255)], # Primary color: Red (R, G, B)
                        "pal": 63,
                        "sx": speed,
                        "ix": 28,
                    }
                ]
            }
            threading.Thread(target=control_pattern.send_wled_command_udp, args=(config.UDP_IP, config.UDP_PORT, command_to_send), daemon=True).start()
            #control_pattern.send_wled_command_udp(config.UDP_IP, config.UDP_PORT, command_to_send)
            time.sleep(2)
            Standard_heart_animation()
            #color_wipe(pixels, (0, 0, 255), 0.2, 0) 
            
            

        elif button_state_down == Value.INACTIVE:
            print("Button down pressed!")
            decrease_speed()
            #run_hue_pulse()
            threading.Thread(target=led.send_udp_color, args=(config.UDP_IP, config.UDP_PORT, 48, 0, 0, 255), daemon=True).start()
            #led.send_udp_color(config.UDP_IP, config.UDP_PORT, 48, 0, 0, 255)
            time.sleep(0.2)

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
