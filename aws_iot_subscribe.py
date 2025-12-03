"""
AWS IoT Monitor
- Listens to 'sensor/waterlevel' and 'har-test/ctrl'.
- Prints data and commands for debugging/monitoring.
- DOES NOT send any commands.
"""

import json
import ssl
import os
import time
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"

# Topics
SENSOR_TOPIC = "sensor/waterlevel"
CONTROL_TOPIC = "har-test/ctrl"

# Certificate Paths
CERT_FILE = "for-lambda-cert/certificate.pem.crt"
PRIVATE_KEY_FILE = "for-lambda-cert/private.pem.key"
CA_FILE = "for-lambda-cert/root-CA.pem"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to AWS IoT!")
        print(f"  Subscribing to: {SENSOR_TOPIC}")
        print(f"  Subscribing to: {CONTROL_TOPIC}")
        client.subscribe([(SENSOR_TOPIC, 1), (CONTROL_TOPIC, 1)])
    else:
        print(f"✗ Connection failed (code: {rc})")

def on_message(client, userdata, message):
    try:
        payload = message.payload.decode('utf-8')
        print(f"[{message.topic}] {payload}")
    except Exception as e:
        print(f"Error: {e}")

# --- MAIN SETUP ---
if __name__ == "__main__":
    client_id = f"python-monitor-{int(time.time())}"
    print(f"Starting Monitor ({client_id})...")

    client = mqtt.Client(client_id=client_id)

    try:
        ssl_context = ssl.create_default_context()
        ssl_context.set_alpn_protocols(["x-amzn-mqtt-ca"]) 
        ssl_context.load_verify_locations(cafile=CA_FILE)
        ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=PRIVATE_KEY_FILE)
        client.tls_set_context(ssl_context)
    except Exception as e:
        print(f"Error setting up SSL: {e}")
        exit(1)

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to {AWS_IOT_ENDPOINT}...")
    try:
        client.connect(AWS_IOT_ENDPOINT, 443, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Connection Failed: {e}")