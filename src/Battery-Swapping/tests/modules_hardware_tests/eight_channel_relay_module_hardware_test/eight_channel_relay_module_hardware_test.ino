// ------ IMPORTATION OF LIBRARIES ------ 
#include <SPI.h>
#include <mcp2515.h> 
#include <Adafruit_NeoPixel.h>

// MCP2515 ARDUINO NANO CONNECTIONS
// VCC → 5v
// GND → GND
// CS (network) → D9
// SO → D12
// SI → D11
// SCK → D13
// INT → D2

uint32_t flipChannelTimer;
uint32_t flipChannelCounter;
uint32_t flipChannelTimeSkip = 1000;
uint8_t eightChannelRelayStates[8] = {0, 0, 0, 0, 0, 0, 0, 0};
const uint8_t EIGHT_CHANNEL_RELAY_PINS[8] = {A0, A1, A2, A3, A4, A5, 4, 5};

void setChannelState(uint8_t idx, uint8_t state){
    if(idx<8 && (state==0 || state==1)){
        eightChannelRelayStates[idx] = state;
        digitalWrite(EIGHT_CHANNEL_RELAY_PINS[idx], state);
    }
}
void fipChannelState(uint8_t idx){setChannelState(idx, !eightChannelRelayStates[idx]);}


void setup() {
    Serial.begin(9600);

    for(int i=0; i<8; i++){
        pinMode(EIGHT_CHANNEL_RELAY_PINS[i], OUTPUT);
        setChannelState(i, 0);
    }
    flipChannelCounter = 0;
    flipChannelTimer = 0;
}

void loop() {
    
    
    if(millis() - flipChannelTimer > flipChannelTimeSkip){
        if(flipChannelCounter < 8){
            flipChannelCounter++;}
        else{flipChannelCounter = 0;}

        fipChannelState(flipChannelCounter);
        flipChannelTimer = millis();
    }
    


}