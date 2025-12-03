"""
AWS IoT Sensor Simulator
- Simulates the ESP32 by publishing fake sensor data to 'sensor/waterlevel'.
- Toggles 'skimmer' between 1 (Normal) and 0 (Low) every 30 seconds.
"""

import json
import ssl
import time
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"
TOPIC = "sensor/waterlevel"

# Certificate Paths
CERT_FILE = "for-lambda-cert/certificate.pem.crt"
PRIVATE_KEY_FILE = "for-lambda-cert/private.pem.key"
CA_FILE = "for-lambda-cert/root-CA.pem"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to AWS IoT!")
    else:
        print(f"✗ Connection failed (code: {rc})")

# --- MAIN SETUP ---
if __name__ == "__main__":
    client_id = f"python-simulator-{int(time.time())}"
    print(f"Starting Simulator ({client_id})...")

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

    print(f"Connecting to {AWS_IOT_ENDPOINT}...")
    client.connect(AWS_IOT_ENDPOINT, 443, 60)
    
    client.loop_start() # Start background thread for network loop

    counter = 0
    skimmer_state = 1 # Start with Normal
    last_toggle = time.time()
    toggle_interval = 30 # Toggle every 30 seconds

    try:
        while True:
            # Toggle Logic
            if time.time() - last_toggle > toggle_interval:
                skimmer_state = 0 if skimmer_state == 1 else 1
                last_toggle = time.time()
                print(f"\n[SIM] Toggling Skimmer to: {skimmer_state} ({'Normal' if skimmer_state==1 else 'LOW - Trigger Backwash'})")

            # Create Payload
            payload = {
                "skimmer": skimmer_state,
                "drumfilter": 1,
                "counter": counter
            }
            
            # Publish
            client.publish(TOPIC, json.dumps(payload))
            print(f"Sent: {payload}")
            
            counter += 1
            time.sleep(5) # Send data every 5 seconds

    except KeyboardInterrupt:
        print("\nStopping Simulator...")
        client.loop_stop()
