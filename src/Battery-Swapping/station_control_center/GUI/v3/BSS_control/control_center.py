import warnings
from collections import deque
from functools import partial
from typing import Callable, List


from PyQt5.QtCore import (
    QTimer,
    QObject,
    pyqtSignal)

from BSS_control.eight_channel_relay import (
    EightChannelRelay, 
    CHANNEL_NAME)

from BSS_control.battery_slot import (
    BatterySlot,
    LED_STRIP_STATE, 
    SOLENOID_NAME)
    
from BSS_control.CanUtils import (
    can_frame,
    MODULE_ADDRESS,
    CanStr)

class ControlCenterSignals(QObject):
    sendCanMsg = pyqtSignal(str)

    proccessToStartChargeIsActive_slot1 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot2 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot3 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot4 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot5 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot6 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot7 = pyqtSignal(bool)
    proccessToStartChargeIsActive_slot8 = pyqtSignal(bool)

    proccessToFinishChargeIsActive_slot1 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot2 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot3 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot4 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot5 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot6 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot7 = pyqtSignal(bool)
    proccessToFinishChargeIsActive_slot8 = pyqtSignal(bool)
    


class ControlCenter:
    SIGNALS = ControlCenterSignals()
    SLOT_ADDRESSES = [MODULE_ADDRESS(i) for i in [1,4,5,8]]
    CONTROL_CENTER_ADDRESS = MODULE_ADDRESS.CONTROL_CENTER
    EIGHT_CHANNEL_RELAY_ADDRESS = MODULE_ADDRESS.EIGHT_CHANNEL_RELAY

    SIGNALS_DICT_START_CHARGE = {
        MODULE_ADDRESS.SLOT1 : SIGNALS.proccessToStartChargeIsActive_slot1,
        MODULE_ADDRESS.SLOT2 : SIGNALS.proccessToStartChargeIsActive_slot2,
        MODULE_ADDRESS.SLOT3 : SIGNALS.proccessToStartChargeIsActive_slot3,
        MODULE_ADDRESS.SLOT4 : SIGNALS.proccessToStartChargeIsActive_slot4,
        MODULE_ADDRESS.SLOT5 : SIGNALS.proccessToStartChargeIsActive_slot5,
        MODULE_ADDRESS.SLOT6 : SIGNALS.proccessToStartChargeIsActive_slot6,
        MODULE_ADDRESS.SLOT7 : SIGNALS.proccessToStartChargeIsActive_slot7,
        MODULE_ADDRESS.SLOT8 : SIGNALS.proccessToStartChargeIsActive_slot8
    }
    
    SIGNALS_DICT_FINISH_CHARGE = {
        MODULE_ADDRESS.SLOT1 : SIGNALS.proccessToFinishChargeIsActive_slot1,
        MODULE_ADDRESS.SLOT2 : SIGNALS.proccessToFinishChargeIsActive_slot1,
        MODULE_ADDRESS.SLOT3 : SIGNALS.proccessToFinishChargeIsActive_slot3,
        MODULE_ADDRESS.SLOT4 : SIGNALS.proccessToFinishChargeIsActive_slot4,
        MODULE_ADDRESS.SLOT5 : SIGNALS.proccessToFinishChargeIsActive_slot5,
        MODULE_ADDRESS.SLOT6 : SIGNALS.proccessToFinishChargeIsActive_slot6,
        MODULE_ADDRESS.SLOT7 : SIGNALS.proccessToFinishChargeIsActive_slot7,
        MODULE_ADDRESS.SLOT8 : SIGNALS.proccessToFinishChargeIsActive_slot8
    }

    def __init__(self):
        self.modules = {address:BatterySlot(address) for address in self.SLOT_ADDRESSES}
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS] = EightChannelRelay()
        self.canMsgQueue = deque([])
        self.currentGlobalTime = 0
        self.connect_addCanMsgToQueue()
        self.connect_startAndFinishChargeProcessSignals()
        return None
    
    def connect_addCanMsgToQueue(self)->None:
        for slotAddress in self.SLOT_ADDRESSES:
            self.modules[slotAddress].SIGNALS_DICT[slotAddress].connect(self.canMsgQueue.appendleft)
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].SIGNALS.addCanMsgToQueue_eightChannelRelay.connect(self.canMsgQueue.appendleft)
        return None
    
    def connect_startAndFinishChargeProcessSignals(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.SIGNALS_DICT_START_CHARGE[slotAddress].connect(self.modules[slotAddress].battery.proccessToStartChargeIsActive_setter)
            self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].connect(self.modules[slotAddress].battery.proccessToFinishChargeIsActive_setter)
        return None
    
    
    def updateStatesFromCanStr(self, canStr : CanStr)->None:
        try:
            canMsg = can_frame.from_canStr(canStr)
        except Exception as e:
            warnings.warn(f"WARNING: Exception catched in ControlCenter.updateStatesFromCanStr(): {e}")
            return None
        
        if canMsg.destinationAddress == self.CONTROL_CENTER_ADDRESS:
            self.modules[canMsg.originAddress].updateStatesFromCanMsg(canMsg)

        relayChannelStates = self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].channelsStates
        for slotAddress in self.SLOT_ADDRESSES:
            self.modules[slotAddress].battery.updateStatesFromControlCenter(relayChannelStates[slotAddress.value-1])
        return None
    
    
    def updateCurrentGlobalTime(self, newCurrentGlobalTime : float)->None:
        self.currentGlobalTime = newCurrentGlobalTime
        for address in self.SLOT_ADDRESSES + [self.EIGHT_CHANNEL_RELAY_ADDRESS]:
            self.modules[address].updateCurrentGlobalTime(newCurrentGlobalTime)
        return None
    
    def sendCanMsg(self):
        if self.canMsgQueue:
            self.SIGNALS.sendCanMsg.emit(self.canMsgQueue.pop())
        return None
    

    def setSlotSolenoidState(self, slotAddress : MODULE_ADDRESS, name : SOLENOID_NAME, state : bool, delay : int = 0)->None:
        try:
            if delay > 0:
                QTimer.singleShot(delay, partial(self.modules[slotAddress].setSolenoidState, name, state))
            else:
                self.modules[slotAddress].setSolenoidState(name, state)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None
    
    def setSlotSolenoidsStates(self, slotAddress : MODULE_ADDRESS, states : List[bool], delay : int = 0)->None:
        try:
            if delay > 0:
                QTimer.singleShot(delay, partial(self.modules[slotAddress].setSolenoidsStates, states))
            else:
                self.modules[slotAddress].setSolenoidsStates(states)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None
    
    def setSlotLedStripState(self, slotAddress : MODULE_ADDRESS, state : LED_STRIP_STATE, delay : int = 0)->None:
        try:
            if delay > 0:
                QTimer.singleShot(delay, partial(self.modules[slotAddress].setLedStripState, state))
            else:
                self.modules[slotAddress].setLedStripState(state)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None    
    
    def setRelayChannelState(self, name : CHANNEL_NAME, state : bool, delay : int = 0)->None:
        if delay > 0:
            QTimer.singleShot(delay, partial(self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelState, name, state))
        else:
            self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelState(name, state)
        return None
    
    def setRelayChannelStates(self, states : List[bool], delay : int = 0)->None:
        if delay > 0:
            QTimer.singleShot(delay, partial(self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelStates, states))
        else: 
            self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelStates(states)
        return None


    def getSlotsThatMatchStates(self, statesToMatch):
        statesToMatchLogic = {
            "LIMIT_SWITCH"                       : (True,  "limitSwitchState"),
            "LED_STRIP"                          : (True,  "ledStripState"), 
            "BMS_SOLENOID"                       : (True,  "bmsSolenoidState"),
            "DOOR_LOCK_SOLENOID"                 : (True,  "doorLockSolenoidState"),
            "BATTERY_LOCK_SOLENOID"              : (True,  "batteryLockSolenoidState"),

            "BATTERY_IN_SLOT"                    : (True,  "limitSwitchState"),
            "BATTERY_BMS_IS_ON"                  : (True,  "bmsSolenoidState"),
            "BATTERY_BMS_HAS_CAN_BUS_ERROR"      : (True,  "batteryCanBusErrorState"),
            "BATTERY_IS_WAITING_FOR_ALL_DATA"    : (False, "waitingForAllData"), 
                

            "BATTERY_IS_ADDRESSABLE"              : (False, "isAddressable"),
            "BATTERY_IS_CHARGING"                 : (False, "isCharging"),
            "BATTERY_IS_CHARGED"                  : (False, "isCharged"),
            "BATTERY_CAN_PROCEED_TO_BE_CHARGED"   : (False, "canProceedToBeCharged"),
            "BATTERY_HAS_WARNINGS"                : (False, "hasWarnings"),
            "BATTERY_HAS_FATAL_WARNINGS"          : (False, "hasFatalWarnings"),
            "BATTERY_IS_DAMAGED"                  : (False, "isDamaged"),
            "BATTERY_IS_DELIVERABLE_TO_USER"      : (False, "isDeliverableToUser"),
            "BATTERY_IS_BUSY_WITH_CHARGE_PROCESS" : (False, "isBusyWithChargeProcess"),
            "BATTERY_RELAY_CHANNEL_IS_ON"         : (False, "relayChanneOn"),

            "PROCESS_TO_START_BATTERY_CHARGE_IS_ACTIVE"   : (False, "proccessToStartChargeIsActive"),
            "PROCESS_TO_FINISH_BATTERY_CHARGE_IS_ACTIVE"  : (False, "proccessToFinishChargeIsActive")
        }
        statesToMatch_ = {key:value for key,value in statesToMatch.items() if key in statesToMatchLogic.keys()}
        res = [slotAddress for slotAddress in self.SLOT_ADDRESSES]

        for stateKeyword, stateValueToMatch in statesToMatch_.items():

            if len(res) < 1:
                break

            isSlotAttr, attrName = statesToMatchLogic[stateKeyword]

            if isSlotAttr:
                res = [slotAddress for slotAddress in res if getattr(self.modules[slotAddress], attrName) == stateValueToMatch]
            else:
                res = [slotAddress for slotAddress in res if getattr(self.modules[slotAddress].battery, attrName) == stateValueToMatch]

        return res

    
    def _debugPrint(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.modules[slotAddress]._debugPrint()
        return None
    
    def secureAllSlots(self):
        notSecuredDoors = self.getSlotsThatMatchStates({"DOOR_LOCK_SOLENOID" : True})
        for slotAddress in notSecuredDoors:
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.DOOR_LOCK, 0)

        notSecuredBatts = self.getSlotsThatMatchStates({"BATTERY_LOCK_SOLENOID" : True})
        for slotAddress in notSecuredBatts:
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BATTERY_LOCK, 0)
        return None
    
    def turnOnBmsSolenoidsWhereWise(self):
        bmsShouldBeOn = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT"                     : True,
                                                      "BATTERY_BMS_IS_ON"                   : False,
                                                      "BATTERY_IS_BUSY_WITH_CHARGE_PROCESS" : False})
        for slotAddress in bmsShouldBeOn:
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 1)
        return None
    
    def turnOffAllBmsSolenoidsIfPossible(self):
        bmsShouldBeOff = self.getSlotsThatMatchStates({"BATTERY_BMS_IS_ON"                   : True,
                                                       "BATTERY_IS_BUSY_WITH_CHARGE_PROCESS" : False,
                                                       "BATTERY_RELAY_CHANNEL_IS_ON"         : False})
        for slotAddress in bmsShouldBeOff:
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
        return None
    

    def turnOnLedStripsBasedOnState(self):
        batteries_notInSlot         = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT"                : False })
        batteries_damaged           = self.getSlotsThatMatchStates({"BATTERY_IS_DAMAGED"             : True  })
        batteries_deliverableToUser = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER" : True  })
        other_batteries             = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT"                : True, 
                                                                    "BATTERY_IS_DAMAGED"             : False,
                                                                    "BATTERY_IS_DELIVERABLE_TO_USER" : False  })

        for slotAddress in batteries_notInSlot:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.BLUE)

        for slotAddress in batteries_damaged:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.PURPLE)

        for slotAddress in batteries_deliverableToUser:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.GREEN)

        for slotAddress in other_batteries:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.RED)

        return None
    
    def turnOnLedStripsBasedOnState_Entry(self):
        freeSlots     = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT" : False})
        occupiedSlots = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT" : True})

        for slotAddress in freeSlots:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.BLUE)

        for slotAddress in occupiedSlots:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.OFF)
        return None
    
    def turnOnLedStripsBasedOnState_Egress(self):
        slotsWithDeliverableBatteriesToUser = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER" : True})
        otherSlots = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER" : False})      

        try:
            selectedSlotAddress = slotsWithDeliverableBatteriesToUser[0]
            self.setSlotLedStripState(selectedSlotAddress, LED_STRIP_STATE.GREEN)
        except IndexError:
            selectedSlotAddress = None

        for slotAddress in otherSlots + slotsWithDeliverableBatteriesToUser[1:]:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.OFF)

        return selectedSlotAddress


    def turnOffAllLedStrips(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.OFF)
        return None
    
    def startChargeOfSlotBatteryIfAllowable(self, slotAddress):

        try:
            batteryCanProceedToBeCharged = self.modules[slotAddress].battery.canProceedToBeCharged
            doorLockSolenoidIsOn         = self.modules[slotAddress].doorLockSolenoidState
            batteryLockSolenoidIsOn      = self.modules[slotAddress].batteryLockSolenoidState
            batteryRelayChannelIsOn      = self.modules[slotAddress].battery.relayChanneOn
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
            

        if batteryCanProceedToBeCharged and (not doorLockSolenoidIsOn) and (not batteryLockSolenoidIsOn) and (not batteryRelayChannelIsOn):
            # We charge batteries that are chargable (i.e: voltage >= 42 and not isCharging), 
            # and also secured in their slot.
            self.SIGNALS_DICT_START_CHARGE[slotAddress].emit(True)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    0)
            self.setRelayChannelState(CHANNEL_NAME(slotAddress.value-1), 1, delay=500)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    1, delay=1000)
            QTimer.singleShot(6000, partial(self.SIGNALS_DICT_START_CHARGE[slotAddress].emit, False))
            print(f"batteryCanProceedToBeCharged: {batteryCanProceedToBeCharged}")
            print(f"startChargeOfSlotBatteryIfAllowable was triggered on slot: {slotAddress}")
            return None

        elif doorLockSolenoidIsOn or batteryLockSolenoidIsOn:
            msg = f"WARNING: Battery on {slotAddress} could proceed to be charged, but it is unsafe to do so"
            msg = f"{msg} as long as it is not secured in place. Ignoring command."
            warnings.warn(msg)
            return None
        
        return None


    def finishChargeOfSlotBatteryIfAllowable(self, slotAddress, forcedStop = False):

        """
        NOTE: Forcibly interrupting the charge process runs the risk of permanently damaging
        the battery's charger. However, in some cases it becomes necessary to do so, as
        charging a damaged battery is a tremendous fire hazard. Better to damage the charger (which
        will just stop working) than to risk an electrical fire breaking out inside the station.
        """

        try:
            batteryIsDamaged               = self.modules[slotAddress].battery.isDamaged
            batteryIsCharging              = self.modules[slotAddress].battery.isCharging
            batteryIsCharged               = self.modules[slotAddress].battery.isCharged
            batteryIsBusyWithChargeProcess = self.modules[slotAddress].battery.isBusyWithChargeProcess
            batteryBmsHasCanBusError       = self.modules[slotAddress].battery.bmsHasCanBusError
            batteryRelayChannelIsOn        = self.modules[slotAddress].battery.relayChanneOn
        except AttributeError: 
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")

        
        if batteryIsCharging and (batteryIsDamaged or forcedStop):
            # If the battery becomes damaged during charging, we forzably stop the charging process. 
            # We also stop it if it is explicitly enforced by the developer.

            self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].emit(True)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    0)
            self.setRelayChannelState(CHANNEL_NAME(slotAddress.value-1), 0,  delay=10000)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    1,  delay=11000)
            QTimer.singleShot(12000, partial(self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].emit, False))

            if forcedStop:
                msg = f"WARNING: PERFORMING MANUAL FORCED STOP OF THE CHARGING PROCESS FOR Battery{slotAddress}."
            else:
                msg = f"WARNING: Battery{slotAddress} has become damaged (isDamaged == True)."
                msg = f"{msg}. FORCIBLY STOPPING THE CHARGE PROCESS NOW."

            warnings.warn(msg)
            
            print(f"finishChargeOfSlotBatteryIfAllowable was triggered on slot: {slotAddress}")
            return None
            
        elif batteryIsCharged and (not batteryIsBusyWithChargeProcess) and batteryRelayChannelIsOn:
            # When the battery has finished its charging process, we shut down the charger in the correct way.
            self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].emit(True)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    0)
            self.setRelayChannelState(CHANNEL_NAME(slotAddress.value-1), 0, delay=500)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    1, delay=1000)
            QTimer.singleShot(6000, partial(self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].emit, False))

            print(f"batteryIsCharged: {batteryIsCharged}")
            print(f"not batteryIsBusyWithChargeProcess: {not batteryIsBusyWithChargeProcess}")
            print(f"finishChargeOfSlotBatteryIfAllowable was triggered on slot: {slotAddress}")
            return None
        
        elif batteryBmsHasCanBusError and batteryRelayChannelIsOn:
            # It may be that the battery becomes incommunicated due to an error in the BMS's CAN-bus.
            # If that happens we want to make sure that charging is physically impossible. Whether the 
            # charge is still on going, it's already finished or just never took place is unknown in this case.
            # Regardless, We shall assume the worst case scenario. That is, the relay channel is ON while
            # the battery posseses a CAN BUS error (which can only happen if the BMS is ON), we assume that
            # the battery was in the middle of a charging cycle when it became incomunicated and forzably shut
            # down the charging process. 
        
            self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].emit(True)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    0)
            self.setRelayChannelState(CHANNEL_NAME(slotAddress.value-1), 0,  delay=10000)
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS,    1,  delay=11000)
            QTimer.singleShot(12000, partial(self.SIGNALS_DICT_FINISH_CHARGE[slotAddress].emit, False))

            msg = f"WARNING: Battery{slotAddress} has become incommunicated (bmsHasCanBusError == True)."
            msg = f"{msg}. due to damage to the BMS's can bus. FORCIBLY STOPPING THE CHARGE PROCESS NOW."
            warnings.warn(msg)

            print(f"finishChargeOfSlotBatteryIfAllowable was triggered on slot: {slotAddress}")
            return None
        
        
        return None
    

    def startChargeOfSlotBatteriesIfAllowable(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.startChargeOfSlotBatteryIfAllowable(slotAddress)
        return None
  

    def finishChargeOfSlotBatteriesIfAllowable(self, forcedStop = False):
        for slotAddress in self.SLOT_ADDRESSES:
            self.finishChargeOfSlotBatteryIfAllowable(slotAddress, forcedStop)
        return None





















