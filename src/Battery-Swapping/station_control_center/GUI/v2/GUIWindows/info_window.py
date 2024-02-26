from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

class InfoWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("Images_and_Icons/chargify_logo_blanco.png"))
        self.logo.setAlignment(Qt.AlignCenter)


        self.labels_Q = {0 : QLabel("¿Quiénes somos?"),
                         1 : QLabel("¿Qué es este aparato?"),
                         2 : QLabel("¿Cómo puedo registrarme?")}
        
        self.texts_R = {}
        self.labels_R = {i : QLabel() for i in self.labels_Q.keys()}

        self.texts_R[0] = "Chargify es un proyecto de la universidad EAFIT, enfocado a soluciones de movildiad sostenible."
        self.texts_R[1] = "Esta es una estación de carga para el intercambio de baterías de motos híbridas."
        self.texts_R[2] = "Usted puede registrase en jhondoe@gmail.com, revisaremos su solicitud y si es aceptada le daremos una tarjeta con la que pueda acceder."

       
        for i in self.labels_Q.keys():
            self.labels_Q[i].setWordWrap(True)
            font = self.labels_Q[i].font()
            font.setPointSize(23)
            self.labels_Q[i].setFont(font)
            self.labels_Q[i].setAlignment(Qt.AlignCenter)

        for i in self.labels_R.keys():
            self.labels_R[i].setText(self.texts_R[i])
            self.labels_R[i].setWordWrap(True)
            font = self.labels_R[i].font()
            font.setPointSize(18)
            self.labels_R[i].setFont(font)
            self.labels_R[i].setAlignment(Qt.AlignCenter)

  
        self.layout_v  = QVBoxLayout()
        self.layouts_h = {i : QHBoxLayout() for i in self.labels_Q.keys()}
        self.container_widgets_h = {i : QWidget() for i in self.labels_Q.keys()}

        for i in range(len(self.labels_Q)):
            self.layouts_h[i].addWidget(self.labels_Q[i])
            self.layouts_h[i].addWidget(self.labels_R[i])
            self.container_widgets_h[i].setLayout(self.layouts_h[i])

        self.layout_v.addWidget(self.logo)
        for i in range(len(self.labels_Q)):
            self.layout_v.addWidget(self.container_widgets_h[i])

        self.setLayout(self.layout_v)

        return None





        




        