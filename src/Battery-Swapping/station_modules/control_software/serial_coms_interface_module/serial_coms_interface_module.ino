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

#include <mcp2515.h> 
#include <CanUtils.h>

// -DEFINITION OF CAN-BUS VARIABLES-
struct can_frame canMsg_net2rpy = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}}; 
struct can_frame canMsg_rpy2net = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}}; 
MCP2515 canNetworkGlobal(9); // CS pin of global CAN network is 9.

// CAN MSG ---> CAN STRING 
String canMsg2canStr(struct can_frame canMsg){
  String canStr = String(canMsg.can_id) + "-";
  for (int i=0; i<8; i++){
    canStr += String(canMsg.data[i]) + ",";
  }
  canStr += "\n";
  return canStr;
}

// CAN MSG <--- CAN STRING 
can_frame canStr2canMsg(String canStr){
  String canData;
  int commaStrIndex;
  int hyphenStrIndex;
  struct can_frame canMsg;

  canMsg.can_dlc = 8;
  hyphenStrIndex = canStr.indexOf("-");
  canData = canStr.substring(hyphenStrIndex+1);
  canMsg.can_id = uint32_t(canStr.substring(0, hyphenStrIndex).toInt());

  for (int i=0; i<8; i++){
    commaStrIndex = canData.indexOf(",");
    canMsg.data[i] = uint8_t(canData.substring(0, commaStrIndex).toInt());
    canData = canData.substring(commaStrIndex+1);
  }
  return canMsg;
}

void transmit_net2rpy(MCP2515& canNetwork, struct can_frame* p_canMsg){
  if (canUtils::readCanMsg(canNetwork, p_canMsg, canUtils::CONTROL_CENTER) == MCP2515::ERROR_OK){
    Serial.print(canMsg2canStr(*p_canMsg));
  }
}

void transmit_rpy2net(MCP2515& canNetwork, struct can_frame* p_canMsg){
  if (Serial.available() > 0){
    *p_canMsg = canStr2canMsg(Serial.readStringUntil('\n'));
    canNetwork.sendMessage(p_canMsg);
  }
}


void setup(){

  // Initialize Serial Communication
  Serial.begin(115200); // Initialize Serial comunication.

  // CAN Network standard set-up.
  canUtils::stdCanNetworkSetUp(canNetworkGlobal);

}


void loop(){

  // Receive CAN messages from global network and send it via Serial to the RPY as strings.
  transmit_net2rpy(canNetworkGlobal, &canMsg_net2rpy);

  // Receive data via Serial from the RPY and send it over to the global network as CAN messages.
  transmit_rpy2net(canNetworkGlobal, &canMsg_rpy2net);
}



