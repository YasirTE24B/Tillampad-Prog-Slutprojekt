#include <Servo.h>
#include "U8glib.h"

U8GLIB_SSD1306_128X64 u8g(U8G_I2C_OPT_NO_ACK);
Servo Xservo;

// Pinnar
const int potPin = A0;
const int XservoPin = 9;
const int knappPin = 2;
const int redPin = 3;
const int greenPin = 5;
const int bluePin = 6;

const int SERVO_MIN = 70; 
const int SERVO_MAX = 100;
const int SERVO_START_POS = 90;

int mode = 0; // 0 = kamera, 1 = pot
bool isDead = false;
unsigned long lastDisplayUpdate = 0;
int currentBallX = 320;

void setup() {
  // Min python använder 115200 baudrate
  Serial.begin(115200);
  Xservo.attach(XservoPin);

  pinMode(knappPin, INPUT_PULLUP);
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  
  Xservo.write(SERVO_START_POS);
}

void updateOLED() {
  u8g.firstPage();  
  do {
    u8g.setFont(u8g_font_unifont);
    u8g.drawStr(0, 15, "lalala boll spel");
    u8g.drawStr(0, 35, mode == 0 ? "Vanlig" : "debug mode");
    u8g.drawStr(0, 55, isDead ? "du dogde" : "Lever");
  } while( u8g.nextPage() );
}

void setRGB(int r, int g, int b) {
  analogWrite(redPin, r);
  analogWrite(greenPin, g);
  analogWrite(bluePin, b);
}

void loop() {
  if (digitalRead(knappPin) == LOW) {
    mode = !mode;
    Serial.println("Bytte lage till nagot");
    delay(300); // kort debounce så att den inte spammar
  }

  int potValue = analogRead(potPin);
  // Serial.println(potValue);

  int servoAngle = map(potValue, 500, 800, SERVO_MIN, SERVO_MAX);
  int servoAngle2 = constrain(servoAngle, SERVO_MIN, SERVO_MAX);
  // Serial.println(servoAngle2);

  Xservo.write(servoAngle2);

  // Boll-data från min python
  if (mode == 1) {
    setRGB(0, 0, 255); // blå RGB (debug)
  } else {
    if (Serial.available() > 0) {
      String data = Serial.readStringUntil('\n');
      
      // Skicka data till python
      int commaIndex = data.indexOf(',');
      if (commaIndex > 0) {
          currentBallX = data.substring(0, commaIndex).toInt();
          isDead = data.substring(commaIndex + 1).toInt() == 1;
      }
    }
    
    if (isDead) setRGB(255, 0, 0); // röd RGB
    else setRGB(0, 255, 0); // grön RGB
  }

  // OLED update saker
  if (millis() - lastDisplayUpdate > 200) {
    updateOLED();
    lastDisplayUpdate = millis();
  }

  // delay(15); // För servot
}