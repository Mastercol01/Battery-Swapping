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


// (1) --- MODULE AND CONTROL CENTER ADDRESS SET-UP --- (1)
const uint8_t MODULE_ADDRESS = 8;
const uint8_t CONTROL_CENTER_ADDRESS = 9;

// (2) --- PINS SET-UP --- (2)
const uint8_t RELAY_PIN = 15;
const uint8_t LED_STRIP_PIN = 5;
const uint8_t REED_SWITCH_PIN = 14;
const uint8_t LOCAL_CAN_CS_PIN = 9;
const uint8_t GLOBAL_CAN_CS_PIN = 10;
const uint8_t DOOR_LOCK_SOLENOID_PIN = 6;
const uint8_t BATTERY_LOCK_SOLENOID_PIN = 3;
const uint8_t BMS_CONNECTION_TO_RELAY_IS_NORMALLY_OPEN = 1;

// (3) --- TIMERS SETUP --- (3)
unsigned int solenoidsTimer;
unsigned int solenoidsTimerDiff;
unsigned int ledTimer;
unsigned int ledTimerDiff;
unsigned int littleTimeSkip = 500;
unsigned int bigTimeSkip = 5000;
bool reedSwitchState = 0;


// (4) --- CAN-BUS SET-UP --- (4)
MCP2515 mcp2515Local(LOCAL_CAN_CS_PIN); 
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

// (5) --- LED SET-UP --- (5)
const uint8_t NUM_LEDS_IN_STRIP = 60;
Adafruit_NeoPixel strip(NUM_LEDS_IN_STRIP, LED_STRIP_PIN, NEO_GRB + NEO_KHZ800);
void setLedStripColor(uint8_t red, uint8_t green, uint8_t blue){
  for (int i = 0; i < NUM_LEDS_IN_STRIP; i++){
    strip.setPixelColor(i, red, green, blue);}
  strip.show();
}
void setLedStripState(uint8_t state){
  if      (state == 0) {setLedStripColor(0,   0,   0);}
  else if (state == 1) {setLedStripColor(120, 0,   0);}
  else if (state == 2) {setLedStripColor(0,   120, 0);}
  else if (state == 3) {setLedStripColor(0,   0,   120);}
  else if (state == 4) {setLedStripColor(60,  0,   104);}
}




void setup() {
  // put your setup code here, to run once:

  // ---- ARDUINO PIN CONFIG ----
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_STRIP_PIN, OUTPUT);
  pinMode(REED_SWITCH_PIN, INPUT_PULLUP);
  pinMode(DOOR_LOCK_SOLENOID_PIN, OUTPUT);
  pinMode(BATTERY_LOCK_SOLENOID_PIN, OUTPUT);
  

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

  solenoidsTimer = millis();
}


void loop() {
  // put your main code here, to run repeatedly:

  // (1) TEST REED SWITCH (1)
  if(!digitalRead(REED_SWITCH_PIN) != reedSwitchState){
    reedSwitchState = !digitalRead(REED_SWITCH_PIN);
    if (reedSwitchState){Serial.println("REED SWITCH WAS ACTIVATED");}
    else                {Serial.println("REED SWITCH WAS DEACTIVATED");}
  }

  // (2) TEST CAN NETWORK (2)
  visualizeLocalNetwork();
  // visualizeGlobalNetwork();

  // (3) TEST LED STRIP (3)
  ledTimerDiff = millis() - ledTimer;
  if      (1*littleTimeSkip > ledTimerDiff && ledTimerDiff >= 0*littleTimeSkip){setLedStripState(0);}
  else if (2*littleTimeSkip > ledTimerDiff && ledTimerDiff >= 1*littleTimeSkip){setLedStripState(1);}
  else if (3*littleTimeSkip > ledTimerDiff && ledTimerDiff >= 2*littleTimeSkip){setLedStripState(2);}
  else if (4*littleTimeSkip > ledTimerDiff && ledTimerDiff >= 3*littleTimeSkip){setLedStripState(3);}
  else if (5*littleTimeSkip > ledTimerDiff && ledTimerDiff >= 4*littleTimeSkip){setLedStripState(4);}
  else if (6*littleTimeSkip > ledTimerDiff && ledTimerDiff >= 5*littleTimeSkip){ledTimer = millis();}

  // (4) TEST SOLENOIDS (4)
  solenoidsTimerDiff = millis() - solenoidsTimer;
  if      (1*littleTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 0*littleTimeSkip){digitalWrite(RELAY_PIN, HIGH);}
  else if (2*littleTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 1*littleTimeSkip){digitalWrite(DOOR_LOCK_SOLENOID_PIN, HIGH);}
  else if (3*littleTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 2*littleTimeSkip){digitalWrite(BATTERY_LOCK_SOLENOID_PIN, HIGH);}

  if      (1*littleTimeSkip + bigTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 0*littleTimeSkip + bigTimeSkip){digitalWrite(RELAY_PIN, LOW);}
  else if (2*littleTimeSkip + bigTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 1*littleTimeSkip + bigTimeSkip){digitalWrite(DOOR_LOCK_SOLENOID_PIN, LOW);}
  else if (3*littleTimeSkip + bigTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 2*littleTimeSkip + bigTimeSkip){digitalWrite(BATTERY_LOCK_SOLENOID_PIN, LOW);}
  else if (4*littleTimeSkip + 2*bigTimeSkip > solenoidsTimerDiff && solenoidsTimerDiff >= 3*littleTimeSkip + 2*bigTimeSkip){solenoidsTimer = millis();}


}
