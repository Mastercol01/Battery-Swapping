import numpy as np
import CanUtils as canUtils
from collections import deque
from CanUtils import can_frame
from enum import Enum, unique
from typing import Deque, Tuple, Set, Dict



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



# canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0
def getBatteryGeneralStatusFromCanMsg(canMsg : can_frame) -> Tuple[float, float, int]:
    voltage = 0.1*(  (canMsg.data[1] << 8) | canMsg.data[0] )
    current = 0.1*( ((canMsg.data[3] << 8) | canMsg.data[2]) - 32000 )
    soc     = canMsg.data[4]
    return (voltage, current, soc)


# canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0
def getBatteryWarningsFromCanMsg_part1(canMsg : can_frame) -> Deque[BATTERY_WARNINGS]:
    activeBatteryWarnings = deque()

    if canMsg.data[5] > 0:
        bitValues = [(((1 << j) & canMsg.data[5]) >> j) for j in range(8)]
        activeBatteryWarnings.extend( [BATTERY_WARNINGS(0 + j) for j in range(8) if bitValues[j]] )

    if canMsg.data[6] > 0:
        bitValues = [(((1 << j) & canMsg.data[6]) >> j) for j in range(8)]
        activeBatteryWarnings.extend( [BATTERY_WARNINGS(8 + j) for j in range(8) if bitValues[j]] )

    if canMsg.data[7] > 0:
        bitValues = [(((1 << j) & canMsg.data[7]) >> j) for j in range(8)]
        activeBatteryWarnings.extend( [BATTERY_WARNINGS(16 + j) for j in range(8) if bitValues[j]] )

    return activeBatteryWarnings


# canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_1
def getBatteryWarningsFromCanMsg_part2(canMsg : can_frame) -> Deque[BATTERY_WARNINGS]:
    activeBatteryWarnings = deque()

    if canMsg.data[0]:
        bitValues = [(((1 << j) & canMsg.data[0]) >> j) for j in range(5)]
        activeBatteryWarnings.extend( [BATTERY_WARNINGS(24 + j) for j in range(5) if bitValues[j]] )

    if canMsg.data[1]:
        bitValues = [(((1 << j) & canMsg.data[1]) >> j) for j in range(3)]
        activeBatteryWarnings.extend( [BATTERY_WARNINGS(29 + j) for j in range(3) if bitValues[j]] )

    return activeBatteryWarnings


# canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_9
def getBatteryTemps_part1(canMsg : can_frame) -> Tuple[float, float, float, float]:
    return (canMsg.data[4] - 40, canMsg.data[5] - 40, canMsg.data[6] - 40, canMsg.data[7] - 40)


# canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_10
def getBatteryTemps_part2(canMsg : can_frame) -> Tuple[float, float, float]:
    return (canMsg.data[0] - 40, canMsg.data[1] - 40, canMsg.data[2] - 40)




class Battery:
    DEQUE_MAXLEN = 10
    def __init__(self):
        self.buffers = {
            "voltage"  : deque(maxlen=self.DEQUE_MAXLEN),
            "current"  : deque(maxlen=self.DEQUE_MAXLEN),
            "soc"      : deque(maxlen=self.DEQUE_MAXLEN),
            "warnings" : deque(maxlen=len(BATTERY_WARNINGS)),
            "NTC1"     : deque(maxlen=self.DEQUE_MAXLEN),
            "NTC2"     : deque(maxlen=self.DEQUE_MAXLEN),
            "NTC3"     : deque(maxlen=self.DEQUE_MAXLEN),
            "NTC4"     : deque(maxlen=self.DEQUE_MAXLEN),
            "NTC5"     : deque(maxlen=self.DEQUE_MAXLEN),
            "NTC6"     : deque(maxlen=self.DEQUE_MAXLEN),
            "MOSFET"   : deque(maxlen=self.DEQUE_MAXLEN),
        }
        return None

    def updateStatesFromCanMsg(self, canMsg : can_frame)->None:

        if canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0:
            (voltage_,current_,soc_) = getBatteryGeneralStatusFromCanMsg(canMsg)
            self.buffers["warnings"].extend(getBatteryWarningsFromCanMsg_part1(canMsg))
            self.buffers["voltage"].append(voltage_)
            self.buffers["current"].append(current_)
            self.buffers["soc"].append(soc_)

        elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_1:
            self.buffers["warnings"].extend(getBatteryWarningsFromCanMsg_part2(canMsg))

        elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_9:
            ntc1_, ntc2_, ntc3_, ntc4_ = getBatteryTemps_part1(canMsg) 
            self.buffers["NTC1"].append(ntc1_)
            self.buffers["NTC2"].append(ntc2_)
            self.buffers["NTC3"].append(ntc3_)
            self.buffers["NTC4"].append(ntc4_)

        elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_10:
            ntc5_, ntc6_, mosfet = getBatteryTemps_part2(canMsg) 
            self.buffers["NTC5"].append(ntc5_)
            self.buffers["NTC6"].append(ntc6_)
            self.buffers["MOSFET"].append(mosfet)

        return None
    
    @property
    def voltage(self)->float:
        return np.mean(self.buffers["voltage"])

    @property
    def current(self)->float:
        return np.mean(self.buffers["current"])
    
    @property
    def soc(self)->float:
        return np.mean(self.buffers["soc"])
    
    @property
    def warnings(self)->Set[BATTERY_WARNINGS]:
        return set(self.buffers["warnings"])
    
    @property
    def temps(self)->Dict[str, float]:
        return {key:np.mean(val) for key,val in self.buffers.items() if key not in ["voltage", "current", "soc", "warnings"]}
    
    @property
    def maxTemp(self)->Dict[str, float]:
        temperatures = self.temps
        maxTemperatureKey = max(temperatures, key=temperatures.get)
        return {maxTemperatureKey:temperatures[maxTemperatureKey]}
    
    def clearBuffers(self)->None:
        for key in self.buffers.keys():
            self.buffers[key].clear()



        
    
if __name__ == "__main__":
    Battery_obj = Battery()

    canMsgs = [0, 0, 0, 0]
    canMsgs[0] = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_0,
                                            canUtils.MODULE_ADDRESS.CONTROL_CENTER,
                                            canUtils.MODULE_ADDRESS.SLOT1,
                                            data=[0x77,0x01,0x50,0x7D,78,0b10000000,0b10000000,0b10000000])
    
    canMsgs[1] = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_1,
                                            canUtils.MODULE_ADDRESS.CONTROL_CENTER,
                                            canUtils.MODULE_ADDRESS.SLOT1,
                                            data=[0b00010000,0b00000100,0,0,0,0,0,0])
    
    canMsgs[2] = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_9,
                                            canUtils.MODULE_ADDRESS.CONTROL_CENTER,
                                            canUtils.MODULE_ADDRESS.SLOT1,
                                            data=[0,0,0,0,70,55,60,50])
    
    canMsgs[3] = can_frame.from_canIdParams(canUtils.PRIORITY_LEVEL.HIGH_,
                                            canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_10,
                                            canUtils.MODULE_ADDRESS.CONTROL_CENTER,
                                            canUtils.MODULE_ADDRESS.SLOT1,
                                            data=[80,79,45,0,0,0,0,0])
    
    for i in range(2):
        for canMsg in canMsgs:
            Battery_obj.updateStatesFromCanMsg(canMsg)

    print("-----BUFFERS-------")
    print(Battery_obj.buffers)
    print("------------------")

    print(f"Voltage: {Battery_obj.voltage}")
    print(f"Current: {Battery_obj.current}")
    print(f"SOC: {Battery_obj.soc}")
    print("----------------------")
    print(f"Warnings: {Battery_obj.warnings}")
    print("----------------------")
    print(f"Temperatures: {Battery_obj.temps}")
    print("----------------------")
    print(f"Max Temperature: {Battery_obj.maxTemp}")



