import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QFrame, QComboBox, QLabel, \
    QVBoxLayout, QTabWidget, QSpacerItem, QSizePolicy, QPushButton, QLineEdit, QHBoxLayout, QMessageBox
from fontTools.feaLib.ast import fea_keywords

from Database.database_handler import DatabaseHandler
from LiveProcessing.UI.backend import Backend
from LiveProcessing.UI.mapHandler import MapHandler
from LiveProcessing.UI.uiUpdater import UiUpdater

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from StateManager import StateManager


class MainWindow(QMainWindow):
    def __init__(self, state_manager: 'StateManager', video_folder):
        super().__init__()
        self.video_folder = video_folder

        # Define other helper classes
        self.db = DatabaseHandler()
        self.backend = Backend(self, self.db)
        self.mapHandler = MapHandler(self.backend)
        self.uiManager = UiUpdater(self, self.db, self.backend)
        self.state_manager = state_manager

        # Define colors
        self.text_color = 'rgb(188, 190, 196)'
        self.background_dark = 'rgb(30, 31, 34)'
        self.background_light = 'rgb(43, 45, 48)'

        # Define fonts
        self.big_font = QFont("Courier New", 20)
        self.small_font = QFont("Courier New", 15)

        # Initiate dropdowns
        self.all_fields_dropdown = QComboBox()
        self.all_crops_dropdown = QComboBox()
        self.all_runs_dropdown = QComboBox()
        self.generate_field_combobox = QComboBox()
        self.runs_in_field_dropdown = QComboBox()
        self.available_videos = QComboBox()
        self.compare_runs_one_dropdown = QComboBox()
        self.compare_runs_two_dropdown = QComboBox()
        self.compared_list = QComboBox()

        self.dropdowns = (
            self.all_fields_dropdown,
            self.all_crops_dropdown,
            self.all_runs_dropdown,
            self.generate_field_combobox,
            self.runs_in_field_dropdown,
            self.available_videos,
            self.compare_runs_one_dropdown,
            self.compare_runs_two_dropdown,
            self.compared_list,
        )

        # Initiate selected field labels
        self.selected_field_name_label = self.make_label("Not selected")
        self.selected_field_crop_label = self.make_label("Not selected")
        self.selected_field_category_label = self.make_label("Not selected")

        # Setup map frame
        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(f"background-color: {self.background_dark};")

        self.web_channel = QWebChannel()

        # Add data from db to the dropdowns
        self.uiManager.update_dropdowns()

        # Spacer for when whitespace is preferred
        self.spacer = QSpacerItem(20, 70, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        # Define GPS input fields for generating run
        self.start_gps_input_lat = QLineEdit()
        self.start_gps_input_lon = QLineEdit()
        self.end_gps_input_lat = QLineEdit()
        self.end_gps_input_lon = QLineEdit()

        # Setup handler for when data is received
        self.backend.field_data_received.connect(self.handle_field_update)

        # Setup window
        self.setWindowTitle("Weed Detection Mapping")
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

    def goto_field(self):
        field_name = self.all_fields_dropdown.currentText().strip("Field_")
        self.mapHandler.goto_field(field_name)

    def define_field_tab(self, tab_layout):
        self.all_fields_dropdown.currentIndexChanged.connect(self.goto_field)
        self.runs_in_field_dropdown.currentIndexChanged.connect(self.backend.send_run_detections_from_fields_tab)

        # Existing fields from db
        own_fields_label = self.make_label("Fields:", small=False)
        tab_layout.addWidget(own_fields_label)
        tab_layout.addWidget(self.all_fields_dropdown)
        tab_layout.addItem(self.spacer)

        info_layout = self.define_info_section()

        tab_layout.addLayout(info_layout)

        field_runs_label = self.make_label("Field Runs:", small=False)
        tab_layout.addWidget(field_runs_label)
        tab_layout.addWidget(self.runs_in_field_dropdown)
        tab_layout.addItem(self.spacer)

        tab_layout.addLayout(self.compare_run_ui())

        compared_list_label = self.make_label("Compared list:", small=False)
        tab_layout.addWidget(compared_list_label)
        self.compared_list.currentIndexChanged.connect(self.backend.send_comparisons_current_text)
        self.compared_list.activated.connect(self.backend.send_comparisons_current_text)

        tab_layout.addWidget(self.compared_list)

        delete_comparison = QPushButton("Delete Comparison")
        delete_comparison.setStyleSheet(f"color: {self.text_color};")
        delete_comparison.clicked.connect(self.uiManager.delete_comparison)
        tab_layout.addWidget(delete_comparison)

        return tab_layout

    def define_info_section(self):
        info_layout = QVBoxLayout()

        # Info header
        info_label = self.make_label("Info:", False)
        info_layout.addWidget(info_label)

        # Define field layouts dynamically
        info_layout.addLayout(self._create_info_row("Field Name:", self.selected_field_name_label))
        info_layout.addLayout(self._create_info_row("Crop Name:", self.selected_field_crop_label))
        info_layout.addLayout(self._create_info_row("Field Category:", self.selected_field_category_label))

        info_layout.addItem(self.spacer)

        return info_layout

    def _create_info_row(self, label_text, value_label):
        """Helper method to create an HBox layout with a fixed label and a value label."""
        layout = QHBoxLayout()
        label = self.make_label(label_text)

        layout.addWidget(label, 1)  # 20% width
        layout.addWidget(value_label, 4)  # 80% width

        return layout

    def define_runs_dropdown(self, label, tab_layout):
        # Delete run section
        self.all_runs_dropdown.currentIndexChanged.connect(self.backend.send_run_detections_from_run_tab)
        label.setFont(self.small_font)
        delete_run_button = QPushButton("Delete run", self)
        delete_run_button.clicked.connect(self.delete_selected_run)

        tab_layout.addWidget(label)
        tab_layout.addWidget(self.all_runs_dropdown)
        tab_layout.addWidget(delete_run_button)
        tab_layout.addItem(self.spacer)

        # Video generation section
        video_generate_text = self.make_label("Generate run from video file:")
        tab_layout.addWidget(video_generate_text)

        # Video Label and ComboBox in one row
        video_row_layout = QHBoxLayout()
        video_label = self.make_label("Video:")

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
        field_label = self.make_label("Field: ")

        field_row_layout.addWidget(field_label)
        field_row_layout.addWidget(self.generate_field_combobox)
        tab_layout.addLayout(field_row_layout)

        # Start and End GPS input fields in one row
        gps_input_layout_start = self.create_gps_input_row("Start GPS:\t", self.start_gps_input_lat,
                                                           self.start_gps_input_lon)
        gps_input_layout_end = self.create_gps_input_row("End GPS:\t", self.end_gps_input_lat, self.end_gps_input_lon)

        tab_layout.addLayout(gps_input_layout_start)
        tab_layout.addLayout(gps_input_layout_end)

        # Generate Run button
        generate_run_button = QPushButton("Generate run", self)
        generate_run_button.clicked.connect(self.uiManager.generate_run)

        tab_layout.addItem(self.spacer)
        tab_layout.addWidget(generate_run_button)

        return tab_layout

    def compare_run_ui(self):
        compare_run_layout = QVBoxLayout()
        compare_run_label = self.make_label("Compare runs:", small=False)
        compare_run_layout.addWidget(compare_run_label)

        run_one_layout = QHBoxLayout()
        run_one_label = self.make_label("Run One:")

        # Populate dropdowns by copying data, not by reference
        self.compare_runs_one_dropdown.addItems(
            [self.runs_in_field_dropdown.itemText(i) for i in range(self.runs_in_field_dropdown.count())])

        self.compare_runs_two_dropdown.addItems(
            [self.runs_in_field_dropdown.itemText(i) for i in range(self.runs_in_field_dropdown.count())])

        run_two_layout = QHBoxLayout()
        run_two_label = self.make_label("Run Two:")
        run_one_layout.addWidget(run_one_label, 1)
        run_one_layout.addWidget(self.compare_runs_one_dropdown, 3)
        run_two_layout.addWidget(run_two_label, 1)
        run_two_layout.addWidget(self.compare_runs_two_dropdown, 3)

        compare_run_button = QPushButton("Compare runs", self)
        compare_run_button.clicked.connect(self.uiManager.compare_runs)

        compare_run_layout.addLayout(run_one_layout)
        compare_run_layout.addLayout(run_two_layout)
        compare_run_layout.addWidget(compare_run_button)
        compare_run_layout.addItem(self.spacer)

        return compare_run_layout

    def create_gps_input_row(self, label_text, lat_input, lon_input):
        gps_input_row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {self.text_color};")
        label.setFont(self.small_font)
        lat_input.setPlaceholderText("Enter Latitude")
        lon_input.setPlaceholderText("Enter Longitude")
        gps_input_row.addWidget(label)
        gps_input_row.addWidget(lat_input)
        gps_input_row.addWidget(lon_input)
        return gps_input_row

    def delete_selected_run(self):
        selected_run = self.all_runs_dropdown.currentText()

        confirm_deletion = QMessageBox(self)
        confirm_deletion.setIcon(QMessageBox.Icon.Question)
        confirm_deletion.setWindowTitle("Confirm Deletion")
        confirm_deletion.setText(f"Are you sure you want to delete run {selected_run}?")

        delete_button = confirm_deletion.addButton("Delete Run", QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = confirm_deletion.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        confirm_deletion.setDefaultButton(cancel_button)

        confirm_deletion.exec()

        if confirm_deletion.clickedButton() == delete_button:
            self.db.delete_run_by_run_name(selected_run)
            print(f"Deleted run {selected_run}")
            self.uiManager.update_dropdowns()

    def define_crops_dropdown(self, label, tab_layout):
        # todo
        dropdown = self.all_crops_dropdown
        tab_layout.addWidget(label)
        tab_layout.addWidget(dropdown)

        return tab_layout

    def make_label(self, text, small=True):
        label = QLabel(text)
        label.setStyleSheet(f"color: {self.text_color};")
        if small:
            label.setFont(self.small_font)
        if not small:
            label.setFont(self.big_font)
        return label

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

    def handle_field_update(self, field_data):
        self.uiManager.update_ui(field_data)
