from array import array
from enum import Enum, unique
from typing import NewType, List

uint32_t = NewType("uint32_t", int)
uint8_t = NewType("uint8_t", int)
CanStr = NewType("CanStr", str)


@unique
class PRIORITY_LEVEL(Enum):
  ULTRA_LOW   = 7
  LOW_        = 6
  MEDIUM_LOW  = 5
  MEDIUM      = 4 
  MEDIUM_HIGH = 3
  HIGH_       = 2
  ULTRA_HIGH  = 1
  PRIORITY_LEVEL_NONE = 0

@unique
class MODULE_ADDRESS(Enum):
  MODULE_ADDRESS_NONE = 0
  SLOT1 = 1
  SLOT2 = 2
  SLOT3 = 3,
  SLOT4 = 4
  SLOT5 = 5
  SLOT6 = 6
  SLOT7 = 7
  SLOT8 = 8
  EIGHT_CHANNEL_RELAY = 9
  CONTROL_CENTER = 10

@unique
class ACTIVITY_CODE(Enum):
  ACTIVITY_CODE_NONE                                      = 0
  net2rpy_STATES_INFO_OF_EIGHT_CHANNEL_RELAY_MODULE       = 1
  rpy2net_SET_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE         = 2
  rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE        = 3
  rpy2net_FLIP_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE        = 4
  rpy2net_FLIP_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE       = 5
  net2rpy_BATTERY_DATA_0                                  = 6 
  net2rpy_BATTERY_DATA_1                                  = 7
  net2rpy_BATTERY_DATA_2                                  = 8
  net2rpy_BATTERY_DATA_3                                  = 9
  net2rpy_BATTERY_DATA_4                                  = 10
  net2rpy_BATTERY_DATA_5                                  = 11
  net2rpy_BATTERY_DATA_6                                  = 12
  net2rpy_BATTERY_DATA_7                                  = 13
  net2rpy_BATTERY_DATA_8                                  = 14
  net2rpy_BATTERY_DATA_9                                  = 15
  net2rpy_BATTERY_DATA_10                                 = 16
  net2rpy_PERIPHERALS_STATES_OF_BATTERY_SLOT_MODULE       = 17
  rpy2net_SET_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE       = 18
  rpy2net_SET_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE     = 19
  rpy2net_FLIP_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE      = 20
  rpy2net_FLIP_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE    = 21
  rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE      = 22
  rpy2net_RESET_BATTERY_CAN_BUS_ERROR_STATE_AND_TIMER     = 23


def createCanMsgCanId(priorityLevel      : PRIORITY_LEVEL, 
                      activityCode       : ACTIVITY_CODE , 
                      destinationAddress : MODULE_ADDRESS , 
                      originAddress      : MODULE_ADDRESS ) -> uint32_t:
  canId = 0
  canId |= originAddress.value
  canId |= destinationAddress.value << 8
  canId |= activityCode.value       << 16
  canId |= priorityLevel.value      << 26
  canId |= 1 << 31
  return canId

def getPriorityLevelFromCanMsgCanId(canId : uint32_t) -> PRIORITY_LEVEL:
  bitmask = 0b111 << 26
  priorityLevel = (canId & bitmask) >> 26
  return PRIORITY_LEVEL(priorityLevel)

def getActivityCodeFromCanMsgCanId(canId : uint32_t) -> ACTIVITY_CODE:
  bitmask = 0b11111111 << 16
  activityCode = (canId & bitmask) >> 16
  return ACTIVITY_CODE(activityCode)

def getDestinationAddressFromCanMsgCanId(canId : uint32_t) -> MODULE_ADDRESS:
  bitmask = 0b11111111 << 8
  destinationAddress = (canId & bitmask) >> 8
  return MODULE_ADDRESS(destinationAddress)

def getOriginAddressFromCanMsgCanId(canId : uint32_t) -> MODULE_ADDRESS:
  bitmask = 0b11111111
  originAddress = (canId & bitmask)
  return MODULE_ADDRESS(originAddress)


class can_frame:
    def __init__(self, can_id: uint32_t = 0, data: List[uint8_t] = [0,0,0,0,0,0,0,0])->None:
        self.can_id = can_id
        self.data = data
        return None
    
    @property
    def can_id(self)->uint32_t:
       return self._can_id
    
    @can_id.setter
    def can_id(self, value: uint32_t)->None:
        if not isinstance(value, int) or value < 0:
            raise ValueError("'can_id' must be of type uint32_t")
        self._can_id = value
        self.priorityLevel      = getPriorityLevelFromCanMsgCanId(self._can_id)
        self.activityCode       = getActivityCodeFromCanMsgCanId(self._can_id)
        self.destinationAddress = getDestinationAddressFromCanMsgCanId(self._can_id)
        self.originAddress      = getOriginAddressFromCanMsgCanId(self._can_id)
        return None
    
    @property
    def data(self)->List[uint8_t]:
       return self._data
    
    @data.setter
    def data(self, value: List[uint8_t])->None:
        if len(value) != 8:
            raise ValueError("'data' must be a list/array of length 8")
        try:
            self._data = array("B", value)
        except TypeError:
            raise TypeError("The elements of 'data' must be of type uint8_t")
        return None
              
    @classmethod
    def from_canStr(cls, canStr: CanStr):
        can_id, data = canStr.split("-")
        return cls(int(can_id), [int(i) for i in data.split(",")[:-1]])
    
    def to_canStr(self)->CanStr:
        return f"{self.can_id}-{','.join([str(i) for i in self.data])},\n"
    
    def __str__(self)->CanStr:
       return self.to_canStr()
    
    @classmethod
    def from_canIdParams(cls, priorityLevel      :PRIORITY_LEVEL, 
                              activityCode       :ACTIVITY_CODE, 
                              destinationAddress :MODULE_ADDRESS, 
                              originAddress      :MODULE_ADDRESS, 
                              data:List[uint8_t]= [0,0,0,0,0,0,0,0]):
         return cls(createCanMsgCanId(priorityLevel, activityCode, destinationAddress, originAddress), data)
    
    def __repr__(self) -> str:
       return f"can_frame.from_canIdParams(\n{self.priorityLevel},\n{self.activityCode},\n{self.destinationAddress},\n{self.originAddress},\n{self.data})\n"

    
  





if __name__ == "__main__":
    canMsgs = [0,0,0,0]

    canMsgs[0] = can_frame()

    canMsgs[1] = can_frame(can_id = 2415987209, data = [0,0,0,0,0,0,0,0])

    canMsgs[2] = can_frame.from_canStr("2349926913-1,0,0,0,0,0,0,0,\n")

    canMsgs[3] = can_frame.from_canIdParams(PRIORITY_LEVEL.ULTRA_HIGH,
                                            ACTIVITY_CODE.rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE,
                                            MODULE_ADDRESS.EIGHT_CHANNEL_RELAY,
                                            MODULE_ADDRESS.CONTROL_CENTER,
                                            data = [1,2,3,4,5,6,7,8])
    for canMsg in canMsgs:
        print("-------------------\n")
        print(canMsg)
        print(repr(canMsg))




    
    

