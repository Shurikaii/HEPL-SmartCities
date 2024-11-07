import utime as time
import machine as pi
from ws2812 import WS2812
from random import choice

# Define color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 150, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (150, 0, 255)
PINK = (255, 0, 255)
ROSE = (255, 0, 150)

# RGB color list for easy reference
RGB = (RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, PINK, ROSE)

# Initialize microphone input and LED output
mic = pi.ADC(0)
led = WS2812(16, 1)

led.pixels_fill(PURPLE)  # Set start led color to purple (because I like it)
led.pixels_show()

# Main loop to read noise levels and change LED colors
while True:
    avg = 0

    # Collect multiple noise readings to calculate average
    for i in range(500):
        noise = mic.read_u16() / 256  # Scale the noise reading
        avg += noise

    avg_noise = avg / 500  # Calculate the average noise level
    print(avg_noise)

    """
    # Change LED color based on noise threshold (discarded)
    if avg_noise < 50:
        led.pixels_fill(GREEN)  # Low noise, set LED to green
        led.pixels_show()
    elif 50 <= avg_noise < 55:
        led.pixels_fill(ORANGE)  # Medium noise, set LED to orange
        led.pixels_show()
    elif avg_noise >= 55:
        led.pixels_fill(RED)  # High noise, set LED to red
        led.pixels_show()
    """

    if avg_noise >= 55:
    
        rnd_color = random.choice(RGB)    # Select a random color

        # Make color is not the same as the previous one
        while rnd_color == prev_color:
            rnd_color = random.choice(RGB)
        
        prev_color = color

        led.pixels_fill(color)  # High noise, set LED to random color
        led.pixels_show()

        # Sleep time to make sure pulse ended (0.2s -> max 300bpm (Trash-metal proof))
        time.sleep(0.2)