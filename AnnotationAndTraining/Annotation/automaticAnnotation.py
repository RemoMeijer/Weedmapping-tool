import cv2
import numpy as np
import yaml

from pathlib import Path
from LiveProcessing.FrameExtractor.getFramesFromVideo import VideoFrameExtractor


class YoloAnnotator:
    def __init__(self, config_path):
        self.cfg = None
        self._load_config(config_path)
        self._init_paths()
        cv2.namedWindow(self.window_name, cv2.WINDOW_FULLSCREEN)

    def _load_config(self, config_path):
        """Load parameters from YAML file"""
        with open(config_path, 'r') as f:
            self.cfg = yaml.safe_load(f)

        # Check if everything is there
        required_sections = ['paths', 'thresholds', 'classes']
        if not all(section in self.cfg for section in required_sections):
            raise ValueError(f"Config missing required sections: {required_sections}")

        self.window_name = self.cfg['display']['window_name']

    def _init_paths(self):
        """Create all paths and dirs needed."""
        self.images_dir = Path(self.cfg['paths']['images_dir'])
        self.annotations_output_dir = Path(self.cfg['paths']['annotations_dir'])
        self.annotations_output_dir.mkdir(parents=True, exist_ok=True)

    def extract_green_plants_mask(self, img):
        """Generate mask for green areas using configured thresholds"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        red, green, blue = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]

        # Create refined mask for defined green areas
        thresholds = self.cfg['thresholds']
        mask = (
                       (green > red + thresholds['red_boundary']) &
                       (green > blue) &
                       (green > thresholds['green_min']) &
                       (green < thresholds['green_max']) &
                       (red < thresholds['red_max']) &
                       (blue < thresholds['blue_max'])
               ).astype(np.uint8) * 255

        # Remove some graining with Erode and Dilate etc.
        kernel = np.ones((5, 5), np.uint8)
        green_mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel,
                                      iterations=1)  # Can finetune this, maybe this or one more

        return green_mask

    def process_contour(self, cnt, img):
        "Process the contour and return the class, and if we want to keep this contour"
        img_copy = img.copy()
        cv2.drawContours(img_copy, [cnt], -1, (0, 0, 255), thickness=2)  # BGR colour!!

        # Resize for the display
        resized_img = self.scale_image(self.cfg['display']['scale_percent'], img_copy)
        cv2.imshow(self.window_name, resized_img)
        cv2.waitKey(1)

        # Get user input
        while True:
            user_class = input("Enter class: 1-crop, 2-weed, 3-skip. ")
            if user_class in self.cfg['classes']['mapping']:
                return self.cfg['classes']['mapping'][user_class], True
            if user_class == '3':
                return None, False
            print("Invalid input. Valid options: 1, 2, 3")

    def contour_to_yolo(self, contour, image_size):
        """Convert contour points to YOLO segmentation format"""
        h, w = image_size
        points = contour.squeeze()
        normalized = [f"{x / w:.6f} {y / h:.6f}" for x, y in points]
        return " ".join(normalized)

    # Main loop for annotation
    def annotate_images(self):

        # Skip first image, or do it twice, because cv2 is weird with the first image showing
        # todo find solution for this cv2 behaviour
        first_image = True

        # Loop trough folder that needs to be labeled
        for img_name in self.images_dir.glob('*.jpg'):
            print(img_name)
            img = cv2.imread(img_name)

            if img is None:
                print(f"Image {img_name} not found.")
                continue

            # First image will show and go away in 1 frame.
            # I do not want to use waitKey(0) because i do not want a key input
            # To achieve this, two waitKey(1) need to be shown, because the first one will always be a black frame
            if first_image:
                cv2.imshow(self.window_name, img)
                cv2.waitKey(1)
                first_image = False

            # Get the green plants from image
            processed_mask = self.extract_green_plants_mask(img)

            # Find contours
            contours, _ = cv2.findContours(processed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            contours = list(contours)

            annotations = []
            # Loop trough found contours in image
            for cnt in contours:
                # If contour under threshold, skip
                if cv2.contourArea(cnt) < self.cfg['thresholds']['min_area']:
                    continue

                class_name, keep = self.process_contour(cnt, img)

                # Skip if we don't want to keep it
                if not keep:
                    print("Removed contour.")
                    continue

                yolo_annotation = f"{self.cfg['classes']['ids'][class_name]} " + self.contour_to_yolo(cnt, img.shape[:2])
                annotations.append(yolo_annotation)

            # Write the annotations per image in txt file
            output_path = self.annotations_output_dir / f"{img_name.stem}.txt"
            with open(output_path, "w") as f:
                f.write("\n".join(annotations))

        # When done, destroy windows
        cv2.destroyAllWindows()

    # # Get frames to extract from a video, using the VideoFrameExtractor class
    def create_frames(self, video_path, output_folder, frame_interval, starting_number):
        """Create some frames from a video.
        frame_interval is how many frames are skipped in the video, for each output frame.
        starting_number is to prevent overwrites of existing frames. eg. if frame_10 exists, you want to start at 11 for the new frames."""
        extractor = VideoFrameExtractor(video_path=video_path, frames_folder=output_folder,
                                        frame_interval=frame_interval,
                                        starting_number=starting_number)
        extractor.extract_frames()

    def scale_image(self, scale_percentage, img):
        """Resize images to fit the screen.
         A 4k image on a 1080p screen is not that great."""
        width = int(img.shape[1] * scale_percentage / 100)
        height = int(img.shape[0] * scale_percentage / 100)
        return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)


    # For calibration
    def calibrate(self, img_path):
        """Calibrate the green values of the mask, try new values and see what happens."""
        img = cv2.imread(img_path)
        mask = self.extract_green_plants_mask(img)
        resized_image = self.scale_image(70, mask)
        cv2.imshow("Green extracted", resized_image)
        cv2.waitKey(0)


annotator = YoloAnnotator("config.yaml")

# annotator.create_frames(annotator.cfg['paths']['video_folder'], annotator.images_dir, 15, 176)
# annotator.calibrate("./images/frame170.jpg")
annotator.annotate_images()
