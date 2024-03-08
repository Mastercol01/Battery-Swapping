
import CanUtils as canUtils
import battery_slot as bslot
from battery_slot import BatterySlot
import eight_channel_relay as ecrelay
from eight_channel_relay import EightChannelRelay
from CanUtils import can_frame, uint32_t, uint8_t, CanStr
from PyQt5.QtCore import QTimer  
from functools import partial


class ControlCenter:
    SLOT_ADDRESSES = [address for address in  canUtils.MODULE_ADDRESS 
                     if address not in [canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY, canUtils.MODULE_ADDRESS.CONTROL_CENTER]]

    def __init__(self):
        self.modules = {address:BatterySlot(address) for address in self.SLOT_ADDRESSES}
        self.modules[canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY] = EightChannelRelay()
        self.timeUntilFullBatteryCharge = {address:None for address in self.SLOT_ADDRESSES}
        self.moduleAddress = canUtils.MODULE_ADDRESS.CONTROL_CENTER
        return None
    
    def updateStatesFromCanStr(self, canStr : CanStr)->None:
        canMsg = can_frame.from_canStr(canStr)
        if canMsg.destinationAddress == self.moduleAddress:
            self.modules[canMsg.originAddress].updateStatesFromCanMsg(canMsg)

        channelsStates = self.modules[canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY].channelsStates
        for address, value in self.timeUntilFullBatteryCharge.items():
            self.modules[address].updateStatesFromControlCenter(channelsStates[address.value - 1], value)
        return None


    def prepareToAdmitBatteryFromUser(self, slotAddress : canUtils.MODULE_ADDRESS):
        if slotAddress in [canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY, canUtils.MODULE_ADDRESS.CONTROL_CENTER]:
            raise ValueError("'slotAddress' must be the address of a battery slot module")
        
        elif self.modules[slotAddress].limitSwitchState:
            raise Exception("SLOT MODULE CAN'T FIT ANOTHER BATTERY INSIDE!")


        self.modules[slotAddress].unlockBatteryAndDoor()
        self.modules[slotAddress].setLedStripState(bslot.LED_STRIP_STATE.BLUE)
        return None
    
    def beginBatteryCharge(self, slotAddress : canUtils.MODULE_ADDRESS):
        if slotAddress in [canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY, canUtils.MODULE_ADDRESS.CONTROL_CENTER]:
            raise ValueError("'slotAddress' must be the address of a battery slot module")
        
        elif not self.modules[slotAddress].limitSwitchState:
            raise Exception("NO BATTERY TO CHARGE!")
        
        elif self.modules[slotAddress].battery.isCharging:
            raise Exception("BATTERY IS ALREADY CHARGING!")
        
        self.modules[slotAddress].setSolenoidState(bslot.SOLENOID_NAME.BMS, 0)
        QTimer().singleShot(1500, partial(self.modules[canUtils.MODULE_ADDRESS.EIGHT_CHANNEL_RELAY].setChannelState, ecrelay.CHANNEL_NAME(slotAddress-1), 0))
        QTimer().singleShot(1500, partial(self.modules[slotAddress].setSolenoidState, bslot.SOLENOID_NAME.BMS, 1))
        return None

