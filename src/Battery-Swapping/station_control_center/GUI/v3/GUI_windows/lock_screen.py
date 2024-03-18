import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from datetime import datetime, date
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

        self.dateLabel = QLabel()
        self.timeLabel = QLabel()

        font = self.dateLabel.font()
        font.setPointSize(25)
        self.dateLabel.setFont(font)

        font = self.timeLabel.font()
        font.setPointSize(60)
        self.timeLabel.setFont(font)

        self.dateLabel.setAlignment(Qt.AlignCenter)
        self.timeLabel.setAlignment(Qt.AlignCenter)

        self.updateDate()
        self.updateTime()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.dateLabel)
        self.layout.addWidget(self.timeLabel)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)

        return None

    def updateDate(self):
        self.currentDate = datetime.today().strftime("%B %d, %Y")
        month = self.currentDate.split(" ")[0]
        self.currentDate = self.currentDate.replace(month, MONTHS_TO_MESES[month])
        self.dateLabel.setText(self.currentDate)
        return None

    def updateTime(self):
        self.currentTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S").split(" ")[-1]
        self.timeLabel.setText(self.currentTime[:-3])
        return None



class LockScreenWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.dateClock = DateClockWidget()

        logoPath = os.path.dirname(os.path.dirname(__file__))
        logoPath = os.path.join(logoPath, "Images_and_Icons/chargify_logo_blanco.png")

        self.logo = QLabel()
        pixmap = QPixmap(logoPath)
        #pixmap.scaled(1000, 1000)
        self.logo.setPixmap(pixmap)
        self.logo.setAlignment(Qt.AlignCenter)

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.text = "POR FAVOR ACERQUE SU TARJETA AL LECTOR PARA INICIAR"
        self.fontSize = 30

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.dateClock)
        self.layout.addWidget(self.logo)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        return None

    @property
    def text(self):
        return self.labelText

    @text.setter
    def text(self, text):
        self.labelText = text
        self.label.setText(self.labelText)
        return None

    @property
    def fontSize(self):
        return self.labelFontSize

    @fontSize.setter
    def fontSize(self, fontSize):
        self.labelFontSize = fontSize
        font = self.label.font()
        font.setPointSize(self.labelFontSize)
        self.label.setFont(font)
        return None


