import gpiod
import time
import signal
import sys
from typing import Any, cast
from gpiod.line import Bias, Direction, Value
import neopixel
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_blinka.board.raspberrypi import raspi_40pin as pi_board

# BCM GPIO 18 = physical pin 12. Blinka Pi uses Dn names; GPn is for Pico, not in raspi_40pin.
pixel_pin = pi_board.D18
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
