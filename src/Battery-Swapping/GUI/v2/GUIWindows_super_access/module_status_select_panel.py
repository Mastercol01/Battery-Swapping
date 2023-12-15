from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QToolButton, QLabel, QVBoxLayout, QHBoxLayout


class ModuleStatusSelectPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("Images_and_Icons/chargify_logo_blanco.png"))
        self.logo.setAlignment(Qt.AlignCenter)

        self.label = QLabel("SELECCIONE EL MÓDULO DE LA ESTACIÓN PARA CONOCER SU ESTADO")
        font = self.label.font()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)
    

        self.btns = {i:QToolButton() for i in range(1,9)}

        for i in self.btns.keys():
            self.btns[i].setIcon(QIcon("Images_and_Icons/chip_icon.png"))
            self.btns[i].setIconSize(QSize(150, 150))
            self.btns[i].setText(f"Módulo {i}")
            font = self.btns[i].font()
            font.setPointSize(15)
            self.btns[i].setFont(font)
            self.btns[i].setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.btns[i].setStyleSheet("border-radius: 10px; border: 1px solid black; padding: 10px;")


        self.layout_v  = QVBoxLayout()
        self.layouts_h = {i:QHBoxLayout() for i in range(2)}
        self.container_widgets_h = {i:QWidget() for i in range(2)}

        for i in range(1, 5):
            self.layouts_h[0].addWidget(self.btns[i])
            self.layouts_h[1].addWidget(self.btns[4+i])

        self.container_widgets_h[0].setLayout(self.layouts_h[0])
        self.container_widgets_h[1].setLayout(self.layouts_h[1])

        self.layout_v.addWidget(self.logo)
        self.layout_v.addWidget(self.label)
        self.layout_v.addWidget(self.container_widgets_h[0])
        self.layout_v.addWidget(self.container_widgets_h[1])

        self.setLayout(self.layout_v)

        return None
    

    def clicked_connect_btns(self, btn_num, func):
        self.btns[btn_num].clicked.connect(func)
        return None
        

        




        





        
    