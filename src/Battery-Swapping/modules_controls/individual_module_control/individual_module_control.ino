// ------ IMPORTATION OF LIBRARIES ------ 
#include <SPI.h>
#include <mcp2515.h> 
#include <Adafruit_NeoPixel.h>

// MCP2515 ARDUINO NANO CONNECTIONS
// VCC → 5v
// GND → GND
// CS (battery) → D9
// CS (network) → D10
// SO → D12
// SI → D11
// SCK → D13
// INT → D2

// --- MODULE AND CONTROL CENTER ADDRESS SET-UP ---
const uint8_t MODULE_ADDRESS = 3;
const uint8_t CONTROL_CENTER_ADDRESS = 9;


// --- PINS SET-UP ---
const int RELAY_PIN = 15;
const int DOOR_LOCK_SOLENOID_PIN = 6;
const int BATTERY_LOCK_SOLENOID_PIN = 3;
const int LED_STRIP_PIN = 5;
const int REED_SWITCH_PIN = 14;
const int LOCAL_CAN_CS_PIN = 9;
const int GLOBAL_CAN_CS_PIN = 10;
const int NUM_LEDS_IN_STRIP = 60;
const bool BMS_CONNECTION_TO_RELAY_IS_NORMALLY_OPEN = 1;

// --- CAN-BUS SET-UP ---
MCP2515 mcp2515Local(LOCAL_CAN_CS_PIN); 
MCP2515 mcp2515Global(GLOBAL_CAN_CS_PIN); 
struct can_frame canMsg = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}}; 
void setAllCanMsgDataToZero(){for (int i = 0; i <= 7; i++){canMsg.data[i] = 0;}}

// --- LED SET-UP ---
Adafruit_NeoPixel strip(NUM_LEDS_IN_STRIP, LED_STRIP_PIN, NEO_GRB + NEO_KHZ800);
void setLedStripColor(uint8_t red, uint8_t green, uint8_t blue){
  for (int i = 0; i < NUM_LEDS_IN_STRIP; i++){
    strip.setPixelColor(i, red, green, blue);}
  strip.show();
}


// --- DEFINITION OF CAN ID RELATED FUNCTIONS ---

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
  bool reedSwitchState; 
  uint8_t ledStripState;
  bool bmsConnectionState;
  bool bmsConnectionError;
  bool doorLockSolenoidState;
  bool batteryLockSolenoidState;
  uint8_t extraPriorityLevel = 0;

  
  unsigned long sendModuleStatesTimer;    // [ms]
  uint16_t sendModuleStatesTimeout = 500; // [ms]

  unsigned long sendBatteryDataTimer;     // [ms]
  uint16_t sendBatteryDataTimeout = 2000; // [ms]

  unsigned long bmsConnectionTimer;       // [ms]
  uint16_t bmsConnectionTimeout = 30000;  // [ms]



  uint8_t batteryData[11][8] = {{0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0},
                                {0,0,0,0,0,0,0,0}};

  const uint32_t BATTERY_DATA_IDS[11] = {2550245121,
                                         2550310657,
                                         2550376193, 
                                         2550441729,
                                         2550507265, 
                                         2550572801, 
                                         2550638337,
                                         2550703873, 
                                         2550769409, 
                                         2550834945,
                                         2550900481};




  void setRelayState(bool state){
    digitalWrite(RELAY_PIN, state);
    relayState = state;
  }
  void flipRelayState(){setRelayState(!relayState);}


  void setDoorLockSolenoidState(bool state){
    if (state) {analogWrite(DOOR_LOCK_SOLENOID_PIN, 255);}
    else       {digitalWrite(DOOR_LOCK_SOLENOID_PIN, 0);}
    doorLockSolenoidState = state;
  }
  void flipDoorLockSolenoidState(){setDoorLockSolenoidState(!doorLockSolenoidState);}


  void setBatteryLockSolenoidState(bool state){
    if (state) {analogWrite(BATTERY_LOCK_SOLENOID_PIN, 255);}
    else       {digitalWrite(BATTERY_LOCK_SOLENOID_PIN, 0);}
    batteryLockSolenoidState = state;
  }
  void flipBatteryLockSolenoidState(){setBatteryLockSolenoidState(!batteryLockSolenoidState);}


  bool getReedSwitchState(){
    bool state = !digitalRead(REED_SWITCH_PIN);
    return state;
  }
  bool updateReedSwitchState(){reedSwitchState = getReedSwitchState();}


  void setLedStripState(uint8_t state){
    if      (state == 0) {setLedStripColor(0,   0,   0);}
    else if (state == 1) {setLedStripColor(120, 0,   0);}
    else if (state == 2) {setLedStripColor(0,   120, 0);}
    else if (state == 3) {setLedStripColor(0,   0,   120);}
    else if (state == 4) {setLedStripColor(60,  0,   104);}
    if      (state <= 4) {ledStripState = state;}
  }


  void updateBmsConnectionState(){
    if (BMS_CONNECTION_TO_RELAY_IS_NORMALLY_OPEN){
      if      (!relayState)                                          {bmsConnectionState = 0;} 
      else if (millis() - bmsConnectionTimer > bmsConnectionTimeout) {bmsConnectionState = 0;} 
      else                                                           {bmsConnectionState = 1;}
    } else {
      if      (relayState)                                           {bmsConnectionState = 0;} 
      else if (millis() - bmsConnectionTimer > bmsConnectionTimeout) {bmsConnectionState = 0;} 
      else                                                           {bmsConnectionState = 1;}
    }
  }

  void updateBmsConnectionError(){
    if (BMS_CONNECTION_TO_RELAY_IS_NORMALLY_OPEN){
      if      (relayState && !bmsConnectionState)                    {bmsConnectionError = 1;} 
      else                                                           {bmsConnectionError = 0;}
    } else {
      if      (!relayState && !bmsConnectionState)                   {bmsConnectionError = 1;} 
      else                                                           {bmsConnectionError = 0;}
    }
  }

  void resetBmsConnection(uint16_t bmsResetDuration /*[ms]*/){
    flipRelayState();
    delay(bmsResetDuration); 
    flipRelayState();
  }







  void readFromLocalNetworkAndUpdate_BatteryData_BmsConnectionState_BmsConnectionError(){
    if (mcp2515Local.readMessage(&canMsg) == MCP2515::ERROR_OK && !Serial.available()){
      for (int i = 0; i <= 10; i++){
        if (canMsg.can_id == BATTERY_DATA_IDS[i]){
          for (int j = 0; j <= 7; j++){batteryData[i][j] = canMsg.data[j];}
          break;
        }
      }
      bmsConnectionTimer = millis();
    }
    updateBmsConnectionState();
    updateBmsConnectionError();
  }


  void sendBatteryDataToGlobalNetwork(){
    uint8_t priorityLevel;
    uint8_t activityCode;
    uint8_t originAddress = MODULE_ADDRESS;
    uint8_t destinationAddress = CONTROL_CENTER_ADDRESS; 

    priorityLevel = 7 - extraPriorityLevel;
    for (int i = 0; i <= 10; i++){
      activityCode = i + 1;
      canMsg.can_id = createCanMsgCanId(priorityLevel, activityCode, destinationAddress, originAddress);
      for (int j = 0; j <= 7; j++){canMsg.data[j] = batteryData[i][j];}
      mcp2515Global.sendMessage(&canMsg);
    }
  }


  void sendModuleStatesToGlobalNetwork(){
    uint8_t activityCode = 12;
    uint8_t priorityLevel = 6 - extraPriorityLevel;
    uint8_t originAddress = MODULE_ADDRESS;
    uint8_t destinationAddress = CONTROL_CENTER_ADDRESS; 

    updateReedSwitchState();
    updateBmsConnectionState();
    updateBmsConnectionError();

    canMsg.can_id = createCanMsgCanId(priorityLevel, activityCode, destinationAddress, originAddress);
    canMsg.data[0] = relayState; 
    canMsg.data[1] = doorLockSolenoidState;
    canMsg.data[2] = batteryLockSolenoidState;
    canMsg.data[3] = reedSwitchState;
    canMsg.data[4] = ledStripState;
    canMsg.data[5] = bmsConnectionState;
    canMsg.data[6] = bmsConnectionError;
    canMsg.data[7] = extraPriorityLevel;
    mcp2515Global.sendMessage(&canMsg);
  }


  void visualizeNetwork(bool network_id){
    bool readMessageLogic;
    if (!network_id){readMessageLogic = (mcp2515Local.readMessage(&canMsg) == MCP2515::ERROR_OK && !Serial.available());}
    else            {readMessageLogic = (mcp2515Global.readMessage(&canMsg) == MCP2515::ERROR_OK && !Serial.available());}

    if (readMessageLogic) {
      uint8_t priorityLevel      = getPriorityLevelFromCanMsgCanId(canMsg.can_id);
      uint8_t activityCode       = getActivityCodeFromCanMsgCanId(canMsg.can_id);
      uint8_t DestinationAddress = getDestinationAddressFromCanMsgCanId(canMsg.can_id);
      uint8_t OriginAddress      = getOriginAddressFromCanMsgCanId(canMsg.can_id);

      Serial.print(canMsg.can_id);
      Serial.print(" : (Priority Level, Activity Code, Destination Address, Origin Address) : ");
      Serial.print("(");
      Serial.print(priorityLevel);
      Serial.print(", ");
      Serial.print(activityCode);
      Serial.print(", ");
      Serial.print(DestinationAddress);
      Serial.print(", ");
      Serial.print(OriginAddress);
      Serial.print(") --> ");
      

      for (int i = 0; i <= 7; i++){
        Serial.print(canMsg.data[i]);
        if (i<7){Serial.print(",");}
        else    {Serial.println(",");}
      }
      Serial.println("--------------------------");
    }
  }
  void visualizeLocalNetwork(){visualizeNetwork(0);}
  void visualizeGlobalNetwork(){visualizeNetwork(1);}


  void setMaskAndFilterForNetwork(bool network_id, uint32_t mask, uint32_t filter){

    if (!network_id){
      mcp2515Local.setFilterMask(mcp2515Local.MASK0, 1, mask);
      mcp2515Local.setFilter(mcp2515Local.RXF0, 1, filter);
    } else{
      mcp2515Global.setFilterMask(mcp2515Global.MASK0, 1, mask);
      mcp2515Global.setFilter(mcp2515Global.RXF0, 1, filter);
    }
  }
  void setMaskAndFilterForLocalNetwork(uint32_t mask, uint32_t filter){setMaskAndFilterForNetwork(0, mask, filter);}
  void setMaskAndFilterForGlobalNetwork(uint32_t mask, uint32_t filter){setMaskAndFilterForNetwork(1, mask, filter);}


  void readFromGlobalNetworkAndExecuteCommand(){
    if (mcp2515Local.readMessage(&canMsg) == MCP2515::ERROR_OK && !Serial.available()){
      if(getOriginAddressFromCanMsgCanId(canMsg.can_id) == CONTROL_CENTER_ADDRESS){  

        //uint8_t priorityLevel = getPriorityLevelFromCanMsgCanId(canMsg.can_id);
        uint8_t activityCode = getActivityCodeFromCanMsgCanId(canMsg.can_id);

        switch (activityCode) {
          case 1:
            byCommand_setPeripheralsStates();
            break;
          case 2:
            byCommand_sendModuleStates();
            break;
          case 3:
            byCommand_sendBatteryData();
            break;
          case 4:
            byCommand_sendTimeouts();
            break;
          case 5:
            byCommand_setTimeouts();
            break;
          case 6:
            byCommand_setExtraPriorityLevel();
            break;
          case 7:
            byCommand_resetBmsConnection();
            break;
        }
      }
    }
  }

  void byCommand_setPeripheralsStates(){
    if (bitRead(canMsg.data[0], 0)) {setRelayState(canMsg.data[1]);}
    if (bitRead(canMsg.data[0], 1)) {setDoorLockSolenoidState(canMsg.data[2]);}
    if (bitRead(canMsg.data[0], 2)) {setBatteryLockSolenoidState(canMsg.data[3]);}
    if (bitRead(canMsg.data[0], 3)) {setLedStripState(canMsg.data[3]);}
  }

  void byCommand_sendModuleStates(){
    sendModuleStatesToGlobalNetwork();
    }

  void byCommand_sendBatteryData(){
    sendBatteryDataToGlobalNetwork();
    }

  void byCommand_sendTimeouts(){
    uint8_t activityCode = 13;
    uint8_t priorityLevel = 6 - extraPriorityLevel;
    uint8_t originAddress = MODULE_ADDRESS;
    uint8_t destinationAddress = CONTROL_CENTER_ADDRESS;  
    canMsg.can_id = createCanMsgCanId(priorityLevel, activityCode, destinationAddress, originAddress);
    setAllCanMsgDataToZero();
    for (int i = 0; i <= 7; i++){
      bitWrite(canMsg.data[0], i, bitRead(sendModuleStatesTimeout, i));
      bitWrite(canMsg.data[1], i, bitRead(sendModuleStatesTimeout, 8 + i));
      bitWrite(canMsg.data[2], i, bitRead(sendBatteryDataTimeout, i));
      bitWrite(canMsg.data[3], i, bitRead(sendBatteryDataTimeout, 8 + i));
      bitWrite(canMsg.data[4], i, bitRead(bmsConnectionTimeout, i));
      bitWrite(canMsg.data[5], i, bitRead(bmsConnectionTimeout, 8 + i));
    }
    mcp2515Global.sendMessage(&canMsg);
  }

  void byCommand_setTimeouts(){
    if (bitRead(canMsg.data[0], 0)) {sendModuleStatesTimeout = (uint16_t) (canMsg.data[1] | canMsg.data[2] << 8);}
    if (bitRead(canMsg.data[0], 1)) {sendBatteryDataTimeout  = (uint16_t) (canMsg.data[3] | canMsg.data[4] << 8);}
    if (bitRead(canMsg.data[0], 2)) {bmsConnectionTimeout    = (uint16_t) (canMsg.data[5] | canMsg.data[6] << 8);}
  }

  void byCommand_setExtraPriorityLevel(){
    if (canMsg.data[0] <= 3){extraPriorityLevel = canMsg.data[0];}
  }

  void byCommand_resetBmsConnection(){
    resetBmsConnection(canMsg.data[0] | canMsg.data[1] << 8);
  } 

  

} Module;









Module module;

void setup() {
  // put your setup code here, to run once:

  // ---- ARDUINO PIN CONFIG ----
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(DOOR_LOCK_SOLENOID_PIN, OUTPUT);
  pinMode(BATTERY_LOCK_SOLENOID_PIN, OUTPUT);
  pinMode(LED_STRIP_PIN, OUTPUT);
  pinMode(REED_SWITCH_PIN, INPUT_PULLUP);
  

  // ---- COMUNICATIONS CONFIG ----
  strip.begin();      // Initialize LED strip.
  while (!Serial);
  Serial.begin(9600); // Initialize Serial comunication.
  SPI.begin();        // Initialize SPI comunication.


  // ---- CAN MODULES CONFIG ----
  mcp2515Local.reset();
  mcp2515Global.reset();

  mcp2515Local.setBitrate(CAN_250KBPS, MCP_8MHZ);  // The battery BMS has a bitrate of 250 kbps according to the datasheet sent by the Chinese.
  mcp2515Global.setBitrate(CAN_250KBPS, MCP_8MHZ); // The MCP2515 arduino module, has  an 8MHz clock.

  mcp2515Local.setNormalMode(); 
  mcp2515Global.setNormalMode();
  

  // ---- MODULE INITIAL CONFIG ----
  module.setLedStripState(0);
  module.setRelayState(BMS_CONNECTION_TO_RELAY_IS_NORMALLY_OPEN);
  module.setBatteryLockSolenoidState(0);
  module.setDoorLockSolenoidState(0);
  module.resetBmsConnection(5000);
  module.sendModuleStatesTimer = millis();
  module.sendBatteryDataTimer  = millis();
  module.bmsConnectionTimer    = millis();

  // --- PERIPHERALS TESTS ---
  //module.setLedStripState(1);
  //module.setBatteryLockSolenoidState(1);
  //module.setDoorLockSolenoidState();
  //module.setRelayState(1);


}

void loop() {
  
  // --- 1) READ FROM LOCAL NETWORK AND UPDATE BATTERY AND BMS DATA ---
 // module.readFromLocalNetworkAndUpdate_BatteryData_BmsConnectionState_BmsConnectionError();

  // --- 2) SEND MODULE STATES TO GLOBAL NETWORK ---
  //if (millis() - module.sendModuleStatesTimer > module.sendModuleStatesTimeout){
  //  module.sendModuleStatesToGlobalNetwork();
  //  module.sendModuleStatesTimer = millis();
  //  Serial.print("Here");
  //}

  // --- 3) SEND BATTERY DATA TO GLOBAL NETWORK ---
  //if (millis() - module.sendBatteryDataTimer > module.sendBatteryDataTimeout){
    //module.sendBatteryDataToGlobalNetwork();
    //module.sendBatteryDataTimer = millis();
    //Serial.print("ThflipRelayState()ere");
  //}

  // --- 4) READ FROM GLOBAL NETWORK AND EXECUTE COMMANDS ---
  //module.readFromGlobalNetworkAndExecuteCommand();

  // module.visualizeLocalNetwork();

module.flipRelayState();
delay(1000);

module.flipBatteryLockSolenoidState();
delay(1000);
 
}
