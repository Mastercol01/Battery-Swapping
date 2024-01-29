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

const uint8_t NUM_MODULES = 8;
const uint8_t NUM_STATES  = 8;
const uint32_t COMMON_ID = 2550245121;
uint8_t modules_states[NUM_MODULES][NUM_STATES] = {{0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0},
                                                   {0,0,0,0,0,0,0,0}};

const uint8_t NUM_BATTERY_DATA_IDS  = 11;
const uint32_t battery_data_ids[NUM_BATTERY_DATA_IDS] = {2550245121, 2550310657, 2550376193, 2550441729, 2550507265, 
                                                         2550572801, 2550638337, 2550703873, 2550769409, 2550834945, 2550900481};
uint8_t batteries_data[NUM_MODULES][NUM_BATTERY_DATA_IDS][8];       



// (1.1) ---------- CAN NETWORK : VARS ----------- (1.1)
const int GLOBAL_CAN_CS_PIN = 53;
struct can_frame canMsg_global;
MCP2515 mcp2515_global(GLOBAL_CAN_CS_PIN);  


// (1.2) ---------- CAN NETWORK : VARS ----------- (1.2)

void update_modules_states_from_global_network()
{
if (mcp2515_global.readMessage(&canMsg_global) == MCP2515::ERROR_OK && !Serial.available()){
  if((canMsg_global.can_id < COMMON_ID) && (COMMON_ID - NUM_MODULES - 1 < canMsg_global.can_id)){
    uint8_t module_id = COMMON_ID - canMsg_global.can_id;
    for(uint8_t state_id = 1; state_id <= NUM_STATES; state_id++){
      modules_states[module_id - 1][state_id - 1] = canMsg_global.data[state_id - 1];}
    }
  }
}

void visualize_modules_states()
{ 
  for(int module_id = 1; module_id <= 2; module_id++){
    Serial.print(module_id);
    Serial.print(" : ");
    for(int k = 0; k <= 7; k++){
      Serial.print(modules_states[module_id-1][k]);
      Serial.print(",");
    }
    Serial.println("");
    Serial.println("-----------------");
  }
}



void set_modules_states(uint8_t module_id, uint8_t states[8])
{
  canMsg_global.can_id = COMMON_ID - module_id;
  canMsg_global.can_dlc = 8;
  for(int k = 0; k <= 7; k++){
      canMsg_global.data[k] = states[k];
  }
  mcp2515_global.sendMessage(&canMsg_global);
}


void update_batteries_data_from_global_network()
{
if (mcp2515_global.readMessage(&canMsg_global) == MCP2515::ERROR_OK && !Serial.available()){
    for(uint8_t i = 1; i <= NUM_BATTERY_DATA_IDS; i++){
      uint32_t battery_data_id = battery_data_ids[i - 1];
      if((battery_data_id < canMsg_global.can_id) && (canMsg_global.can_id < battery_data_id + NUM_BATTERY_DATA_IDS + 1)){
        uint8_t module_id = canMsg_global.can_id - battery_data_id;
        for(uint8_t j = 0; j <= 7; j++){
          batteries_data[module_id][battery_data_id][j] = canMsg_global.data[j];
        }
      }
    }
  }
}

unsigned int initial_time;
unsigned int current_time;
uint8_t vec[8] = {0,0,0,0,0,1,0,1};

void setup() {

  while (!Serial);
  Serial.begin(9600);
  SPI.begin();

  mcp2515_global.reset();

  // The battery BMS has a baud rate of 250 kbps according
  // to the DataSheet sent by the Chinese.
  // The MCP2515 arduino module, has  an 8MHz clock.
  mcp2515_global.setBitrate(CAN_250KBPS, MCP_8MHZ); 
  mcp2515_global.setNormalMode();


  // FILL 'batteries_data' INITIALLY WITH ZEROS
  for(int module_id = 1; module_id <= NUM_MODULES; module_id++){
    for(int battery_data_id = 1; battery_data_id <= NUM_BATTERY_DATA_IDS; battery_data_id++){
      for(int k = 0; k <= 7; k++){
        batteries_data[module_id-1][battery_data_id-1][k] = 0;
      }
    }
  }


  initial_time = millis();
}

void loop() {
  canMsg_global.can_id = 2550245116;
  canMsg_global.can_dlc = 8;
  canMsg_global.data[0] = 1;
  canMsg_global.data[1] = 1;
  canMsg_global.data[2] = 1;
  canMsg_global.data[3] = 1;
  canMsg_global.data[4] = 1;
  canMsg_global.data[5] = 1;
  canMsg_global.data[6] = 1;
  canMsg_global.data[7] = 1;
  mcp2515_global.sendMessage(&canMsg_global);
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




  /*
  update_modules_states_from_global_network();

  
  if((current_time - initial_time > 5000) && (current_time - initial_time <  5050)){
    visualize_modules_states();
     
    vec[5] = 1;
    vec[7] = 1;
    set_modules_states(1, vec);
    vec[5] = 0;
    vec[7] = 2;
    set_modules_states(2, vec);
    visualize_modules_states();

  }else if((current_time - initial_time > 10000) && (current_time - initial_time <  10050)){
    visualize_modules_states();
    vec[5] = 0;
    vec[7] = 2;
    set_modules_states(1, vec);
    vec[5] = 1;
    vec[7] = 1;
    set_modules_states(2, vec);
    visualize_modules_states();
    initial_time = current_time;
  }
  
  
  update_batteries_data_from_global_network();
*/



  /*
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
  */