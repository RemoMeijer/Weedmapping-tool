import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QLabel, QComboBox


class Backend(QObject):
    # Signal to send data from Python to JavaScript
    send_data_to_js = pyqtSignal(str)

    def __init__(self, main_window, db):
        super().__init__()
        self.main_window = main_window # Main window reference to set fields with incoming data
        self.db = db

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
                    widget.setText(f"{value}")

                # Update QComboBox
                elif isinstance(widget, QComboBox):
                    if value not in [widget.itemText(i) for i in range(widget.count())]:
                        widget.addItem(value)
                    widget.setCurrentText(value)
        # self.update_field_runs_dropdown(parsed_data)
        self.main_window.update_dropdowns()


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
        self.run_dropdown.blockSignals(True)
        self.field_dropdown.blockSignals(True)
        self.field_runs_dropdown.blockSignals(True)

        try:
            # Clear and repopulate
            self.run_dropdown.clear()
            self.field_dropdown.clear()
            self.field_runs_dropdown.clear()

            # Add fresh items
            self.run_dropdown.addItems(self.db.get_all_runs())
            self.field_dropdown.addItems(self.db.get_all_fields())
            field_id = self.db.get_field_id_by_field_name(f"Field_{self.field_name_label.text()}")
            print(field_id)
            runs_in_field = self.db.get_runs_by_field_id(field_id)
            if runs_in_field:
                self.field_runs_dropdown.addItems(runs_in_field)
            else:
                self.field_runs_dropdown.addItem("No runs in this field")

        finally:
            # Always restore signal handling
            self.run_dropdown.blockSignals(False)
            self.field_dropdown.blockSignals(False)
            self.field_runs_dropdown.blockSignals(False)

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