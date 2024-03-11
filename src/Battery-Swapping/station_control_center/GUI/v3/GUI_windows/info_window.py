import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

class InfoWindow(QWidget):
    def __init__(self):
        super().__init__()

        logoPath = os.path.dirname(os.path.dirname(__file__))
        logoPath = os.path.join(logoPath, "Images_and_Icons/chargify_logo_blanco.png")

        self.mainLogo = QLabel()
        self.mainLogo.setPixmap(QPixmap(logoPath))
        self.mainLogo.setAlignment(Qt.AlignCenter)

        self.labelsQ = {
            0: QLabel("¿Quiénes somos?"),
            1: QLabel("¿Qué es este aparato?"),
            2: QLabel("¿Cómo puedo registrarme?")
        }

        self.labelsR = {
            0: QLabel("Chargify es un proyecto de la universidad EAFIT, enfocado a soluciones de movildiad sostenible."),
            1: QLabel("Esta es una estación de carga para el intercambio de baterías de motos híbridas."),
            2: QLabel("Usted puede registrase en jhondoe@gmail.com, revisaremos su solicitud y si es aceptada le daremos una tarjeta con la que pueda acceder.")
        }

        for i in range(3):
            self.labelsQ[i].setWordWrap(True)
            font = self.labelsQ[i].font()
            font.setPointSize(23)
            self.labelsQ[i].setFont(font)
            self.labelsQ[i].setAlignment(Qt.AlignCenter)

            self.labelsR[i].setWordWrap(True)
            font = self.labelsR[i].font()
            font.setPointSize(18)
            self.labelsR[i].setFont(font)
            self.labelsR[i].setAlignment(Qt.AlignCenter)

        self.mainLayoutV = QVBoxLayout()
        self.layoutsH = {i: QHBoxLayout() for i in range(3)}

        self.mainLayoutV.addWidget(self.mainLogo)
        for i in range(3):
            self.layoutsH[i].addWidget(self.labelsQ[i])
            self.layoutsH[i].addWidget(self.labelsR[i])
            self.mainLayoutV.addLayout(self.layoutsH[i])

        self.setLayout(self.mainLayoutV)

        return None





        




        