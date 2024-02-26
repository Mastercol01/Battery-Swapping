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
    enum SOLENOID_NAME {BMS, DOOR_LOCK, BATTERY_LOCK};
    enum LED_STRIP_STATE {OFF, RED, GREEN, BLUE, PURPLE};

    const uint8_t LIMIT_SWITCH_PIN = 14;
    const uint8_t SOLENOIDS_PINS[3] = {15, 6, 3};

    bool limitSwitchState;                    // UN-PRESSED = 0, PRESSED = 1
    bool solenoidsStates[3];                  // {(BMS_OFF = 0, BMS_ON = 1), (DOOR_LOCKED = 0, DOOR_UNLOCKED = 1), (BATTERY_LOCKED = 0, BATTERY_UNLOCKED = 1)}
    LED_STRIP_STATE ledStripState;
    canUtils::MODULE_ADDRESS moduleAddress;

 
    BatterySlotModule(canUtils::MODULE_ADDRESS moduleAddress){
        this->moduleAddress = moduleAddress;
    }

    void getLimitSwitchState(){
        limitSwitchState = digitalRead(LIMIT_SWITCH_PIN);
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
        if      (state == OFF)   {setLedStripColor(0,   0,   0);}
        else if (state == RED)   {setLedStripColor(120, 0,   0);}
        else if (state == GREEN) {setLedStripColor(0,   120, 0);}
        else if (state == BLUE)  {setLedStripColor(0,   0,   120);}
        else if (state == PURPLE){setLedStripColor(60,  0,   104);}
    }
    void stdSetUp(){
        pinMode(LIMIT_SWITCH_PIN, INPUT);
        pinMode(LED_STRIP_PIN, OUTPUT);
        pinMode(SOLENOIDS_PINS[0], OUTPUT);
        pinMode(SOLENOIDS_PINS[1], OUTPUT);
        pinMode(SOLENOIDS_PINS[2], OUTPUT);

        getLimitSwitchState();
        setLedStripState(OFF);
        setSolenoidsStates((1, 0, 0));
    }


    void net2rpy_relayBatteryStates(MCP2515& canNetwork0, MCP2515& canNetwork1, struct can_frame* p_canMsg){

        if(canUtils::readCanMsg(canNetwork0, p_canMsg) == MCP2515::ERROR_OK){

            canUtils::ACTIVITY_CODE activityCode;
            canUtils::PRIORITY_LEVEL priorityLevel = canUtils::LOW_;
            
            switch (p_canMsg->can_id){
                case 2550245121:
                    priorityLevel = canUtils::MEDIUM_HIGH;
                    activityCode  = canUtils::net2rpy_BATTERY_DATA_0;
                    break;
                case 2550310657:
                    priorityLevel = canUtils::MEDIUM_LOW;
                    activityCode = canUtils::net2rpy_BATTERY_DATA_1;
                    break;
                case 2550376193:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_2;
                    break;
                case 2550441729:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_3;
                    break;
                case 2550507265:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_4;
                    break;
                case 2550572801:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_5;
                    break;
                case 2550638337:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_6;
                    break;
                case 2550703873:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_7;
                    break;
                case 2550769409:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_8;
                    break;
                case 2550834945:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_9;
                    break;
                case 2550900481:
                    activityCode = canUtils::net2rpy_BATTERY_DATA_10;
                    break;
            }
            p_canMsg->can_id = 
            canUtils::createCanMsgCanId(priorityLevel, 
                                        activityCode, 
                                        canUtils::CONTROL_CENTER, 
                                        moduleAddress);

            canNetwork1.sendMessage(p_canMsg);
        }
    }
    void net2rpy_sendPeripheralsStates(MCP2515& canNetwork, struct can_frame* p_canMsg){
        getLimitSwitchState();
        p_canMsg->can_dlc = 8;
        p_canMsg->data[0] = (uint8_t)limitSwitchState;
        p_canMsg->data[1] = (uint8_t)ledStripState;
        p_canMsg->data[2] = (uint8_t)solenoidsStates[0];
        p_canMsg->data[3] = (uint8_t)solenoidsStates[1];
        p_canMsg->data[4] = (uint8_t)solenoidsStates[2];

        p_canMsg->can_id = 
        canUtils::createCanMsgCanId(canUtils::MEDIUM_HIGH, 
                                    canUtils::net2rpy_PERIPHERALS_STATES_OF_BATTERY_SLOT_MODULE, 
                                    canUtils::CONTROL_CENTER,
                                    moduleAddress);

        canNetwork.sendMessage(p_canMsg);
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
 
  

};




// -INTIALIZATION OF EIGHT-CHANNEL RELAY MODULE CLASS- 
BatterySlotModule batterySlotModule(canUtils::SLOT1);


void setup(){
  
  // Eight-channel relay module standard set-up.
  batterySlotModule.stdSetUp();

  // Global CAN Network standard set-up.
  canUtils::stdCanNetworkSetUp(canNetworkGlobal);

  // Battery CAN Network standard set-up.
  canUtils::stdCanNetworkSetUp(canNetworkBattery);

}

void loop(){

    // Send battery states.
    batterySlotModule.net2rpy_relayBatteryStates(canNetworkBattery, canNetworkGlobal, &canMsg_battery);

    // Send peripherals states.
    batterySlotModule.net2rpy_sendPeripheralsStates(canNetworkGlobal, &canMsg_net2rpy);

    // Receive orders and execute them.
    batterySlotModule.rpy2net_readAndExecuteCommands(canNetworkGlobal, &canMsg_net2rpy);

}