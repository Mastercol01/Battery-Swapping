// ------ IMPORTATION OF LIBRARIES ------ 
#include <SPI.h>
#include <mcp2515.h> 
#include <Adafruit_NeoPixel.h>

// MCP2515 ARDUINO NANO CONNECTIONS
// VCC → 5v
// GND → GND
// CS (network) → D9
// SO → D12
// SI → D11
// SCK → D13
// INT → D2

// --- PINS SET-UP ---
const int GLOBAL_CAN_CS_PIN = 9;

// --- CAN-BUS SET-UP ---
struct can_frame canMsg_RPY; 
struct can_frame canMsg_arduinos; 
MCP2515 mcp2515Global(GLOBAL_CAN_CS_PIN); 

String canMsgToCanStr(can_frame canMsg){
  String canStr = String(canMsg.can_id) + "-";
  canStr += String(canMsg.data[0]) + ",";
  canStr += String(canMsg.data[1]) + ",";
  canStr += String(canMsg.data[2]) + ",";
  canStr += String(canMsg.data[3]) + ",";
  canStr += String(canMsg.data[4]) + ",";
  canStr += String(canMsg.data[5]) + ",";
  canStr += String(canMsg.data[6]) + ",";
  canStr += String(canMsg.data[7]) + ",";
  canStr += "\n";
  return canStr;
}

can_frame canStrToCanMsg(String canStr){
  String canData;
  can_frame canMsg;
  int commaStrIndex;
  int hyphenStrIndex;

  hyphenStrIndex = canStr.indexOf("-");
  canData = canStr.substring(hyphenStrIndex+1);

  canMsg.can_dlc = 8;
  canMsg.can_id = uint32_t(canStr.substring(0, hyphenStrIndex).toInt());
  for (int i = 0; i <= 7; i++){
    commaStrIndex = canData.indexOf(",");
    canMsg.data[i] = uint8_t(canData.substring(0, commaStrIndex).toInt());
    canData = canData.substring(commaStrIndex+1);}

  return canMsg;
}


void setup(){
  Serial.begin(115200); // Initialize Serial comunication.
  mcp2515Global.reset();
  mcp2515Global.setBitrate(CAN_250KBPS, MCP_8MHZ); // The MCP2515 arduino module, has  an 8MHz clock.
  mcp2515Global.setNormalMode();
}


void loop(){

  // Receive CAN messages from global network and send it via Serial as strings.
  if (mcp2515Global.readMessage(&canMsg_arduinos) == MCP2515::ERROR_OK && !Serial.available()){
    Serial.print(canMsgToCanStr(canMsg_arduinos));    
  }

  // Receive data from Serial and send it over the from network as CAN messages.
  if(Serial.available() > 0){
    canMsg_RPY = canStrToCanMsg(Serial.readStringUntil('\n'));
    mcp2515Global.sendMessage(&canMsg_RPY);
    }
}
