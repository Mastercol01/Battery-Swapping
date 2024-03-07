import numpy as np
import battery as batt
from array import array
from typing import List, Union
import CanUtils as canUtils
from enum import Enum, unique
from collections import deque
from CanUtils import can_frame, ArrayOfBool
from PyQt5.QtCore import pyqtSignal, QObject

class BatterySlotSignals(QObject):
    command = pyqtSignal(str)

@unique
class SOLENOID_NAME(Enum):
    BMS          = 0
    DOOR_LOCK    = 1
    BATTERY_LOCK = 2

@unique
class LED_STRIP_STATE(Enum):
    OFF    = 0
    RED    = 1
    GREEN  = 2
    BLUE   = 3
    PURPLE = 4


class BatterySlot:
    DEQUE_MAXLEN = 5
    SIGNALS = BatterySlotSignals()
    

    def __init__(self, moduleAddressToControl : canUtils.MODULE_ADDRESS):
        self.buffers = {
        "limitSwitchState"        : deque(maxlen=self.DEQUE_MAXLEN),
        "batteryCanBusErrorState" : deque(maxlen=self.DEQUE_MAXLEN),
        "ledStripState"           : deque(maxlen=self.DEQUE_MAXLEN),
        "solenoidsStates"         : {SOLENOID_NAME.BMS          : deque(maxlen=self.DEQUE_MAXLEN),
                                     SOLENOID_NAME.DOOR_LOCK    : deque(maxlen=self.DEQUE_MAXLEN),
                                     SOLENOID_NAME.BATTERY_LOCK : deque(maxlen=self.DEQUE_MAXLEN)},
        }
        self.battery = batt.Battery()
        self.moduleAddressToControl = moduleAddressToControl
        self.moduleAddress = canUtils.MODULE_ADDRESS.CONTROL_CENTER
        

    def updateStatesFromCanMsg(self, canMsg : can_frame)->None:
        if canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_PERIPHERALS_STATES_OF_BATTERY_SLOT_MODULE:
            self.buffers["limitSwitchState"].append(canMsg.data[0])
            self.buffers["ledStripState"].append(canMsg.data[1])
            self.buffers["solenoidsStates"][SOLENOID_NAME.BMS].append(canMsg.data[2])
            self.buffers["solenoidsStates"][SOLENOID_NAME.DOOR_LOCK].append(canMsg.data[3])
            self.buffers["solenoidsStates"][SOLENOID_NAME.BATTERY_LOCK].append(canMsg.data[4])
            self.buffers["batteryCanBusErrorState"].append(canMsg.data[5])

            self.battery.updateStatesFromBatterySlotModule(self.limitSwitchState, 
                                                           self.batteryCanBusErrorState, 
                                                           self.solenoidsStates[0] and self.chargerRelayState,
                                                           self.timeUntilFullBatteryCharge)
        else:
            self.battery.updateStatesFromCanMsg(canMsg)
        return None
     
    def updateStatesFromControlCenter(self, chargerRelayState:bool, timeUntilFullBatteryCharge:Union[float, None])->None:
        self.chargerRelayState = chargerRelayState
        self.timeUntilFullBatteryCharge = timeUntilFullBatteryCharge
        return None
    
    @property
    def limitSwitchState(self)->bool:
        return bool(round(np.mean(self.buffers["limitSwitchState"])))
    
    @property
    def ledStripState(self)->LED_STRIP_STATE:
        return LED_STRIP_STATE(round(np.mean(self.buffers["ledStripState"])))
    
    @property
    def solenoidsStates(self)->ArrayOfBool:
        solenoidsStates_ = array("B",[
        bool(round(np.mean(self.buffers["solenoidsStates"][SOLENOID_NAME.BMS]))),
        bool(round(np.mean(self.buffers["solenoidsStates"][SOLENOID_NAME.DOOR_LOCK]))),
        bool(round(np.mean(self.buffers["solenoidsStates"][SOLENOID_NAME.BATTERY_LOCK])))
        ])
        return solenoidsStates_
    
    @property
    def batteryCanBusErrorState(self)->bool:
        return bool(round(np.mean(self.buffers["batteryCanBusErrorState"])))
    
    def sendCanMsg(self, canMsg : can_frame)->None:
        self.SIGNALS.command.emit(canMsg.to_canStr())
        return None
    
    def setSolenoidState(self, name : SOLENOID_NAME, state : bool)->None:
        data = [name.value, state, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_SET_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def setSolenoidsStates(self, states : List[bool]):
        if len(states)!=3:
            raise ValueError("'states' must be a list/array of length 3")
        
        data = [states[0], states[1], states[2], 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_SET_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress,
                                            data)
        self.sendCanMsg(canMsg)
        return None

    def flipSolenoidState(self, name : SOLENOID_NAME):
        data = [name.value, 0, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_FLIP_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def flipSolenoidStates(self, states : List[bool]):
        if len(states)!=3:
            raise ValueError("'states' must be a list/array of length 3")
        
        data = [states[0], states[1], states[2], 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_FLIP_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress,
                                            data)
        self.sendCanMsg(canMsg)
        return None

    def setLedStripState(self, name : LED_STRIP_STATE):
        data = [name.value, 0, 0, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def resetBatteryCanBusErrorAndTimer(self):
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress)
        self.sendCanMsg(canMsg)
        return None
    
    def lockBatteryAndDoor(self):
        self.setSolenoidState(SOLENOID_NAME.BATTERY_LOCK, 0)
        self.setSolenoidState(SOLENOID_NAME.DOOR_LOCK, 0)
        return None
    
    def unlockBatteryAndDoor(self):
        self.setSolenoidState(SOLENOID_NAME.BATTERY_LOCK, 1)
        self.setSolenoidState(SOLENOID_NAME.DOOR_LOCK, 1)
        return None


