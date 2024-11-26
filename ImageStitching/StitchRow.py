import os
import cv2 as cv
import shutil
import json
from pathlib import Path
from natsort import natsorted
from stitching import Stitcher


class ImageStitcher:
    def __init__(self, source_folder, result_folder, temp_folder='./TempFrames', batch_size=5):
        self.source_folder = source_folder
        self.result_folder = result_folder
        self.temp_folder = temp_folder
        self.batch_size = batch_size
        self.stitcher = Stitcher()
        self.all_offsets = {}
        self.main_image = None
        self.offset = 0
        self.first_image = True

        # Create necessary directories if they don't exist
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.result_folder, exist_ok=True)

    def _get_image_paths(self, img_set):
        return [str(path.relative_to('.')) for path in Path(self.temp_folder).rglob(f'{img_set}*')]

    def stitch_images(self):
        all_images = natsorted([
            f for f in os.listdir(self.source_folder)
            if f.endswith(('.jpg', '.jpeg', '.png'))
        ])

        for i in range(0, len(all_images), self.batch_size - 1):
            batch = all_images[i:i + self.batch_size]

            # Copy images to the temporary folder
            for image_name in batch:
                source_path = os.path.join(self.source_folder, image_name)
                destination_path = os.path.join(self.temp_folder, image_name)
                shutil.copy(source_path, destination_path)

            temp_images = self._get_image_paths('frame')

            # Stitch the batch
            if len(batch) > 1:
                self.main_image = self.stitcher.stitch(temp_images)
            else:
                break

            # Save the stitched batch image
            result_path = os.path.join(self.result_folder, f'batch{i}.jpg')
            cv.imwrite(result_path, self.main_image)

            # Calculate offset
            _, width = self.main_image.shape[:2]
            last_image_name = batch[-1]
            last_image_path = os.path.join(self.source_folder, last_image_name)
            last_image = cv.imread(last_image_path)
            _, last_image_width = last_image.shape[:2]

            if self.first_image:
                self.offset = 0
                self.first_image = False
            else:
                self.offset = self.offset + width - last_image_width

            self.all_offsets[f'batch{i}.jpg'] = [self.offset, last_image_width]
            print(f'Offset for batch{i}.jpg: {self.offset}')

            # Clean up the temporary folder
            for temp_image in os.listdir(self.temp_folder):
                os.remove(os.path.join(self.temp_folder, temp_image))

        # Save offsets to a JSON file
        with open(os.path.join(self.result_folder, 'batch_offsets.json'), 'w') as json_file:
            json.dump(self.all_offsets, json_file, indent=4)
        print(f"Stitching complete! Results saved in '{self.result_folder}'.")
