#%%                          IMPORTATION OF MODULES     
import pickle
import random
from users import User
from PyQt5.QtGui import QFont
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, QProcess, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, QLayout, QSizePolicy

#%%                        LOADING OF USER DATABASE

database_path = r"/home/joveninvestigador/Desktop/GUI/v1/database.pkl"
with open(database_path, 'rb') as inp:
    database = pickle.load(inp)

#%%                      DEFINITION OF WORKERSIGNALS CLASS

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)


#%%                   DEFINITION OF WORKER CLASS FOR READING RFID CARD IDS
card_manager = SimpleMFRC522()

def dummy_card_read_id():
    c = 0
    while c < 1e+7:
        c+=1
    card_id = random.choice([1111, 2222, 3333])
    card_id = random.choice([2222])
    return card_id

 

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

class FrontWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.label_text = "POR FAVOR ACERQUE SU TARJETA AL LECTOR."
        self.label_fontsize = 30

        # Define layout. 
        self.layout = QHBoxLayout()

        # Define front label.
        self.label = QLabel()
        self.label.setWordWrap(True)

        # Set label text and fontsize.
        self.text = self.label_text
        self.fontsize = self.label_fontsize

        # Center-align label.
        self.label.setAlignment(Qt.AlignCenter)

        # Nest label within layout.
        self.layout.addWidget(self.label)

        # Set widget layout.
        self.setLayout(self.layout)

        return None

    @property
    def text(self):
        return self.label_text

    @text.setter
    def text(self, text):
        self.label_text = text
        self.label.setText(self.label_text)
        return None

    @property
    def fontsize(self):
        return self.label_fontsize
    
    @fontsize.setter
    def fontsize(self, fontsize):
        self.label_fontsize = fontsize
        font = self.label.font()
        font.setPointSize(self.label_fontsize)
        self.label.setFont(font)
        return None
    


class OptionsPanel(QWidget):
    def __init__(self):
        super().__init__()    

        # Define layout and layout spacing.
        self.layout = QVBoxLayout()
        self.layout.setSpacing(25)

        # Define label, change text fontsize and center-align.
        self.label = QLabel("¿QUÉ DESEA HACER HOY?")
        font = self.label.font()
        font.setPointSize(30)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        # Define buttons and change texts' fontsizes.
        self.btns = {}
        for i, text in enumerate(["SOLO INGRESAR", "SOLO RETIRAR", "INGRESAR Y RETIRAR"]):
            self.btns[i] = QPushButton(text)
            font = self.btns[i].font()
            font.setPointSize(30)
            self.btns[i].setFont(font)

        # Nest widgets within layouts.
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btns[0])
        self.layout.addWidget(self.btns[1])
        self.layout.addWidget(self.btns[2])

        # Set widget layout
        self.setLayout(self.layout)


    def clicked_connect_btns(self, btn_num, func):
        self.btns[btn_num].clicked.connect(func)
        return None


    


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.main()

        return None
    

    def main(self):

        self.timer_setup()
        
        self.threadpool = QThreadPool()

        self.window_setup()

        self.read_card_id()

        return None
    
    def timer_setup(self):
        """
        self.counter = 0
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.count)
        self.timer.start()
        """
        pass
        return None

    
    def window_setup(self):

        self.windows = {}
        self.windows[0] = FrontWindow()
        self.windows[1] = OptionsPanel()

        self.windows[1].clicked_connect_btns(0, self.battery_entry)
        self.windows[1].clicked_connect_btns(1, self.battery_withdrawal)
        self.windows[1].clicked_connect_btns(2, self.battery_entry_and_withdrawal)


        # ------ STACKED WINDOW SETUP ------
        self.widget_stckd = QWidget()
        self.layout_stckd = QStackedLayout()
        self.layout_stckd.addWidget(self.windows[0])
        self.layout_stckd.addWidget(self.windows[1])
        self.widget_stckd.setLayout(self.layout_stckd)

        self.setCentralWidget(self.widget_stckd)
        
        self.window_index = 0

        return None
    

    @property
    def window_index(self):
        return self.window_index_
    
    @window_index.setter
    def window_index(self, index):
        self.window_index_ = index
        self.layout_stckd.setCurrentIndex(self.window_index_)
        return None
    
    def go_to_options_panel(self):
        self.window_index = 1
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
        if self.user is not None:
            self.windows[0].text = f"BIENVENID@ {self.user.full_name}"
            QTimer.singleShot(3000, self.go_to_options_panel)
        else:
            self.windows[0].text = f"USUARIO NO ENCONTRADO"
            QTimer.singleShot(3000, self.reset)
        return None    
    


    
    def battery_entry(self):
        self.window_index = 0
        self.windows[0].text = "aefaefaefaefaf"
        return None
    
    def battery_withdrawal(self):
        user_current_num_batts = self.user.history.\
        loc[self.user.history.shape[0] - 1, "No. Batteries"]
        user_max_num_batts = self.user.max_num_batts


        if  user_current_num_batts <= user_max_num_batts:
            pass

        else:
            self.window_index = 0
            text = f"Señor usuario, Ud. ha alcanzado el número máximo de baterías ({user_max_num_batts}) en préstamo simultáneo."
            text = f"{text} No podemos facilitarle nuevas baterías hasta que devuelva de las que ya tiene.\n"
            text = f"{text} ¡GRACIAS POR SU COMPRENSIÓN!"
            self.windows[0].text = text
            QTimer.singleShot(7000, self.reset)

        return None
    
    def battery_entry_and_withdrawal(self):
        pass
        return None
    
    def reset(self):
        self.main()
        return None