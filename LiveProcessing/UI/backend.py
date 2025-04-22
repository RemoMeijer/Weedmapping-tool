import json
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from LiveProcessing.Database.database_handler import DatabaseHandler
    from LiveProcessing.UI.mainUI import MainWindow

"""Handle data interaction between UI and map, using pyqtSignals"""
class Backend(QObject):
    # Signal to send data from Python to JavaScript
    send_data_to_js = pyqtSignal(str)
    field_data_received = pyqtSignal(dict)

    def __init__(self, main_window: 'MainWindow', db: 'DatabaseHandler'):
        super().__init__()

        self.main_window: MainWindow = main_window # Main window reference to set fields with incoming data
        self.db: DatabaseHandler = db

    @pyqtSlot(str)
    def receive_data_from_js(self, data):
        parsed_data = json.loads(data)

        # Check the identifier to handle different types of data
        identifier = parsed_data.get("identifier")
        if identifier == "field":
            field_properties = parsed_data.get("properties", {})
            # Emit signal that some field data is received
            self.field_data_received.emit(field_properties)

        else:
            print(f"Unknown identifier: {identifier}")


    def send_run_detections_from_fields_tab(self):
        run_id = self.main_window.runs_in_field_dropdown.currentText()
        self.send_detections(run_id)

    def send_run_detections_from_run_tab(self):
        run_id = self.main_window.all_runs_dropdown.currentText()
        # self.goto_field_on_map_from_run_tab()
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
        self.send_data_to_js.emit(json_data)

    def send_comparisons_current_text(self):
        self.send_comparisons( self.main_window.compared_list.currentText())

    def send_comparisons(self, comparison_id):
        comparisons = self.db.get_comparisons_by_id(comparison_id)

        data = {
            "identifier": "comparisons",
            "comparisons": comparisons
        }

        json_data = json.dumps(data)
        print(json_data)
        self.send_data_to_js.emit(json_data)
