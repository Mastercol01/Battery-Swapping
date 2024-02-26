from datetime import datetime, date
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

MONTHS_TO_MESES = {"January":"Enero", "February":"Febrero",
                   "March":"Marzo", "April":"Abril",
                   "May":"Mayo", "June":"Junio", 
                   "July":"Julio", "August":"Agosto", 
                   "September":"Septiembre", "October":"Octubre",
                   "November":"Noviembre", "December":"Diciembre"}



class DateClockWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.date_label = QLabel()
        self.time_label = QLabel()
        
        font = self.date_label.font()
        font.setPointSize(10)
        self.date_label.setFont(font)
        
        font = self.time_label.font()
        font.setPointSize(45)
        self.time_label.setFont(font)

        self.date_label.setAlignment(Qt.AlignCenter)
        self.time_label.setAlignment(Qt.AlignCenter)

        self.update_date()
        self.update_time()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.date_label)
        self.layout.addWidget(self.time_label)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        
        return None
    

    def update_date(self):
        self.current_date = date.today().strftime("%B %d, %Y")
        month = self.current_date.split(" ")[0]
        self.current_date = self.current_date.replace(month, MONTHS_TO_MESES[month])
        self.date_label.setText(self.current_date)
        return None
    
    def update_time(self):
        self.current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S").split(" ")[-1]
        self.time_label.setText(self.current_time[:-3])
        return None
    





class LockScreenWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.dateclock = DateClockWidget()
        

        self.img = QLabel()
        pixmap = QPixmap("Images_and_Icons/chargify_logo_blanco.png")
        #pixmap.scaled(1000, 1000)
        self.img.setPixmap(pixmap)
        self.img.setAlignment(Qt.AlignCenter)


        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.text = "POR FAVOR ACERQUE SU TARJETA AL LECTOR PARA INICIAR"
        self.fontsize = 25


        self.layout = QVBoxLayout()
        self.layout.addWidget(self.dateclock)
        self.layout.addWidget(self.img)
        self.layout.addWidget(self.label)
      

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