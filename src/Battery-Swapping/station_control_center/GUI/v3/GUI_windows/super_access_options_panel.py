import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QToolButton
from BSS_control.CanUtils import MODULE_ADDRESS


class SuperAccessOptionsPanelWindow(QWidget):

    def __init__(self):
        super().__init__()    

        # Get the paths of all images
        imgsPath = os.path.dirname(os.path.dirname(__file__))
        imgsPath = os.path.join(imgsPath, "Images_and_Icons")
        logoPath = os.path.join(imgsPath, "chargify_logo_blanco.png")
        moduleSelectionBtnPath = os.path.join(imgsPath, "chip_icon.png")


        self.logo = QLabel()
        self.logo.setPixmap(QPixmap(logoPath))
        self.logo.setAlignment(Qt.AlignCenter)

        self.label = QLabel("SELECT A MODULE TO MONITOR ITS STATUS")
        font = self.label.font()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.btns = {MODULE_ADDRESS(i):QToolButton() for i in range(1,10)}

        for moduleAddress in self.btns.keys():
            self.btns[moduleAddress].setIcon(QIcon(moduleSelectionBtnPath))
            self.btns[moduleAddress].setIconSize(QSize(100, 100))
            self.btns[moduleAddress].setText(f"{moduleAddress}".replace("MODULE_ADDRESS.", ""))
            font = self.btns[moduleAddress].font()
            font.setPointSize(13)
            self.btns[moduleAddress].setFont(font)
            self.btns[moduleAddress].setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.btns[moduleAddress].setStyleSheet("border-radius: 10px; border: 1px solid black; padding: 10px;")

        
        self.mainLayout       = QVBoxLayout()
        self.subLayouts       = {i:QHBoxLayout() for i in range(3)}
        self.containerWidgets = {i:QWidget()     for i in range(3)}

        self.mainLayout.addWidget(self.logo)
        self.mainLayout.addWidget(self.label)

        for moduleAddress in self.btns.keys():
            if       moduleAddress.value <= 4: idx = 0
            elif 4 < moduleAddress.value <= 8: idx = 1
            else:                              idx = 2 
            self.subLayouts[idx].addWidget(self.btns[moduleAddress])

        for key in range(3):
            self.containerWidgets[key].setLayout(self.subLayouts[key])
            self.mainLayout.addWidget(self.containerWidgets[key])


        # Set widget layout
        self.setLayout(self.mainLayout)
        return None
    
    def clickedConnectBtn(self, btnModuleAddress, func):
        self.btns[btnModuleAddress].clicked.connect(func)
        return None


    