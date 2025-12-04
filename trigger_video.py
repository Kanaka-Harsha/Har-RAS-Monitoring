import json
import ssl
import time
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"
VIDEO_COMMAND_TOPIC = "har-test/video_command"

# Certificate Paths
CERT_FILE = "Test_Certificates/Har-Device.pem.crt"
PRIVATE_KEY_FILE = "Test_Certificates/Har-Private.pem.key"
CA_FILE = "Test_Certificates/Har-RootCA1.pem"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to AWS IoT!")
    else:
        print(f"✗ Connection failed (code: {rc})")

if __name__ == "__main__":
    client_id = f"video-trigger-{int(time.time())}"
    client = mqtt.Client(client_id=client_id)

    # SSL Context
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
    
    # Start loop in background
    client.loop_start()
    time.sleep(2) # Wait for connection

    # Send Command
    duration = 10
    payload = {
        "command": "click_video",
        "duration": duration
    }
    
    print(f"Sending command: {json.dumps(payload)}")
    client.publish(VIDEO_COMMAND_TOPIC, json.dumps(payload), qos=1)
    
    print("Command sent! Check video_agent.py output.")
    
    time.sleep(2)
    client.loop_stop()
    client.disconnect()
