import cv2
import numpy as np
import yaml

from pathlib import Path

from PyQt6.QtGui import QImage, QPixmap

from getFramesFromVideo import VideoFrameExtractor


class YoloAnnotator:
    def __init__(self, config_path):
        self.cfg = None
        self._load_config(config_path)
        self._init_paths()
        # cv2.namedWindow(self.window_name, cv2.WINDOW_FULLSCREEN)

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

    def extract_green_plants_mask_from_yaml(self, img):
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

    def extract_green_plants_mask(self, img,  red_min, red_max, green_min, green_max, blue_min, blue_max, red_threshold):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        red, green, blue = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]

        mask = (
            (green > red + red_threshold) &
            (green > blue) &
            (red > red_min) &
            (red < red_max) &
            (green > green_min) &
            (green < green_max) &
            (blue > blue_min) &
            (blue < blue_max)
        ).astype(np.uint8) * 255

        kernel = np.ones((5, 5), np.uint8)
        green_mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel,
                                      iterations=1)

        return green_mask

    def update_mask(self, calibration_values, original_img):
        thresholds = {
            "red_min": calibration_values["red"]["min"].value(),
            "red_max": calibration_values["red"]["max"].value(),
            "green_min": calibration_values["green"]["min"].value(),
            "green_max": calibration_values["green"]["max"].value(),
            "blue_min": calibration_values["blue"]["min"].value(),
            "blue_max": calibration_values["blue"]["max"].value(),
            "red_boundary": calibration_values["red_calibration"]["calibration"].value()
        }
        width = original_img.width()
        height = original_img.height()
        ptr = original_img.bits()
        ptr.setsize(height * width * 4)
        arr = np.array(ptr).reshape((height, width, 4))
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # Generate new mask
        mask = self.extract_green_plants_mask(
            img_bgr,
            thresholds["red_min"],
            thresholds["red_max"],
            thresholds["green_min"],
            thresholds["green_max"],
            thresholds["blue_min"],
            thresholds["blue_max"],
            thresholds["red_boundary"]
        )

        # Convert mask to pixmap and return
        qimg = QImage(mask.data, mask.shape[1], mask.shape[0], mask.strides[0], QImage.Format.Format_Grayscale8)
        return QPixmap.fromImage(qimg)

    def cv_img_to_qpixmap(self, cv_img):
        if len(cv_img.shape) == 2:  # grayscale
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        elif cv_img.shape[2] == 1:  # single channel
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)

        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        return QPixmap.fromImage(q_img)

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
            processed_mask = self.extract_green_plants_mask_from_yaml(img)

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

    # Get frames to extract from a video
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

        mask = self.extract_green_plants_mask_from_yaml(img)
        # resized_image = self.scale_image(50, mask)
        # original_image = self.scale_image(50, img)

        # cv2.imshow("Green extracted", resized_image)
        # cv2.waitKey(0)
        return img, mask


# annotator = YoloAnnotator("config.yaml")

# annotator.create_frames(annotator.cfg['paths']['video_folder'], annotator.images_dir, 15, 176)
# annotator.calibrate("./images/frame170.jpg")
# annotator.annotate_images()
