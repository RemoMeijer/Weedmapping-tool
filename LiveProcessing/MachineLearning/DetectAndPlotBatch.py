import os
import json
import math
import cv2 as cv
import numpy as np
from natsort import natsorted
from ultralytics import RTDETR

from Database.database_handler import DatabaseHandler
from GpsConversion.ConvertVideoToGps import GPSMapper

"""Machine learning detects on the batches created by the stitching. It works with the offset to create detections of the entire video"""
class BatchProcessor:
    def __init__(self, batch_folder, offset_file, model_file, field_id, distance_threshold=0, crop='gras'):
        self.batch_folder = batch_folder
        self.offset_file = offset_file
        self.model_file = model_file
        self.field_id = field_id
        self.crop = crop

        # How much overlap is allowed, batches share one image, so detection overlap in the shared image is possible
        self.distance_threshold = distance_threshold

        # Load model
        self.model = RTDETR(self.model_file)

        # Initialize database handler
        self.db = DatabaseHandler()

        # Load offsets
        if not os.path.exists(self.offset_file):
            raise FileNotFoundError("Offset file not found. Ensure the batch creation script has run.")
        with open(self.offset_file, 'r') as f:
            self.offset_data = json.load(f)

        # Initialize storage for combined centers and classes
        self.combined_centers = []
        self.combined_classes = []
        self.max_image_height = 0

    def _is_close_to_existing(self, point, existing_points):
        # Check if a point is within a threshold distance of any existing point.
        x_new, y_new = point
        for x_existing, y_existing in existing_points:
            distance = math.sqrt((x_new - x_existing) ** 2 + (y_new - y_existing) ** 2)
            if distance < self.distance_threshold:
                return True
        return False

    def _refine_offset(self, current_offset, new_centers):
        # Refine the offset by minimizing the distance between new and existing centers.
        best_offset = current_offset
        min_overlap = float("inf")

        for offset_adjustment in np.arange(-200, 200, 5):  # Test range of offsets
            adjusted_centers = [(x + offset_adjustment, y) for x, y in new_centers]
            overlap_count = sum(
                self._is_close_to_existing(point, self.combined_centers)
                for point in adjusted_centers
            )

            if overlap_count < min_overlap:
                min_overlap = overlap_count
                best_offset = current_offset + offset_adjustment

        return best_offset

    def _in_overlapping_image(self, x, image_width, name):
        # Check if a point overlaps with the previous batch.
        last_image_width = self.offset_data[name][1]
        return x + last_image_width > image_width

    def process_batches(self, start_gps, end_gps, total_width):
        run_id = self.db.create_new_run()

        self.db.ensure_field_exists(self.field_id)
        self.db.ensure_crop_exists(self.crop)

        print(self.field_id)
        self.db.add_run(run_id=run_id, field_name=self.field_id, crop_name=self.crop)

        # Process all batches, apply offsets, and generate combined plot.
        batches = natsorted(self.offset_data.keys())
        first_image = True

        for batch_name in batches:
            image_path = os.path.join(self.batch_folder, batch_name)
            image = cv.imread(image_path)
            height, width, _ = image.shape
            self.max_image_height = max(self.max_image_height, height)

            # Get offset for this batch
            offset = self.offset_data[batch_name][0]

            # Make predictions using YOLO
            results = self.model(image)
            predictions = []

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    if conf > 0.7:  # Confidence threshold
                        predictions.append([x1, y1, x2, y2, conf, cls])

            valid_centers, valid_classes = [], []

            # Extract centers and apply offset
            for pred in predictions:
                x1, y1, x2, y2, _, cls = pred
                x_center = (x1 + x2) / 2
                if first_image or not self._in_overlapping_image(x_center, width, batch_name):
                    x_center = ((x_center - width) * -1) + offset
                    y_center = (y1 + y2) / 2
                    valid_centers.append((x_center, y_center))
                    valid_classes.append(int(cls))

            first_image = False

            # Refine the offset for better alignment
            refined_offset = self._refine_offset(offset, valid_centers)
            valid_centers = [(x + (refined_offset - offset), y) for x, y in valid_centers]

            # Add non-overlapping points to the combined data
            for valid_center, valid_class in zip(valid_centers, valid_classes):
                if not self._is_close_to_existing(valid_center, self.combined_centers):
                    self.combined_centers.append(valid_center)
                    self.combined_classes.append(valid_class)


        gps_mapper = GPSMapper(start_gps=start_gps, end_gps=end_gps, frame_width=total_width, frame_height=self.max_image_height)
        combined_centers_gps = gps_mapper.map_to_gps(self.combined_centers, self.combined_classes)

        # Insert into db
        for centre, classes in zip(combined_centers_gps, self.combined_classes):
            self.db.add_detection(run_id=run_id, x=centre[0], y=centre[1],detection_class=classes)
            self.db.conn.commit()
