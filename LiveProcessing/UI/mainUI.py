from PyQt6.QtCore import Qt, QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QFont
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QFrame, QComboBox, QLabel, \
    QVBoxLayout, QTabWidget, QSpacerItem, QSizePolicy

from Database.database_handler import DatabaseHandler


class Backend(QObject):
    # Signal to send data from Python to JavaScript
    sendDataToJs = pyqtSignal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @pyqtSlot(str)
    def receiveDataFromJs(self, data):
        print(f"Data received from JavaScript: {data}")
        # Here, parse the received JSON data and update the UI
        import json
        parsed_data = json.loads(data)
        self.updateUI(parsed_data)

    def updateUI(self, parsed_data):
        key_to_widget = {
            "id": self.main_window.field_id_label,
            "gewas": self.main_window.field_crop_label,
            "category": self.main_window.field_category_label,
        }

        for key, value in parsed_data.items():
            widget = key_to_widget.get(key)
            if widget:
                # Update QLabel
                if isinstance(widget, QLabel):
                    widget.setText(f"{key.capitalize()}: {value}")

                # Update QComboBox
                elif isinstance(widget, QComboBox):
                    if value not in [widget.itemText(i) for i in range(widget.count())]:
                        widget.addItem(value)
                    widget.setCurrentText(value)

        print(f"Updated UI with data: {parsed_data}")


class MainWindow(QMainWindow):
    def __init__(self, centers, classes):
        super().__init__()

        self.setWindowTitle("Weed Detection Mapping")
        self.textColor = 'rgb(188, 190, 196)'
        self.backgroundDark = 'rgb(30, 31, 34)'
        self.backgroundLight = 'rgb(43, 45, 48)'
        self.big_font = QFont("Courier New", 20)
        self.small_font = QFont("Courier New", 15)

        self.field_dropdown = QComboBox()
        self.field_runs_dropdown = QComboBox()
        self.crop_dropdown = QComboBox()
        self.run_dropdown = QComboBox()

        self.field_id_label = QLabel("Field ID: Not selected")
        self.field_crop_label = QLabel("Field crop: Not selected")
        self.field_category_label = QLabel("Field category: Not selected")
        self.field_runs_label = QLabel("Field runs:")


        self.centers = centers
        self.classes = classes

        self.db = DatabaseHandler()

        self.mainUI()
        self.showMaximized()

    def mainUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid = QGridLayout(central_widget)

        grid.addWidget(self.settingsFrame(), 0, 0)
        grid.addWidget(self.mapFrame(), 0, 1)

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 5)

    def settingsFrame(self):
        settingsFrame = QFrame()
        settingsFrame.setStyleSheet(f"background-color: {self.backgroundLight};")

        # Create a QTabWidget for tabs
        tabs = QTabWidget(settingsFrame)
        tabs.setStyleSheet(f"background-color: {self.backgroundLight}; color: {self.textColor};")

        self.populate_dropdowns()

        # Create tabs
        fields_tab = self.createTab("Fields")
        crops_tab = self.createTab("Crops")
        runs_tab = self.createTab("Runs")

        # Add tabs to the tab widget
        tabs.addTab(fields_tab, "Fields")
        tabs.addTab(crops_tab, "Crops")
        tabs.addTab(runs_tab, "Runs")

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
        dropdown.setStyleSheet(f"color: {self.textColor};")

        if label_text == "Runs":
            tab_layout = self.define_runs_dropdown(label, tab_layout)
        if label_text == "Fields":
            tab_layout = self.define_field_tab(tab_layout)
        if label_text == "Crops":
            tab_layout = self.define_crops_dropdown(label, tab_layout)

        return tab

    def define_field_tab(self, tab_layout):
        dropdown = self.field_dropdown

        own_fields_label = QLabel()
        own_fields_label.setText("Fields:")
        own_fields_label.setStyleSheet(f"color: {self.textColor};")
        own_fields_label.setFont(self.big_font)
        info_label = QLabel()
        info_label.setText("Info:")
        info_label.setFont(self.big_font)
        info_label.setStyleSheet(f"color: {self.textColor};")

        tab_layout.addWidget(own_fields_label)
        tab_layout.addWidget(dropdown)

        spacer = QSpacerItem(20, 70, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        tab_layout.addItem(spacer)

        self.field_id_label.setFont(self.small_font)
        self.field_id_label.setStyleSheet(f"color: {self.textColor};")
        self.field_category_label.setFont(self.small_font)
        self.field_category_label.setStyleSheet(f"color: {self.textColor};")
        self.field_crop_label.setFont(self.small_font)
        self.field_crop_label.setStyleSheet(f"color: {self.textColor};")

        self.field_runs_label.setFont(self.big_font)
        self.field_runs_label.setStyleSheet(f"color: {self.textColor};")

        tab_layout.addWidget(info_label)
        tab_layout.addWidget(self.field_id_label)
        tab_layout.addWidget(self.field_crop_label)
        tab_layout.addWidget(self.field_category_label)
        tab_layout.addItem(spacer)
        tab_layout.addWidget(self.field_runs_label)
        tab_layout.addWidget(self.field_runs_dropdown)

        return tab_layout

    def define_runs_dropdown(self, label, tab_layout):
        dropdown = self.run_dropdown

        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)

        return tab_layout

    def define_crops_dropdown(self, label, tab_layout):
        dropdown = self.crop_dropdown
        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)

        return tab_layout

    def populate_dropdowns(self):
        # Fetch data from database
        fields = self.db.get_all_fields()
        crops = self.db.get_all_crops()
        runs = self.db.get_all_runs()

        # Populate the dropdowns
        self.field_dropdown.addItems(fields)
        self.crop_dropdown.addItems(crops)
        self.run_dropdown.addItems(runs)
        self.field_runs_dropdown.addItem("None")

    def mapFrame(self):
        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(f"background-color: {self.backgroundDark};")

        # Create QWebEngineView
        self.web_view = QWebEngineView()

        # Enable LocalContentCanAccessRemoteUrls
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # Set up QWebChannel // todo
        self.web_channel = QWebChannel()
        self.backend = Backend(self)
        self.web_channel.registerObject("backend", self.backend)
        self.web_view.page().setWebChannel(self.web_channel)

        # Load the map.html file
        html_file = QUrl.fromLocalFile("/home/remco/Afstudeerstage/PythonScripts/AgronomischePerformanceMeting/LiveProcessing/UI/_map.html")  # Replace with your actual path
        self.web_view.setUrl(html_file)

        # Add QWebEngineView to the layout
        layout = QGridLayout(self.map_frame)
        layout.addWidget(self.web_view)

        return self.map_frame

    def createScene(self):
        pass

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