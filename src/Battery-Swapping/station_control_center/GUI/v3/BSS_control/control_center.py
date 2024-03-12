import warnings
from typing import Callable
from functools import partial
from PyQt5.QtCore import QTimer

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



class ControlCenter:
    SLOT_ADDRESSES = [MODULE_ADDRESS(i) for i in [1,4,5,8]]
    CONTROL_CENTER_ADDRESS = MODULE_ADDRESS.CONTROL_CENTER
    EIGHT_CHANNEL_RELAY_ADDRESS = MODULE_ADDRESS.EIGHT_CHANNEL_RELAY


    def __init__(self):
        self.modules = {address:BatterySlot(address) for address in self.SLOT_ADDRESSES}
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS] = EightChannelRelay()
        self.currentGlobalTime = 0
        return None
    
    def updateStatesFromCanStr(self, canStr : CanStr)->None:
        try:
            canMsg = can_frame.from_canStr(canStr)
        except Exception as e:
            warnings.warn(f"WARNING: Exception catched in ControlCenter.updateStatesFromCanStr(): {e}")
            return None
        
        if canMsg.destinationAddress == self.CONTROL_CENTER_ADDRESS:
            self.modules[canMsg.originAddress].updateStatesFromCanMsg(canMsg)
        return None
    
    def updateCurrentGlobalTime(self, newCurrentGlobalTime : float)->None:
        self.currentGlobalTime = newCurrentGlobalTime
        for address in self.SLOT_ADDRESSES + [self.EIGHT_CHANNEL_RELAY_ADDRESS]:
            self.modules[address].updateCurrentGlobalTime(newCurrentGlobalTime)
        return None
    
    def connect_sendCanMsg(self, sendCanMsg_func : Callable[[CanStr], None])->None:
        for address in self.SLOT_ADDRESSES:
            self.modules[address].SIGNALS_DICT[address].connect(sendCanMsg_func)
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].SIGNALS.sendCanMsg_eightChannelRelay.connect(sendCanMsg_func)
        return None
    
    def setSlotSolenoidState(self, slotAddress : MODULE_ADDRESS, name : SOLENOID_NAME, state : bool)->None:
        try:
            self.modules[slotAddress].setSolenoidState(name, state)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None
    
    def setSlotSolenoidStates(self, slotAddress : MODULE_ADDRESS, states : bool)->None:
        try:
            self.modules[slotAddress].setSolenoidsStates(states)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None
    
    def setSlotLedStripState(self, slotAddress : MODULE_ADDRESS, state : LED_STRIP_STATE)->None:
        try:
            self.modules[slotAddress].setLedStripState(state)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None    
    
    def setRelayChannelState(self, name : CHANNEL_NAME, state : bool)->None:
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelState(name, state)
        return None
    
    def setRelayChannelStates(self, states : bool)->None:
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelStates(states)
        return None


    def getSlotsThatMatchStates(self, statesToMatch):
        statesToMatchLogic = {
            "LIMIT_SWITCH"                     : (True,  "limitSwitchState"),
            "LED_STRIP"                        : (True,  "ledStripState"), 
            "BMS"                              : (True,  "bmsSolenoidState"),
            "DOOR_LOCK"                        : (True,  "doorLockSolenoidState"),
            "BATTERY_LOCK"                     : (True,  "batteryLockSolenoidState"),

            "BATTERY_IN_SLOT"                  : (True,  "limitSwitchState"),
            "BATTERY_BMS_IS_ON"                : (True,  "bmsSolenoidState"),
            "BATTERY_BMS_HAS_CAN_BUS_ERROR"    : (True,  "batteryCanBusErrorState"),
            "BATTERY_IS_WAITING_FOR_ALL_DATA"  : (False, "waitingForAllData"), 
                

            "BATTERY_IS_ADDRESSABLE"           : (False, "isAddressable"),
            "BATTERY_IS_CHARGING"              : (False, "isCharging"),
            "BATTERY_IS_CHARGED"               : (False, "isCharged"),
            "BATTERY_IS_CHARGABLE"             : (False, "isChargable"),
            "BATTERY_HAS_WARNINGS"             : (False, "hasWarnings"),
            "BATTERY_HAS_FATAL_WARNINGS"       : (False, "hasFatalWarnings"),
            "BATTERY_IS_DAMAGED"               : (False, "isDamaged"),
            "BATTERY_IS_DELIVERABLE_TO_USER"   : (False, "isDeliverableToUser")
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
    
    
    def std_setup(self):
        batteries_inSlot = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": True})
        for slotAddress in batteries_inSlot:
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 1)

        self.turnOnLedStripsBasedOnState()
        QTimer.singleShot(5000, self.turnOffAllLedStrips)
        return None
    
    def std_closeEvent(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
        return None
    
    

    def turnOnLedStripsBasedOnState(self):
        batteries_notInSlot = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": False})
        batteries_damaged = self.getSlotsThatMatchStates({"BATTERY_IS_DAMAGED": True})
        batteries_deliverableToUser = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER": True})
        other_batteries = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": True,
                                                        "BATTERY_IS_DELIVERABLE_TO_USER":False, 
                                                        "BATTERY_IS_DAMAGED": False})

        for slotAddress in batteries_notInSlot:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.BLUE)

        for slotAddress in batteries_damaged:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.PURPLE)

        for slotAddress in batteries_deliverableToUser:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.GREEN)

        for slotAddress in other_batteries:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.RED)

        return None


    def turnOffAllLedStrips(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.OFF)
        return None
    
    def startChargeOfSlotBattery(self, slotAddress):


        

        batteryAndDoorSolenoidsAreOn = self.modules[slotAddress].batteryAndDoorSolenoidsAreOn
        batteryIsChargable = 

        if self.modules[slotAddress].batteryAndDoorSolenoidsAreOn and 

        try:
            if self.modules[slotAddress].battery.limitSwitchState = False
            if self.modules[slotAddress].solenoidsStates != [1, 0, 0]:
                msg = "Battery is not secured (or BMS is off). Ignoring command."
                warnings.warn(msg)
                return None
            elif not self.modules[slotAddress].battery.isChargable:
                msg = "Battery is not chargable. Ignoring command."
                warnings.warn(msg)
                return None
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")

        self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
        QTimer.singleShot(330, partial(self.setRelayChannelState, CHANNEL_NAME(slotAddress.value), 1))
        QTimer.singleShot(660, partial(self.setSlotSolenoidState, slotAddress, SOLENOID_NAME.BMS,  1))
        return None
    
    def finishChargeOf










