import sys
import cv2
import numpy as np
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QFrame, QVBoxLayout, QWidget, QGridLayout, QApplication,
    QLabel, QSizePolicy, QHBoxLayout, QSlider
)
from PyQt6.QtCore import Qt
from automaticAnnotation import YoloAnnotator
import yaml


class MainWindow(QMainWindow):
    def __init__(self, config_path):
        super().__init__()

        self.calibration_values = {}

        self.config_values = None
        self._load_config(config_path)


        # Define colors
        self.text_color = 'rgb(188, 190, 196)'
        self.background_dark = 'rgb(30, 31, 34)'
        self.background_light = 'rgb(43, 45, 48)'

        # Define fonts
        self.big_font = QFont("Courier New", 20)
        self.small_font = QFont("Courier New", 15)

        # Annotator and images
        self.annotator = YoloAnnotator("config.yaml")
        original_image, calibrated_image = self.annotator.calibrate("./images/frame170.jpg")

        # QLabel widgets for images
        self.top_image_label = QLabel()
        self.bottom_image_label = QLabel()

        self.top_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.bottom_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.top_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Store original QPixmaps
        self.original_pixmap = self.annotator.cv_img_to_qpixmap(original_image)
        self.calibrated_pixmap = self.annotator.cv_img_to_qpixmap(calibrated_image)

        # Initial set (will be scaled in resizeEvent)
        self.top_image_label.setPixmap(self.original_pixmap)
        self.bottom_image_label.setPixmap(self.calibrated_pixmap)

        # Setup UI
        self.setWindowTitle("Annotation tool")
        self.main_ui()
        self.showMaximized()

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config_values = yaml.safe_load(f)

        required_sections = ["paths", "thresholds", "classes"]
        if not all(section in self.config_values for section in required_sections):
            raise ValueError(f"Config missing required sections: {required_sections}")

    def main_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid = QGridLayout(central_widget)

        grid.addWidget(self.settings_frame(), 0, 0)
        grid.addWidget(self.image_frame(), 0, 1)

        grid.setColumnStretch(0, 2)  # settings frame
        grid.setColumnStretch(1, 5)  # image display frame

    def settings_frame(self):
        settings_frame = QFrame(self)
        settings_frame.setStyleSheet(f"background-color: {self.background_light}")

        layout = QVBoxLayout(settings_frame)

        layout.addWidget(self.create_min_max_slider("Red"))
        layout.addWidget(self.create_min_max_slider("Green"))
        layout.addWidget(self.create_min_max_slider("Blue"))

        layout.addSpacing(5)

        layout.addWidget(self.create_calibration_sliders("Red"))

        layout.addStretch()
        return settings_frame

    def image_frame(self):
        image_frame = QFrame(self)
        image_frame.setStyleSheet(f"background-color: {self.background_dark}")

        layout = QVBoxLayout(image_frame)
        layout.addWidget(self.top_image_label, stretch=1)
        layout.addWidget(self.bottom_image_label, stretch=1)
        return image_frame


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

    def create_slider(self, initial_value=0):
        slider_frame = QFrame()
        layout = QHBoxLayout(slider_frame)

        # Min slider
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(initial_value)

        # Labels showing values
        label = QLabel(str(initial_value))
        label.setStyleSheet(f"color: {self.text_color}")

        # Connect updates
        slider.valueChanged.connect(lambda value: (
            label.setText(str(value)),
            self.update_mask()
        ))

        layout.addWidget(slider)
        layout.addWidget(label)

        return slider_frame, slider

    def create_min_max_slider(self, color):
        threshold = self.config_values["thresholds"]
        initial_min = threshold[f"{color.lower()}_min"]
        initial_max = threshold[f"{color.lower()}_max"]


        container = QFrame(self)
        slider_box = QHBoxLayout(container)

        label = QLabel(color)
        label.setFont(self.small_font)
        label.setStyleSheet(f"color: {self.text_color}")
        label.setFixedWidth(80)

        slider_min_widget, slider_min = self.create_slider(initial_min)
        slider_max_widget, slider_max = self.create_slider(initial_max)


        # Save sliders
        self.calibration_values[color.lower()] = {
            "min": slider_min,
            "max": slider_max,
        }

        slider_box.addWidget(label)
        slider_box.addWidget(slider_min_widget)
        slider_box.addWidget(slider_max_widget)
        return container

    def create_calibration_sliders(self, name):
        thresholds = self.config_values["thresholds"]
        initial_value = thresholds[f"{name.lower()}_boundary"]

        container = QFrame(self)
        slider_box = QHBoxLayout(container)

        label = QLabel(name + " calibration")
        label.setFont(self.small_font)
        label.setStyleSheet(f"color: {self.text_color}")
        label.setFixedWidth(200)

        slider_value_widget, slider_value = self.create_slider(initial_value)

        self.calibration_values[f"{name.lower()}_calibration"] = {
            "calibration": slider_value
        }

        slider_box.addWidget(label)
        slider_box.addWidget(slider_value_widget)
        return container

    def update_mask(self):
        self.calibrated_pixmap = self.annotator.update_mask(self.calibration_values, self.top_image_label.pixmap().toImage())

        self.bottom_image_label.setPixmap(
            self.calibrated_pixmap.scaled(
                self.bottom_image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("config.yaml")
    window.show()
    sys.exit(app.exec())
