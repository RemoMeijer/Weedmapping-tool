import StateManager

frames_folder = 'LiveProcessing/FrameExtractor/Frames'
stitched_folder = 'LiveProcessing/ImageStitching/batch'
ml_file = 'LiveProcessing/MachineLearning/rt-detr.pt'
video_folder = 'RunVideos'

state_manager = StateManager.StateManager(frames_folder, stitched_folder, ml_file, video_folder)
state_manager.start_map()
