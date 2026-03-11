#include <Servo.h>

Servo xServo;
int currentAngle = 90;

void setup() {
  Serial.begin(9600);
  xServo.attach(9); // Servo connected to Pin 9
  xServo.write(90);  // Start at center
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming string until the newline character
    String data = Serial.readStringUntil('\n');
    int targetAngle = data.toInt();
    
    // Safety check to ensure valid data
    if (targetAngle >= 0 && targetAngle <= 180) {
      xServo.write(targetAngle);
    }
  }
}