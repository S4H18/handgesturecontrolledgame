# handgesturecontrolledgame
A Python game controlled by hand gestures using an ESP32 and an Ultrasonic sensor.


ESP32 + HC-SR04 Ultrasonic Sensor Connections

Component Mapping:
HC-SR04 Ultrasonic Sensor → ESP32
VCC → VIN (5V)
GND → GND
TRIG → GPIO 5
ECHO → GPIO 18 (through voltage divider)

Voltage Divider (IMPORTANT):
ECHO (Sensor) → 1kΩ → GPIO 18 (ESP32)
↓
1kΩ → GND

Instructions:
1. Connect sensor VCC to ESP32 VIN (5V).
2. Connect all GND pins together (common ground).
3. Connect TRIG directly to GPIO 5.
4. Connect ECHO ONLY through voltage divider.
5. Upload ESP32 code and test in Serial Monitor.
6. Close Serial Monitor before running Python game.
Warning:
Do NOT connect ECHO directly to ESP32 (5V can damage it).
