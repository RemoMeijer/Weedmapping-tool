import sys
import cv2
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QFrame, QVBoxLayout, QWidget, QGridLayout, QApplication,
    QLabel, QSizePolicy, QHBoxLayout, QSlider
)
from PyQt6.QtCore import Qt
from automaticAnnotation import YoloAnnotator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.calibration_values = {}

        # Define colors
        self.text_color = 'rgb(188, 190, 196)'
        self.background_dark = 'rgb(30, 31, 34)'
        self.background_light = 'rgb(43, 45, 48)'

        # Define fonts
        self.big_font = QFont("Courier New", 20)
        self.small_font = QFont("Courier New", 15)

        # Annotator and images
        annotator = YoloAnnotator("config.yaml")
        original_image, calibrated_image = annotator.calibrate("./images/frame170.jpg")

        # QLabel widgets for images
        self.top_image_label = QLabel()
        self.bottom_image_label = QLabel()

        self.top_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.bottom_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.top_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Store original QPixmaps
        self.original_pixmap = self.cv_img_to_qpixmap(original_image)
        self.calibrated_pixmap = self.cv_img_to_qpixmap(calibrated_image)

        # Initial set (will be scaled in resizeEvent)
        self.top_image_label.setPixmap(self.original_pixmap)
        self.bottom_image_label.setPixmap(self.calibrated_pixmap)

        # Setup UI
        self.setWindowTitle("Annotation tool")
        self.main_ui()
        self.showMaximized()

    def main_ui(self):
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        grid = QGridLayout(centralWidget)

        grid.addWidget(self.settings_frame(), 0, 0)
        grid.addWidget(self.image_frame(), 0, 1)

        grid.setColumnStretch(0, 2)  # settings frame
        grid.setColumnStretch(1, 5)  # image display frame

    def settings_frame(self):
        settings_frame = QFrame(self)
        settings_frame.setStyleSheet(f"background-color: {self.background_light}")

        layout = QVBoxLayout(settings_frame)

        layout.addWidget(self.create_color_slider("Red"))
        layout.addWidget(self.create_color_slider("Green"))
        layout.addWidget(self.create_color_slider("Blue"))

        layout.addStretch()
        return settings_frame

    def image_frame(self):
        image_frame = QFrame(self)
        image_frame.setStyleSheet(f"background-color: {self.background_dark}")

        layout = QVBoxLayout(image_frame)
        layout.addWidget(self.top_image_label, stretch=1)
        layout.addWidget(self.bottom_image_label, stretch=1)
        return image_frame

    def cv_img_to_qpixmap(self, cv_img):
        if len(cv_img.shape) == 2:  # grayscale
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        elif cv_img.shape[2] == 1:  # single channel
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)

        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        return QPixmap.fromImage(q_img)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not self.original_pixmap.isNull():
            self.top_image_label.setPixmap(
                self.original_pixmap.scaled(
                    self.top_image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        if not self.calibrated_pixmap.isNull():
            self.bottom_image_label.setPixmap(
                self.calibrated_pixmap.scaled(
                    self.bottom_image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def create_color_slider(self, color):
        slider_frame = QFrame()
        h_layout = QHBoxLayout(slider_frame)

        label = QLabel(color)
        label.setFont(self.small_font)
        label.setStyleSheet(f"color: {self.text_color}")
        label.setFixedWidth(80)


        # Min slider
        min_slider = QSlider(Qt.Orientation.Horizontal)
        min_slider.setRange(0, 255)
        min_slider.setValue(0)

        # Max slider
        max_slider = QSlider(Qt.Orientation.Horizontal)
        max_slider.setRange(0, 255)
        max_slider.setValue(255)

        # Labels showing values
        min_label = QLabel("0")
        max_label = QLabel("255")
        min_label.setStyleSheet(f"color: {self.text_color}")
        max_label.setStyleSheet(f"color: {self.text_color}")

        # Connect updates
        min_slider.valueChanged.connect(lambda value: min_label.setText(str(value)))
        max_slider.valueChanged.connect(lambda value: max_label.setText(str(value)))

        # Save sliders
        self.calibration_values[color.lower()] = {
            "min": min_slider,
            "max": max_slider
        }

        # Add widgets to layout
        h_layout.addWidget(label)
        h_layout.addWidget(min_slider)
        h_layout.addWidget(min_label)
        h_layout.addSpacing(3)
        h_layout.addWidget(max_slider)
        h_layout.addWidget(max_label)

        return slider_frame

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
