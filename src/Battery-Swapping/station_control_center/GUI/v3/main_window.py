import serial
import warnings
from enum import Enum
from functools import partial
from GUI_windows.info_window import InfoWindow
from GUI_windows.lock_screen import LockScreenWindow
from GUI_windows.options_panel import OptionsPanelWindow
from GUI_windows.user_prompt_panel import UserPromptPanelWindow

from PyQt5.QtGui import (
    QFont,
    QPixmap,
    QIcon)

from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    Qt, 
    QThreadPool, 
    QTimer, 
    QSize)

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget, 
    QLabel, 
    QPushButton,
    QHBoxLayout, 
    QVBoxLayout,
    QStackedLayout,
    QLayout,
    QSizePolicy,
    qApp,
    QToolBar,
    QAction,
    QStyle,
    QStackedWidget)

from User_database.user_database import (
    getUsers,
    updateUsers)

from BSS_control.thread_workers import (
    SerialReadWorker,
    RfidReadWorker)



class WINS(Enum):
    INFO_WINDOW = 0
    LOCK_SCREEN = 1
    OPTIONS_PANEL = 2
    USER_PROMPT_PANEL = 3


class MainWindowSignals(QObject):
    terminate_SerialReadWorker = pyqtSignal()
    terminate_RfidReadWorker   = pyqtSignal()
    

class MainWindow(QMainWindow):
    SIGNALS = MainWindowSignals()

    def __init__(self):
        super().__init__()
        self.setup()
        return None
    
    
# (1) ------ SET-UP RELATED FUNCS ------- (1)

    def setup(self):
        self.user = None
        self.attendingUser = False
        self.globalTimers_setup()
        self.windows_setup()
        self.toolbar_setup()
        self.threadWorkers_setup()
        return None
    

    def globalTimers_setup(self):
        self.currentGlobalTime = 0

        self.globalTimers = {
              250 : QTimer(),
            30000 : QTimer() 
        }
        for key in self.globalTimers.keys():
            self.globalTimers[key].setInterval(key)

        self.globalTimers[250].timeout.connect(self.updateGlobalTimerVars250)
        self.globalTimers[30000].timeout.connect(self.updateGlobalTimerVars30000)

        for key in self.globalTimers.keys():
            self.globalTimers[key].setInterval(key)
            self.globalTimers[key].start()
        return None

    def updateGlobalTimerVars250(self):
        self.currentGlobalTime += 250
        return None
    
    def updateGlobalTimerVars30000(self):
        self.windows[WINS.LOCK_SCREEN].dateClock.updateTime()
        self.windows[WINS.LOCK_SCREEN].dateClock.updateDate()

        if self.currentWindow == WINS.INFO_WINDOW:
            if self.currentGlobalTime - self.timeInsideAboutUsSection > 30000:
                self.show_window[WINS.LOCK_SCREEN]()
        return None


    def windows_setup(self):
        self.stckdWidget = QStackedWidget()

        self.windows = {
            WINS.INFO_WINDOW       : InfoWindow(),
            WINS.LOCK_SCREEN       : LockScreenWindow(),
            WINS.OPTIONS_PANEL     : OptionsPanelWindow(),
            WINS.USER_PROMPT_PANEL : UserPromptPanelWindow()
        }
        
        for key in self.windows.keys():
            self.stckdWidget.insertWidget(key.value, self.windows[key])

        self.show_window = {key:partial(self.stckdWidget.setCurrentIndex, key.value) for key in WINS}

        self.show_window[WINS.LOCK_SCREEN]()
        self.setCentralWidget(self.stckdWidget)
        return None
    
    @property
    def currentWindow(self):
        return WINS(self.stckdWidget.currentIndex())
    

    def toolbar_setup(self):
        toolbar = QToolBar("toolbar")
        toolbar.setIconSize(QSize(25, 25))
        self.addToolBar(toolbar)
        icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        button_action = QAction(QIcon(icon), "Sobre Nosotros", self)
        button_action.triggered.connect(self.showAboutUsSection)
        toolbar.addAction(button_action)
        toolbar.addSeparator()
        return None
    
    def showAboutUsSection(self):
        if self.currentWindow == WINS.LOCK_SCREEN:
            self.show_window[WINS.INFO_WINDOW]()
            self.timeInsideAboutUsSection = float(self.currentGlobalTime)

        elif self.currentWindow == WINS.INFO_WINDOW:
            self.show_window[WINS.LOCK_SCREEN]()
        return None
    

    def threadWorkers_setup(self):
        self.threadpool = QThreadPool()
        #self.serialReadWorker_setup()
        self.rfidReadWorker_setup()
        return None
    
    def serialReadWorker_setup(self):
        try:
            self.ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
            self.ser.reset_input_buffer()
            print("SERIAL LAUNCH SUCCESFUL")
        except:
            print("FAILURE TO LAUNCH SERIAL")
            self.close()

        self.serialReadWorker = SerialReadWorker(self.ser)
        self.SIGNALS.terminate_SerialReadWorker.connect(self.serialReadWorker.endRun)

        self.threadpool.start(self.serialReadWorker)
        return None
    
    def rfidReadWorker_setup(self):
        self.rfidReadWorker = RfidReadWorker()
        self.SIGNALS.terminate_RfidReadWorker.connect(self.rfidReadWorker.endRun)
        self.rfidReadWorker.signals.rfidReadResults.connect(self.LockScreenWindow_initWorkFlow)
        self.threadpool.start(self.rfidReadWorker)
        return None
    


# (1) ------------------------------------------------------ (1)
    
    def LockScreenWindow_initWorkFlow(self, cardId):
        if self.attendingUser:
            return None
        
        elif self.currentWindow not in [WINS.LOCK_SCREEN, WINS.INFO_WINDOW]:
            return None
        
        elif self.currentWindow == WINS.INFO_WINDOW:
            self.show_window[WINS.LOCK_SCREEN]()

        self.attendingUser = True

        if cardId < 0:
            errorMsg = "ERROR AL LEER TARJETA! INTENTE DE NUEVO"
            self.windows[WINS.LOCK_SCREEN].text = errorMsg
            QTimer.singleShot(2000, self.LockScreenWindow_reset)
            return None
        
        print(cardId)
        users = getUsers({"cardId":cardId})

        if not users:
            noUsersFoundMsg = "USUARIO NO REGISTRADO. REGÍSTRESE PARA USAR LA ESTACIÓN"
            self.windows[WINS.LOCK_SCREEN].text = noUsersFoundMsg
            QTimer.singleShot(2000, self.LockScreenWindow_reset)
            return None
        
        elif len(users) > 1:
            manyUsersFoundMsg = f"ERROR: {len(users)} users were found matching the current cardId" 
            manyUsersFoundMsg = f"{manyUsersFoundMsg}. Closing app. Users' data might be compromised."
            raise Exception(manyUsersFoundMsg)
        
        self.user = users[0]
        userName = f"{self.user['firstName']} {self.user['lastName']}"
        userFoundMsg = f"BIENVENID@ {userName}"
        self.windows[WINS.LOCK_SCREEN].text = userFoundMsg      
        QTimer.singleShot(3000, self.LockScreenWindow_reset)
        return None
    

    def LockScreenWindow_reset(self, reloadWindow=False):
        resetMsg = "POR FAVOR ACERQUE SU TARJETA AL LECTOR PARA INICIAR"
        self.windows[WINS.LOCK_SCREEN].text = resetMsg
        if reloadWindow:
            self.show_window[WINS.LOCK_SCREEN]()
        self.attendingUser = False
        return None
    

    def closeEvent(self, event):
        self.SIGNALS.terminate_RfidReadWorker.emit()
        self.SIGNALS.terminate_SerialReadWorker.emit()
        self.ser.close()
        print('CLOSING APP')
        QTimer.singleShot(1000, event.accept)
        event.accept()
        return None
    
 
        


    
 