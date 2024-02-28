#include <mcp2515.h> 
#include <CanUtils.h>

// (1) DEFINITION OF CAN-BUS VARIABLES
struct can_frame canMsg = {.can_id = 0, .can_dlc = 8, .data = {0,0,0,0,0,0,0,0}};
MCP2515 canNetworkGlobal(10); // CS pin of global CAN network is 9.


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


  void serialPrintBatteryStates(uint8_t batteryStatesIdx){
    if(batteryStatesIdx < 11){
      Serial.print("BATTERY_DATA_"); Serial.print(batteryStatesIdx); Serial.print(": ");

      for(int i=0; i<8; i++){
        Serial.print(batteryStates[batteryStatesIdx][i]);
        Serial.print(",");
      }
      Serial.println();
    }
  }
  void readAndUpdateBatteryStates(MCP2515& canNetwork, struct can_frame* p_canMsg, uint32_t executionTime = 12000){
    Serial.print("-----------------------");
    Serial.print("BATTERY STATES OF SLOT"); Serial.println(moduleAddressToTest);
    Serial.print("-----------------------"); Serial.println();

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
        Serial.print("---------------------------");
        Serial.print("PERIPHERALS STATES OF SLOT"); Serial.println(moduleAddressToTest);
        Serial.print("---------------------------"); Serial.println();

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
        Serial.print("BMS SOLENOID: ");          Serial.println(peripheralsStates[2]);
        Serial.print("DOOR_LOCK SOLENOID: ");    Serial.println(peripheralsStates[3]);
        Serial.print("BATTERY_LOCK SOLENOID: "); Serial.println(peripheralsStates[4]);
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

      Serial.print("Enter the solenoids's name ('BMS', 'DOOR_LOCK' or 'BATTERY_LOCK') whose state you want to set: ");
      while (!Serial.available()){}
      String solenoidName = Serial.readStringUntil("\n");

      if      (solenoidName == "BMS")         {helperStates.canId[0] = 0; Serial.println(solenoidName);}
      else if (solenoidName == "DOOR_LOCK")   {helperStates.canId[0] = 1; Serial.println(solenoidName);}
      else if (solenoidName == "BATTERY_LOCK"){helperStates.canId[0] = 2; Serial.println(solenoidName);}
      else {Serial.println("VALUE_ERROR!"); helperStates.ERROR_HAPPENED = true;}

    }
    void setSolenoidState_part2(struct MenuHelperStates& helperStates){

      Serial.print("Enter the solenoids's state (0 or 1): ");
      while (!Serial.available()){}
      helperStates.canId[1] = Serial.readStringUntil("\n").toInt();

      if (0<=helperStates.canId[1] && helperStates.canId[1]<=1){
        Serial.println(helperStates.canId[1]);
      } else {
        Serial.println("VALUE_ERROR!"); 
        helperStates.ERROR_HAPPENED = true;
      }
    }
    void setSolenoidsStates(struct MenuHelperStates& helperStates){

      Serial.println("Enter the state (0 or 1) to set of: ");

      for (int i=0; i<3; i++){
          Serial.print(solenoidsNames[i]);
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
    void flipSolenoidState(struct MenuHelperStates& helperStates){

      Serial.print("Enter the solenoids's name ('BMS', 'DOOR_LOCK' or 'BATTERY_LOCK') whose state you want to flip: ");
      while (!Serial.available()){}
      String solenoidName = Serial.readStringUntil("\n");

      if      (solenoidName == "BMS")         {helperStates.canId[0] = 0; Serial.println(solenoidName);}
      else if (solenoidName == "DOOR_LOCK")   {helperStates.canId[0] = 1; Serial.println(solenoidName);}
      else if (solenoidName == "BATTERY_LOCK"){helperStates.canId[0] = 2; Serial.println(solenoidName);}
      else {Serial.println("VALUE_ERROR!"); helperStates.ERROR_HAPPENED = true;}

    }
    void flipSolenoidsStates(struct MenuHelperStates& helperStates){

      Serial.println("For each SOLENOID enter 1 to flip its state or 0 to leave its state unchanged:");
      for (int i=0; i<3; i++){
          Serial.print(solenoidsNames[i]);
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
    void setLedStripState(struct MenuHelperStates& helperStates){

      Serial.print("Enter the state ('OFF', 'RED', 'GREEN', 'BLUE' or 'PURPLE') you want to set the LED strip to: ");
      while (!Serial.available()){}
      String ledStripState = Serial.readStringUntil("\n");

      if      (ledStripState == "OFF")    {helperStates.canId[0] = 0; Serial.println(ledStripState);}
      else if (ledStripState == "RED")    {helperStates.canId[0] = 1; Serial.println(ledStripState);}
      else if (ledStripState == "GREEN")  {helperStates.canId[0] = 2; Serial.println(ledStripState);}
      else if (ledStripState == "BLUE")   {helperStates.canId[0] = 3; Serial.println(ledStripState);}
      else if (ledStripState == "PURPLE") {helperStates.canId[0] = 4; Serial.println(ledStripState);}
      else {Serial.println("VALUE_ERROR!"); helperStates.ERROR_HAPPENED = true;}

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



void setup(){

}



void loop(){


}