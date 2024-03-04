import serial
import time

import logging
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout
from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, QProcess, QTimer, pyqtSignal, pyqtSlot, QSize


#%%                   DEFINITION OF WORKER CLASS FOR READING RFID CARD IDS
card_manager = SimpleMFRC522()

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)

class WorkerReadCardId(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        return None
        
    @pyqtSlot()
    def run(self):
        try:
            card_id, _ = card_manager.read()
            self.signals.result.emit({"card_id" : card_id})
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.result.emit({"card_id" : None})
        self.signals.finished.emit()

        return None
    
class WorkerSerialSetup(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        return None
        
    @pyqtSlot()
    def run(self):
        try:
            ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            time.sleep(3)
            ser.reset_input_buffer()
            logging.info("Serial OK")
            self.signals.result.emit({"ser" : ser})
        except:
            logging.info("Serial FAIL")
        return None

class WorkerPrintCanMsgs(QRunnable):
    def __init__(self, ser):
        super().__init__()
        self.signals = WorkerSignals()
        self.ser = ser
        return None

    @pyqtSlot()
    def run(self):
        init_time = time.time()
        while time.time() - init_time > 10:
            if self.ser.in_waiting > 0:
                logging.info(self.ser.readline().decode("utf-8").rstrip())
        return None

#%%

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setup()
        self.main()
        return None
    
    def setup(self):
        self.setWindowTitle("My App")
        self.threadpool = QThreadPool()
        self.serial_setup()

        # ------ BTNS SETUP ------
        self.send_order1_btn = QPushButton("SET 8-MODULE RELAY: 0", parent=self)
        self.send_order2_btn = QPushButton("SET 8-MODULE RELAY: 1", parent=self)
        self.print_canMsgs   = QPushButton("PRINT CAN MSGs", parent=self)

        # ------ VBOX WINDOW SETUP ------
        self.central_widget = QWidget()
        self.vbox_layeout = QVBoxLayout()

        self.vbox_layeout.addWidget(self.send_order1_btn)
        self.vbox_layeout.addWidget(self.send_order2_btn)
        self.vbox_layeout.addWidget(self.print_canMsgs)

        self.central_widget.setLayout(self.vbox_layeout)
        self.setCentralWidget(self.central_widget)

        # ------ BTNs SIGNALS AND CONNECTIONS ------
        self.send_order1_btn.clicked.connect(self.send_order1_btn_clicked)
        self.send_order2_btn.clicked.connect(self.send_order2_btn_clicked)
        self.print_canMsgs.clicked.connect(self.print_canMsgs_clicked)
        return None
    
    def serial_setup(self):
        worker = WorkerSerialSetup()
        worker.signals.result.connect(self.get_serial)
        self.threadpool.start(worker)
        return None
    
    def get_serial(self, res):
        self.ser = res["ser"]
        return None
    
    def send_order1_btn_clicked(self):
        canId = int('100' + '001' + '00' + '{0:08b}'.format(3) + '{0:08b}'.format(9) + '{0:08b}'.format(10), 2)
        canStr = str(canId) + "-0,0,0,0,0,0,0,0,\n"
        self.ser.write(canStr.encode("utf-8"))
        return None
    
    def send_order2_btn_clicked(self):
        canId = int('100' + '001' + '00' + '{0:08b}'.format(3) + '{0:08b}'.format(9) + '{0:08b}'.format(10), 2)
        canStr = str(canId) + "-1,1,1,1,1,1,1,1,\n"
        self.ser.write(canStr.encode("utf-8"))
        return None
    
    def print_canMsgs_clicked(self):
        worker = WorkerPrintCanMsgs(self.ser)
        self.threadpool.start(worker)
        return None
    
    def main(self):
        #self.read_card_id()
        return None

    def read_card_id(self):
        worker = WorkerReadCardId()
        worker.signals.error.connect(self.read_card_id_error)
        worker.signals.result.connect(self.read_card_id_output)
        worker.signals.finished.connect(self.read_card_id_finished)    
        self.threadpool.start(worker)
        return None
    
    def read_card_id_error(self, e):
        logging.info("ERROR:")
        logging.info(e)
        return None
    
    def read_card_id_output(self, res):
        logging.info("CARD_ID:")
        self.card_id = res["card_id"]
        logging.info(self.card_id)
        return None
    
    def read_card_id_finished(self):
        if self.card_id is None:
            self.read_card_id()
        return None
    
    def closeEvent(self, event):
        self.ser.close()
        print('close event fired')
        event.accept()
        return None

    