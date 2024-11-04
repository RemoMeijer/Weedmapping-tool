import cv2
import numpy as np


def stitch_images_dynamic(image1, image2):
    # Convert images to grayscale for feature matching
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Detect ORB keypoints and descriptors
    orb = cv2.ORB_create(5000)
    keypoints1, descriptors1 = orb.detectAndCompute(gray1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(gray2, None)

    # Match descriptors using BFMatcher with Hamming distance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)

    # Sort matches by distance
    matches = sorted(matches, key=lambda x: x.distance)

    # Extract good match points
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    # Compute homography matrix
    H, _ = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

    # Determine size of new canvas to accommodate both images
    h1, w1 = image1.shape[:2]
    h2, w2 = image2.shape[:2]

    # Calculate corners of the warped second image
    corners_img2 = np.array([[0, 0], [0, h2], [w2, h2], [w2, 0]], dtype=np.float32).reshape(-1, 1, 2)
    transformed_corners_img2 = cv2.perspectiveTransform(corners_img2, H)

    # Determine the bounds of the stitched image
    all_corners = np.vstack(([[0, 0], [0, h1], [w1, h1], [w1, 0]], transformed_corners_img2.reshape(-1, 2)))
    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

    # Translation matrix to shift the images to positive coordinates
    translation_dist = [-x_min, -y_min]
    translation_matrix = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

    # Warp the second image to fit onto the canvas
    result_canvas = cv2.warpPerspective(image2, translation_matrix @ H, (x_max - x_min, y_max - y_min))

    # Place the first image on the canvas
    result_canvas[translation_dist[1]:h1 + translation_dist[1], translation_dist[0]:w1 + translation_dist[0]] = image1

    return result_canvas


# Load your images here
image1 = cv2.imread('./Frames/frame1.jpg')
image2 = cv2.imread('./Frames/frame2.jpg')

# Call the dynamic stitching function
stitched_image = stitch_images_dynamic(image1, image2)

# Show or save the stitched image
cv2.imshow("Stitched Image", stitched_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
