import shutil, os
import sys

from PyQt6.QtWidgets import QApplication

from LiveProcessing.FrameExtractor.getFramesFromVideo import VideoFrameExtractor
from LiveProcessing.GpsConversion.ConvertVideoToGps import GPSMapper
from LiveProcessing.ImageStitching.StitchRow import ImageStitcher
from LiveProcessing.MachineLearning.DetectAndPlotBatch import BatchProcessor
from LiveProcessing.UI.mainUI import MainWindow

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


    def make_run(self, video_path, field_id):
        video_path = os.path.join(self.video_folder, video_path)
        extractor = VideoFrameExtractor(video_path=video_path, frames_folder=self.frames_folder, frame_interval=8)
        extractor.extract_frames()

        stitcher = ImageStitcher(source_folder=self.frames_folder, result_folder=self.stitched_folder)
        total_width = stitcher.stitch_images()

        processor = BatchProcessor(batch_folder=self.stitched_folder, offset_file=f'{self.stitched_folder}/batch_offsets.json',
                                   model_file=self.ml_file, field_id=field_id)
        centers, classes = processor.process_batches()
        self.cleanup()

        # todo remove mock start and end gps, work with live data
        mapper = GPSMapper(
            start_gps=(51.465959, 3.628151),
            end_gps=(51.467815, 3.626611),
            frame_width=total_width,
            frame_height=1080)

        weed_crop_gps_coordinates = mapper.map_to_gps(centers, classes)
        print(weed_crop_gps_coordinates)

    def calculate_delta(self):
        pass

    def show_runs_on_map(self):
        pass

    def start_map(self):
        app = QApplication(sys.argv)
        window = MainWindow(self, self.video_folder)
        window.show()
        sys.exit(app.exec())

