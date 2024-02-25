#include <mcp2515.h> 
#include <CanUtils.h>

// -DEFINITION OF CAN-BUS VARIABLES-
struct can_frame canMsg; 
MCP2515 canNetworkGlobal(9); // CS pin of global CAN network is 9.


// -DEFINITION OF EIGHT-CHANNEL RELAY MODULE CLASS- 
class EightChannelRelayModule
{
  public:
  // (1) DEFINITION OF ENUMERATIONS
  enum CHANNEL_STATE {OFF, ON};
  enum CHANNEL_NAME 
  {
    CHANNEL0,
    CHANNEL1,
    CHANNEL2,
    CHANNEL3,
    CHANNEL4,
    CHANNEL5,
    CHANNEL6,
    CHANNEL7,    
  };

  // (2) DEFINITION OF VARIABLES
  CHANNEL_STATE channelStates[8];
  const int CHANNEL_PINS[8] = {A0, A1, A2, A3, A4, A5, 4, 5};
  const canUtils::MODULE_ADDRESS moduleAddress = canUtils::EIGHT_CHANNEL_RELAY;
  

  // (3) DEFINITION OF METHODS

  // (3.1) Constructor Method
  void EightChannelRelayModule(){}

  // (3.2) Internal Methods
  void stdSetUp(){
    for(int i; i<8; i++){pinMode(CHANNEL_PINS[i], OUTPUT);}
    setChannelStates({OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF});
  }
  void setChannelState(CHANNEL_NAME name, CHANNEL_STATE state){
        digitalWrite(CHANNEL_PINS[name], state);
        channelStates[name] = state;    
  }
  void setChannelStates(CHANNEL_STATE states[8]){
    for (int i=0; i<8; i++){
      setChannelState(static_cast<CHANNEL_NAME>(i), states[i]);
    }
  }
  void flipChannelState(CHANNEL_NAME name){
    setChannelState(name, !channelStates[name]);
  }
  void flipChannelStates(bool flipLogic[8]){
    for (int i=0; i<8; i++){
      if (flipLogic[i]){fipChannelState(static_cast<CHANNEL_NAME>(i));}
    }
  }

  // (3.3) Net2Rpy Methods
  void net2rpy_sendChannelStates(MCP2515& canNetwork, struct can_frame* p_canMsg){
    p_canMsg->can_dlc = 8;

    for (int i=0; i<8; i++){
      p_canMsg->data[i] = static_cast<uint8_t>(channelStates[i]);
    }
    p_canMsg->can_id = 
    canUtils::createCanMsgCanId(canUtils::MEDIUM_LOW, 
                                canUtils::net2rpy_STATES_INFO_OF_EIGHT_CHANNEL_RELAY_MODULE, 
                                canUtils::CONTROL_CENTER,
                                moduleAddress);

    canNetwork.sendMessage(p_canMsg);
  }

  // (3.4) Rpy2Net Methods
  void rpy2net_readAndExecuteCommands(MCP2515& canNetwork, struct can_frame* p_canMsg){
    if (canUtils::readCanMsg(canNetwork, p_canMsg, moduleAddress, canUtils::CONTROL_CENTER) == MCP2515::ERROR_OK){

      canUtils::ACTIVITY_CODE activityCode = 
      canUtils::getActivityCodeFromCanMsgCanId(p_canMsg->can_id);

      switch (activityCode) {
        case canUtils::rpy2net_SET_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE:
          rpy2net_setChannelState(p_canMsg->data);
          break;
        case canUtils::rpy2net_SET_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE:
          rpy2net_setChannelStates(p_canMsg->data);
          break;
        case canUtils::rpy2net_FLIP_STATE_OF_EIGHT_CHANNEL_RELAY_MODULE:
          rpy2net_flipChannelState(p_canMsg->data);
          break;
        case canUtils::rpy2net_FLIP_STATES_OF_EIGHT_CHANNEL_RELAY_MODULE:
          rpy2net_flipChannelStates(p_canMsg->data);
          break;
      }
    }
  }
  void rpy2net_setChannelState(uint8_t canData[8]){
    CHANNEL_NAME name = static_cast<CHANNEL_NAME>(canData[0]);
    CHANNEL_STATE state = static_cast<CHANNEL_STATE>(canData[1]);
    setChannelState(name, state);
  }
  void rpy2net_setChannelStates(uint8_t canData[8]){
    CHANNEL_STATE states[8];
    for (int i=0; i<8; i++){states[i] = static_cast<CHANNEL_STATE>(canData[i]);}
    setChannelStates(states);
  }
  void rpy2net_flipChannelState(uint8_t canData[8]){
    CHANNEL_NAME name = static_cast<CHANNEL_NAME>(canData[0]);
    fipChannelState(name);
  }
  void rpy2net_flipChannelStates(uint8_t canData[8]){
    bool flipLogic[8];
    for (int i=0; i<8; i++){flipLogic[i] = static_cast<bool>(canData[i]);}
    flpChannelStates(flipLogic);
  }

};


// -INTIALIZATION OF EIGHT-CHANNEL RELAY MODULE CLASS- 
EightChannelRelayModule eightChannelRelayModule;


void setup(){
  
  // Eight-channel relay module standard set-up.
  eightChannelRelayModule.stdSetUp();

  // CAN Network standard set-up.
  canUtils::stdCanNetworkSetUp(canNetworkGlobal)

}

void loop(){

  // Send module states.
  eightChannelRelayModule.net2rpy_sendChannelStates(canNetworkGlobal, &canMsg);

  // Receive orders and execute them.
  eightChannelRelayModule.rpy2net_readAndExecuteCommands(canNetworkGlobal, &canMsg);

}

