import serial
import time

ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
time.sleep(3)
ser.reset_input_buffer()
print("Serial OK")

try:
    while True:
        time.sleep(1)
        canId = int('100' + '001' + '00' + '{0:08b}'.format(3) + '{0:08b}'.format(9) + '{0:08b}'.format(10), 2)
        canStr = str(canId) + "-1,1,1,1,1,1,1,1,\n"
        print(f"Send message to Arduino: {canStr}")
        ser.write(canStr.encode("utf-8"))
        time.sleep(1)
        canId = int('100' + '001' + '00' + '{0:08b}'.format(3) + '{0:08b}'.format(9) + '{0:08b}'.format(10), 2)
        canStr = str(canId) + "-0,0,0,0,0,0,0,0,\n"
        print(f"Send message to Arduino: {canStr}")
        ser.write(canStr.encode("utf-8"))
except KeyboardInterrupt:                                                                                                               
    print("Close serial communication")
    ser.close()    