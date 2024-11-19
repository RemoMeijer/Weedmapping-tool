import os

png_folder = './images_old'
txt_folder = './annotations_bonirob'

# Loop through each file in the png folder
for png_file in os.listdir(png_folder):
    # Check if the file has a .png extension
    if png_file.endswith('.png'):
        # Construct the corresponding .txt filename
        txt_file = png_file.replace('.png', '.txt')

        # Check if the .txt file exists in the txt folder
        if not os.path.exists(os.path.join(txt_folder, txt_file)):
            # If the .txt file does not exist, delete the .png file
            os.remove(os.path.join(png_folder, png_file))
            print(f"Deleted {png_file} as no corresponding .txt file was found.")
