import warnings
import BSS_control.CanUtils as canUtils
from typing import List, Dict, Callable
from BSS_control.battery import BATTERY_WARNINGS
from BSS_control.CanUtils import can_frame, CanStr
from BSS_control.eight_channel_relay import EightChannelRelay
from BSS_control.battery_slot import BatterySlot, LED_STRIP_STATE, SOLENOID_NAME



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
        ALLOWED_KEYS = [
            "LIMIT_SWITCH"                     ,
            "LED_STRIP"                        ,
            "BMS"                              ,
            "DOOR_LOCK"                        ,
            "BATTERY_LOCK"                     ,

            "BATTERY_IN_SLOT"                  ,
            "BATTERY_BMS_IS_ON"                ,
            "BATTERY_IS_WAITING_FOR_ALL_DATA"  ,
            "BATTERY_BMS_HAS_CAN_BUS_ERROR"    ,

            "BATTERY_IS_ADDRESSABLE"           ,
            "BATTERY_IS_CHARGING"              ,
            "BATTERY_IS_CHARGED"               ,
            "BATTERY_IS_CHARGABLE"             ,
            "BATTERY_HAS_WARNINGS"             ,
            "BATTERY_HAS_FATAL_WARNINGS"       ,
            "BATTERY_IS_DAMAGED"               ,
            "BATTERY_IS_DELIVERABLE_TO_USER"   
        ]
        statesToMatch_ = {key:value for key,value in statesToMatch.items() if key in ALLOWED_KEYS}
        res = [slotAddress for slotAddress in self.SLOT_ADDRESSES]

        for stateKeyword, stateValueToMatch in statesToMatch_.items():

            if len(res) < 1:
                break

            if stateKeyword in ["LIMIT_SWITCH", "BATTERY_IN_SLOT"]:
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].limitSwitchState == stateValueToMatch]

            elif stateKeyword == "LED_STRIP":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].ledStripState == stateValueToMatch]

            elif stateKeyword in ["BMS", "BATTERY_BMS_IS_ON"]:
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.BMS.value] == stateValueToMatch]

            elif stateKeyword == "DOOR_LOCK":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.DOOR_LOCK.value] == stateValueToMatch]

            elif stateKeyword == "BATTERY_LOCK":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.BATTERY_LOCK.value] == stateValueToMatch]

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

            elif stateKeyword == "BATTERY_IS_CHARGABLE":
                res = [slotAddress for slotAddress in res if self.modules[slotAddress].battery.isChargable == stateValueToMatch]

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
    

