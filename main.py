import os
import shutil

from LiveProcessing.FrameExtractor.getFramesFromVideo import VideoFrameExtractor
from LiveProcessing.ImageStitching.StitchRow import ImageStitcher
from LiveProcessing.MachineLearning.DetectAndPlotBatch import BatchProcessor

def cleanup():
    print("\nCleaning up:")
    if os.path.exists(frames_folder):
        shutil.rmtree(frames_folder)
        print("\tRemoved frames folder")
    if os.path.exists(stitched_folder):
        shutil.rmtree(stitched_folder)
        print("\tRemoved stitched folder\n")


video_folder = 'test_video.mp4'
frames_folder = 'LiveProcessing/FrameExtractor/Frames'
stitched_folder = 'LiveProcessing/ImageStitching/batch'
ml_model_file = 'LiveProcessing/MachineLearning/plantdetectionmodel.pt'

extractor = VideoFrameExtractor(video_path=video_folder, frames_folder=frames_folder, frame_interval=15)
extractor.extract_frames()

stitcher = ImageStitcher(source_folder=frames_folder, result_folder=stitched_folder)
stitcher.stitch_images()

processor = BatchProcessor(batch_folder=stitched_folder, offset_file=f'{stitched_folder}/batch_offsets.json', model_file=ml_model_file)
processor.process_batches()

cleanup()

print(f"Plotting {video_folder} done!")
