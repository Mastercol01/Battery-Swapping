/* 
MODULE DESRIPTION

This script mediates the communication between the Raspberry Pi and the rest of the global CAN network. 
It turns out that implementing CAN-bus communication directly with the Raspberry Pi is a very error-prone 
process and a pain in the ass. Serial communication, on the other hand, is a piece of cake. 
Thus, it is easier and more reliable to convert between modes of communication, when trying to interface the 
global CAN network together with the Raspberry Pi. To do this, we translate CAN messages proceeding from the 
global CAN network into string messages that can be sent to the Raspberry Pi via Serial, and we translate
string messages coming from the Raspberry Pi into CAN messages that can then be sent over the global CAN network.
*/

#include <SPI.h>
#include <mcp2515.h> 
#include <Adafruit_NeoPixel.h>

// PINS SET-UP 
const int GLOBAL_CAN_CS_PIN = 9;

// CAN-BUS SET-UP
struct can_frame canMsg_RPY; 
struct can_frame canMsg_arduinos; 
MCP2515 mcp2515Global(GLOBAL_CAN_CS_PIN); 

// CAN MSG ---> CAN STRING FUNCTION
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

// CAN MSG <--- CAN STRING FUNTION
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

  // Receive CAN messages from global network and send it via Serial to the RPY as strings.
  if (mcp2515Global.readMessage(&canMsg_arduinos) == MCP2515::ERROR_OK && !Serial.available()){
    Serial.print(canMsgToCanStr(canMsg_arduinos));    
  }

  // Receive data via Serial from the RPY and send it over to the global network as CAN messages.
  if(Serial.available() > 0){
    canMsg_RPY = canStrToCanMsg(Serial.readStringUntil('\n'));
    mcp2515Global.sendMessage(&canMsg_RPY);
    }
}
