from __future__ import print_function
from __future__ import division

import platform
from typing import Any, cast
import numpy as np
import config
import time
import socket
# ESP8266 uses WiFi communication
if config.DEVICE == 'esp8266':
    _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Raspberry Pi controls the LED strip directly
elif config.DEVICE == 'pi':
    from rpi_ws281x import Adafruit_NeoPixel
    strip = Adafruit_NeoPixel(config.N_PIXELS, config.LED_PIN,
                              config.LED_FREQ_HZ, config.LED_DMA,
                              config.LED_INVERT, config.BRIGHTNESS)
    strip.begin()


_gamma = np.load(config.GAMMA_TABLE_PATH)
"""Gamma lookup table used for nonlinear brightness correction"""

_prev_pixels = np.tile(253, (3, config.N_PIXELS))
"""Pixel values that were most recently displayed on the LED strip"""

pixels = np.tile(1, (3, config.N_PIXELS))
"""Pixel values for the LED strip"""

_is_python_2 = int(platform.python_version_tuple()[0]) == 2

def _update_esp8266():
    """Sends UDP packets to ESP8266 to update LED strip values

    The ESP8266 will receive and decode the packets to determine what values
    to display on the LED strip. The communication protocol supports LED strips
    with a maximum of 256 LEDs.

    The packet encoding scheme is:
        |i|r|g|b|
    where
        i (0 to 255): Index of LED to change (zero-based)
        r (0 to 255): Red value of LED
        g (0 to 255): Green value of LED
        b (0 to 255): Blue value of LED
    """
    global pixels, _prev_pixels
    # Truncate values and cast to integer
    pixels = np.clip(pixels, 0, 255).astype(int)
    # Optionally apply gamma correc tio
    p = np.copy(pixels) # _gamma[pixels] if config.SOFTWARE_GAMMA_CORRECTION else np.copy(pixels)
    MAX_PIXELS_PER_PACKET = 126
    # Pixel indices
    idx = range(pixels.shape[1])
    idx = [i for i in idx if not np.array_equal(p[:, i], _prev_pixels[:, i])]
    n_packets = len(idx) // MAX_PIXELS_PER_PACKET + 1
    idx = np.array_split(idx, n_packets)
    for packet_indices in idx:
        m = [1,2]
        for i in packet_indices:

            m.append(i)  # Index of pixel to change
            m.append(p[0][i])  # Pixel red value
            m.append(p[1][i])  # Pixel green value
            m.append(p[2][i])  # Pixel blue value
        m_bytes = bytes(m)
        _sock.sendto(m_bytes, (config.UDP_IP, config.UDP_PORT))
    _prev_pixels = np.copy(p)


def _update_pi():
    """Writes new LED values to the Raspberry Pi's LED strip

    Raspberry Pi uses the rpi_ws281x to control the LED strip directly.
    This function updates the LED strip with new values.
    """
    global pixels, _prev_pixels
    # Truncate values and cast to integer
    pixels = np.clip(pixels, 0, 255).astype(int)
    # Optional gamma correction
    p = _gamma[pixels] if config.SOFTWARE_GAMMA_CORRECTION else np.copy(pixels)
    # Encode 24-bit LED values in 32 bit integers
    r = np.left_shift(p[0][:].astype(int), 8)
    g = np.left_shift(p[1][:].astype(int), 16)
    b = p[2][:].astype(int)
    rgb = np.bitwise_or(np.bitwise_or(r, g), b)
    # Update the pixels
    for i in range(config.N_PIXELS):
        # Ignore pixels if they haven't changed (saves bandwidth)
        if np.array_equal(p[:, i], _prev_pixels[:, i]):
            continue
        #strip._led_data[i] = rgb[i]
        cast(Any, strip)._led_data[i] = int(rgb[i])
    _prev_pixels = np.copy(p)
    strip.show()


def update():
    """Updates the LED strip values"""
    if config.DEVICE == 'esp8266':
        _update_esp8266()
    elif config.DEVICE == 'pi':
        _update_pi()
    else:
        raise ValueError('Invalid device selected')




def send_udp_color(ip, port, num_leds, r, g, b):
    """Sends a UDP packet to set all LEDs to a specific RGB color using WARLS protocol."""
    
    # The WARLS protocol requires a specific header.
    # Byte 0: Protocol ID (1 = WARLS)
    # Byte 1: LED start index (0, for the entire strip)
    header = bytes([2, 1])
    
    # Create the data payload for the LEDs
    # Each LED requires 3 bytes: Red, Green, Blue
    led_data = bytes()
    for _ in range(num_leds):
        led_data += bytes([r, g, b])
        
    # Combine header and LED data
    packet = header + led_data
    
    # Send the UDP packet
    _sock = None
    try:
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.connect((config.UDP_IP, config.UDP_PORT))
        _sock.sendto(packet, (config.UDP_IP, config.UDP_PORT))
        print(f"Sent UDP packet to {ip}:{port} to set all {num_leds} LEDs to RGB({r}, {g}, {b})")
    except socket.error as e: # type: ignore
        print(f"Error sending UDP packet: {e}")
    finally:
        if _sock is not None:
            _sock.close()

        time.sleep(.1)

def send_udp_led_data(leds):
    """Sends a UDP packet to set the LED data using WARLS protocol."""
    
    # The WARLS protocol requires a specific header.
    # Byte 0: Protocol ID (1 = WARLS)
    # Byte 1: LED start index (0, for the entire strip)
    header = bytes([2, 1])
    
    # Create the data payload for the LEDs
    # Each LED requires 3 bytes: Red, Green, Blue
    led_data = bytes()
    for led in leds:
        led_data += bytes([led[0], led[1], led[2]])
        
    # Combine header and LED data
    packet = header + led_data
    
    # Send the UDP packet
    try:
        _sock.sendto(packet, (config.UDP_IP_robot_hearts, config.UDP_PORT_robot_hearts))
    except socket.error as e:
        print(f"Error sending UDP packet: {e}")
    #finally:
        #_sock.close()

# Execute this file to run a LED strand test
# If everything is working, you should see a red, green, and blue pixel scroll
# across the LED strip continuously
if __name__ == '__main__':
    
    pixels *= 0
    pixels[0, 0] = 255  # Set 1st pixel red
    pixels[1, 1] = 255  # Set 2nd pixel green
    pixels[2, 2] = 255  # Set 3rd pixel blue
    print('Starting LED strand test')
    while True:
        pixels = np.roll(pixels, 1, axis=0)
        update()
        time.sleep(.1)


