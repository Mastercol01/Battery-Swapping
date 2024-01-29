// IMPORTATION OF LIBRARIES
#include <SPI.h>
#include <mcp2515.h> 

// MCP2515 ARDUINO NANO CONNECTIONS
// VCC → 5v
// GND → GND
// CS (battery) → D10
// CS (network) → D9
// SO → D12
// SI → D11
// SCK → D13
// INT → D2


// Define struct for canMsg.
struct can_frame canMsg_bat; 
struct can_frame canMsg_net;

// Define struct and pins for mcp2515_bat and mcp2515_net.
MCP2515 mcp2515_bat(10);  
MCP2515 mcp2515_net(9); 

void setup() {
  // put your setup code here, to run once:

  pinMode(6, OUTPUT);

  while (!Serial);
  Serial.begin(9600);

  SPI.begin();
  mcp2515_bat.reset();
  mcp2515_net.reset();

  // The battery BMS has a baud rate of 250 kbps according
  // to the DataSheet sent by the Chinese.
  // The MCP2515 arduino module, has  an 8MHz clock.
  mcp2515_bat.setBitrate(CAN_250KBPS, MCP_8MHZ); 
  mcp2515_net.setBitrate(CAN_250KBPS, MCP_8MHZ); 

  mcp2515_bat.setNormalMode(); 
  mcp2515_net.setNormalMode();
  
  
}

void loop() {
  
  // RECEIVE DATA FROM THE BATTERY AND SEND IT TO THE GLOBAL CAN NETWORK.
  if (mcp2515_bat.readMessage(&canMsg_bat) == MCP2515::ERROR_OK && !Serial.available()){
      canMsg_bat.can_id = canMsg_bat.can_id + 0;
      mcp2515_net.sendMessage(&canMsg_bat); 
  }



  // RECEIVE DATA FROM THE GLOBAL CAN NETWORK
  if (mcp2515_net.readMessage(&canMsg_net) == MCP2515::ERROR_OK && !Serial.available()){

      // We read the can_id as well as the complete set of data, byte by byte.
      Serial.print(canMsg_net.can_id);
      Serial.print(",");
      Serial.print(canMsg_net.data[0]);
      Serial.print(",");
      Serial.print(canMsg_net.data[1]);
      Serial.print(",");
      Serial.print(canMsg_net.data[2]);
      Serial.print(",");
      Serial.print(canMsg_net.data[3]);
      Serial.print(",");
      Serial.print(canMsg_net.data[4]);
      Serial.print(",");
      Serial.print(canMsg_net.data[5]);
      Serial.print(",");
      Serial.print(canMsg_net.data[6]);
      Serial.print(",");
      Serial.println(canMsg_net.data[7]);

      if(canMsg_net.can_id == 2550245111){digitalWrite(6, bool(canMsg_net.data[0]));}
      
      
  }












  

  }


  

  
  

