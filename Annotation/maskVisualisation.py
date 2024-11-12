import cv2
import numpy as np
from random import randint

with open('Annotation/annotations/bonirob_2016-05-23-10-57-33_4_frame124.txt', 'r') as f:
    labels = f.read().splitlines()
img = cv2.imread('Annotation/images/bonirob_2016-05-23-10-57-33_4_frame124.png')
h, w = img.shape[:2]

for label in labels:
    class_id, *poly = label.split(' ')

    poly = np.asarray(poly, dtype=np.float16).reshape(-1, 2)  # Read poly, reshape
    poly *= [w, h]  # Unscale

    cv2.polylines(img, [poly.astype('int')], True, (randint(0, 255), randint(0, 255), randint(0, 255)),
                  2)  # Draw Poly Lines

    cv2.imshow('img with poly', img)
    cv2.waitKey(0)