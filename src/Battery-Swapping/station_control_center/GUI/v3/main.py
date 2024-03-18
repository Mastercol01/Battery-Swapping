import sys
from main_window import MainWindow
#from main_window_test import MainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication



app = QApplication(sys.argv)
app.setStyle('Fusion')

palette = QPalette()
palette.setColor(QPalette.Window, Qt.white)
app.setPalette(palette)

window = MainWindow()
window.showMaximized()

app.exec()