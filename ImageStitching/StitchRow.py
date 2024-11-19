from matplotlib import pyplot as plt
import cv2 as cv
from pathlib import Path
from stitching import Stitcher
import os
import shutil
from natsort import natsorted

def plot_image(img, figsize_in_inches=(5, 5)):
    fig, ax = plt.subplots(figsize=figsize_in_inches)
    ax.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
    plt.show()


def plot_images(imgs, figsize_in_inches=(5, 5)):
    fig, axs = plt.subplots(1, len(imgs), figsize=figsize_in_inches)
    for col, img in enumerate(imgs):
        axs[col].imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
    plt.show()

def get_image_paths(img_set):
    return [str(path.relative_to('.')) for path in Path('TempFrames').rglob(f'{img_set}*')]

source_folder = '../FrameExtractor/Frames'
temp_folder = './TempFrames'
all_images = natsorted([f for f in os.listdir(source_folder) if f.endswith(('.jpg', '.jpeg', '.png'))])

batch_size = 5
stitcher = Stitcher()
mainImage= None
offset = 0
for i in range (0, len(all_images), batch_size - 1):
    batch = all_images[i:i + batch_size]
    for image_name in batch:
        source_path = os.path.join(source_folder, image_name)
        destination_path = os.path.join(temp_folder, image_name)
        shutil.copy(source_path, destination_path)
    temp_images = get_image_paths('frame')
    mainImage = stitcher.stitch(temp_images)
    plot_image(mainImage, (20, 8))
    cv.imwrite(f'./batch/batch{i}.jpg', mainImage)

    # Get main image's width
    _, width = mainImage.shape[:2]

    # Get width of the last image in the batch
    last_image_name = batch[-1]
    last_image_path = os.path.join(source_folder, last_image_name)
    last_image = cv.imread(last_image_path)
    _, last_image_width = last_image.shape[:2]

    # Offset is main image, minus the last image width
    offset = offset + width - last_image_width
    print(offset)

    for temp_image in os.listdir(temp_folder):
        os.remove(os.path.join(temp_folder, temp_image))
