import cv2
import time
import argparse
import os
from datetime import datetime

def capture_video(duration=10, source=0):
    # Define the codec and create VideoWriter object
    # mp4v is a popular codec for .mp4 files
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"video_{timestamp}.mp4"
    
    # Open the video source (webcam index or RTSP URL)
    print(f"Connecting to video source: {source}")
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return None

    # Get actual width and height
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 20.0 # Standard fps
    
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    start_time = time.time()
    print(f"Recording for {duration} seconds...")
    
    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            print("Error: Failed to read frame from source.")
            break

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"Video saved: {filename}")
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Capture video from webcam or RTSP.')
    parser.add_argument('--duration', type=int, default=10, help='Duration of video in seconds')
    parser.add_argument('--rtsp', type=str, default=None, help='RTSP URL for IP Camera')
    
    args = parser.parse_args()
    
    # Use RTSP URL if provided, otherwise default to 0 (Webcam)
    source = args.rtsp if args.rtsp else 0
    
    output_file = capture_video(args.duration, source)
    if output_file:
        # Print only the filename to stdout for the caller to pick up
        print(f"OUTPUT_FILE:{output_file}")
