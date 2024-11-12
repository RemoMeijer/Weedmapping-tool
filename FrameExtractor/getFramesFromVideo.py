import cv2
import os

# Paths
videos_folder = 'Videos'
frames_folder = 'Frames'

# Create the 'Frames' folder if it doesn't exist
os.makedirs(frames_folder, exist_ok=True)

# Get a list of all .mp4 files in the 'Videos' folder
video_files = [f for f in os.listdir(videos_folder) if f.endswith('.mp4')]

# Initialize global frame counter
global_frame_count = 1
frame_interval = 15  # Extract every 15 frames

# Loop through each video file in the 'Videos' folder
for video_file in video_files:
    video_path = os.path.join(videos_folder, video_file)

    # Load the video
    cap = cv2.VideoCapture(video_path)

    # Check if video loaded successfully
    if not cap.isOpened():
        print(f"Error: Could not open video {video_file}")
        continue

    frame_count = 0  # Reset the frame count for each video

    # Loop through video frames
    while True:
        ret, frame = cap.read()

        if not ret:
            break  # End of video

        # Check if this is a frame we need to save
        if frame_count % frame_interval == 0:
            # Construct filename for the frame (e.g., frame1, frame2, ...)
            frame_filename = os.path.join(frames_folder, f"frame{global_frame_count}.jpg")

            # Save the frame as an image
            cv2.imwrite(frame_filename, frame)

            # Increment the global frame counter
            global_frame_count += 1

        frame_count += 1

    # Release the video capture object for the current video
    cap.release()

print(f"Extracted and saved {global_frame_count - 1} frames from all Videos.")
