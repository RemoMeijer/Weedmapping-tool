import cv2
import os
import shutil


class VideoFrameExtractor:
    def __init__(self, video_path, frames_folder, frame_interval):
        self.video_path = video_path
        self.frames_folder = frames_folder
        self.frame_interval = frame_interval

        # Create frames folder if not exist
        if os.path.exists(self.frames_folder):
            shutil.rmtree(self.frames_folder)
        os.makedirs(self.frames_folder, exist_ok=True)

    def extract_frames(self):
        # Load the video
        cap = cv2.VideoCapture(self.video_path)

        # Check if the video loaded successfully
        if not cap.isOpened():
            print(f"Error: Could not open video {self.video_path}")
            return

        frame_count = 0 # For looping through the video
        frame_save_count = 0 # For saving frames

        # Loop through video frames
        while True:
            ret, frame = cap.read()

            if not ret:
                break  # End of video

            # Check if this is a frame we need to save
            if frame_count % self.frame_interval == 0:
                # Save the frame as an image
                frame_save_count += 1

                frame_filename = os.path.join(self.frames_folder, f"frame{frame_save_count}.jpg")
                cv2.imwrite(frame_filename, frame)

            frame_count += 1

        # Release the video capture object for the current video
        cap.release()

        print(f"Extracted and saved {frame_save_count} frames from {self.video_path}.")
