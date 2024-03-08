import datetime
import warnings
import numpy as np
import CanUtils as canUtils
from typing import Set, Dict
from collections import deque
from enum import Enum, unique
from CanUtils import can_frame
from scipy.interpolate import interp1d


batteryVoltagesForInterpolation = 30 + 0.1*np.arange(122)
batteryChargeTimesForInterpolation = np.array(
[177.34895,    177.32961667, 177.29101667, 177.27165, 177.25233333,
177.21355,    177.17483333, 177.1361,     177.07796667, 177.01991667,
176.96181667, 176.9231,     176.86501667, 176.78758333, 176.72948333,
176.67145,    176.59405,    176.51668333, 176.4393,     176.34256667,
176.26518333, 176.14923333, 176.05256667, 175.95593333, 175.84003333,
175.72398333, 175.58865,    175.45335,    175.31798333, 175.18265,
175.02811667, 174.85423333, 174.69956667, 174.52573333, 174.31316667,
174.11993333, 173.9075,     173.71433333, 173.48268333, 173.23161667,
172.98033333, 172.70966667, 172.45833333, 172.16835,    171.85905,
171.53023333, 171.18208333, 170.83398333, 170.42781667, 170.02163333,
169.32525,   167.93226667, 165.26195,    162.85978333, 160.64756667,
158.62843333, 156.6084,     154.66566667, 152.74218333, 150.79928333,
148.75936667, 146.467,      143.92238333, 141.06715,    138.15401667,
135.20273333, 132.30953333, 129.4363,     126.67925,    123.9419,
121.3403,     118.85528333, 116.35053333, 113.98221667, 111.76906667,
109.65301667, 107.71158333, 105.82806667, 104.06123333, 102.37181667,
100.77986667,  99.22666667,  97.67303333,  96.21676667,  94.72176667,
93.28525,     91.82913333,  90.39266667,  88.89791667,  87.42256667,
85.92761667,  84.37466667,  82.86028333,  81.28778333,  79.67615,
78.02576667,  76.35581667,  74.60815,     72.91908333,  71.26901667,
69.61908333,  67.96913333,  66.455,       65.03761667,  63.65901667,
62.31966667,  60.99906667,  59.75615,     58.51353333,  57.27091667,
56.04766667,  54.78558333,  53.50378333,  52.14465,     50.66911667,
49.0953,      46.95813333,  40.50658333,  32.15116667,  25.35266667,
16.42386667,  0])
batteryVoltage2TimeUntilFullCharge = interp1d(batteryVoltagesForInterpolation,batteryChargeTimesForInterpolation*60)


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
    MAX_CHARGING_CURRENT = 12 #[A]
    WAITING_FOR_ALL_DATA_TIMEOUT = 4.5 #[s]
    TOTAL_TIME_UNTIL_FULL_CHARGE = 10672  #[s] (From 30V to 42.1V)
    PARTIAL_TIME_UNTIL_FULL_CHARGE = 3022 #[s] (From SOC=100% to 42.1V)
    SECONDS_PER_SOC_PERCENTAGE_INCREASE = 76.5 #[s/%]
   

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
        
        self.inSlot = False
        self.bmsState = 0
        self.currentGlobalTime = 0
        self.bmsHasCanBusError = False
        self.waitingForAllData = False
        self.localTimer = 0
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
    

    def updateStatesFromBatterySlotModule(self, inSlot:bool, bmsHasCanBusError:bool, bmsState:bool)->None:
        self.inSlot = inSlot

        if self.inSlot and not self.bmsState and bmsState:
            self.waitingForAllData = True
            self.localTimer = self.currentGlobalTime

        elif self.inSlot and self.bmsState and bmsState:
            if self.currentGlobalTime - self.localTimer > self.WAITING_FOR_ALL_DATA_TIMEOUT:
                self.waitingForAllData = False

        elif (self.inSlot and self.bmsState and not bmsState) or not self.inSlot or self.bmsHasCanBusError:
            self.waitingForAllData = False

        self.bmsState = bmsState
        self.bmsHasCanBusError = bmsHasCanBusError

        if not self.inSlot or self.bmsHasCanBusError or self.waitingForAllData:
            self.clearBuffers()
        return None
    

    def checkForBatteryErrors(self)->None:
        if not self.inSlot:
            warnings.warn("Battery values are empty. Battery is not in slot")
        
        elif self.bmsHasCanBusError:
            warnings.warn("Battery values are empty. Battery has a CAN-bus connection error.")
        
        elif self.waitingForAllData:
            msg = "Battery values are empty. Waiting for all data."
            msg = f"{msg} Try again in: {self.currentGlobalTime - self.localTimer}s"
            warnings.warn(msg)
            
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
        if self.current > 0.4: 
            self.isCharging_ = True
        else: 
            self.isCharging_ = False
        return self.isCharging_
    
    @property
    def timeUntilFullCharge(self)->float:
        voltage_ = self.voltage
        if voltage_ < 30: voltage_ = 30
        elif voltage_ > 42.1: voltage_ = 42.1
        return float(batteryVoltage2TimeUntilFullCharge(voltage_))
    
    @property
    def timeUntilFullChargeInStrFormat(self):
        timeStr = str(datetime.timedelta(seconds=self.timeUntilFullCharge))
        timeStr = timeStr.split(":")
        timeStr = f"{timeStr[0]}h:{timeStr[1]}min:{round(float(timeStr[2]))}s"
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
            Battery_obj.updateStatesFromBatterySlotModule(True, False, True)

    print("-----BUFFERS-------")
    print(Battery_obj.buffers)
    print("------------------")

    print("-----OTHER STATES-------")
    print(f"BMS state: {Battery_obj.bmsState}")
    print(f"In Slot: {Battery_obj.inSlot}")
    print(f"BMS has can bus error: {Battery_obj.bmsHasCanBusError}")
    print(f"Waiting for all Data: {Battery_obj.waitingForAllData}")
    print(f"Current Global Time: {Battery_obj.currentGlobalTime}")
    print(f"Local Timer: {Battery_obj.localTimer}")
    print("------------------")
    Battery_obj.checkForBatteryErrors()

    Battery_obj.currentGlobalTime = 6
    Battery_obj.updateStatesFromBatterySlotModule(True, False, True)


    print("-----OTHER STATES-------")
    print(f"BMS state: {Battery_obj.bmsState}")
    print(f"In Slot: {Battery_obj.inSlot}")
    print(f"BMS has can bus error: {Battery_obj.bmsHasCanBusError}")
    print(f"Waiting for all Data: {Battery_obj.waitingForAllData}")
    print(f"Current Global Time: {Battery_obj.currentGlobalTime}")
    print(f"Local Timer: {Battery_obj.localTimer}")
    print("------------------")
    Battery_obj.checkForBatteryErrors()


    Battery_obj.currentGlobalTime = 11
    Battery_obj.updateStatesFromBatterySlotModule(True, False, True)
    Battery_obj.checkForBatteryErrors()

    print("----------------------")
    print(f"Voltage: {Battery_obj.voltage}")
    print(f"Current: {Battery_obj.current}")
    print(f"SOC: {Battery_obj.soc}")
    print(f"Is Charging: {Battery_obj.isCharging}")
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

