import machine as pi
import utime as time


LED = pi.Pin(16, pi.Pin.OUT)
B1= pi.Pin(18, pi.Pin.IN)

state = 0  
previous_button_state = 0
counter = 0

while True:
    time.sleep(0.1)
    counter = ((counter) % 20) + 1
    
    button_state = B1.value()
    
    if button_state == 1 and previous_button_state == 0:
        state = (state + 1) % 3
        i = 0
        while i < 6 :
            i += 1
            LED.value(not LED.value())
            time.sleep(0.05)

    previous_button_state = button_state
    
    if state == 0:
        LED.value(0) 
    elif state == 1 and counter % 10 == 0:
        LED.value(not LED.value())    
    elif state == 2 and counter % 5 == 0:
        LED.value(not LED.value()) 



      
