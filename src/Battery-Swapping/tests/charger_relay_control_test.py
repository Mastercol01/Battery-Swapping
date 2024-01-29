
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(36, GPIO.OUT)

for i in range(20):
    GPIO.output(36, True)
    time.sleep(2)
    GPIO.output(36, False)
    time.sleep(2)

GPIO.cleanup()
