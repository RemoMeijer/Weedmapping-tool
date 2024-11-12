import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import pyautogui

lower_green = (29, 40, 20) # finetune this
upper_green = (90, 255, 110)

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


    first_image = True

    for img_name in os.listdir(img_path):
        annotations = []
        print(img_name)
        img = cv2.imread(f'{img_path}/{img_name}')

        if first_image:
            cv2.imshow(f"Display image", img)
            cv2.imshow(f"HSV", img)
            cv2.waitKey(15)
            first_image = False

        # Convert to HSV
        processed_mask, converted_hsv = convertHSV(img)
        cv2.imshow(f"HSV", img)
        height, width, _ = img.shape

        # Find contours
        contours, _ = cv2.findContours(processed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours = list(contours)

        # Area threshold
        min_area = 100
        contour_count = 0

        for cnt in contours:
            # If contour above threshold
            if cv2.contourArea(cnt) > min_area:
                img_copy = img.copy()
                cv2.drawContours(img_copy, [cnt], -1, (0, 255, 0), thickness=1)
                cv2.imshow(f"Display image", img_copy)
                cv2.waitKey(1)

                class_mapping = {"2": "weed", "1": "crop"}

                # User decision if weed or crop
                user_class = class_mapping.get(input("Enter class for this contour (crop 1 / weed 2 / other 3): ").strip())

                # Remove if other
                if user_class is None:
                    print("Removed contour.")
                    contours.pop(contour_count)
                    continue

                contour_count += 1

                # Get class ID
                class_id = class_ids[user_class]

                # Extract and normalize contour points
                contour_points = cnt.squeeze()
                normalized_points = []
                for point in contour_points:
                    x, y = point
                    normalized_x = x / width
                    normalized_y = y / height
                    normalized_points.append(f"{normalized_x:.6f} {normalized_y:.6f}")

                # Prepare the line in YOLO segmentation format
                annotation_line = f"{class_id} " + " ".join(normalized_points)
                annotations.append(annotation_line)

        # Write the annotations per image in txt file
        with open(f"Annotation/annotations/{os.path.splitext(img_name)[0]}.txt", "w") as f:
            for annotation in annotations:
                f.write(annotation + "\n")

    # When done, destroy windows
    cv2.destroyAllWindows()


loop_dir_and_annotate('images')
# for img_name in os.listdir('./images'):
# calibrateGreenValues(f'./images/bonirob_2016-05-04-10-05-47_1_frame36.png')
