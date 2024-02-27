#include <mcp2515.h> 
#include <CanUtils.h>

// (1) DEFINITION OF CAN-BUS VARIABLES
struct can_frame canMsg = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}};
MCP2515 canNetworkGlobal(9); // CS pin of global CAN network is 9.



// (1) DEFINITION OF CAN-BUS VARIABLES
class EightChannelRelayModule_SoftwareTest{
    public:    
    bool channelsStates[8];
    const canUtils::MODULE_ADDRESS moduleAddress = canUtils::CONTROL_CENTER;


    EightChannelRelayModule_SoftwareTest(){}


    void serialPrintChannelsStates(){
        Serial.print("--------");
        Serial.print("CHANNELS STATES");
        Serial.print("--------"); Serial.println();

        for (int i=0; i<8; i++){
        Serial.print("CHANNEL");
        Serial.print(i);
        Serial.print(": ");
        Serial.println(channelsStates[i]);
        }
    }
    void readAndUpdateChannelsStates(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 5000){

        uint32_t initTime = millis();

        while (millis() - initTime <= executionTime){
            if (canUtils::readCanMsg(canNetwork, p_canMsg, moduleAddress, canUtils::EIGHT_CHANNEL_RELAY) == MCP2515::ERROR_OK){

              canUtils::ACTIVITY_CODE activityCode = 
              canUtils::getActivityCodeFromCanMsgCanId(p_canMsg->can_id);        

              switch (activityCode) {
              case canUtils::net2rpy_STATES_INFO_OF_EIGHT_CHANNEL_RELAY_MODULE:
                  for (int i=0; i<8; i++){channelsStates[i] = p_canMsg->data[i];}
                  serialPrintChannelsStates();
                  break;    
              }
           }
         }
    }


    void Menu(){
        int commandOptionChoice;
        bool ERROR_HAPPENED = false;
        uint8_t canId[8] = {0,0,0,0,0,0,0,0};
        canUtils::ACTIVITY_CODE activityCode;

        Serial.println("---------------------------------------------------------");
        Serial.println("WELCOME!: Please select one command option from the menu:");
        Serial.println("1 - readAndUpdateChannelsStates");
        Serial.println("2 - setChannelState");
        Serial.println("3 - setChannelsStates");
        Serial.println("4 - flipChannelState");
        Serial.println("5 - flipChannelsStates");
        Serial.print("ENTER OPTION NOW: ");
        while (!Serial.available()){}
        commandOptionChoice = Serial.readStringUntil("\n").toInt();
        Serial.println(commandOptionChoice);
        Serial.println();

        switch (commandOptionChoice){
        case 1:
            readAndUpdateChannelsStates(canNetworkGlobal, &canMsg);
            break;
        case 2:
            Serial.print("Enter the channel's name (0 through 7) whose state you want to set: ");
            while (!Serial.available()){}
            canId[0] = Serial.readStringUntil("\n").toInt();
            if (0<=canId[0] && canId[0]<=7){Serial.println(canId[0]);}
            else {Serial.println("VALUE_ERROR!"); ERROR_HAPPENED=true; break;}

            Serial.print("Enter the channel's state (0 or 1): ");
            while (!Serial.available()){}
            canId[1] = Serial.readStringUntil("\n").toInt();
            if (0<=canId[1] && canId[1]<=1){Serial.println(canId[1]);}
            else {Serial.println("VALUE_ERROR!"); ERROR_HAPPENED=true; break;}

            activityCode = canUtils::rpy2net_SET_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE;
            break;
        case 3:
            Serial.println("Enter the state (0 or 1) to set of: ");
            for (int i=0; i<8; i++){
                Serial.print("CHANNEL");
                Serial.print(i);
                Serial.print(": ");
                while (!Serial.available()){}
                canId[i] = Serial.readStringUntil("\n").toInt();
                if (0<=canId[i] && canId[i]<=1){Serial.println(canId[i]);}
                else {Serial.println("VALUE_ERROR!"); ERROR_HAPPENED=true; break;}
            }   
            activityCode = canUtils::rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE;
            break;
        case 4:
            Serial.print("Enter the channel's name (0 through 7) whose state you want to flip: ");
            while (!Serial.available()){}
            canId[0] = Serial.readStringUntil("\n").toInt();
            if (0<=canId[0] && canId[0]<=7){Serial.println(canId[0]);}
            else {Serial.println("VALUE_ERROR!"); ERROR_HAPPENED=true; break;}
               
            activityCode = canUtils::rpy2net_FLIP_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE;
            break;
        case 5:
            Serial.println("For each CHANNEL enter 1 to flip its state or 0 to leave its state unchanged:");
            for (int i=0; i<8; i++){
                Serial.print("CHANNEL");
                Serial.print(i);
                Serial.print(": ");
                while (!Serial.available()){}
                canId[i] = Serial.readStringUntil("\n").toInt();
                if (0<=canId[i] && canId[i]<=1){Serial.println(canId[i]);}
                else {Serial.println("VALUE_ERROR!"); ERROR_HAPPENED=true; break;}
            }   
            activityCode = canUtils::rpy2net_FLIP_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE;
            break;
        default:
          Serial.println("ERROR: Option not supported!");
            break;
        }

        
        if((2 <= commandOptionChoice) && (commandOptionChoice <= 5) && !ERROR_HAPPENED){

            canMsg.can_dlc = 8;
            for(int i=0; i<8; i++){canMsg.data[i] = canId[i];}

            canMsg.can_id =
            createCanMsgCanId(canUtils::HIGH_,
                              activityCode,
                              canUtils::EIGHT_CHANNEL_RELAY,
                              moduleAddress);

            canNetworkGlobal.sendMessage(&canMsg);

        }
        
    }

};


EightChannelRelayModule_SoftwareTest softwareTest;


void setup(){

Serial.begin(9600);
canUtils::stdCanNetworkSetUp(canNetworkGlobal);

}

void loop(){
    softwareTest.Menu();
}