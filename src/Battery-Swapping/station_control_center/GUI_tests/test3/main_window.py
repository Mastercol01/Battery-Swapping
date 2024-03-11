import time
import serial
from functools import partial
from PyQt5.QtWidgets import qApp, QMainWindow
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QTimer
from station_control_center.GUI.v3.BSS_control.control_center import ControlCenter
import station_control_center.GUI.v3.BSS_control.CanUtils as canUtils


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
                line = self.ser.readline().decode("utf-8").rstrip()
                self.signals.results.emit(line)
        return None


#%%              DEFINITION OF MAIN WINDOW WIDGET

class MainWindow(QMainWindow):
    signals = WorkerSignals()
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setup()
        return None
    
    def setup(self):
        self.setWindowTitle("My App")
        self.threadpool =  QThreadPool()
        self.ControlCenter_obj = ControlCenter()
        self.time_setup()
        self.serial_setup()

        for slotAddress in self.ControlCenter_obj.SLOT_ADDRESSES:
            self.ControlCenter_obj.modules[slotAddress].SIGNALS.command.connect(self.sendCanStr)

        for slotAddress in self.ControlCenter_obj.SLOT_ADDRESSES:
            self.ControlCenter_obj.modules[slotAddress].setSolenoidsStates([1,0,0])

        self.ControlCenter_obj.turnOnLedStripsBasedOnState()

        return None
    
    def updateCurrentGlobalTime(self):
        self.currentGlobalTime += 0.25
        self.ControlCenter_obj.updateCurrentGlobalTimeForAllModules(self.currentGlobalTime)

        if not self.currentGlobalTime % 5:
            self.ControlCenter_obj.modules[canUtils.MODULE_ADDRESS.SLOT1]._debugPrint()

        if not self.currentGlobalTime % 5.5:
            self.ControlCenter_obj.modules[canUtils.MODULE_ADDRESS.SLOT1].battery._debugPrint()

        return None
    
    def time_setup(self):
        self.currentGlobalTime = 0
        self.globalTimer = QTimer()
        self.globalTimer.setInterval(250)
        self.globalTimer.timeout.connect(self.updateCurrentGlobalTime)
        return None
    
    
    def serial_setup(self):
        try:
            self.ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            self.ser.reset_input_buffer()
            print("SERIAL LAUNCH SUCCESFUL")
        except:
            print("FAILURE TO LAUNCH SERIAL")
            qApp.exit()

        worker = SerialReadWorker(self.ser)
        worker.signals.results.connect(self.ControlCenter_obj.updateStatesFromCanStr)
        self.threadpool.start(worker)
        return None
    
    def sendCanStr(self, canStr):
        print(canStr)
        return None
    
    def closeEvent(self, event):
        self.ser.close()
        time.sleep(2)
        print('close event fired')
        event.accept()
        return None
    

    

    

    