#%%                          IMPORTATION OF MODULES     
import random
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522



from functools import partial
from collections import OrderedDict
from GUI_windows.info_window import InfoWindow
from GUI_windows.lock_screen import LockScreenWindow
from GUI_windows.options_panel import OptionsPanelWindow
from GUI_windows.user_prompt_panel import UserPromptPanelWindow
from GUIWindows_super_access.module_status_select_panel import ModuleStatusSelectPanel
from GUIWindows_super_access.module_status_panel import BatteryGeneralStatus

from users import User, load_database, save_database


from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, QProcess, QTimer, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, QLayout, QSizePolicy, QToolBar, QAction, QStyle, QTabWidget

#%%                        LOADING OF USER DATABASE

DATABASE_PATH = r"/home/joveninvestigador/Desktop/GUI/v2/database.pkl"
database = load_database(DATABASE_PATH)

#%%                      DEFINITION OF WORKERSIGNALS CLASS

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)


#%%                   DEFINITION OF WORKER CLASS FOR READING RFID CARD IDS
card_manager = SimpleMFRC522()

class WorkerReadCardId(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
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
    


#%%


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setup()
        self.main()

        return None
    
    def setup(self):
        self.toolbar_setup()
        self.window_setup()
        self.timer_setup()
        self.threadpool = QThreadPool()
        return None
    
    def main(self):
        self.set_window_from_name("Lock Screen")
        self.read_card_id()
        return None
    
    def reset(self):
        self.main()
        return None
    
    
    def toolbar_setup(self):
        toolbar = QToolBar("toolbar")
        toolbar.setIconSize(QSize(25, 25))
        self.addToolBar(toolbar)

        icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        button_action = QAction(QIcon(icon), "Sobre Nosotros", self)
        button_action.triggered.connect(self.show_info_window)
        toolbar.addAction(button_action)
        toolbar.addSeparator()
        return None

    def window_setup(self):

        #self.windows = OrderedDict()
        self.windows = {}
        self.windows["Lock Screen"]                = LockScreenWindow()
        self.windows["Options Panel"]              = OptionsPanelWindow()
        self.windows["User Prompt Panel"]          = UserPromptPanelWindow()
        self.windows["Info"]                       = InfoWindow()
        self.windows["Tabs"]                       = QTabWidget()
        self.windows["Module Status Select Panel"] = ModuleStatusSelectPanel()
        self.windows["Module Status"]              = BatteryGeneralStatus()

        self.windows["Tabs"].addTab(self.windows["Module Status Select Panel"], "Module Status")
        



        
        self.WINDOW_IDXS_FROM_NAMES = {key:i for i,key in enumerate(self.windows)}
        self.WINDOW_NAMES_FROM_IDXS = {i:key for i,key in enumerate(self.windows)}
        self.GOTO_FUNCS = {key:partial(self.set_window_from_name, key) for key in self.windows.keys()}

        self.windows["Options Panel"].clicked_connect_btns(0, self.battery_entry)
        self.windows["Options Panel"].clicked_connect_btns(1, self.battery_withdrawal)
        self.windows["Options Panel"].clicked_connect_btns(2, self.battery_entry_and_withdrawal)

        

        for i in range(1, 9):
            self.windows["Module Status Select Panel"].clicked_connect_btns(i, self.GOTO_FUNCS["Module Status"])

    
        # ------ STACKED WINDOW SETUP ------
        self.widget_stckd = QWidget()
        self.layout_stckd = QStackedLayout()

        for key in self.windows.keys():
            self.layout_stckd.addWidget(self.windows[key])

        self.widget_stckd.setLayout(self.layout_stckd)
        self.setCentralWidget(self.widget_stckd)
    
        return None
    
    def timer_setup(self):
        self.update_time_timer = QTimer()
        self.update_date_timer = QTimer()

        self.update_time_timer.setInterval(6*1000)
        self.update_date_timer.setInterval(6*60*1000)

        self.update_time_timer.timeout.connect(self.windows["Lock Screen"].dateclock.update_time)
        self.update_date_timer.timeout.connect(self.windows["Lock Screen"].dateclock.update_date)

        self.update_time_timer.start()
        self.update_date_timer.start()
        
        return None
    

    def set_window_from_index(self, window_index):
        self.window_index = window_index
        self.window_name  = self.WINDOW_NAMES_FROM_IDXS[self.window_index] 
        self.layout_stckd.setCurrentIndex(self.window_index)
        return None
    
    def set_window_from_name(self, window_name):
        window_index = self.WINDOW_IDXS_FROM_NAMES[window_name]
        self.set_window_from_index(window_index)
        return None
    
    
    def goto(self, window_name, delay_ms = 0):
        if delay_ms == 0:
            self.GOTO_FUNCS[window_name]()
        else:
            QTimer.singleShot(delay_ms, self.GOTO_FUNCS[window_name])
        return None



    def read_card_id(self):
        worker = WorkerReadCardId()
        worker.signals.error.connect(self.read_card_id_error)
        worker.signals.result.connect(self.read_card_id_output)
        worker.signals.finished.connect(self.read_card_id_finished)    
        self.threadpool.start(worker)
        return None
    
    def read_card_id_output(self, res):
        self.card_id = res["card_id"]
        return None
    
    def read_card_id_error(self, e):
        print(e)
        return None
    
    def read_card_id_finished(self):
        if self.card_id is None:
            self.read_card_id()
        else:
            self.user = database.get(self.card_id)
            self.card_id_was_read()
        return None
    
    def card_id_was_read(self):
        self.goto("User Prompt Panel")

        if self.user is not None:
            self.windows["User Prompt Panel"].clear_imgs()
            self.windows["User Prompt Panel"].text = f"BIENVENID@\n {self.user.full_name}"

            if not self.user.super_access:
                self.goto("Options Panel", 3000)
            else:
                self.goto("Module Status Select Panel", 3000)
        else: 
            self.windows["User Prompt Panel"].set_imgs(0,"Images_and_Icons/error_404.png")
            self.windows["User Prompt Panel"].resize_imgs(0,250,250)
            self.windows["User Prompt Panel"].set_imgs_equal()
            self.windows["User Prompt Panel"].text = f"USUARIO NO ENCONTRADO"
            QTimer.singleShot(3000, self.reset)
        return None    
    


    def battery_entry(self):
        self.goto("User Prompt Panel")
        self.windows["User Prompt Panel"].text = "aefaefaefaefaf"
        return None
    
    def battery_withdrawal(self):
        user_current_num_batts = self.user.history.\
        loc[self.user.history.shape[0] - 1, "No. Batteries"]
        user_max_num_batts = self.user.max_num_batts

        if  user_current_num_batts <= user_max_num_batts:
            pass

        else:
            self.goto("User Prompt Panel")
            text = f"¡LO SENTIMOS!\n"
            text = f"{text} Has alcanzado el número máximo de baterías en préstamo. Devuelve las"
            text = f"{text} que ya tienes para poder recibir nuevas."
            self.windows["User Prompt Panel"].text = text

            self.windows["User Prompt Panel"].set_imgs(0,"Images_and_Icons/attention_symbol.png")
            self.windows["User Prompt Panel"].resize_imgs(0,250,250)
            self.windows["User Prompt Panel"].set_imgs_equal()

            QTimer.singleShot(8000, self.reset)

        return None
    
    def battery_entry_and_withdrawal(self):
        pass
        return None
    
 
    
    def show_info_window(self):
        if self.window_name == "Lock Screen":
            self.goto("Info")
        elif self.window_name == "Info":
            self.goto("Lock Screen")
        return None


    def closeEvent(self, event):
        save_database(database, DATABASE_PATH)
        print('close event fired')

        event.accept()