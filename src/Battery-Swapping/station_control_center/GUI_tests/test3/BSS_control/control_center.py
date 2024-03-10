
from typing import List, Dict
import CanUtils as canUtils
from battery import BATTERY_WARNINGS
from CanUtils import can_frame, CanStr
from eight_channel_relay import EightChannelRelay
from battery_slot import BatterySlot, LED_STRIP_STATE, SOLENOID_NAME



class ControlCenter:
    SLOT_ADDRESSES = [canUtils.MODULE_ADDRESS(i) for i in [1,4,5,8]]
    CONTROL_CENTER_ADDRESS = canUtils.MODULE_ADDRESS.CONTROL_CENTER
    EIGHT_CHANNEL_RELAY_ADDRESS = canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY
    FATAL_BATTERY_WARNINGS = set()

    def __init__(self):
        self.modules = {address:BatterySlot(address) for address in self.SLOT_ADDRESSES}
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS] = EightChannelRelay()
        self.currentGlobalTime = 0
        return None
    
    def updateStatesFromCanStr(self, canStr : CanStr)->None:
        canMsg = can_frame.from_canStr(canStr)
        if canMsg.destinationAddress == self.CONTROL_CENTER_ADDRESS:
            self.modules[canMsg.originAddress].updateStatesFromCanMsg(canMsg)
        return None
    
    def updateCurrentGlobalTimeForAllModules(self, newCurrentGlobalTime : float)->None:
        self.currentGlobalTime = newCurrentGlobalTime
        for address in self.SLOT_ADDRESSES:
            self.modules[address].currentGlobalTime = self.currentGlobalTime
            self.modules[address].battery.currentGlobalTime = self.currentGlobalTime
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].currentGlobalTime = self.currentGlobalTime
        return None
    

    def getSlotsThatMatchStates(self, statesToMatch):
        statesToMatch_ = {
            "LIMIT_SWITCH"                     : None,
            "LED_STRIP"                        : None,
            "BMS"                              : None,
            "DOOR_LOCK"                        : None,
            "BATTERY_LOCK"                     : None,

            "BATTERY_IN_SLOT"                  : None,
            "BATTERY_BMS_IS_ON"                : None,
            "BATTERY_IS_WAITING_FOR_ALL_DATA"  : None,
            "BATTERY_BMS_HAS_CAN_BUS_ERROR"    : None,

            "BATTERY_IS_ADDRESSABLE"           : None,
            "BATTERY_IS_CHARGING"              : None,
            "BATTERY_IS_CHARGED"               : None,
            "BATTERY_HAS_WARNINGS"             : None,
            "BATTERY_HAS_FATAL_WARNINGS"       : None,
            "BATTERY_IS_DAMAGED"               : None,
            "BATTERY_IS_DELIVERABLE_TO_USER"   : None
        } 
        ALLOWED_KEYS = statesToMatch_.keys()
        statesToMatch_.update(statesToMatch)
        statesToMatch_ = {key:value for key,value in ALLOWED_KEYS if value is not None}
        res = [slotAddress for slotAddress in self.SLOT_ADDRESSES]

        for stateKeyword, stateValueToMatch in statesToMatch_.items():

            if len(res) < 1:
                break

            if stateKeyword in ["LIMIT_SWITCH", "BATTERY_IN_SLOT"]:
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].limitSwitchState == stateValueToMatch]

            elif stateKeyword == "LED_STRIP":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].ledStripState == stateValueToMatch]

            elif stateKeyword in ["BMS", "BATTERY_BMS_IS_ON"]:
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.BMS] == stateValueToMatch]

            elif stateKeyword == "DOOR_LOCK":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.DOOR_LOCK] == stateValueToMatch]

            elif stateKeyword == "BATTERY_LOCK":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.BATTERY_LOCK] == stateValueToMatch]

            elif stateKeyword == "BATTERY_IS_WAITING_FOR_ALL_DATA":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.waitingForAllData == stateValueToMatch]

            elif stateKeyword == "BATTERY_BMS_HAS_CAN_BUS_ERROR":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.bmsHasCanBusError == stateValueToMatch]

            elif stateKeyword == "BATTERY_IS_ADDRESSABLE":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.isAddressable == stateValueToMatch]

            elif stateKeyword == "BATTERY_IS_CHARGING":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.isCharging == stateValueToMatch]

            elif stateKeyword == "BATTERY_IS_CHARGED":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.isCharged == stateValueToMatch]

            elif stateKeyword == "BATTERY_HAS_WARNINGS":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.hasWarnings == stateValueToMatch]

            elif stateKeyword == "BATTERY_HAS_FATAL_WARNINGS":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.hasFatalWarnings == stateValueToMatch]

            elif stateKeyword == "BATTERY_IS_DAMAGED":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.isDamaged == stateValueToMatch]

            elif stateKeyword == "BATTERY_IS_DELIVERABLE_TO_USER":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.isDeliverableToUser == stateValueToMatch]

        return res
    

    def turnOnLedStripsBasedOnState(self):
        batteries_notInSlot = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": False})
        batteries_damaged = self.getSlotsThatMatchStates({"BATTERY_IS_DAMAGED": True})
        batteries_deliverableToUser = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER": True})
        other_batteries = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": True, "BATTERY_IS_DELIVERABLE_TO_USER":False, "BATTERY_IS_DAMAGED": False})

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
    

