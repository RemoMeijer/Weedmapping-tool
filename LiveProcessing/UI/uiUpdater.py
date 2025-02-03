from PyQt6.QtWidgets import QLabel, QComboBox


class UiUpdater:
    def __init__(self, main_window, db, back_end):
        self.main_window = main_window
        self.db = db
        self.back_end = back_end

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
                    widget.setText(f"{value}")

                # Update QComboBox
                elif isinstance(widget, QComboBox):
                    if value not in [widget.itemText(i) for i in range(widget.count())]:
                        widget.addItem(value)
                    widget.setCurrentText(value)
        self.update_field_runs_dropdown(parsed_data)
        self.update_dropdowns()


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

    def update_dropdowns(self):
        # Block signals during update
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
            print(field_id)
            runs_in_field = self.db.get_runs_by_field_id(field_id)
            if runs_in_field:
                self.main_window.field_runs_dropdown.addItems(runs_in_field[0])
            else:
                self.main_window.field_runs_dropdown.addItem("No runs in this field")

        finally:
            # Always restore signal handling
            self.main_window.run_dropdown.blockSignals(False)
            self.main_window.field_dropdown.blockSignals(False)
            self.main_window.field_runs_dropdown.blockSignals(False)

