#include <Arduino.h>
#include <stdint.h>
#include <SPI.h>
#include <mcp2515.h> 
#include "ArduinoCanUtils.h"

ArduinoCanUtils::ArduinoCanUtils(){};

uint32_t ArduinoCanUtils::createCanMsgCanId(uint8_t priorityLevel, uint8_t activityCode, uint8_t destinationAddress, uint8_t originAddress)
{
  uint32_t canId = 0;
  canId = canId | originAddress;
  canId = canId | destinationAddress << 8;
  canId = canId | ((uint32_t) activityCode) << 16;
  for (int i = 0; i <= 2; i++){bitWrite(canId, 26 + i, bitRead(priorityLevel, i));}  
  bitWrite(canId, 31, 1);
  return canId;
}

uint8_t ArduinoCanUtils::getPriorityLevelFromCanMsgCanId(uint32_t canId){
  uint8_t priorityLevel = 0; 
  for (int i = 0; i <= 2; i++){bitWrite(priorityLevel, i, bitRead(canId, 26 + i));}  
  return priorityLevel;
}

uint8_t ArduinoCanUtils::getActivityCodeFromCanMsgCanId(uint32_t canId){
  uint8_t activityCode = 0; 
  for (int i = 0; i <= 7; i++){bitWrite(activityCode, i, bitRead(canId, 16 + i));}  
  return activityCode;
}

uint8_t ArduinoCanUtils::getDestinationAddressFromCanMsgCanId(uint32_t canId){
  uint8_t destinationAddress = 0; 
  for (int i = 0; i <= 7; i++){bitWrite(destinationAddress, i, bitRead(canId, 8 + i));} 
  return destinationAddress;
}

uint8_t ArduinoCanUtils::getOriginAddressFromCanMsgCanId(uint32_t canId){
  uint8_t originAddress = 0; 
  for (int i = 0; i <= 7; i++){bitWrite(originAddress, i, bitRead(canId, i));}  
  return originAddress;
}

void ArduinoCanUtils::setAllCanMsgDataToZero(can_frame &canMsg){
    for (int i = 0; i <= 7; i++){canMsg.data[i] = 0;}
}