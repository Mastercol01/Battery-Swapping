import numpy as np
from array import array
from typing import List
from enum import Enum, unique
from collections import deque
from BSS_control.battery import Battery
from PyQt5.QtCore import pyqtSignal, QObject

from BSS_control.CanUtils import (
    can_frame,
    PRIORITY_LEVEL,
    MODULE_ADDRESS,
    ACTIVITY_CODE,
    ArrayOfBool)



class BatterySlotSignals(QObject):
    sendCanMsg_slot1 = pyqtSignal(str)
    sendCanMsg_slot2 = pyqtSignal(str)
    sendCanMsg_slot3 = pyqtSignal(str)
    sendCanMsg_slot4 = pyqtSignal(str)
    sendCanMsg_slot5 = pyqtSignal(str)
    sendCanMsg_slot6 = pyqtSignal(str)
    sendCanMsg_slot7 = pyqtSignal(str)
    sendCanMsg_slot8 = pyqtSignal(str)

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
    CONTROL_CENTER_ADDRESS = MODULE_ADDRESS.CONTROL_CENTER

    SIGNALS_DICT = {
        MODULE_ADDRESS.SLOT1 : SIGNALS.sendCanMsg_slot1,
        MODULE_ADDRESS.SLOT2 : SIGNALS.sendCanMsg_slot2,
        MODULE_ADDRESS.SLOT3 : SIGNALS.sendCanMsg_slot3,
        MODULE_ADDRESS.SLOT4 : SIGNALS.sendCanMsg_slot4,
        MODULE_ADDRESS.SLOT5 : SIGNALS.sendCanMsg_slot5,
        MODULE_ADDRESS.SLOT6 : SIGNALS.sendCanMsg_slot6,
        MODULE_ADDRESS.SLOT7 : SIGNALS.sendCanMsg_slot7,
        MODULE_ADDRESS.SLOT8 : SIGNALS.sendCanMsg_slot8
    }


    def __init__(self, moduleAddressToControl : MODULE_ADDRESS):
        self.moduleAddressToControl = moduleAddressToControl
        self.buffers = {
        "limitSwitchState"        : deque(maxlen=self.DEQUE_MAXLEN),
        "batteryCanBusErrorState" : deque(maxlen=self.DEQUE_MAXLEN),
        "ledStripState"           : deque(maxlen=self.DEQUE_MAXLEN),
        "solenoidsStates"         : {SOLENOID_NAME.BMS          : deque(maxlen=self.DEQUE_MAXLEN),
                                     SOLENOID_NAME.DOOR_LOCK    : deque(maxlen=self.DEQUE_MAXLEN),
                                     SOLENOID_NAME.BATTERY_LOCK : deque(maxlen=self.DEQUE_MAXLEN)},
        }
        self.battery = Battery(self.moduleAddressToControl)
        self.currentGlobalTime = 0
        return None

    def updateStatesFromCanMsg(self, canMsg : can_frame)->None:
        if canMsg.activityCode == ACTIVITY_CODE.net2rpy_PERIPHERALS_STATES_OF_BATTERY_SLOT_MODULE:
            self.buffers["limitSwitchState"].append(canMsg.data[0])
            self.buffers["ledStripState"].append(canMsg.data[1])
            self.buffers["solenoidsStates"][SOLENOID_NAME.BMS].append(canMsg.data[2])
            self.buffers["solenoidsStates"][SOLENOID_NAME.DOOR_LOCK].append(canMsg.data[3])
            self.buffers["solenoidsStates"][SOLENOID_NAME.BATTERY_LOCK].append(canMsg.data[4])
            self.buffers["batteryCanBusErrorState"].append(canMsg.data[5])
        else:
            self.battery.updateStatesFromCanMsg(canMsg)

        try:
            self.battery.updateStatesFromBatterySlotModule(self.limitSwitchState, 
                                                           self.batteryCanBusErrorState,
                                                           self.solenoidsStates[SOLENOID_NAME.BMS.value])
        except TypeError:
            pass
        return None
    
    def updateCurrentGlobalTime(self, newCurrentGlobalTime : float)->None:
        self.currentGlobalTime = newCurrentGlobalTime
        self.battery.updateCurrentGlobalTime(newCurrentGlobalTime)
        return None 


    @property
    def limitSwitchState(self)->bool | float:
        try:
            res = bool(round(np.mean(self.buffers["limitSwitchState"])))
        except ValueError:
            res = np.nan
        return res
    
    @property
    def ledStripState(self)->LED_STRIP_STATE | float:
        try:
            res = LED_STRIP_STATE(round(np.mean(self.buffers["ledStripState"])))
        except ValueError:
            res = np.nan
        return res
    
    @property
    def solenoidsStates(self)->ArrayOfBool | float:
        try:
            res = array("B",[
            bool(round(np.mean(self.buffers["solenoidsStates"][SOLENOID_NAME.BMS]))),
            bool(round(np.mean(self.buffers["solenoidsStates"][SOLENOID_NAME.DOOR_LOCK]))),
            bool(round(np.mean(self.buffers["solenoidsStates"][SOLENOID_NAME.BATTERY_LOCK])))
            ])
        except ValueError:
            res = np.nan
        return res
    @property
    def bmsSolenoidState(self):
        try: res = self.solenoidsStates[SOLENOID_NAME.BMS]
        except TypeError: res = np.nan
        return res    
    @property
    def doorLockSolenoidState(self):
        try: res = self.solenoidsStates[SOLENOID_NAME.DOOR_LOCK]
        except TypeError: res = np.nan
        return res
    @property
    def batteryLockSolenoidState(self):
        try: res = self.solenoidsStates[SOLENOID_NAME.BATTERY_LOCK]
        except TypeError: res = np.nan
        return res
    
    @property
    def batteryCanBusErrorState(self)->bool | float:
        try:
            res = bool(round(np.mean(self.buffers["batteryCanBusErrorState"])))
        except ValueError:
            res = np.nan
        return res
    
    @property
    def batteryAndDoorSolenoidsAreOn(self):
        res = self.solenoidsStates
        return res[1] and res[2]
    
    def sendCanMsg(self, canMsg : can_frame)->None:
        self.SIGNALS_DICT[self.moduleAddressToControl].emit(canMsg.to_canStr())
        return None
    
    def setSolenoidState(self, name : SOLENOID_NAME, state : bool)->None:
        data = [name.value, state, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_SET_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def setSolenoidsStates(self, states : List[bool]):
        if len(states)!=3:
            raise ValueError("'states' must be a list/array of length 3")
        
        data = [states[0], states[1], states[2], 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_SET_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None

    def flipSolenoidState(self, name : SOLENOID_NAME):
        data = [name.value, 0, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_FLIP_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def flipSolenoidStates(self, flipLogic : List[bool]):
        if len(flipLogic)!=3:
            raise ValueError("'flipLogic' must be a list/array of length 3")
        
        data = [flipLogic[0], flipLogic[1], flipLogic[2], 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_FLIP_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None

    def setLedStripState(self, state : LED_STRIP_STATE):
        data = [state.value, 0, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def resetBatteryCanBusErrorAndTimer(self):
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE,
                                            self.moduleAddressToControl,
                                            self.CONTROL_CENTER_ADDRESS)
        self.sendCanMsg(canMsg)
        return None

    

    def _debugPrint(self):
        print()

        print(f"--------- MODULE TO CONTROL:  {self.moduleAddressToControl} ---------")
  
        print()

        print("----- BUFFERS -----")
        for key, val in self.buffers.items():
            print(f"{key}: {val}")

        print()

        print("----- ATTRIBUTES -----")
        print(f"limitSwitchState: {self.limitSwitchState}")
        print(f"ledStripState: {self.ledStripState}")
        print(f"solenoidsStates: {self.solenoidsStates}")
        print(f"batteryCanBusErrorState: {self.batteryCanBusErrorState}")

        print()

        print("-----TIMERS-----")
        print(f"currentGlobalTime: {self.currentGlobalTime}")

        print()

        return None

