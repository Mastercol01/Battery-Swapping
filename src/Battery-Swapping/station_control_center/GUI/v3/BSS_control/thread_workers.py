from mfrc522 import SimpleMFRC522
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


#%%                   DEFINITION OF WORKER CLASS FOR READING SERIAL DATA

class SerialReadWorkerSignals(QObject):
    results = pyqtSignal(str)


class SerialReadWorker(QRunnable):
    def __init__(self, ser):
        super(SerialReadWorker, self).__init__()
        self.ser = ser
        self.signals = SerialReadWorkerSignals()
        return None
    
    @pyqtSlot()
    def run(self):
        while True:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode("utf-8").rstrip()
                    self.signals.results.emit(line)
                except UnicodeDecodeError:
                    pass
        return None
    
    
#%%                   DEFINITION OF WORKER CLASS FOR READING RFID CARD DATA
    
card_manager = SimpleMFRC522()

class RfidReadWorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)


class RfidReadWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = RfidReadWorkerSignals()
        return None
        
    
    @pyqtSlot()
    def run(self):
        try:
            #card_id = dummy_card_read_id()
            card_id, _ = card_manager.read()
            print(card_id)
            self.signals.result.emit({"card_id" : card_id})

        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.result.emit({"card_id" : None})
        
        self.signals.finished.emit()

        return None