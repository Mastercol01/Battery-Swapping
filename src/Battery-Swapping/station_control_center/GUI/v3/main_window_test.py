import time
import serial
from functools import partial
from PyQt5.QtWidgets import qApp, QMainWindow
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QTimer
from control_center import ControlCenter
import CanUtils as canUtils


#%%                   DEFINITION OF WORKER CLASS FOR READING SERIAL DATA

class WorkerSignals(QObject):
    results = pyqtSignal(str)


class SerialReadWorker(QRunnable):
    def __init__(self, ser):
        super(SerialReadWorker, self).__init__()
        self.ser = ser
        self.signals = WorkerSignals()
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
    
#%%
    
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("My App")
        self.threadpool =  QThreadPool()
       

        self.currentGlobalTime = 0
        self.globalTimer = QTimer()
        self.globalTimer.setInterval(250)
        self.globalTimer.timeout.connect(self.updateCurrentGlobalTime)
        self.globalTimer.start()

        self.ControlCenter_obj = ControlCenter()
        self.ControlCenter_obj.connect_sendCanMsg(self.sendCanMsg)
        self.serial_setup()

    
        
        QTimer().singleShot(2000, partial(self.ControlCenter_obj.modules[canUtils.MODULE_ADDRESS.SLOT8].setSolenoidsStates, [1,0,0]))
        QTimer().singleShot(8000, self.ControlCenter_obj.turnOnLedStripsBasedOnState)
        QTimer().singleShot(11000, partial(self.ControlCenter_obj.modules[canUtils.MODULE_ADDRESS.SLOT8].setSolenoidsStates, [0,0,0]))
        QTimer().singleShot(12000, self.ControlCenter_obj.turnOffAllLedStrips)
        return None
    
    def serial_setup(self):
        try:
            self.ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            self.ser.reset_input_buffer()
            print("SERIAL LAUNCH SUCCESFUL")
        except:
            print("FAILURE TO LAUNCH SERIAL")
            qApp.exit()

        self.worker = SerialReadWorker(self.ser)
        self.worker.signals.results.connect(self.ControlCenter_obj.updateStatesFromCanStr)
        self.threadpool.start(self.worker)
        return None
    
    def updateCurrentGlobalTime(self):
        self.currentGlobalTime += 0.25
        self.ControlCenter_obj.updateCurrentGlobalTime(self.currentGlobalTime)
        return None
        
    def sendCanMsg(self, canStr):
        self.ser.write(canStr.encode("utf-8"))
        return None
    
    def closeEvent(self, event):
        self.ser.close()
        time.sleep(2)
        print('close event fired')
        event.accept()
        return None
    
