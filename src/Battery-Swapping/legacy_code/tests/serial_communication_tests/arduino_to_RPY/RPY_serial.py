import serial
import time

ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
time.sleep(3)
ser.reset_input_buffer()
print("Serial OK")

try:
    while True:
        time.sleep(0.01)
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").rstrip()
            print(line)
except KeyboardInterrupt:
    print("Close serial communication")
    ser.close()
