import shutil, os
import sys
import yaml

from pathlib import Path
from PyQt6.QtWidgets import QApplication

from FrameExtractor.getFramesFromVideo import VideoFrameExtractor
from UI.mainUI import MainWindow
from ImageStitching.StitchRow import ImageStitcher
from MachineLearning.DetectAndPlotBatch import BatchProcessor

class StateManager:
    def __init__(self, configuration_file: Path):
        # Check if config file exists
        if not os.path.exists(configuration_file):
            raise FileNotFoundError(f"Config file not found: {configuration_file}")

        # Load the YAML
        try:
            with open(configuration_file, 'r') as yaml_file:
                full_config = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error reading config file: {e}")

        paths = full_config['paths']

        # Files and folder paths needed to run the program
        required_keys = ["frames_folder", "stitched_folder", "machine_learning_model", "video's_folder"]

        # Check if keys are there
        for key in required_keys:
            if key not in paths:
                raise KeyError(f"Required key {key} is missing")

        # All okay, assign paths
        self.frames_folder = paths["frames_folder"]
        self.stitched_folder = paths["stitched_folder"]
        self.ml_file = paths["machine_learning_model"]
        self.video_folder = paths["video's_folder"]

        # Same stuff but for video settings
        video_settings = full_config["video_settings"]

        required_video_keys = ["frame_interval"]
        for key in required_video_keys:
            if key not in video_settings:
                raise KeyError(f"Required key {key} is missing")

        self.frame_interval = video_settings["frame_interval"]

        self.json_file_path = "batch_offset.json"

    # Help folders are created with creating a new run
    # This cleans up the help folders after creating a new run
    def cleanup(self):
        print("\nCleaning up:")
        if os.path.exists(self.frames_folder):
            shutil.rmtree(self.frames_folder)
            print("\tRemoved frames folder")
        if os.path.exists(self.stitched_folder):
            shutil.rmtree(self.stitched_folder)
            print("\tRemoved stitched folder\n")

    # Makes a run from a video_file, maybe run in separate thread
    def make_run(self, video_path, field_id, start_gps, end_gps):
        try:
            # Load video and extract frames, configure frame_interval
            video_path = os.path.join(self.video_folder, video_path)
            extractor = VideoFrameExtractor(video_path=video_path, frames_folder=self.frames_folder, frame_interval=self.frame_interval)
            extractor.extract_frames()

            # Stitch images together in batches of 5, into the temporary stitched folder
            stitcher = ImageStitcher(source_folder=self.frames_folder, result_folder=self.stitched_folder, json_file_path=self.json_file_path)
            total_width = stitcher.stitch_images()

            # Make detections on the batched images, and put them into the database
            processor = BatchProcessor(batch_folder=self.stitched_folder, offset_file=f'{self.stitched_folder}/{self.json_file_path}', model_file=self.ml_file, field_id=field_id)
            processor.process_batches(start_gps, end_gps, total_width)

            # Clean-up the temporary folders
            self.cleanup()
            print('Run made successfully')

        except Exception as e:
            print("Run failed with exception:", e)
            self.cleanup()

    # Starts the mainUI
    def start_map(self):
        app = QApplication(sys.argv)
        window = MainWindow(self, self.video_folder)
        window.show()
        sys.exit(app.exec())

if __name__ == '__main__':
    # Get path from root
    script_path = Path(__file__).resolve().parent
    config_path = script_path / 'config.yaml'

    # Start process with correct config path
    manager = StateManager(config_path)
    manager.start_map()