import cv2
from ultralytics import RTDETR


def predict(chosen_model, img, classes=[], conf=0.5):
    if classes:
        results = chosen_model.predict(img, classes=classes, conf=conf)
    else:
        results = chosen_model.predict(img, conf=conf)

    return results


def predict_and_detect(chosen_model, img, classes=[], conf=0.5, rectangle_thickness=2, text_thickness=1):
    # Define colors for each class (in BGR format)
    class_colors = {
        0: (255, 0, 0),  # Class 0 - Blue
        1: (0, 255, 0),  # Class 1 - Green
        # Add more classes and colors as needed
    }

    # Predict results
    results = predict(chosen_model, img, classes, conf=conf)

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # Class ID
            color = class_colors.get(cls, (255, 255, 255))  # Default to white if class not found

            # Draw the rectangle with the class-specific color
            cv2.rectangle(img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])), color, rectangle_thickness)

            # Put the class name above the rectangle
            class_name = result.names[cls]
            cv2.putText(img, f"{class_name}",
                        (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                        cv2.FONT_HERSHEY_PLAIN, 1, color, text_thickness)

    return img, results


# defining function for creating a writer (for mp4 videos)
def create_video_writer(video_cap, output_filename):
    # grab the width, height, and fps of the frames in the video stream.
    frame_width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video_cap.get(cv2.CAP_PROP_FPS))
    # initialize the FourCC and a video writer object
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    writer = cv2.VideoWriter(output_filename, fourcc, fps,
                             (frame_width, frame_height))
    return writer


model = RTDETR("rt-detr.pt")

output_filename = "example.mp4"

video_path = r"../RunVideos/test_video.mp4"
cap = cv2.VideoCapture(video_path)
writer = create_video_writer(cap, output_filename)
while True:
    success, img = cap.read()
    if not success:
        break
    result_img, _ = predict_and_detect(model, img, classes=[], conf=0.5)
    writer.write(result_img)
    cv2.imshow("Image", result_img)

    cv2.waitKey(1)
writer.release()