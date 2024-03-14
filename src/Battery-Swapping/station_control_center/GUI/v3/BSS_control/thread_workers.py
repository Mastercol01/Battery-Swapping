import serial
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


#%%                   DEFINITION OF WORKER CLASS FOR READING SERIAL DATA

class SerialReadWorkerSignals(QObject):
    serialReadResults   = pyqtSignal(str)
    serialLaunchFailure = pyqtSignal()


class SerialReadWorker(QRunnable):
    def __init__(self):
        super(SerialReadWorker, self).__init__()
        self.signals = SerialReadWorkerSignals()
        self.keepRunning = True
        return None
    
    def endRun(self):
        self.keepRunning = False
        return None
    
    def setup(self):
        try:
            self.ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            self.ser.reset_input_buffer()
            print("SERIAL LAUNCH SUCCESS")
        except:
            print("SERIAL LAUNCH FAILURE")
            self.signals.serialLaunchFailure()
        return None
    
    def sendCanMsg(self, canStr):
        self.ser.write(canStr.encode("utf-8"))
        return None
    
    @pyqtSlot()
    def run(self):
        self.setup()
        while self.keepRunning:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode("utf-8").rstrip()
                    self.signals.serialReadResults.emit(line)
                except UnicodeDecodeError:
                    pass
        self.ser.close()
        print("SHUTTING SERIAL READER THREAD DOWN")
        return None
    
    
#%%                   DEFINITION OF WORKER CLASS FOR READING RFID CARD DATA
    
card_manager = SimpleMFRC522()

class RfidReadWorkerSignals(QObject):
    rfidReadResults = pyqtSignal(int)


class RfidReadWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = RfidReadWorkerSignals()
        self.keepRunning = True
        return None
    
    def endRun(self):
        self.keepRunning = False
        return None
        
    @pyqtSlot()
    def run(self):
        while self.keepRunning:
            try:
                card_id = card_manager.read_id_no_block()
                if card_id:
                    self.signals.rfidReadResults.emit(card_id)
            except Exception:
                self.signals.rfidReadResults.emit(-1)
        GPIO.cleanup()
        print("SHUTTING RFID READER THREAD DOWN")
        return None