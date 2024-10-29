import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from random import randint

img_path = './images'
finished_img_path = './finished_images'
os.makedirs(f'{finished_img_path}', exist_ok=True)
os.makedirs(f'annotations', exist_ok=True)

count = 0
show_image = randint(1, 30)


class_ids = {
    "crop": 0,  # Assign class ID 0 for crop
    "weed": 1,  # Assign class ID 1 for weed
}

for img_name in os.listdir(img_path):
    annotations = []
    img = cv2.imread(f"{img_path}/{img_name}")

    height, width, _ = img.shape

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB for visualization with matplotlib

    # Step 1: Convert to HSV and apply color thresholding for green vegetation
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_green = (23, 30, 5)
    upper_green = (101, 195, 200)

    mask = cv2.inRange(hsv_img, lower_green, upper_green)
    segmented_img = cv2.bitwise_and(img_rgb, img_rgb, mask=mask)


    # Step 2: Apply morphological operations to clean up the mask
    kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (3, 3))
    processed_mask = cv2.morphologyEx(mask, cv2.MORPH_ERODE, kernel)


    # Find contours on the morphed mask
    contours, _ = cv2.findContours(processed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(contours)

    # Define a minimum area threshold to filter out small specks
    min_area = 80  # Adjust this value based on your image size and object size

    # Create a new mask for only large blobs
    large_blobs_mask = np.zeros_like(processed_mask)
    contour_count = -1
    for cnt in contours:
        if cv2.contourArea(cnt) > min_area:
            # img_copy = img_rgb.copy()
            # contour_count += 1

            # cv2.drawContours(img_copy, [cnt], -1, (0, 255, 0), thickness=2)
            # cv2.imshow("Contour", img_copy)
            # if contour_count == 0:
            #     cv2.waitKey(0)
            #
            # cv2.waitKey(1)
            #
            #
            # class_mapping = {"0": "weed", "1": "crop"}
            # user_class = class_mapping.get(input("Enter class for this contour (crop 1 /weed 0): ").strip())
            #
            # if user_class is None:
            #     print("Invalid or removed input.")
            #     contours.pop(contour_count)
            #     continue
            #
            #
            # # Get class ID
            # class_id = class_ids[user_class]
            #
            # # Extract and normalize contour points
            contour_points = cnt.squeeze()  # Remove extra dimensions if any
            normalized_points = []
            for point in contour_points:
                x, y = point
                normalized_x = x / width
                normalized_y = y / height
                # normalized_points.append(f"{normalized_x:.6f} {normalized_y:.6f}")
            #
            # # Prepare the line in YOLO segmentation format
            # annotation_line = f"{class_id} " + " ".join(normalized_points)
            # annotations.append(annotation_line)

    # with open(f"annotations/{os.path.splitext(img_name)[0]}.txt", "w") as f:
    #     for annotation in annotations:
    #         f.write(annotation + "\n")



    # Step 3: Edge Detection using Canny on the processed mask
    edges = cv2.Canny(large_blobs_mask, 100, 200)

    # Step 4: Overlay the edges on the original image
    overlay = img_rgb.copy()
    overlay[edges > 0] = [255, 0, 0]  # Color the edges in red for visibility

    large_blobs_mask = cv2.resize(large_blobs_mask, (img_rgb.shape[1], img_rgb.shape[0]))

    if len(img_rgb.shape) == 3 and img_rgb.shape[2] == 3:
        large_blobs_mask = cv2.cvtColor(large_blobs_mask, cv2.COLOR_GRAY2BGR)

    # Apply a color (e.g., green) to the mask
    colored_mask = large_blobs_mask.copy()
    colored_mask[:, :, 1] = large_blobs_mask[:, :, 1]  # Increase the green channel intensity
    colored_mask[:, :, 0] = 0  # Set blue channel to 0
    colored_mask[:, :, 2] = 0  # Set red channel to 0

    # Blend the original image and contour mask
    mask_highlighted = cv2.addWeighted(img_rgb, 0.4, colored_mask, 0.2, 0)

    print(f"{finished_img_path}/{img_name}")
    cv2.imwrite(f"{finished_img_path}/{img_name}", mask_highlighted)
    count += 1

    # Show random result
    if count == 1:

        # Visualization of the intermediate results
        fig, axs = plt.subplots(1, 2, figsize=(20, 10))

        axs[0].imshow(overlay)
        axs[0].set_title('Edge overlay', fontsize=30)
        axs[0].axis('off')

        axs[1].imshow(processed_mask)
        axs[1].set_title('Plant highlight', fontsize=30)
        axs[1].axis('off')

        plt.tight_layout()
        plt.show()

