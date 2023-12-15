// ------ IMPORTATION OF LIBRARIES ------ 
#include <SPI.h>
#include <mcp2515.h> 
#include <Adafruit_NeoPixel.h>

// MCP2515 ARDUINO NANO CONNECTIONS
// VCC → 5v
// GND → GND
// CS (battery) → D10
// CS (network) → D9
// SO → D12
// SI → D11
// SCK → D13
// INT → D2


 

//--------- MAIN MODULE VARS -----------
/*
 MODULE_NUM : Number assigned to the current module.

 COMMON_ID : Raspberry Pi ID. From it, all other module IDs are constructed. Also, it carries
             all instructions from the Raspberry Pi.

 MODULE_ID : ID of current module. It is used to send the data in the 'module_state' vector
             over the global CAN network.
             
 module_state[0] : Pack voltage       (RESOLVING POWER: 0.196 V/bit,   OFFSET: 0V,  VALUE RANGE: 0-50V)
 module_state[1] : Pack current       (RESOLVING POWER: 0.0784 A/bit,  OFFSET: 0A,  VALUE RANGE: 0-20A)
 module_state[2] : SOC                (RESOLVING POWER: 1 %/bit,       OFFSET: 0%,  VALUE RANGE: 0-100%)
 module_state[3] : Num. Faults        (VALUE RANGE: 0-29)
 module_state[4] : BMS state          (0 : ON,   1 : OFF)
 module_state[5] : Solenoid state     (0 : OFF,  1 : ON)
 module_state[6] : Reed-Switch state  (0 : OPEN, 1 : CLOSED)
 module_state[7] : LED-strip state    (0 : OFF,  1 : RED,  2 : GREED,  3 : BLUE,  4 : PURPLE)
*/
const uint8_t MODULE_NUM = 1;
const uint32_t COMMON_ID = 2550245121;
const uint32_t MODULE_ID = COMMON_ID - MODULE_NUM;
uint8_t module_state[8] = {0,0,0,0,0,0,0,0};



// (0)--------- AUXILIARY FUNCS -----------(0)
/*
 combineBytes: Combine bytes using little endian ordering,
               where 'byte0' is the least significant byte.
*/

int combineBytes(uint8_t byte0, uint8_t byte1) 
{
  uint16_t combinedValue = byte0 | (byte1 << 8);  
  return int(combinedValue);                      
}



// (1) ---------- BATTERY MANAGMENT SYSTEM (BMS) : VARS AND FUNCS ----------- (1)
/*
 BMS_PIN : Arduino pin in charge of the BMS control signal.

 set_battery_bms_state: Activates or deactivates the battery BMS on command 
                        and updates the module_state[4] variable, 
                        which is the variable corresponding to battery BMS
                        state. 
*/

const int BMS_PIN = 5;
void set_battery_bms_state(uint8_t state)
{
  digitalWrite(BMS_PIN, state);
  module_state[4] = state;
}


// (2) ---------- SOLENOID: VARS AND FUNCS ----------- (2)
/*
 SOLENOID_PIN : Arduino pin in charge of the solenoid control signal.

 set_solenoid_state: Activates or deactivates the solenoid in order to
                     lock or unlock the battery from station. It also
                     updates the module_state[5] variable, which is the
                     variable corresponding to battery solenoid state. 
*/

const int SOLENOID_PIN = 3;
void set_solenoid_state(uint8_t state)
{
  if(state == 0){
  digitalWrite(SOLENOID_PIN, 0);
  module_state[5] = 0;

  }else if(state == 1){
  analogWrite(SOLENOID_PIN, 130);
  module_state[5] = 1;
  }
}


// (3) ---------- REED SWITCH: VARS AND FUNCS ----------- (3)
/*
 REED_SWITCH_PIN : Arduino pin attached to reed switch.

 read_and_update_reed_switch_state: Reads the state of the reed switch. if equal to 1, that means
                                    the battery is inside its slot. If equal to 0, it means it's 
                                    not. It also updates the module_state[6] variable, which is the
                                    variable corresponding to reed switch state. 
*/
const int REED_SWITCH_PIN = 19;
void read_and_update_reed_switch_state()
{
  module_state[6] = 1 - digitalRead(REED_SWITCH_PIN);
}


// (4) ---------- LED STRIP: VARS AND FUNCS ----------- (4)
/*
set_strip_color : Set color of whole LED strip, based on the RGB values
                  passed to the function. These RGB values go from 0 to 255.

set_strip_state : Set the state of the LED strip, from one of the predefined 
                  states. There are 5 predefined states: Off', 'Red', 'Green',
                  'Blue' and 'Purple'.
*/

const int LED_STRIP_DIN_PIN = 6;
const int NUM_LEDS_IN_STRIP = 60;
Adafruit_NeoPixel strip(NUM_LEDS_IN_STRIP, LED_STRIP_DIN_PIN, NEO_GRB + NEO_KHZ800);

void set_strip_color(uint8_t red, uint8_t green, uint8_t blue)
{
  for (int i = 0; i < NUM_LEDS_IN_STRIP; i++){strip.setPixelColor(i, red, green, blue);}
  strip.show();
}

void set_strip_state(uint8_t state)
{
  switch (state)
  {
  case 0: //STRIP IS TURNED OFF.
    set_strip_color(0, 0, 0);
    module_state[7] = 0;
    break;
  case 1: //STRIP TURNS RED.
    set_strip_color(100, 0, 0);
    module_state[7] = 1;
    break;
  case 2: //STRIP TURNS GREEN.
    set_strip_color(0, 100, 0);
    module_state[7] = 2;
    break;
  case 3: //STRIP TURNS BLUE.
    set_strip_color(0, 0, 100);
    module_state[7] = 3;
    break;
  case 4: //STRIP TURNS PURPLE.
    set_strip_color(60, 0, 100);
    module_state[7] = 4;
    break;
  }
}




// (5.1) ---------- CAN NETWORK : VARS ----------- (5.1)
/*
LOCAL_CAN_CS_PIN : Arduino pin connected to the Chip Select Pin (CS) of
                   the MCP2515 module connected to the local network.
                  
GLOBAL_CAN_CS_PIN : Arduino pin connected to the Chip Select Pin (CS) of
                    the MCP2515 module connected to the global network.
                
canMsg_local  : Struct for storing all message data coming from the local network.

canMsg_global : Struct for storing all message data coming from the local network.

mcp2515_local  : Class for controlling the MCP2515 module connected to the local network.

mcp2515_global : Class for controlling the MCP2515 module connected to the global network.   
*/
const int LOCAL_CAN_CS_PIN = 10;
const int GLOBAL_CAN_CS_PIN = 9;

struct can_frame canMsg_local; 
struct can_frame canMsg_global;

MCP2515 mcp2515_local(LOCAL_CAN_CS_PIN); 
MCP2515 mcp2515_global(GLOBAL_CAN_CS_PIN); 


uint8_t battery_data[11][8];
const uint32_t BATTERY_DATA_IDS[11] = {2550245121, 2550310657, 2550376193, 2550441729, 2550507265, 
                                       2550572801, 2550638337, 2550703873, 2550769409, 2550834945, 2550900481};

unsigned long send_battery_data_timer;
const int BATTERY_DATA_TRANSMISSION_PERIOD = 10000; //[ms]

unsigned long send_module_state_timer;
const int MODULE_STATE_TRANSMISSION_PERIOD = 500; //[ms]

unsigned long battery_connection_timer;
const int BATTERY_CONNECTION_TIMEOUT = 30000; //[ms]

unsigned long bms_reset_timer;
const int BMS_RESET_DURATION = 2000; //[ms]

// (5.2) ---------- CAN NETWORK : FUNCS ----------- (5.2)
/*
send_battery_data_from_local_to_global_network_and_update_module_states :
                  Read battery data from the local CAN network, use it to
                  update the module state (specifically, voltage, current, SOC
                  and Faults) and then said the read (unaltered) data over to
                  the global CAN network.

send_module_states_to_global_network :
                  Sends the most updated version of the module states over
                  the global CAN network.

set_module_states_from_global_network :
                 Read commands from the global network and execute them.
                 The Raspberry Py sends commands over the global network.
                 This function reads them and executes them by updating the 
                 module state. 
*/


void read_from_local_network_and_update_battery_data()
{
  if (mcp2515_local.readMessage(&canMsg_local) == MCP2515::ERROR_OK && !Serial.available()){
    for (int i = 0; i <= 11; i++){
      if (canMsg_local.can_id == BATTERY_DATA_IDS[i]){
        for (int j = 0; j <= 7; j++){
          battery_data[i][j] = canMsg_local.data[j];
        }
        break;
      }
    }
    battery_connection_timer = millis();
  } 
}


void send_battery_data_to_global_network()
{
  for (int i = 0; i <= 11; i++){
    canMsg_global.can_id = BATTERY_DATA_IDS[i] + MODULE_NUM;
    canMsg_global.can_dlc = 8;
    for (int j = 0; j <= 7; j++){
      canMsg_global.data[j] = battery_data[i][j];
    }
    mcp2515_global.sendMessage(&canMsg_global);
  }
  send_battery_data_timer = millis();
}


void update_module_state_from_battery_data()
{
  float pack_voltage = 0.1* combineBytes(battery_data[0][0], battery_data[0][1]);
  float pack_current = 0.1*(combineBytes(battery_data[0][2], battery_data[0][3]) - 32000);
  int soc            = battery_data[0][4];
  int num_faults = 0;
  for(int j = 0; j <= 7; j++){num_faults += bitRead(battery_data[0][5], j);}
  for(int j = 0; j <= 7; j++){num_faults += bitRead(battery_data[0][6], j);}
  for(int j = 0; j <= 7; j++){num_faults += bitRead(battery_data[0][7], j);}
  for(int j = 0; j <= 7; j++){num_faults += bitRead(battery_data[1][0], j);}
  for(int j = 0; j <= 7; j++){num_faults += bitRead(battery_data[1][1], j);}

  module_state[0] = uint8_t(map(pack_voltage, 0, 50, 0, 255));
  module_state[1] = uint8_t(map(pack_current, 0, 20, 0, 255));
  module_state[2] = uint8_t(soc);
  module_state[3] = uint8_t(num_faults);

}

void send_module_states_to_global_network()
{
  read_and_update_reed_switch_state();
  update_module_state_from_battery_data();
  canMsg_global.can_id = MODULE_ID;
  canMsg_global.can_dlc = 8;
  for (int j = 0; j <= 7; j++){
    canMsg_global.data[j] = module_state[j];
  }
  mcp2515_global.sendMessage(&canMsg_global);
  send_module_state_timer = millis();
}


void set_module_states_from_global_network()
{
  if (mcp2515_global.readMessage(&canMsg_global) == MCP2515::ERROR_OK && !Serial.available()){
    if(canMsg_global.can_id == COMMON_ID && canMsg_global.data[0] == MODULE_NUM){
      set_battery_bms_state(canMsg_global.data[1]);
      set_solenoid_state(canMsg_global.data[2]);
      set_strip_state(canMsg_global.data[3]);
    }
  }
}



void setup() {
  // put your setup code here, to run once:

  pinMode(BMS_PIN, OUTPUT);
  pinMode(SOLENOID_PIN, OUTPUT);
  pinMode(REED_SWITCH_PIN, INPUT_PULLUP);
  pinMode(LED_STRIP_DIN_PIN, OUTPUT);
  

  strip.begin();
  while (!Serial);
  Serial.begin(9600);
  SPI.begin();


  set_battery_bms_state(1);
  delay(2500);
  set_battery_bms_state(0);
  read_and_update_reed_switch_state();
  set_solenoid_state(0);
  set_strip_state(0);


  mcp2515_local.reset();
  mcp2515_global.reset();

  // The battery BMS has a baud rate of 250 kbps according
  // to the DataSheet sent by the Chinese.
  // The MCP2515 arduino module, has  an 8MHz clock.
  mcp2515_local.setBitrate(CAN_250KBPS, MCP_8MHZ); 
  mcp2515_global.setBitrate(CAN_250KBPS, MCP_8MHZ); 

  mcp2515_local.setNormalMode(); 
  mcp2515_global.setNormalMode();
  

  send_battery_data_timer = millis();
  send_module_state_timer = millis();
  battery_connection_timer = millis();
}



void loop() {

  set_module_states_from_global_network();


  if (millis() - send_module_state_timer > MODULE_STATE_TRANSMISSION_PERIOD){
    send_module_states_to_global_network();
  }


  if (millis() - send_battery_data_timer > BATTERY_DATA_TRANSMISSION_PERIOD){
    send_battery_data_to_global_network();
  }


  read_from_local_network_and_update_battery_data();


  if (millis() - battery_connection_timer > BATTERY_CONNECTION_TIMEOUT){

    set_battery_bms_state(1 - module_state[4]);
    bms_reset_timer = millis();

    if (millis() - bms_reset_timer > BMS_RESET_DURATION){
      set_battery_bms_state(1 - module_state[4]);
      battery_connection_timer = millis();
    }
  }


}












// --- DEBUGGING FUNCTIONS --- 

void visualize_global_network()
{
  if (mcp2515_global.readMessage(&canMsg_global) == MCP2515::ERROR_OK && !Serial.available()){
    Serial.print(canMsg_global.can_id);
    Serial.print(",");
    Serial.print(canMsg_global.data[0]);
    Serial.print(",");
    Serial.print(canMsg_global.data[1]);
    Serial.print(",");
    Serial.print(canMsg_global.data[2]);
    Serial.print(",");
    Serial.print(canMsg_global.data[3]);
    Serial.print(",");
    Serial.print(canMsg_global.data[4]);
    Serial.print(",");
    Serial.print(canMsg_global.data[5]);
    Serial.print(",");
    Serial.print(canMsg_global.data[6]);
    Serial.print(",");
    Serial.print(canMsg_global.data[7]);
    Serial.println(",");
    Serial.println("--------------------------");
  }
}


void visualize_local_network()
{
  if (mcp2515_local.readMessage(&canMsg_local) == MCP2515::ERROR_OK && !Serial.available()){
    Serial.print(canMsg_local.can_id);
    Serial.print(",");
    Serial.print(canMsg_local.data[0]);
    Serial.print(",");
    Serial.print(canMsg_local.data[1]);
    Serial.print(",");
    Serial.print(canMsg_local.data[2]);
    Serial.print(",");
    Serial.print(canMsg_local.data[3]);
    Serial.print(",");
    Serial.print(canMsg_local.data[4]);
    Serial.print(",");
    Serial.print(canMsg_local.data[5]);
    Serial.print(",");
    Serial.print(canMsg_local.data[6]);
    Serial.print(",");
    Serial.print(canMsg_local.data[7]);
    Serial.println(",");
    Serial.println("--------------------------");
  }
}


struct Module
{
  int x;
  void test()
  {
    
  }



};





























  

  
  

