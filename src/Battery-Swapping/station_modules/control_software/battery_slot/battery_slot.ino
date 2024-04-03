#include <SPI.h>
#include <mcp2515.h> 
#include <CanUtils.h>
#include <Adafruit_NeoPixel.h>


// -DEFINITION OF CAN-BUS VARIABLES-
struct can_frame canMsg_battery = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}};
struct can_frame canMsg_net2rpy = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}};
MCP2515 canNetworkGlobal(10); // CS pin of global CAN network is 10.
MCP2515 canNetworkBattery(9); // CS pin of battery CAN network is 9.


// -DEFINITION OF LED-STRIP VARIABLES AND UTILITY FUNCTIONS-
const uint8_t LED_STRIP_PIN = 5;
const uint8_t NUM_LEDS_IN_STRIP = 60;
Adafruit_NeoPixel strip(NUM_LEDS_IN_STRIP, LED_STRIP_PIN, NEO_GRB + NEO_KHZ800);
void setLedStripColor(uint8_t red, uint8_t green, uint8_t blue){
  for (int i = 0; i < NUM_LEDS_IN_STRIP; i++){
    strip.setPixelColor(i, red, green, blue);}
  strip.show();
}



class BatterySlotModule
{
    public:
    
    enum SOLENOID_NAME {BMS=0, DOOR_LOCK=1, BATTERY_LOCK=2};
    enum LED_STRIP_STATE {OFF=0, RED=1, GREEN=2, BLUE=3, PURPLE=4};

    const uint8_t LIMIT_SWITCH_PIN = A0;
    const uint8_t SOLENOIDS_PINS[3] = {15, 6, 3};
    const canUtils::MODULE_ADDRESS moduleAddress;

    bool limitSwitchState;                    // UN-PRESSED = 0, PRESSED = 1
    bool solenoidsStates[3];                  // {(BMS_OFF = 0, BMS_ON = 1), (DOOR_LOCKED = 0, DOOR_UNLOCKED = 1), (BATTERY_LOCKED = 0, BATTERY_UNLOCKED = 1)}
    LED_STRIP_STATE ledStripState;
    uint8_t batteryStates[11][8];
    bool batteryCanBusErrorState ;            // NO-ERROR = 0, ERROR = 1

    const canUtils::ACTIVITY_CODE net2rpy_batteryActivityCodes[11] =
    {
      canUtils::net2rpy_BATTERY_DATA_0,
      canUtils::net2rpy_BATTERY_DATA_1,
      canUtils::net2rpy_BATTERY_DATA_2,
      canUtils::net2rpy_BATTERY_DATA_3,
      canUtils::net2rpy_BATTERY_DATA_4,
      canUtils::net2rpy_BATTERY_DATA_5,
      canUtils::net2rpy_BATTERY_DATA_6,
      canUtils::net2rpy_BATTERY_DATA_7,
      canUtils::net2rpy_BATTERY_DATA_8,
      canUtils::net2rpy_BATTERY_DATA_9,
      canUtils::net2rpy_BATTERY_DATA_10
    };
    uint32_t relayBatteryStatesTimer;
    uint32_t sendPeripheralsStatesTimer;
    uint32_t batteryCanBusErrorStateTimer;
    uint32_t relayBatteryStatesTimeout = 50;
    uint32_t sendPeripheralsStatesTimeout = 50;
    uint32_t batteryCanBusErrorStateTimeout = 4000;


 
    BatterySlotModule(canUtils::MODULE_ADDRESS moduleAddress):moduleAddress(moduleAddress){
      for(int j=0; j<11; j++){
        for(int i=0; i<8; i++){
          batteryStates[j][i] = 0;
        }
      }
    }

    void getLimitSwitchState(){
        limitSwitchState = !digitalRead(LIMIT_SWITCH_PIN);
    }
    void setSolenoidState(SOLENOID_NAME name, bool state){
        digitalWrite(SOLENOIDS_PINS[name], state);
        solenoidsStates[name] = state;
    }
    void setSolenoidsStates(bool states[3]){
        for (int i=0; i<3; i++){
            setSolenoidState(static_cast<SOLENOID_NAME>(i), states[i]);
        }
    }
    void flipSolenoidState(SOLENOID_NAME name){
        setSolenoidState(name, !solenoidsStates[name]);
    }
    void flipSolenoidsStates(bool flipLogic[3]){
        for (int i=0; i<3; i++){
            if (flipLogic[i]){flipSolenoidState(static_cast<SOLENOID_NAME>(i));}
        }
    }
    void setLedStripState(LED_STRIP_STATE state){
      switch (state) {
        case OFF:    setLedStripColor(0,   0,   0);   ledStripState = state; break;
        case RED:    setLedStripColor(120, 0,   0);   ledStripState = state; break;
        case GREEN:  setLedStripColor(0,   120, 0);   ledStripState = state; break;
        case BLUE:   setLedStripColor(0,   0,   120); ledStripState = state; break;
        case PURPLE: setLedStripColor(60,  0,   104); ledStripState = state; break;
      }
    }
    void stdSetUp(){
        pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
        pinMode(LED_STRIP_PIN, OUTPUT);
        pinMode(SOLENOIDS_PINS[0], OUTPUT);
        pinMode(SOLENOIDS_PINS[1], OUTPUT);
        pinMode(SOLENOIDS_PINS[2], OUTPUT);

        getLimitSwitchState();
        setLedStripState(OFF);
        setSolenoidState(BMS, 0);
        setSolenoidState(DOOR_LOCK, 0);
        setSolenoidState(BATTERY_LOCK, 0);
        resetBatteryCanBusErrorAndTimer();
        relayBatteryStatesTimer = millis();
        sendPeripheralsStatesTimer = millis();
    }

    void resetBatteryCanBusErrorAndTimer(){
      batteryCanBusErrorState = 0;
      batteryCanBusErrorStateTimer = millis();
    } 
    void updateBatteryCanBusErrorState(){
      if(!limitSwitchState || !solenoidsStates[0]){
        resetBatteryCanBusErrorAndTimer();
      } else if(millis() - batteryCanBusErrorStateTimer > batteryCanBusErrorStateTimeout){
        batteryCanBusErrorState = 1;
      } else {
        batteryCanBusErrorState = 0;
      }
    }
    void getBatteryStates(MCP2515& canNetwork, struct can_frame* p_canMsg){
      getLimitSwitchState();
      updateBatteryCanBusErrorState();

      if(limitSwitchState && solenoidsStates[0] && !batteryCanBusErrorState){
        if(canUtils::readCanMsg(canNetwork, p_canMsg) == MCP2515::ERROR_OK){
          switch (p_canMsg->can_id){
              case 2550245121: for(int i=0; i<8; i++){batteryStates[0][i]  = p_canMsg->data[i];} break;
              case 2550310657: for(int i=0; i<8; i++){batteryStates[1][i]  = p_canMsg->data[i];} break;
              case 2550376193: for(int i=0; i<8; i++){batteryStates[2][i]  = p_canMsg->data[i];} break;
              case 2550441729: for(int i=0; i<8; i++){batteryStates[3][i]  = p_canMsg->data[i];} break;
              case 2550507265: for(int i=0; i<8; i++){batteryStates[4][i]  = p_canMsg->data[i];} break;
              case 2550572801: for(int i=0; i<8; i++){batteryStates[5][i]  = p_canMsg->data[i];} break;
              case 2550638337: for(int i=0; i<8; i++){batteryStates[6][i]  = p_canMsg->data[i];} break;
              case 2550703873: for(int i=0; i<8; i++){batteryStates[7][i]  = p_canMsg->data[i];} break;
              case 2550769409: for(int i=0; i<8; i++){batteryStates[8][i]  = p_canMsg->data[i];} break;
              case 2550834945: for(int i=0; i<8; i++){batteryStates[9][i]  = p_canMsg->data[i];} break;
              case 2550900481: for(int i=0; i<8; i++){batteryStates[10][i] = p_canMsg->data[i];} break;
          }
          resetBatteryCanBusErrorAndTimer();
        }
      }
    }
    void net2rpy_relayBatteryStates(MCP2515& canNetwork, struct can_frame* p_canMsg){
      getLimitSwitchState();
      updateBatteryCanBusErrorState();

      if(limitSwitchState && solenoidsStates[0] && !batteryCanBusErrorState){
        canUtils::PRIORITY_LEVEL priorityLevel;
        canUtils::ACTIVITY_CODE activityCode;

        for(int j=0; j<11; j++){
          switch (j) {
            case 0:  priorityLevel = canUtils::MEDIUM_HIGH; break;
            case 1:  priorityLevel = canUtils::MEDIUM_LOW;  break;
            default: priorityLevel = canUtils::LOW_;        break;
          }
          activityCode = net2rpy_batteryActivityCodes[j];

          p_canMsg->can_dlc = 8;
          for(int i=0; i<8; i++){p_canMsg->data[i] = batteryStates[j][i];}
          
          p_canMsg->can_id =
          canUtils::createCanMsgCanId(priorityLevel,
                                      activityCode,
                                      canUtils::CONTROL_CENTER, 
                                      moduleAddress);

          canNetwork.sendMessage(p_canMsg);
        }
      } 
    }
    net2rpy_relayBatteryStatesPeriodically(MCP2515& canNetwork, struct can_frame* p_canMsg){
      if(millis() - relayBatteryStatesTimer > relayBatteryStatesTimeout){
        net2rpy_relayBatteryStates(canNetwork, p_canMsg);
        relayBatteryStatesTimer = millis();
      }
    }
    void net2rpy_sendPeripheralsStates(MCP2515& canNetwork, struct can_frame* p_canMsg){
        p_canMsg->can_dlc = 8;
        getLimitSwitchState();
        updateBatteryCanBusErrorState();
        p_canMsg->data[0] = (uint8_t)limitSwitchState;
        p_canMsg->data[1] = (uint8_t)ledStripState;
        p_canMsg->data[2] = (uint8_t)solenoidsStates[0];
        p_canMsg->data[3] = (uint8_t)solenoidsStates[1];
        p_canMsg->data[4] = (uint8_t)solenoidsStates[2];
        p_canMsg->data[5] = (uint8_t)batteryCanBusErrorState;

        p_canMsg->can_id = 
        canUtils::createCanMsgCanId(canUtils::MEDIUM_HIGH, 
                                    canUtils::net2rpy_PERIPHERALS_STATES_OF_BATTERY_SLOT_MODULE, 
                                    canUtils::CONTROL_CENTER,
                                    moduleAddress);

        canNetwork.sendMessage(p_canMsg);
    }
    void net2rpy_sendPeripheralsStatesPeriodically(MCP2515& canNetwork, struct can_frame* p_canMsg){
      if(millis() - sendPeripheralsStatesTimer > sendPeripheralsStatesTimeout){
        net2rpy_sendPeripheralsStates(canNetwork, p_canMsg);
        sendPeripheralsStatesTimer = millis();
      }
    }

    void rpy2net_readAndExecuteCommands(MCP2515& canNetwork, struct can_frame* p_canMsg){
        if (canUtils::readCanMsg(canNetwork, p_canMsg, moduleAddress, canUtils::CONTROL_CENTER) == MCP2515::ERROR_OK){

            canUtils::ACTIVITY_CODE activityCode = 
            canUtils::getActivityCodeFromCanMsgCanId(p_canMsg->can_id);

            switch (activityCode) {
                case canUtils::rpy2net_SET_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE:
                rpy2net_setSolenoidState(p_canMsg->data);
                break;
                case canUtils::rpy2net_SET_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE:
                rpy2net_setSolenoidsStates(p_canMsg->data);
                break;
                case canUtils::rpy2net_FLIP_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE:
                rpy2net_flipSolenoidState(p_canMsg->data);
                break;
                case canUtils::rpy2net_FLIP_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE:
                rpy2net_flipSolenoidsStates(p_canMsg->data);
                break;
                case canUtils::rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE:
                rpy2net_setLedStripState(p_canMsg->data);
                break;
                case canUtils::rpy2net_RESET_BATTERY_CAN_BUS_ERROR_STATE_AND_TIMER:
                rpy2net_resetBatteryCanBusErrorAndTimer();
                break;
            }
        }
    }
    void rpy2net_setSolenoidState(uint8_t canData[8]){
        SOLENOID_NAME name = static_cast<SOLENOID_NAME>(canData[0]);
        bool state = (bool)canData[1];
        setSolenoidState(name, state);
    }
    void rpy2net_setSolenoidsStates(uint8_t canData[8]){
        bool states[3];
        states[0] = (bool)canData[0];
        states[1] = (bool)canData[1];
        states[2] = (bool)canData[2];
        setSolenoidsStates(states);
    }
    void rpy2net_flipSolenoidState(uint8_t canData[8]){
        SOLENOID_NAME name = static_cast<SOLENOID_NAME>(canData[0]);
        flipSolenoidState(name);
    }
    void rpy2net_flipSolenoidsStates(uint8_t canData[8]){
        bool flipLogic[3];
        flipLogic[0] = (bool)canData[0];
        flipLogic[1] = (bool)canData[1];
        flipLogic[2] = (bool)canData[2];
        flipSolenoidsStates(flipLogic);
    }
    void rpy2net_setLedStripState(uint8_t canData[8]){
        LED_STRIP_STATE state = static_cast<LED_STRIP_STATE>(canData[0]);
        setLedStripState(state);
    }
    void rpy2net_resetBatteryCanBusErrorAndTimer(){
      resetBatteryCanBusErrorAndTimer();
    }
 
  

};




// -INTIALIZATION OF EIGHT-CHANNEL RELAY MODULE CLASS- 
BatterySlotModule batterySlotModule(canUtils::SLOT8);

uint32_t time_test;

void setup(){
  Serial.begin(9600);
  
  // Eight-channel relay module standard set-up.
  batterySlotModule.stdSetUp();

  // Global CAN Network standard set-up.
  canUtils::stdCanNetworkSetUp(canNetworkGlobal);

  // Battery CAN Network standard set-up.
  canUtils::stdCanNetworkSetUp(canNetworkBattery);

}        

void loop(){
    
    // Receive and store battery states.
    batterySlotModule.getBatteryStates(canNetworkBattery, &canMsg_battery);

    // Relay battery states every x amount of time.
    batterySlotModule.net2rpy_relayBatteryStatesPeriodically(canNetworkGlobal, &canMsg_net2rpy);

    // Send peripherals states.
    batterySlotModule.net2rpy_sendPeripheralsStatesPeriodically(canNetworkGlobal, &canMsg_net2rpy);

    // Receive orders and execute them.
    batterySlotModule.rpy2net_readAndExecuteCommands(canNetworkGlobal, &canMsg_net2rpy);



    

}