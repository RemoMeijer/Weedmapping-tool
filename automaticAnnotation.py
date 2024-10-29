import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from random import randint

lower_green = (27, 35, 24) # finetune this
upper_green = (100, 250, 150)

def calibrateGreenValues(img):
    img = cv2.imread(f'{img}')
    processed_mask, hsv = convertHSV(img)
    # Visualization of the intermediate results
    fig, axs = plt.subplots(1, 2, figsize=(20, 10))

    axs[0].imshow(hsv)
    axs[0].set_title('Hsv green image', fontsize=30)
    axs[0].axis('off')

    axs[1].imshow(processed_mask)
    axs[1].set_title('Highlighted areas', fontsize=30)
    axs[1].axis('off')

    plt.tight_layout()
    plt.show()


def convertHSV(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Remove some graining
    kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (3, 3))
    inner_processed_mask = cv2.morphologyEx(mask, cv2.MORPH_ERODE, kernel)
    inner_processed_mask = cv2.morphologyEx(inner_processed_mask, cv2.MORPH_OPEN, kernel)
    inner_processed_mask = cv2.morphologyEx(inner_processed_mask, cv2.MORPH_DILATE, kernel)

    return inner_processed_mask, hsv

def loop_dir_and_annotate(images_dir):
    img_path = images_dir
    os.makedirs(f'annotations', exist_ok=True)

    class_ids = {
        "crop": 0,  # Assign class ID 0 for crop
        "weed": 1,  # Assign class ID 1 for weed
    }

    for img_name in os.listdir(img_path):
        annotations = []
        img = cv2.imread(f'{img_path}/{img_name}')

        processed_mask, _ = convertHSV(img)
        height, width, _ = img.shape

        # Find contours
        contours, _ = cv2.findContours(processed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = list(contours)

        # Area threshold
        min_area = 80

        # Create a new mask for only large blobs
        large_blobs_mask = np.zeros_like(processed_mask)
        contour_count = -1
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                img_copy = img.copy()
                contour_count += 1

                cv2.drawContours(img_copy, [cnt], -1, (0, 255, 0), thickness=2)
                cv2.imshow(f"{img_name}", img_copy)
                if contour_count == 0:
                    cv2.waitKey(0)

                cv2.waitKey(1)


                class_mapping = {"2": "weed", "1": "crop"}
                user_class = class_mapping.get(input("Enter class for this contour (crop 1 /weed 2): ").strip())

                if user_class is None:
                    print("Invalid or removed input.")
                    contours.pop(contour_count)
                    continue


                # Get class ID
                class_id = class_ids[user_class]

                # Extract and normalize contour points
                contour_points = cnt.squeeze()  # Remove extra dimensions if any
                normalized_points = []
                for point in contour_points:
                    x, y = point
                    normalized_x = x / width
                    normalized_y = y / height
                    normalized_points.append(f"{normalized_x:.6f} {normalized_y:.6f}")

                # Prepare the line in YOLO segmentation format
                annotation_line = f"{class_id} " + " ".join(normalized_points)
                annotations.append(annotation_line)

        cv2.destroyAllWindows()

        with open(f"annotations/{os.path.splitext(img_name)[0]}.txt", "w") as f:
            for annotation in annotations:
                f.write(annotation + "\n")

loop_dir_and_annotate('./images')
# calibrateGreenValues('./images/bonirob_2016-05-23-11-02-39_5_frame203.png')