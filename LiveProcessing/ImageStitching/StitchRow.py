import os
import cv2 as cv
import shutil
import json
from pathlib import Path
from natsort import natsorted
from stitching import Stitcher


class ImageStitcher:
    def __init__(self, source_folder, result_folder, json_file_path, temp_folder='TempFrames2', batch_size=5):
        self.source_folder = source_folder
        self.result_folder = result_folder
        self.temp_folder = temp_folder
        self.batch_size = batch_size
        self.stitcher = Stitcher()
        self.all_offsets = {}
        self.main_image = None
        self.offset = 0
        self.first_image = True
        self.json_file_path = json_file_path

        # Create necessary directories if they don't exist
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.result_folder, exist_ok=True)

    def _get_image_paths(self, img_set):
        return [str(path.relative_to('.')) for path in Path(self.temp_folder).rglob(f'{img_set}*')]

    def stitch_images(self):
        try:

            last_image_width = 0

            all_images = natsorted([
                f for f in os.listdir(self.source_folder)
                if f.endswith(('.jpg', '.jpeg', '.png'))
            ])

            if not all_images:
                raise RuntimeError(f"No images found in {self.source_folder}")

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
                    if self.main_image is None:
                        raise RuntimeError(f"Stitching failed for batch {i}")
                else:
                    break

                # Save the stitched batch image
                result_path = os.path.join(self.result_folder, f'batch{i}.jpg')
                success = cv.imwrite(result_path, self.main_image)
                if not success:
                    raise IOError(f'Failed to write stitched image to: {result_path}')

                # Calculate offset
                _, width = self.main_image.shape[:2]
                last_image_name = batch[-1]
                last_image_path = os.path.join(self.source_folder, last_image_name)
                last_image = cv.imread(last_image_path)
                if last_image is None:
                    raise IOError(f'Could not read image {last_image_path}')

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
                    # File already removed error catching
                    try:
                        os.remove(os.path.join(self.temp_folder, temp_image))
                    except FileNotFoundError:
                        pass

            # Save offsets to a JSON file
            full_json_path = os.path.join(self.result_folder, self.json_file_path)
            with open(full_json_path, 'w', encoding='utf-8') as json_file:
                json.dump(self.all_offsets, json_file, indent=4)
            print(f"Stitching complete!")

            # Remove folder
            shutil.rmtree(self.temp_folder)

            return self.offset + last_image_width

        except Exception as e:
            print(f"Stitching error: {e}")
            shutil.rmtree(self.temp_folder)
            raise
