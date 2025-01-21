import json
import os

from PyQt6.QtCore import Qt, QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QFrame, QComboBox, QLabel, \
    QVBoxLayout, QTabWidget, QSpacerItem, QSizePolicy, QPushButton

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
    def __init__(self, state_manager, video_folder):
        super().__init__()

        self.state_manager = state_manager
        self.video_folder = video_folder

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

        # Set up QWebChannel
        self.web_channel = QWebChannel()
        self.backend = Backend(self)

        self.spacer = QSpacerItem(20, 70, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.available_videos = QComboBox()

        self.db = DatabaseHandler()

        self.main_ui()
        self.showMaximized()

    def main_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid = QGridLayout(central_widget)

        grid.addWidget(self.settings_frame(), 0, 0)
        grid.addWidget(self.map_container(), 0, 1)

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
            self.define_runs_dropdown(label, tab_layout)
            return tab
        if label_text == "Fields":
            self.define_field_tab(tab_layout)
            return tab
        if label_text == "Crops":
            self.define_crops_dropdown(label, tab_layout)
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

        tab_layout.addItem(self.spacer)

        # Info from clicked field
        info_label = QLabel()
        info_label.setText("Info:")
        info_label.setFont(self.big_font)
        info_label.setStyleSheet(f"color: {self.text_color};")

        tab_layout.addWidget(info_label)
        tab_layout.addWidget(self.field_id_label)
        tab_layout.addWidget(self.field_crop_label)
        tab_layout.addWidget(self.field_category_label)
        tab_layout.addItem(self.spacer)

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
        dropdown = self.run_dropdown
        label.setFont(self.small_font)
        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)
        tab_layout.addItem(self.spacer)

        video_generate_text = QLabel()
        video_generate_text.setText("Generate run from video file:")
        video_generate_text.setStyleSheet(f"color: {self.text_color};")
        video_generate_text.setFont(self.small_font)

        video_text = QLabel()
        video_text.setText("Video:")
        video_text.setStyleSheet(f"color: {self.text_color};")
        video_text.setFont(self.small_font)

        if os.path.exists(self.video_folder) and os.path.isdir(self.video_folder):
            video_files = [
                f for f in os.listdir(self.video_folder)
                if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov'))  # Add more extensions if needed
            ]
            self.available_videos.addItems(video_files)

        field_text = QLabel()
        field_text.setText("Field of run:")
        field_text.setStyleSheet(f"color: {self.text_color};")
        field_text.setFont(self.small_font)

        tab_layout.addWidget(video_generate_text)
        tab_layout.addWidget(video_text)
        tab_layout.addWidget(self.available_videos)
        tab_layout.addWidget(field_text)

        generate_field_combobox = QComboBox()
        generate_field_combobox.addItems([self.field_dropdown.itemText(i) for i in range(self.field_dropdown.count())])
        tab_layout.addWidget(generate_field_combobox)

        generate_run_button = QPushButton("Generate run", self)
        generate_run_button.clicked.connect(self.generate_run)

        tab_layout.addItem(self.spacer)
        tab_layout.addWidget(generate_run_button)

        return tab_layout

    def generate_run(self):
        selected_video = self.available_videos.currentText()
        if selected_video:
            self.state_manager.make_run(selected_video)
        else:
            print("No video selected")

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

    def map_container(self):
        # Make container to run html map in
        web_view = QWebEngineView()

        # Let web_page access Open Street Map
        web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        self.web_channel.registerObject("backend", self.backend)
        web_view.page().setWebChannel(self.web_channel)

        # Load the map.html file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(script_dir, "_map.html")
        html_file = QUrl.fromLocalFile(html_path)
        web_view.setUrl(html_file)

        # Add QWebEngineView to the layout
        layout = QGridLayout(self.map_frame)
        layout.addWidget(web_view)

        return self.map_frame
