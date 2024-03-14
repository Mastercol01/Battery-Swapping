import numpy as np
from array import array
from typing import List
from enum import Enum, unique
from collections import deque
from PyQt5.QtCore import pyqtSignal, QObject

from BSS_control.CanUtils import (
    can_frame,
    PRIORITY_LEVEL,
    MODULE_ADDRESS,
    ACTIVITY_CODE,
    ArrayOfBool)


class EightChannelRelaySignals(QObject):
    sendCanMsg_eightChannelRelay = pyqtSignal(str)

class CHANNEL_NAME(Enum):
    CHANNEL0 = 0
    CHANNEL1 = 1
    CHANNEL2 = 2
    CHANNEL3 = 3
    CHANNEL4 = 4
    CHANNEL5 = 5
    CHANNEL6 = 6
    CHANNEL7 = 7

class EightChannelRelay:
    DEQUE_MAXLEN = 5
    SIGNALS = EightChannelRelaySignals()
    CONTROL_CENTER_ADDRESS = MODULE_ADDRESS.CONTROL_CENTER
    EIGHT_CHANNEL_RELAY_ADDRESS = MODULE_ADDRESS.EIGHT_CHANNEL_RELAY

    def __init__(self):
        self.buffers = {name:deque(maxlen=self.DEQUE_MAXLEN) for name in CHANNEL_NAME}
        self.currentGlobalTime = 0
        return None

    def updateStatesFromCanMsg(self, canMsg : can_frame)->None:
        if canMsg.activityCode == ACTIVITY_CODE.net2rpy_STATES_INFO_OF_EIGHT_CHANNEL_RELAY_MODULE:
            for name in CHANNEL_NAME:
                self.buffers[name].append(canMsg.data[name.value])
        return None
    
    def updateCurrentGlobalTime(self, newCurrentGlobalTime):
        self.currentGlobalTime = newCurrentGlobalTime
        return None

    @property
    def channelsStates(self)->ArrayOfBool:
        try:
            res = array("B", [bool(round(np.mean(self.buffers[name]))) for name in CHANNEL_NAME])
        except ValueError:
            res = np.nan
        return res
    

    def sendCanMsg(self, canMsg : can_frame)->None:
        self.SIGNALS.sendCanMsg_eightChannelRelay.emit(canMsg.to_canStr())
        return None
    
    def setChannelState(self, name : CHANNEL_NAME, state : bool)->None:
        data = [name.value, state, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_SET_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                            self.EIGHT_CHANNEL_RELAY_ADDRESS,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def setChannelStates(self, states : List[bool])->None:
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                            self.EIGHT_CHANNEL_RELAY_ADDRESS,
                                            self.CONTROL_CENTER_ADDRESS,
                                            states)
        self.sendCanMsg(canMsg)
        return None

    def flipChannelState(self, name : CHANNEL_NAME)->None:
        data = [name.value, 0, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_FLIP_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                            self.EIGHT_CHANNEL_RELAY_ADDRESS,
                                            self.CONTROL_CENTER_ADDRESS,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def flipChannelStates(self, flipLogic : List[bool])->None:
        canMsg = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.rpy2net_FLIP_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                            self.EIGHT_CHANNEL_RELAY_ADDRESS,
                                            self.CONTROL_CENTER_ADDRESS,
                                            flipLogic)
        self.sendCanMsg(canMsg)
        return None

    

    def _debugPrint(self):
        print("----MODULE TO CONTROL ----")
        print(f"moduleAddressToControl: {self.EIGHT_CHANNEL_RELAY_ADDRESS}")

        print()

        print("----- BUFFERS -----")
        for key, val in self.buffers.items():
            print(f"{key}: {val}")

        print()

        print("----- ATTRIBUTES -----")
        print(f"channelsStates: {self.channelsStates}")

        print()

        print("-----TIMERS-----")
        print(f"currentGlobalTime: {self.currentGlobalTime}")

        print()
        return None
    
    