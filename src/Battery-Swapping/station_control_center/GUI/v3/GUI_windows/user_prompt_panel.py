import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout


class UserPromptPanelWindow(QWidget):
    def __init__(self):
        super().__init__()  

        logoPath = os.path.dirname(os.path.dirname(__file__))
        logoPath = os.path.join(logoPath, "Images_and_Icons/chargify_logo_blanco.png")

        self.logo = QLabel()
        self.logo.setPixmap(QPixmap(logoPath))
        self.logo.setAlignment(Qt.AlignCenter)

        self.imgs = {}
        self.pixmaps = {}
        for i in range(2):
            self.imgs[i] = QLabel()
            self.imgs[i].setAlignment(Qt.AlignCenter)       

        self.mainLabel = QLabel()
        self.mainLabel.setWordWrap(True)
        self.mainLabel.setAlignment(Qt.AlignCenter)
        self.fontSize = 25

        self.mainLayoutV = QVBoxLayout()
        self.mainLayoutH = QHBoxLayout()

        self.mainLayoutH.addWidget(self.imgs[0])
        self.mainLayoutH.addWidget(self.mainLabel)
        self.mainLayoutH.addWidget(self.imgs[1])
        self.containerWidget = QWidget()
        self.containerWidget.setLayout(self.mainLayoutH)

        self.mainLayoutV.addWidget(self.logo)
        self.mainLayoutV.addWidget(self.containerWidget)
        

        self.setLayout(self.mainLayoutV)
        
        return None

    @property
    def text(self):
        return self.labelText

    @text.setter
    def text(self, text):
        self.labelText = text
        self.mainLabel.setText(self.labelText)
        return None
    
    def setText(self, text):
        self.text = text
        return None

    @property
    def fontSize(self):
        return self.labelFontSize
    
    @fontSize.setter
    def fontSize(self, fontsize):
        self.labelFontSize = fontsize
        font = self.mainLabel.font()
        font.setPointSize(self.labelFontSize)
        self.mainLabel.setFont(font)
        return None
    
    def setImgs(self, imgNum, imgPath):
        self.pixmaps[imgNum] = QPixmap(imgPath)
        self.imgs[imgNum].setPixmap(self.pixmaps[imgNum])
        return None
    
    def resizeImgs(self, imgNum, boxPixelWidth, boxPixelHeight):
        self.pixmaps[imgNum] = self.pixmaps[imgNum].scaled(boxPixelWidth, boxPixelHeight, Qt.AspectRatioMode.KeepAspectRatio)
        self.imgs[imgNum].setPixmap(self.pixmaps[imgNum])
        return None
    
    def setImgsEqual(self):
        try:
            self.pixmaps[1] = self.pixmaps[0]
            self.imgs[1].setPixmap(self.pixmaps[1])
        except KeyError:
            try:
                self.pixmaps[0] = self.pixmaps[1]
                self.imgs[0].setPixmap(self.pixmaps[0])
            except KeyError:
                pass
        return None
    
    def clearImgs(self, imgNum = None):
        
        if imgNum is None:
            self.imgs[0].clear()
            self.imgs[1].clear()
        else:
            try:
                self.imgs[imgNum].clear()
            except KeyError:
                pass

        return None
    
    def clearAll(self):
        self.clearImgs(None)
        self.text = ""
        return None






    

