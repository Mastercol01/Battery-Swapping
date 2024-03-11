from enum import Enum
from GUI_windows.info_window import InfoWindow
from GUI_windows.lock_screen import LockScreenWindow
from GUI_windows.options_panel import OptionsPanelWindow
from GUI_windows.user_prompt_panel import UserPromptPanelWindow

from PyQt5.QtGui import (
    QFont,
    QPixmap,
    QIcon)

from PyQt5.QtCore import (
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
    QToolBar,
    QAction,
    QStyle,
    QStackedWidget)

class WINS(Enum):
    INFO_WINDOW = 0
    LOCK_SCREEN = 1
    OPTIONS_PANEL = 2
    USER_PROMPT_PANEL = 3



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.globalTimers_setup()
        self.windows_setup()

        return None
    
    def globalTimers_setup(self):
        self.currentGlobalTime = 0

        self.globalTimers = {
              250 : QTimer(),
            60000 : QTimer() 
        }
        for key in self.globalTimers.keys():
            self.globalTimers[key].setInterval(key)

        self.globalTimers[250].timeout.connect(self.updateGlobalTimerVars250)
        self.globalTimers[60000].timeout.connect(self.updateGlobalTimerVars60000)

        for key in self.globalTimers.keys():
            self.globalTimers[key].setInterval(key)
        return None
    def updateGlobalTimerVars250(self):
        self.currentGlobalTime += 0.25
        return None
    def updateGlobalTimerVars60000(self):
        self.windows[WINS.LOCK_SCREEN].dateClock.updateTime()
        self.windows[WINS.LOCK_SCREEN].dateClock.updateDate()
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

        self.stckdWidget.setCurrentIndex(WINS.OPTIONS_PANEL.value)

        self.setCentralWidget(self.stckdWidget)
        return None