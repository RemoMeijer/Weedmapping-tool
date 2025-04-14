import cv2
import numpy as np
from random import randint

with open('annotations/frame55.txt', 'r') as f:
    labels = f.read().splitlines()
img = cv2.imread('annotated_images/frame55.jpg')
h, w = img.shape[:2]

for label in labels:
    class_id, *poly = label.split(' ')

    poly = np.asarray(poly, dtype=np.float16).reshape(-1, 2)  # Read poly, reshape
    poly *= [w, h]  # Unscale

    cv2.polylines(img, [poly.astype('int')], True, (randint(0, 255), randint(0, 255), randint(0, 255)),
                  2)  # Draw Poly Lines

    cv2.imshow('img with poly', img)
    cv2.waitKey(1)

cv2.waitKey(0)
cv2.destroyAllWindows()