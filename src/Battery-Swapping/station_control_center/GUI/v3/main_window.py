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

class WINDOWS(Enum):
    INFO_WINDOW = 0
    LOCK_SCREEN = 1
    OPTIONS_PANEL = 2
    USER_PROMPT_PANEL = 3



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        return None
    
    def globalTimer_setup(self):
        self.currentGlobalTime = 0
        self.globalTimer = QTimer()
        self.globalTimer.setInterval(250)
        self.globalTimer.timeout.connect(self.updateTimeDependentVars)
        self.globalTimer.start()
        return None
    def updateTimeDependentVars(self):
        self.currentGlobalTime += 0.25
        return None

    def windows_setup(self):
        self.windows = QStackedWidget()


        return None