import warnings
from typing import Callable
from BSS_control.eight_channel_relay import EightChannelRelay

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
    
    def connect_sendCanMsg(self, sendCanMsg_func : Callable[[CanStr],None])->None:
        for address in self.SLOT_ADDRESSES:
            self.modules[address].SIGNALS_DICT[address].connect(sendCanMsg_func)
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].SIGNALS.sendCanMsg_eightChannelRelay.connect(sendCanMsg_func)
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

    
    

    def turnOnLedStripsBasedOnState(self):
        batteries_notInSlot = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": False})
        batteries_damaged = self.getSlotsThatMatchStates({"BATTERY_IS_DAMAGED": True})
        batteries_deliverableToUser = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER": True})
        other_batteries = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": True,
                                                        "BATTERY_IS_DELIVERABLE_TO_USER":False, 
                                                        "BATTERY_IS_DAMAGED": False})

        print(batteries_notInSlot)
        print(batteries_damaged)
        print(batteries_deliverableToUser)
        print(other_batteries)

        for slotAddress in batteries_notInSlot:
            self.modules[slotAddress].setLedStripState(LED_STRIP_STATE.BLUE)

        for slotAddress in batteries_damaged:
            self.modules[slotAddress].setLedStripState(LED_STRIP_STATE.PURPLE)

        for slotAddress in batteries_deliverableToUser:
            self.modules[slotAddress].setLedStripState(LED_STRIP_STATE.GREEN)

        for slotAddress in other_batteries:
            self.modules[slotAddress].setLedStripState(LED_STRIP_STATE.RED)

        return None


    def turnOffAllLedStrips(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.modules[slotAddress].setLedStripState(LED_STRIP_STATE.OFF)
        return None
    

