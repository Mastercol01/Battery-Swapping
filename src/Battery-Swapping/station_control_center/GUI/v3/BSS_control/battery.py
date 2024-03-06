import numpy as np
import CanUtils as canUtils
from itertools import islice
from collections import deque
from operator import itemgetter
from typing import Deque, Tuple
from enum import Enum, unique, auto
from CanUtils import can_frame, uint32_t, uint8_t, CanStr

@unique
class BATTERY_WARNINGS(Enum):
    CELL_OVERVOLTAGE_WARNING                    = 0
    CELL_OVERVOLTAGE_PROTECTION                 = 1
    CELL_UNDERVOLTAGE_WARNING                   = 2
    CELL_UNDERVOLTAGE_PROTECTION                = 3
    PACK_VOLTAGE_OVERVOLTAGE_WARNING            = 4
    PACK_VOLTAGE_OVERVOLTAGE_PROTECTION         = 5
    PACK_UNDERVOLTAGE_WARNING                   = 6
    PACK_UNDERVOLTAGE_PROTECTION                = 7
    CHARGING_HIGH_TEMPERATURE_WARNING           = 8
    CHARGING_HIGH_TEMPERATURE_PROTECTION        = 9
    CHARGING_LOW_TEMPERATURE_WARNING            = 10
    CHARGING_LOW_TEMPERATURE_PROTECTION         = 11
    DISCHARGE_HIGH_TEMPERATURE_WARNING          = 12
    DISCHARGE_HIGH_TEMPERATURE_PROTECTION       = 13
    DISCHARGE_LOW_TEMPERATURE_WARNING           = 14
    DISCHARGE_LOW_TEMPERATURE_PROTECTION        = 15
    CHARGING_OVERCURRENT_WARNING                = 16
    CHARGING_OVERCURRENT_PROTECTION             = 17
    DISCHARGE_OVERCURRENT_WARNING               = 18
    DISCHARGE_OVERCURRENT_PROTECTION            = 19
    SHORT_CIRCUIT_PROTECTION                    = 20
    MOSFET_OVERTEMPERATURE_WARNING              = 21
    MOSFET_OVERTEMPERATURE_PROTECTION           = 22
    EXCESSIVE_DIFFERENTIAL_PRESSURE_WARNING     = 23
    EXCESSIVE_DIFFERENTIAL_PRESSURE_PROTECTION  = 24
    EXCESSIVE_TEMPERATURE_DIFFERENCE_WARNING    = 25
    EXCESSIVE_TEMPERATURE_DIFFERENCE_PROTECTION = 26
    SOC_LOW_ALARM                               = 27
    ACQUISITION_CHIP_FAILURE                    = 28
    CHARGING_SWITCH_STATUS                      = 29
    DISCHARGE_SWITCH_STATUS                     = 30
    STATE_OF_CHARGE                             = 31

@unique
class BATTERY_TEMPERATURES(Enum):
    MOSFET = 0
    NTC1   = 1
    NTC2   = 2
    NTC3   = 3
    NTC4   = 4
    NTC5   = 5
    NTC6   = 6
    


def getBatteryGeneralStatusFromCanMsg(canMsg : can_frame) -> Tuple[float, float, int]:
    if canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0:
        voltage = 0.1*(  (canMsg.data[1] << 8) | canMsg.data[0] )
        current = 0.1*( ((canMsg.data[3] << 8) | canMsg.data[2]) - 32000 )
        soc     = canMsg.data[4]
    return (voltage, current, soc)


def getBatteryWarningsFromCanMsg(canMsg : can_frame) -> Deque[BATTERY_WARNINGS]:
    activeBatteryWarnings = deque()

    if canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0:
        if canMsg.data[5] > 0:
            bitValues = [(((1 << j) & canMsg.data[5]) >> j) for j in range(8)]
            activeBatteryWarnings.extend( [BATTERY_WARNINGS(0 + j) for j in range(8) if bitValues[j]] )

        if canMsg.data[6] > 0:
            bitValues = [(((1 << j) & canMsg.data[6]) >> j) for j in range(8)]
            activeBatteryWarnings.extend( [BATTERY_WARNINGS(8 + j) for j in range(8) if bitValues[j]] )

        if canMsg.data[7] > 0:
            bitValues = [(((1 << j) & canMsg.data[7]) >> j) for j in range(8)]
            activeBatteryWarnings.extend( [BATTERY_WARNINGS(16 + j) for j in range(8) if bitValues[j]] )
                
    elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_1:
        if canMsg.data[0]:
            bitValues = [(((1 << j) & canMsg.data[0]) >> j) for j in range(5)]
            activeBatteryWarnings.extend( [BATTERY_WARNINGS(24 + j) for j in range(5) if bitValues[j]] )

        if canMsg.data[1]:
            bitValues = [(((1 << j) & canMsg.data[1]) >> j) for j in range(5)]
            activeBatteryWarnings.extend( [BATTERY_WARNINGS(29 + j) for j in range(3) if bitValues[j]] )

    return activeBatteryWarnings

def getBatteryMaxTempAndNameFromCanMsg(canMsg : can_frame) -> Tuple[float, BATTERY_TEMPERATURES]:
    res = [0, 0, 0, 0, 0, 0, 0]
    if canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_9:
        res[0] = (canMsg.data[4] - 40, BATTERY_TEMPERATURES.NTC1)
        res[1] = (canMsg.data[5] - 40, BATTERY_TEMPERATURES.NTC2)
        res[2] = (canMsg.data[6] - 40, BATTERY_TEMPERATURES.NTC3)
        res[3] = (canMsg.data[7] - 40, BATTERY_TEMPERATURES.NTC4)
    elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_10:
        res[4] = (canMsg.data[0] - 40, BATTERY_TEMPERATURES.NTC5)
        res[5] = (canMsg.data[1] - 40, BATTERY_TEMPERATURES.NTC6)
        res[7] = (canMsg.data[2] - 40, BATTERY_TEMPERATURES.MOSFET)
    return max(res, itemgetter(0))




               




class Battery:
    DEQUE_MAXLEN = 10
    def __init__(self):
        self.voltage  = deque(maxlen=self.DEQUE_MAXLEN)
        self.current  = deque(maxlen=self.DEQUE_MAXLEN)
        self.soc      = deque(maxlen=self.DEQUE_MAXLEN)
        self.warnings = deque(maxlen=len(BATTERY_WARNINGS))
        self.maxTemp  = deque(maxlen=self.DEQUE_MAXLEN)
        self.maxTempName = None
        
    
if __name__ == "__main__":
    canMsg = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                        canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0,
                                        canUtils.MODULE_ADDRESS.CONTROL_CENTER,
                                        canUtils.MODULE_ADDRESS.SLOT1,
                                        data=[0x77,0x01,0x50,0x7D,78,0,0,0])
    
    print(getBatteryGeneralStatusFromCanMsg(canMsg))

    
