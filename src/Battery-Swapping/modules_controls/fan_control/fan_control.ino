// -------------- IMPORTATION OF LIBRARIES --------------
#include <stdio.h>     
#include <math.h>   

// -------------- MODULE SET-UP --------------
float Vcc = 5.0;
float R1 = 33120.0;
int NUM_Tt_AVGS = 30;
int THERMISTOR_PIN = A7;
int FAN_SPEEDS_CONTROL_PIN = 9;
float fanActivationThresholdTemperature = 27; 
float fanMaxedOutSpeedThresholdTemperature = 42;

// -------------- 25kHz PWM SET-UP --------------
//PWM output @ 25 kHz, only on pins 9 and 10.
// Output value should be between 0 and 320, inclusive.
void analogWrite25k(int pin, int value){
  switch (pin){
    case 9:
      OCR1A = value;
      break;
      
    case 10:
      OCR1B = value;
      break;
      
    default: // no other pin will work
      break;
  }
}

// -------------- TEMPERATURE SENSING SET-UP --------------
float readThermistorTemperature(){

  // 1) READ THERMISTOR VOLTAGE
  float Vt = 0;
  for(int j=0; j<NUM_Tt_AVGS; j++){
    Vt += analogRead(THERMISTOR_PIN);
  }
  Vt /= NUM_Tt_AVGS;
  Vt = Vcc*Vt/1023.0;

  // 2) COMPUTE THERMISTOR RESISTANCE
  float Rt = R1*Vt/(Vcc - Vt);

  // 3) COMPUTE THERMISTOR TEMPERATURE
  float A =  610.5282190830485;
  float B = -85.97402403405586;
  float C =  3.4037509247172553;
  float D = -0.007982876975644648;
  float E = -0.0019710091731159445;

  float lnRt = log(Rt);
  float Tt = A + B*lnRt + C*pow(lnRt,2) + D*pow(lnRt,3) + E*pow(lnRt,4);

  // 4) RETURN VALUE
  return Tt;
}

// -------------- TEMPERATURE SENSING SET-UP --------------

float setFanSpeeds(float Tt){
  int dutyCycle = int(map(Tt, fanActivationThresholdTemperature, fanMaxedOutSpeedThresholdTemperature, 32, 320));
  if      (dutyCycle <  32){dutyCycle = 0;}
  else if (dutyCycle > 320){dutyCycle = 320;}
  analogWrite25k(FAN_SPEEDS_CONTROL_PIN, dutyCycle);
  return 100*float(dutyCycle)/320;
}



void setup(){
  // --- INITIAL SET-UP---
  Serial.begin(9600);
  pinMode(THERMISTOR_PIN, INPUT);

  // -25KHZ SET-UP
  // Configure Timer 1 for PWM @ 25 kHz.
  TCCR1A = 0; // undo the configuration done by...
  TCCR1B = 0; // ...the Arduino core library
  TCNT1 = 0; // reset timer
  TCCR1A = _BV(COM1A1) // non-inverted PWM on ch. A
           | _BV(COM1B1) // same on ch; B
           | _BV(WGM11); // mode 10: ph. correct PWM, TOP = ICR1
  TCCR1B = _BV(WGM13) // ditto
           | _BV(CS10); // prescaler = 1
  ICR1 = 320; // TOP = 320
  // Set the PWM pins as output.
  pinMode( 9, OUTPUT);
  pinMode(10, OUTPUT);
}

void loop() {
  float Tt = readThermistorTemperature();
  float dutyCycle = setFanSpeeds(Tt);
  String dataString = "(Temperature, Fan duty cycle) = (";
  dataString = dataString + Tt + ", " + dutyCycle + ")";
  Serial.println(dataString);
  

}
