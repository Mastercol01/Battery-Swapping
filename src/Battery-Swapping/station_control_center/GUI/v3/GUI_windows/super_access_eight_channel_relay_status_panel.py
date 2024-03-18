from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout


class SuperAccessEightChannelRelayStatusPanel(QWidget):
    def __init__(self, ControlCenter_obj):
        super().__init__()   

        self.ControlCenter_obj = ControlCenter_obj

        self.mainLayout = QVBoxLayout()
        self.subLayout  = QGridLayout()

        self.label = QLabel("STATES OF: ")
        font = self.label.font()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.valueLabels = {}
        for i, name in enumerate([f"CHANNEL{j}" for j in range(8)] + ["CURRENT_GLOBAL_TIME"]):
            nameLabel  = QLabel(name)
            font = nameLabel.font()
            font.setPointSize(15)
            nameLabel.setFont(font)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.subLayout.addWidget(nameLabel, i, 0)

            self.valueLabels[i] = QLabel("")
            font = self.valueLabels[i].font()
            font.setPointSize(15)
            self.valueLabels[i].setFont(font)
            self.valueLabels[i].setAlignment(Qt.AlignCenter)
            self.subLayout.addWidget(self.valueLabels[i], i, 1)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addLayout(self.subLayout)
        self.setLayout(self.mainLayout)
    
        return None
    
    def update(self):
        self.label.setText(f"STATES OF: EIGHT_CHANNEL_RELAY")

        channelsStates = self.ControlCenter_obj.modules[self.ControlCenter_obj.EIGHT_CHANNEL_RELAY_ADDRESS].channelsStates
        currentGlobalTime = self.ControlCenter_obj.modules[self.ControlCenter_obj.EIGHT_CHANNEL_RELAY_ADDRESS].currentGlobalTime

        for i, val in enumerate(channelsStates):
            self.valueLabels[i].setText(str(val))

        self.valueLabels[8].setText(str(currentGlobalTime))
        return None
    

    def clear(self):
        self.label.setText(f"STATES OF: ")
        for key in self.valueLabels:
            self.valueLabels[key].setText("")
        return None

