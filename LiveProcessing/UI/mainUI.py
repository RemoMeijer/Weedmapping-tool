import json
import os

from PyQt6.QtCore import Qt, QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QFrame, QComboBox, QLabel, \
    QVBoxLayout, QTabWidget, QSpacerItem, QSizePolicy, QPushButton, QLineEdit, QHBoxLayout, QMessageBox

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
        parsed_data = json.loads(data)
        print(parsed_data)
        # Check the identifier to handle different types of data
        identifier = parsed_data.get("identifier")

        if identifier == "field":
            field_properties = parsed_data.get("properties", {})
            # print(f"Field data received: {field_properties}")

            # Perform necessary actions with the field properties
            self.update_ui(field_properties)

        else:
            print(f"Unknown identifier: {identifier}")


    def update_ui(self, parsed_data):
        # Data we want to keep
        key_to_widget = {
            "id": self.main_window.field_name_label,
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
        self.update_field_runs_dropdown(parsed_data)


    def update_field_runs_dropdown(self, data):
        field_name = "Field_" + str(data["id"])
        if not field_name:
            print("No field name in JS data")
            return

        field_id = self.main_window.db.get_field_id_by_field_name(field_name)
        if not field_id:
            print(f"No field id found in DB with name {field_name}")
            return

        field_runs = self.main_window.db.get_runs_by_field_id(field_id)
        self.main_window.field_runs_dropdown.clear()
        if field_runs:
            run_ids = [str(run[0]) for run in field_runs]
            self.main_window.field_runs_dropdown.addItems(run_ids)
        else:
            self.main_window.field_runs_dropdown.addItem("No runs available")


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
        self.generate_field_combobox = QComboBox()

        self.field_name_label = QLabel("Field Name: Not selected")
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

        self.start_gps_input_lat = QLineEdit()
        self.start_gps_input_lon = QLineEdit()
        self.end_gps_input_lat = QLineEdit()
        self.end_gps_input_lon = QLineEdit()

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

    def goto_field_on_map(self):
        field = self.field_dropdown.currentText()
        field_id = field.replace("Field_", "")
        self.goto_field(field_id)

    def goto_field_on_map_from_run_tab(self):
        run_id = self.run_dropdown.currentText()
        field = self.db.get_field_by_run_id(run_id)
        if field is not None:
            field_id = field.replace("Field_", "")
            self.goto_field(field_id)


    def goto_field(self, field_id):
        data = {
            "identifier": "field",  # Add an identifier
            "field_id": field_id  # Include the field ID
        }

        json_data = json.dumps(data)

        self.backend.send_data_to_js.emit(json_data)

    def send_run_detections_from_fields_tab(self):
        run_id = self.field_runs_dropdown.currentText()
        self.send_detections(run_id)

    def send_run_detections_from_run_tab(self):
        run_id = self.run_dropdown.currentText()
        self.goto_field_on_map_from_run_tab()
        self.send_detections(run_id)

    def send_detections(self, run_id):
        # Check if run_id is valid or not default
        if not run_id or run_id == "No runs available":
            detections = []
        else:
            detections = self.db.get_detections_by_run_id(run_id=run_id)

        # Even with empty detections, they need to be sent to clean the map of the old detections
        data = {
            "identifier": "run_detections",  # Add an identifier
            "detections": detections  # Include the field ID
        }

        json_data = json.dumps(data)
        self.backend.send_data_to_js.emit(json_data)

    def define_field_tab(self, tab_layout):
        dropdown = self.field_dropdown
        dropdown.currentIndexChanged.connect(self.goto_field_on_map)

        self.field_runs_dropdown.currentIndexChanged.connect(self.send_run_detections_from_fields_tab)

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
        tab_layout.addWidget(self.field_name_label)
        tab_layout.addWidget(self.field_crop_label)
        tab_layout.addWidget(self.field_category_label)
        tab_layout.addItem(self.spacer)

        # Runs on selected field
        self.field_name_label.setFont(self.small_font)
        self.field_name_label.setStyleSheet(f"color: {self.text_color};")
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
        self.run_dropdown.currentIndexChanged.connect(self.send_run_detections_from_run_tab)
        label.setFont(self.small_font)
        delete_run_button = QPushButton("Delete run", self)
        delete_run_button.clicked.connect(self.delete_selected_run)
        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)
        tab_layout.addWidget(delete_run_button)
        tab_layout.addItem(self.spacer)

        # Video generation section
        video_generate_text = QLabel()
        video_generate_text.setText("Generate run from video file:")
        video_generate_text.setStyleSheet(f"color: {self.text_color};")
        video_generate_text.setFont(self.small_font)
        tab_layout.addWidget(video_generate_text)

        # Video Label and ComboBox in one row
        video_row_layout = QHBoxLayout()
        video_label = QLabel("Video:")
        video_label.setStyleSheet(f"color: {self.text_color};")
        video_label.setFont(self.small_font)

        self.available_videos = QComboBox()
        if os.path.exists(self.video_folder) and os.path.isdir(self.video_folder):
            video_files = [
                f for f in os.listdir(self.video_folder)
                if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov'))  # Add more extensions if needed
            ]
            self.available_videos.addItems(video_files)

        video_row_layout.addWidget(video_label)
        video_row_layout.addWidget(self.available_videos)
        tab_layout.addLayout(video_row_layout)

        # Field Label and ComboBox in one row
        field_row_layout = QHBoxLayout()
        field_label = QLabel("Field:")
        field_label.setStyleSheet(f"color: {self.text_color};")
        field_label.setFont(self.small_font)

        self.generate_field_combobox.addItems(
            [self.field_dropdown.itemText(i) for i in range(self.field_dropdown.count())])

        field_row_layout.addWidget(field_label)
        field_row_layout.addWidget(self.generate_field_combobox)
        tab_layout.addLayout(field_row_layout)

        # Start and End GPS input fields in one row
        gps_input_layout_start = QHBoxLayout()
        start_gps_label = QLabel("Start GPS:\t")
        start_gps_label.setStyleSheet(f"color: {self.text_color};")
        start_gps_label.setFont(self.small_font)
        self.start_gps_input_lat.setPlaceholderText("Enter Latitude")
        self.start_gps_input_lon.setPlaceholderText("Enter Longitude")

        gps_input_layout_end = QHBoxLayout()
        end_gps_label = QLabel("End GPS:\t")
        end_gps_label.setStyleSheet(f"color: {self.text_color};")
        end_gps_label.setFont(self.small_font)
        self.end_gps_input_lat.setPlaceholderText("Enter Latitude")
        self.end_gps_input_lon.setPlaceholderText("Enter Longitude")

        gps_input_layout_start.addWidget(start_gps_label)
        gps_input_layout_start.addWidget(self.start_gps_input_lat)
        gps_input_layout_start.addWidget(self.start_gps_input_lon)

        gps_input_layout_end.addWidget(end_gps_label)
        gps_input_layout_end.addWidget(self.end_gps_input_lat)
        gps_input_layout_end.addWidget(self.end_gps_input_lon)

        tab_layout.addLayout(gps_input_layout_start)
        tab_layout.addLayout(gps_input_layout_end)

        # Generate Run button
        generate_run_button = QPushButton("Generate run", self)
        generate_run_button.clicked.connect(self.generate_run)

        tab_layout.addItem(self.spacer)
        tab_layout.addWidget(generate_run_button)

        return tab_layout

    def generate_run(self):
        # Get inputs
        selected_video = self.available_videos.currentText()
        selected_field = self.generate_field_combobox.currentText()

        # Get GPS values with clear names
        ns_start = self.start_gps_input_lat.text().strip()
        ew_start = self.start_gps_input_lon.text().strip()
        ns_end = self.end_gps_input_lat.text().strip()
        ew_end = self.end_gps_input_lon.text().strip()

        if not self.validate_coordinates(ns_start, ew_start, ns_end, ew_end):
            print("Invalid GPS coordinates")
            return

        try:
            # Convert to floats after validation
            start_gps = (float(ns_start), float(ew_start))
            end_gps = (float(ns_end), float(ew_end))
            self.state_manager.make_run(selected_video, selected_field, start_gps, end_gps)
        except ValueError:
            print("GPS coordinates must be numbers")

    def validate_coordinates(self, ns1, ew1, ns2, ew2):
        """Validate GPS coordinates are within Earth's ranges"""

        def is_valid(ns, ew):
            try:
                lat = float(ns)
                lon = float(ew)
                return -90 <= lat <= 90 and -180 <= lon <= 180
            except ValueError:
                return False

        return all([
            ns1 and ew1 and ns2 and ew2,  # Check non-empty
            is_valid(ns1, ew1),  # Check start coordinates
            is_valid(ns2, ew2)  # Check end coordinates
        ])

    def delete_selected_run(self):
        selected_run = self.run_dropdown.currentText()

        confirm_deletion = QMessageBox(self)
        confirm_deletion.setIcon(QMessageBox.Icon.Question)
        confirm_deletion.setWindowTitle("Confirm Deletion")
        confirm_deletion.setText(f"Are you sure you want to delete run {selected_run}?")

        delete_button = confirm_deletion.addButton("Delete Run", QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = confirm_deletion.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        confirm_deletion.setDefaultButton(cancel_button)

        confirm_deletion.exec()

        if confirm_deletion.clickedButton() == delete_button:
            self.db.delete_run_by_run_id(selected_run)
            print(f"Deleted run {selected_run}")
            self.populate_dropdowns()


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
