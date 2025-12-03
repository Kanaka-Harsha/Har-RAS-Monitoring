SHRIMP FARM AUTOMATION SYSTEM - HOW IT WORKS
============================================

1. THE GOAL
-----------
To keep the water clean and safe for the shrimp automatically. The system monitors water levels, cleans the filter (Backwash) when needed, and keeps you informed about everything it does.

2. THE HARDWARE (The Body)
--------------------------
- **The Brain (ESP32)**: A small computer chip near the pond.
- **The Eyes (Sensors)**:
  - **Skimmer Sensor**: Checks if water level is low.
  - **Drum Filter Sensor**: Checks filter water level.
- **The Hands (Motors)**:
  - **Backwash Motor**: Cleans the filter (Pin 16).
  - **Main Pump**: Circulates water (Smart Plug).
- **The Manager (Laptop)**: Runs `commands.py` to control everything.

3. THE FEEDBACK LOOP (New!)
---------------------------
Every time the system does something, it tells you.
- **Topic**: `har-test/feedback`
- **What you see**:
  - "Received Manual Command: ON"
  - "Sent Signal to ESP32: Turn on Backwash"
  - "Hardware: Backwash Motor ON" (Confirmation from the pond!)

4. THE PROCESS (The Story)
--------------------------
A. **Monitoring**:
   The ESP32 reads sensors and sends data to the Laptop.

B. **Automatic Cleaning**:
   - **Trigger**: Skimmer water level drops (0).
   - **Action**: Laptop sees this and sends "Turn on Backwash".
   - **Feedback**: Laptop says "Auto-Trigger: Backwash ON". ESP32 says "Hardware: Backwash Motor ON".
   - **Recovery**: When water rises (1), Laptop sends "Turn off Backwash".

C. **Safety**:
   - If Backwash runs > 20 mins, Laptop forces it OFF and `alerts.py` beeps loudly.

5. MANUAL CONTROL
-----------------
You can send commands to `har-test/command`:
- `ON` / `OFF` (Main Pump)
- `BACKWASH_ON` / `MOTOR_OFF`
- `MOTOR_ON_20_MIN` (Runs for 20 mins then stops)

6. SUMMARY OF FILES
-------------------
- **main.ino**: Firmware. Reads sensors, runs motors, sends hardware feedback.
- **commands.py**: The Manager. Decides when to run motors, logs everything.
- **alerts.py**: The Alarm. Beeps on critical errors.





WALKTHROUGH
------------------

Walkthrough - Shrimp Farm Automation System
This document outlines the final configuration and usage of the automation system.

System Architecture
1. The Manager: 
commands.py
This script is the central brain. It connects to AWS IoT and:

Listens to sensor/waterlevel for sensor data.
Listens to har-test/command for your manual instructions.
Decides when to turn the Backwash ON/OFF.
Reports everything to har-test/feedback.
2. The Body: 
main.ino
 (ESP32)
This is the firmware running on the device.

Reads Pin 4 (Skimmer) and Pin 5 (Drumfilter).
Controls Pin 16 (Backwash Motor) and the Main Pump (Tapo).
Confirms actions by sending messages to har-test/feedback.
3. The Alarm: 
alerts.py
Watches the sensor data silently.
Beeps if the Skimmer level stays low (0) for more than 20 minutes.
How to Use
1. Start the System
Run these commands in separate terminals:

python commands.py
python alerts.py
2. Manual Control
Go to AWS IoT Console -> MQTT Test Client. Publish to har-test/command:

ON / OFF -> Controls Main Pump.
BACKWASH_ON -> Turns Backwash ON immediately.
MOTOR_OFF -> Turns Backwash OFF.
MOTOR_ON_20_MIN -> Runs Backwash for 20 mins, then stops.
3. Monitor Status
Subscribe to har-test/feedback to see live updates:

"Received Manual Command..."
"Auto-Trigger: Skimmer LOW..."
"Hardware: Backwash Motor ON"
4. Automatic Behavior
When Skimmer Sensor (Pin 4) goes LOW (0):
System automatically turns Backwash ON.
When Skimmer Sensor goes HIGH (1):
System automatically turns Backwash OFF.
If Backwash runs for > 20 minutes:
System forces it OFF (Safety).
Alarm starts BEEPING.
