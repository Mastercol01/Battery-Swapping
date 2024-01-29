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


// Define struct for canMsg.
struct can_frame canMsg_net; 

// Define struct and pin for mcp2515_net.
MCP2515 mcp2515_net(53);  

// Define global variables.
unsigned long c1;
unsigned long t_init1;
unsigned char led_command1;

unsigned long c2;
unsigned long t_init2;
unsigned char led_command2;


void setup() {
  // put your setup code here, to run once:

  while (!Serial);
  Serial.begin(9600);

  SPI.begin();
  mcp2515_net.reset();

  // The battery BMS has a baud rate of 250 kbps according
  // to the DataSheet sent by the Chinese.
  // The MCP2515 arduino module, has an 8MHz clock.
  mcp2515_net.setBitrate(CAN_250KBPS, MCP_8MHZ); 
  mcp2515_net.setNormalMode();

  // Initialize values of global variables.
  c1 = 1;
  led_command1 = 0;
  t_init1 = millis();

  c2 = 1;
  led_command2 = 0;
  t_init2 = millis();
}

void loop() {


  // We check if there was an error in the delivery of the message and if there is 
  // None, we read it.
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

  }


  // Every 10 seconds, we instruct a LED to turn
  // on and off in arduino 1.
  if (millis() - t_init1 > 10000){
    
    led_command1 = c1 % 2;
    canMsg_net.can_id = 2550245111;
    canMsg_net.can_dlc = 8;
    canMsg_net.data[0] = led_command1;
    canMsg_net.data[1] = led_command1;
    canMsg_net.data[2] = led_command1;
    canMsg_net.data[3] = led_command1;
    canMsg_net.data[4] = led_command1;
    canMsg_net.data[5] = led_command1;
    canMsg_net.data[6] = led_command1;
    canMsg_net.data[7] = led_command1;
    mcp2515_net.sendMessage(&canMsg_net);

    c1 += 1;
    t_init1 = millis();
  }



  // Every 5 seconds, we instruct a LED to turn
  // on and off in arduino 2.
  if (millis() - t_init2 > 5000){
    
    led_command2 = c2 % 2;
    canMsg_net.can_id = 2550245112;
    canMsg_net.can_dlc = 8;
    canMsg_net.data[0] = led_command2;
    canMsg_net.data[1] = led_command2;
    canMsg_net.data[2] = led_command2;
    canMsg_net.data[3] = led_command2;
    canMsg_net.data[4] = led_command2;
    canMsg_net.data[5] = led_command2;
    canMsg_net.data[6] = led_command2;
    canMsg_net.data[7] = led_command2;
    mcp2515_net.sendMessage(&canMsg_net);

    c2 += 1;
    t_init2 = millis();
  }


















}
