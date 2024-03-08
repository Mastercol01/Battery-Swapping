import numpy as np
from array import array
import CanUtils as canUtils
from enum import Enum, unique
from collections import deque
from typing import List, Union
from CanUtils import can_frame, ArrayOfBool
from PyQt5.QtCore import pyqtSignal, QObject

class BatterySlotSignals(QObject):
    command = pyqtSignal(str)

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
    SIGNALS = BatterySlotSignals()

    def __init__(self):
        self.buffers = {name:deque(maxlen=self.DEQUE_MAXLEN) for name in CHANNEL_NAME}
        self.moduleAddress = canUtils.MODULE_ADDRESS.CONTROL_CENTER
        self.moduleAddressToControl = canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY
        return None

    def updateStatesFromCanMsg(self, canMsg : can_frame)->None:
        if canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_STATES_INFO_OF_EIGHT_CHANNEL_RELAY_MODULE:
            for name in CHANNEL_NAME:
                self.buffers[name].append(canMsg.data[name.value])
        return None
    

    @property
    def channelsStates(self)->ArrayOfBool:
        return array("B", [bool(round(np.mean(self.buffers[name]))) for name in CHANNEL_NAME])
    


    def sendCanMsg(self, canMsg : can_frame)->None:
        self.SIGNALS.command.emit(canMsg.to_canStr())
        return None
    
    def setChannelState(self, name : CHANNEL_NAME, state : bool)->None:
        data = [name.value, state, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.rpy2net_SET_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                            self.moduleAddressToControl,
                                            self.moduleAddress,
                                            data)
        self.sendCanMsg(canMsg)
        return None
    
    def setChannelStates(self, states : List[bool])->None:
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                    canUtils.ACTIVITY_CODE.rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                    self.moduleAddressToControl,
                                    self.moduleAddress,
                                    states)
        self.sendCanMsg(canMsg)
        return None

    def flipChannelState(self, name : CHANNEL_NAME)->None:
        data = [name.value, 0, 0, 0, 0, 0, 0, 0]
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                    canUtils.ACTIVITY_CODE.rpy2net_FLIP_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                    self.moduleAddressToControl,
                                    self.moduleAddress,
                                    data)
        self.sendCanMsg(canMsg)
        return None
    
    def flipChannelStates(self, flipLogic : List[bool])->None:
        canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                    canUtils.ACTIVITY_CODE.rpy2net_FLIP_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                    self.moduleAddressToControl,
                                    self.moduleAddress,
                                    flipLogic)
        self.sendCanMsg(canMsg)
        return None

    

    
