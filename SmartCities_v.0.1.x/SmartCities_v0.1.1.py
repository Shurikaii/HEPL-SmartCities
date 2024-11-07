import machine as pi
import utime as time
from lcd1602 import LCD1602
from dht11 import DHT

# Define pin assignments and constants
LED = pi.Pin(16, pi.Pin.OUT)  # LED pin setup
B1 = pi.Pin(18, pi.Pin.IN)   # Button pin setup
POT = pi.ADC(0)              # Potentiometer pin setup for analog input
PWM1 = pi.PWM(pi.Pin(27))    # PWM pin for buzzer control
I2C = pi.I2C(1, scl=pi.Pin(7), sda=pi.Pin(6), freq=400000)  # I2C bus setup for LCD
lcd = LCD1602(I2C, 2, 16)    # LCD display setup (2 rows, 16 columns)
dht = DHT(20)                # DHT sensor pin for temperature and humidity

lcd.display()                # Display LCD
time.sleep(0.5)              # Delay for 0.5 seconds
lcd.print("Hello")           # Print "Hello" on the LCD screen
time.sleep(1)                # Wait for 1 second

# Frequency values for LED blinking based on button press
FREQ_LED = [0, 2, 5, 10]

# State for paused mode
PAUSED = [0]

# Define melodies as lists of note frequencies
NIRVANA_COME_AS_YOU_ARE = [120, 82, 0, 82, 0, 87, 0, 92, 0, 110, 0, 92, 0, 110, 0, 92, 0, 92, 0, 87, 0, 82, 0, 123, 0, 82, 0, 82, 0, 123, 0, 82, 0, 87, 0, 92, 0, 110, 0, 92, 0, 110, 0, 92, 0, 92, 0, 87, 0, 82, 0, 123, 0, 82, 0, 82, 0, 123]
STAR_WARS_IMPERIAL_MARCH = [120, 131, 0, 131, 0, 131, 0, 103, 0, 155, 0, 131, 0, 103, 0, 155, 0, 131, 0, 196, 0, 196, 0, 196, 0, 207, 0, 155, 0, 123, 0, 103, 0, 155, 0, 130, 0, 262, 0, 130, 0, 130, 0, 262, 0, 247, 233, 220, 247, 233, 220, 0, 103, 0, 155, 0, 131, 0, 103, 0, 155, 0, 131, 131]
MELODY = [PAUSED, NIRVANA_COME_AS_YOU_ARE, STAR_WARS_IMPERIAL_MARCH]  # Collection of melodies

# Initialize various state variables for the system
state = 0  # Current mode state
previous_button_state = 0  # Previous button state for debouncing
previous_vol = 0  # Previous volume for comparison
counter = 0  # General counter for timing
t1 = time.time()  # Timestamp for button presses
prev_mel_state = 0  # Previous melody state for transition
led_state = 0  # LED state for frequency cycling
mel_state = 0  # Melody state
prev_temp = 0  # Previous temperature reading for comparison
prev_set_temp = 0  # Previous set temperature for comparison
i = 0  # Counter for melody index
temp = 0  # Temperature reading
buzz = True  # Buzzer state flag

# Button cycle functions to handle state transitions based on button presses
def button_cycle(button, states_nbr, actual_state):
    """
    Cycle through states based on button press.

    :param button: Pin object for button
    :param states_nbr: Number of states to cycle through
    :param actual_state: Current state
    :return: New state after button press
    """
    global previous_button_state, state

    btn_state = button.value()

    # If button is pressed (state changes from 0 to 1)
    if btn_state == 1 and previous_button_state == 0:
        if states_nbr > 0:
            state = (actual_state + 1) % states_nbr  # Cycle to next state
        else:
            raise ValueError('Invalid states_nbr. Must be > 0.')

    previous_button_state = btn_state
    return state


def button_multi(button, states_nbr, actual_state, delay):
    """
    Multi-press button state control with delay between state changes.

    :param button: Pin object for button
    :param states_nbr: Number of states to cycle through
    :param actual_state: Current state
    :param delay: Delay in seconds to reset the state
    :return: New state after button press
    """
    global t1, previous_button_state, state

    btn_state = button.value()

    # Multi-press detection with delay between presses
    if btn_state == 1 and previous_button_state == 0:
        if time.time() - t1 < delay:
            if states_nbr > 0:
                state = (actual_state + 1) % states_nbr
            else:
                raise ValueError('Invalid states_nbr. Must be > 0.')
        else:
            state = 0  # Reset state if delay is too long
        t1 = time.time()

    previous_button_state = btn_state
    return state


# LED control function to blink at different frequencies based on button input
def led_control_100hz(mode, led, button, freq_list):
    """
    Control LED blinking at 100Hz frequency based on button input.

    :param mode: Operation mode ('multi' or 'cycle')
    :param led: Pin object for LED
    :param button: Pin object for button
    :param freq_list: List of frequencies for LED blinking
    """
    global counter, led_state
    time.sleep(0.01)  # 100Hz cycle
    counter = (counter % 100) + 1
    states_nbr = len(freq_list)
    
    if states_nbr <= 0:
        raise ValueError('Invalid freq_list length. Must not be empty')

    # Choose state cycling mode
    if mode in ["multi", "m"]:
        led_state = button_multi(button, states_nbr, led_state, 1.5)
    elif mode in ["cycle", "c"]:
        led_state = button_cycle(button, states_nbr, led_state)
    else:
        raise ValueError('Invalid mode value. Must be "multi"/"m" or "cycle"/"c".')

    # Frequency control based on selected state
    print(led_state)
    freq = freq_list[led_state]

    if freq != 0:
        approx_period = int(100 / freq)
        if counter % approx_period == 0:
            led.value(not led.value())  # Toggle LED state
    else:
        led.value(0)  # Turn off LED if frequency is 0


# Melody control function to play melody based on button and volume control
def melody_100hz(melody_matrix, buzzer_pwm, vol_adc, button, led):
    """
    Play melody at 100Hz frequency based on button input and volume.

    :param melody_matrix: List of melodies to play
    :param buzzer_pwm: PWM object for buzzer
    :param vol_adc: ADC object for volume control
    :param button: Pin object for button
    :param led: Pin object for LED
    """
    global counter, previous_vol, prev_mel_state, i, mel_state
    time.sleep(0.01)
    counter = (counter % 100) + 1

    melodies_nbr = len(melody_matrix)
    vol = int((vol_adc.read_u16() / 65535) * 100)  # Normalize ADC value to percentage volume

    # Print volume if it changes significantly
    if abs(vol - previous_vol) > 5:
        print(vol)
        previous_vol = vol

    # Control melody playback if volume is above threshold
    if vol > 0:
        mel_state = button_cycle(button, melodies_nbr, mel_state)
        melody = melody_matrix[mel_state]
        bpm = melody[0] * 2.5  # Calculate beats per minute from the melody
        print(mel_state)
        if bpm > 0:
            approx_period = int(100 / (bpm / 60))  # Calculate period between notes

            if prev_mel_state != mel_state:
                i = 0
                prev_mel_state = mel_state

            if counter % approx_period == 0:
                i = (i % (len(melody) - 1)) + 1  # Move to next note in the melody
                note = melody[i]
                if note > 0:
                    buzzer_pwm.freq(note)  # Set buzzer frequency
                    buzzer_pwm.duty_u16(vol * 20)  # Set buzzer volume
                    led.value(1)  # Turn on LED when playing note
                else:
                    buzzer_pwm.duty_u16(0)  # Turn off buzzer if note is 0
                    led.value(0)  # Turn off LED
        else:
            PWM1.duty_u16(0)  # Turn off buzzer if melody BPM is 0
    else:
        PWM1.duty_u16(0)  # Turn off buzzer if volume is 0


# Temperature control function with alarm if temperature exceeds set threshold
def temp_control():
    """
    Control the temperature, adjust the LED and buzzer based on set temperature.
    """
    global prev_temp, start, temp, i, start_read, start_alarm1, start_alarm2, buzz

    # Read potentiometer value and calculate set temperature
    pot = POT.read_u16()
    set_temp = 15 + float((pot / 65535) * 20)

    # Read temperature from DHT sensor and update display
    if time.ticks_diff(time.ticks_ms(), start_read) > 1000:
        temp = dht.readTemperature()
        print(temp)

        lcd.clear()
        lcd.setCursor(0, 0)
        if temp - set_temp < 3:
            PWM1.duty_u16(0)
            lcd.print(f"Set: {str(set_temp):.4}")  # Display set temperature
            lcd.setCursor(0, 1)
            lcd.print("Ambient: " + str(temp))  # Display current temperature

        if temp > set_temp and temp - set_temp < 3:
            LED.value(not LED.value())  # Blink LED if temperature is slightly above set point
        elif temp < set_temp:
            LED.value(0)  # Turn off LED if temperature is below set point
        start_read = time.ticks_ms()

    # Alarm condition if temperature exceeds set limit
    if temp - set_temp > 3:
        PWM1.freq(500)
        time.sleep(0.1)
        PWM1.freq(1000)
        time.sleep(0.1)
        PWM1.freq(1500)
        time.sleep(0.1)

        # Flash alarm and buzzer at intervals
        if time.ticks_diff(time.ticks_ms(), start_alarm1) > 500:
            LED.value(not LED.value())
            buzz = not buzz
            if buzz:
                PWM1.duty_u16(3000)  # Activate buzzer
            else:
                PWM1.duty_u16(0)  # Deactivate buzzer
            i = (i + 1) % 21  # Update alarm message display
            lcd.setCursor(0, 0)
            lcd.clear()
            alarm_str = "                ALARM"
            lcd.print(alarm_str[i:])  # Display alarm message
            start_alarm1 = time.ticks_ms()

        if time.ticks_diff(time.ticks_ms(), start_alarm2) > 1500:
            lcd.setCursor(0, 1)
            lcd.print("ALARM")  # Display "ALARM" message
            start_alarm2 = time.ticks_ms()


# Initialize timing variables for various operations
start_read = time.ticks_ms()
start_alarm1 = time.ticks_ms()
start_alarm2 = time.ticks_ms()

while True:
    # Uncomment the following lines to test different modes
    # led_control_100hz("m", LED, B1, FREQ_LED)
    # melody_100hz(MELODY, PWM1, POT, B1, LED)
    temp_control()  # Call the temperature control function
