import datetime
import numpy as np
from typing import Set, Dict
from collections import deque
from enum import Enum, unique
from scipy.interpolate import interp1d
from math import isnan

from BSS_control.CanUtils import (
    can_frame,
    PRIORITY_LEVEL,
    MODULE_ADDRESS,
    ACTIVITY_CODE)



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


def voltage2TimePassed(voltage):

    if voltage < 35.072:
        timePassed = 103.630*voltage - 3111.774
    
    elif voltage < 41.697:
        timePassed = -70.81*voltage**2 + 6552.578*voltage - 142189.681
    
    elif voltage < 42.1:
        timePassed = 4665.0124*voltage - 186597.0223

    return timePassed

# @property
# def timeUntilFullCharge(self)->float:
#     if self.isChargedEnough:
#         return 0
    
#     if    self.voltage < 30.03: voltage_ = 30.03
#     elif  self.voltage > 42.10: voltage_ = 42.10
#     else: voltage_ = self.voltage

#     if voltage_ < 42.1:
#         timePassed    = voltage2TimePassed(voltage_)
#         timeRemaining = self.TOTAL_TIME_UNTIL_FULL_CHARGE - timePassed
    
#     elif self.isCharging:
#         timeRemaining  = self.TOTAL_TIME_UNTIL_FULL_CHARGE
#         timeRemaining -= self.PARTIAL_TIME_UNTIL_FULL_CHARGE
#         timeRemaining *= self.current/self.MAX_CHARGING_CURRENT

#     else:
#         timeRemaining  = self.TOTAL_TIME_UNTIL_FULL_CHARGE
#         timeRemaining -= self.PARTIAL_TIME_UNTIL_FULL_CHARGE

#     return timeRemaining

# MAX_CHARGING_CURRENT = 12 #[A]
# TOTAL_TIME_UNTIL_FULL_CHARGE = 11000  #[s] (From 30V to Full Charge)
# PARTIAL_TIME_UNTIL_FULL_CHARGE = 9800 #[s] (From 30V to 42.1V)


class Battery:
    DEQUE_MAXLEN = 10
    MAX_CHARGING_CURRENT = 12 #[A]
    SECONDS_PER_SOC_PERCENTAGE_INCREASE = 76.5 #[s/%]

    BATTERY_IS_CHARGED_ENOUGH_SOC_THRESHOLD = 97 #[%]
    BATTERY_IS_CHARGING_CURRENT_THRESHOLD = 0.6 #[A]

    FATAL_BATTERY_WARNINGS = set()
    WAITING_FOR_ALL_DATA_TIMEOUT = 4.5*1000 #[ms]
    DATA_PACKETS_ARE_DAMAGED_TIMEOUT = 3*60*1000 #[ms]
    
   

    def __init__(self, moduleAddressToControl):
        self.moduleAddressToControl = moduleAddressToControl

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
        
        
        # TIMERS
        self.localTimer = 0
        self.currentGlobalTime = 0
        self.dataPacketsAreDamagedTimer = 0

        # ADDRESSABILITY STATUS
        self.inSlot = False
        self.bmsON = False
        self.waitingForAllData = False
        self.bmsHasCanBusError = False

        # OTHER VARS
        self.relayChanneOn = False
        self.proccessToStartChargeIsActive_setter(False)     
        self.proccessToFinishChargeIsActive_setter(False)
        self.dataPacketsAreDamaged = False
        return None



    def updateStatesFromCanMsg(self, canMsg : can_frame)->None:

        if canMsg.activityCode == ACTIVITY_CODE.net2rpy_BATTERY_DATA_0:
            self.buffers["soc"].append(canMsg.data[4])
            self.buffers["voltage"].append( 0.1*((canMsg.data[1] << 8) | canMsg.data[0]) )
            self.buffers["current"].append( 0.1*((canMsg.data[3] << 8) | canMsg.data[2]) - 3200 )
            
            for i in range(3):
                if canMsg.data[i+5] > 0:
                    bitValues = [(((1 << j) & canMsg.data[i+5]) >> j) for j in range(8)]
                    self.buffers["warnings"].extend( [BATTERY_WARNINGS(8*i + j) for j in range(8) if bitValues[j]] )


        elif canMsg.activityCode == ACTIVITY_CODE.net2rpy_BATTERY_DATA_1:
            if canMsg.data[0]:
                bitValues = [(((1 << j) & canMsg.data[0]) >> j) for j in range(5)]
                self.buffers["warnings"].extend( [BATTERY_WARNINGS(24 + j) for j in range(5) if bitValues[j]] )

            if canMsg.data[1]:
                bitValues = [(((1 << j) & canMsg.data[1]) >> j) for j in range(3)]
                self.buffers["warnings"].extend( [BATTERY_WARNINGS(29 + j) for j in range(3) if bitValues[j]] )


        elif canMsg.activityCode == ACTIVITY_CODE.net2rpy_BATTERY_DATA_9:
            for i in range(1,5):
                self.buffers[f"NTC{i}"].append(canMsg.data[i+3] - 40)


        elif canMsg.activityCode == ACTIVITY_CODE.net2rpy_BATTERY_DATA_10:
            self.buffers["NTC5"].append(  canMsg.data[0] - 40)
            self.buffers["NTC6"].append(  canMsg.data[1] - 40)
            self.buffers["MOSFET"].append(canMsg.data[2] - 40)

        return None
    
    def updateCurrentGlobalTime(self, newCurrentGlobalTime : float)->None:
        self.currentGlobalTime = newCurrentGlobalTime

        if self.currentGlobalTime - self.dataPacketsAreDamagedTimer > self.DATA_PACKETS_ARE_DAMAGED_TIMEOUT:
            self.dataPacketsAreDamaged = False

        return None

    def updateStatesFromBatterySlotModule(self, inSlot:bool|float, bmsHasCanBusError:bool|float, bmsON:bool|float)->None:

        if any(np.isnan([inSlot, bmsHasCanBusError, bmsON])):
            return None

        if not inSlot:
            self.waitingForAllData = False
            self.clearBuffers()

        elif not bmsON:
            self.waitingForAllData = False
            self.clearBuffers()

        elif not self.bmsON:
            self.waitingForAllData = True
            self.localTimer = self.currentGlobalTime
            self.clearBuffers()

        elif self.currentGlobalTime - self.localTimer > self.WAITING_FOR_ALL_DATA_TIMEOUT:
            self.waitingForAllData = False
            if bmsHasCanBusError:
                self.clearBuffers()

        else:
            self.clearBuffers()

        self.inSlot = inSlot
        self.bmsON = bmsON
        self.bmsHasCanBusError = bmsHasCanBusError
        return None
    
    def updateStatesFromControlCenter(self, relayChannelOn : bool|float)->None:
        self.relayChanneOn = relayChannelOn
        return None
    

    @property
    def isAddressable(self)->bool:
        if isnan(self.inSlot):
            res = False
        elif isnan(self.bmsON):
            res = False
        elif isnan(self.bmsHasCanBusError):
            res = False
        else:
            res = self.inSlot and self.bmsON and (not self.waitingForAllData) and (not self.bmsHasCanBusError)
        return res

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
    def fatalWarnings(self)->Set[BATTERY_WARNINGS]:
        return self.warnings.intersection(self.FATAL_BATTERY_WARNINGS)
    
    @property
    def hasWarnings(self)->bool|float:
        if not self.isAddressable:
            res = np.nan
        else:
            res = bool(self.warnings)
        return res
        
    @property
    def hasFatalWarnings(self)->bool|float:
        if not self.isAddressable:
            res = np.nan
        else:
            res = bool(self.fatalWarnings)
        return res
    
    @property
    def isDamaged(self)->bool|float:

        if (not self.inSlot) or (not self.bmsON) or self.waitingForAllData:
            return np.nan

        dataPacketsAreDamagedLogic = any(np.array(self.buffers["voltage"]) < 0)
        dataPacketsAreDamagedLogic = any(np.array(self.buffers["current"]) < 0)                                                 or dataPacketsAreDamagedLogic
        dataPacketsAreDamagedLogic = any(np.array(self.buffers["soc"]) < 0)                                                     or dataPacketsAreDamagedLogic
        dataPacketsAreDamagedLogic = ((self.current > self.BATTERY_IS_CHARGING_CURRENT_THRESHOLD) and (not self.relayChanneOn)) or dataPacketsAreDamagedLogic

        if dataPacketsAreDamagedLogic:
            self.dataPacketsAreDamaged = True
            self.dataPacketsAreDamagedTimer = self.currentGlobalTime

        if self.bmsHasCanBusError:
            res = True
        elif self.dataPacketsAreDamaged:
            res = True
        elif self.hasFatalWarnings:
            res = True
        else:
            res = False
            
        return res
    
    @property
    def temps(self)->Dict[str, float]:
        return {key:np.mean(val) for key,val in self.buffers.items() if key not in ["voltage", "current", "soc", "warnings"]}
    
    @property
    def maxTemp(self)->Dict[str, float]:
        temperatures = self.temps
        maxTemperatureKey = max(temperatures, key=temperatures.get)
        return {maxTemperatureKey:temperatures[maxTemperatureKey]}
    
    @property
    def isCharging(self)->bool|float:
        if (not self.inSlot) or (not self.bmsON) or (not self.relayChanneOn):
            res = False
        elif self.waitingForAllData or self.bmsHasCanBusError or self.dataPacketsAreDamaged:
            res = np.nan
        else:
            res = self.current > self.BATTERY_IS_CHARGING_CURRENT_THRESHOLD
        return res
    
    @property
    def isChargedEnough(self)->bool|float:
        if not self.isAddressable:
            res = np.nan
        else:
            res = self.soc >= self.BATTERY_IS_CHARGED_ENOUGH_SOC_THRESHOLD
        return res

    @property
    def canProceedToBeCharged(self)->bool: 
        if not self.isAddressable:
            res = False 
        elif self.isDamaged:
            res = False
        elif self.isBusyWithChargeProcess:
            res = False
        elif self.isChargedEnough:
            res = False
        elif self.relayChanneOn:
            res = False
        else:
            res = True
        return res
    

    
    @property
    def timeUntilFullCharge(self)->float:
        if self.isChargedEnough and not self.isCharging:
            timeRemaining = 0
        
        elif self.soc < self.BATTERY_IS_CHARGED_ENOUGH_SOC_THRESHOLD:
            timeRemaining = (self.BATTERY_IS_CHARGED_ENOUGH_SOC_THRESHOLD - self.soc)*self.SECONDS_PER_SOC_PERCENTAGE_INCREASE + 20*60

        elif self.isCharging:
            timeRemaining = (20*60)*(self.current/self.MAX_CHARGING_CURRENT)
        
        else:
            timeRemaining = np.nan
        
        return timeRemaining
    
    
    @property
    def timeUntilFullChargeInStrFormat(self)->str|float:
        try:
            timeStr = str(datetime.timedelta(seconds=self.timeUntilFullCharge))
            timeStr = timeStr.split(":")
            timeStr = f"{timeStr[0]}h:{timeStr[1]}min:{round(float(timeStr[2]))}s"
        except ValueError:
            timeStr = np.nan
        return timeStr
    
    @property
    def isDeliverableToUser(self)->bool:
        if not self.isAddressable:
            res = False
        elif self.isDamaged:
            res = False
        elif self.isBusyWithChargeProcess:
            res = False
        elif not self.isChargedEnough:
            res = False
        elif self.relayChanneOn:
            res = False
        else:
            res = True
        return res
    
    @property
    def proccessToStartChargeIsActive(self)->bool:
        return self.proccessToStartChargeIsActive_
    
    
    def proccessToStartChargeIsActive_setter(self, value)->bool:
        self.proccessToStartChargeIsActive_ = value
        return None


    @property
    def proccessToFinishChargeIsActive(self)->bool:
        return self.proccessToFinishChargeIsActive_
    
    def proccessToFinishChargeIsActive_setter(self, value)->bool:
        self.proccessToFinishChargeIsActive_ = value
        return None

    @property
    def isBusyWithChargeProcess(self):
        if self.proccessToStartChargeIsActive or self.proccessToFinishChargeIsActive:
            res = True
        else:
            res = self.isCharging
        return res

    
    
    def clearBuffers(self)->None:
        for key in self.buffers.keys():
            self.buffers[key].clear()
        return None
    
    def _debugPrint(self)->None:

        print()

        print(f"--------- BATTERY OF MODULE:  {self.moduleAddressToControl} ---------")
  
        print()

        print("----- BUFFERS -----")
        for key, val in self.buffers.items():
            print(f"{key}: {val}")

        print()

        print("----- ADDRRESABILITY -----")
        print(f"inSlot: {self.inSlot}")
        print(f"bmsON: {self.bmsON}")
        print(f"waitingForAllData: {self.waitingForAllData}")
        print(f"bmsHasCanBusError: {self.bmsHasCanBusError}")
        print(f"isAddressable: {self.isAddressable}")

        print()

        print("----- ATTRIBUTES -----")
        print(f"voltage: {self.voltage}")
        print(f"current: {self.current}")
        print(f"soc: {self.soc}")
        print(f"warnings: {self.warnings}")
        print(f"fatalWarnings: {self.fatalWarnings}")
        print(f"hasWarnings: {self.hasWarnings}")
        print(f"hasFatalWarnings: {self.hasFatalWarnings}")
        print(f"dataPacketsAreDamaged: {self.dataPacketsAreDamaged}")
        print(f"isDamaged: {self.isDamaged}")
        print(f"temps: {self.temps}")
        print(f"maxTemp: {self.maxTemp}")
        print(f"isCharging: {self.isCharging}")
        print(f"isChargedEnough: {self.isChargedEnough}")
        print(f"canProceedToBeCharged: {self.canProceedToBeCharged}")
        print(f"timeUntilFullChargeInStrFormat: {self.timeUntilFullChargeInStrFormat}")
        print(f"isDeliverableToUser: {self.isDeliverableToUser}")
        print(f"proccessToStartChargeIsActive: {self.proccessToStartChargeIsActive}")
        print(f"proccessToFinishChargeIsActive: {self.proccessToFinishChargeIsActive}")
        print(f"isBusyWithChargeProcess: {self.isBusyWithChargeProcess}")
        print(f"relayChanneOn: {self.relayChanneOn}")

        print()

        print("----- TIMERS -----")
        print(f"currentGlobalTime: {self.currentGlobalTime}")
        print(f"localTimer: {self.localTimer}")
        print(f"dataPacketsAreDamagedTimer: {self.dataPacketsAreDamagedTimer}")

        print()

        return None









if __name__ == "__main__":
    Battery_obj = Battery(MODULE_ADDRESS.SLOT1)
    Battery_obj.updateStatesFromBatterySlotModule(True, False, True)
    Battery_obj._debugPrint()

    Battery_obj.currentGlobalTime = 10
    Battery_obj.updateStatesFromBatterySlotModule(True, False, True)
    Battery_obj._debugPrint()

    canMsgs = [0, 0, 0, 0]
    canMsgs[0] = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.net2rpy_BATTERY_DATA_0,
                                            MODULE_ADDRESS.CONTROL_CENTER,
                                            MODULE_ADDRESS.SLOT1,
                                            data=[0x77,0x01,0x50,0x7D,78,0b10000000,0b10000000,0b10000000])
    
    canMsgs[1] = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.net2rpy_BATTERY_DATA_1,
                                            MODULE_ADDRESS.CONTROL_CENTER,
                                            MODULE_ADDRESS.SLOT1,
                                            data=[0b00010000,0b00000100,0,0,0,0,0,0])
    
    canMsgs[2] = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.net2rpy_BATTERY_DATA_9,
                                            MODULE_ADDRESS.CONTROL_CENTER,
                                            MODULE_ADDRESS.SLOT1,
                                            data=[0,0,0,0,70,55,60,50])
    
    canMsgs[3] = can_frame.from_canIdParams(PRIORITY_LEVEL.HIGH_,
                                            ACTIVITY_CODE.net2rpy_BATTERY_DATA_10,
                                            MODULE_ADDRESS.CONTROL_CENTER,
                                            MODULE_ADDRESS.SLOT1,
                                            data=[80,79,45,0,0,0,0,0])
    

    for canMsg in canMsgs:
        Battery_obj.updateStatesFromCanMsg(canMsg)

    Battery_obj._debugPrint()


