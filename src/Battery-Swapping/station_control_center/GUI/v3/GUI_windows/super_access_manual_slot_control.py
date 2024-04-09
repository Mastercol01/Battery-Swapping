import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from BSS_control.CanUtils import MODULE_ADDRESS
from BSS_control.eight_channel_relay import CHANNEL_NAME


class SuperAccessManualSlotControl(QWidget):

    def __init__(self, ControlCenter_obj):
        super().__init__()   

        self.slotAddress = None 
        self.ControlCenter_obj = ControlCenter_obj

        self.mainLayout = QVBoxLayout()

        self.title = QLabel(f"MANUAL CONTROL FOR: {self.slotAddress}")
        font = self.title.font()
        font.setPointSize(60)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignCenter)

        self.releaseBtn = QPushButton("RELEASE")
        font = self.releaseBtn.font()
        font.setPointSize(50)
        self.releaseBtn.setFont(font)

        self.withholdBtn = QPushButton("WITHHOLD")
        font = self.withholdBtn.font()
        font.setPointSize(50)
        self.withholdBtn.setFont(font)
        
        self.releaseBtn.clicked.connect(self.releaseBtnClicked)
        self.withholdBtn.clicked.connect(self.withholdBtnClicked)

        self.mainLayout.addWidget(self.title)
        self.mainLayout.addWidget(self.releaseBtn)
        self.mainLayout.addWidget(self.withholdBtn)
        self.setLayout(self.mainLayout)



    def update(self, slotAddress):
        self.slotAddress = slotAddress
        self.title.setText(f"MANUAL CONTROL FOR: {str(slotAddress).replace('MODULE_ADDRESS.', '')}")
        return None
    
    def clear(self):
        self.slotAddress = None
        self.title.setText(f"MANUAL CONTROL FOR: {self.slotAddress}")
        return None

    def releaseBtnClicked(self):
        if self.slotAddress in self.ControlCenter_obj.SLOT_ADDRESSES:
            self.ControlCenter_obj.setSlotSolenoidsStates(self.slotAddress, [0,1,1])
            self.ControlCenter_obj.setRelayChannelState(CHANNEL_NAME(self.slotAddress.value-1), 0)
            self.ControlCenter_obj.setSlotSolenoidsStates(self.slotAddress, [0,0,0], delay = 10000)
        return None
    
    def withholdBtnClicked(self):
        if self.slotAddress in self.ControlCenter_obj.SLOT_ADDRESSES:
            self.ControlCenter_obj.setSlotSolenoidsStates(self.slotAddress, [1,0,0])
        return None