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
        time.sleep(0.2)

    previous_button_state = button_state
    
    if state == 0:
        LED.value(0) 
    elif state == 1 and counter % 10 == 0:
        LED.value(not LED.value())    
    elif state == 2:
        LED.value(not LED.value()) 



      
