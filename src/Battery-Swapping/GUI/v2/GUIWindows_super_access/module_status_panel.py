import typing
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QToolButton, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, QLineEdit, QGroupBox


class LabeledReadOnlyLineEdit(QWidget):
    def __init__(self, label_text = None, label_fontsize = 15):
        super().__init__()

        self.label = QLabel()
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

        if label_text is not None:
            self.label_text = label_text

        label_fontsize = label_fontsize

        return None


    @property
    def label_text(self):
        return self.label_text_
    
    @label_text.setter
    def label_text(self, text):
        self.label_text_ = text
        self.label.setText(self.label_text_)
        return None
    

    @property
    def label_fontsize(self):
        return self.label_fontsize_
    
    @label_fontsize.setter
    def label_fontsize(self, fontsize):
        self.label_fontsize_ = fontsize
        font = self.label.font()
        font.setPointSize(self.label_fontsize_)
        self.label.setFont(font)
        return None


    @property
    def text(self):
        return self.line_edit_text
    
    @text.setter
    def text(self, text):
        self.line_edit_text = text
        self.label.setText(self.line_edit_text)
        return None
    

    @property
    def fontsize(self):
        return self.line_edit_fontsize
    
    @fontsize.setter
    def fontsize(self, fontsize):
        self.line_edit_fontsize = fontsize
        font = self.line_edit.font()
        font.setPointSize(self.label_fontsize_)
        self.line_edit.setFont(font)
        return None
    



class LabeledProgressBar(QWidget):
    def __init__(self, label_text = None, label_fontsize = 15):
        super().__init__()

        self.label = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setOrientation(Qt.Vertical)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress_bar)
        self.setLayout(self.layout)

        if label_text is not None:
            self.label_text = label_text
            
        label_fontsize = label_fontsize

        return None


    @property
    def label_text(self):
        return self.label_text_
    
    @label_text.setter
    def label_text(self, text):
        self.label_text_ = text
        self.label.setText(self.label_text_)
        return None
    

    @property
    def label_fontsize(self):
        return self.label_fontsize_
    
    @label_fontsize.setter
    def label_fontsize(self, fontsize):
        self.label_fontsize_ = fontsize
        font = self.label.font()
        font.setPointSize(self.label_fontsize_)
        self.label.setFont(font)
        return None
    

    @property
    def value(self):
        return self.progress_bar_value
    
    @value.setter
    def value(self, val):
        self.progress_bar_value = val
        self.progress_bar.setValue(self.progress_bar_value)
        return None





class BatteryGeneralStatus(QGroupBox):
    def __init__(self):
        super().__init__()

        self.title = "Battery General Status"

        self.labeled_progess_bar = LabeledProgressBar("SOC")
        self.labeled_read_only_line_edits =\
        {
            0 : LabeledReadOnlyLineEdit("Pack Voltage"),
            1 : LabeledReadOnlyLineEdit("Pack Current"),
            2 : LabeledReadOnlyLineEdit("Max. Temperature")
        }

        self.layout_h = QHBoxLayout()
        self.layout_v = QVBoxLayout()

        for key in range(len(self.labeled_read_only_line_edits)):
            self.layout_v.addWidget(self.labeled_read_only_line_edits[key])

        self.container_widget_v = QWidget()
        self.container_widget_v.setLayout(self.layout_v)

        self.layout_h.addWidget(self.labeled_progess_bar)
        self.layout_h.addWidget(self.container_widget_v)

        self.setLayout(self.layout_h)

        return None
        


        

        