#include <Servo.h>

Servo pan;  // Pan servo (x-axis rotation)
Servo tilt; // Tilt servo (y-axis rotation)
int serial_byte = 0; // Serial data buffer

void setup() {
    Serial.begin(9600); // Serial connection on 9600 baud
    pan.attach(9);      // Pan servo on pin 9
    tilt.attach(10);    // Tilt servo on pin 10
}

void loop() {
    if(Serial.available() > 0) {
        serial_byte = Serial.read();
    }
    /* A byte value of 255 indicates the start of a pan/tilt combination.
     * If we see this value, we know that the next 2 values read should be
     * the pan angle, followed by the tilt angle. */
    if(serial_byte == 255) {
        if(Serial.available() > 0) {
            serial_byte = Serial.read();
            pan.write(serial_byte);
        }
        if(Serial.available() > 0) {
            serial_byte = Serial.read();
            tilt.write(serial_byte);
        }
    }
}
