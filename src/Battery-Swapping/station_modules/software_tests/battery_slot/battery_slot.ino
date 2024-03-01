#include <mcp2515.h> 
#include <CanUtils.h>

// (1) DEFINITION OF CAN-BUS VARIABLES
struct can_frame canMsg = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}};
MCP2515 canNetworkGlobal(9); // CS pin of global CAN network is 9.


class BatterySlotModule_SoftwareTest
{
  public:
  uint8_t batteryStates[11][8];
  uint8_t peripheralsStates[5];
  const canUtils::MODULE_ADDRESS moduleAddressToTest;
  const canUtils::MODULE_ADDRESS moduleAddress = canUtils::CONTROL_CENTER;
  const String solenoidsNames[3] = {"BMS", "DOOR_LOCK", "BATTERY_LOCK"};

  struct MenuHelperStates {
    bool ERROR_HAPPENED = false;
    uint8_t canId[8] = {0,0,0,0,0,0,0,0};
    canUtils::ACTIVITY_CODE activityCode;
  };
  


  BatterySlotModule_SoftwareTest(canUtils::MODULE_ADDRESS moduleAddressToTest): moduleAddressToTest(moduleAddressToTest)
  {
    for(int j=0; j<11; j++){
      for(int i=0; i<8; i++){
        batteryStates[j][i]=0;
      }
    }
  }

    void Menu(MCP2515& canNetwork, struct can_frame* p_canMsg){

        int commandOptionChoice;
        struct MenuHelperStates menuHelperStates;

        Serial.println();
        Serial.println(F("Please select one command option from the menu:"));
        Serial.println(F("1 - readAndUpdateBatteryStates"));
        Serial.println(F("2 - readAndUpdatePeripheralsStates"));
        Serial.println(F("3 - setSolenoidState"));
        Serial.println(F("4 - setSolenoidsStates"));
        Serial.println(F("5 - flipSolenoidState"));
        Serial.println(F("6 - flipSolenoidsStates"));
        Serial.println(F("7 - setLedStripState"));
        Serial.println(F("8 - visualizeCanNetwork"));
        Serial.print(F("ENTER OPTION NOW: "));
        while (!Serial.available()){}
        commandOptionChoice = Serial.readStringUntil("\n").toInt();
        Serial.println(commandOptionChoice);
        Serial.println();


        switch (commandOptionChoice) {
          case 1:
            readAndUpdateBatteryStates(canNetwork, p_canMsg);
            break;
          case 2:
            readAndUpdatePeripheralsStates(canNetwork, p_canMsg);
            break;
          case 3:
            setSolenoidState_part1(menuHelperStates);
            if(menuHelperStates.ERROR_HAPPENED){break;}
            setSolenoidState_part2(menuHelperStates);
            if(menuHelperStates.ERROR_HAPPENED){break;}
            menuHelperStates.activityCode = canUtils::rpy2net_SET_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE;
            break;
          case 4:
            setSolenoidsStates(menuHelperStates);
            if(menuHelperStates.ERROR_HAPPENED){break;}
            menuHelperStates.activityCode = canUtils::rpy2net_SET_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE;
            break;
          case 5:
            flipSolenoidState(menuHelperStates);
            if(menuHelperStates.ERROR_HAPPENED){break;}
            menuHelperStates.activityCode = canUtils::rpy2net_FLIP_SOLENOID_STATE_OF_BATTERY_SLOT_MODULE;
            break;
          case 6:
            flipSolenoidsStates(menuHelperStates);
            if(menuHelperStates.ERROR_HAPPENED){break;}
            menuHelperStates.activityCode = canUtils::rpy2net_FLIP_SOLENOIDS_STATES_OF_BATTERY_SLOT_MODULE;
            break;
          case 7:
            setLedStripState(menuHelperStates);
            if(menuHelperStates.ERROR_HAPPENED){break;}
            menuHelperStates.activityCode = canUtils::rpy2net_SET_LED_STRIP_STATE_OF_BATTERY_SLOT_MODULE;
            break;
          case 8:
            visualizeCanNetwork(canNetwork, p_canMsg);
            break;
          default:
            Serial.println("ERROR: Option not supported!");
        }

        if((3 <= commandOptionChoice) && (commandOptionChoice <= 7) && !menuHelperStates.ERROR_HAPPENED){

            canMsg.can_dlc = 8;
            for(int i=0; i<8; i++){canMsg.data[i] = menuHelperStates.canId[i];}

            canMsg.can_id =
            createCanMsgCanId(canUtils::HIGH_,
                              menuHelperStates.activityCode,
                              moduleAddressToTest,
                              moduleAddress);

            canNetwork.sendMessage(p_canMsg);
        }

        if(!menuHelperStates.ERROR_HAPPENED){
          Serial.println();
          Serial.println(F("PROCESS DONE!"));
        }
    }

  void serialPrintBatteryStates(uint8_t batteryStatesIdx){
    if(batteryStatesIdx < 11){
      Serial.print(F("BATTERY_DATA_")); Serial.print(batteryStatesIdx); Serial.print(F(": "));

      for(int i=0; i<8; i++){
        Serial.print(batteryStates[batteryStatesIdx][i]);
        Serial.print(",");
      }
      Serial.println();
    }
  }
  void readAndUpdateBatteryStates(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 12000){
    Serial.print(F("---"));
    Serial.print(F("BATTERY STATES OF SLOT")); Serial.print(moduleAddressToTest);
    Serial.print(F("---")); Serial.println();

    uint32_t initTime = millis();

    while (millis() - initTime <= executionTime){
      if (canUtils::readCanMsg(canNetwork, p_canMsg, moduleAddress, moduleAddressToTest) == MCP2515::ERROR_OK){

        canUtils::ACTIVITY_CODE activityCode = 
        canUtils::getActivityCodeFromCanMsgCanId(p_canMsg->can_id); 

        switch (activityCode) {
          case canUtils::net2rpy_BATTERY_DATA_0:
            for(int i=0; i<8; i++){batteryStates[0][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(0);
            break;
          case canUtils::net2rpy_BATTERY_DATA_1:
            for(int i=0; i<8; i++){batteryStates[1][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(1);
            break;
          case canUtils::net2rpy_BATTERY_DATA_2:
            for(int i=0; i<8; i++){batteryStates[2][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(2);
            break;
          case canUtils::net2rpy_BATTERY_DATA_3:
            for(int i=0; i<8; i++){batteryStates[3][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(3);
            break;
          case canUtils::net2rpy_BATTERY_DATA_4:
            for(int i=0; i<8; i++){batteryStates[4][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(4);
            break;
          case canUtils::net2rpy_BATTERY_DATA_5:
            for(int i=0; i<8; i++){batteryStates[5][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(5);
            break;
          case canUtils::net2rpy_BATTERY_DATA_6:
            for(int i=0; i<8; i++){batteryStates[6][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(6);
            break;
          case canUtils::net2rpy_BATTERY_DATA_7:
            for(int i=0; i<8; i++){batteryStates[7][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(7);
            break;
          case canUtils::net2rpy_BATTERY_DATA_8:
            for(int i=0; i<8; i++){batteryStates[8][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(8);
            break;
          case canUtils::net2rpy_BATTERY_DATA_9:
            for(int i=0; i<8; i++){batteryStates[9][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(9);
            break;
          case canUtils::net2rpy_BATTERY_DATA_10:
            for(int i=0; i<8; i++){batteryStates[10][i] = p_canMsg->data[i];}
            serialPrintBatteryStates(10);
            break;
        }
      }
    }
  } 
  void serialPrintPeripheralsStates(){
        Serial.print(F("---"));
        Serial.print(F("PERIPHERALS STATES OF SLOT")); Serial.println(moduleAddressToTest);
        Serial.print(F("---")); Serial.println();

        Serial.print("LIMIT SWITCH: "); Serial.println(peripheralsStates[0]);
        Serial.print("LED STRIP: ");

        String ledStripState;
        switch (peripheralsStates[1]) {
          case 0: ledStripState = "OFF";    break;
          case 1: ledStripState = "RED";    break;
          case 2: ledStripState = "GREEN";  break;
          case 3: ledStripState = "BLUE";   break;
          case 4: ledStripState = "PURPLE"; break;
        }

        Serial.println(ledStripState);
        Serial.print(F("BMS SOLENOID: "));          Serial.println(peripheralsStates[2]);
        Serial.print(F("DOOR_LOCK SOLENOID: "));    Serial.println(peripheralsStates[3]);
        Serial.print(F("BATTERY_LOCK SOLENOID: ")); Serial.println(peripheralsStates[4]);
    }
    void readAndUpdatePeripheralsStates(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 2500){

        uint32_t initTime = millis();
        while (millis() - initTime <= executionTime){
            if (canUtils::readCanMsg(canNetwork, p_canMsg, moduleAddress, canUtils::EIGHT_CHANNEL_RELAY) == MCP2515::ERROR_OK){

              canUtils::ACTIVITY_CODE activityCode = 
              canUtils::getActivityCodeFromCanMsgCanId(p_canMsg->can_id);        

              switch (activityCode) {
              case canUtils::net2rpy_PERIPHERALS_STATES_OF_BATTERY_SLOT_MODULE:
                  for (int i=0; i<8; i++){peripheralsStates[i] = p_canMsg->data[i];}
                  serialPrintPeripheralsStates();
                  break;    
              }
           }
        }
    }
    void setSolenoidState_part1(struct MenuHelperStates& helperStates){

      Serial.print(F("Enter the solenoids's id [0 (BMS), 1 (DOOR_LOCK) or 2 (BATTERY_LOCK)] whose state you want to set: "));
      while (!Serial.available()){}
      uint8_t solenoidId = Serial.readStringUntil("\n").toInt();

      if      (solenoidId == 0){helperStates.canId[0] = 0; Serial.print(solenoidId); Serial.println(F(" (BMS)"));}
      else if (solenoidId == 1){helperStates.canId[0] = 1; Serial.print(solenoidId); Serial.println(F(" (DOOR_LOCK)"));}
      else if (solenoidId == 2){helperStates.canId[0] = 2; Serial.print(solenoidId); Serial.println(F(" (BATTERY_LOCK)"));}
      else {Serial.println("VALUE_ERROR!"); helperStates.ERROR_HAPPENED = true;}

    }
    void setSolenoidState_part2(struct MenuHelperStates& helperStates){

      Serial.print(F("Enter the solenoids's state (0 or 1): "));
      while (!Serial.available()){}
      helperStates.canId[1] = Serial.readStringUntil("\n").toInt();

      if (0<=helperStates.canId[1] && helperStates.canId[1]<=1){
        Serial.println(helperStates.canId[1]);
      } else {
        Serial.println(F("VALUE_ERROR!")); 
        helperStates.ERROR_HAPPENED = true;
      }
    }
    void setSolenoidsStates(struct MenuHelperStates& helperStates){

      Serial.println(F("Enter the state (0 or 1) to set of: "));

      for (int i=0; i<3; i++){
          Serial.print(solenoidsNames[i]);
          Serial.print(": ");
          while (!Serial.available()){}
          helperStates.canId[i] = Serial.readStringUntil("\n").toInt();

          if (0<=helperStates.canId[i] && helperStates.canId[i]<=1){
            Serial.println(helperStates.canId[i]);
          } else {
            Serial.println(F("VALUE_ERROR!")); 
            helperStates.ERROR_HAPPENED=true; 
            return;
          }
      }   
    }
    void flipSolenoidState(struct MenuHelperStates& helperStates){

      Serial.print(F("Enter the solenoids's id [0 (BMS), 1 (DOOR_LOCK) or 2 (BATTERY_LOCK)] whose state you want to flip: "));
      while (!Serial.available()){}
      uint8_t solenoidId = Serial.readStringUntil("\n").toInt();

      if      (solenoidId == 0){helperStates.canId[0] = 0; Serial.print(solenoidId); Serial.println(F(" (BMS)"));}
      else if (solenoidId == 1){helperStates.canId[0] = 1; Serial.print(solenoidId); Serial.println(F(" (DOOR_LOCK)"));}
      else if (solenoidId == 2){helperStates.canId[0] = 2; Serial.print(solenoidId); Serial.println(F(" (BATTERY_LOCK)"));}
      else {Serial.println("VALUE_ERROR!"); helperStates.ERROR_HAPPENED = true;}

    }
    void flipSolenoidsStates(struct MenuHelperStates& helperStates){

      Serial.println("For each SOLENOID enter 1 to flip its state or 0 to leave its state unchanged:");
      for (int i=0; i<3; i++){
          Serial.print(solenoidsNames[i]);
          Serial.print(F(": "));
          while (!Serial.available()){}
          helperStates.canId[i] = Serial.readStringUntil("\n").toInt();

          if (0<=helperStates.canId[i] && helperStates.canId[i]<=1){
            Serial.println(helperStates.canId[i]);
          } else { 
            Serial.println(F("VALUE_ERROR!"));
            helperStates.ERROR_HAPPENED=true; 
            return;
          }
      }   
    }
    void setLedStripState(struct MenuHelperStates& helperStates){

      Serial.print(F("Enter the state [0 (OFF), 1 (RED), 2 (GREEN), 3 (BLUE) or 4 (PURPLE)] you want to set the LED strip to: "));
      while (!Serial.available()){}
      uint8_t ledStripState = Serial.readStringUntil("\n").toInt();

      if      (ledStripState == 0){helperStates.canId[0] = 0; Serial.print(ledStripState); Serial.println(F(" (OFF)"));}
      else if (ledStripState == 1){helperStates.canId[0] = 1; Serial.print(ledStripState); Serial.println(F(" (RED)"));}
      else if (ledStripState == 2){helperStates.canId[0] = 2; Serial.print(ledStripState); Serial.println(F(" (GREEN)"));}
      else if (ledStripState == 3){helperStates.canId[0] = 3; Serial.print(ledStripState); Serial.println(F(" (BLUE)"));}
      else if (ledStripState == 4){helperStates.canId[0] = 4; Serial.print(ledStripState); Serial.println(F(" (PURPLE)"));}
      else {Serial.println(F("VALUE_ERROR!")); helperStates.ERROR_HAPPENED = true;}

    }
    void visualizeCanNetwork(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 5000){

      uint32_t initTime = millis();
      while (millis() - initTime <= executionTime){
        canUtils::visualizeCanNetwork(canNetwork, p_canMsg,
                                      canUtils::PRIORITY_LEVEL_NONE,
                                      canUtils::ACTIVITY_CODE_NONE,
                                      moduleAddress,
                                      moduleAddressToTest);
      }

    }

};
BatterySlotModule_SoftwareTest slots[8] =
{
  BatterySlotModule_SoftwareTest(canUtils::SLOT1),
  BatterySlotModule_SoftwareTest(canUtils::SLOT2),
  BatterySlotModule_SoftwareTest(canUtils::SLOT3),
  BatterySlotModule_SoftwareTest(canUtils::SLOT4),
  BatterySlotModule_SoftwareTest(canUtils::SLOT5),
  BatterySlotModule_SoftwareTest(canUtils::SLOT6),
  BatterySlotModule_SoftwareTest(canUtils::SLOT7),
  BatterySlotModule_SoftwareTest(canUtils::SLOT8),
};

void superMenu(BatterySlotModule_SoftwareTest arr[8], MCP2515& canNetwork, struct can_frame* p_canMsg){

  Serial.println(F("-----------------------------------------------------------------------------------------"));
  Serial.print(F("WELCOME!: Please enter the id (1 through 8) of the battery slot that you wish to control: "));
  while (!Serial.available()){}
  int commandOptionChoice = Serial.readStringUntil("\n").toInt();

  if ((1 <= commandOptionChoice) && (commandOptionChoice <= 8)){

    if (commandOptionChoice == 1 || commandOptionChoice == 4 || commandOptionChoice == 5 || commandOptionChoice == 8){
      Serial.print(F("SLOT")); Serial.println(commandOptionChoice);
      arr[commandOptionChoice-1].Menu(canNetwork, p_canMsg);
    } else {
      Serial.println(F("ID NOT YET SUPPORTED"));
    }

  } else{
    Serial.println(F("VALUE_ERROR"));
  }

}




void setup(){

Serial.begin(9600);
canUtils::stdCanNetworkSetUp(canNetworkGlobal);

}



void loop(){

  superMenu(slots, canNetworkGlobal, &canMsg);

}