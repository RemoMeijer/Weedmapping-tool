import shutil, os
import sys

from PyQt6.QtWidgets import QApplication

from LiveProcessing.FrameExtractor.getFramesFromVideo import VideoFrameExtractor
from LiveProcessing.UI.mainUI import MainWindow
from LiveProcessing.ImageStitching.StitchRow import ImageStitcher
from LiveProcessing.MachineLearning.DetectAndPlotBatch import BatchProcessor

class StateManager:
    def __init__(self, frames_folder, stitched_folder, ml_file, video_folder):
        self.frames_folder = frames_folder
        self.stitched_folder = stitched_folder
        self.ml_file = ml_file
        self.video_folder = video_folder

    def cleanup(self):
        print("\nCleaning up:")
        if os.path.exists(self.frames_folder):
            shutil.rmtree(self.frames_folder)
            print("\tRemoved frames folder")
        if os.path.exists(self.stitched_folder):
            shutil.rmtree(self.stitched_folder)
            print("\tRemoved stitched folder\n")


    def make_run(self, video_path, field_id, start_gps, end_gps):
        video_path = os.path.join(self.video_folder, video_path)
        extractor = VideoFrameExtractor(video_path=video_path, frames_folder=self.frames_folder, frame_interval=8)
        extractor.extract_frames()

        stitcher = ImageStitcher(source_folder=self.frames_folder, result_folder=self.stitched_folder)
        total_width = stitcher.stitch_images()

        processor = BatchProcessor(batch_folder=self.stitched_folder, offset_file=f'{self.stitched_folder}/batch_offsets.json', model_file=self.ml_file, field_id=field_id)
        processor.process_batches(start_gps, end_gps, total_width)
        self.cleanup()

        print('Run made')

    def calculate_delta(self):
        pass

    def show_runs_on_map(self):
        pass

    def start_map(self):
        app = QApplication(sys.argv)
        window = MainWindow(self, self.video_folder)
        window.show()
        sys.exit(app.exec())

