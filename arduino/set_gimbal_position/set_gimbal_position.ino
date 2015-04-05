#include <Servo.h>
Servo pan;  // Pan servo (x-axis rotation)
Servo tilt; // Tilt servo (y-axis rotation)
char serial_byte; // Serial data buffer
String serial_string; // Concatenated string of serial data

void setup() {
    Serial.begin(9600); // Serial connection on 9600 baud
    pan.attach(9);      // Pan servo on pin 9
    tilt.attach(10);    // Tilt servo on pin 10
}

void loop() {
    serial_string = "";
    while(Serial.available()) {
        serial_byte = Serial.read();
        serial_string += serial_byte;
        delay(2);
    }
    
    if(serial_string.length() >= 6) {
      int pan_angle = serial_string.substring(0,3).toInt();
      int tilt_angle = serial_string.substring(3,6).toInt();
      Serial.println(pan_angle);
      pan.write(pan_angle);
      Serial.println(tilt_angle);
      tilt.write(tilt_angle);
    }
}
