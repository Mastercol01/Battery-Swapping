
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
    

    def getSlotsThatMatchStates(self, matchStates : Dict):

        matchStates_ = {
            "LIMIT_SWITCH"                     : None,
            "LED_STRIP"                        : None,
            "BMS"                              : None,
            "DOOR_LOCK"                        : None,
            "BATTERY_LOCK"                     : None,
            "BATTERY_CAN_BUS_ERROR"            : None,
            "BATTERY_IS_WAITING_FOR_ALL_DATA"  : None,
            "BATTERY_HAS_NO_FATAL_WARNINGS"    : None
        }
        ALLOWED_KEYS = matchStates_.keys()
        matchStates_.update(matchStates)
        matchStates_ = {key:value for key,value in matchStates_.items()
                        if key in ALLOWED_KEYS and value is not None}

        retrieverFuncs = {
            "LIMIT_SWITCH"                     : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].limitSwitchState == matchStates_["LIMIT_SWITCH"]},
            "LED_STRIP"                        : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].ledStripState == matchStates_["LED_STRIP"]},
            "BMS"                              : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.BMS]== matchStates_["BMS"]},
            "DOOR_LOCK"                        : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.DOOR_LOCK] == matchStates_["DOOR_LOCK"]},
            "BATTERY_LOCK"                     : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].solenoidsStates[SOLENOID_NAME.BATTERY_LOCK] == matchStates_["BATTERY_LOCK"]},
            "BATTERY_CAN_BUS_ERROR"            : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].batteryCanBusErrorState == matchStates_["BATTERY_CAN_BUS_ERROR"]},
            "BATTERY_IS_WAITING_FOR_ALL_DATA"  : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].battery.waitingForAllData == matchStates_["BATTERY_IS_WAITING_FOR_ALL_DATA"]},
            "BATTERY_HAS_NO_FATAL_WARNINGS"    : lambda:{slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].battery.warnings.isdisjoint(self.FATAL_BATTERY_WARNINGS)},
        }

        return set.intersection(*[retrieverFuncs[key]() for key in matchStates_.keys()])


    def getEmptySlots(self):
        return self.getSlotsThatMatchStates({"LIMIT_SWITCH":1})

    def getOccupiedSlots(self):
        return self.getSlotsThatMatchStates({"LIMIT_SWITCH":0})
        


        

        
    

"""
def getEmptySlots(self)->List[canUtils.MODULE_ADDRESS]:
    return [slotAddress for slotAddress in self.SLOT_ADDRESSES if not self.modules[slotAddress].battery.inSlot]

def getOccupiedSlots(self)->List[canUtils.MODULE_ADDRESS]:
    return [slotAddress for slotAddress in self.SLOT_ADDRESSES if self.modules[slotAddress].battery.inSlot]


        
def getOccupiedSlotsWithAddressableAndSafeBatteries(self)->List[canUtils.MODULE_ADDRESS]:
    return [slotAddress for slotAddress in self.getOccupiedSlots() if not self.modules[slotAddress].battery.bmsHasCanBusError and 
                                                                        not self.modules[slotAddress].battery.waitingForAllData and 
                                                                        self.modules[slotAddress].battery.bmsState              and
                                                                        self.modules[slotAddress].battery.warnings.isdisjoint(self.FATAL_BATTERY_WARNINGS)]

def getOccupiedSlotsWithoutAddressableOrSafeBatteries(self)->List[canUtils.MODULE_ADDRESS]:
    return [slotAddress for slotAddress in self.getOccupiedSlots() if not self.modules[slotAddress].battery.waitingForAllData and 
                                                                        self.modules[slotAddress].battery.bmsState              and
                                                                        (self.modules[slotAddress].battery.bmsHasCanBusError    or
                                                                        not self.modules[slotAddress].battery.warnings.isdisjoint(self.FATAL_BATTERY_WARNINGS))]
    
def turnOffAllLedStrips(self)->None:
    for slotAddress in self.SLOT_ADDRESSES:
        self.modules[slotAddress].setLedStripState(LED_STRIP_STATE.OFF)
    return None

def turnOnAllLedStripsBasedOnSlotState(self)->None:
    emptySlots = self.getEmptySlots()
    occupiedSlotsWithoutAddressableOrSafeBatteries = self.getOccupiedSlotsWithoutAddressableOrSafeBatteries()
    return None

"""
        



"""
def prepareToAdmitBatteryFromUser(self, slotAddress : canUtils.MODULE_ADDRESS):
    if slotAddress in [self.EIGHT_CHANNEL_RELAY_ADDRESS, self.CONTROL_CENTER_ADDRESS]:
        raise ValueError("'slotAddress' must be the address of a battery slot module")
    
    elif self.modules[slotAddress].limitSwitchState:
        raise Exception("SLOT MODULE CAN'T FIT ANOTHER BATTERY INSIDE!")


    self.modules[slotAddress].unlockBatteryAndDoor()
    self.modules[slotAddress].setLedStripState(bslot.LED_STRIP_STATE.BLUE)
    return None


def beginBatteryCharge(self, slotAddress : canUtils.MODULE_ADDRESS):
    if slotAddress in [self.EIGHT_CHANNEL_RELAY_ADDRESS, self.CONTROL_CENTER_ADDRESS]:
        raise ValueError("'slotAddress' must be the address of a battery slot module")
    
    elif not self.modules[slotAddress].limitSwitchState:
        raise Exception("NO BATTERY TO CHARGE!")
    
    elif self.modules[slotAddress].battery.isCharging:
        raise Exception("BATTERY IS ALREADY CHARGING!")
    
    self.modules[slotAddress].setSolenoidState(bslot.SOLENOID_NAME.BMS, 0)
    QTimer().singleShot(1500, partial(self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelState, ecrelay.CHANNEL_NAME(slotAddress-1), 0))
    QTimer().singleShot(1500, partial(self.modules[slotAddress].setSolenoidState, bslot.SOLENOID_NAME.BMS, 1))
    return None
"""

