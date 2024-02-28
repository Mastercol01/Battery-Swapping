#include <mcp2515.h> 
#include <CanUtils.h>

// (1) DEFINITION OF CAN-BUS VARIABLES
struct can_frame canMsg = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}};
MCP2515 canNetworkGlobal(10); // CS pin of global CAN network is 9.



// (1) DEFINITION OF CAN-BUS VARIABLES
class EightChannelRelayModule_SoftwareTest{
    public:    
    bool channelsStates[8];
    const canUtils::MODULE_ADDRESS moduleAddress = canUtils::CONTROL_CENTER;

    struct MenuHelperStates {
      bool ERROR_HAPPENED = false;
      uint8_t canId[8] = {0,0,0,0,0,0,0,0};
      canUtils::ACTIVITY_CODE activityCode;
    };


    EightChannelRelayModule_SoftwareTest(){}

    void Menu(MCP2515& canNetwork, struct can_frame* p_canMsg){

        int commandOptionChoice;
        struct MenuHelperStates menuHelperStates;


        Serial.println("---------------------------------------------------------");
        Serial.println("WELCOME!: Please select one command option from the menu:");
        Serial.println("1 - readAndUpdateChannelsStates");
        Serial.println("2 - setChannelState");
        Serial.println("3 - setChannelsStates");
        Serial.println("4 - flipChannelState");
        Serial.println("5 - flipChannelsStates");
        Serial.println("6 - visualizeCanNetwork");
        Serial.print("ENTER OPTION NOW: ");
        while (!Serial.available()){}
        commandOptionChoice = Serial.readStringUntil("\n").toInt();
        Serial.println(commandOptionChoice);
        Serial.println();

        switch (commandOptionChoice){
        case 1:
          readAndUpdateChannelsStates(canNetwork, p_canMsg);
          break;
        case 2:
          setChannelState_part1(menuHelperStates);
          if(menuHelperStates.ERROR_HAPPENED){break;}
          setChannelState_part2(menuHelperStates);
          if(menuHelperStates.ERROR_HAPPENED){break;}
          menuHelperStates.activityCode = canUtils::rpy2net_SET_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE;
          break;
        case 3:
          setChannelsStates(menuHelperStates);
          if(menuHelperStates.ERROR_HAPPENED){break;}
          menuHelperStates.activityCode = canUtils::rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE;
          break;
        case 4:
          flipChannelState(menuHelperStates);
          if(menuHelperStates.ERROR_HAPPENED){break;}
          menuHelperStates.activityCode = canUtils::rpy2net_FLIP_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE;
          break;
        case 5:
          flipChannelsStates(menuHelperStates);
          if(menuHelperStates.ERROR_HAPPENED){break;}
          menuHelperStates.activityCode = canUtils::rpy2net_FLIP_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE;
          break;
        case 6:
          visualizeCanNetwork(canNetwork, p_canMsg);
          break;
        default:
          Serial.println("ERROR: Option not supported!");
          break;
        }

        
        if((2 <= commandOptionChoice) && (commandOptionChoice <= 5) && !menuHelperStates.ERROR_HAPPENED){

            canMsg.can_dlc = 8;
            for(int i=0; i<8; i++){canMsg.data[i] = menuHelperStates.canId[i];}

            canMsg.can_id =
            createCanMsgCanId(canUtils::HIGH_,
                              menuHelperStates.activityCode,
                              canUtils::EIGHT_CHANNEL_RELAY,
                              moduleAddress);

            canNetwork.sendMessage(p_canMsg);

        }

        if(!menuHelperStates.ERROR_HAPPENED){
          Serial.println();
          Serial.println("PROCESS DONE!");
        }
        
    }

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
    void readAndUpdateChannelsStates(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 2500){

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
    void setChannelState_part1(struct MenuHelperStates& helperStates){

      Serial.print("Enter the channel's name (0 through 7) whose state you want to set: ");
      while (!Serial.available()){}
      helperStates.canId[0] = Serial.readStringUntil("\n").toInt();

      if (0<=helperStates.canId[0] && helperStates.canId[0]<=7){
        Serial.println(helperStates.canId[0]);
      } else {
        Serial.println("VALUE_ERROR!"); 
        helperStates.ERROR_HAPPENED = true; 
      }
    }
    void setChannelState_part2(struct MenuHelperStates& helperStates){

      Serial.print("Enter the channel's state (0 or 1): ");
      while (!Serial.available()){}
      helperStates.canId[1] = Serial.readStringUntil("\n").toInt();

      if (0<=helperStates.canId[1] && helperStates.canId[1]<=1){
        Serial.println(helperStates.canId[1]);
      } else {
        Serial.println("VALUE_ERROR!"); 
        helperStates.ERROR_HAPPENED=true;
      }
    }
    void setChannelsStates(struct MenuHelperStates& helperStates){

      Serial.println("Enter the state (0 or 1) to set of: ");

      for (int i=0; i<8; i++){
          Serial.print("CHANNEL");
          Serial.print(i);
          Serial.print(": ");
          while (!Serial.available()){}
          helperStates.canId[i] = Serial.readStringUntil("\n").toInt();

          if (0<=helperStates.canId[i] && helperStates.canId[i]<=1){
            Serial.println(helperStates.canId[i]);
          } else {
            Serial.println("VALUE_ERROR!"); 
            helperStates.ERROR_HAPPENED=true; 
            return;
          }
      }   
    }
    void flipChannelState(struct MenuHelperStates& helperStates){

      Serial.print("Enter the channel's name (0 through 7) whose state you want to flip: ");
      while (!Serial.available()){}
      helperStates.canId[0] = Serial.readStringUntil("\n").toInt();

      if (0<=helperStates.canId[0] && helperStates.canId[0]<=7){
        Serial.println(helperStates.canId[0]);
      } else {
        Serial.println("VALUE_ERROR!"); 
        helperStates.ERROR_HAPPENED=true;
      }
    }
    void flipChannelsStates(struct MenuHelperStates& helperStates){

      Serial.println("For each CHANNEL enter 1 to flip its state or 0 to leave its state unchanged:");
      for (int i=0; i<8; i++){
          Serial.print("CHANNEL");
          Serial.print(i);
          Serial.print(": ");
          while (!Serial.available()){}
          helperStates.canId[i] = Serial.readStringUntil("\n").toInt();

          if (0<=helperStates.canId[i] && helperStates.canId[i]<=1){
            Serial.println(helperStates.canId[i]);
          } else {
            Serial.println("VALUE_ERROR!");
            helperStates.ERROR_HAPPENED=true; 
            return;
          }
      }   
    }
    void visualizeCanNetwork(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 2500){

      uint32_t initTime = millis();
      while (millis() - initTime <= executionTime){
        canUtils::visualizeCanNetwork(canNetwork, p_canMsg,
                                      canUtils::PRIORITY_LEVEL_NONE,
                                      canUtils::ACTIVITY_CODE_NONE,
                                      moduleAddress,
                                      canUtils::EIGHT_CHANNEL_RELAY);
      }



    }
  




































};


EightChannelRelayModule_SoftwareTest softwareTest;


void setup(){

Serial.begin(9600);
canUtils::stdCanNetworkSetUp(canNetworkGlobal);

}

void loop(){
    softwareTest.Menu(canNetworkGlobal, &canMsg);
}