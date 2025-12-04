# """
# AWS IoT Central Controller
# - Listens to 'har-test/command' for manual user inputs.
# - Listens to 'sensor/waterlevel' for automation (Backwash).
# - Sends all commands to 'har-test/ctrl'.
# - Publishes status/feedback to 'har-test/feedback'.
# """

# import json
# import ssl
# import os
# import time
# from datetime import datetime
# import paho.mqtt.client as mqtt

# # --- CONFIGURATION ---
# AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"

# # Topics
# MANUAL_TOPIC = "har-test/command" 
# SENSOR_TOPIC = "sensor/waterlevel"
# CONTROL_TOPIC = "har-test/ctrl"
# FEEDBACK_TOPIC = "har-test/feedback"

# # Certificate Paths
# CERT_FILE = "for-lambda-cert/certificate.pem.crt"
# PRIVATE_KEY_FILE = "for-lambda-cert/private.pem.key"
# CA_FILE = "for-lambda-cert/root-CA.pem"

# # Log file
# LOG_FILE = "logs.txt"

# # --- STATE TRACKING ---
# class State:
#     def __init__(self):
#         self.backwash_active = False
#         self.backwash_start_time = None

# state = State()

# # --- HELPER FUNCTIONS ---
# def log_and_feedback(client, message):
#     """Logs to file and publishes to feedback topic."""
#     try:
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         full_msg = f"[{timestamp}] {message}"
        
#         # 1. Log to File
#         with open(LOG_FILE, 'a') as log_file:
#             log_file.write(full_msg + "\n")
            
#         # 2. Publish to AWS
#         client.publish(FEEDBACK_TOPIC, full_msg, qos=1)
#         print(f"📢 {full_msg}")
        
#     except Exception as e:
#         print(f"Log Error: {e}")

# def on_connect(client, userdata, flags, rc):
#     """Callback for when the client connects to AWS IoT."""
#     if rc == 0:
#         print(f"✓ Connected to AWS IoT!")
#         print(f"  Subscribing to: {MANUAL_TOPIC}")
#         print(f"  Subscribing to: {SENSOR_TOPIC}")
#         client.subscribe([(MANUAL_TOPIC, 1), (SENSOR_TOPIC, 1)])
#         log_and_feedback(client, "System Online: Central Controller Connected.")
#     else:
#         print(f"✗ Connection failed (code: {rc})")
#         os._exit(1)

# def handle_manual_command(client, payload):
#     print(f"\n[MANUAL CMD] Payload: {payload}")
#     log_and_feedback(client, f"Received Manual Command: {payload}")
    
#     command_to_send = None
    
#     if payload == "ON":
#         command_to_send = "Turn on Main Pump"
#     elif payload == "OFF":
#         command_to_send = "Turn off Main Pump"
#     elif payload == "BACKWASH_ON":
#         command_to_send = "Turn on Backwash"
#     elif payload == "MOTOR_ON_15_MIN":
#         command_to_send = "Start Motor 15min"
#     elif payload == "MOTOR_ON_20_MIN":
#         command_to_send = "Start Motor 20min"
#     elif payload == "MOTOR_OFF":
#         command_to_send = "Turn off Motor"
#     else:
#         log_and_feedback(client, f"Warning: Unknown command '{payload}'")
#         return

#     if command_to_send:
#         client.publish(CONTROL_TOPIC, command_to_send, qos=1)
#         log_and_feedback(client, f"Sent Signal to ESP32: {command_to_send}")

# def handle_sensor_data(client, payload):
#     try:
#         data = json.loads(payload)
#         skimmer = data.get('skimmer')
        
#         if skimmer is None:
#             return

#         # --- BACKWASH LOGIC ---
#         if skimmer == 0:
#             # Condition: Skimmer is 0 (Low)
#             if not state.backwash_active:
#                 # Turn ON if not already on
#                 log_and_feedback(client, "Auto-Trigger: Skimmer LOW (0). Turning ON Backwash.")
#                 client.publish(CONTROL_TOPIC, "Turn on Backwash", qos=1)
#                 log_and_feedback(client, "Sent Signal to ESP32: Turn on Backwash")
                
#                 state.backwash_active = True
#                 state.backwash_start_time = datetime.now()
#             else:
#                 # Already ON, check timeout (20 mins)
#                 elapsed = (datetime.now() - state.backwash_start_time).total_seconds()
#                 if elapsed > (20 * 60):
#                     log_and_feedback(client, "🚨 Safety Timeout (20m). Forcing Backwash OFF.")
#                     client.publish(CONTROL_TOPIC, "Turn off Backwash", qos=1)
#                     log_and_feedback(client, "Sent Signal to ESP32: Turn off Backwash")
#                     pass 
#         else:
#             # Condition: Skimmer is NOT 0 (e.g. 1)
#             if state.backwash_active:
#                 log_and_feedback(client, "Auto-Trigger: Skimmer Recovered (1). Turning OFF Backwash.")
#                 client.publish(CONTROL_TOPIC, "Turn off Backwash", qos=1)
#                 log_and_feedback(client, "Sent Signal to ESP32: Turn off Backwash")
#                 state.backwash_active = False
#                 state.backwash_start_time = None

#     except json.JSONDecodeError:
#         pass
#     except Exception as e:
#         print(f"Error in sensor logic: {e}")

# def on_message(client, userdata, message):
#     """Callback for when a message is received."""
#     try:
#         payload = message.payload.decode('utf-8').strip()
        
#         if message.topic == MANUAL_TOPIC:
#             handle_manual_command(client, payload.upper())
#         elif message.topic == SENSOR_TOPIC:
#             handle_sensor_data(client, payload)
            
#     except Exception as e:
#         print(f"Error processing message: {e}")

# # --- MAIN SETUP ---
# if __name__ == "__main__":
#     client_id = f"python-central-controller-{int(time.time())}"
#     print(f"Starting Central Controller ({client_id})...")

#     client = mqtt.Client(client_id=client_id)

#     # --- SSL/TLS Configuration ---
#     try:
#         ssl_context = ssl.create_default_context()
#         ssl_context.set_alpn_protocols(["x-amzn-mqtt-ca"]) 
#         ssl_context.load_verify_locations(cafile=CA_FILE)
#         ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=PRIVATE_KEY_FILE)
        
#         client.tls_set_context(ssl_context)
#     except Exception as e:
#         print(f"✗ Error setting up SSL/ALPN: {e}")
#         exit(1)

#     client.on_connect = on_connect
#     client.on_message = on_message

#     print(f"Connecting to {AWS_IOT_ENDPOINT} on Port 443...")
#     try:
#         client.connect(AWS_IOT_ENDPOINT, 443, 60)
#         print("\nListening for commands and sensor data...")
#         client.loop_forever()
        
#     except Exception as e:
#         print(f"✗ Connection Failed: {e}")


# """
# How to use this script:
# 1. Run this script from your terminal:
#    python commands.py

# 2. Use an MQTT client (like the AWS IoT MQTT Test Client in the console) to publish a message
#    to the topic 'har-test/manual_command'.

# 3. Send 'ON' as the message payload to turn the pump on.
#    Send 'OFF' as the message payload to turn the pump off.

# 4. The script will receive the command and forward a detailed instruction to the ESP32.
# """

"""
AWS IoT Central Controller
- Listens to 'har-test/command' for manual user inputs.
- Listens to 'sensor/waterlevel' for automation (Backwash).
- Sends all commands to 'har-test/ctrl'.
- Publishes status/feedback to 'har-test/feedback'.
"""

import json
import ssl
import os
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"

# Topics
MANUAL_TOPIC = "har-test/command" 
SENSOR_TOPIC = "har-test/sensor"
CONTROL_TOPIC = "har-test/ctrl"
FEEDBACK_TOPIC = "har-test/feedback"

# Certificate Paths
# Ensure these match the location on your Pi
CERT_FILE = "Test_Certificates/Har-Device.pem.crt"
PRIVATE_KEY_FILE = "Test_Certificates/Har-Private.pem.key"
CA_FILE = "Test_Certificates/Har-RootCA1.pem"

# Log file
LOG_FILE = "logs.txt"

# --- STATE TRACKING ---
class State:
    def __init__(self):
        self.backwash_active = False
        self.backwash_start_time = None

state = State()

# --- HELPER FUNCTIONS ---
def log_and_feedback(client, message):
    """Logs to file and publishes to feedback topic."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {message}"
        
        # 1. Log to File
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(full_msg + "\n")
            
        # 2. Publish to AWS
        client.publish(FEEDBACK_TOPIC, full_msg, qos=1)
        print(f"📢 {full_msg}")
        
    except Exception as e:
        print(f"Log Error: {e}")

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to AWS IoT."""
    if rc == 0:
        print(f"✓ Connected to AWS IoT!")
        print(f"  Subscribing to: {MANUAL_TOPIC}")
        print(f"  Subscribing to: {SENSOR_TOPIC}")
        client.subscribe([(MANUAL_TOPIC, 1), (SENSOR_TOPIC, 1)])
        log_and_feedback(client, "System Online: Central Controller Connected.")
    else:
        print(f"✗ Connection failed (code: {rc})")
        os._exit(1)

def handle_manual_command(client, payload):
    print(f"\n[MANUAL CMD] Payload: {payload}")
    log_and_feedback(client, f"Received Manual Command: {payload}")
    
    command_to_send = None
    
    if payload == "ON":
        command_to_send = "Turn on Main Pump"
    elif payload == "OFF":
        command_to_send = "Turn off Main Pump"
    elif payload == "BACKWASH_ON":
        command_to_send = "Turn on Backwash"
    elif payload == "MOTOR_ON_15_MIN":
        command_to_send = "Start Motor 15min"
    elif payload == "MOTOR_ON_20_MIN":
        command_to_send = "Start Motor 20min"
    elif payload == "MOTOR_OFF":
        command_to_send = "Turn off Motor"
    else:
        log_and_feedback(client, f"Warning: Unknown command '{payload}'")
        return

    if command_to_send:
        client.publish(CONTROL_TOPIC, command_to_send, qos=1)
        log_and_feedback(client, f"Sent Signal to ESP32: {command_to_send}")

def handle_sensor_data(client, payload):
    try:
        data = json.loads(payload)
        skimmer = data.get('skimmer')
        
        if skimmer is None:
            return

        # --- BACKWASH LOGIC ---
        if skimmer == 0:
            # Condition: Skimmer is 0 (Low)
            if not state.backwash_active:
                # Turn ON if not already on
                log_and_feedback(client, "Auto-Trigger: Skimmer LOW (0). Turning ON Backwash.")
                client.publish(CONTROL_TOPIC, "Turn on Backwash", qos=1)
                log_and_feedback(client, "Sent Signal to ESP32: Turn on Backwash")
                
                state.backwash_active = True
                state.backwash_start_time = datetime.now()
            else:
                # Already ON, check timeout (20 mins)
                elapsed = (datetime.now() - state.backwash_start_time).total_seconds()
                if elapsed > (20 * 60):
                    log_and_feedback(client, "🚨 Safety Timeout (20m). Forcing Backwash OFF.")
                    client.publish(CONTROL_TOPIC, "Turn off Backwash", qos=1)
                    log_and_feedback(client, "Sent Signal to ESP32: Turn off Backwash")
                    pass 
        else:
            # Condition: Skimmer is NOT 0 (e.g. 1)
            if state.backwash_active:
                log_and_feedback(client, "Auto-Trigger: Skimmer Recovered (1). Turning OFF Backwash.")
                client.publish(CONTROL_TOPIC, "Turn off Backwash", qos=1)
                log_and_feedback(client, "Sent Signal to ESP32: Turn off Backwash")
                state.backwash_active = False
                state.backwash_start_time = None

    except json.JSONDecodeError:
        pass
    except Exception as e:
        print(f"Error in sensor logic: {e}")

def on_message(client, userdata, message):
    """Callback for when a message is received."""
    try:
        payload = message.payload.decode('utf-8').strip()
        
        if message.topic == MANUAL_TOPIC:
            handle_manual_command(client, payload.upper())
        elif message.topic == SENSOR_TOPIC:
            handle_sensor_data(client, payload)
            
    except Exception as e:
        print(f"Error processing message: {e}")

# --- MAIN SETUP ---
if __name__ == "__main__":
    client_id = f"python-central-controller-{int(time.time())}"
    print(f"Starting Central Controller ({client_id})...")

    client = mqtt.Client(client_id=client_id)

    # --- SSL/TLS Configuration ---
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.set_alpn_protocols(["x-amzn-mqtt-ca"]) 
        ssl_context.load_verify_locations(cafile=CA_FILE)
        ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=PRIVATE_KEY_FILE)
        
        client.tls_set_context(ssl_context)
    except Exception as e:
        print(f"✗ Error setting up SSL/ALPN: {e}")
        exit(1)

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to {AWS_IOT_ENDPOINT} on Port 443...")
    try:
        client.connect(AWS_IOT_ENDPOINT, 443, 60)
        print("\nListening for commands and sensor data...")
        client.loop_forever()
        
    except Exception as e:
        print(f"✗ Connection Failed: {e}")