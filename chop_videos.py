import cv2
import os

input_dir = 'raw_videos'
output_dir = 'extracted_images'
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.endswith((".mp4", ".mov", ".MOV")):
        cap = cv2.VideoCapture(os.path.join(input_dir, filename))
        count = 0
        
        # Take a photo every 3 frames (~0.1s) for blinking to catch the 'OFF' state
        # Take a photo every 15 frames (~0.5s) for solid light/isolator
        gap = 3 if "blink" in filename.lower() else 15
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            if count % gap == 0:
                cv2.imwrite(f"{output_dir}/{filename}_f{count}.jpg", frame)
            count += 1
        cap.release()
        print(f"Finished slicing: {filename}")