/* 
MODULE DESRIPTION

This script controls the station's refrigeration system. 
The refrigeration system is composed of two PWM-controllable fans and a thermocouple for 
temperature sensing. This module instructs to arduino to constantly read the ambient temperature 
adjust the duty cycle that controls the fans' speed accordingly.
*/

#include <stdio.h>     
#include <math.h>   

// PINS SET-UP 
const int THERMISTOR_PIN = A7;
const int FAN_SPEEDS_CONTROL_PIN = 9;

// MODULE SET-UP 
const float Vcc = 5.0;                // The thermistor's supply voltage.
const float R1 = 33120.0;             // Resistance of the the thermistor's accompanying series resistor.
const int NUM_THERMISTOR_AVGS = 30;   
const float fanActivationTemperature = 26; 
const float fanMaxSpeedTemperature = 40;

// 25kHz PWM SET-UP 
// PWM output @ 25 kHz, only on pins 9 and 10.
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

// TEMPERATURE SENSING FUNCTION 
float readThermistorTemperature(){
  // Init vars
  float Vt; // Voltage drop across thermistor [V].
  float Rt; // Thermistor resistance [Ohm].
  float Tt; // Thermistor temperature [°C]

  // 1) READ SMOOTHED-OUT VOLTAGE FROM THERMISTOR PIN
  Vt = 0;
  for(int j=0; j<NUM_THERMISTOR_AVGS; j++){
    Vt += analogRead(THERMISTOR_PIN);
  }
  Vt /= NUM_THERMISTOR_AVGS;
  Vt = Vcc*Vt/1023.0;

  // 2) COMPUTE THERMISTOR RESISTANCE
  Rt = R1*Vt/(Vcc - Vt);

  // 3) COMPUTE THERMISTOR TEMPERATURE
  float A =  610.5282190830485;
  float B = -85.97402403405586;
  float C =  3.4037509247172553;
  float D = -0.007982876975644648;
  float E = -0.0019710091731159445;

  float lnRt = log(Rt);
  Tt = A + B*lnRt + C*pow(lnRt,2) + D*pow(lnRt,3) + E*pow(lnRt,4);
  return Tt;
}

// TEMPERATURE-BASED FAN CONTROL FUNCTION
float setFanSpeeds(float Tt){
  int dutyCycle = int(map(Tt, fanActivationTemperature, fanMaxSpeedTemperature, 32, 320));
  if      (dutyCycle <  32){dutyCycle = 0;}
  else if (dutyCycle > 320){dutyCycle = 320;}
  analogWrite25k(FAN_SPEEDS_CONTROL_PIN, dutyCycle);
  return 100*float(dutyCycle)/320;
}


void setup(){
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

  // 1) Read temperature.
  // 2) Set fans' speeds according to temperature.
  // 3) Print temperature and duty cycle to the serial monitor for revision.

  float Tt = readThermistorTemperature();
  float dutyCycle = setFanSpeeds(Tt);
  String dataString = "(Temperature, Fan duty cycle) = (";
  dataString = dataString + Tt + ", " + dutyCycle + ")";
  Serial.println(dataString);
}
