
#include <SPI.h>
#include <mcp2515.h> 
#include <ArduinoCanUtils.h>
#include <Adafruit_NeoPixel.h>


// CAN-BUS SET-UP
struct can_frame canMsg; 
const int GLOBAL_CAN_CS_PIN = 9;
MCP2515 mcp2515Global(GLOBAL_CAN_CS_PIN); 

enum statusOfCanMsg {FAIL, OK}
statusOfCanMsg readGlobalNetwork(struct can_frame &canMsg)
{
  statusOfCanMsg msgStatus;
  if (mcp2515Global.readMessage(&canMsg) == MCP2515::ERROR_OK) {
    msgStatus = OK;
  }else{
    msgStatus = FAIL;
  }
  return msgStatus;
};





class EightChannelRelayModule
{
  public:
  uint8_t originAddress;
  enum stateOfChannel {OFF, ON};
  const int CHANNEL_PINS[8] = {A0, A1, A2, A3, A4, A5, 4, 5};
  stateOfChannel channelStates[8] = {OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF};


  void EightChannelRelayModule(uint8_t moduleOriginAddress)
  {
  originAddress = moduleOriginAddress;
  }
  void setChannelState(uint8_t idx, stateOfChannel state)
  {
      if(idx<8 && (state==OFF || state==ON)){
          channelStates[idx] = state;
          digitalWrite(CHANNEL_PINS[idx], state);
      }
  }
  void fipChannelState(uint8_t idx)
  {
    setChannelState(idx, !channelStates[idx]);
  }



};


EightChannelRelayModule eightChannelRelayModule(1);




void setup(){
  
  for(int i; i<8; i++){
    pinMode(EIGHT_CHANNEL_RELAY_CHANNEL_PINS[i], OUTPUT);
    digitalWrite(EIGHT_CHANNEL_RELAY_CHANNEL_PINS[i], eight_channel_relay_module_states[i]);
    }

  mcp2515Global.reset();
  mcp2515Global.setBitrate(CAN_250KBPS, MCP_8MHZ); // The MCP2515 arduino module, has  an 8MHz clock.
  mcp2515Global.setNormalMode();
}

void loop(){
  
  
}