from typing import TYPE_CHECKING
from UI.runComparator import RunComparator

if TYPE_CHECKING:
    from UI.mainUI import MainWindow
    from Database.database_handler import DatabaseHandler
    from UI.backend import Backend


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
        self.update_dropdowns()

        # Send the backend the current existing runs on the field
        self.back_end.send_run_detections_from_fields_tab()

    def update_dropdowns(self):
        # Block signals during update for preventing feedback loop
        for dropdown in self.main_window.dropdowns:
            dropdown.blockSignals(True)

        try:
            # Clear and repopulate
            for dropdown in self.main_window.dropdowns:
                dropdown.clear()

            # update dropdowns
            self.update_field_tab_dropdowns()
            self.update_runs_tab_dropdowns()
            self.update_crops_tab_dropdowns()

        finally:
            # Always restore signal handling
            for dropdown in self.main_window.dropdowns:
                dropdown.blockSignals(False)

    def update_field_tab_dropdowns(self):
        self.main_window.all_fields_dropdown.addItems(self.db.get_all_fields())

        self.main_window.all_fields_dropdown.setCurrentIndex(self.current_selected_field())

        # Get runs in the field from db
        field_id = self.db.get_field_id_by_field_name(f"Field_{self.main_window.selected_field_name_label.text()}")
        runs_in_field = self.db.get_runs_by_field_id(field_id)
        self.main_window.runs_in_field_dropdown.addItems(runs_in_field)

        self.main_window.compare_runs_one_dropdown.addItems(
            [self.main_window.runs_in_field_dropdown.itemText(i) for i in
             range(self.main_window.runs_in_field_dropdown.count())])

        self.main_window.compare_runs_two_dropdown.addItems(
            [self.main_window.runs_in_field_dropdown.itemText(i) for i in
             range(self.main_window.runs_in_field_dropdown.count())])

        self.main_window.compared_list.addItems(self.db.get_compared_runs_by_field(field_id))

    def update_runs_tab_dropdowns(self):
        self.main_window.all_runs_dropdown.addItems(self.db.get_all_runs())
        self.main_window.generate_field_combobox.addItems(self.db.get_all_fields())
        self.main_window.generate_field_combobox.setCurrentIndex(self.current_selected_field())

    def update_crops_tab_dropdowns(self):
        self.main_window.all_crops_dropdown.addItems(self.db.get_all_crops())

    def current_selected_field(self):
        # Set field dropdown text to clicked field
        full_field_name = f"Field_{self.main_window.selected_field_name_label.text()}"
        for index in range(self.main_window.all_fields_dropdown.count()):
            if self.main_window.all_fields_dropdown.itemText(index) == full_field_name:
                return index
        return 0

    def generate_run(self):
        # Get inputs
        selected_video = self.main_window.available_videos.currentText()
        selected_field = self.main_window.generate_field_combobox.currentText()

        # Get GPS values with clear names
        lat_start = self.main_window.start_gps_input_lat.text().strip()
        lon_start = self.main_window.start_gps_input_lon.text().strip()
        lat_end = self.main_window.end_gps_input_lat.text().strip()
        lon_end = self.main_window.end_gps_input_lon.text().strip()

        if not self.validate_coordinates(lat_start, lon_start, lat_end, lon_end):
            print("Invalid GPS coordinates")
            return

        try:
            # Convert to floats after validation
            start_gps = (float(lat_start), float(lon_start))
            end_gps = (float(lat_end), float(lon_end))
            self.main_window.state_manager.make_run(selected_video, selected_field, start_gps, end_gps)
        except ValueError:
            print("GPS coordinates must be numbers")

    def validate_coordinates(self, lat1, lon1, lat2, lon2):
        """Validate GPS coordinates are within Earth's ranges"""

        def is_valid(lat, lon):
            try:
                lat = float(lat)
                lon = float(lon)
                return -90 <= lat <= 90 and -180 <= lon <= 180
            except ValueError:
                return False

        return all([
            lat1 and lon1 and lat2 and lon2,  # Check non-empty
            is_valid(lat1, lon1),  # Check start coordinates
            is_valid(lat2, lon2)  # Check end coordinates
        ])

    def compare_runs(self):
        comparison_id = self.run_comparator.compare_runs(self.main_window.compare_runs_one_dropdown.currentText(), self.main_window.compare_runs_two_dropdown.currentText())
        self.back_end.send_comparisons(comparison_id)

    def delete_comparison(self):
        self.db.delete_comparison_by_id(self.main_window.compared_list.currentText())