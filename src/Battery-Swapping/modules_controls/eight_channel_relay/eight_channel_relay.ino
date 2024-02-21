
#include <SPI.h>
#include <mcp2515.h> 
#include <Adafruit_NeoPixel.h>

// PINS SET-UP
const int GLOBAL_CAN_CS_PIN = 9;
const int EIGHT_CHANNEL_RELAY_MODULE_PINS[8] = {A0, A1, A2, A3, A4, A5, 4, 5}

// CAN-BUS SET-UP
struct can_frame canMsg; 
MCP2515 mcp2515Global(GLOBAL_CAN_CS_PIN); 

// GLOBAL STATE VARIABLES SET-UP
enum channel_state {OFF, ON};

typedef struct 
{
  channel_state channel_states[8] = {OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF};
  

} eight_channel_relay_module;





void setup(){
  
  for(int i; i<8; i++){
    pinMode(EIGHT_CHANNEL_RELAY_MODULE_PINS[i], OUTPUT);
    digitalWrite(EIGHT_CHANNEL_RELAY_MODULE_PINS[i], eight_channel_relay_module_states[i]);
    }

  mcp2515Global.reset();
  mcp2515Global.setBitrate(CAN_250KBPS, MCP_8MHZ); // The MCP2515 arduino module, has  an 8MHz clock.
  mcp2515Global.setNormalMode();
}

void loop(){
  
  
}