import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QFrame, QGraphicsView, QGraphicsScene, \
    QGraphicsEllipseItem, QComboBox, QLabel, QVBoxLayout, QTabWidget, QGraphicsPixmapItem
from PyQt6.QtGui import QColor, QBrush, QPen, QPainter, QPixmap
from PyQt6.QtCore import Qt
import requests
from io import BytesIO

from Database.database_handler import DatabaseHandler


class ClickableEllipse(QGraphicsEllipseItem):
    def __init__(self, x, y, size, cls):
        super().__init__(x - size / 2, y - size / 2, size, size)  # Center the ellipse
        self.setBrush(QBrush(QColor.fromRgbF(*cls)))  # Set color from class mapping
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.class_color = cls  # Save the color for hover events

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("yellow")))  # Change color on hover
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor.fromRgbF(*self.class_color)))  # Revert color on hover out
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        print(
            f"Point clicked at ({self.rect().x() + self.rect().width() / 2}, {self.rect().y() + self.rect().height() / 2})")  # Placeholder action
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, centers, classes):
        super().__init__()
        self.setWindowTitle("Weed Detection Mapping")
        self.textColor = 'rgb(188, 190, 196)'
        self.backgroundDark = 'rgb(30, 31, 34)'
        self.backgroundLight = 'rgb(43, 45, 48)'

        self.field_dropdown = QComboBox()
        self.crop_dropdown = QComboBox()
        self.run_dropdown = QComboBox()

        self.centers = centers
        self.classes = classes

        self.db = DatabaseHandler()

        self.mainUI()
        self.showMaximized()

    def mainUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid = QGridLayout(central_widget)

        grid.addWidget(self.settingsFrame(), 0, 0, 3, 1)
        grid.addWidget(self.mapFrame(), 0, 1, 3, 3)

    def settingsFrame(self):
        settingsFrame = QFrame()
        settingsFrame.setStyleSheet(f"background-color: {self.backgroundLight};")

        # Create a QTabWidget for tabs
        tabs = QTabWidget(settingsFrame)
        tabs.setStyleSheet(f"background-color: {self.backgroundLight}; color: {self.textColor};")

        self.populate_dropdowns()

        # Create tabs
        runs_tab = self.createTab("Runs")
        fields_tab = self.createTab("Fields")
        crops_tab = self.createTab("Crops")

        # Add tabs to the tab widget
        tabs.addTab(runs_tab, "Runs")
        tabs.addTab(fields_tab, "Fields")
        tabs.addTab(crops_tab, "Crops")

        # Add tabs to the settingsFrame layout
        layout = QVBoxLayout(settingsFrame)
        layout.addWidget(tabs)

        return settingsFrame

    def createTab(self, label_text):
        """
        Create a tab containing a label and a dropdown list.
        """
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        # Add a label and dropdown to the tab
        label = QLabel(label_text + ":")
        dropdown = QComboBox()
        if label_text == "Runs":
            dropdown = self.run_dropdown
        if label_text == "Fields":
            dropdown = self.field_dropdown
        if label_text == "Crops":
            dropdown = self.crop_dropdown

        dropdown.setStyleSheet(f"color: {self.textColor};")

        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)

        return tab

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Update the grid when the mapFrame is resized
        self.graphicsView.setScene(self.createScene())

    def populate_dropdowns(self):
        # Fetch data from database (replace these with actual database queries)
        fields = self.db.get_all_fields()  # Example: Returns a list like ['Field A', 'Field B']
        crops = self.db.get_all_crops()  # Example: Returns a list like ['Crop X', 'Crop Y']
        runs = self.db.get_all_runs()  # Example: Returns a list like ['Run 1', 'Run 2']

        # Populate the dropdowns
        self.field_dropdown.addItems(fields)
        self.crop_dropdown.addItems(crops)
        self.run_dropdown.addItems(runs)

    def mapFrame(self):
        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(f"background-color: {self.backgroundDark};")

        self.graphicsView = QGraphicsView(self.map_frame)
        self.graphicsView.setScene(self.createScene())

        layout = QGridLayout(self.map_frame)
        layout.addWidget(self.graphicsView)

        return self.map_frame

    def createScene(self):


        return scene

    def drawGrid(self, scene):
        grid_size = 50  # Size between grid lines

        width = self.map_frame.width()
        height = self.map_frame.height()

        pen = QPen(QColor(80, 80, 80), 1)  # Grid line color

        # Draw vertical grid lines
        for x in range(0, width + 1, grid_size):
            scene.addLine(x, 0, x, height, pen)

        # Draw horizontal grid lines
        for y in range(0, height + 1, grid_size):
            scene.addLine(0, y, width, y, pen)

        # No need to draw axes below zero
        axis_pen = QPen(QColor(255, 255, 255), 2)  # Axis line color
        scene.addLine(0, 0, width, 0, axis_pen)  # X-axis at top
        scene.addLine(0, 0, 0, height, axis_pen)  # Y-axis at left

        # Set scene dimensions
        scene.setSceneRect(0, 0, width, height)
