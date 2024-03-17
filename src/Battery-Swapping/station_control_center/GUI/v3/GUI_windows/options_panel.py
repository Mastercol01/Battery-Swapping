import os
from enum import Enum
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QToolButton




class OptionsPanelWindow(QWidget):


    def __init__(self):
        super().__init__()    

        # Get the paths of all images
        imgsPath = os.path.dirname(os.path.dirname(__file__))
        imgsPath = os.path.join(imgsPath, "Images_and_Icons")
        logoPath = os.path.join(imgsPath, "chargify_logo_blanco.png")
        inputBtnPath = os.path.join(imgsPath, "input.png")
        outputBtnPath = os.path.join(imgsPath, "output.png")
        inputAndOutputPath = os.path.join(imgsPath, "input_and_output.png")


        # Define layout and layout spacing.
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(25)

        # Define label, change text fontsize and center-align.
        self.mainLabel = QLabel("¿QUÉ DESEA HACER HOY CON SUS BATERÍAS?")
        font = self.mainLabel.font()
        font.setPointSize(30)
        self.mainLabel.setFont(font)
        self.mainLabel.setAlignment(Qt.AlignCenter)

        #Define logo
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap(logoPath))
        self.logo.setAlignment(Qt.AlignCenter)

        # Define buttons and change texts' fontsizes.
        self.btnsLayout = QHBoxLayout()
        self.btnsLayout.setSpacing(5)
        self.btns = {i: QToolButton() for i in range(3)}
        self.btns[0].setIcon(QIcon(inputBtnPath))
        self.btns[1].setIcon(QIcon(outputBtnPath))
        self.btns[2].setIcon(QIcon(inputAndOutputPath))

        for i, text in enumerate(["INGRESAR", "RETIRAR", "INGRESAR Y RETIRAR"]):
            self.btns[i].setIconSize(QSize(200, 100))
            self.btns[i].setText(text)
            font = self.btns[i].font()
            font.setPointSize(15)
            self.btns[i].setFont(font)
            self.btns[i].setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.btns[i].setStyleSheet("border-radius: 10px; border: 1px solid black; padding: 10px;")
        
            self.btnsLayout.addWidget(self.btns[i])

        self.btnsContainerWidget = QWidget()
        self.btnsContainerWidget.setLayout(self.btnsLayout)

        # Nest widgets within layouts.
        self.mainLayout.addWidget(self.logo)
        self.mainLayout.addWidget(self.mainLabel)
        self.mainLayout.addWidget(self.btnsContainerWidget)

        # Set widget layout
        self.setLayout(self.mainLayout)

    def clickedConnectBtn(self, btnNum, func):
        self.btns[btnNum].clicked.connect(func)
        return None


