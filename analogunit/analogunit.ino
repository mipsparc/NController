#include <Adafruit_MCP4725.h>
#include <stdio.h>

#define MCP4725_address 0x60

//Servo myServo;
Adafruit_MCP4725 dac;
int last_pressure_angle;
int speed_value = 0;

void setup() {
  Serial.begin(19200);
  dac.begin(MCP4725_address);

  dac.setVoltage(0, false);

  //myServo.attach(A0);
}

void loop() {
  String input;
  String input_value_str;
  int input_value;
  
  /** 受信段 **/
  input = Serial.readStringUntil('\n');
  Serial.println(input);
  if (input.indexOf("EOF")) {
    input.replace("EOF", "");
  } else {
    return;
  }
  input_value_str = input.substring(1);
  input_value = input_value_str.toInt();

  // 速度計にアナログ出力する
  if (input.charAt(0) == 's') {
    speed_value = input_value;
  }

  // 圧力計サーボに指令する
  if (input.charAt(0) == 'p') {
    int pressure_angle = input_value;
    if (last_pressure_angle != pressure_angle) {
      //myServo.writeMicroseconds(pressure_angle);
      last_pressure_angle = pressure_angle;
    }
  }

  dac.setVoltage(speed_value, false);
  delay(50);
}
