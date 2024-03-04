import time
import serial
import logging
from PyQt5.QtWidgets import qApp, QMainWindow
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


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
                #self.signals.results.emit(line)
                print(line)
        return None


#%%              DEFINITION OF MAIN WINDOW WIDGET

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setup()
        return None
    
    def setup(self):
        self.threadpool =  QThreadPool()
        self.setWindowTitle("My App")
        self.serial_setup()
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
        #worker.signals.results.connect(self.serialPrint)
        self.threadpool.start(worker)
        return None
    
    def serialPrint(line):
        print(line)
        return None
    
    def closeEvent(self, event):
        self.ser.close()
        time.sleep(2)
        print('close event fired')
        event.accept()
        return None
    

    

    

    