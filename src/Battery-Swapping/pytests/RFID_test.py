import time as tm
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

card_manager = SimpleMFRC522()


card_manager.write("Owner : Andres Moreno")

tm.sleep(3)    



id, text = card_manager.read()
print(id)
print(text)


GPIO.cleanup()
    