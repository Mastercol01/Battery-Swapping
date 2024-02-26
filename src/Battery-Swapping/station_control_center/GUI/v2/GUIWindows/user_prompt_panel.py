from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

class UserPromptPanelWindow(QWidget):
    def __init__(self):
        super().__init__()  


        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("Images_and_Icons/chargify_logo_blanco.png"))
        self.logo.setAlignment(Qt.AlignCenter)

        self.imgs = {}
        self.pixmaps = {}
        for i in range(2):
            self.imgs[i] = QLabel()
            self.imgs[i].setAlignment(Qt.AlignCenter)       

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.fontsize = 25

        self.layout_v = QVBoxLayout()
        self.layout_h = QHBoxLayout()

        self.layout_h.addWidget(self.imgs[0])
        self.layout_h.addWidget(self.label)
        self.layout_h.addWidget(self.imgs[1])
        self.container_widget = QWidget()
        self.container_widget.setLayout(self.layout_h)

        self.layout_v.addWidget(self.logo)
        self.layout_v.addWidget(self.container_widget)
        

        self.setLayout(self.layout_v)
        
        return None



    @property
    def text(self):
        return self.label_text

    @text.setter
    def text(self, text):
        self.label_text = text
        self.label.setText(self.label_text)
        return None

    @property
    def fontsize(self):
        return self.label_fontsize
    
    @fontsize.setter
    def fontsize(self, fontsize):
        self.label_fontsize = fontsize
        font = self.label.font()
        font.setPointSize(self.label_fontsize)
        self.label.setFont(font)
        return None
    
    def set_imgs(self, img_num, img_path):
        self.pixmaps[img_num] = QPixmap(img_path)
        self.imgs[img_num].setPixmap(self.pixmaps[img_num])
        return None
    
    def resize_imgs(self, img_num, new_h, new_v):
        self.pixmaps[img_num] = self.pixmaps[img_num].scaled(new_h, new_v)
        self.imgs[img_num].setPixmap(self.pixmaps[img_num])
        return None
    
    def set_imgs_equal(self):
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
    
    def clear_imgs(self, img_num = None):
        
        if img_num is None:
            self.imgs[0].clear()
            self.imgs[1].clear()
        else:
            try:
                self.imgs[img_num].clear()
            except KeyError:
                pass

        return None





    

