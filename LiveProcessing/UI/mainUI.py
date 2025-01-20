import json

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
    send_data_to_js = pyqtSignal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window # Main window reference to set fields with incoming data

    @pyqtSlot(str)
    def receive_data_from_js(self, data):
        # Parse data
        print(f"Data received from JavaScript: {data}")
        parsed_data = json.loads(data)
        self.update_ui(parsed_data)

    def update_ui(self, parsed_data):
        # Data we want to keep
        key_to_widget = {
            "id": self.main_window.field_id_label,
            "gewas": self.main_window.field_crop_label,
            "category": self.main_window.field_category_label,
        }

        # Add data to UI
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
        self.send_data_to_js.emit("hoi")


class MainWindow(QMainWindow):
    def __init__(self, centers, classes):
        super().__init__()

        self.setWindowTitle("Weed Detection Mapping")
        self.text_color = 'rgb(188, 190, 196)'
        self.background_dark = 'rgb(30, 31, 34)'
        self.background_light = 'rgb(43, 45, 48)'
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

        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(f"background-color: {self.background_dark};")

        self.centers = centers
        self.classes = classes

        # Set up QWebChannel
        self.web_channel = QWebChannel()
        self.backend = Backend(self)

        self.db = DatabaseHandler()

        self.main_ui()
        self.showMaximized()

    def main_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid = QGridLayout(central_widget)

        grid.addWidget(self.settings_frame(), 0, 0)
        grid.addWidget(self.mapFrame(), 0, 1)

        # Settings gets 2/7 width, map gets 5/7
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 5)

    def settings_frame(self):
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"background-color: {self.background_light};")

        # Create a QTabWidget for tabs
        tabs = QTabWidget(settings_frame)
        tabs.setStyleSheet(f"background-color: {self.background_light}; color: {self.text_color};")

        # Add data from db to the dropdowns
        self.populate_dropdowns()

        # Create tabs
        fields_tab = self.create_tab("Fields")
        crops_tab = self.create_tab("Crops")
        runs_tab = self.create_tab("Runs")

        # Add tabs to the tab widget
        tabs.addTab(fields_tab, "Fields")
        tabs.addTab(crops_tab, "Crops")
        tabs.addTab(runs_tab, "Runs")

        # Add tabs to the settingsFrame layout
        layout = QVBoxLayout(settings_frame)
        layout.addWidget(tabs)

        return settings_frame

    def create_tab(self, label_text):
        # Create tab of settings frame
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        # Add a label and dropdown to the tab
        label = QLabel(label_text + ":")
        dropdown = QComboBox()
        dropdown.setStyleSheet(f"color: {self.text_color};")

        # Check which we want
        if label_text == "Runs":
            tab_layout = self.define_runs_dropdown(label, tab_layout)
        if label_text == "Fields":
            tab_layout = self.define_field_tab(tab_layout)
        if label_text == "Crops":
            tab_layout = self.define_crops_dropdown(label, tab_layout)

        return tab

    def define_field_tab(self, tab_layout):
        dropdown = self.field_dropdown

        # Existing fields from db
        own_fields_label = QLabel()
        own_fields_label.setText("Fields:")
        own_fields_label.setStyleSheet(f"color: {self.text_color};")
        own_fields_label.setFont(self.big_font)

        tab_layout.addWidget(own_fields_label)
        tab_layout.addWidget(dropdown)

        # Spacer for better UI
        spacer = QSpacerItem(20, 70, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        tab_layout.addItem(spacer)

        # Info from clicked field
        info_label = QLabel()
        info_label.setText("Info:")
        info_label.setFont(self.big_font)
        info_label.setStyleSheet(f"color: {self.text_color};")

        tab_layout.addWidget(info_label)
        tab_layout.addWidget(self.field_id_label)
        tab_layout.addWidget(self.field_crop_label)
        tab_layout.addWidget(self.field_category_label)
        tab_layout.addItem(spacer)

        # Runs on selected field
        self.field_id_label.setFont(self.small_font)
        self.field_id_label.setStyleSheet(f"color: {self.text_color};")
        self.field_category_label.setFont(self.small_font)
        self.field_category_label.setStyleSheet(f"color: {self.text_color};")
        self.field_crop_label.setFont(self.small_font)
        self.field_crop_label.setStyleSheet(f"color: {self.text_color};")
        self.field_runs_label.setFont(self.big_font)
        self.field_runs_label.setStyleSheet(f"color: {self.text_color};")

        tab_layout.addWidget(self.field_runs_label)
        tab_layout.addWidget(self.field_runs_dropdown)

        return tab_layout

    def define_runs_dropdown(self, label, tab_layout):
        # todo
        dropdown = self.run_dropdown

        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)

        return tab_layout

    def define_crops_dropdown(self, label, tab_layout):
        # todo
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
        # Make container to run html map in
        self.web_view = QWebEngineView()

        # Let web_page access Open Street Map
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)


        self.web_channel.registerObject("backend", self.backend)
        self.web_view.page().setWebChannel(self.web_channel)

        # Load the map.html file
        html_file = QUrl.fromLocalFile(
            "/home/remco/Afstudeerstage/PythonScripts/AgronomischePerformanceMeting/LiveProcessing/UI/_map.html")
        self.web_view.setUrl(html_file)

        # Add QWebEngineView to the layout
        layout = QGridLayout(self.map_frame)
        layout.addWidget(self.web_view)

        return self.map_frame
