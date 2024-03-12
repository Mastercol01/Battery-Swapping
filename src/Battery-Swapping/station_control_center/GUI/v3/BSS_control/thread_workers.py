import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


#%%                   DEFINITION OF WORKER CLASS FOR READING SERIAL DATA

class SerialReadWorkerSignals(QObject):
    serialReadResults = pyqtSignal(str)


class SerialReadWorker(QRunnable):
    def __init__(self, ser):
        super(SerialReadWorker, self).__init__()
        self.ser = ser
        self.signals = SerialReadWorkerSignals()
        self.keepRunning = True
        return None
    
    def endRun(self):
        self.keepRunning = False
        return None
    
    @pyqtSlot()
    def run(self):
        while self.keepRunning:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode("utf-8").rstrip()
                    self.signals.serialReadResults.emit(line)
                except UnicodeDecodeError:
                    pass
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
                card_id = card_manager.read_id()
                self.signals.rfidReadResults.emit(int(card_id))
            except Exception:
                self.signals.rfidReadResults.emit(-1)
        GPIO.cleanup()
        return None