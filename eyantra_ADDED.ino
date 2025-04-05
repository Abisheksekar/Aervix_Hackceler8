#include <SoftwareSerial.h>

#define MQ3_SENSOR A0  // MQ-3 sensor connected to A0 (Analog)
#define DRUNKEN_PIN 12  // Output to Raspberry Pi (HIGH if drunk)
#define SOBER_PIN 10    // Output to Raspberry Pi (HIGH if sober)
#define THRESHOLD 400  // Adjust threshold based on MQ-3 sensor calibration

#define LPWM_PIN 5       // Motor Driver LPWM (Light Control)
#define L_EN_PIN 6       // Motor Driver Enable
#define TRIGGER_LIGHT 4  // Trigger pin for hazard light (Active HIGH)
#define TRIGGER_CALL 7   // Trigger pin for call (Active LOW)

#define SIM800L_RX 3     // SIM800L RX
#define SIM800L_TX 2     // SIM800L TX

SoftwareSerial sim800l(SIM800L_RX, SIM800L_TX);  // SIM800L communication

const char phoneNumber[] = "+918870833282";  // Replace with your number

void setup() {
    pinMode(MQ3_SENSOR, INPUT);
    pinMode(DRUNKEN_PIN, OUTPUT);
    pinMode(SOBER_PIN, OUTPUT);

    pinMode(LPWM_PIN, OUTPUT);
    pinMode(L_EN_PIN, OUTPUT);
    pinMode(TRIGGER_LIGHT, INPUT_PULLUP);
    pinMode(TRIGGER_CALL, INPUT_PULLUP);

    Serial.begin(9600);
    sim800l.begin(9600);

    digitalWrite(TRIGGER_LIGHT, HIGH);
    digitalWrite(DRUNKEN_PIN, LOW);
    digitalWrite(SOBER_PIN, LOW);
    digitalWrite(LPWM_PIN, LOW);
    digitalWrite(L_EN_PIN, LOW);

    delay(3000);
    Serial.println("System Initialized...");
}

void loop() {
    int alcoholValue = analogRead(MQ3_SENSOR);
    Serial.print("MQ-3 Value: ");
    Serial.println(alcoholValue);

    if (alcoholValue > THRESHOLD) {  
        Serial.println("Alcohol Detected! Sending alert...");
        digitalWrite(DRUNKEN_PIN, HIGH);
        digitalWrite(SOBER_PIN, LOW);
        delay(1000);
    } else {
        Serial.println("Driver is Sober.");
        digitalWrite(DRUNKEN_PIN, LOW);
        digitalWrite(SOBER_PIN, HIGH);
    }

    if (digitalRead(TRIGGER_CALL) == LOW) {  // Fix trigger check
        Serial.println("Call is triggered");
        callPhoneNumber();
    }

    delay(1000);  // Adjust delay as needed
}

void callPhoneNumber() {
    sim800l.print("ATD");
    sim800l.print(phoneNumber);
    sim800l.println(";");
    Serial.println("Calling...");
    delay(3000);
}
