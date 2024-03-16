import os
import warnings
import numpy as np
from enum import Enum
from functools import partial
from GUI_windows.info_window import InfoWindow
from GUI_windows.lock_screen import LockScreenWindow
from GUI_windows.options_panel import OptionsPanelWindow
from GUI_windows.user_prompt_panel import UserPromptPanelWindow

from PyQt5.QtGui import (
    QFont,
    QPixmap,
    QIcon)

from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    Qt, 
    QThreadPool, 
    QTimer, 
    QSize)

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget, 
    QLabel, 
    QPushButton,
    QHBoxLayout, 
    QVBoxLayout,
    QStackedLayout,
    QLayout,
    QSizePolicy,
    qApp,
    QToolBar,
    QAction,
    QStyle,
    QStackedWidget)

from User_database.user_database import (
    getUsers,
    updateUsersNumBatts)

from BSS_control.thread_workers import (
    SerialReadWorker,
    RfidReadWorker)


from BSS_control.CanUtils import MODULE_ADDRESS
from BSS_control.control_center import ControlCenter
from BSS_control.battery_slot import LED_STRIP_STATE, SOLENOID_NAME



IMGS_PATH = os.path.join(os.path.dirname(__file__), "Images_and_Icons")
SYMBOLS_PATHS = {
    "ATTENTION" : os.path.join(IMGS_PATH, "attention_symbol.png"),
    "ERROR_404" : os.path.join(IMGS_PATH, "error_404.png"),
    "INPUT"     : os.path.join(IMGS_PATH, "input.png"),
    "OUTPUT"    : os.path.join(IMGS_PATH, "output.png"),
}



class WINS(Enum):
    INFO_WINDOW = 0
    LOCK_SCREEN = 1
    OPTIONS_PANEL = 2
    USER_PROMPT_PANEL = 3


class MainWindowSignals(QObject):
    terminate_SerialReadWorker = pyqtSignal()
    terminate_RfidReadWorker   = pyqtSignal()
    batteryEntryDetected       = pyqtSignal(int)
    batteryEgressDetected      = pyqtSignal(int)
    

class MainWindow(QMainWindow):
    SIGNALS = MainWindowSignals()
    USER_INTERACTION_TIMEOUT = 300000
    BATTERY_INTERACTION_EMIT_TIMEOUT = 1500
    

    def __init__(self):
        super().__init__()
        self.setup()
        return None
    
    
# (0) ------ SET-UP RELATED FUNCS ------- (0)

    def setup(self):
        self.isBootingUp = True
        self.isShuttingDown = False
        self.readyToCloseApp = False

        self.user = None
        self.attendingUser = False
        self.numBattsStationDelta  = 0
        self.checkingForUserAndBatteryInteraction = False

        self.ControlCenter_obj = ControlCenter()
        self.globalTimers_setup()
        self.windows_setup()
        self.toolbar_setup()
        self.threadWorkers_setup()

        self.windows[WINS.LOCK_SCREEN].text = "BOOTING UP..."
        QTimer.singleShot(10000, self.hardware_setup)
        QTimer.singleShot(19500, self.isNotBootingUp)
        QTimer.singleShot(20000, self.workFlowReset)
        return None
    

    def globalTimers_setup(self):
        self.currentGlobalTime = 0
        self.globalTimers = {
              250 : QTimer(),
             1000 : QTimer(),
            30000 : QTimer() 
        }
        for key in self.globalTimers.keys():
            self.globalTimers[key].setInterval(key)

        self.globalTimers[250].timeout.connect(self.updateGlobalTimerVars250)
        self.globalTimers[1000].timeout.connect(self.updateGlobalTimerVars1000)
        self.globalTimers[30000].timeout.connect(self.updateGlobalTimerVars30000)

        for key in self.globalTimers.keys():
            self.globalTimers[key].start()
        return None


    def windows_setup(self):
        self.stckdWidget = QStackedWidget()

        self.windows = {
            WINS.INFO_WINDOW       : InfoWindow(),
            WINS.LOCK_SCREEN       : LockScreenWindow(),
            WINS.OPTIONS_PANEL     : OptionsPanelWindow(),
            WINS.USER_PROMPT_PANEL : UserPromptPanelWindow()
        }
        
        for key in self.windows.keys():
            self.stckdWidget.insertWidget(key.value, self.windows[key])

        self.show_window = {key:partial(self.stckdWidget.setCurrentIndex, key.value) for key in WINS}

        for key in self.windows[WINS.OPTIONS_PANEL].btns.keys():
            self.windows[WINS.OPTIONS_PANEL].clickedConnectBtns(key, partial(self.OptionsPanelWindow_workFlow, key))

        self.show_window[WINS.LOCK_SCREEN]()
        self.setCentralWidget(self.stckdWidget)
        return None
    @property
    def currentWindow(self):
        return WINS(self.stckdWidget.currentIndex())
    

    def toolbar_setup(self):
        toolbar = QToolBar("toolbar")
        toolbar.setIconSize(QSize(25, 25))
        self.addToolBar(toolbar)
        icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        button_action = QAction(QIcon(icon), "Sobre Nosotros", self)
        button_action.triggered.connect(self.showAboutUsSection)
        toolbar.addAction(button_action)
        toolbar.addSeparator()
        return None 
    def showAboutUsSection(self):
        if self.currentWindow == WINS.LOCK_SCREEN:
            self.show_window[WINS.INFO_WINDOW]()
            self.timeInsideAboutUsSection = float(self.currentGlobalTime)
        elif self.currentWindow == WINS.INFO_WINDOW:
            self.show_window[WINS.LOCK_SCREEN]()
        return None
    

    def threadWorkers_setup(self):
        self.threadpool = QThreadPool()
        self.serialReadWorker_setup()
        self.rfidReadWorker_setup()
        return None
    def serialReadWorker_setup(self):
        self.serialReadWorker = SerialReadWorker()
        self.SIGNALS.terminate_SerialReadWorker.connect(self.serialReadWorker.endRun)
        self.ControlCenter_obj.SIGNALS.sendCanMsg.connect(self.serialReadWorker.sendCanMsg)
        self.serialReadWorker.signals.serialLaunchFailure.connect(self.serialLaunchFailure)
        self.serialReadWorker.signals.serialReadResults.connect(self.ControlCenter_obj.updateStatesFromCanStr)
        self.threadpool.start(self.serialReadWorker)
        return None
    def serialLaunchFailure(self):
        self.readyToCloseApp = True
        self.close()
        return None
    def rfidReadWorker_setup(self):
        self.rfidReadWorker = RfidReadWorker()
        self.SIGNALS.terminate_RfidReadWorker.connect(self.rfidReadWorker.endRun)
        self.rfidReadWorker.signals.rfidReadResults.connect(self.LockScreenWindow_workFlow)
        self.threadpool.start(self.rfidReadWorker)
        return None
    
    def hardware_setup(self):
        self.ControlCenter_obj.turnOffAllLedStrips()
        self.ControlCenter_obj.secureAllSlots()
        self.ControlCenter_obj.turnOnBmsSolenoidsWhereWise()
        return None
    


# (1) ------------------- GLOBAL TIMERS FUNCS --------------------------- (1)
    
    def updateGlobalTimerVars250(self):
        self.currentGlobalTime += 250
        self.ControlCenter_obj.updateCurrentGlobalTime(self.currentGlobalTime)
        self.ControlCenter_obj.sendCanMsg()
        return None
    
    def updateGlobalTimerVars1000(self):
        freeSlots = self.ControlCenter_obj.getSlotsThatMatchStates({"BATTERY_IN_SLOT":False})
        
        if self.checkingForUserAndBatteryInteraction:   
            # BATTERY ENTRY DETECTION
            if len(freeSlots) < len(self.freeSlots):
                self.user["numBatts"] -= 1
                self.numBattsStationDelta += 1
                slotTargeted = [slotAddress for slotAddress in self.freeSlots if slotAddress not in freeSlots][0]
                QTimer.singleShot(
                    self.BATTERY_INTERACTION_EMIT_TIMEOUT, 
                    partial(self.batteryEntry_workflow_part2, slotTargeted.value))
                self.checkingForUserAndBatteryInteraction = False

            # BATTERY EGRESS DETECTION
            elif len(freeSlots) > len(self.freeSlots):
                self.user["numBatts"] += 1
                self.numBattsStationDelta -= 1
                slotTargeted = [slotAddress for slotAddress in freeSlots if slotAddress not in self.freeSlots][0]
                QTimer.singleShot(
                    self.BATTERY_INTERACTION_EMIT_TIMEOUT, 
                    partial(self.batteryEgress_workflow_part2, slotTargeted.value))
                self.checkingForUserAndBatteryInteraction = False

        self.freeSlots = freeSlots
        self.slotsWithDeliverableBattsToUser = self.ControlCenter_obj.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER":True})


        if not self.attendingUser:
            self.userInteractionTimer = self.currentGlobalTime
        return None
    
    def updateGlobalTimerVars30000(self):
        self.windows[WINS.LOCK_SCREEN].dateClock.updateTime()
        self.windows[WINS.LOCK_SCREEN].dateClock.updateDate()

        if self.currentWindow == WINS.INFO_WINDOW:
            if self.currentGlobalTime - self.timeInsideAboutUsSection > 30000:
                self.show_window[WINS.LOCK_SCREEN]()

        if not self.attendingUser:
            #self.ControlCenter_obj.startChargeOfSlotBatteriesIfAllowable()
            #QTimer.singleShot(1000, self.ControlCenter_obj.finishChargeOfSlotBatteriesIfAllowable)
            pass
        elif self.currentGlobalTime - self.userInteractionTimer > self.USER_INTERACTION_TIMEOUT:
            self.workFlowReset()
        return None


# (2) -----------------LOCK SCREEN WINDOW WORKFLOW ---------------------- (2)
    
    def LockScreenWindow_workFlow(self, cardId):
        if self.attendingUser or self.isBootingUp or self.isShuttingDown:
            return None
        
        elif self.currentWindow not in [WINS.LOCK_SCREEN, WINS.INFO_WINDOW]:
            return None
        
        elif self.currentWindow == WINS.INFO_WINDOW:
            self.show_window[WINS.LOCK_SCREEN]()

        self.attendingUser = True
        self.ControlCenter_obj.turnOnLedStripsBasedOnState()

        if cardId < 0:
            errorMsg = "ERROR AL LEER TARJETA! INTENTE DE NUEVO"
            self.windows[WINS.LOCK_SCREEN].text = errorMsg
            QTimer.singleShot(2000, self.workFlowReset)
            return None
        
        users = getUsers({"cardId":cardId})

        if not users:
            noUsersFoundMsg = "USUARIO NO REGISTRADO. REGÍSTRESE PARA USAR LA ESTACIÓN"
            self.windows[WINS.LOCK_SCREEN].text = noUsersFoundMsg
            QTimer.singleShot(2000, self.workFlowReset)
            return None
        
        elif len(users) > 1:
            manyUsersFoundMsg = f"ERROR: {len(users)} users were found matching the current cardId" 
            manyUsersFoundMsg = f"{manyUsersFoundMsg}. Closing app. Users' data might be compromised."
            warnings.warn(manyUsersFoundMsg)
            manyUsersFoundMsg = f"ERROR DE BASE DE DATOS: MULTIPLICIDAD DE USUARIOS DETECTADA."
            self.windows[WINS.LOCK_SCREEN].text = manyUsersFoundMsg
            QTimer.singleShot(2000, self.workFlowReset)
            raise None
        
        self.user = users[0]
        userName = f"{self.user['firstName']} {self.user['lastName']}"
        userFoundMsg = f"BIENVENID@ {userName}"
        self.windows[WINS.LOCK_SCREEN].text = userFoundMsg      
        QTimer.singleShot(3000, self.show_window[WINS.OPTIONS_PANEL])
        return None
    

# (3) ------------ OPTIONS PANEL WINDOW WORKFLOW ----------------------- (3)

    def OptionsPanelWindow_workFlow(self, btnClicked):
        self.optionsPanelBtnClickedByUser = btnClicked
        if self.optionsPanelBtnClickedByUser in [0,2]:
            self.batteryEntry_workflow_part1()
        elif self.optionsPanelBtnClickedByUser == 1:
            self.batteryEgress_workflow_part1()
        return None
    

# (3.1) ------------ BATTERY ENTRY WORKFLOW-------------------- (3.1)
    
    def batteryEntry_workflow_part1(self):
        msg = None        
        if self.user["numBatts"] == 0:
            msg = "¡LO SENTIMOS! EL SISTEMA NO REGISTRA QUE USTED TENGA BATERÍAS PARA ENTREGAR" 

        elif len(self.freeSlots) < self.user["numBatts"]:
            msg = "¡LO SENTIMOS! ACTUALMENTE NO HAY SUFICIENTES SLOTS VACÍOS DISPONIBLES. VUELVA MÁS TARDE"

        if msg is not None:
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            self.windows[WINS.USER_PROMPT_PANEL].setImgs(0, SYMBOLS_PATHS["ATTENTION"])
            self.windows[WINS.USER_PROMPT_PANEL].setImgsEqual()
            self.show_window[WINS.USER_PROMPT_PANEL]()
            QTimer.singleShot(3000, self.workFlowReset)
            return None
        
        self.batteryEntry_workflow_part2()
        return None


    def batteryEntry_workflow_part2(self, slotTargetedValue = None):

        self.ControlCenter_obj.turnOnLedStripsBasedOnState_Entry()

        if self.user["numBatts"] > 0 and self.numBattsStationDelta == 0:
            msg = "POR FAVOR INGRESE LA 1ª BATERÍA EN UN SLOT AZUL DE SU ELECCIÓN"
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            self.windows[WINS.USER_PROMPT_PANEL].setImgs(0, SYMBOLS_PATHS["INPUT"])
            self.windows[WINS.USER_PROMPT_PANEL].setImgsEqual()
            self.show_window[WINS.USER_PROMPT_PANEL]()

            for slotAddress in self.freeSlots:
                self.ControlCenter_obj.setSlotSolenoidsStates(slotAddress, [0,1,1])

            self.checkingForUserAndBatteryInteraction = True


        elif self.user["numBatts"] == 1 and self.numBattsStationDelta == 1:
            msg = "POR FAVOR INGRESE LA 2ª BATERÍA EN UN SLOT AZUL DE SU ELECCIÓN"
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            slotTargeted = MODULE_ADDRESS(slotTargetedValue)
            self.ControlCenter_obj.setSlotSolenoidsStates(slotTargeted, [1,0,0])
            self.checkingForUserAndBatteryInteraction = True


        else:
            msg = "¡BATERÍAS INGRESADAS EXITOSAMENTE!"
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            self.windows[WINS.USER_PROMPT_PANEL].setImgs(0, SYMBOLS_PATHS["INPUT"])
            self.windows[WINS.USER_PROMPT_PANEL].setImgsEqual()
            slotTargeted = MODULE_ADDRESS(slotTargetedValue)
            self.ControlCenter_obj.setSlotSolenoidsStates(slotTargeted, [1,0,0])
            self.checkingForUserAndBatteryInteraction = False
            self.numBattsStationDelta = 0

            if self.optionsPanelBtnClickedByUser  == 0:
                msg = "GRACIAS POR USAR NUESTRA ESTACIÓN ¡VUELVA PRONTO!"
                QTimer.singleShot(2000, partial(self.windows[WINS.USER_PROMPT_PANEL].setText, msg))
                QTimer.singleShot(4000, self.workFlowReset)

            elif self.optionsPanelBtnClickedByUser == 2:
                for slotAddress in self.freeSlots:
                    self.ControlCenter_obj.setSlotSolenoidState(slotAddress, SOLENOID_NAME.DOOR_LOCK,    0)
                    self.ControlCenter_obj.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BATTERY_LOCK, 0)
                self.batteryEgress_workflow_part1()
                    
        return None


# (3.2) ------------ BATTERY EGRESS WORKFLOW-------------------- (3.2)
    
    def batteryEgress_workflow_part1(self):
        msg = None
        maxNumBattsRequestableByUser = self.user["maxNumBatts"] - self.user["numBatts"]

        if self.user["numBatts"] >= self.user["maxNumBatts"]:
            msg = "¡LO SENTIMOS! EL SISTEMA REGISTRA QUE USTED ACTUALMENTE POSEE EL NÚMERO MÁXIMO DE BATERÍAS"
            msg = f"{msg} QUE SE PUEDEN PRESTAR EN SIMULTÁNEO. ENTREGUE LAS QUE YA TIENE PARA OBTENER NUEVAS."


        elif len(self.slotsWithDeliverableBattsToUser) < maxNumBattsRequestableByUser:
            msg = "¡LO SENTIMOS! NO HAY SUFICIENTES BATERÍAS CARGADAS DISPONIBLES"

            eligibleSlots = self.ControlCenter_obj.getSlotsThatMatchStates({"BATTERY_IS_ADDRESSABLE" : True,
                                                                            "BATTERY_IS_DAMAGED"     : False})
            
            if len(eligibleSlots) < maxNumBattsRequestableByUser:
                msg = f"{msg}. VUELVA MÁS TARDE."
            
            else:
                timeUntilFullCharge = [(slotAddress, self.ControlCenter_obj.modules[slotAddress].battery.timeUntilFullCharge) for slotAddress in eligibleSlots]
                timeUntilFullCharge = sorted(timeUntilFullCharge, key=lambda x: x[1])[maxNumBattsRequestableByUser-1]
                timeUntilFullCharge = self.ControlCenter_obj.modules[timeUntilFullCharge[0]].battery.timeUntilFullChargeInStrFormat
                msg = f"{msg}. VUELVA EN APROX. {timeUntilFullCharge}"


        if msg is not None:
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            self.windows[WINS.USER_PROMPT_PANEL].setImgs(0, SYMBOLS_PATHS["ATTENTION"])
            self.windows[WINS.USER_PROMPT_PANEL].setImgsEqual()
            self.show_window[WINS.USER_PROMPT_PANEL]()
            QTimer.singleShot(3000, self.workFlowReset)
            return None
        
        self.batteryEgress_workflow_part2()
        return None
    


    def batteryEgress_workflow_part2(self, slotTargetedValue = None):

        maxNumBattsRequestableByUser = self.user["maxNumBatts"] - self.user["numBatts"]

        if maxNumBattsRequestableByUser > 0 and self.numBattsStationDelta == 0:
            selectedSlotAddress = self.ControlCenter_obj.turnOnLedStripsBasedOnState_Egress()
            msg = "POR FAVOR RETIRE LA 1ª BATERÍA DEL SLOT VERDE INDICADO"
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            self.windows[WINS.USER_PROMPT_PANEL].setImgs(0, SYMBOLS_PATHS["OUTPUT"])
            self.windows[WINS.USER_PROMPT_PANEL].setImgsEqual()
            self.show_window[WINS.USER_PROMPT_PANEL]()
            self.ControlCenter_obj.setSlotSolenoidsStates(selectedSlotAddress, [0,1,1])
            self.checkingForUserAndBatteryInteraction = True

        elif maxNumBattsRequestableByUser == 1 and self.numBattsStationDelta == -1:
            selectedSlotAddress = self.ControlCenter_obj.turnOnLedStripsBasedOnState_Egress()
            msg = "POR FAVOR RETIRE LA 2ª BATERÍA DEL SLOT VERDE INDICADO"
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            slotTargeted = MODULE_ADDRESS(slotTargetedValue)
            self.ControlCenter_obj.setSlotSolenoidsStates(slotTargeted, [0,0,0])
            self.ControlCenter_obj.setSlotSolenoidsStates(selectedSlotAddress, [0,1,1])
            self.checkingForUserAndBatteryInteraction = True            

        else:
            msg = "¡BATERÍAS RETIRADAS EXITOSAMENTE!"
            self.windows[WINS.USER_PROMPT_PANEL].text = msg
            self.windows[WINS.USER_PROMPT_PANEL].setImgs(0, SYMBOLS_PATHS["OUTPUT"])
            self.windows[WINS.USER_PROMPT_PANEL].setImgsEqual()
            slotTargeted = MODULE_ADDRESS(slotTargetedValue)
            self.ControlCenter_obj.setSlotSolenoidsStates(slotTargeted, [0,0,0])
            self.checkingForUserAndBatteryInteraction = False
            self.numBattsStationDelta = 0

            msg = "GRACIAS POR USAR NUESTRA ESTACIÓN ¡VUELVA PRONTO!"
            QTimer.singleShot(2000, partial(self.windows[WINS.USER_PROMPT_PANEL].setText, msg))
            QTimer.singleShot(4000, self.workFlowReset)
        return None
    





# (4) ------------ OTHER RELEVANT FUNCTIONS ------------------- (4)

    def workFlowReset(self):
        if self.user is not None:
            updateUsersNumBatts({"cardId":self.user["cardId"]}, self.user["numBatts"])
        
        self.user = None
        self.checkingForUserAndBatteryInteraction = False
        self.hardware_setup()
        resetMsg = "POR FAVOR ACERQUE SU TARJETA AL LECTOR PARA INICIAR"
        self.windows[WINS.LOCK_SCREEN].text = resetMsg
        self.show_window[WINS.LOCK_SCREEN]()
        self.attendingUser = False
        return None


    def isNotBootingUp(self):
        self.isBootingUp = False
        return None

    def readyToCloseAppTrue(self):
        self.readyToCloseApp = True
        return None

    def hardware_shutdown(self):
        self.ControlCenter_obj.turnOffAllLedStrips()
        self.ControlCenter_obj.secureAllSlots()
        self.ControlCenter_obj.turnOffAllBmsSolenoidsIfPossible()
        return None
    
    def exitCall(self):
        self.isShuttingDown = True
        self.windows[WINS.LOCK_SCREEN].text = "SHUTTING DOWN ..."
        self.show_window[WINS.LOCK_SCREEN]()
        self.hardware_shutdown()
        self.SIGNALS.terminate_RfidReadWorker.emit()
        QTimer.singleShot(3000, self.SIGNALS.terminate_SerialReadWorker.emit)
        QTimer.singleShot(8000, self.readyToCloseAppTrue)
        QTimer.singleShot(8500, self.close)
        return None

    def closeEvent(self, e):
        if self.readyToCloseApp:
            e.accept()
        else:
            self.exitCall()
            e.ignore()
        return None
    
 
        


    
 