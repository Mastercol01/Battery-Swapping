import warnings
from functools import partial
from PyQt5.QtCore import QTimer
from typing import Callable, List

from BSS_control.eight_channel_relay import (
    EightChannelRelay, 
    CHANNEL_NAME)

from BSS_control.battery_slot import (
    BatterySlot,
    LED_STRIP_STATE, 
    SOLENOID_NAME)
    
from BSS_control.CanUtils import (
    can_frame,
    MODULE_ADDRESS,
    CanStr)



class ControlCenter:
    SLOT_ADDRESSES = [MODULE_ADDRESS(i) for i in [1,4,5,8]]
    CONTROL_CENTER_ADDRESS = MODULE_ADDRESS.CONTROL_CENTER
    EIGHT_CHANNEL_RELAY_ADDRESS = MODULE_ADDRESS.EIGHT_CHANNEL_RELAY
    


    def __init__(self):
        self.modules = {address:BatterySlot(address) for address in self.SLOT_ADDRESSES}
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS] = EightChannelRelay()
        self.currentGlobalTime = 0
        return None
    
    def updateStatesFromCanStr(self, canStr : CanStr)->None:
        try:
            canMsg = can_frame.from_canStr(canStr)
        except Exception as e:
            warnings.warn(f"WARNING: Exception catched in ControlCenter.updateStatesFromCanStr(): {e}")
            return None
        
        if canMsg.destinationAddress == self.CONTROL_CENTER_ADDRESS:
            self.modules[canMsg.originAddress].updateStatesFromCanMsg(canMsg)
        return None
    
    def updateCurrentGlobalTime(self, newCurrentGlobalTime : float)->None:
        self.currentGlobalTime = newCurrentGlobalTime
        for address in self.SLOT_ADDRESSES + [self.EIGHT_CHANNEL_RELAY_ADDRESS]:
            self.modules[address].updateCurrentGlobalTime(newCurrentGlobalTime)
        return None
    
    def connect_sendCanMsg(self, sendCanMsg_func : Callable[[CanStr], None])->None:
        for address in self.SLOT_ADDRESSES:
            self.modules[address].SIGNALS_DICT[address].connect(sendCanMsg_func)
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].SIGNALS.sendCanMsg_eightChannelRelay.connect(sendCanMsg_func)
        return None
    
    def setSlotSolenoidState(self, slotAddress : MODULE_ADDRESS, name : SOLENOID_NAME, state : bool, delay : int = None)->None:
        try:
            if isinstance(delay, int):
                QTimer.singleShot(delay, partial(self.modules[slotAddress].setSolenoidState, name, state))
            else:
                self.modules[slotAddress].setSolenoidState(name, state)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None
    
    def setSlotSolenoidStates(self, slotAddress : MODULE_ADDRESS, states : List[bool], delay : int | None = None)->None:
        try:
            if isinstance(delay, int):
                QTimer.singleShot(delay, partial(self.modules[slotAddress].setSolenoidsStates, states))
            else:
                self.modules[slotAddress].setSolenoidsStates(states)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None
    
    def setSlotLedStripState(self, slotAddress : MODULE_ADDRESS, state : LED_STRIP_STATE, delay : int | None = None)->None:
        try:
            if isinstance(delay, int):
                QTimer.singleShot(delay, partial(self.modules[slotAddress].setLedStripState, state))
            else:
                self.modules[slotAddress].setLedStripState(state)
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
        return None    
    
    def setRelayChannelState(self, name : CHANNEL_NAME, state : bool, delay : int | None = None)->None:
        if isinstance(delay, int):
            QTimer.singleShot(delay, partial(self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelState, name, state))
        else:
            self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelState(name, state)
        return None
    
    def setRelayChannelStates(self, states : List[bool], delay : int | None = None)->None:
        if isinstance(delay, int):
            QTimer.singleShot(delay, partial(self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelStates, states))
        else:
            self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].setChannelStates(states)
        return None


    def getSlotsThatMatchStates(self, statesToMatch):
        statesToMatchLogic = {
            "LIMIT_SWITCH"                     : (True,  "limitSwitchState"),
            "LED_STRIP"                        : (True,  "ledStripState"), 
            "BMS_SOLENOID"                     : (True,  "bmsSolenoidState"),
            "DOOR_LOCK_SOLENOID"               : (True,  "doorLockSolenoidState"),
            "BATTERY_LOCK_SOLENOID"            : (True,  "batteryLockSolenoidState"),

            "BATTERY_IN_SLOT"                  : (True,  "limitSwitchState"),
            "BATTERY_BMS_IS_ON"                : (True,  "bmsSolenoidState"),
            "BATTERY_BMS_HAS_CAN_BUS_ERROR"    : (True,  "batteryCanBusErrorState"),
            "BATTERY_IS_WAITING_FOR_ALL_DATA"  : (False, "waitingForAllData"), 
                

            "BATTERY_IS_ADDRESSABLE"           : (False, "isAddressable"),
            "BATTERY_IS_CHARGING"              : (False, "isCharging"),
            "BATTERY_IS_CHARGED"               : (False, "isCharged"),
            "BATTERY_IS_CHARGABLE"             : (False, "isChargable"),
            "BATTERY_HAS_WARNINGS"             : (False, "hasWarnings"),
            "BATTERY_HAS_FATAL_WARNINGS"       : (False, "hasFatalWarnings"),
            "BATTERY_IS_DAMAGED"               : (False, "isDamaged"),
            "BATTERY_IS_DELIVERABLE_TO_USER"   : (False, "isDeliverableToUser")
        }
        statesToMatch_ = {key:value for key,value in statesToMatch.items() if key in statesToMatchLogic.keys()}
        res = [slotAddress for slotAddress in self.SLOT_ADDRESSES]

        for stateKeyword, stateValueToMatch in statesToMatch_.items():

            if len(res) < 1:
                break

            isSlotAttr, attrName = statesToMatchLogic[stateKeyword]

            if isSlotAttr:
                res = [slotAddress for slotAddress in res if getattr(self.modules[slotAddress], attrName) == stateValueToMatch]
            else:
                res = [slotAddress for slotAddress in res if getattr(self.modules[slotAddress].battery, attrName) == stateValueToMatch]

        return res
    
    
    def std_setup(self):
        delay = None
        delayIncrease = 250
        filledSlots = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": True})
        emptySlots  = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT": False})
        
        for i, slotAddress in enumerate(filledSlots):
            self.setSlotSolenoidStates(slotAddress, [1,0,0], delay)
            delay = delayIncrease*(i+1)

        if delay is None:
            for i, slotAddress in enumerate(emptySlots):
                self.setSlotSolenoidStates(slotAddress, [0,0,0], delay)
                delay = delayIncrease*(i+1)
        else:
            for i, slotAddress in enumerate(emptySlots):
                    self.setSlotSolenoidStates(slotAddress, [0,0,0], delay)
                    delay = delay + delayIncrease*(i+1)

        
        self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS]._debugPrint()

        for i, slotAddress in enumerate(self.SLOT_ADDRESSES):
            QTimer.singleShot(2500, self.modules[slotAddress]._debugPrint)
            #QTimer.singleShot(6000 + 500*i, self.modules[slotAddress].battery._debugPrint)
        return None
    
    def std_closeEvent(self):
        # self.turnOffAllLedStrips()
        delay = None
        delayIncrease = 250
        for i, slotAddress in enumerate(self.SLOT_ADDRESSES):
            self.setSlotSolenoidStates(slotAddress, [0,0,0], delay)
            delay = delayIncrease*(i+1)

        #for slotAddress in self.SLOT_ADDRESSES:
        #    self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.DOOR_LOCK, 0)
        #    self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BATTERY_LOCK, 0)
        
        #self.finishChargeOfSlotBatteriesIfAllowable()

        return None
    
    

    def turnOnLedStripsBasedOnState(self):
        batteries_notInSlot         = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT"                : False })
        batteries_damaged           = self.getSlotsThatMatchStates({"BATTERY_IS_DAMAGED"             : True  })
        batteries_deliverableToUser = self.getSlotsThatMatchStates({"BATTERY_IS_DELIVERABLE_TO_USER" : True  })
        other_batteries             = self.getSlotsThatMatchStates({"BATTERY_IN_SLOT"                : True, 
                                                                    "BATTERY_IS_DAMAGED"             : False,
                                                                    "BATTERY_IS_DELIVERABLE_TO_USER" : False  })

        for slotAddress in batteries_notInSlot:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.BLUE)

        for slotAddress in batteries_damaged:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.PURPLE)

        for slotAddress in batteries_deliverableToUser:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.GREEN)

        for slotAddress in other_batteries:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.RED)

        return None

    def turnOffAllLedStrips(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.setSlotLedStripState(slotAddress, LED_STRIP_STATE.OFF)
        return None
    
    def startChargeOfSlotBatteryIfAllowable(self, slotAddress):

        try:
            batteryIsChargable           = self.modules[slotAddress].battery.isChargable
            batteryAndDoorSolenoidsAreOn = self.modules[slotAddress].batteryAndDoorSolenoidsAreOn
            batteryRelayChannelIsOn      = self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].channelsStates[slotAddress.value-1]
        except AttributeError:
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")
            

        if batteryIsChargable and batteryAndDoorSolenoidsAreOn and not batteryRelayChannelIsOn:
            # We charge batteries that are chargable, secured in their slot, and not already charging.
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
            QTimer.singleShot(500, partial(self.setRelayChannelState, CHANNEL_NAME(slotAddress.value-1), 1))
            QTimer.singleShot(1000, partial(self.setSlotSolenoidState, slotAddress, SOLENOID_NAME.BMS,  1))
            return None

        elif not batteryAndDoorSolenoidsAreOn:
            warnings.warn("WARNING: Battery is chargable but not secured. Ignoring command.")
            return None
        

        return None


    def finishChargeOfSlotBatteryIfAllowable(self, slotAddress, forcedStop = False):

        """
        NOTE: Forcibly interrupting the charge process runs the risk of permanently damaging
        the battery's charger. However, in some cases it becomes necessary to do so, as
        charging a damaged battery is a tremendous fire hazard. Better to damage the charger (which
        will just stop working) than to risk an electrical fire breaking out inside the station.
        """

        try:
            batteryIsInSlot          = self.modules[slotAddress].battery.inSlot
            batteryBmsIsOn           = self.modules[slotAddress].battery.bmsON
            batteryBmsHasCanBusError = self.modules[slotAddress].battery.bmsHasCanBusError
            batteryHasFatalWarnings  = self.modules[slotAddress].battery.hasFatalWarnings
            batteryIsCharging        = self.modules[slotAddress].battery.isCharging
            batteryIsCharged         = self.modules[slotAddress].battery.isCharged
            batteryRelayChannelIsOn  = self.modules[self.EIGHT_CHANNEL_RELAY_ADDRESS].channelsStates[slotAddress.value-1]
        except AttributeError: 
            Exception("'slotAddress' is not valid. It must be of type MODULE_ADDRESS.SLOTi")


        if not batteryIsInSlot or not (batteryBmsIsOn and batteryRelayChannelIsOn):
            # Either:
            #  1) The battery is not in the slot
            #  2) The battery BMS and the Charger are not ON at the same time.
            # In either case it's not worth continuing the check since the battery could not possibly be charging.
            return None
        
        elif batteryBmsHasCanBusError and batteryBmsIsOn and batteryRelayChannelIsOn:
            # In the case that the battery becomes incomunicated with the station while charging,
            # we forzably stop the charging process.
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
            QTimer.singleShot(10000, partial(self.setRelayChannelState, CHANNEL_NAME(slotAddress.value-1), 0))
            QTimer.singleShot(10500, partial(self.setSlotSolenoidState, slotAddress, SOLENOID_NAME.BMS,  1))

            msg = f"WARNING: Battery{slotAddress} has become incomunicated with the station (bmsHasCanBusError == True)"
            msg = f"{msg}. FORCIBLY STOPPING THE CHARGE PROCESS NOW."
            warnings.warn(msg)

            return None

        elif batteryIsCharging and (batteryHasFatalWarnings or forcedStop):
            # If the battery develops "fatal warnings" during charging, we forzably
            # stop the charging process. We also stop it if it is explicitly enforced by the developer.
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
            QTimer.singleShot(10000, partial(self.setRelayChannelState, CHANNEL_NAME(slotAddress.value-1), 0))
            QTimer.singleShot(10500, partial(self.setSlotSolenoidState, slotAddress, SOLENOID_NAME.BMS,  1))

            if forcedStop:
                msg = f"WARNING: PERFORMING MANUAL FORCED STOP OF THE CHARGING PROCESS FOR Battery{slotAddress}."
            else:
                msg = f"WARNING: Battery{slotAddress} has developed fatal warnings (hasFatalWarnings == True)."
                msg = f"{msg}. FORCIBLY STOPPING THE CHARGE PROCESS NOW."

            warnings.warn(msg)
            return None
        
        elif batteryIsCharged and batteryRelayChannelIsOn:
            # When the battery has finished its charging process, we shut down the charger in the correct way.
            self.setSlotSolenoidState(slotAddress, SOLENOID_NAME.BMS, 0)
            QTimer.singleShot(500, partial(self.setRelayChannelState, CHANNEL_NAME(slotAddress.value), 0))
            QTimer.singleShot(1000, partial(self.setSlotSolenoidState, slotAddress, SOLENOID_NAME.BMS,  1))
            return None
        
        return None


    def startChargeOfSlotBatteriesIfAllowable(self):
        for slotAddress in self.SLOT_ADDRESSES:
            self.startChargeOfSlotBatteryIfAllowable(slotAddress)
        return None
  

    def finishChargeOfSlotBatteriesIfAllowable(self, forcedStop = False):
        for slotAddress in self.SLOT_ADDRESSES:
            self.finishChargeOfSlotBatteryIfAllowable(slotAddress, forcedStop)
        return None





















