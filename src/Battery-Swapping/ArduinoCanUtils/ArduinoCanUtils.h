#ifndef ArduinoCanUtils_h
#define ArduinoCanUtils_h


#include <Arduino.h>
#include <stdint.h>
#include <SPI.h>
#include <mcp2515.h> 


class ArduinoCanUtils
{
  public:
    ArduinoCanUtils();
    uint32_t createCanMsgCanId(uint8_t priorityLevel, uint8_t activityCode, uint8_t destinationAddress, uint8_t originAddress);
    uint8_t getPriorityLevelFromCanMsgCanId(uint32_t canId);
    uint8_t getActivityCodeFromCanMsgCanId(uint32_t canId);
    uint8_t getDestinationAddressFromCanMsgCanId(uint32_t canId);
    uint8_t getOriginAddressFromCanMsgCanId(uint32_t canId);
    void setAllCanMsgDataToZero(can_frame &canMsg);

};



#endif