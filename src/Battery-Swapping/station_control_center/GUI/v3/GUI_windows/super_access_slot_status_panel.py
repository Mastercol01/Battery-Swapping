from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout




class SuperAccessSlotStatusPanelWindow(QWidget):
    SLOT_STATES_LABEL_NAMES = {
        "limitSwitchState"           :"LIMIT_SWITCH",
        "ledStripState"              :"LED_STRIP",
        "bmsSolenoidState"           :"BMS_SOLENOID",        
        "doorLockSolenoidState"      :"DOOR_LOCK_SOLENOID",
        "batteryLockSolenoidState"   :"BATTERY_LOCK_SOLENOID",
        "batteryCanBusErrorState"    :"BATTERY_HAS_CAN_BUS_ERROR", 
        "currentGlobalTime"          :"CURRENT_GLOBAL_TIME"
    }


    def __init__(self, ControlCenter_obj):
        super().__init__()   

        self.ControlCenter_obj = ControlCenter_obj

        self.mainLayout = QVBoxLayout()
        self.subLayout  = QGridLayout()
        self.containerWidget = QWidget()

        self.label = QLabel("STATES OF: ")
        font = self.label.font()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.valueLabels = {}
        for i, (name, labelName) in enumerate(self.SLOT_STATES_LABEL_NAMES.items()):
            nameLabel  = QLabel(labelName)
            font = self.label.font()
            font.setPointSize(15)
            nameLabel.setFont(font)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.subLayout.addWidget(nameLabel, i, 0)

            self.valueLabels[name] = QLabel("")
            font = self.label.font()
            font.setPointSize(15)
            self.valueLabels[name].setFont(font)
            self.valueLabels[name].setAlignment(Qt.AlignCenter)
            self.subLayout.addWidget(self.valueLabels[name], i, 1)
        self.containerWidget.setLayout(self.subLayout)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.containerWidget)

        self.setLayout(self.mainLayout)
    
        return None
    
    def update(self, slotAddress):
        if slotAddress not in self.ControlCenter_obj.SLOT_ADDRESSES:
            return None
        self.label.setText(f"STATES OF: {str(slotAddress).replace('MODULE_ADDRESS.', '')}")

        for key in self.valueLabels:
            value = str(getattr(self.ControlCenter_obj.modules[slotAddress], key))

            if key == "ledStripState":
                value = value.replace('LED_STRIP_STATE', '')

            self.valueLabels[key].setText(value)
        return None
    
    def clear(self):
        self.label.setText(f"STATES OF: ")
        for key in self.valueLabels:
            self.valueLabels[key].setText("")
        return None




        


    

