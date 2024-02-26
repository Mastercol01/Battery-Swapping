from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QToolButton




class OptionsPanelWindow(QWidget):
    def __init__(self):
        super().__init__()    

        # Define layout and layout spacing.
        self.layout = QVBoxLayout()
        self.layout.setSpacing(25)

        # Define label, change text fontsize and center-align.
        self.label = QLabel("¿QUÉ DESEA HACER HOY CON SUS BATERÍAS?")
        font = self.label.font()
        font.setPointSize(30)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.img = QLabel()
        self.img.setPixmap(QPixmap("Images_and_Icons/chargify_logo_blanco"))
        self.img.setAlignment(Qt.AlignCenter)


        # Define buttons and change texts' fontsizes.
        self.btns_layout = QHBoxLayout()
        self.btns_layout.setSpacing(5)

        self.btns = {i:QToolButton() for i in range(3)}
        self.btns[0].setIcon(QIcon("Images_and_Icons/input.png"))
        self.btns[1].setIcon(QIcon("Images_and_Icons/output.png"))
        self.btns[2].setIcon(QIcon("Images_and_Icons/input_and_output.png"))

        for i, text in enumerate(["INGRESAR", "RETIRAR", "INGRESAR Y RETIRAR"]):
            self.btns[i].setIconSize(QSize(200, 100))
            self.btns[i].setText(text)
            font = self.btns[i].font()
            font.setPointSize(15)
            self.btns[i].setFont(font)
            self.btns[i].setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.btns[i].setStyleSheet("border-radius: 10px; border: 1px solid black; padding: 10px;")
        
            self.btns_layout.addWidget(self.btns[i])

        self.btns_container_widget = QWidget()
        self.btns_container_widget.setLayout(self.btns_layout)

        # Nest widgets within layouts.
        self.layout.addWidget(self.img)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btns_container_widget)


        # Set widget layout
        self.setLayout(self.layout)


    def clicked_connect_btns(self, btn_num, func):
        self.btns[btn_num].clicked.connect(func)
        return None