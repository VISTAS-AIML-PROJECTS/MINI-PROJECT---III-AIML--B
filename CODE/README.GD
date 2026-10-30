#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// LCD configuration
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ESP32 pin connections
const int vibrationPin = 27;
const int ledPin = 26;

// Change to true if the sensor output is LOW during vibration
const bool SENSOR_ACTIVE_LOW = false;

unsigned long previousMillis = 0;
const unsigned long blinkInterval = 200;

int ledState = LOW;
int previousDetected = -1;

void setup() {
  Serial.begin(115200);

  pinMode(vibrationPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Track Shield");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");
  delay(1500);

  lcd.clear();
}

void loop() {
  int sensorValue = digitalRead(vibrationPin);

  bool detected;

  if (SENSOR_ACTIVE_LOW) {
    detected = (sensorValue == LOW);
  } else {
    detected = (sensorValue == HIGH);
  }

  // Print sensor status
  Serial.print("Sensor: ");
  Serial.print(sensorValue);
  Serial.print(" | Vibration: ");
  Serial.println(detected ? "YES" : "NO");

  // Update LCD only when detection status changes
  if ((int)detected != previousDetected) {
    lcd.clear();

    if (detected) {
      lcd.setCursor(0, 0);
      lcd.print("VIBRATION");
      lcd.setCursor(0, 1);
      lcd.print("DETECTED!");
      Serial.println("VIBRATION DETECTED");
    } else {
      lcd.setCursor(0, 0);
      lcd.print("VIBRATION NOT");
      lcd.setCursor(0, 1);
      lcd.print("DETECTED");
      Serial.println("VIBRATION NOT DETECTED");
    }

    previousDetected = detected;
    delay(2000);  // Display message for 2 seconds
  }

  // Blink LED continuously while vibration is detected
  if (detected) {
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= blinkInterval) {
      previousMillis = currentMillis;
      ledState = !ledState;
      digitalWrite(ledPin, ledState);
    }
  } else {
    digitalWrite(ledPin, LOW);
    ledState = LOW;
  }
}
