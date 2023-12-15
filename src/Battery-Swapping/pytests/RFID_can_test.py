import os
import can
import threading
import time as tm
import RPi.GPIO as GPIO
from can.interface import Bus
from mfrc522 import SimpleMFRC522


#%% --- CARD SET-UP ---

card_manager = SimpleMFRC522()


def card_reader():
    print('INITIATING....')
    while True:
        id, text = card_manager.read()
        print('--------')
        print(id)
        print(text)
        print('--------')
        tm.sleep(0.5)
        

    return None



#%% --- CAN BUS SET-UP ---

can.rc['interface'] = 'socketcan'
can.rc['channel'] = 'can0'
can.rc['bitrate'] = 250000

print('\n\rCAN Rx test')
print('Bring up CAN0....')
os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
tm.sleep(0.1)	

try:
	bus = Bus()
except OSError:
	print('Cannot find PiCAN board.')
	exit()
        

def CAN_reader():
    try:
        while True:
            message = bus.recv()	# Wait until a message is received.
            
            c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
            s=''
            for i in range(message.dlc ):
                s +=  '{0:x} '.format(message.data[i])
                
            print(' {}'.format(c+s))
        
        
    except KeyboardInterrupt:
        #Catch keyboard interrupt
        os.system("sudo /sbin/ip link set can0 down")
        print('\n\rKeyboard interrtupt')	

    return None
        


#%% --- MAIN ---

if __name__== '__main__':
     threads = {}
     threads[0] = threading.Thread(target=card_reader)
     threads[1] = threading.Thread(target=CAN_reader)

     for key in threads.keys():
          threads[key].start()
          

      











GPIO.cleanup()