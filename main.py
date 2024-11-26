from FrameExtractor.getFramesFromVideo import VideoFrameExtractor
from ImageStitching.StitchRow import ImageStitcher
from MachineLearning.DetectAndPlotBatch import BatchProcessor

video_folder = 'test_video.mp4'
frames_folder = './FrameExtractor/Frames'
stitched_folder = './ImageStitching/batch'
ml_model_file = './MachineLearning/plantdetectionmodel.pt'

extractor = VideoFrameExtractor(video_path=video_folder, frames_folder=frames_folder, frame_interval=15)
extractor.extract_frames()

stitcher = ImageStitcher(source_folder=frames_folder, result_folder=stitched_folder)
stitcher.stitch_images()

processor = BatchProcessor(batch_folder=stitched_folder, offset_file=f'{stitched_folder}/batch_offsets.json', model_file=ml_model_file)
processor.process_batches()