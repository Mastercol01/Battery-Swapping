import datetime
import numpy as np
import CanUtils as canUtils
from collections import deque
from enum import Enum, unique
from CanUtils import can_frame
from typing import Deque, Tuple, Set, Dict, Union



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



class Battery:
    DEQUE_MAXLEN = 10
    TOTAL_TIME_UNTIL_FULL_CHARGE = 10672 #[s] (From 30V to 40.1V)
    PARTIAL_TIME_UNTIL_FULL_CHARGE = 3022 #[s] (From SOC=100% to 40.1V)
    SECONDS_PER_SOC_PERCENTAGE_INCREASE = 76.5 #[s/%]
    MAX_CHARGING_CURRENT = 12 #[A]

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
            self.buffers["soc"].append(canMsg.data[4])
            self.buffers["voltage"].append( 0.1*((canMsg.data[1] << 8) | canMsg.data[0]) )
            self.buffers["current"].append( 0.1*((canMsg.data[3] << 8) | canMsg.data[2]) - 3200 )
            
            for i in range(3):
                if canMsg.data[i+5] > 0:
                    bitValues = [(((1 << j) & canMsg.data[i+5]) >> j) for j in range(8)]
                    self.buffers["warnings"].extend( [BATTERY_WARNINGS(8*i + j) for j in range(8) if bitValues[j]] )


        elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_1:
            if canMsg.data[0]:
                bitValues = [(((1 << j) & canMsg.data[0]) >> j) for j in range(5)]
                self.buffers["warnings"].extend( [BATTERY_WARNINGS(24 + j) for j in range(5) if bitValues[j]] )

            if canMsg.data[1]:
                bitValues = [(((1 << j) & canMsg.data[1]) >> j) for j in range(3)]
                self.buffers["warnings"].extend( [BATTERY_WARNINGS(29 + j) for j in range(3) if bitValues[j]] )


        elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_9:
            for i in range(1,5):
                self.buffers[f"NTC{i}"].append(canMsg.data[i+3] - 40)


        elif canMsg.activityCode == canUtils.ACTIVITY_CODE.net2rpy_BATTERY_DATA_10:
            self.buffers["NTC5"].append(  canMsg.data[0] - 40)
            self.buffers["NTC6"].append(  canMsg.data[1] - 40)
            self.buffers["MOSFET"].append(canMsg.data[2] - 40)

        return None
    

    def updateStatesFromBatterySlotModule(self, inSlot:bool, bmsHasCanBusError:bool, isCharging_:bool, timeUntilFullCharge_:Union[float, None])->None:
        self.inSlot = inSlot
        self.bmsHasCanBusError = bmsHasCanBusError
        self.isCharging_ = isCharging_
        self.timeUntilFullCharge_ = timeUntilFullCharge_

        if not self.inSlot or self.bmsHasCanBusError:
            self.clearBuffers()
        return None

    def checkForBatteryErrors(self)->None:
        if not self.inSlot:
            raise ValueError("Battery values are empty. Battery is not in slot")
        
        elif self.bmsHasCanBusError:
            raise ValueError("Battery values are empty. Battery has a CAN-bus connection error.")
        return None
    


    @property
    def voltage(self)->float:
        self.checkForBatteryErrors()
        return np.mean(self.buffers["voltage"])

    @property
    def current(self)->float:
        self.checkForBatteryErrors()
        return np.mean(self.buffers["current"])
    
    @property
    def soc(self)->float:
        self.checkForBatteryErrors()
        return np.mean(self.buffers["soc"])
    
    @property
    def warnings(self)->Set[BATTERY_WARNINGS]:
        self.checkForBatteryErrors()
        return set(self.buffers["warnings"])
    
    @property
    def temps(self)->Dict[str, float]:
        self.checkForBatteryErrors()
        return {key:np.mean(val) for key,val in self.buffers.items() if key not in ["voltage", "current", "soc", "warnings"]}
    
    @property
    def maxTemp(self)->Dict[str, float]:
        temperatures = self.temps
        maxTemperatureKey = max(temperatures, key=temperatures.get)
        return {maxTemperatureKey:temperatures[maxTemperatureKey]}
    
    @property
    def isCharging(self)->bool:
        try:           
            if self.current > 0.5: 
                self.isCharging_ = True
            else: 
                self.isCharging_ = False
        except ValueError:
            pass
        return self.isCharging_
    
    def estimateTimeUntilFullChargeFromBatteryValues(self)->float:
        if self.soc < 100:
            estimatedTime = self.TOTAL_TIME_UNTIL_FULL_CHARGE - self.SECONDS_PER_SOC_PERCENTAGE_INCREASE*self.soc #[s]
        else:
            estimatedTime = self.PARTIAL_TIME_UNTIL_FULL_CHARGE*self.current/self.MAX_CHARGING_CURRENT #[s]
        return estimatedTime
    
    @property
    def timeUntilFullCharge(self):
        try: 
            self.timeUntilFullCharge_ = self.estimateTimeUntilFullChargeFromBatteryValues()
        except ValueError:
            pass
        return self.timeUntilFullCharge_
    
    @property
    def timeUntilFullChargeInStrFormat(self):
        timeStr = str(datetime.timedelta(seconds=self.timeUntilFullCharge))
        timeStr = timeStr.split(":")
        timeStr = f"{timeStr[0]}h:{timeStr[1]}min:{timeStr[2]}s"
        return timeStr
    
    def clearBuffers(self)->None:
        for key in self.buffers.keys():
            self.buffers[key].clear()
        return None

    
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
            Battery_obj.updateStatesFromBatterySlotModule(True, False, False, None)

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
    print("-----------------------")
    print(f"Time until full charge: {Battery_obj.timeUntilFullChargeInStrFormat}")

    Battery_obj.clearBuffers()

    print("-----BUFFERS-------")
    print(Battery_obj.buffers)
    print("------------------")

