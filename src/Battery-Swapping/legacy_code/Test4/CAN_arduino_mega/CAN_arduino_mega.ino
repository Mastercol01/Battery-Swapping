// IMPORTATION OF LIBRARIES
#include <SPI.h>
#include <mcp2515.h> 

// MCP2515 ARDUINO MEGA CONNECTIONS
// VCC → 5v
// GND → GND
// CS → 53
// SO → 50
// SI → 51
// SCK → 52
// INT → 2

const uint8_t NUM_MODULES = 8;
const uint8_t CONTROL_CENTER_ADDRESS = 9;
const int GLOBAL_CAN_CS_PIN = 53;

MCP2515 mcp2515Global(GLOBAL_CAN_CS_PIN); 
struct can_frame canMsg = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}}; 
void setAllCanMsgDataToZero(){for (int i = 0; i <= 7; i++){canMsg.data[i] = 0;}}





uint32_t createCanMsgCanId(uint8_t priorityLevel, uint8_t activityCode, uint8_t destinationAddress, uint8_t originAddress)
{
  uint32_t canId = 0;
  canId = canId | originAddress;
  canId = canId | destinationAddress << 8;
  canId = canId | ((uint32_t) activityCode) << 16;
  for (int i = 0; i <= 2; i++){bitWrite(canId, 26 + i, bitRead(priorityLevel, i));}  
  bitWrite(canId, 31, 1);

  return canId;
}

uint8_t getPriorityLevelFromCanMsgCanId(uint32_t canId){
  uint8_t priorityLevel = 0; 
  for (int i = 0; i <= 2; i++){bitWrite(priorityLevel, i, bitRead(canId, 26 + i));}  
  return priorityLevel;
}

uint8_t getActivityCodeFromCanMsgCanId(uint32_t canId){
  uint8_t activityCode = 0; 
  for (int i = 0; i <= 7; i++){bitWrite(activityCode, i, bitRead(canId, 16 + i));}  
  return activityCode;
}

uint8_t getDestinationAddressFromCanMsgCanId(uint32_t canId){
  uint8_t destinationAddress = 0; 
  for (int i = 0; i <= 7; i++){bitWrite(destinationAddress, i, bitRead(canId, 8 + i));} 
  return destinationAddress;
}

uint8_t getOriginAddressFromCanMsgCanId(uint32_t canId){
  uint8_t originAddress = 0; 
  for (int i = 0; i <= 7; i++){bitWrite(originAddress, i, bitRead(canId, i));}  
  return originAddress;
}



typedef struct
{
  bool relayState; 
  bool solenoidState;
  bool reedSwitchState;
  uint8_t ledStripState;
  bool bmsConnectionState;
  bool bmsConnectionError;
  uint8_t extraPriorityLevel;
  
  uint16_t sendModuleStatesTimeout; // [ms]
  uint16_t sendBatteryDataTimeout;  // [ms]
  uint16_t bmsConnectionTimeout;    // [ms]

  uint8_t batteryData[11][8] = {{0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0}};

   

} Module;




typedef struct 
{

  Module modules[NUM_MODULES];

  void visualizeGlobalNetwork(){
    if (mcp2515Global.readMessage(&canMsg) == MCP2515::ERROR_OK && !Serial.available());) {
      Serial.print(canMsg.can_id);
      Serial.print(",");
      for (int i = 0; i <= 7; i++){
        Serial.print(canMsg.data[0]);
        if (i<7){Serial.print(",");}
        else    {Serial.println(",");}
      }
      Serial.println("--------------------------");
    }
  }


  void readAndUpdateModulesData(){
    if (mcp2515Global.readMessage(&canMsg) == MCP2515::ERROR_OK && !Serial.available()){

      uint8_t originAddress = getOriginAddressFromCanMsgCanId(canMsg.can_id);
      uint8_t activityCode = getActivityCodeFromCanMsgCanId(canMsg.can_id);

      if (activityCode <= 11){
        for (int i = 0; i <= 7; i++){
          modules[originAddress].batteryData[activityCode-1][i] = canMsg.data[i];
        }

      } else if (activityCode == 12){
         modules[originAddress].relayState         = canMsg.data[0]; 
         modules[originAddress].solenoidState      = canMsg.data[1];
         modules[originAddress].reedSwitchState    = canMsg.data[2];
         modules[originAddress].ledStripState      = canMsg.data[3];
         modules[originAddress].bmsConnectionState = canMsg.data[4];
         modules[originAddress].bmsConnectionError = canMsg.data[5];
         modules[originAddress].extraPriorityLevel = canMsg.data[6];

      } else if (activityCode == 13){
        modules[originAddress].sendModuleStatesTimeout = (uint16_t) (canMsg.data[1] | canMsg.data[2] << 8);
        modules[originAddress].sendBatteryDataTimeout  = (uint16_t) (canMsg.data[3] | canMsg.data[4] << 8);
        modules[originAddress].bmsConnectionTimeout    = (uint16_t) (canMsg.data[5] | canMsg.data[6] << 8);

      }
    }
  }


  void setModulePeripheralsStates(uint8_t priorityLevel, uint8_t moduleAddress, bool relayStateEnable, bool solenoidStateEnable, bool ledStripStateEnable,  bool relayState, bool solenoidState, uint8_t ledStripState){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 1, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();

    uint8_t enableByte = 0;
    bitWrite(enableByte, 0, relayStateEnable);
    bitWrite(enableByte, 1, solenoidStateEnable);
    bitWrite(enableByte, 2, ledStripStateEnable);

    canMsg.data[0] = enableByte;
    canMsg.data[1] = relayState;
    canMsg.data[2] = solenoidState;
    canMsg.data[3] = ledStripState;
    mcp2515Global.sendMessage(&canMsg);
  }
  void setModuleRelayState(uint8_t priorityLevel, uint8_t moduleAddress, bool relayState){
    setModulePeripheralsStates(priorityLevel, moduleAddress, 1, 0, 0, relayState, 0, 0);
  }
  void setModuleSolenoidState(uint8_t priorityLevel, uint8_t moduleAddress, bool solenoidState){
    setModulePeripheralsStates(priorityLevel, moduleAddress, 0, 1, 0, 0, solenoidState, 0);
  }  
  void setModuleLedStripState(uint8_t priorityLevel, uint8_t moduleAddress, uint8_t ledStripState){
    setModulePeripheralsStates(priorityLevel, moduleAddress, 0, 0, 1, 0, 0, ledStripState);
  }  


  void requestModuleStates(uint8_t priorityLevel, uint8_t moduleAddress){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 2, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();
    mcp2515Global.sendMessage(&canMsg);
  }


  void requestModuleBatteryData(uint8_t priorityLevel, uint8_t moduleAddress){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 3, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();
    mcp2515Global.sendMessage(&canMsg);
  }


  void requestModuleTimeouts(uint8_t priorityLevel, uint8_t moduleAddress){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 4, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();
    mcp2515Global.sendMessage(&canMsg);
  }

  void setModuleTimeouts(uint8_t priorityLevel, uint8_t moduleAddress, bool sendModuleStatesTimeoutEnable, bool sendBatteryDataTimeoutEnable, bool bmsConnectionTimeoutEnable,  uint16_t sendModuleStatesTimeout, uint16_t sendBatteryDataTimeout, uint16_t bmsConnectionTimeout){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 5, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();

    uint8_t enableByte = 0;
    bitWrite(enableByte, 0, sendModuleStatesTimeoutEnable);
    bitWrite(enableByte, 1, sendBatteryDataTimeoutEnable);
    bitWrite(enableByte, 2, bmsConnectionTimeoutEnable);

    canMsg.data[0] = enableByte;
    for (int i = 0; i <= 7; i++){
      bitWrite(canMsg.data[1], i, bitRead(sendModuleStatesTimeout, i));
      bitWrite(canMsg.data[2], i, bitRead(sendModuleStatesTimeout, 8 + i));
      bitWrite(canMsg.data[3], i, bitRead(sendBatteryDataTimeout, i));
      bitWrite(canMsg.data[4], i, bitRead(sendBatteryDataTimeout, 8 + i));
      bitWrite(canMsg.data[5], i, bitRead(bmsConnectionTimeout, i));
      bitWrite(canMsg.data[6], i, bitRead(bmsConnectionTimeout, 8 + i));
    }
    mcp2515Global.sendMessage(&canMsg);
  }
  void setSendModuleStatesTimeout(uint8_t priorityLevel, uint8_t moduleAddress, uint16_t sendModuleStatesTimeout){
    setModuleTimeouts(priorityLevel, moduleAddress, 1, 0, 0, sendModuleStatesTimeout, 0, 0);
  }
  void setSendBatteryDataTimeout(uint8_t priorityLevel, uint8_t moduleAddress, uint16_t sendBatteryDataTimeout){
    setModuleTimeouts(priorityLevel, moduleAddress, 0, 1, 0, 0, sendBatteryDataTimeout, 0);
  }
  void setBmsConnectionTimeout(uint8_t priorityLevel, uint8_t moduleAddress, uint16_t bmsConnectionTimeout){
    setModuleTimeouts(priorityLevel, moduleAddress, 0, 0, 1, 0, 0, bmsConnectionTimeout);
  }


  void setModuleExtraPriorityLevel(uint8_t priorityLevel, uint8_t moduleAddress, uint8_t ModuleExtraPriorityLevel){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 6, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();

    if (ModuleExtraPriorityLevel <= 3){
      canMsg.data[0] = ModuleExtraPriorityLevel;
    } else{
      canMsg.data[0] = 3;
    }
    mcp2515Global.sendMessage(&canMsg);
  }


  void resetModuleBmsConnection(uint8_t priorityLevel, uint8_t moduleAddress, uint16_t bmsResetDuration){
    canMsg.can_id = createCanMsgCanId(priorityLevel, 7, moduleAddress, CONTROL_CENTER_ADDRESS);
    setAllCanMsgDataToZero();

    for (int i = 0; i <= 7; i++){
      bitWrite(canMsg.data[0], i, bitRead(bmsResetDuration, i);
      bitWrite(canMsg.data[1], i, bitRead(bmsResetDuration, 8 + i);
    }
    mcp2515Global.sendMessage(&canMsg);
  }







} ControlCenter;



void setup() {
  // put your setup code here, to run once:

  // ---- COMUNICATIONS CONFIG ----
  while (!Serial);
  Serial.begin(9600); // Initialize Serial comunication.
  SPI.begin();        // Initialize SPI comunication.

}

void loop() {
  // put your main code here, to run repeatedly:

}
