import json
import os
from natsort import natsorted
from ultralytics import YOLO
import matplotlib.pyplot as plt
import cv2
import math
import numpy as np


def is_close_to_existing(point, existing_points, threshold=10):
    """Check if a point is within a threshold distance of any existing point."""
    x_new, y_new = point
    for x_existing, y_existing in existing_points:
        distance = math.sqrt((x_new - x_existing) ** 2 + (y_new - y_existing) ** 2)
        if distance < threshold:
            return True
    return False


def refine_offset(current_offset, combined_centers, new_centers, distance_threshold):
    """
    Refine the offset by minimizing the distance between the new centers and the existing combined centers.
    """
    best_offset = current_offset
    min_overlap = float("inf")

    # Test small variations in the offset
    for offset_adjustment in np.arange(-200, 200, 5):  # Adjust range and step as needed
        adjusted_centers = [(x + offset_adjustment, y) for x, y in new_centers]
        overlap_count = sum(
            is_close_to_existing(point, combined_centers, distance_threshold)
            for point in adjusted_centers
        )

        # Minimize overlap
        if overlap_count < min_overlap:
            min_overlap = overlap_count
            best_offset = current_offset + offset_adjustment

    return best_offset


# Load offsets
offset_file = './batch/batch_offsets.json'
if not os.path.exists(offset_file):
    raise FileNotFoundError("Offset file not found. Ensure the batch creation script has run.")

with open(offset_file, 'r') as f:
    offset_data = json.load(f)

# Sort batches naturally
batches = natsorted(offset_data.keys())

# Load YOLO model
model = YOLO('plantdetectionmodel.pt')

# Initialize storage for combined centers and classes
combined_centers = []
combined_classes = []
max_image_height = 0
distance_threshold = 50

# Loop through batches
for batch_name in batches:
    image_path = os.path.join('batch', batch_name)
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    if height > max_image_height:
        max_image_height = height

    # Get offset for this batch
    offset = offset_data[batch_name]

    # Make predictions
    results = model(image)

    # Extract predictions
    predictions = []
    for result in results:  # Iterate through results (in case of multiple images)
        for box in result.boxes:  # Extract each bounding box
            x1, y1, x2, y2 = box.xyxy[0].tolist()  # Bounding box coordinates
            conf = box.conf[0].item()  # Confidence score
            cls = box.cls[0].item()  # Class ID
            if conf > 0.7:
                predictions.append([x1, y1, x2, y2, conf, cls])

    valid_centers = []
    valid_classes = []

    # Extract centers and apply offset
    for pred in predictions:
        x1, y1, x2, y2, _, cls = pred
        x_center = (x1 + x2) / 2
        x_center = ((x_center - width) * -1) + offset
        y_center = (y1 + y2) / 2
        valid_centers.append((x_center, y_center))
        valid_classes.append(int(cls))

    # Refine the offset for better alignment
    refined_offset = refine_offset(offset, combined_centers, valid_centers, distance_threshold)
    valid_centers = [(x + (refined_offset - offset), y) for x, y in valid_centers]

    # Add non-overlapping points to the combined data
    for valid_center, valid_class in zip(valid_centers, valid_classes):
        if not is_close_to_existing(valid_center, combined_centers, distance_threshold):
            combined_centers.append(valid_center)
            combined_classes.append(valid_class)

# Plot all results in one figure
unique_classes = list(set(combined_classes))
color_map = plt.get_cmap('tab10', len(unique_classes))
class_colors = {cls: color_map(i) for i, cls in enumerate(unique_classes)}

plt.figure(figsize=(15, 8))
for (x, y), cls in zip(combined_centers, combined_classes):
    plt.scatter(x, y, color=class_colors[cls], s=50, label=f'Class {cls}' if cls not in plt.gca().get_legend_handles_labels()[1] else "")

# Adjust axes to make (0, 0) the bottom-right
max_x = max(x for x, y in combined_centers)
plt.xlim(max_x, 0)  # Reverse x-axis
plt.ylim(max_image_height, 0)  # Reverse y-axis

# Add legend
handles = [plt.Line2D([0], [0], marker='o', color=color_map(i), label=f'Class {cls}', linestyle='', markersize=10)
           for i, cls in enumerate(unique_classes)]
plt.legend(handles=handles, title="Classes")

# Set labels and title
plt.xlabel('X-coordinate')
plt.ylabel('Y-coordinate')
plt.title('Combined Bounding Box Centers Across Batches')
plt.grid(True)
plt.show()
