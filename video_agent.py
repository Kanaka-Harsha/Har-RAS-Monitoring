import json
import ssl
import time
import os
import subprocess
import paho.mqtt.client as mqtt
from upload_to_s3 import upload_file

# --- CONFIGURATION ---
AWS_IOT_ENDPOINT = "a2x983sew4xtsh-ats.iot.ap-northeast-1.amazonaws.com"
VIDEO_COMMAND_TOPIC = "har-test/video_command"
VIDEO_FEEDBACK_TOPIC = "har-test/video_feedback"
BUCKET_NAME = "har-test-ebi"

# Certificate Paths (Same as commands.py)
CERT_FILE = "Test_Certificates/Har-Device.pem.crt"
PRIVATE_KEY_FILE = "Test_Certificates/Har-Private.pem.key"
CA_FILE = "Test_Certificates/Har-RootCA1.pem"

# Load Environment Variables (for RTSP URL)
def load_env():
    env_file = "credentials.env"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to AWS IoT!")
        print(f"  Subscribing to: {VIDEO_COMMAND_TOPIC}")
        client.subscribe(VIDEO_COMMAND_TOPIC, 1)
    else:
        print(f"✗ Connection failed (code: {rc})")

def on_message(client, userdata, message):
    try:
        payload_str = message.payload.decode('utf-8')
        print(f"\n[CMD] Received: {payload_str}")
        
        data = json.loads(payload_str)
        
        # KISS Strategy: Check for specific command
        if data.get("command") == "click_video":
            duration = data.get("duration", 10)
            
            # Validate duration
            if not isinstance(duration, int):
                duration = 10
            if duration < 5: duration = 5
            if duration > 30: duration = 30 # Cap at 30s for safety
            
            print(f"Starting video capture for {duration} seconds...")
            client.publish(VIDEO_FEEDBACK_TOPIC, json.dumps({"status": "recording", "duration": duration}), qos=1)
            
            # Run capture.py
            # We use subprocess to run it as a separate process
            try:
                cmd = ["python", "capture.py", "--duration", str(duration)]
                
                # Check for RTSP URL
                rtsp_url = os.environ.get("RTSP_URL")
                if rtsp_url:
                    print(f"Using RTSP URL: {rtsp_url}")
                    cmd.extend(["--rtsp", rtsp_url])
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    check=True
                )
                
                # Parse output to find the filename
                # capture.py prints "OUTPUT_FILE:filename"
                output_lines = result.stdout.splitlines()
                video_file = None
                for line in output_lines:
                    if "OUTPUT_FILE:" in line:
                        video_file = line.split("OUTPUT_FILE:")[1].strip()
                        break
                
                if video_file and os.path.exists(video_file):
                    print(f"Capture successful: {video_file}")
                    client.publish(VIDEO_FEEDBACK_TOPIC, json.dumps({"status": "uploading", "file": video_file}), qos=1)
                    
                    # Upload to S3
                    print(f"Uploading to S3 bucket: {BUCKET_NAME}...")
                    success = upload_file(video_file, BUCKET_NAME)
                    
                    if success:
                        msg = {"status": "success", "file": video_file, "bucket": BUCKET_NAME}
                        print("Upload Complete!")
                    else:
                        msg = {"status": "error", "message": "S3 Upload Failed"}
                        print("Upload Failed.")
                        
                    client.publish(VIDEO_FEEDBACK_TOPIC, json.dumps(msg), qos=1)
                    
                    # Optional: Clean up local file
                    # os.remove(video_file)
                    
                else:
                    print("Error: Could not determine output filename from capture.py")
                    client.publish(VIDEO_FEEDBACK_TOPIC, json.dumps({"status": "error", "message": "Capture script failed to return filename"}), qos=1)

            except subprocess.CalledProcessError as e:
                print(f"Error running capture.py: {e}")
                client.publish(VIDEO_FEEDBACK_TOPIC, json.dumps({"status": "error", "message": "Capture script execution failed"}), qos=1)

    except json.JSONDecodeError:
        print("Error: Invalid JSON received")
    except Exception as e:
        print(f"Error processing message: {e}")

if __name__ == "__main__":
    client_id = f"video-agent-{int(time.time())}"
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
    client.on_message = on_message

    print(f"Connecting to {AWS_IOT_ENDPOINT}...")
    client.connect(AWS_IOT_ENDPOINT, 443, 60)
    
    print("Video Agent Listening...")
    client.loop_forever()
