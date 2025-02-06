from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from LiveProcessing.UI.mainUI import MainWindow
    from Database.database_handler import DatabaseHandler
    from LiveProcessing.UI.backend import Backend

class UiUpdater:
    def __init__(self, main_window: 'MainWindow', db: 'DatabaseHandler', back_end: 'Backend'):


        self.main_window: MainWindow = main_window
        self.db: DatabaseHandler = db
        self.back_end: Backend = back_end

    def update_ui(self, parsed_data):
        # Data we want to display in the info section
        key_to_widget = {
            "id": self.main_window.field_name_label,
            "gewas": self.main_window.field_crop_label,
            "category": self.main_window.field_category_label,
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
        self.main_window.run_dropdown.blockSignals(True)
        self.main_window.field_dropdown.blockSignals(True)
        self.main_window.field_runs_dropdown.blockSignals(True)

        try:
            # Clear and repopulate
            self.main_window.run_dropdown.clear()
            self.main_window.field_dropdown.clear()
            self.main_window.field_runs_dropdown.clear()

            # Add fresh items
            self.main_window.run_dropdown.addItems(self.db.get_all_runs())
            self.main_window.field_dropdown.addItems(self.db.get_all_fields())
            field_id = self.db.get_field_id_by_field_name(f"Field_{self.main_window.field_name_label.text()}")

            # Set field dropdown text to clicked field
            full_field_name = f"Field_{self.main_window.field_name_label.text()}"
            for index in range(self.main_window.field_dropdown.count()):
                if self.main_window.field_dropdown.itemText(index) == full_field_name:
                    self.main_window.field_dropdown.setCurrentIndex(index)

            # Get runs in the field from db
            runs_in_field = self.db.get_runs_by_field_id(field_id)
            self.main_window.field_runs_dropdown.addItems(runs_in_field)

        finally:
            # Always restore signal handling
            self.main_window.run_dropdown.blockSignals(False)
            self.main_window.field_dropdown.blockSignals(False)
            self.main_window.field_runs_dropdown.blockSignals(False)
