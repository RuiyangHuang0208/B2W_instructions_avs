#include <MightyZap.h>

Mightyzap m_zap(&Serial1, 2);

int relay1 = 7;

void setup()
{
  Serial.begin(57600);
  pinMode(relay1, OUTPUT);
  digitalWrite(relay1, LOW);
}

void loop()
{
  if (Serial.available())
  {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
}

void processCommand(String command)
{
  if (command == "relay_off")
  {
    digitalWrite(relay1, LOW);
    Serial.println("Relay turned OFF");
  }
  if (command == "relay_on")
  {
    digitalWrite(relay1, HIGH);
    Serial.println("Relay turned ON");
  }
  if (command == "actuator_01_off")
  {
    m_zap.begin(32);
    m_zap.GoalPosition(1, 4090);
    Serial.println("Actuator 1 turned OFF (position 4090)");
  }
  if (command == "actuator_01_on")
  {
    m_zap.begin(32);
    m_zap.GoalPosition(1, 100);
    Serial.println("Actuator 1 turned ON (position 100)");
  }
  if (command == "actuator_02_off")
  {
    m_zap.begin(32);
    m_zap.GoalPosition(2, 4090);
    Serial.println("Actuator 2 turned OFF (position 4090)");
  }
  if (command == "actuator_02_on")
  {
    m_zap.begin(32);
    m_zap.GoalPosition(2, 100);
    Serial.println("Actuator 2 turned ON (position 100)");
  }
}