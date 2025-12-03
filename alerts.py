"""
AWS IoT Alerts System
Listens to 'sensor/waterlevel' and plays an audio alert if skimmer value is 0 for more than 20 minutes.
"""

import json
import ssl
import os
import time
import winsound
import paho.mqtt.client as mqtt
from datetime import datetime

# --- CONFIGURATION ---
AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"
TOPIC = "sensor/waterlevel"

# Certificate Paths, change them to production certificates
CERT_FILE = "for-lambda-cert/certificate.pem.crt"
PRIVATE_KEY_FILE = "for-lambda-cert/private.pem.key"
CA_FILE = "for-lambda-cert/root-CA.pem"

# Alert Threshold (20 minutes in seconds)
ALERT_THRESHOLD_SECONDS = 10

# --- STATE TRACKING ---
class AlertState:
    def __init__(self):
        self.skimmer_zero_start_time = None
        self.alert_triggered = False

state = AlertState()

# Audio File Path (Put your .wav file in the same folder)
ALERT_AUDIO_FILE = "alertSound.wav"

def play_alert_sound():
    """Plays a custom sound file or a system beep."""
    print("🔊 PLAYING ALERT SOUND!")
    
    if os.path.exists(ALERT_AUDIO_FILE):
        try:
            # SND_FILENAME = play from file, SND_ASYNC = play in background
            winsound.PlaySound(ALERT_AUDIO_FILE, winsound.SND_FILENAME | winsound.SND_ASYNC)
            print(f"   Playing: {ALERT_AUDIO_FILE}")
        except Exception as e:
            print(f"   Error playing file: {e}")
            winsound.Beep(1000, 1000) # Fallback
    else:
        print(f"   File '{ALERT_AUDIO_FILE}' not found. Using Beep.")
        winsound.Beep(1000, 1000) 

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to AWS IoT!")
        print(f"  Subscribing to: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"✗ Connection failed (code: {rc})")

def on_message(client, userdata, message):
    try:
        payload = message.payload.decode('utf-8')
        # print(f"[DATA] {payload}") # Optional: print every message
        
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        skimmer = data.get('skimmer')

        if skimmer is None:
            return

        # --- ALERT LOGIC ---
        if skimmer == 0:
            # If this is the first time we see 0, start the timer
            if state.skimmer_zero_start_time is None:
                state.skimmer_zero_start_time = datetime.now()
                print(f"⚠️ Skimmer is 0. Timer started.")
            else:
                # Check elapsed time
                elapsed = (datetime.now() - state.skimmer_zero_start_time).total_seconds()
                
                if elapsed > ALERT_THRESHOLD_SECONDS:
                    print(f"🚨 CRITICAL: Skimmer has been 0 for {int(elapsed/60)} minutes!")
                    play_alert_sound()
                    state.alert_triggered = True
                elif int(elapsed) % 60 == 0: # Log every minute
                    print(f"⏳ Skimmer is 0. Elapsed: {int(elapsed/60)} min / 20 min")
        
        else:
            # Skimmer is not 0 (it's 1 or something else)
            if state.skimmer_zero_start_time is not None:
                print("✓ Skimmer recovered (Value: 1). Timer reset.")
                state.skimmer_zero_start_time = None
                state.alert_triggered = False

    except Exception as e:
        print(f"Error: {e}")

# --- MAIN SETUP ---
if __name__ == "__main__":
    client_id = f"python-alerts-{int(time.time())}"
    print(f"Starting Alerts System ({client_id})...")
    print(f"Alert Threshold: {ALERT_THRESHOLD_SECONDS / 60} minutes")

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
