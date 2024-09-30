import machine as pi
import utime as time
from lcd1602 import LCD1602
from dht11 import *


# Define pin assignments and constants
LED = pi.Pin(16, pi.Pin.OUT)  # LED pin
B1 = pi.Pin(18, pi.Pin.IN)  # Button pin
POT = pi.ADC(0)  # Potentiometer pin
PWM1 = pi.PWM(pi.Pin(27))  # PWM pin for buzzer
I2C = pi.I2C(1, scl = pi.Pin(7), sda = pi.Pin(6), freq = 400000)
lcd = LCD1602(I2C, 2, 16)
dht = DHT(20)

lcd.display()

time.sleep(0.5)

lcd.print("Hello")

time.sleep(1)

FREQ_LED = [0, 2, 5, 10]  # Frequency values for LED control

PAUSED = [0]

NIRVANA_COME_AS_YOU_ARE = [120,
    82, 0, 82, 0, 87, 0, 92, 0, 110, 0, 92, 0, 110, 0, 92,
    0, 92, 0, 87, 0, 82, 0, 123, 0, 82, 0, 82, 0, 123, 0, 82,
    0, 87, 0, 92, 0, 110, 0, 92, 0, 110, 0, 92, 0, 92, 0, 87,
    0, 82, 0, 123, 0, 82, 0, 82, 0, 123
    ]

STAR_WARS_IMPERIAL_MARCH = [120, 
    131, 0, 131, 0, 131, 0, 103, 0, 155, 0, 131, 0, 103, 0, 155,
    0, 131, 0, 196, 0, 196, 0, 196, 0, 207, 0, 155, 0, 123, 0, 103,
    0, 155, 0, 130, 0, 262, 0, 130, 0, 130, 0, 262, 0, 247, 233,
    220, 247, 233, 220, 0, 103, 0, 155, 0, 131, 0, 103,
    0, 155, 0, 131, 131
    ]

MELODY = [PAUSED, NIRVANA_COME_AS_YOU_ARE, STAR_WARS_IMPERIAL_MARCH]

# Initialize variables
state = 0
previous_button_state = 0
previous_vol = 0
counter = 0
t1 = time.time()
prev_mel_state = 0
led_state = 0
mel_state = 0
prev_temp = 0
prev_set_temp = 0
i = 0
temp = 0
buzz = True
# Define Button cycle functions
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

    if btn_state == 1 and previous_button_state == 0:
        if states_nbr > 0:
            state = (actual_state + 1) % states_nbr
        else:
            raise ValueError('Invalid states_nbr. Must be > 0.')

    previous_button_state = btn_state
    return state

def button_multi(button, states_nbr, actual_state, delay):
    """
    Multi-press button state control.

    :param button: Pin object for button
    :param states_nbr: Number of states to cycle through
    :param actual_state: Current state
    :param delay: Delay in seconds to reset the state
    :return: New state after button press
    """
    global t1, previous_button_state, state

    btn_state = button.value()

    if btn_state == 1 and previous_button_state == 0:
        if time.time() - t1 < delay:
            if states_nbr > 0:
                state = (actual_state + 1) % states_nbr
            else:
                raise ValueError('Invalid states_nbr. Must be > 0.')
        else:
            state = 0
        t1 = time.time()

    previous_button_state = btn_state
    return state

# Define LED control function
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

    if mode in ["multi", "m"]:
        led_state = button_multi(button, states_nbr, led_state, 1.5)
    elif mode in ["cycle", "c"]:
        led_state = button_cycle(button, states_nbr, led_state)
    else:
        raise ValueError('Invalid mode value. Must be "multi"/"m" or "cycle"/"c".')
    print(led_state)
    freq = freq_list[led_state]

    if freq != 0:
        approx_period = int(100 / freq)
        if counter % approx_period == 0:
            led.value(not led.value())
    else:
        led.value(0)

# Define melody control function
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
    vol = int((vol_adc.read_u16() / 65535) * 100)

    # Print volume if it changes by more than 5
    if abs(vol - previous_vol) > 5:
        print(vol)
        previous_vol = vol

    if vol > 0:
        mel_state = button_cycle(button, melodies_nbr, mel_state)
        melody = melody_matrix[mel_state]
        bpm = melody[0] * 2.5
        print(mel_state)
        if bpm > 0:
            approx_period = int(100 / (bpm / 60))

            if prev_mel_state != mel_state:
                i = 0
                prev_mel_state = mel_state

            if counter % approx_period == 0:
                i = (i % (len(melody) - 1)) + 1
                note = melody[i]
                if note > 0:
                    buzzer_pwm.freq(note)
                    buzzer_pwm.duty_u16(vol * 20)
                    led.value(1)
                else:
                    buzzer_pwm.duty_u16(0)
                    led.value(0)
        else:
            PWM1.duty_u16(0)
    else:
        PWM1.duty_u16(0)


def temp_control():
    
    global prev_temp, start, temp, i, start_read, start_alarm1, start_alarm2, buzz
    
    
    pot = POT.read_u16()
    set_temp = 15 + float((pot / 65535) * 20)
    
    if time.ticks_diff(time.ticks_ms(), start_read) > 1000:
        temp = dht.readTemperature()
        print(temp)

        lcd.clear()
        lcd.setCursor(0, 0)
        if temp - set_temp < 3:
            PWM1.duty_u16(0)
            lcd.print(f"Set: {str(set_temp):.4}")
            lcd.setCursor(0, 1)
            lcd.print("Ambient: "+str(temp))

        if temp > set_temp and temp - set_temp < 3:
            LED.value(not LED.value())
        elif temp < set_temp:
            LED.value(0)
        start_read = time.ticks_ms()
    
    if temp - set_temp > 3:

        PWM1.freq(500)
        time.sleep(0.1)
        PWM1.freq(1000)
        time.sleep(0.1)
        PWM1.freq(1500)
        time.sleep(0.1)
        
        if time.ticks_diff(time.ticks_ms(), start_alarm1)>500:
            LED.value(not LED.value())
            buzz = not buzz
            if buzz:
                PWM1.duty_u16(3000)
            else:
                PWM1.duty_u16(0)
            i = (i+1) % 21
            lcd.setCursor(0, 0)
            lcd.clear()
            alarm_str = "                ALARM"
            lcd.print(alarm_str[i:])
            start_alarm1 = time.ticks_ms()
        if time.ticks_diff(time.ticks_ms(), start_alarm2) > 1500:
            lcd.setCursor(0, 1)
            lcd.print("ALARM")
            start_alarm2 = time.ticks_ms()

start_read = time.ticks_ms()
start_alarm1 = time.ticks_ms()
start_alarm2 = time.ticks_ms()
while True:
    # led_control_100hz("m", LED, B1, FREQ_LED)
    # melody_100hz(MELODY, PWM1, POT, B1, LED)
    temp_control()