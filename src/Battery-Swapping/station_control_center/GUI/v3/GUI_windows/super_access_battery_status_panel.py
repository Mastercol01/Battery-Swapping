from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPlainTextEdit




class SuperAccessBatteryStatusPanelWindow(QWidget):
    TIMERS_LABEL_NAMES = {
        "currentGlobalTime" : "CURRENT_GLOBAL_TIME",
        "localTimer"        : "LOCAL_TIMER"
    }

    ADDRESSABILITY_LABEL_NAMES = {
        "inSlot"            : "IN_SLOT",
        "bmsON"             : "BMS_IS_ON",
        "waitingForAllData" : "IS_WAITING_FOR_ALL_DATA",
        "bmsHasCanBusError" : "BMS_HAS_CAN_BUS_ERROR",
        "isAddressable"     : "IS_ADDRESSABLE"
    }
    HEALTH_LABEL_NAMES = {
        "isDamaged"         : "IS_DAMAGED",
        "hasWarnings"       : "HAS_WARNINGS",
        "hasFatalWarnings"  : "HAS_FATAL_WARNINGS",
        "bmsHasCanBusError" : "BMS_HAS_CAN_BUS_ERROR",
    }
    ATTRS_LABEL_NAMES = {
        "voltage"                        : "VOLTAGE [V]",
        "current"                        : "CURRENT [A]",
        "soc"                            : "SOC [%]",
        "maxTemp"                        : "MAX_TEMP [°C]",
        "isCharging"                     : "IS_CHARGING",
        "isCharged"                      : "IS_CHARGED",
        "canProceedToBeCharged"          : "CAN_PROCEED_TO_BE_CHARGED",
        "timeUntilFullChargeInStrFormat" : "TIME_UNTIL_FULL_CHARGE",
        "isDeliverableToUser"            : "IS_DELIVERABLE_TO_USER",
        "proccessToStartChargeIsActive"  : "PROCESS_TO_START_CHARGE_IS_ACTIVE",
        "proccessToFinishChargeIsActive" : "PROCESS_TO_FINISH_CHARGE_IS_ACTIVE",
        "isBusyWithChargeProcess"        : "IS_BUSY_WITH_CHARGE_PROCESS",
        "relayChanneOn"                  : "RELAY_CHANNEL_IS_ON"
    }

    

    def __init__(self, ControlCenter_obj):
        super().__init__()   
        self.ControlCenter_obj = ControlCenter_obj

        self.primaryLayout   = QVBoxLayout()
        self.secondaryLayout = QHBoxLayout()
        self.tertiaryLayout_colLeft  = QVBoxLayout()
        self.tertiaryLayout_colRight = QVBoxLayout()
        self.quaternaryLayout_timersGrid         = QGridLayout() 
        self.quaternaryLayout_addressabilityGrid = QGridLayout()
        self.quaternaryLayout_healthGrid         = QGridLayout() 
        self.quaternaryLayout_attributesGrid     = QGridLayout() 
        
        self.timersLabels         = {}
        self.addressabilityLabels = {}
        self.healthLabels         = {}
        self.attributesLabels     = {}

        self.mainTitle = QLabel("STATES OF BATTERY IN: ")
        font = self.mainTitle.font()
        font.setPointSize(30)
        self.mainTitle.setFont(font)
        self.mainTitle.setAlignment(Qt.AlignCenter)

        self.timerTitle = QLabel("TIMERS")
        font = self.timerTitle.font()
        font.setPointSize(25)
        self.timerTitle.setFont(font)
        self.timerTitle.setAlignment(Qt.AlignCenter)

        self.addressabilityTitle = QLabel("ADDRESSABILITY")
        font = self.addressabilityTitle.font()
        font.setPointSize(25)
        self.addressabilityTitle.setFont(font)
        self.addressabilityTitle.setAlignment(Qt.AlignCenter)

        self.healthTitle = QLabel("HEALTH")
        font = self.healthTitle.font()
        font.setPointSize(25)
        self.healthTitle.setFont(font)
        self.healthTitle.setAlignment(Qt.AlignCenter)

        self.attrsTitle = QLabel("ATTRIBUTES")
        font = self.attrsTitle.font()
        font.setPointSize(25)
        self.attrsTitle.setFont(font)
        self.attrsTitle.setAlignment(Qt.AlignCenter)
        
        self.warningsTitle = QLabel("WARNINGS")
        font = self.warningsTitle.font()
        font.setPointSize(20)
        self.warningsTitle.setFont(font)
        self.warningsTitle.setAlignment(Qt.AlignCenter)

        self.fatalWarningsTitle = QLabel("FATAL WARNINGS")
        font = self.fatalWarningsTitle.font()
        font.setPointSize(20)
        self.fatalWarningsTitle.setFont(font)
        self.fatalWarningsTitle.setAlignment(Qt.AlignCenter)

        self.warnings = QPlainTextEdit()
        self.warnings.setReadOnly(True)

        self.fatalWarnings = QPlainTextEdit()
        self.fatalWarnings.setReadOnly(True)



        #TIMERS SETUP
        for i, (name, labelName) in enumerate(self.TIMERS_LABEL_NAMES.items()):
            nameLabel  = QLabel(labelName)
            font = nameLabel.font()
            font.setPointSize(15)
            nameLabel.setFont(font)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_timersGrid.addWidget(nameLabel, i, 0)

            self.timersLabels[name] = QLabel("")
            font = self.timersLabels[name].font()
            font.setPointSize(15)
            self.timersLabels[name].setFont(font)
            self.timersLabels[name].setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_timersGrid.addWidget(self.timersLabels[name], i, 1)

        # ADDRESSABILITY SETUP
        for i, (name, labelName) in enumerate(self.ADDRESSABILITY_LABEL_NAMES.items()):
            nameLabel  = QLabel(labelName)
            font = nameLabel.font()
            font.setPointSize(15)
            nameLabel.setFont(font)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_addressabilityGrid.addWidget(nameLabel, i, 0)

            self.addressabilityLabels[name] = QLabel("")
            font = self.addressabilityLabels[name].font()
            font.setPointSize(15)
            self.addressabilityLabels[name].setFont(font)
            self.addressabilityLabels[name].setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_addressabilityGrid.addWidget(self.addressabilityLabels[name], i, 1)

        # HEALTH SETUP
        for i, (name, labelName) in enumerate(self.HEALTH_LABEL_NAMES.items()):
            nameLabel  = QLabel(labelName)
            font = nameLabel.font()
            font.setPointSize(15)
            nameLabel.setFont(font)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_healthGrid.addWidget(nameLabel, i, 0)

            self.healthLabels[name] = QLabel("")
            font = self.healthLabels[name].font()
            font.setPointSize(15)
            self.healthLabels[name].setFont(font)
            self.healthLabels[name].setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_healthGrid.addWidget(self.healthLabels[name], i, 1)

        # ATTR SETUP 
        for i, (name, labelName) in enumerate(self.ATTRS_LABEL_NAMES.items()):
            nameLabel  = QLabel(labelName)
            font = nameLabel.font()
            font.setPointSize(15)
            nameLabel.setFont(font)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_attributesGrid.addWidget(nameLabel, i, 0)

            self.attributesLabels[name] = QLabel("")
            font = self.attributesLabels[name].font()
            font.setPointSize(15)
            self.attributesLabels[name].setFont(font)
            self.attributesLabels[name].setAlignment(Qt.AlignCenter)
            self.quaternaryLayout_attributesGrid.addWidget(self.attributesLabels[name], i, 1)


        #ASSEMBLY
        self.tertiaryLayout_colLeft.addWidget(self.addressabilityTitle)
        self.tertiaryLayout_colLeft.addLayout(self.quaternaryLayout_addressabilityGrid)
        self.tertiaryLayout_colLeft.addWidget(self.attrsTitle)
        self.tertiaryLayout_colLeft.addLayout(self.quaternaryLayout_attributesGrid)
        self.tertiaryLayout_colLeft.addWidget(self.timerTitle)
        self.tertiaryLayout_colLeft.addLayout(self.quaternaryLayout_timersGrid)

        self.tertiaryLayout_colRight.addWidget(self.healthTitle)
        self.tertiaryLayout_colRight.addLayout(self.quaternaryLayout_healthGrid)
        self.tertiaryLayout_colRight.addWidget(self.warningsTitle)
        self.tertiaryLayout_colRight.addWidget(self.warnings)
        self.tertiaryLayout_colRight.addWidget(self.fatalWarningsTitle)
        self.tertiaryLayout_colRight.addWidget(self.fatalWarnings)

        self.secondaryLayout.addLayout(self.tertiaryLayout_colLeft)
        self.secondaryLayout.addLayout(self.tertiaryLayout_colRight)

        self.primaryLayout.addWidget(self.mainTitle)
        self.primaryLayout.addLayout(self.secondaryLayout)
            
        self.setLayout(self.primaryLayout)
        return None
    
    def update(self, slotAddress):
        if slotAddress not in self.ControlCenter_obj.SLOT_ADDRESSES:
            return None
        self.mainTitle.setText(f"STATES BATTERY IN: {str(slotAddress).replace('MODULE_ADDRESS.', '')}")

        for key in self.addressabilityLabels:
            value = getattr(self.ControlCenter_obj.modules[slotAddress].battery, key)
            self.addressabilityLabels[key].setText(str(value))

        for key in self.attributesLabels:
            value = getattr(self.ControlCenter_obj.modules[slotAddress].battery, key)
            if key in ["voltage", "current"]:
                value = round(value, 2)
            self.attributesLabels[key].setText(str(value))

        for key in self.timersLabels:
            value = getattr(self.ControlCenter_obj.modules[slotAddress].battery, key)
            self.timersLabels[key].setText(str(value))

        for key in self.healthLabels:
            value = getattr(self.ControlCenter_obj.modules[slotAddress].battery, key)
            self.healthLabels[key].setText(str(value))

        warnings = self.ControlCenter_obj.modules[slotAddress].battery.warnings
        warnings = [str(warning).replace('BATTERY_WARNINGS.', '') for warning in warnings]
        warnings.sort()
        warnings = "\n".join(warnings)
        self.warnings.setPlainText(warnings)

        fatalWarnings = self.ControlCenter_obj.modules[slotAddress].battery.fatalWarnings
        fatalWarnings = [str(fatalWarning).replace('BATTERY_WARNINGS.', '') for fatalWarning in fatalWarnings]
        fatalWarnings.sort()
        fatalWarnings = "\n".join(fatalWarnings)
        self.fatalWarnings.setPlainText(fatalWarnings)
    
        return None
    
    def clear(self):
        self.mainTitle.setText(f"STATES BATTERY IN: ")
        
        for key in self.addressabilityLabels:
            self.addressabilityLabels[key].setText("")

        for key in self.attributesLabels:
            self.attributesLabels[key].setText("")

        for key in self.timersLabels:
            self.timersLabels[key].setText("")

        for key in self.healthLabels:
            self.healthLabels[key].setText("")

        self.warnings.setPlainText("")
        self.fatalWarnings.setPlainText("")
        return None

