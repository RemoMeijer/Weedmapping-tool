import os
import json
import math
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from natsort import natsorted
from ultralytics import YOLO


class BatchProcessor:
    def __init__(self, batch_folder, offset_file, model_file, distance_threshold=10):
        self.batch_folder = batch_folder
        self.offset_file = offset_file
        self.model_file = model_file
        self.distance_threshold = distance_threshold

        # Load YOLO model
        self.model = YOLO(self.model_file)

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
        """Check if a point is within a threshold distance of any existing point."""
        x_new, y_new = point
        for x_existing, y_existing in existing_points:
            distance = math.sqrt((x_new - x_existing) ** 2 + (y_new - y_existing) ** 2)
            if distance < self.distance_threshold:
                return True
        return False

    def _refine_offset(self, current_offset, new_centers):
        """Refine the offset by minimizing the distance between new and existing centers."""
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
        """Check if a point overlaps with the previous batch."""
        last_image_width = self.offset_data[name][1]
        return x + last_image_width > image_width

    def process_batches(self):
        """Process all batches, apply offsets, and generate combined plot."""
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

        self._plot_combined_results()

    def _plot_combined_results(self):
        """Plot all detected centers across batches."""
        unique_classes = list(set(self.combined_classes))
        color_map = plt.get_cmap('tab10', len(unique_classes))
        class_colors = {cls: color_map(i) for i, cls in enumerate(unique_classes)}

        plt.figure(figsize=(15, 8))
        for (x, y), cls in zip(self.combined_centers, self.combined_classes):
            plt.scatter(x, y, color=class_colors[cls], s=50,
                        label=f'Class {cls}' if cls not in plt.gca().get_legend_handles_labels()[1] else "")

        # Reverse axes for proper alignment
        max_x = max(x for x, _ in self.combined_centers)
        plt.xlim(max_x, 0)  # Reverse x-axis
        plt.ylim(self.max_image_height, 0)  # Reverse y-axis

        # Add legend
        handles = [
            plt.Line2D([0], [0], marker='o', color=color_map(i), label=f'Class {cls}', linestyle='', markersize=10)
            for i, cls in enumerate(unique_classes)]
        plt.legend(handles=handles, title="Classes")

        plt.xlabel('X-coordinate')
        plt.ylabel('Y-coordinate')
        plt.title('Combined Bounding Box Centers Across Batches')
        plt.grid(True)
        plt.show()
