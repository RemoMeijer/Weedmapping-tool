from typing import TYPE_CHECKING
from LiveProcessing.UI.runComparator import RunComparator

if TYPE_CHECKING:
    from LiveProcessing.UI.mainUI import MainWindow
    from Database.database_handler import DatabaseHandler
    from LiveProcessing.UI.backend import Backend


class UiUpdater:
    def __init__(self, main_window: 'MainWindow', db: 'DatabaseHandler', back_end: 'Backend'):
        self.main_window: MainWindow = main_window
        self.db: DatabaseHandler = db
        self.back_end: Backend = back_end
        self.run_comparator: RunComparator = RunComparator(self.db)

    def update_ui(self, parsed_data):
        # Data we want to display in the info section
        key_to_widget = {
            "id": self.main_window.selected_field_name_label,
            "gewas": self.main_window.selected_field_crop_label,
            "category": self.main_window.selected_field_category_label,
        }

        # Add data to UI
        for key, value in parsed_data.items():
            widget = key_to_widget.get(key)
            if widget:
                widget.setText(f"{value}")

        # Update dropdowns based on info text
        self.update_field_section_dropdowns()
        self.back_end.send_run_detections_from_fields_tab()


    def update_field_section_dropdowns(self):
        # Block signals during update for preventing feedback loop
        self.main_window.all_runs_dropdown.blockSignals(True)
        self.main_window.all_fields_dropdown.blockSignals(True)
        self.main_window.runs_in_field_dropdown.blockSignals(True)

        try:
            # Clear and repopulate
            self.main_window.all_runs_dropdown.clear()
            self.main_window.all_fields_dropdown.clear()
            self.main_window.runs_in_field_dropdown.clear()
            self.main_window.compare_runs_one_dropdown.clear()
            self.main_window.compare_runs_two_dropdown.clear()

            # Add fresh items
            self.main_window.all_runs_dropdown.addItems(self.db.get_all_runs())
            self.main_window.all_fields_dropdown.addItems(self.db.get_all_fields())
            field_id = self.db.get_field_id_by_field_name(f"Field_{self.main_window.selected_field_name_label.text()}")

            # Set field dropdown text to clicked field
            full_field_name = f"Field_{self.main_window.selected_field_name_label.text()}"
            for index in range(self.main_window.all_fields_dropdown.count()):
                if self.main_window.all_fields_dropdown.itemText(index) == full_field_name:
                    self.main_window.all_fields_dropdown.setCurrentIndex(index)

            # Get runs in the field from db
            runs_in_field = self.db.get_runs_by_field_id(field_id)
            self.main_window.runs_in_field_dropdown.addItems(runs_in_field)

            self.main_window.compare_runs_one_dropdown.addItems(
                [self.main_window.runs_in_field_dropdown.itemText(i) for i in range(self.main_window.runs_in_field_dropdown.count())])

            self.main_window.compare_runs_two_dropdown.addItems(
                [self.main_window.runs_in_field_dropdown.itemText(i) for i in range(self.main_window.runs_in_field_dropdown.count())])

        finally:
            # Always restore signal handling
            self.main_window.all_runs_dropdown.blockSignals(False)
            self.main_window.all_fields_dropdown.blockSignals(False)
            self.main_window.runs_in_field_dropdown.blockSignals(False)

    def generate_run(self):
        # Get inputs
        selected_video = self.main_window.available_videos.currentText()
        selected_field = self.main_window.generate_field_combobox.currentText()

        # Get GPS values with clear names
        ns_start = self.main_window.start_gps_input_lat.text().strip()
        ew_start = self.main_window.start_gps_input_lon.text().strip()
        ns_end = self.main_window.end_gps_input_lat.text().strip()
        ew_end = self.main_window.end_gps_input_lon.text().strip()

        if not self.validate_coordinates(ns_start, ew_start, ns_end, ew_end):
            print("Invalid GPS coordinates")
            return

        try:
            # Convert to floats after validation
            start_gps = (float(ns_start), float(ew_start))
            end_gps = (float(ns_end), float(ew_end))
            self.main_window.state_manager.make_run(selected_video, selected_field, start_gps, end_gps)
        except ValueError:
            print("GPS coordinates must be numbers")

    def validate_coordinates(self, lat1, lon1, lat2, lon2):
        """Validate GPS coordinates are within Earth's ranges"""

        def is_valid(ns, ew):
            try:
                lat = float(ns)
                lon = float(ew)
                return -90 <= lat <= 90 and -180 <= lon <= 180
            except ValueError:
                return False

        return all([
            lat1 and lon1 and lat2 and lon2,  # Check non-empty
            is_valid(lat1, lon1),  # Check start coordinates
            is_valid(lat2, lon2)  # Check end coordinates
        ])

    def compare_runs(self):
        id = self.run_comparator.compare_runs(self.main_window.compare_runs_one_dropdown.currentText(), self.main_window.compare_runs_two_dropdown.currentText())
        self.back_end.send_comparisons(id)