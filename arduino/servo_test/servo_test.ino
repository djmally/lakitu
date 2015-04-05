#include <Servo.h>

Servo pan;  // Pan servo (x-axis rotation)
Servo tilt; // Tilt servo (y-axis rotation)
int serial_byte = 0; // Serial data buffer

void setup() {
    pan.attach(9);      // Pan servo on pin 9
    tilt.attach(10);    // Tilt servo on pin 10
}

void loop() {
  pan.write(0);
  tilt.write(0);
  pan.write(90);
  tilt.write(180);
}
