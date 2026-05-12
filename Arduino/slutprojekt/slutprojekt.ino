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
const int piezoPin = 10;

const int SERVO_MIN = 70; 
const int SERVO_MAX = 100;
const int SERVO_START_POS = 90;

int mode = 0; // 0 = kamera, 1 = pot
int currentBallX = 320;
bool isDead = false;
unsigned long lastDisplayUpdate = 0;
unsigned long lastSerialSend = 0;

void setup() {
  Serial.begin(115200); // python använder 115200 baudrate
  Xservo.attach(XservoPin);

  pinMode(knappPin, INPUT_PULLUP);
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  pinMode(piezoPin, OUTPUT);
  
  Xservo.write(SERVO_START_POS);
}

void buttonPress() {
  if (digitalRead(knappPin) == LOW) {
    mode = !mode;
    while(Serial.available() > 0) Serial.read();
    Serial.println("Bytte lage (DEBUG ELLER KAMERA)");
    delay(300); // kort debounce så att den inte spammar
  }
}

void updateOLED() {
  if (millis() - lastDisplayUpdate > 200) {
    u8g.firstPage();  
    do {
      u8g.setFont(u8g_font_unifont);

      if (mode == 1) {
        u8g.drawStr(0, 15, "DEBUG MODE");
      } else {
        u8g.drawStr(0, 15, "lalala boll spel");
      }

      if (isDead && mode == 0) {
        u8g.drawStr(0, 35, "DU DOG :(");
      } else if (mode == 0) {
        u8g.drawStr(0, 35, "Vanlig");
      } else {
        u8g.drawStr(0, 35, "Debug");
      }

      if (mode == 1) {
        int potValue = analogRead(potPin); 
        int debugX = map(potValue, 500, 800, 640, 0); // mappar pot värde 500-800 till 0px-640px (kamerans resolution)
        debugX = constrain(debugX, 0, 640); // så att den inte ger något dumt värde

        String potStr = "POT: " + String(debugX);
        u8g.drawStr(0, 55, potStr.c_str());
      } else {
        if (isDead) {
          u8g.drawStr(0, 55, "DOD");
        } else {
          u8g.drawStr(0, 55, "LEVER");
        }
      }

    } while( u8g.nextPage() );

    lastDisplayUpdate = millis();
  }
}

void setRGB(int r, int g, int b) {
  analogWrite(redPin, r);
  analogWrite(greenPin, g);
  analogWrite(bluePin, b);
}

void playDeadSound() {
  tone(piezoPin, 3000, 3000); // piezo, frek, tid (ms)
}

void playPointSound() {
  tone(piezoPin, 2000, 100); // piezo, frek, tid (ms)
}

void uppdateraServo() {
  int potValue = analogRead(potPin);
  // Serial.println(potValue);

  int servoAngle = map(potValue, 500, 800, SERVO_MIN, SERVO_MAX);
  int servoAngle2 = constrain(servoAngle, SERVO_MIN, SERVO_MAX);
  // Serial.println(servoAngle2);

  Xservo.write(servoAngle2);
}

void setRGB2() {
  if (mode == 1) {
    setRGB(0, 0, 255); // blå = debug
  } else if (isDead) {
    setRGB(255, 0, 0); // röd = död
  } else {
    setRGB(0, 255, 0); // grön = lever
  }  
}



void loop() {
  buttonPress();

  uppdateraServo();

  
  // Boll-data från min python
  if (mode == 1) {
    setRGB(0, 0, 255); // blå RGB (debug)

    if (millis() - lastSerialSend > 20) {
      int potValue = analogRead(potPin);
      int debugX = map(potValue, 500, 800, 640, 0); // mappar pot värde 500-800 till 0px-640px (kamerans resolution)

      debugX = constrain(debugX, 0, 640); // så att den inte ger något dumt värde
      Serial.println(debugX); 

      lastSerialSend = millis();
    }

    isDead = false;
  } else {
    if (Serial.available() > 0) {
        // läs första tecknet för att förstå vad det är som python koden vill
        char kommando = Serial.read(); 

        if (kommando == 'D') { // D för död
            isDead = true;
            playDeadSound();
        } 
        else if (kommando == 'L') { // L för lever
            isDead = false;
        } 
        else if (kommando == 'P') { // P för poäng
            playPointSound();
        }
        else if (isDigit(kommando)) {
            // om det är en siffra så ska den läsa resten av talet som bollens position
            String rest = Serial.readStringUntil('\n');
            String helaTalet = String(kommando) + rest;
            currentBallX = helaTalet.toInt();
        }
    }
    
    if (isDead) {
      setRGB(255, 0, 0); // röd RGB
    } else {
      setRGB(0, 255, 0); // grön RGB
    }
  }

  
  updateOLED();

}