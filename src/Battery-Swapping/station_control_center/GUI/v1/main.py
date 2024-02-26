from users import User
from PyQt5.QtWidgets import QApplication
from window import MainWindow
import sys




app = QApplication(sys.argv)
app.setStyle('Fusion')

window = MainWindow()
window.show()

app.exec()