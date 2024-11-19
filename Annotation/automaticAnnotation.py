import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import pyautogui

lower_green = (29, 40, 20) # finetune this
upper_green = (120, 255, 150)

# def calibrateGreenValues(img):
#     img = cv2.imread(f'{img}')
#     processed_mask, hsv = convertHSV(img)
#     # Visualization of the intermediate results
#     fig, axs = plt.subplots(1, 2, figsize=(20, 10))
#
#     axs[0].imshow(hsv)
#     axs[0].set_title('Hsv green image', fontsize=30)
#     axs[0].axis('off')
#
#     axs[1].imshow(processed_mask)
#     axs[1].set_title('Highlighted areas', fontsize=30)
#     axs[1].axis('off')
#
#     plt.tight_layout()
#     plt.show()

def extract_green_plants_refined(img_path):
    # Load the image
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Split the color channels
    r, g, b = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]

    # Define a mask where green is prominent and of sufficient intensity
    # Adjust these thresholds to reduce sensitivity to light ground areas
    green_mask = (g > r + 15) & (g > b + 15) & (g > 20) & (g < 255) & (r < 220) & (b < 100)

    # Convert boolean mask to uint8 (binary image)
    green_mask = green_mask.astype(np.uint8) * 255

    # # Apply morphological operations to clean up the mask
    # kernel = np.ones((3, 3), np.uint8)
    # green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
    # green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)

    # Create an output image that shows only the green plants
    green_plants = cv2.bitwise_and(img_rgb, img_rgb, mask=green_mask)

    # Visualization of the intermediate results
    fig, axs = plt.subplots(1, 3, figsize=(20, 10))

    axs[0].imshow(img_rgb)
    axs[0].set_title('Original Image', fontsize=20)
    axs[0].axis('off')

    axs[1].imshow(green_mask, cmap='gray')
    axs[1].set_title('Refined Green Mask', fontsize=20)
    axs[1].axis('off')

    axs[2].imshow(green_plants)
    axs[2].set_title('Refined Extracted Green Plants', fontsize=20)
    axs[2].axis('off')

    plt.tight_layout()
    plt.show()

def convertHSV(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Remove some graining
    kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (5, 5))
    inner_processed_mask = cv2.morphologyEx(mask, cv2.MORPH_ERODE, kernel)
    inner_processed_mask = cv2.morphologyEx(inner_processed_mask, cv2.MORPH_OPEN, kernel)
    inner_processed_mask = cv2.morphologyEx(inner_processed_mask, cv2.MORPH_DILATE, kernel)


    return inner_processed_mask, hsv


# Modified function to return green mask only, without visualization
def extract_green_plants_mask(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    r, g, b = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]

    # Create refined mask for green areas
    green_mask = (g> r + 14) & (g > b) & (g > 50) & (g < 250) & (r < 200) & (b < 100)
    green_mask = green_mask.astype(np.uint8) * 255

    # # Apply morphological operations to clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_DILATE, kernel)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_DILATE, kernel)

    # # green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)

    return green_mask


# Main loop for annotation
def loop_dir_and_annotate(images_dir):
    img_path = images_dir
    os.makedirs('annotations', exist_ok=True)

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
            cv2.waitKey(0)
            first_image = False

        # Convert to HSV
        processed_mask = extract_green_plants_mask(img)
        cv2.imshow(f"HSV", processed_mask)
        height, width, _ = img.shape

        # Find contours
        contours, _ = cv2.findContours(processed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours = list(contours)

        # Area threshold
        min_area = 600
        contour_count = 0

        for cnt in contours:
            # If contour above threshold
            if cv2.contourArea(cnt) > min_area:
                img_copy = img.copy()
                cv2.drawContours(img_copy, [cnt], -1, (0, 0, 255), thickness=2)

                # cv2.drawContours(img_copy, [cnt], -1, (0, 255, 0), thickness=1)

                # Create a resized version for display
                scale_percent = 70  # Scale down to 50% of the original size
                display_width = int(img_copy.shape[1] * scale_percent / 100)
                display_height = int(img_copy.shape[0] * scale_percent / 100)
                dim = (display_width, display_height)

                resized_img = cv2.resize(img_copy, dim, interpolation=cv2.INTER_AREA)

                cv2.imshow(f"Display image", resized_img)
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
        with open(f"annotations/{os.path.splitext(img_name)[0]}.txt", "w") as f:
            for annotation in annotations:
                f.write(annotation + "\n")

    # When done, destroy windows
    cv2.destroyAllWindows()


loop_dir_and_annotate('./images')
# for img_name in os.listdir('./images'):
# calibrateGreenValues(f'./images/frame1.jpg')
# extract_green_plants_refined(f'./images/frame1.jpg')
