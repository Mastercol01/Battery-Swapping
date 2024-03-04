import sys
import serial
import time

import logging
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, qApp
from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, QThread, QProcess, QTimer, pyqtSignal, pyqtSlot, QSize


#%%                   DEFINITION OF WORKER CLASS FOR READING RFID CARD IDS

    

#%%

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup()
        return None
    
    def setup(self):
        self.serial_setup()
        self.setWindowTitle("My App")
        self.serial_setup()
        return None
    
    def closeEvent(self, event):
        self.ser.close()
        print('close event fired')
        event.accept()
        return None
    
    def serial_setup(self):
        try:
            self.ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            print("SERIAL LAUNCH SUCCESFUL")
        except:
            print("FAILURE TO LAUNCH SERIAL")
            qApp.exit()
            
        return None

    

    